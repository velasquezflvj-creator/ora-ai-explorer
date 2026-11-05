import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { createDemoModel, rooms } from './model.mjs';
import { moveWithCollisions } from './collision.mjs';

const canvas = document.querySelector('#scene');
const viewport = document.querySelector('#viewport');
const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
let renderer;
try { renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false }); }
catch (error) { document.querySelector('#error').hidden = false; throw error; }
renderer.setPixelRatio(Math.min(devicePixelRatio, 1.75));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.3;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
const scene = new THREE.Scene();
scene.background = new THREE.Color('#e8e8db');
const camera = new THREE.PerspectiveCamera(43,1,.08,100);
const controls = new OrbitControls(camera,canvas);
controls.enableDamping = true; controls.minDistance = 7; controls.maxDistance = 45;
controls.maxPolarAngle = Math.PI * .47;
const model = createDemoModel(); scene.add(model.group);
scene.add(new THREE.HemisphereLight('#fff9e9','#78867a',2.4));
const sun = new THREE.DirectionalLight('#fff1d3',3.3); sun.position.set(-5,13,9);sun.castShadow=true;
sun.shadow.mapSize.set(1024,1024);Object.assign(sun.shadow.camera,{left:-10,right:10,top:10,bottom:-10,near:.5,far:35});sun.shadow.normalBias=.04;scene.add(sun);
const ground = new THREE.Mesh(new THREE.PlaneGeometry(200,200),new THREE.MeshStandardMaterial({color:'#e1e2d4',roughness:1}));
ground.rotation.x=-Math.PI/2;ground.position.y=-.39;ground.receiveShadow=true;scene.add(ground);

