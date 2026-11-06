const {test,before,after}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const {spawn,execFileSync}=require('node:child_process');
const {once}=require('node:events');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'..');
const base='http://127.0.0.1:18769';
const baseline='http://127.0.0.1:18772';
const artifactDir=process.env.ORA_VISUAL_DIR;
const measurements=[];
let browser,temp,servers=[];
async function serve(cwd,port){
 const server=spawn(process.execPath,['server.mjs'],{cwd,env:{...process.env,PORT:String(port)},stdio:['ignore','pipe','pipe']});servers.push(server);
 await Promise.race([once(server.stdout,'data'),once(server,'exit').then(([code])=>{throw new Error(`Servidor ${port} terminó: ${code}`);})]);
}
before(async()=>{
 temp=fs.mkdtempSync(path.join(os.tmpdir(),'ora-responsive-baseline-'));
 const archive=execFileSync('git',['archive','origin/main'],{cwd:root,maxBuffer:64*1024*1024});
 execFileSync('tar',['-x','-C',temp],{input:archive});
 await serve(root,18769);await serve(temp,18772);
 const executablePath=process.env.CHROMIUM_PATH||(fs.existsSync('/usr/bin/chromium')?'/usr/bin/chromium':undefined);
 browser=await chromium.launch({executablePath,args:['--no-sandbox']});
 if(artifactDir)fs.mkdirSync(artifactDir,{recursive:true});
});
after(async()=>{
 await browser?.close();
 for(const server of servers){if(server.exitCode===null){const exited=once(server,'exit');server.kill();await exited;}}
 if(temp)fs.rmSync(temp,{recursive:true,force:true});
 if(artifactDir)fs.writeFileSync(path.join(artifactDir,'metrics.json'),JSON.stringify(measurements,null,2));
});
async function open(t,width,height,url=base,extra={}){
 const context=await browser.newContext({viewport:{width,height},deviceScaleFactor:1,reducedMotion:'no-preference',isMobile:width<=600,hasTouch:width<=900,...extra});
 t.after(()=>context.close());const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));t.after(()=>assert.deepEqual(errors,[]));
 await page.route('https://fonts.googleapis.com/**',r=>r.abort());await page.goto(url+'/?scan=0');return page;
}
async function enter(page,k=5){
 const floor=page.locator(`polygon[data-tod="day"][data-plane="T2L"][data-k="${k}"]`);
 if(await page.evaluate(()=>matchMedia('(hover: none)').matches)){
  await floor.tap();
  await page.waitForFunction(()=>+getComputedStyle(document.querySelector('#tip')).opacity>.99);
  const tip=await page.locator('#tip').boundingBox();
  if(page.url().startsWith(base+'/'))assert(tip.width<=360&&tip.x>=0&&tip.x+tip.width<=page.viewportSize().width,'selector de pisos compacto y dentro de la pantalla');
  if(artifactDir)await page.screenshot({path:path.join(artifactDir,`${page.url().startsWith(base+'/')?'after':'before'}-floor-selector-${page.viewportSize().width}x${page.viewportSize().height}.png`)});
  await page.locator('#tip').tap();
 }else await floor.click();
 await page.locator('#panel').waitFor({state:'visible'});
 await page.waitForFunction(()=>!ORA_API.state.busy&&ORA_API.state.mode==='plan'&&ORA_API.state.state==='int'&&+getComputedStyle(document.querySelector('#panel')).opacity>.99);
}
async function capture(page,name){
 const data=await page.locator('#panel').evaluate(panel=>{
  const r=panel.getBoundingClientRect(),s=getComputedStyle(panel),title=getComputedStyle(document.querySelector('#pT'));
  return{width:r.width,height:r.height,x:r.x,y:r.y,padding:s.padding,background:s.backgroundColor,border:s.border,font:s.fontFamily,titleFont:title.font,viewport:[innerWidth,innerHeight]};
 });measurements.push({name,...data});
 if(artifactDir){
  // Mismo fotograma en ambos servidores con soporte HTTP Range real.
  await page.evaluate(async()=>{
   const video=document.querySelector('#vid');video.pause();
   async function seek(t){if(Math.abs(video.currentTime-t)<.001&&!video.seeking)return;await new Promise(resolve=>{video.addEventListener('seeked',resolve,{once:true});video.currentTime=t;});}
   await seek(.7);await seek(.54);await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
  });
  await page.screenshot({path:path.join(artifactDir,name+'.png')});
 }
 return data;
}
async function isTopTarget(page,selector){
 await page.locator(selector).scrollIntoViewIfNeeded();
 assert(await page.locator(selector).evaluate(e=>{const r=e.getBoundingClientRect();return document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)?.closest('button,a')===e;}),selector+' recibe su propio clic');
}
async function assertSingleExit(page,expected){
 await page.locator(expected).waitFor({ state: 'visible' });
 await page.locator(expected === '#back' ? '#pBack' : '#back').waitFor({ state: 'hidden' });
 assert.equal(await page.locator('#back').isVisible(),expected==='#back');
 assert.equal(await page.locator('#pBack').isVisible(),expected==='#pBack');
 await isTopTarget(page,expected);
}
for(const [width,height] of [[1440,900],[1280,800]]){
 test(`escritorio ${width}: panel con geometría y tipografía originales`,async t=>{
  const old=await open(t,width,height,baseline);await enter(old);const before=await capture(old,`before-${width}x${height}`);
  const page=await open(t,width,height);await enter(page);const after=await capture(page,`after-${width}x${height}`);
  assert.deepEqual(after,before);await assertSingleExit(page,'#pBack');assert(await page.locator('#cta').isVisible());
 });
}
for(const [width,height] of [[1024,768],[901,768],[900,768],[768,1024],[901,501]]){
 test(`ventana/tableta ${width}x${height}: tarjeta compacta y habitación sin superposición`,async t=>{
  const old=await open(t,width,height,baseline);await enter(old);await capture(old,`before-${width}x${height}`);
  const page=await open(t,width,height);await enter(page);const card=await capture(page,`after-${width}x${height}`);
  assert(card.width<=280);assert(card.width<width*.4);assert.equal(await page.locator('#panelToggle').isVisible(),false);
  await assertSingleExit(page,'#pBack');await isTopTarget(page,'#pRooms li:last-child button');
  await page.locator('#pRooms li:last-child button').click();await page.waitForFunction(()=>ORA_API.state.mode==='room');
  await assertSingleExit(page,'#back');assert.equal(await page.locator('#capT').textContent(),'Baño principal');
  assert(await page.locator('#cta').isVisible());await isTopTarget(page,'#cta');
 });
}
for(const [width,height] of [[600,900],[390,844],[320,568],[844,390],[1280,400]]){
 test(`teléfono ${width}x${height}: ficha plegable y salida siempre disponible`,async t=>{
  const old=await open(t,width,height,baseline);await enter(old);await capture(old,`before-${width}x${height}`);
  const page=await open(t,width,height);await enter(page);const small=await capture(page,`after-${width}x${height}-collapsed`);
  assert.equal(await page.locator('#panelToggle').getAttribute('aria-expanded'),'false');assert.equal(await page.locator('#panelDetails').isVisible(),false);
  assert(small.height<height*.4);assert(small.height<180);assert(await page.locator('#cta').isVisible());await isTopTarget(page,'#cta');await assertSingleExit(page,'#pBack');
  await page.locator('#panelToggle').click();assert.equal(await page.locator('#panelToggle').getAttribute('aria-expanded'),'true');
  const expanded=await capture(page,`after-${width}x${height}-expanded`);assert(expanded.height<=height*.56+1||width>600);assert(expanded.height<height-90);
  await assertSingleExit(page,'#pBack');await isTopTarget(page,'#pPlan');
  for(let i=0;i<3;i++){
   const button=page.locator('#pRooms button').nth(i);await button.scrollIntoViewIfNeeded();await button.click();
   await page.waitForFunction(i=>ORA_API.state.mode==='room'&&document.querySelector('#chips button.on')?.dataset.i===String(i),i);
   await assertSingleExit(page,'#back');await page.locator('#back').click();await page.waitForFunction(()=>ORA_API.state.mode==='plan');
  }
  await page.locator('#panelToggle').click();assert.equal(await page.locator('#panelDetails').isVisible(),false);
  await page.locator('#pBack').click();await page.waitForFunction(()=>ORA_API.state.state==='ext'&&!ORA_API.state.busy);
 });
}
test('carga pendiente: cancelar y Tour privado siguen accesibles',async t=>{
 const page=await open(t,390,844);await page.route('**/media/*.mp4',()=>{});
 const floor=page.locator('polygon[data-tod="day"][data-plane="T2L"][data-k="5"]');await floor.tap();await page.locator('#tip').tap();
 await page.locator('#mediaLoading').waitFor({state:'visible'});await assertSingleExit(page,'#back');
 await isTopTarget(page,'#cta');assert.equal(await page.locator('#cta').getAttribute('href'),'#');
 await page.locator('#cta').focus();await page.keyboard.press('Enter');assert(await page.locator('#mediaLoading').isVisible());
 await page.locator('#back').click();await page.waitForFunction(()=>ORA_API.state.state==='ext'&&!ORA_API.state.busy);
});
test('redimensionar y girar actualiza detalles sin perder foco ni navegación',async t=>{
 const page=await open(t,900,768);await enter(page);await page.setViewportSize({width:390,height:844});
 await page.waitForFunction(()=>document.querySelector('#panelDetails').hidden);await page.locator('#panelToggle').click();await page.locator('#pRooms button').first().focus();
 await page.setViewportSize({width:1440,height:900});await page.waitForFunction(()=>!document.querySelector('#panelDetails').hidden&&getComputedStyle(document.querySelector('#panelToggle')).display==='none');
 await page.setViewportSize({width:844,height:390});await page.waitForFunction(()=>document.querySelector('#panelDetails').hidden);
 assert.equal(await page.evaluate(()=>document.activeElement.id),'panelToggle');await assertSingleExit(page,'#pBack');
});
test('el primer botón visible funciona sin esperar un estado interno',async t=>{
 const page=await open(t,1440,900);await page.locator('polygon[data-tod="day"][data-plane="T2L"][data-k="5"]').click();
 await page.locator('#pRooms button').nth(1).click();await page.waitForFunction(()=>ORA_API.state.mode==='room');
 assert.equal(await page.locator('#capT').textContent(),'Habitación principal');
});

