// Entorno exterior CONCEPTUAL del apartamento 102. No representa la vista real del proyecto: el visor lo
// rotula así. Reemplaza el paisaje de bloques del 104 (que no se modifica) por:
//   - un cielo y un terreno fotográficos proyectados (HDRI «parque» de Poly Haven, CC0, vía pmndrs/assets),
//     que también iluminan y se reflejan en los materiales;
//   - árboles y arbustos tridimensionales generados con ez-tree (MIT, Daniel Greenheck), con corteza de
//     ambientCG (CC0) y hojas con transparencia;
//   - un receptor de sombras sobre el terreno, para que árboles y edificio asienten.
// Todo se carga después de mostrar el apartamento (carga progresiva) y se escala según la calidad gráfica.
import * as THREE from 'three';
import { Sky } from 'three/addons/objects/Sky.js';
import { GroundedSkybox } from 'three/addons/objects/GroundedSkybox.js';
import { HDRLoader } from 'three/addons/loaders/HDRLoader.js';
import { Tree, TreePreset } from './vendor/ez-tree/index.js';

export const NIVEL_TERRENO = -3.2;   // supuesto conceptual: el apartamento se ve a un nivel sobre un jardín

function mulberry(seed) { return () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const b64buf = b64 => { const s = atob(b64), u = new Uint8Array(s.length); for (let i = 0; i < s.length; i++) u[i] = s.charCodeAt(i); return u.buffer; };
function imgTex(b64, mime, srgb) {
  const img = new Image(); const t = new THREE.Texture(img);
  img.onload = () => { t.needsUpdate = true; }; img.src = `data:${mime};base64,${b64}`;
  t.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace; t.wrapS = t.wrapT = THREE.RepeatWrapping;
  return t;
}

export function crearEntorno({ sunDir, W, H, exterior = null, calidad = 'media', poke = () => {} }) {
  const g = new THREE.Group(); g.name = 'ENTORNO_conceptual';
  const rnd = mulberry(102);
  const Y = NIVEL_TERRENO;

  // cielo físico de respaldo (se ve solo mientras carga el HDRI o si no está disponible)
  const sky = new Sky(); sky.scale.setScalar(900);
  const u = sky.material.uniforms;
  u.turbidity.value = 5.5; u.rayleigh.value = 1.1; u.mieCoefficient.value = 0.004; u.mieDirectionalG.value = 0.82;
  u.sunPosition.value.copy(sunDir).multiplyScalar(400);
  g.add(sky);
  const suelo = new THREE.Mesh(new THREE.CircleGeometry(300, 64).rotateX(-Math.PI / 2), new THREE.MeshLambertMaterial({ color: '#7b8a5c' }));
  suelo.position.y = Y - 0.02; g.add(suelo);

  // receptor de sombras sobre el terreno (invisible salvo la sombra)
  const sombra = new THREE.Mesh(new THREE.PlaneGeometry(90, 90).rotateX(-Math.PI / 2), new THREE.ShadowMaterial({ opacity: 0.32 }));
  sombra.position.y = Y + 0.005; sombra.receiveShadow = true; g.add(sombra);

  // zócalo bajo el apartamento (conceptual) y franja de fachada
  const conc = new THREE.MeshStandardMaterial({ color: '#d6d0c6', roughness: 0.9 });
  const zocalo = new THREE.Mesh(new THREE.BoxGeometry(W + 0.02, -0.13 - Y, H + 0.02), conc);
  zocalo.position.set(0, (Y - 0.13) / 2, 0); zocalo.receiveShadow = zocalo.castShadow = true; g.add(zocalo);
  const banda = new THREE.Mesh(new THREE.BoxGeometry(W + 0.06, 0.12, H + 0.06), new THREE.MeshStandardMaterial({ color: '#9b958c', roughness: 0.8 }));
  banda.position.y = -0.19; g.add(banda);

  // galería de acceso conceptual frente a la puerta principal (el DWG del apartamento no la incluye)
  const gal = new THREE.Group(); gal.name = 'ENTORNO_galeria';
  const gw = 16, gd = 1.6, gx = 0.2, gz = -H / 2 - gd / 2;
  const std = (c, r = 0.85) => new THREE.MeshStandardMaterial({ color: c, roughness: r });
  const piso = new THREE.Mesh(new THREE.BoxGeometry(gw, 0.14, gd), std('#d3cdc3')); piso.position.set(gx, -0.07, gz); piso.receiveShadow = true; gal.add(piso);
  const losa = new THREE.Mesh(new THREE.BoxGeometry(gw, 0.14, gd + 0.3), std('#f1efea')); losa.position.set(gx, 2.47, gz - 0.15); losa.castShadow = true; gal.add(losa);
  const baranda = new THREE.Mesh(new THREE.BoxGeometry(gw, 0.04, 0.04), std('#2a2a2c', 0.5)); baranda.position.set(gx, 1.0, gz - gd / 2 + 0.03); gal.add(baranda);
  for (let x = -7; x <= 8; x += 1.5) { const p = new THREE.Mesh(new THREE.BoxGeometry(0.025, 1.0, 0.025), baranda.material); p.position.set(x, 0.5, gz - gd / 2 + 0.03); gal.add(p); }
  const muroMat = std('#ebe6de');
  for (const [x0, x1] of [[gx - gw / 2, -W / 2], [W / 2, gx + gw / 2]]) {
    const mw = new THREE.Mesh(new THREE.BoxGeometry(x1 - x0, 2.4, 0.15), muroMat); mw.position.set((x0 + x1) / 2, 1.2, -H / 2 + 0.075); gal.add(mw);
  }
  const luzGal = new THREE.Mesh(new THREE.BoxGeometry(0.6, 0.02, 0.12), new THREE.MeshBasicMaterial({ color: '#fff1d8' }));
  luzGal.position.set(-W / 2 + 0.65, 2.39, gz); gal.add(luzGal);
  g.add(gal);

  const fog = new THREE.Fog('#dfe4e2', 45, 320);
  const estado = { hdr: null, skybox: null, rot: 0, arboles: 0, listo: false };

  // ---------------------------------------------------------------- HDRI proyectado
  function cargarHDR() {
    if (!exterior?.hdr) return;
    const td = new HDRLoader().setDataType(THREE.HalfFloatType).parse(b64buf(exterior.hdr));
    const tex = new THREE.DataTexture(td.data, td.width, td.height, THREE.RGBAFormat, td.type);
    tex.colorSpace = THREE.LinearSRGBColorSpace; tex.minFilter = tex.magFilter = THREE.LinearFilter; tex.generateMipmaps = false;
    tex.flipY = true; tex.mapping = THREE.EquirectangularReflectionMapping; tex.needsUpdate = true;
    // gira el HDRI para que su sol coincida con el sol del visor (sombras y reflejos coherentes)
    const [su, sv] = exterior.sol_uv;                    // posición del sol en la imagen (0..1, v desde arriba)
    const az = (su - 0.5) * 2 * Math.PI;                 // convención equirectangular de three.js
    const azS = Math.atan2(sunDir.z, sunDir.x);
    estado.rot = az - azS;
    const sb = new GroundedSkybox(tex, exterior.altura_camara || 4, 160, 96);
    sb.position.y = Y + (exterior.altura_camara || 4); sb.rotation.y = estado.rot;
    sb.material.fog = false; sb.material.toneMapped = true;
    g.add(sb); sky.visible = false; suelo.visible = false;
    estado.hdr = tex; estado.skybox = sb;
  }

  // ---------------------------------------------------------------- árboles y arbustos (ez-tree)
  function cargarArboles() {
    if (!exterior?.hojas) return;
    const corteza = { color: imgTex(exterior.corteza.color, 'image/jpeg', true), normal: imgTex(exterior.corteza.normal, 'image/jpeg', false), roughness: imgTex(exterior.corteza.rough, 'image/jpeg', false), ao: null };
    const hojas = Object.fromEntries(Object.entries(exterior.hojas).map(([k, b]) => [k, imgTex(b, 'image/png', true)]));
    const plantilla = (preset, hoja, seed, alto, tinte) => {
      const t = new Tree(); t.options.copy(JSON.parse(JSON.stringify(TreePreset[preset])));
      t.options.seed = seed; t.options.bark.maps = corteza; t.options.bark.textured = true;
      t.options.leaves.map = hojas[hoja] || Object.values(hojas)[0]; t.options.leaves.tint = tinte;
      t.options.leaves.count = Math.round(t.options.leaves.count * 1.6); t.options.leaves.size *= 1.15;   // copas más llenas
      t.generate();
      const w = new THREE.Group();                       // envoltura simple: se clona compartiendo geometría y materiales
      t.traverse(o => { if (o.isMesh && o.geometry?.attributes?.position?.count) { const c = o.clone(); c.castShadow = c.receiveShadow = true; w.add(c); } });
      const bb = new THREE.Box3().setFromObject(w); const s = alto / Math.max(0.01, bb.max.y - bb.min.y);
      w.scale.setScalar(s);
      return w;
    };
    const N = calidad === 'alta' ? { arb: 13, arbu: 12 } : calidad === 'baja' ? { arb: 5, arbu: 5 } : { arb: 9, arbu: 8 };
    const tipos = [plantilla('Oak Medium', 'oak', 11, 9.5, 0xb9cf9a), plantilla('Ash Medium', 'ash', 23, 11, 0xb4c994), plantilla('Oak Large', 'oak', 41, 12.5, 0xaec58e)];
    const arbustos = [plantilla('Bush 1', 'ash', 5, 1.4, 0xa9c08a), plantilla('Bush 2', 'oak', 8, 1.2, 0xb2c693)];
    const pos = [];
    const libre = (x, z, r) => pos.every(([a, b, c]) => Math.hypot(x - a, z - b) > r + c);
    let n = 0, guard = 0;
    while (n < N.arb && guard++ < 500) {          // arboleda: marco lateral y fondo, con la vista del balcón despejada
      const a = rnd() * Math.PI * 2, r = 11 + Math.pow(rnd(), 0.7) * 26;
      const x = Math.cos(a) * r, z = Math.sin(a) * r + 2;
      if (z > 3 && Math.abs(x + 2.5) < 4.5 + (z - 3) * 0.12) continue;     // cono de vista del balcón
      if (Math.abs(x) < 8 && Math.abs(z) < 8) continue;
      if (!libre(x, z, 4)) continue;
      const t = tipos[n % tipos.length].clone(); const k = 0.8 + rnd() * 0.45;
      t.scale.multiplyScalar(k); t.rotation.y = rnd() * 6.28; t.position.set(x, Y, z); g.add(t); pos.push([x, z, 4]); n++;
    }
    for (let i = 0, gi = 0; i < N.arbu && gi < 400; gi++) {               // arbustos junto al zócalo y en el jardín
      const lado = i % 3; let x, z;
      if (lado === 0) { x = -W / 2 - 1.2 - rnd() * 2.5; z = -H / 2 + rnd() * (H + 6); }
      else if (lado === 1) { x = W / 2 + 1.2 + rnd() * 2.5; z = -H / 2 + rnd() * (H + 6); }
      else { x = -W / 2 + rnd() * (W + 8) - 4; z = H / 2 + 4 + rnd() * 5; }
      if (!libre(x, z, 1.0)) continue;
      const b = arbustos[i % arbustos.length].clone(); b.scale.multiplyScalar(0.8 + rnd() * 0.6); b.rotation.y = rnd() * 6.28; b.position.set(x, Y, z); g.add(b); pos.push([x, z, 1]); i++;
    }
    estado.arboles = n;
  }

  // ---------------------------------------------------------------- hora del día
  function setHora(h) {
    const sb = estado.skybox;
    if (sb) sb.material.color.set(h === 'atardecer' ? '#d3a07c' : '#ffffff');
    fog.color.set(h === 'atardecer' ? '#d9b49a' : '#dfe4e2');
    u.turbidity.value = h === 'atardecer' ? 9 : 5.5;
  }

  // carga progresiva: primero el HDRI y luego los árboles, cada uno en su propio cuadro
  function cargar(paso = 0) {
    try {
      if (paso === 0) cargarHDR();
      if (paso === 1) cargarArboles();
    } catch (e) { console.warn('entorno', e); }
    poke(6);
    if (paso < 1) setTimeout(() => cargar(paso + 1), 60); else estado.listo = true;
  }

  return { group: g, fog, sky, estado, cargar, setHora };
}