// Texturas procedurales propias; no se descargan materiales ni modelos externos.
function woodTexture() {
  const c=document.createElement('canvas');c.width=c.height=256;const ctx=c.getContext('2d');
  ctx.fillStyle='#c3a278';ctx.fillRect(0,0,256,256);
  for(let i=0;i<256;i++){ctx.fillStyle=`rgba(91,64,34,${.02+((i*37)%13)/180})`;ctx.fillRect(i,0,1,256);}
  for(let z=0;z<256;z+=64){ctx.fillStyle='#95734c';ctx.fillRect(0,z,256,1);ctx.fillRect(z%128+40,z,1,64);}
  const texture=new THREE.CanvasTexture(c);texture.colorSpace=THREE.SRGBColorSpace;texture.wrapS=texture.wrapT=THREE.RepeatWrapping;texture.repeat.set(3,3);texture.anisotropy=Math.min(renderer.capabilities.getMaxAnisotropy(),4);return texture;
}
const oakTexture=woodTexture();
const floors={oak:{label:'Roble',color:'#ffffff',roughness:.72,map:oakTexture},stone:{label:'Piedra',color:'#bfc3b8',roughness:.42,map:null},clay:{label:'Arcilla',color:'#b6755d',roughness:.9,map:null}};
let floorId='oak';
function setFloor(id){
 const value=floors[id];if(!value)return;
 model.materials.floor.color.set(value.color);model.materials.floor.roughness=value.roughness;model.materials.floor.map=value.map;model.materials.floor.needsUpdate=true;floorId=id;
 document.querySelectorAll('[data-floor]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.floor===id)));
 document.querySelector('#materialStatus').textContent='Piso: '+value.label;
}
setFloor('oak');
document.querySelectorAll('[data-floor]').forEach(b=>b.addEventListener('click',()=>setFloor(b.dataset.floor)));
document.querySelector('#wallColor').addEventListener('input',e=>model.materials.walls.color.set(e.target.value));

let mode='orbit', selected=null, yaw=0,pitch=0,cinemaTime=0,disposed=false;
const keys=new Set(); const pad=new Set();
const hints={orbit:'Arrastra para rotar · rueda o gesto de pinza para zoom',cinematic:'Recorrido automático · elige Explorar para tomar el control',walk:'WASD o flechas para caminar · arrastra para mirar · Esc: vista general'};
const points=[
 {p:[12,11,14],t:[0,0,0]},
 {p:[-1.5,1.55,3],t:[-4,1,2.7]},
 {p:[-1.5,1.55,.7],t:[-1.5,1.3,-2]},
 {p:[-1.5,1.55,-1.7],t:[-4,1,-3.3]},
 {p:[-1,1.55,-2.9],t:[2.7,1,-3]},
 {p:[.6,1.55,-2.9],t:[4.8,1,-3.5]},
 {p:[2.8,1.55,-1.8],t:[4.8,1,-3.5]},
 {p:[2.8,1.55,.9],t:[4.9,1,2.5]},
 {p:[2.1,1.55,1.5],t:[4.9,1,2.5]},
 {p:[12,11,14],t:[0,0,0]},
];
function resetOrbit(){const framing=Math.max(1,1.15/camera.aspect);camera.position.set(12,11,14).multiplyScalar(framing);controls.target.set(0,.4,0);camera.lookAt(controls.target);controls.update();}
function updateAngles(){const d=new THREE.Vector3();camera.getWorldDirection(d);yaw=Math.atan2(d.x,-d.z);pitch=Math.asin(THREE.MathUtils.clamp(d.y,-1,1));}
function look(){camera.lookAt(camera.position.x+Math.sin(yaw)*Math.cos(pitch),camera.position.y+Math.sin(pitch),camera.position.z-Math.cos(yaw)*Math.cos(pitch));}
function setMode(next){
 keys.clear();pad.clear();mode=next;controls.enabled=next==='orbit';
 if(next==='orbit'){selected=null;resetOrbit();}
 if(next==='walk'){
  // Siempre entra en un punto interior seguro, nunca desde una posición exterior de cámara.
  const room=rooms.find(r=>r.id===selected)||rooms[0];camera.position.fromArray(room.point);camera.lookAt(new THREE.Vector3().fromArray(room.look));updateAngles();
 }
 if(next==='cinematic'){cinemaTime=0;selected=null;if(reduced){setMode('orbit');document.querySelector('#modeHint').textContent='Movimiento reducido: presentación en vista fija';return;}}
 document.querySelectorAll('[data-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.mode===mode)));
 document.querySelector('#walkControls').hidden=mode!=='walk';
 document.querySelector('#modeHint').textContent=hints[mode];
 document.querySelector('#selection').textContent=mode==='orbit'?'Vista general':mode==='cinematic'?'Presentación cinematográfica':rooms.find(r=>r.id===selected)?.label||'Exploración libre';
 document.querySelectorAll('[data-room]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.room===selected)));
}
function selectRoom(id){const room=rooms.find(r=>r.id===id);if(!room)return;selected=id;setMode('walk');}
document.querySelectorAll('[data-mode]').forEach(b=>b.addEventListener('click',()=>setMode(b.dataset.mode)));
document.querySelectorAll('[data-room]').forEach(b=>b.addEventListener('click',()=>selectRoom(b.dataset.room)));
document.querySelector('#reset').addEventListener('click',()=>setMode('orbit'));

const markerButtons=rooms.map((room,i)=>{
 const b=document.createElement('button');b.className='marker';b.textContent=String(i+1).padStart(2,'0');b.setAttribute('aria-label','Entrar a '+room.label);b.dataset.hotspot=room.id;b.addEventListener('click',()=>selectRoom(room.id));document.querySelector('#markers').append(b);return b;
});
const raycaster=new THREE.Raycaster();let pointer=null;
canvas.addEventListener('pointerdown',e=>{canvas.focus({preventScroll:true});pointer={id:e.pointerId,x:e.clientX,y:e.clientY,lastX:e.clientX,lastY:e.clientY,moved:false};if(mode==='walk')canvas.setPointerCapture(e.pointerId);});
canvas.addEventListener('pointermove',e=>{
 if(!pointer||pointer.id!==e.pointerId)return;
 if(Math.hypot(e.clientX-pointer.x,e.clientY-pointer.y)>5)pointer.moved=true;
 if(mode==='walk'){yaw+=(e.clientX-pointer.lastX)*.004;pitch=THREE.MathUtils.clamp(pitch-(e.clientY-pointer.lastY)*.004,-1.15,1.15);look();}
 pointer.lastX=e.clientX;pointer.lastY=e.clientY;
});
canvas.addEventListener('pointerup',e=>{
 if(!pointer||pointer.id!==e.pointerId)return;
 if(!pointer.moved){const r=canvas.getBoundingClientRect();raycaster.setFromCamera(new THREE.Vector2((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1),camera);const hit=raycaster.intersectObjects(model.markers)[0];if(hit)selectRoom(hit.object.userData.room);}
 pointer=null;
});
canvas.addEventListener('pointercancel',()=>{pointer=null;});
const movementKeys=new Set(['w','a','s','d','arrowup','arrowleft','arrowdown','arrowright']);
addEventListener('keydown',e=>{
 if(/INPUT|SELECT|TEXTAREA/.test(e.target.tagName))return;
 if(e.key==='Escape'){setMode('orbit');return;}
 const key=e.key.toLowerCase();if(mode==='walk'&&movementKeys.has(key)){e.preventDefault();keys.add(key);}
});
addEventListener('keyup',e=>keys.delete(e.key.toLowerCase()));
function clearInput(){keys.clear();pad.clear();pointer=null;}
addEventListener('blur',clearInput);document.addEventListener('visibilitychange',clearInput);
for(const button of document.querySelectorAll('[data-move]')){
 button.addEventListener('pointerdown',e=>{e.preventDefault();pad.add(button.dataset.move);button.setPointerCapture(e.pointerId);});
 for(const event of ['pointerup','pointercancel','lostpointercapture'])button.addEventListener(event,()=>pad.delete(button.dataset.move));
}
const resize=new ResizeObserver(()=>{const {width,height}=viewport.getBoundingClientRect();renderer.setSize(width,height,false);camera.aspect=width/height;camera.updateProjectionMatrix();if(mode==='orbit')resetOrbit();});resize.observe(viewport);
resetOrbit();setMode('orbit');
const clock=new THREE.Clock();let frame;
function animate(){
 if(disposed)return;
 const dt=Math.min(clock.getDelta(),.05);
 if(!document.hidden){
  if(mode==='orbit')controls.update();
  if(mode==='walk'){
   let forward=Number(keys.has('w')||keys.has('arrowup')||pad.has('forward'))-Number(keys.has('s')||keys.has('arrowdown')||pad.has('back'));
   let side=Number(keys.has('d')||keys.has('arrowright')||pad.has('right'))-Number(keys.has('a')||keys.has('arrowleft')||pad.has('left'));
   const length=Math.hypot(forward,side)||1;forward/=length;side/=length;
   const delta=dt*2.2;
   const result=moveWithCollisions(camera.position,(Math.sin(yaw)*forward+Math.cos(yaw)*side)*delta,(-Math.cos(yaw)*forward+Math.sin(yaw)*side)*delta,model.obstacles);
   camera.position.x=result.x;camera.position.z=result.z;
  }
  if(mode==='cinematic'){
   cinemaTime+=dt;const progress=Math.min(cinemaTime/24,1)*(points.length-1);const index=Math.min(Math.floor(progress),points.length-2);let t=progress-index;t=t*t*(3-2*t);
   camera.position.lerpVectors(new THREE.Vector3().fromArray(points[index].p),new THREE.Vector3().fromArray(points[index+1].p),t);
   camera.lookAt(new THREE.Vector3().fromArray(points[index].t).lerp(new THREE.Vector3().fromArray(points[index+1].t),t));
   if(cinemaTime>=24)setMode('orbit');
  }
  renderer.render(scene,camera);
  const r=canvas.getBoundingClientRect();
  model.markers.forEach((mesh,i)=>{const projected=mesh.position.clone().project(camera);const button=markerButtons[i];button.hidden=mode!=='orbit'||projected.z<0||projected.z>1||Math.abs(projected.x)>1||Math.abs(projected.y)>1;button.style.left=(projected.x*.5+.5)*r.width+'px';button.style.top=(-projected.y*.5+.5)*r.height+'px';});
 }
 frame=requestAnimationFrame(animate);
}
animate();
// Solo observación para pruebas; los cambios de modo se prueban mediante controles visibles.
window.ORA3D={getSnapshot:()=>({mode,selected,provisional:true,position:camera.position.toArray(),floor:floorId,wallColor:'#'+model.materials.walls.color.getHexString(),cinemaTime,geometries:renderer.info.memory.geometries,drawCalls:renderer.info.render.calls,version:THREE.REVISION})};
addEventListener('pagehide',event=>{
 if(event.persisted){clearInput();return;}
 if(disposed)return;
 disposed=true;cancelAnimationFrame(frame);clearInput();resize.disconnect();controls.dispose();
 const geometries=new Set(),materials=new Set();scene.traverse(o=>{if(o.geometry)geometries.add(o.geometry);if(o.material)for(const m of Array.isArray(o.material)?o.material:[o.material])materials.add(m);});
 geometries.forEach(g=>g.dispose());materials.forEach(m=>m.dispose());oakTexture.dispose();renderer.dispose();
});
