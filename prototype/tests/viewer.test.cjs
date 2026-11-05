const {test,before,after}=require('node:test');
const assert=require('node:assert/strict');
const {spawn}=require('node:child_process');
const {once}=require('node:events');
const fs=require('node:fs');
const path=require('node:path');
const {chromium}=require('playwright');
let server,browser;
before(async()=>{
 server=spawn(process.execPath,['server.mjs'],{cwd:path.resolve(__dirname,'../..'),env:{...process.env,PORT:'18770'},stdio:['ignore','pipe','pipe']});
 await Promise.race([once(server.stdout,'data'),once(server,'exit').then(([code])=>{throw new Error('Servidor terminó '+code);})]);
 browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||(fs.existsSync('/usr/bin/chromium')?'/usr/bin/chromium':undefined),args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
});
after(async()=>{await browser?.close();server?.kill();});
async function open(t,options={}){
 const context=await browser.newContext({viewport:{width:1440,height:1000},...options});t.after(()=>context.close());
 const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));t.after(()=>assert.deepEqual(errors,[]));
 await page.goto('http://127.0.0.1:18770/prototype/');await page.waitForFunction(()=>window.ORA3D?.getSnapshot().drawCalls>20);return page;
}
const snapshot=p=>p.evaluate(()=>ORA3D.getSnapshot());
const distance=(a,b)=>Math.hypot(...a.map((v,i)=>v-b[i]));
async function advanceFrames(page,n=12){await page.evaluate(n=>new Promise(resolve=>{function tick(){if(--n<=0)resolve();else requestAnimationFrame(tick);}requestAnimationFrame(tick);}),n);}
test('WebGL real y maqueta identificada como provisional',async t=>{
 const p=await open(t);assert((await snapshot(p)).provisional);assert(await p.getByText('MAQUETA PROVISIONAL',{exact:true}).first().isVisible());assert.equal(await p.locator('#error').isVisible(),false);
 const requests=[];p.on('request',r=>requests.push(r.url()));await advanceFrames(p);assert(!requests.some(x=>x.includes('http')&&!x.includes('127.0.0.1')));
});
test('rotación orbital y zoom mediante gestos reales',async t=>{
 const p=await open(t);const old=await snapshot(p);const c=await p.locator('canvas').boundingBox();await p.mouse.move(c.x+c.width*.55,c.y+c.height*.6);await p.mouse.down();await p.mouse.move(c.x+c.width*.65,c.y+c.height*.65,{steps:10});await p.mouse.up();await advanceFrames(p);const rotated=await snapshot(p);assert(distance(old.position,rotated.position)>.2);
 await p.mouse.wheel(0,-400);await advanceFrames(p,25);assert(distance((await snapshot(p)).position,rotated.position)>.2);
});
test('hotspot visible y las cuatro habitaciones responden a clics',async t=>{
 const p=await open(t);await p.locator('[data-hotspot="bedroom"]').click();assert.equal((await snapshot(p)).selected,'bedroom');assert.equal((await snapshot(p)).mode,'walk');
 for(const id of ['living','kitchen','bedroom','bathroom']){await p.locator(`[data-room="${id}"]`).click();assert.equal((await snapshot(p)).selected,id);assert.equal((await snapshot(p)).mode,'walk');}
 await p.keyboard.press('Escape');assert.equal((await snapshot(p)).mode,'orbit');
});
test('raycasting sobre un punto 3D selecciona su habitación',async t=>{
 const p=await open(t);const marker=p.locator('[data-hotspot="living"]');const r=await marker.boundingBox();assert(r);await p.locator('#markers').evaluate(e=>e.style.visibility='hidden');await p.mouse.click(r.x+r.width/2,r.y+r.height/2);assert.equal((await snapshot(p)).selected,'living');
});
test('presentación mueve la misma cámara y se cancela al explorar',async t=>{
 const p=await open(t);await p.locator('[data-mode="cinematic"]').click();const a=await snapshot(p);await advanceFrames(p,30);const b=await snapshot(p);assert.equal(b.mode,'cinematic');assert(b.cinemaTime>a.cinemaTime);assert(distance(a.position,b.position)>.01);
 await p.locator('[data-mode="walk"]').click();const stopped=await snapshot(p);await advanceFrames(p,15);const later=await snapshot(p);assert.equal(later.mode,'walk');assert.equal(later.cinemaTime,stopped.cinemaTime);assert(distance(later.position,stopped.position)<.001);
});
test('teclado y arrastre permiten desplazarse y mirar en interior',async t=>{
 const p=await open(t);await p.locator('[data-mode="walk"]').click();const a=await snapshot(p);await p.keyboard.down('w');await advanceFrames(p,30);await p.keyboard.up('w');const b=await snapshot(p);assert(distance(a.position,b.position)>.15);
 await p.mouse.move(500,420);await p.mouse.down();await p.mouse.move(600,420,{steps:10});await p.mouse.up();await p.keyboard.down('w');await advanceFrames(p,15);await p.keyboard.up('w');assert(distance((await snapshot(p)).position,b.position)>.05);
});
test('acabados cambian el render y se conservan al cambiar de cámara',async t=>{
 const p=await open(t);const canvas=p.locator('canvas');const a=await canvas.screenshot();await p.locator('[data-floor="clay"]').click();await advanceFrames(p);const b=await canvas.screenshot();assert.equal((await snapshot(p)).floor,'clay');assert(!a.equals(b));
 await p.locator('#wallColor').fill('#a0bba1');assert.equal((await snapshot(p)).wallColor,'#a0bba1');await p.locator('[data-mode="walk"]').click();await p.locator('[data-mode="orbit"]').click();assert.equal((await snapshot(p)).floor,'clay');assert.equal((await snapshot(p)).wallColor,'#a0bba1');
});
test('móvil: puntos, controles táctiles y selector accesibles',async t=>{
 const p=await open(t,{viewport:{width:390,height:844},isMobile:true,hasTouch:true});assert(await p.getByText('MAQUETA PROVISIONAL',{exact:true}).first().isVisible());await p.locator('[data-hotspot="kitchen"]').tap();assert.equal((await snapshot(p)).selected,'kitchen');const button=p.locator('[data-move="forward"]');const r=await button.boundingBox();assert(r);const old=await snapshot(p);const cdp=await p.context().newCDPSession(p);await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:r.x+r.width/2,y:r.y+r.height/2}]});await advanceFrames(p,25);await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});assert(distance((await snapshot(p)).position,old.position)>.05);await p.locator('[data-floor="stone"]').tap();assert.equal((await snapshot(p)).floor,'stone');
});
test('movimiento reducido evita el vuelo automático',async t=>{
 const p=await open(t,{reducedMotion:'reduce'});await p.locator('[data-mode="cinematic"]').click();assert.equal((await snapshot(p)).mode,'orbit');
});

test('abrir la referencia y volver conserva un visor utilizable',async t=>{
 const p=await open(t);await p.locator('.reference').click();await p.waitForFunction(()=>!!window.ORA_API);assert.equal(await p.title(),'Ora AI — Explorador de torres');
 await p.goBack();await p.waitForFunction(()=>window.ORA3D?.getSnapshot().drawCalls>20);await p.locator('[data-mode="walk"]').click();assert.equal((await snapshot(p)).mode,'walk');
});
