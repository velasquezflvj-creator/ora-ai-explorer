import * as THREE from 'three';
import { box } from './collision.mjs';
export const rooms = [
  { id: 'living', label: 'Sala', point: [-1.5, 1.55, 2], look: [-3.8, 1.1, 2.7], marker: [-3, .8, 1.4] },
  { id: 'kitchen', label: 'Cocina', point: [2.1, 1.55, 1.5], look: [5, 1, 2.4], marker: [3.4, .8, 1.4] },
  { id: 'bedroom', label: 'Habitación', point: [-1.5, 1.55, -1.7], look: [-4, 1, -3], marker: [-3, .8, -1.7] },
  { id: 'bathroom', label: 'Baño', point: [2.8, 1.55, -1.8], look: [4.7, .9, -3.7], marker: [3.6, .8, -2.1] },
];
export function createDemoModel() {
  const group = new THREE.Group(); group.name = 'provisional-demo-not-pinares';
  const obstacles = [];
  const walls = new THREE.MeshStandardMaterial({ color: '#ede6d8', roughness: .85, side: THREE.DoubleSide });
  const floor = new THREE.MeshStandardMaterial({ color: '#c1a27c', roughness: .72 });
  const wood = new THREE.MeshStandardMaterial({ color: '#82684c', roughness: .65 });
  const cream = new THREE.MeshStandardMaterial({ color: '#e2dfce', roughness: .95 });
  const green = new THREE.MeshStandardMaterial({ color: '#718775', roughness: .9 });
  const dark = new THREE.MeshStandardMaterial({ color: '#33483f', roughness: .55 });
  const metal = new THREE.MeshStandardMaterial({ color: '#b8a472', roughness: .3, metalness: .6 });
  function block(name, x, y, z, w, h, d, material, solid = false) {
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), material);
    mesh.name = name; mesh.position.set(x, y, z); mesh.castShadow = true; mesh.receiveShadow = true;
    group.add(mesh); if (solid) obstacles.push(box(x, z, w, d)); return mesh;
  }
  block('plinth',0,-.2,0,12.5,.35,10.5,cream);
  block('floor',0,-.015,0,12,.1,10,floor);
  // Fachada abierta y antepechos ficticios: maqueta expositiva, no reconstrucción CAD.
  block('north',0,1.4,-5,12,2.8,.16,walls,true);
  block('west',-6,1.4,0,.16,2.8,10,walls,true);
  block('east',6,.6,0,.16,1.2,10,walls,true);
  block('south',0,.3,5,12,.6,.16,walls,true);
  for (const [x,w] of [[-4.1,3.8],[.7,3],[4.8,2.4]]) block('divider-z',x,1.4,0,w,2.8,.14,walls,true);
  for (const [z,d] of [[-4.3,1.4],[-.5,3.4],[3.8,2.4]]) block('divider-x',0,1.4,z,.14,2.8,d,walls,true);
  // Dinteles: visuales, sin bloquear los pasos a la altura de los ojos.
  for(const x of [-1.5,2.9]) block('door-lintel',x,2.6,0,1.4,.4,.14,walls);
  for(const z of [-2.9,1.9]) block('door-lintel',0,2.6,z,.14,.4,1.4,walls);
  block('sofa-base',-4.1,.35,3.5,3,.55,1,green,true);
  block('sofa-back',-4.1,.78,3.95,3,.5,.15,green);
  for (const x of [-5,-4.1,-3.2]) block('cushion',x,.67,3.5,.82,.15,.75,cream);
  block('coffee-table',-3.4,.35,2,1.2,.12,.7,wood,true);
  block('rug',-3.4,.05,2.4,3.4,.02,2.4,cream);
  block('kitchen-base',5.3,.5,2.7,.85,1,3,dark,true);
  block('worktop',5.3,1.04,2.7,1,.08,3.1,cream);
  block('island',3.2,.48,3.1,1.8,.96,.8,wood,true);
  block('island-top',3.2,1,3.1,1.95,.08,.95,cream);
  block('bed-frame',-3.8,.3,-3.2,2,.4,2.5,wood,true);
  block('mattress',-3.8,.61,-3.2,1.95,.3,2.4,cream);
  block('bed-cover',-3.8,.79,-2.9,1.96,.05,1.7,green);
  for(const x of [-4.3,-3.3]) block('pillow',x,.85,-4,.8,.15,.45,cream);
  block('headboard',-3.8,.8,-4.5,2.2,1.2,.12,wood);
  block('vanity',1.2,.45,-4.4,1.4,.9,.65,wood,true);
  block('basin',1.2,.95,-4.4,.8,.1,.5,cream);
  block('bath',4.7,.3,-3.5,1.5,.6,2,cream,true);
  block('bath-water',4.7,.61,-3.5,1.17,.03,1.6,new THREE.MeshStandardMaterial({color:'#a9c7bf',roughness:.2}));
  block('tap',1.2,1.1,-4.65,.07,.25,.07,metal);
  const markers = rooms.map((room,i)=>{
    const mesh = new THREE.Mesh(new THREE.SphereGeometry(.16,16,12),new THREE.MeshStandardMaterial({color:'#b79654',emissive:'#503714',emissiveIntensity:.35}));
    mesh.position.fromArray(room.marker);mesh.userData.room = room.id;mesh.name = 'hotspot-'+room.id;group.add(mesh);return mesh;
  });
  return {group,obstacles,materials:{walls,floor},markers,rooms};
}