test('ventana amplia de poca altura: salida fija y detalles desplazables',async t=>{
 const page=await open(t,1440,550);await enter(page);await assertSingleExit(page,'#pBack');
 const r=await page.locator('#panel').boundingBox();assert(r.y>=50&&r.y+r.height<=550);
 await isTopTarget(page,'#cta');await isTopTarget(page,'#pRooms li:last-child button');
});

test('clic real durante el fundido cambia de baño a sala sin activar la salida',async t=>{
 const page=await open(t,390,844);
 await enter(page);await page.locator('#panelToggle').click();
 await page.locator('#pRooms button').nth(2).click();
 // No esperar a que desaparezca el panel saliente: reproducir el intervalo auditado.
 await page.waitForFunction(()=>ORA_API.state.mode==='room'&&+getComputedStyle(document.querySelector('#chips')).opacity>=.3);
 const outgoing=await page.locator('#panel').evaluate(e=>+getComputedStyle(e).opacity);
 assert(outgoing>0,'el panel anterior todavía está en pleno fundido');
 const chip=page.locator('#chips button').first();const r=await chip.boundingBox();
 const point={x:r.x+r.width/2,y:r.y+r.height/2};
 const receivesClick=await chip.evaluate((e,p)=>document.elementFromPoint(p.x,p.y)?.closest('button')===e,point);
 await page.mouse.click(point.x,point.y);
 assert(receivesClick,'Sala y cocina recibe el clic durante el fundido');
 if(artifactDir)fs.writeFileSync(path.join(artifactDir,'rapid-click-fixed.json'),JSON.stringify({viewport:page.viewportSize(),outgoingOpacity:outgoing,point,receivesClick},null,2));
 await page.waitForFunction(()=>ORA_API.state.state==='int'&&!ORA_API.state.busy&&document.querySelector('#chips button.on')?.dataset.i==='0');
 assert.equal(await page.locator('#capT').textContent(),'Sala y cocina');
 assert.equal(await page.evaluate(()=>ORA_API.state.state),'int');
});
