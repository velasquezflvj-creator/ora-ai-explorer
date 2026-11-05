// Opt-in comparison against an untouched checkout of Nicolas's reference.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const {spawn,execFileSync}=require('node:child_process');
const {once}=require('node:events');
const fs=require('node:fs');
const path=require('node:path');
const {chromium}=require('playwright');
const reference=process.env.ORA_REFERENCE_DIR;
test('Nicolás: exterior, selección e interior en cinco resoluciones', {skip:!reference,timeout:240000},async()=>{
 const output=path.resolve(process.env.ORA_COMPARISON_DIR||'/tmp/ora-comparison');fs.mkdirSync(output,{recursive:true});
 const root=path.resolve(__dirname,'..'),servers=[];let browser;const metrics=[];
 try{
  for(const [cwd,port] of [[reference,18774],[root,18775]]){
   const server=spawn(process.execPath,['server.mjs'],{cwd,env:{...process.env,PORT:String(port)},stdio:['ignore','pipe','pipe']});servers.push(server);
   await Promise.race([once(server.stdout,'data'),once(server,'exit').then(()=>{throw Error('Servidor no inició');})]);
  }
  browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox']});
  for(const [width,height] of [[1440,900],[1280,800],[900,768],[768,1024],[390,844]]){
   for(const [label,port] of [['nicolas',18774],['corregido',18775]]){
    const context=await browser.newContext({viewport:{width,height},deviceScaleFactor:1,reducedMotion:'no-preference'});
    try{
     const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
     // Identical fallback fonts: external font availability must not skew comparison.
     await page.route('https://fonts.googleapis.com/**',r=>r.abort());
     await page.goto(`http://127.0.0.1:${port}/?scan=0`);
     await page.waitForFunction(()=>window.ORA_API&&document.querySelector('#img-day').complete);
     const shot=async state=>{
      await page.screenshot({path:path.join(output,`${width}x${height}-${state}-${label}.png`)});
      const data=await page.evaluate(()=>{
       const rect=id=>{const r=document.getElementById(id).getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height};};
       return {tip:rect('tip'),panel:rect('panel'),viewport:[innerWidth,innerHeight],videoTime:document.querySelector('#vid').currentTime};
      });metrics.push({label,state,...data});
     };
     await shot('exterior');
     await page.evaluate(()=>ORA_API.hover('day','T2L',5));await page.waitForTimeout(250);
     await shot('pisos');
     if(label==='corregido'){
      const r=await page.locator('#tip').boundingBox();assert(r.width<=280&&r.x>=14&&r.x+r.width<=width-14&&r.y>=80&&r.y+r.height<height-65);
      assert(await page.locator('#tip').evaluate(e=>{const r=e.getBoundingClientRect();return document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)?.closest('button')===e;}));
     }
     await page.locator('#tip').click();
     await page.waitForFunction(()=>ORA_API.state.state==='int'&&!ORA_API.state.busy&&ORA_API.state.mode==='plan');
     await page.waitForTimeout(800);
     await page.evaluate(async()=>{const v=document.querySelector('#vid');v.pause();if(Math.abs(v.currentTime-.54)>.001)await new Promise(r=>{v.addEventListener('seeked',r,{once:true});v.currentTime=.54;});await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));});
     await shot('interior');
     if(label==='corregido'){
      const p=await page.locator('#panel').boundingBox();assert(p.width<=Math.max(360,width-32));
      if(width>600)assert(p.width<width*.4);
      await page.locator('#pBack').click();await page.waitForFunction(()=>ORA_API.state.state==='ext'&&!ORA_API.state.busy);
     }
     assert.deepEqual(errors,[]);
    }finally{await context.close();}
   }
  }
  fs.writeFileSync(path.join(output,'metrics.json'),JSON.stringify({referenceCommit:execFileSync('git',['rev-parse','HEAD'],{cwd:reference,encoding:'utf8'}).trim(),baseCommit:'7e377987956416617d08efb0ea44ee6a01bd229d',fonts:'Identical system fallback; Google Fonts blocked in both',metrics},null,2));
 }finally{await browser?.close();for(const s of servers){if(s.exitCode===null){const exited=once(s,'exit');s.kill();await exited;}}}
});
