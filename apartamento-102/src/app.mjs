// ORA AI · Apartamento 102, Torre 1 — PROPUESTA DE REDISTRIBUCIÓN (rediseño conceptual, no planta verificada).
// Del DWG se conservan la envolvente, los vanos de fachada, el acceso y los ductos; la distribución interior,
// los baños, la cocina y el balcón son propuestas; acabados, mobiliario y entorno son ilustrativos.
// Visor derivado del del apartamento 104; texturas, acabados y entorno se comparten con él.
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { GTAOPass } from 'three/addons/postprocessing/GTAOPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { Reflector } from 'three/addons/objects/Reflector.js';
import { RectAreaLightUniformsLib } from 'three/addons/lights/RectAreaLightUniformsLib.js';
import { setTextureSize, anisotropy, cacheSize } from '../../apartamento-104/src/texturas.mjs';
import { RECETAS, OPCIONES, PRESETS, FIJOS, opcion, ambiente as ambienteBase } from '../../apartamento-104/src/acabados.mjs';
import { crearEntorno, NIVEL_TERRENO } from './entorno102.mjs';
import { initPBR, aplicar102, texturaPBR, OPC_PREMIUM, AMB_PREMIUM, PRESET_PREMIUM } from './pbr102.mjs';

// ------------------------------------------------------------------ propuesta monocromática (solo en el 102)
// Paleta en blanco, grises y negro mate, pedida para la propuesta con barra. Ilustrativa, no contractual.
Object.assign(RECETAS, {
  microcemento_gris: { gen: 'microcemento', base: '#bdbab4', sombra: '#9c9993', seed: 35, rough: 0.5 },
  negro_mate: { gen: 'chapa', claro: '#2c2c2e', oscuro: '#232325', seed: 57, contraste: 0.1, rough: 0.7 },
  marmol_gris: { gen: 'marmol', base: '#e9e8e5', veta: '#8a8986', veta2: '#b5b4b0', intensidad: 0.7, seed: 27, rough: 0.14 },
  baldosa_gris_grande: { gen: 'piedra', base: '#a7a5a1', veta: '#c2c0bb', lx: 0.6, ly: 1.2, junta: '#8d8b87', rough: 0.3, vetas: 0.2, seed: 19 },
  piso_bano_gris: { gen: 'piedra', base: '#6f6e6b', veta: '#85847f', lx: 0.6, ly: 0.6, junta: '#5a5956', rough: 0.4, vetas: 0.2, seed: 20 },
  tapete_mono: { gen: 'tapete', base: '#8e8c88', linea: '#b5b3ae', seed: 84 },
  cuadro_mono: { gen: 'cuadro', fondo: '#ecebe8', a: '#1d1d1f', b: '#8d8c88', c: '#c9c8c4', seed: 104 },
});
OPCIONES.piso.push({ id: 'microcemento_gris', nombre: 'Microcemento gris perla', muestra: 'linear-gradient(135deg,#c4c1bb,#a19e98)', m: { piso_madera: { t: 'microcemento_gris', n: 0.4 }, guardaescoba: { c: '#2c2c2e', r: 0.6 } } });
OPCIONES.muros.push({ id: 'blanco_puro', nombre: 'Blanco puro', muestra: '#f4f4f2', m: { muro: { t: 'pintura', c: '#f6f6f4', n: 0.5 } } });
OPCIONES.cocina.push({ id: 'negro_marmol', nombre: 'Negro mate y mármol gris', muestra: 'linear-gradient(90deg,#2c2c2e 50%,#e2e1de 50%)',
  m: { gabinete_cocina: { t: 'negro_mate', r: 0.7 }, meson: { t: 'marmol_gris', n: 0.2 }, salpicadero: { t: 'marmol_gris', n: 0.2 } } });
OPCIONES.bano.push({ id: 'gris_negro', nombre: 'Piedra gris y negro mate', muestra: 'linear-gradient(90deg,#a7a5a1 50%,#2c2c2e 50%)',
  m: { revestimiento_bano: { t: 'baldosa_gris_grande', n: 0.6 }, piso_ceramica: { t: 'piso_bano_gris', n: 0.5 }, mueble_bano: { t: 'negro_mate', r: 0.7 }, meson_bano: { t: 'marmol_gris', n: 0.2 } } });
PRESETS.unshift({ id: 'monocromatica', nombre: 'Monocromática elegante', corto: 'Monocromática', descripcion: 'Blanco, grises y negro mate; mármol gris y metal negro', piso: 'microcemento_gris', muros: 'blanco_puro', cocina: 'negro_marmol', bano: 'gris_negro' });
const AMB_MONO = {
  tela_sofa: { t: 'tela_lino', c: '#b9b8b5' }, tela_acento: { t: 'tela_lino', c: '#3a3a3c' }, tela_cama: { t: 'tela_lino', c: '#f2f2f0' },
  tela_silla: { t: 'tela_boucle', c: '#2f2f31' }, tela_cortina: { t: 'tela_lino', c: '#e6e5e2' }, toalla: { t: 'tela_boucle', c: '#d9d8d5' },
  madera_mueble: { t: 'negro_mate' }, laca_mueble: { t: 'laca_blanca', c: '#f1f1ef' }, carpinteria: { t: 'negro_mate' }, marco_puerta: { t: 'negro_mate' },
  puerta_entrada: { t: 'negro_mate' }, laton: { c: '#1d1d1f', r: 0.45, mt: 0.8 }, textil_tapete: { t: 'tapete_mono' }, cuadro: { t: 'cuadro_mono' },
  maceta: { c: '#2a2a2c', r: 0.6 }, ceramica_deco: { c: '#efeeeb', r: 0.35 },
};
for (const t of ['piso', 'muros', 'cocina', 'bano']) OPCIONES[t].unshift(OPC_PREMIUM[t]);
PRESETS.unshift(PRESET_PREMIUM);
const ambiente = id => (id === 'monocromatica' ? AMB_MONO : id === 'calida_premium' ? AMB_PREMIUM : ambienteBase(id));
const aplicar = aplicar102;   // entiende tanto las recetas del 104 como las texturas propias del 102

const DATA = window.APTO102;
const geo = DATA.geo;
// Propuesta de balcón: NO proviene del DWG; se muestra siempre rotulada como propuesta.
const PROP = DATA.propuesta || null;
let balcony = !!PROP;
const [, , W, H] = geo.envolvente_exterior;
const EYE = 1.6;
const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
const $ = s => document.querySelector(s);
const $$ = s => [...document.querySelectorAll(s)];
const params = new URLSearchParams(location.search);
const coarse = matchMedia('(pointer: coarse)').matches;
const compact = matchMedia('(max-width: 700px), (max-height: 560px), (max-width: 900px) and (orientation: portrait)');

// planta local (x este, y norte) ⇄ escena (X este, Z sur)
const toScene = (x, y, h = 0) => new THREE.Vector3(x - W / 2, h, H / 2 - y);
const toPlan = v => ({ x: v.x + W / 2, y: H / 2 - v.z });

// render bajo demanda: sin movimiento ni cambios, la escena no se vuelve a dibujar (ahorra batería)
let dirty = 90;
const poke = (n = 40) => { dirty = Math.max(dirty, n); };

// ------------------------------------------------------------------ calidad
// alta: oclusión ambiental (GTAO) + MSAA, sombras 2048. media: render directo, sombras 1024 (teléfonos y tabletas).
let quality = ['alta', 'media', 'baja'].includes(params.get('calidad')) ? params.get('calidad') : (coarse || innerWidth < 900 ? 'media' : 'alta');
const qualityPinned = params.has('calidad');
setTextureSize(quality === 'alta' && !compact.matches ? 1024 : 512);

// ------------------------------------------------------------------ renderizador
const canvas = $('#scene');
let renderer;
try {
  renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
} catch (error) {
  $('#error').hidden = false; document.body.classList.remove('is-loading'); throw error;
}
const pixelRatio = () => Math.min(devicePixelRatio, quality === 'alta' ? 2 : quality === 'baja' ? 1 : (innerWidth < 700 ? 1.5 : 1.6));
renderer.setPixelRatio(pixelRatio());
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.NeutralToneMapping;   // Khronos PBR Neutral: colores de material fieles, como una foto de arquitectura
renderer.toneMappingExposure = 0.92;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.shadowMap.autoUpdate = false;   // una actualización por cuadro (no por cada reflejo)
RectAreaLightUniformsLib.init();

const scene = new THREE.Scene();
const navy = new THREE.Color('#050a14');
scene.background = navy;
const pmrem = new THREE.PMREMGenerator(renderer);
const roomEnv = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
scene.environment = roomEnv;
scene.environmentIntensity = 0.45;

const camera = new THREE.PerspectiveCamera(42, 1, 0.05, 1200);
const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true; controls.dampingFactor = 0.08;
controls.minDistance = 2.6; controls.maxDistance = 40; controls.maxPolarAngle = Math.PI * 0.46;
controls.target.set(0, 0.6, 0);

// luces: sol de la tarde entrando por la fachada de ventanas (sur del dibujo), cielo y luces cálidas interiores
const SUN_DIR = new THREE.Vector3(-6, 8.5, 8).normalize();
const hemi = new THREE.HemisphereLight('#f6efe2', '#2a2621', 0.85); scene.add(hemi);
const sun = new THREE.DirectionalLight('#fff0d8', 2.6);
sun.position.copy(SUN_DIR).multiplyScalar(14); sun.castShadow = true;
const shadowRes = () => (quality === 'alta' ? 2048 : quality === 'baja' ? 512 : 1024);
sun.shadow.mapSize.set(shadowRes(), shadowRes());
Object.assign(sun.shadow.camera, { left: -6.6, right: 6.6, top: 6.6, bottom: -6.6, near: 2, far: 32 });
sun.shadow.bias = -0.0003; sun.shadow.normalBias = 0.025; sun.shadow.radius = 3;
scene.add(sun); scene.add(sun.target);

// luces interiores (cálidas, 2.700–3.000 K) y luz de día por las ventanas. Para que el sombreado sea fluido
// también en teléfonos, un grupo fijo de 4 luces puntuales y 2 luces de ventana se asigna a las fuentes más
// cercanas al visitante, con transición suave de intensidad.
const LIGHTS = {   // [x, y, intensidad] — posiciones bajo las luminarias del GLB
  social: [[1.37, 1.2, 2.2], [1.15, 3.75, 1.6], [1.6, 6.3, 1.6]], hall: [[3.9, 4.25, 0.9]], habitacion_2: [[4.0, 1.9, 1.5]], principal: [[6.5, 2.4, 1.7]],
  bano_principal: [[5.75, 6.0, 1.0]], vestier: [[7.1, 6.0, 0.7]], bano_social: [[4.2, 5.8, 0.8]], ropas: [[3.1, 5.3, 0.5]],
};
const SRC_P = Object.values(LIGHTS).flat().map(([x, y, k]) => ({ pos: toScene(x, y, 2.25), k }));
const SALA_V = geo.ventanas.reduce((a, b) => (b.ancho > a.ancho ? b : a));
const SRC_R = geo.ventanas.map(w => {
  const sala = w === SALA_V, sur = w.fachada === 'sur';
  const width = (sur ? w.x1 - w.x0 : w.y1 - w.y0) - 0.08;
  const pos = sur ? toScene((w.x0 + w.x1) / 2, w.y1 + 0.02, 1.5) : toScene(w.x0 - 0.02, (w.y0 + w.y1) / 2, 1.5);
  const look = sur ? toScene((w.x0 + w.x1) / 2, w.y1 + 2, 1.2) : toScene(w.x0 - 2, (w.y0 + w.y1) / 2, 1.2);
  return { sala, width, pos, look, k: sala ? 5 : 4 };
});
const luz = { interior: 1, ventana: 1 };   // multiplicadores de la hora del día
const interiorLights = new THREE.Group(); scene.add(interiorLights);
const windowLights = new THREE.Group(); scene.add(windowLights);
const poolP = Array.from({ length: 4 }, () => { const l = new THREE.PointLight('#ffcf9a', 0, 5.2, 1.8); l.userData = { src: null, k: 0 }; interiorLights.add(l); return l; });
const poolR = Array.from({ length: 2 }, () => { const l = new THREE.RectAreaLight('#e9eff5', 0, 1, 1.15); l.userData = { src: null, k: 0 }; windowLights.add(l); return l; });
function assignPool(pool, sources, ref, apply) {
  const best = sources.map(s => [s, s.pos.distanceToSquared(ref)]).sort((a, b) => a[1] - b[1]).slice(0, pool.length).map(v => v[0]);
  const keep = new Set(pool.map(l => l.userData.src).filter(s => best.includes(s)));
  const spare = pool.filter(l => !keep.has(l.userData.src));
  for (const s of best) if (!keep.has(s)) { const l = spare.shift(); l.userData.src = s; l.intensity = 0; apply(l, s); }
  for (const l of pool) { if (l.userData.src) apply(l, l.userData.src); l.userData.k = l.userData.src ? l.userData.src.k * (l.isRectAreaLight ? luz.ventana : luz.interior) : 0; }
}
function updateLightPool(dt, force) {
  if (force || frame % 8 === 0) {
    assignPool(poolP, SRC_P, camera.position, (l, s) => l.position.copy(s.pos));
    assignPool(poolR, SRC_R, camera.position, (l, s) => { l.position.copy(s.pos); l.width = s.width; l.height = s.sala && balconyOn() ? 1.9 : 1.15; l.lookAt(s.look); });
  }
  let moving = false;
  for (const l of [...poolP, ...poolR]) { const d = l.userData.k - l.intensity; if (Math.abs(d) > 0.01) { l.intensity += d * Math.min(1, dt * 4); moving = true; } else l.intensity = l.userData.k; }
  return moving;
}
interiorLights.visible = windowLights.visible = false;

// maqueta: un plano oscuro que recibe la sombra
const ground = new THREE.Mesh(new THREE.CircleGeometry(26, 64), new THREE.MeshStandardMaterial({ color: '#0b1220', roughness: 1 }));
ground.rotation.x = -Math.PI / 2; ground.position.y = -0.125; ground.receiveShadow = true; scene.add(ground);

// entorno exterior conceptual (no es la vista real del proyecto)
const entorno = crearEntorno({ sunDir: SUN_DIR, W, H, exterior: DATA.exterior, calidad: quality, poke: n => poke(n) });
let envHDR = null;
entorno.group.visible = false; scene.add(entorno.group);

// ------------------------------------------------------------------ posproceso (calidad alta)
let composer = null, gtao = null;
function setupComposer() {
  if (composer || quality !== 'alta') return;
  const size = renderer.getDrawingBufferSize(new THREE.Vector2());
  const rt = new THREE.WebGLRenderTarget(size.x, size.y, { type: THREE.HalfFloatType, samples: 4 });
  composer = new EffectComposer(renderer, rt);
  composer.setPixelRatio(renderer.getPixelRatio()); composer.setSize(innerWidth, innerHeight);
  composer.addPass(new RenderPass(scene, camera));
  gtao = new GTAOPass(scene, camera, innerWidth, innerHeight);
  gtao.output = GTAOPass.OUTPUT.Default; gtao.blendIntensity = 0.9;
  gtao.updateGtaoMaterial({ radius: 0.32, distanceExponent: 1.5, thickness: 1.2, scale: 1.0, samples: 12, distanceFallOff: 1.0, screenSpaceRadius: false });
  gtao.updatePdMaterial({ lumaPhi: 10, depthPhi: 2, normalPhi: 3, radius: 5, rings: 2, samples: 12 });
  // los vidrios y espejos no deben oscurecer lo que está detrás
  const base = gtao._overrideVisibility.bind(gtao);
  gtao._overrideVisibility = function () {
    base(); const cache = this._visibilityCache;
    this.scene.traverse(o => { if (o.visible && ((o.isMesh && o.material?.transparent) || o.isReflector || o.isSky || o === entorno.sky)) { o.visible = false; cache.push(o); } });
    if (entorno.group.visible) { entorno.group.visible = false; cache.push(entorno.group); }   // el exterior (cielo HDRI y hojas con transparencia) no recibe oclusión
  };
  composer.addPass(gtao);
  composer.addPass(new OutputPass());
}
function setQuality(q) {
  if (q === quality) return;
  quality = q;
  if (q !== 'alta' && composer) { composer.dispose?.(); composer = null; gtao = null; }
  renderer.setPixelRatio(pixelRatio()); setupComposer(); resize();
  sun.shadow.mapSize.set(shadowRes(), shadowRes()); sun.shadow.map?.dispose(); sun.shadow.map = null; renderer.shadowMap.needsUpdate = true;
  $$('#layerQuality').forEach(i => { i.checked = q === 'alta'; });
  $$('#calidad button').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.q === q)));
  poke(20);
}

// ------------------------------------------------------------------ modelo
const mats = {};
const groups = { arquitectura: [], aparatos: [], ilustrativo: [], acabados: [], mobiliario: [], cielo: [], propuesta: [], propuesta_mobiliario: [], sin_balcon: [], rediseno: [] };
let model = null;
const stats = { verificados: 0, ilustrativos: 0, nodos: [], categorias: {} };
const huellas = [];          // { node, rects, segs }
const mirrors = [];          // Reflector + espejo base
let ready = false;

function base64ToBuffer(b64) {
  const bin = atob(b64); const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out.buffer;
}

// Muebles de terceros (Khronos glTF-Sample-Assets; créditos en modelo/muebles/CREDITOS.md). El GLB del
// apartamento solo trae su posición (nodos con userData.modelo); se cargan antes y se clonan.
const MUEBLES = {};
const TINTE = {   // tela del sofá, tela de las butacas y madera de las patas, por propuesta de acabados
  calida_premium: { sofa: '#eee6d9', butaca: '#cdbfab', madera: '#b48f68' },
  monocromatica: { sofa: '#c9c8c5', butaca: '#3b3b3e', madera: '#1f1f21' },
  calida: { sofa: '#d3c7b5', butaca: '#a8603e', madera: '#6b4f38' },
  sofisticada: { sofa: '#6a6b6f', butaca: '#8e5b36', madera: '#2f2620' },
  luminosa: { sofa: '#ece8e0', butaca: '#aab69f', madera: '#cdb999' },
};
const mueblesMats = [];
const puertasOcultas = [];   // puerta corrediza oculta de ropas: se abre al acercarse
const PUERTA_ROPAS = (() => { const d = geo.puertas.find(p => p.id === 'ropas'); return d ? { x: (d.rect[0] + d.rect[2]) / 2, y: (d.rect[1] + d.rect[3]) / 2 } : null; })();
function tintMuebles(id) {
  const t = TINTE[id] || TINTE.monocromatica;
  for (const m of mueblesMats) {
    const c = /tela_sofa/.test(m.name) ? t.sofa : /tela_butaca/.test(m.name) ? t.butaca : /madera/.test(m.name) ? t.madera : null;
    if (!c) continue;
    m.color.set(c); if (m.sheenColor) m.sheenColor.set(c).lerp(new THREE.Color('#ffffff'), 0.35);
    if (/tela_sofa/.test(m.name) && id === 'calida_premium') {   // bouclé crema, como en la referencia de la sala
      const nb = texturaPBR('boucle', 'normal'); if (nb && m.normalMap !== nb) { m.userData.n0 = m.userData.n0 || m.normalMap; m.normalMap = nb.clone(); m.normalMap.repeat.set(9, 9); m.normalMap.needsUpdate = true; m.normalScale.set(1.2, 1.2); m.sheenRoughness = 0.9; m.needsUpdate = true; }
    } else if (m.userData.n0 && /tela_sofa/.test(m.name)) { m.normalMap = m.userData.n0; m.needsUpdate = true; }
  }
}
const loadMuebles = Promise.all(Object.entries(DATA.muebles || {}).map(([k, b64]) => new GLTFLoader().parseAsync(base64ToBuffer(b64), '').then(g => { MUEBLES[k] = g.scene; })));

loadMuebles.catch(e => console.warn('muebles', e)).then(() => new GLTFLoader().parse(base64ToBuffer(DATA.glb), '', gltf => {
  model = gltf.scene; scene.add(model);
  const conModelo = []; model.traverse(o => { if (o.userData?.modelo && MUEBLES[o.userData.modelo]) conModelo.push(o); if (o.userData?.corrediza) puertasOcultas.push({ node: o, rec: o.userData.corrediza.recorrido, t: 0 }); });
  for (const o of conModelo) {
    const c = MUEBLES[o.userData.modelo].clone(true); c.scale.setScalar(o.userData.escala || 1); o.add(c);
    c.traverse(q => { if (q.isMesh) { q.castShadow = q.receiveShadow = true; q.userData.mueble = true; if (!mueblesMats.includes(q.material)) mueblesMats.push(q.material); } });
  }
  model.traverse(o => {
    if (o.userData && 'verificado' in o.userData) {
      (groups[o.userData.grupo] || groups.arquitectura).push(o);
      const cat = o.userData.categoria || (o.userData.verificado ? 'verificado' : 'ilustrativo');
      stats.nodos.push({ nombre: o.name, verificado: o.userData.verificado, grupo: o.userData.grupo, categoria: cat });
      stats.categorias[cat] = (stats.categorias[cat] || 0) + 1;
      o.userData.verificado ? stats.verificados++ : stats.ilustrativos++;
      if (o.userData.huella?.length || o.userData.segmentos?.length) huellas.push({ node: o, rects: o.userData.huella || [], segs: o.userData.segmentos || [] });
    }
    if (o.isMesh) {
      const m = o.material, transparent = m.transparent;
      o.castShadow = !transparent && !/Cielo|Piso|Luminarias|Revestimientos|Guardaescobas/.test(o.name) && m.name !== 'cuadro';
      o.receiveShadow = !transparent;
      if (transparent) { m.depthWrite = false; o.renderOrder = 2; }
      if (/^vidrio/.test(m.name)) Object.assign(m, { roughness: 0.03, metalness: 0, envMapIntensity: 1.6 });
      if (m.name === 'luz_calida') { m.emissive.set('#ffd9a8'); m.emissiveIntensity = 2.2; m.toneMapped = true; }
      if (m.name === 'vidrio_opal') { m.emissive.set('#ffe2bd'); m.emissiveIntensity = 0.9; }
      if (m.name === 'tela_visillo') { m.opacity = 0.5; m.depthWrite = false; }
      if (m.name === 'pantalla_lampara') m.emissiveIntensity = 0.8;
      if (!o.userData.mueble) mats[m.name] = m;
    }
  });
  physicalize();
  buildMirrors(); updateMirrors();
  aplicar(mats, FIJOS);
  initPBR(DATA.texturas, { anisotropy: Math.min(8, renderer.capabilities.getMaxAnisotropy()), poke });
  setPreset('calida_premium');
  groups.cielo.forEach(o => { o.visible = false; });
  anisotropy(renderer);
  buildHotspots(); buildPois(); buildDims(); buildTour(); applyLayers(); resetOrbit(true);
  setupComposer(); resize();
  document.body.classList.remove('is-loading');
  ready = true;
  setTimeout(() => entorno.cargar(), 250);   // carga progresiva: HDRI y vegetación después del primer cuadro
}, error => { console.error(error); $('#error').hidden = false; document.body.classList.remove('is-loading'); }));

// materiales físicos: telas con brillo de terciopelo (sheen) y piedras pulidas con capa transparente (clearcoat)
const SHEEN = /^(tela_|textil_tapete|toalla)/, CLEAR = /^(meson|meson_bano|vidrio_negro|electro_blanco|ceramica_blanca|ceramica_calida)$/;
function physicalize() {
  const swap = {};
  for (const [name, m] of Object.entries(mats)) {
    if (!SHEEN.test(name) && !CLEAR.test(name)) continue;
    const p = new THREE.MeshPhysicalMaterial();
    THREE.MeshStandardMaterial.prototype.copy.call(p, m); p.name = name; p.userData = { ...m.userData };
    if (SHEEN.test(name)) Object.assign(p, { sheen: 1, sheenRoughness: 0.75, roughness: Math.max(0.85, m.roughness) }), p.sheenColor.set('#8a8a8a');
    else Object.assign(p, { clearcoat: /ceramica/.test(name) ? 0.5 : /vidrio|electro/.test(name) ? 0.6 : 0.12, clearcoatRoughness: /meson/.test(name) ? 0.35 : 0.1 });   // travertino apomazado: brillo apenas perceptible
    swap[name] = p; mats[name] = p;
  }
  model.traverse(o => { if (o.isMesh && !o.userData.mueble && swap[o.material.name]) o.material = swap[o.material.name]; });
}

// espejos de los baños: reflejo plano real (Reflector) sobre la cara del espejo del GLB
function buildMirrors() {
  for (const [name, face] of [['espejo_principal', 1], ['espejo_social', -1]]) {   // cara hacia +X o −X
    let mesh = null; model.traverse(o => { if (o.isMesh && o.material.name === name) mesh = o; });
    if (!mesh) continue;
    mesh.geometry.computeBoundingBox();
    const bb = mesh.geometry.boundingBox.clone().applyMatrix4(mesh.matrixWorld), size = bb.getSize(new THREE.Vector3()), c = bb.getCenter(new THREE.Vector3());
    const alongX = size.x > size.z;
    const w = alongX ? size.x : size.z;
    const ref = new Reflector(new THREE.PlaneGeometry(w, size.y), { clipBias: 0.003, textureWidth: 512, textureHeight: Math.round(512 * size.y / w), color: 0x777777, multisample: 0 });
    if (alongX) ref.position.set(c.x, c.y, bb.max.z + 0.001);
    else { ref.position.set(face > 0 ? bb.max.x + 0.001 : bb.min.x - 0.001, c.y, c.z); ref.rotation.y = face * Math.PI / 2; }
    ref.name = 'REF_' + name; ref.userData.base = mesh;
    mesh.parent.add(ref); ref.updateMatrixWorld();
    mesh.parent.worldToLocal(ref.position);
    mirrors.push(ref);
  }
}
function updateMirrors() {   // los reflejos planos cuestan un render extra: solo dentro del apartamento
  const on = mode !== 'orbit';
  for (const r of mirrors) { r.visible = on; r.userData.base.visible = !on; }
}

// ------------------------------------------------------------------ acabados ilustrativos (no contractuales)
const fin = { preset: 'calida', piso: 'roble', muros: 'marfil', cocina: 'roble_cuarzo', bano: 'arena', personalizado: false };
function setFinish(tipo, id, fromPreset = false) {
  poke(30);
  const o = opcion(tipo, id); if (!o) return;
  if (!verifiedOnly()) aplicar(mats, o.m);
  fin[tipo] = id; if (!fromPreset) fin.personalizado = true;
  $$(`[data-fin="${tipo}"] button`).forEach(b => b.setAttribute('aria-pressed', String(b.dataset.id === id)));
  syncPresetUi();
}
function setPreset(id) {
  const p = PRESETS.find(v => v.id === id); if (!p) return;
  fin.preset = id; fin.personalizado = false;
  if (!verifiedOnly()) aplicar(mats, ambiente(id));
  tintMuebles(id);
  for (const t of ['piso', 'muros', 'cocina', 'bano']) setFinish(t, p[t], true);
  fin.personalizado = false; syncPresetUi();
}
function syncPresetUi() {
  $$('#presets button').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.id === fin.preset && !fin.personalizado)));
  const p = PRESETS.find(v => v.id === fin.preset);
  const lbl = $('#presetNote'); if (lbl) lbl.textContent = fin.personalizado ? `Personalizada sobre «${p.nombre}»` : p.descripcion;
}
function reapplyFinishes() {   // tras salir de la vista técnica
  aplicar(mats, FIJOS); aplicar(mats, ambiente(fin.preset));
  for (const t of ['piso', 'muros', 'cocina', 'bano']) aplicar(mats, opcion(t, fin[t]).m);
}
for (const p of PRESETS) {
  const b = document.createElement('button'); b.type = 'button'; b.dataset.id = p.id; b.title = `${p.nombre}: ${p.descripcion}`;
  b.innerHTML = `<b>${p.corto}</b>`; b.addEventListener('click', () => setPreset(p.id)); $('#presets').append(b);
}
for (const [tipo, lista] of Object.entries(OPCIONES)) {
  const box = $(`[data-fin="${tipo}"]`); if (!box) continue;
  for (const o of lista) {
    const b = document.createElement('button'); b.type = 'button'; b.dataset.id = o.id; b.title = o.nombre; b.setAttribute('aria-label', `${box.getAttribute('aria-label')}: ${o.nombre}`);
    b.style.background = o.muestra; b.addEventListener('click', () => setFinish(tipo, o.id)); box.append(b);
  }
}

// ------------------------------------------------------------------ espacios: puntos de vista (elección de cámara, no del DWG)
const VIEWS = {
  social: { pos: [2.1, 0.85], look: [1.0, 6.0], orbit: [1.4, 3.8] },
  hall: { pos: [2.45, 4.25], look: [5.2, 4.25], orbit: [4.0, 4.2] },
  habitacion_2: { pos: [3.45, 3.2], look: [4.8, 0.5], orbit: [4.0, 1.9] },
  principal: { pos: [5.7, 4.2], look: [7.6, 2.4], orbit: [6.6, 2.4] },
  vestier: { pos: [7.2, 5.0], look: [7.3, 6.9], orbit: [7.3, 6.1] },
  ropas: { pos: [3.1, 4.3], look: [3.0, 5.6], orbit: [3.1, 5.4] },
  bano_social: { pos: [4.2, 4.95], look: [4.3, 6.9], orbit: [4.2, 6.0] },
  bano_principal: { pos: [5.95, 5.1], look: [5.2, 6.9], orbit: [5.75, 6.0] },
  balcon: { pos: [2.1, -0.3], look: [0.6, -1.4], orbit: [1.4, -0.8] },
};
const BALCON = PROP && { id: 'balcon', nombre: 'Balcón', area_neta_m2: PROP.area_util_m2, piso_rectangulos: [PROP.rect_util], propuesta: true };
const allRooms = () => (BALCON ? [...geo.espacios, BALCON] : geo.espacios);
const roomById = Object.fromEntries(allRooms().map(r => [r.id, r]));
const fmt = n => n.toFixed(2).replace('.', ',');
const fmtDim = n => (Math.abs(n * 100 - Math.round(n * 100)) > 1e-6 && Math.abs(n * 1000 - Math.round(n * 1000)) < 1e-6 ? n.toFixed(3) : n.toFixed(2)).replace('.', ',');   // 2,475 se muestra tal como en el plano
const roomName = r => r.nombre;
const roomNote = r => (r.id === 'principal' ? 'con baño privado y vestier' : '');
function roomAt(p) {
  for (const r of allRooms()) if (r.propuesta && !balconyOn()) continue; else for (const [x0, y0, x1, y1] of r.piso_rectangulos) if (p.x >= x0 && p.x <= x1 && p.y >= y0 && p.y <= y1) return r;
  return null;
}

const hotspots = [];
function buildHotspots() {
  const list = $('#rooms');
  for (const r of allRooms()) {
    const v = VIEWS[r.id];
    const hs = document.createElement('button'); hs.type = 'button'; hs.className = 'hs' + (r.propuesta ? ' prop' : ''); hs.dataset.room = r.id;
    hs.setAttribute('aria-label', `${roomName(r)}${r.propuesta ? ' propuesto' : ''}, ${fmt(r.area_neta_m2)} metros cuadrados`);
    hs.innerHTML = `<i></i><span>${roomName(r)}${r.propuesta ? ' · propuesta' : ''} · ${fmt(r.area_neta_m2)} m²</span>`;
    hs.addEventListener('click', e => { e.stopPropagation(); goRoom(r.id); });
    $('#hotspots').append(hs);
    hotspots.push({ el: hs, room: r, anchor: toScene(v.orbit[0], v.orbit[1], 1.05) });
    const li = document.createElement('li'); const b = document.createElement('button'); b.type = 'button'; b.dataset.room = r.id;
    if (r.propuesta) { li.className = 'prop'; b.title = 'Propuesta: no figura en los planos DWG'; }
    b.innerHTML = `${roomName(r)}${r.propuesta ? ' <small>propuesta</small>' : ''}<em>${fmt(r.area_neta_m2)} m²</em>`; b.addEventListener('click', () => goRoom(r.id));
    li.append(b); list.append(li);
  }
}

// ------------------------------------------------------------------ puntos de interés: qué es verificado, provisional, ilustrativo o propuesta
const CATS = {
  verificado: 'Del DWG', provisional: 'Medida provisional', ilustrativo: 'Ilustrativo', propuesta: 'Propuesta sin validar',
};
const POIS = [
  { id: 'acceso', p: [0.65, 7.42, 1.85], cat: 'verificado', t: 'Puerta de acceso · 1,00 m', d: 'Vano y posición del DWG (P2). La altura de 2,10 m es provisional; la hoja es ilustrativa.' },
  { id: 'cocina', p: [2.1, 6.9, 1.25], cat: 'propuesta', t: 'Cocina en U abierta', d: 'Propuesta: mesón norte con estufa y horno, nevera de columna y barra-península con lavaplatos. Sin comedor tradicional: la barra lo reemplaza.' },
  { id: 'barra', p: [0.9, 4.6, 1.1], cat: 'propuesta', t: 'Barra de 2 puestos · 1,45 m', d: 'Propuesta: península de 1,45 × 0,90 m con voladizo de 0,30 m para dos banquetas. Deja un eje libre de al menos 0,85 m entre la cocina, la sala y el balcón.' },
  { id: 'ropas', p: [3.1, 5.25, 1.95], cat: 'propuesta', t: 'Ropas junto a los ductos · 1,11 m²', d: 'Propuesta: lavadora-secadora apilada, lavadero y almacenamiento en el antiguo cuarto, tras una puerta corrediza oculta en el muro. Desagüe y extracción al ducto D1, a unos 0,4 m; agua desde el baño social. Se descartó la columna junto al acceso: desagüe de ≈3,2 m, sin ventilación cercana y ruido en la zona social.' },
  { id: 'ductos', p: [3.83, 5.25, 2.05], cat: 'verificado', t: 'Ductos del DWG', d: 'Los dos ductos verticales del plano se conservan. Los dos baños y la zona de ropas se agrupan junto a ellos.' },
  { id: 'hall', p: [4.0, 4.24, 2.15], cat: 'propuesta', t: 'Hall de alcobas · 2,12 m²', d: 'Un solo hall reparte las dos habitaciones, el baño social y la zona de ropas: menos pasillo y más área útil en los recintos.' },
  { id: 'ingreso', p: [1.0, 6.65, 1.9], cat: 'propuesta', t: 'Ingreso libre de 0,95 m', d: 'Entre la despensa de 0,40 m y el mesón de la cocina quedan 0,95 m frente a frente (1,00 m medido; lo limita la puerta de acceso).' },
  { id: 'habitacion_2', p: [4.0, 1.9, 1.2], cat: 'propuesta', t: 'Habitación 2 · 8,88 m²', d: 'Cama doble con cabecero tapizado, mesas de noche flotantes, armario corredizo de 1,40 m y cómoda baja bajo la ventana. La alcoba equivalente del plano original medía 2,50 × 2,52 m (6,30 m²).' },
  { id: 'principal', p: [6.6, 2.5, 1.3], cat: 'propuesta', t: 'Habitación principal · 11,39 m²', d: 'Suite con baño privado de 4,70 m² y vestier de 3,06 m², en el área que ocupaban el estudio y la alcoba del plano original.' },
  { id: 'bano_principal', p: [5.75, 6.9, 1.5], cat: 'propuesta', t: 'Baño principal · 4,70 m²', d: 'Propuesta: ducha de 1,78 m con mampara, doble lavamanos y sanitario suspendido.' },
  { id: 'altura', p: [3.0, 4.24, 2.25], cat: 'provisional', t: 'Altura libre 2,40 m (supuesta)', d: 'El DWG no incluye cortes: altura piso–cielo, losa, puertas de 2,10 m y antepechos de 0,90 m son provisionales.' },
  { id: 'acabados', p: [1.44, 1.8, 0.55], cat: 'ilustrativo', t: 'Acabados en vivo', d: 'Pisos, muros, cocina y baños cambian sobre el mismo modelo. Son ilustrativos y no contractuales.', accion: 'acabados' },
  { id: 'ventana_sala', p: [1.37, 0.1, 1.55], cat: 'verificado', t: 'Ventana de la sala · 2,449 m', d: 'Ancho del DWG; antepecho de 0,90 m provisional.', bal: false },
  { id: 'corrediza', p: [1.99, 0.1, 1.6], cat: 'propuesta', t: 'Puerta-ventana corrediza', d: 'Propuesta: el vano de 2,449 m de la sala se abre al balcón con dos hojas corredizas de 2,10 m.', bal: true },
  { id: 'balcon', p: [0.9, -1.25, 1.25], cat: 'propuesta', t: 'Balcón propuesto · 4,04 m²', d: 'Extensión de la sala. No figura en los planos: requiere diseño estructural, viabilidad urbanística, licencia y aprobación del arquitecto. El paisaje exterior es conceptual.', bal: true },
];
const pois = [];
function buildPois() {
  for (const p of POIS) {
    const el = document.createElement('button'); el.type = 'button'; el.className = `poi ${p.cat}`; el.dataset.poi = p.id;
    el.setAttribute('aria-label', `${p.t}. ${CATS[p.cat]}`); el.innerHTML = '<i>i</i>';
    el.addEventListener('click', e => { e.stopPropagation(); openPoi(p); });
    $('#pois').append(el);
    pois.push({ ...p, el, pos: toScene(p.p[0], p.p[1], p.p[2]), blocked: false });
  }
  $('#poiClose').addEventListener('click', () => closePoi());
}
let poiOpen = null;
function openPoi(p) {
  poke(10);
  poiOpen = p; const c = $('#poiCard');
  c.className = `poi-card ${p.cat}`; $('#poiCat').textContent = CATS[p.cat]; $('#poiT').textContent = p.t; $('#poiD').textContent = p.d;
  $('#poiAct').hidden = !p.accion; c.hidden = false;
  if (mode === 'tour' && tourPlaying) setTourPlaying(false);
}
function closePoi() { poiOpen = null; $('#poiCard').hidden = true; }
$('#poiAct').addEventListener('click', () => { closePoi(); openPanel('acabados'); });

// ------------------------------------------------------------------ cotas del plano (capa COTAS del DWG)
const dimGroup = new THREE.Group(); dimGroup.visible = false; scene.add(dimGroup);
const dimLabels = [];
const propDims = [];
function buildDims() {
  const seen = new Set();
  const mat = new THREE.LineBasicMaterial({ color: '#f2e0b0', transparent: true, opacity: .85, depthTest: false });
  const add = (a, b, value) => {
    const key = [a.x, a.y, b.x, b.y].map(v => v.toFixed(2)).sort().join('|') + value;
    if (seen.has(key)) return; seen.add(key);
    const pa = toScene(a.x, a.y, 2.46), pb = toScene(b.x, b.y, 2.46);
    const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints([pa, pb]), mat); line.renderOrder = 5; dimGroup.add(line);
    const el = document.createElement('span'); el.className = 'dim'; el.textContent = fmtDim(value); el.hidden = true; $('#labels').append(el);
    dimLabels.push({ el, pos: pa.clone().add(pb).multiplyScalar(.5) });
  };
  for (const d of geo.cotas) {
    if (d.medida < 0.7 || d.medida > 9) continue;
    const a = { x: d.a[0], y: d.a[1] }, b = { x: d.b[0], y: d.b[1] };
    const horiz = Math.abs(a.y - b.y) < Math.abs(a.x - b.x);
    const pb = horiz ? { x: b.x, y: a.y } : { x: a.x, y: b.y };   // la cota mide la proyección
    add(a, pb, d.medida);
  }
  add({ x: 0, y: -0.3 }, { x: W, y: -0.3 }, W);
  add({ x: W + 0.3, y: 0 }, { x: W + 0.3, y: H }, H);
  if (PROP) {   // medidas de la propuesta, rotuladas aparte
    const [x0, y0, x1, y1] = PROP.rect_util, n = dimLabels.length;
    add({ x: x0, y: y0 - 0.25 }, { x: x1, y: y0 - 0.25 }, PROP.ancho_util);
    add({ x: x1 + 0.25, y: y0 }, { x: x1 + 0.25, y: y1 }, PROP.fondo_util);
    for (const d of dimLabels.slice(n)) { d.prop = true; d.el.classList.add('prop'); }
    propDims.push(...dimGroup.children.slice(-2));
  }
}

// ------------------------------------------------------------------ capas y vista técnica («solo arquitectura verificada»)
const verifiedOnly = () => $('#layerVerified').checked;
const balconyOn = () => balcony && !!PROP && !verifiedOnly();
const NEUTRAL = {
  muro: new THREE.MeshStandardMaterial({ color: '#e7e5e0', roughness: 0.92 }),
  piso: new THREE.MeshStandardMaterial({ color: '#cfccc5', roughness: 0.95 }),
  aparato: new THREE.MeshStandardMaterial({ color: '#f1f0ec', roughness: 0.6 }),
  provisional: new THREE.MeshStandardMaterial({ color: '#7fb2dd', roughness: 0.8, transparent: true, opacity: 0.55, depthWrite: false }),
};
let techView = false;
function setTechnical(on) {
  if (on === techView || !model) return; techView = on;
  model.traverse(o => {
    if (!o.isMesh) return;
    const node = o.userData.verificado !== undefined ? o : o.parent;
    const nm = node?.name || '';
    if (on) {
      o.userData.mat0 = o.material;
      if (/^ARQ_(Dinteles|Losa)|^ILU_Antepecho_sala/.test(nm)) o.material = o.material.name === 'muro_corte' ? o.material : NEUTRAL.provisional;
      else if (/^ARQ_Piso/.test(nm)) o.material = NEUTRAL.piso;
      else if (nm === 'ARQ_Muros' && o.material.name === 'muro') o.material = NEUTRAL.muro;
      else if (/^APA_/.test(nm)) o.material = /vidrio/.test(o.material.name) ? o.material : NEUTRAL.aparato;
    } else if (o.userData.mat0) { o.material = o.userData.mat0; delete o.userData.mat0; }
  });
  if (!on) reapplyFinishes();
}
function applyLayers() {
  poke(30);
  const vo = verifiedOnly();
  const furniture = $('#layerFurniture').checked && !vo;
  const bal = balconyOn();
  setTechnical(vo);
  groups.mobiliario.forEach(o => { o.visible = furniture; });
  groups.ilustrativo.forEach(o => { o.visible = !vo; });
  groups.acabados.forEach(o => { o.visible = !vo; });
  groups.rediseno.forEach(o => { o.visible = !vo; });
  groups.aparatos.forEach(o => { o.visible = !vo; });   // en el 102 los aparatos están en posición propuesta
  original.visible = vo || $('#layerOriginal').checked;
  for (const o of groups.arquitectura) if (o.userData.verificado === false) o.visible = true;   // provisionales: en la vista técnica se ven en azul
  groups.propuesta.forEach(o => { o.visible = bal; });
  groups.propuesta_mobiliario.forEach(o => { o.visible = bal && furniture; });
  groups.sin_balcon.forEach(o => { o.visible = !bal && !(vo && o.name === 'ILU_Ventana_sala'); });
  $('#layerFurniture').disabled = vo;
  const lb = $('#layerBalcony'); if (lb) { lb.disabled = vo; lb.checked = balcony; }
  document.body.classList.toggle('has-balcony', bal);
  document.body.classList.toggle('tech', vo);
  $$('[data-room="balcon"]').forEach(e => { e.closest('li') ? (e.closest('li').hidden = !bal) : e.classList.toggle('gone', !bal); });
  dimGroup.visible = $('#layerDims').checked && mode === 'orbit';
  propDims.forEach(l => { l.visible = bal; });
  if (ready) updateLightPool(0, true);
  updateEnvironment();
}
// planta original del DWG dibujada sobre el piso (para comparar con la propuesta)
const original = new THREE.Group(); original.visible = false; scene.add(original);
{
  const add = (segs, color) => {
    const pts = []; for (const [a, b] of segs) pts.push(toScene(a[0], a[1], 0.025), toScene(b[0], b[1], 0.025));
    const l = new THREE.LineSegments(new THREE.BufferGeometry().setFromPoints(pts), new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.95, depthTest: false }));
    l.renderOrder = 6; original.add(l);
  };
  add(geo.original.segmentos.muros, '#ff5a3c'); add(geo.original.segmentos.ventanas, '#59b7ff'); add(geo.original.segmentos.aparatos, '#ffb04a');
}
['#layerFurniture', '#layerDims', '#layerVerified', '#layerOriginal'].forEach(s => $(s).addEventListener('change', () => { applyLayers(); if (s === '#layerVerified') buildTour(); }));
$('#layerQuality') && ($('#layerQuality').checked = quality === 'alta');
$('#layerQuality')?.addEventListener('change', e => setQuality(e.target.checked ? 'alta' : 'media'));
function setBalcony(on) {
  if (!PROP) return;
  balcony = !!on;
  if (!balcony && current === 'balcon') { markRoom('social'); if (mode === 'walk') goRoom('social'); }
  if (mode === 'tour') setMode('orbit');
  buildTour(); applyLayers();
}
$('#layerBalcony')?.addEventListener('change', e => setBalcony(e.target.checked));

// ------------------------------------------------------------------ cámara: vuelos suaves
let flight = null;
const ease = t => (t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
function flyTo(pos, target, dur = 1.6, done) {
  poke(30);
  if (reduce) dur = 0.01;
  flight = { p0: camera.position.clone(), t0: (mode === 'orbit' ? controls.target.clone() : lookTarget()), p1: pos, t1: target, start: performance.now(), dur: dur * 1000, done };
}
let yaw = 0, pitch = -0.08;
function lookTarget() {
  return camera.position.clone().add(new THREE.Vector3(Math.sin(yaw) * Math.cos(pitch), Math.sin(pitch), -Math.cos(yaw) * Math.cos(pitch)));
}
function yawPitchFrom(dir) { const d = dir.clone().normalize(); yaw = Math.atan2(d.x, -d.z); pitch = Math.asin(THREE.MathUtils.clamp(d.y, -1, 1)); }
function resetOrbit(instant) {
  // encuadre: la maqueta completa, desplazada hacia la izquierda para no quedar bajo la ficha lateral
  const narrow = camera.aspect < 0.9;
  const vf = THREE.MathUtils.degToRad(42), hf = 2 * Math.atan(Math.tan(vf / 2) * camera.aspect);
  const fit = 6.1 / Math.sin(Math.min(vf, hf) / 2);
  const dir = new THREE.Vector3(0.52, 0.66, 0.54).normalize();
  const tgt = new THREE.Vector3(narrow ? -0.35 : 0.9, narrow ? -1.0 : 0.0, narrow ? 0.4 : 0.2);
  const pos = tgt.clone().add(dir.multiplyScalar(Math.min(fit, 34) * (narrow ? 1.05 : 0.86)));
  if (instant) { camera.position.copy(pos); controls.target.copy(tgt); camera.lookAt(tgt); controls.update(); }
  else flyTo(pos, tgt, 1.4);
}

let current = null;
function markRoom(id) {
  current = id;
  $$('#rooms button').forEach(b => b.classList.toggle('on', b.dataset.room === id));
}
let captionTimer = null;
function caption(r, kicker) {
  if (!r && !kicker) { $('#caption').classList.remove('on'); return; }
  $('#captionK').textContent = kicker || (r.propuesta ? `Balcón propuesto · ${fmt(r.area_util_m2 ?? r.area_neta_m2)} m² · no figura en los planos` : `Propuesta · área neta ${fmt(r.area_neta_m2)} m²${roomNote(r) ? ' · ' + roomNote(r) : ''}`);
  $('#captionT').textContent = r ? roomName(r) : '';
  $('#caption').classList.add('on');
}
function flashCaption(r, ms = 2600) { caption(r); clearTimeout(captionTimer); captionTimer = setTimeout(() => caption(null), ms); }

function goRoom(id) {
  const r = roomById[id]; const v = VIEWS[id]; if (!r || !ready) return;
  if (r.propuesta && !balconyOn()) return;
  if (mode === 'tour') setMode('orbit');
  markRoom(id); flashCaption(r);
  if (mode === 'walk') {
    const p = toScene(v.pos[0], v.pos[1], EYE), l = toScene(v.look[0], v.look[1], EYE - 0.15);
    flyTo(p, l, 1.4, () => yawPitchFrom(l.clone().sub(p)));
  } else {
    const c = toScene(v.orbit[0], v.orbit[1], 0.3);
    const off = new THREE.Vector3(1.9, 6.2, 3.4).multiplyScalar(camera.aspect < 0.9 ? 1.35 : 1);
    flyTo(c.clone().add(off), c, 1.5);
  }
}

// ------------------------------------------------------------------ caminar: colisiones con muros, ventanas, aparatos y mobiliario visible
const dwgWalls = geo.muros_rectangulos.filter((m, i) => geo.muros_origen[i] === 'dwg');
const baseObstacles = [
  ...geo.muros_rectangulos,
  ...geo.ventanas.filter(w => w !== SALA_V).map(w => [w.x0, w.y0, w.x1, w.y1]),
  ...geo.aparatos.filter(f => f.rect && f.tipo !== 'ducha').map(f => f.rect),
  ...geo.puertas.filter(d => d.id === 'entrada').map(d => d.rect),   // no se sale al corredor
];
const RADIUS = 0.22;
function shown(o) { for (let q = o; q; q = q.parent) if (!q.visible) return false; return true; }
function segsNow() {   // hojas de puerta abiertas (segmentos con espesor)
  const out = []; for (const h of huellas) if (h.segs.length && shown(h.node)) out.push(...h.segs); return out;
}
function segDist(px, py, [ax, ay, bx, by]) {
  const dx = bx - ax, dy = by - ay, t = Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)));
  return Math.hypot(px - ax - t * dx, py - ay - t * dy);
}
function obstaclesNow() {
  // con «solo envolvente del DWG» desaparecen los tabiques y aparatos de la propuesta
  const list = verifiedOnly() ? [...dwgWalls, ...geo.puertas.filter(d => d.id === 'entrada').map(d => d.rect), ...geo.ventanas.filter(w => w !== SALA_V).map(w => [w.x0, w.y0, w.x1, w.y1])] : [...baseObstacles];
  for (const h of huellas) if (/^(MOB|PROP|ILU_Puerta|APA)_/.test(h.node.name) && shown(h.node)) list.push(...h.rects);
  if (!balconyOn()) list.push([SALA_V.x0, SALA_V.y0, SALA_V.x1, SALA_V.y1]);
  else { const [h0, h1] = PROP.acceso.hojas_cerradas; list.push([h0, SALA_V.y0, h1, SALA_V.y1]); }
  return list;
}
let obsCache = null, segCache = null, obsFrame = -1;
function obstacles() { if (obsFrame !== frame) { obsCache = obstaclesNow(); segCache = segsNow(); obsFrame = frame; } return obsCache; }
function onBalcony(x, y) {
  if (!balconyOn()) return false;
  const [x0, y0, x1] = PROP.rect_util;
  return x >= x0 + RADIUS && x <= x1 - RADIUS && y >= y0 + RADIUS && y < RADIUS + 0.01;
}
function free(x, y, r = RADIUS) {
  if (!onBalcony(x, y) && (x < r || x > W - r || y < r || y > H - r)) return false;
  if (obstacles().some(([x0, y0, x1, y1]) => x > Math.min(x0, x1) - r && x < Math.max(x0, x1) + r && y > Math.min(y0, y1) - r && y < Math.max(y0, y1) + r)) return false;
  return !segCache.some(sg => segDist(x, y, sg) < r + sg[4] / 2);
}
function nearestFree(p) {
  if (free(p.x, p.y)) return p;
  for (let rad = 0.05; rad < 1.5; rad += 0.05) for (let a = 0; a < 16; a++) {
    const q = { x: p.x + Math.cos(a / 16 * Math.PI * 2) * rad, y: p.y + Math.sin(a / 16 * Math.PI * 2) * rad };
    if (free(q.x, q.y)) return q;
  }
  return null;
}
function moveBy(dx, dy) {
  const p = toPlan(camera.position);
  const steps = Math.max(1, Math.ceil(Math.hypot(dx, dy) / 0.04));
  for (let i = 0; i < steps; i++) {
    if (free(p.x + dx / steps, p.y)) p.x += dx / steps;
    if (free(p.x, p.y + dy / steps)) p.y += dy / steps;
  }
  camera.position.copy(toScene(p.x, p.y, EYE));
}
const keys = new Set(); const pad = new Set();
addEventListener('keydown', e => {
  if (e.target.closest('input')) return;
  const k = e.key.toLowerCase();
  if (mode === 'tour' && k === ' ') { setTourPlaying(!tourPlaying); e.preventDefault(); return; }
  if (mode !== 'walk') { if (k === 'escape' && mode === 'tour') setMode('orbit'); return; }
  if (['w', 'a', 's', 'd', 'arrowup', 'arrowdown', 'arrowleft', 'arrowright'].includes(k)) { keys.add(k); e.preventDefault(); }
  if (k === 'escape') setMode('orbit');
});
addEventListener('keyup', e => keys.delete(e.key.toLowerCase()));
addEventListener('blur', () => { keys.clear(); pad.clear(); });
$$('#walkpad button').forEach(b => {
  const on = e => { e.preventDefault(); pad.add(b.dataset.move); b.setPointerCapture?.(e.pointerId); };
  const off = () => pad.delete(b.dataset.move);
  b.addEventListener('pointerdown', on); b.addEventListener('pointerup', off); b.addEventListener('pointercancel', off); b.addEventListener('lostpointercapture', off);
});
// mirar arrastrando; tocar el piso para caminar hasta ese punto
let drag = null;
canvas.addEventListener('pointerdown', e => {
  if (mode === 'tour') { setTourPlaying(false); return; }   // tocar pausa el recorrido
  if (mode !== 'walk') return;
  drag = { x: e.clientX, y: e.clientY, yaw, pitch, moved: false, id: e.pointerId };
  canvas.setPointerCapture(e.pointerId);
});
canvas.addEventListener('pointermove', e => {
  if (!drag || e.pointerId !== drag.id) return;
  const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
  if (Math.hypot(dx, dy) > 6) drag.moved = true;
  const k = (e.pointerType === 'touch' ? 0.006 : 0.004);
  yaw = drag.yaw - dx * k; pitch = THREE.MathUtils.clamp(drag.pitch - dy * k, -1.1, 1.0);
});
const ray = new THREE.Raycaster();
canvas.addEventListener('pointerup', e => {
  if (!drag || e.pointerId !== drag.id) return;
  const wasTap = !drag.moved; drag = null;
  if (!wasTap || mode !== 'walk') return;
  const r = canvas.getBoundingClientRect();
  ray.setFromCamera(new THREE.Vector2(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1), camera);
  const targets = []; model.traverse(o => { if (o.isMesh && shown(o) && (/^ARQ_(Piso|Muros)|^PROP_Balcon_losa|^MOB_|^APA_/.test(o.name) || /^ARQ_Piso|^MOB_|^APA_/.test(o.parent?.name || ''))) targets.push(o); });
  const hit = ray.intersectObjects(targets, false)[0];
  if (hit) walkTo(toPlan(hit.point));
});
let walkTarget = null;
function walkTo(p) { walkTarget = p; }

// ------------------------------------------------------------------ recorrido cinematográfico en 12 capítulos
// Puntos en planta [x, altura, y]; la trayectoria cruza solo vanos reales (prueba automática).
const CHAPTERS = ['Vista general', 'Aproximación al acceso', 'Entrada y cocina', 'Sala y barra', 'Balcón', 'Hall de alcobas',
  'Habitación 2', 'Baño social y ropas', 'Habitación principal', 'Baño principal y vestier', 'Regreso a la zona social', 'Vista final'];
const K = (c, t, p, l, room = null) => ({ c, t, p, l, room });
const TOUR_A = [
  K(0, 0, [11.0, 10.5, -5.5], [4.0, 0, 3.8]),
  K(0, 6, [-3.8, 8.5, 1.5], [3.6, 0, 4.4]),
  K(1, 10.5, [-2.6, 4.2, 11.4], [0.65, 1.5, 7.6]),
  K(1, 14, [0.65, 1.65, 10.0], [0.65, 1.5, 7.0]),
  K(2, 17, [0.65, 1.6, 7.85], [1.0, 1.4, 5.5]),
  K(2, 20, [1.0, 1.6, 6.6], [1.0, 1.1, 4.6], 'social'),
  K(2, 23, [1.85, 1.6, 6.0], [2.2, 1.2, 7.45], 'social'),
  K(3, 27, [2.25, 1.6, 4.9], [0.9, 0.95, 4.3], 'social'),
  K(3, 31, [2.12, 1.55, 3.2], [0.6, 1.0, 1.4], 'social'),
  K(3, 35, [2.05, 1.5, 0.75], [0.6, 1.1, 3.0], 'social'),
];
const TOUR_BAL = [   // el balcón propuesto como extensión de la sala; la hoja corrediza abre al este
  K(4, 38.5, [2.0, 1.6, 0.45], [2.0, 1.3, -1.6], 'social'),
  K(4, 42, [2.0, 1.6, -0.55], [1.0, 1.0, -1.5], 'balcon'),
  K(4, 45.5, [1.9, 1.6, -1.25], [3.0, 0.7, -8.0], 'balcon'),
  K(4, 49, [1.85, 1.62, -1.1], [1.2, 1.2, 3.5], 'balcon'),
  K(4, 52.5, [2.05, 1.6, 0.6], [2.2, 1.3, 3.6], 'social'),
];
const TOUR_WIN = [
  K(4, 38.5, [1.4, 1.6, 0.6], [1.4, 1.2, -6.0], 'social'),
  K(4, 42.5, [1.2, 1.6, 0.9], [2.2, 1.3, 3.6], 'social'),
];
const TOUR_B = [   // tiempos relativos al final del capítulo 4
  K(5, 1.8, [1.95, 1.6, 0.85], [2.3, 1.3, 4.0], 'social'),
  K(5, 3.5, [2.05, 1.6, 2.0], [2.4, 1.3, 4.5], 'social'),
  K(5, 6.5, [2.35, 1.6, 4.15], [5.2, 1.4, 4.2], 'social'),
  K(5, 9.5, [3.3, 1.6, 4.25], [5.2, 1.3, 4.3], 'hall'),
  K(6, 12, [3.45, 1.6, 4.0], [3.6, 1.2, 2.5], 'hall'),
  K(6, 14.5, [3.5, 1.6, 3.0], [4.7, 1.0, 0.5], 'habitacion_2'),
  K(6, 18, [4.3, 1.55, 2.75], [2.9, 0.9, 1.6], 'habitacion_2'),
  K(6, 21.5, [3.35, 1.6, 3.25], [3.3, 1.4, 4.5], 'habitacion_2'),
  K(7, 23.5, [3.3, 1.6, 4.25], [4.2, 1.3, 5.5], 'hall'),
  K(7, 26, [4.2, 1.6, 4.3], [4.2, 1.2, 6.5], 'hall'),
  K(7, 29, [4.2, 1.6, 5.1], [4.4, 1.2, 6.9], 'bano_social'),
  K(7, 32, [4.15, 1.6, 4.95], [4.75, 1.4, 6.2], 'bano_social'),
  K(7, 33.6, [4.2, 1.6, 4.42], [3.0, 1.2, 4.6], 'hall'),
  K(7, 35.6, [3.1, 1.6, 4.3], [3.0, 1.1, 5.6], 'hall'),
  K(8, 38.5, [4.9, 1.6, 4.25], [6.5, 1.3, 3.5], 'hall'),
  K(8, 41.5, [5.75, 1.6, 4.15], [7.6, 0.9, 2.6], 'principal'),
  K(8, 45, [5.65, 1.55, 2.0], [7.6, 0.8, 2.6], 'principal'),
  K(8, 48.5, [6.2, 1.55, 0.85], [7.4, 1.0, 3.0], 'principal'),
  K(8, 50.3, [5.68, 1.6, 1.6], [5.75, 1.3, 4.2], 'principal'),
  K(9, 52.6, [5.7, 1.6, 3.75], [5.9, 1.3, 6.0], 'principal'),
  K(9, 55, [5.95, 1.6, 5.2], [5.5, 1.2, 6.8], 'bano_principal'),
  K(9, 58.5, [6.0, 1.55, 5.4], [4.88, 1.35, 5.75], 'bano_principal'),
  K(9, 60.5, [5.95, 1.6, 4.45], [7.0, 1.4, 4.4], 'principal'),
  K(9, 62, [6.5, 1.6, 4.2], [7.3, 1.4, 5.6], 'principal'),
  K(9, 63.5, [7.15, 1.6, 4.4], [7.3, 1.3, 6.0], 'principal'),
  K(9, 65.5, [7.3, 1.6, 5.0], [7.2, 1.2, 6.9], 'vestier'),
  K(10, 67.3, [7.2, 1.6, 4.42], [6.0, 1.4, 4.3], 'principal'),
  K(10, 68.6, [6.4, 1.6, 4.25], [5.0, 1.4, 4.2], 'principal'),
  K(10, 71, [5.0, 1.6, 4.25], [2.0, 1.3, 4.0], 'hall'),
  K(10, 74, [2.4, 1.6, 4.25], [1.0, 1.2, 1.0], 'social'),
  K(10, 77.5, [2.15, 1.6, 2.7], [0.9, 1.2, -1.5], 'social'),
  K(11, 81, [1.95, 1.65, 1.0], [1.3, 1.0, -6.0], 'social'),
  K(11, 83.5, [2.0, 1.7, 0.5], [1.6, 1.0, -6.0], 'social'),
];
const TOUR_END_BAL = [K(11, 93, [3.5, 4.4, -6.2], [1.4, 0.9, 0.2], null)];
const TOUR_END_WIN = [K(11, 87.5, [1.9, 1.65, 0.6], [0.9, 1.0, -6.0], 'social')];
let TOUR = [], tourCurve, lookCurve, TOUR_LEN = 0, tourSlopes = [];
function buildTour() {
  const bal = balconyOn(), mid = bal ? TOUR_BAL : TOUR_WIN, off = mid[mid.length - 1].t;
  const list = [...TOUR_A, ...mid, ...[...TOUR_B, ...(bal ? TOUR_END_BAL : TOUR_END_WIN)].map(k => ({ ...k, t: k.t + off }))];
  TOUR = list.map(k => ({ ...k, P: toScene(k.p[0], k.p[2], k.p[1]), L: toScene(k.l[0], k.l[2], k.l[1]) }));
  tourCurve = new THREE.CatmullRomCurve3(TOUR.map(k => k.P), false, 'centripetal');
  lookCurve = new THREE.CatmullRomCurve3(TOUR.map(k => k.L), false, 'centripetal');
  TOUR_LEN = TOUR[TOUR.length - 1].t;
  // interpolación monótona (Fritsch–Carlson) del índice de nudo en el tiempo: sin paradas en cada nudo
  const n = TOUR.length, d = [], m = new Array(n).fill(0);
  for (let i = 0; i < n - 1; i++) d.push(1 / (TOUR[i + 1].t - TOUR[i].t));
  for (let i = 1; i < n - 1; i++) m[i] = (d[i - 1] + d[i]) / 2;
  m[0] = 0; m[n - 1] = 0;   // arranque y llegada suaves
  tourSlopes = m;
  $('#tourChapters') && ($('#tourChapters').innerHTML = CHAPTERS.map((c, i) => `<i style="left:${(TOUR.find(k => k.c === i)?.t || 0) / TOUR_LEN * 100}%" title="${i + 1}. ${c}"></i>`).join(''));
}
function tourParam(t) {
  const n = TOUR.length - 1;
  t = THREE.MathUtils.clamp(t, 0, TOUR_LEN);
  let i = 0; while (i < n - 1 && t > TOUR[i + 1].t) i++;
  const a = TOUR[i], b = TOUR[i + 1], h = b.t - a.t, s = (t - a.t) / h;
  const h00 = 2 * s ** 3 - 3 * s ** 2 + 1, h10 = s ** 3 - 2 * s ** 2 + s, h01 = -2 * s ** 3 + 3 * s ** 2, h11 = s ** 3 - s ** 2;
  const idx = h00 * i + h10 * h * tourSlopes[i] + h01 * (i + 1) + h11 * h * tourSlopes[i + 1];
  return { u: THREE.MathUtils.clamp(idx / n, 0, 1), room: s < .5 ? a.room : b.room, chapter: s < .5 ? a.c : b.c };
}
let tourT = 0, tourRoom = undefined, tourChapter = -1, tourPlaying = true, tourBlend = null;
function setTourPlaying(on) {
  tourPlaying = !!on;
  $('#tourPlay').setAttribute('aria-label', on ? 'Pausar recorrido' : 'Reanudar recorrido');
  $('#tourPlay').classList.toggle('paused', !on);
  $('#tourbar').classList.toggle('paused', !on);
}
$('#tourPlay').addEventListener('click', () => { if (tourT >= TOUR_LEN - 0.05) tourT = 0; setTourPlaying(!tourPlaying); });
$('#tourExplore').addEventListener('click', () => exploreHere());
$('#tourProgress').addEventListener('click', e => {
  const r = e.currentTarget.getBoundingClientRect(); tourT = THREE.MathUtils.clamp((e.clientX - r.left) / r.width, 0, 1) * TOUR_LEN; tourBlend = null;
});
function exploreHere() {   // del recorrido a la exploración libre, desde la posición actual de la cámara
  const p = toPlan(camera.position); const dir = new THREE.Vector3(); camera.getWorldDirection(dir);
  const inside = camera.position.y < 2.3 && (roomAt(p) || onBalcony(p.x, p.y));
  setMode('walk', { keepCamera: inside });
  if (inside) {
    const q = nearestFree(p) || p;
    camera.position.copy(toScene(q.x, q.y, EYE)); dir.y = Math.max(-0.4, Math.min(0.3, dir.y)); yawPitchFrom(dir);
  }
}

// panel plegable en teléfono y pestañas
const toggle = $('#panelToggle'), body = $('#panelBody');
function syncPanel() { if (compact.matches || $('#panel').classList.contains('folded')) body.hidden = toggle.getAttribute('aria-expanded') !== 'true'; else body.hidden = false; }
toggle.addEventListener('click', () => { toggle.setAttribute('aria-expanded', String(toggle.getAttribute('aria-expanded') !== 'true')); syncPanel(); });
compact.addEventListener('change', syncPanel); syncPanel();
function showTab(id) {
  $$('#tabs [role=tab]').forEach(b => { const on = b.dataset.tab === id; b.setAttribute('aria-selected', String(on)); b.tabIndex = on ? 0 : -1; });
  $$('[data-pane]').forEach(p => { p.hidden = p.dataset.pane !== id; });
}
$$('#tabs [role=tab]').forEach(b => b.addEventListener('click', () => showTab(b.dataset.tab)));
function openPanel(tab) { showTab(tab); if (body.hidden) { toggle.setAttribute('aria-expanded', 'true'); syncPanel(); } }

// ------------------------------------------------------------------ modos
let mode = 'orbit';
const HINTS = {
  orbit: 'Arrastra para girar la maqueta · toca un punto para ver cada espacio',
  tour: 'Recorrido · toca la pantalla o la barra espaciadora para pausar',
  walk: 'Arrastra para mirar · toca el piso para caminar · WASD o flechas',
};
let fovTarget = 42;
function setMode(next, opts = {}) {
  if (!ready) return;
  const prev = mode; mode = next; flight = null; keys.clear(); pad.clear(); walkTarget = null; closePoi();
  controls.enabled = next === 'orbit';
  $$('#modes button').forEach(b => { const on = b.dataset.mode === next; b.classList.toggle('on', on); b.setAttribute('aria-pressed', String(on)); });
  $('#walkpad').hidden = next !== 'walk';
  $('#tourbar').hidden = next !== 'tour';
  $('#hintTxt').textContent = HINTS[next];
  const inside = next !== 'orbit';
  groups.cielo.forEach(o => { o.visible = inside && next === 'walk'; });
  interiorLights.visible = windowLights.visible = inside; ground.visible = !inside;
  canvas.style.cursor = next === 'walk' ? 'crosshair' : '';
  fovTarget = next === 'orbit' ? 42 : (camera.aspect < 0.9 ? 74 : 60);
  luzAmbiente();
  // dentro del apartamento la arquitectura manda: la ficha de opciones se pliega
  if (next !== 'orbit' && !compact.matches) { body.hidden = true; toggle.setAttribute('aria-expanded', 'false'); }
  if (next === 'orbit' && !compact.matches) { body.hidden = false; }
  $('#panel').classList.toggle('folded', next !== 'orbit');
  if (next === 'orbit') { caption(null); if (prev !== 'orbit') resetOrbit(); }
  if (next === 'walk' && !opts.keepCamera) {
    const v = VIEWS[current] || VIEWS.social;
    const p = toScene(v.pos[0], v.pos[1], EYE), l = toScene(v.look[0], v.look[1], EYE - 0.15);
    flyTo(p, l, prev === 'orbit' || prev === 'tour' ? 1.8 : 0.01, () => yawPitchFrom(l.clone().sub(p)));
  }
  if (next === 'tour') {
    tourT = 0; tourRoom = undefined; tourChapter = -1; setTourPlaying(true);
    tourBlend = { p: camera.position.clone(), l: (prev === 'orbit' ? controls.target.clone() : lookTarget()), start: performance.now() };
    if (reduce) { setMode('walk'); $('#hintTxt').textContent = 'Movimiento reducido: recorre los espacios con la lista'; return; }
  }
  updateMirrors();
  applyLayers();
}
$$('#modes button').forEach(b => b.addEventListener('click', () => setMode(b.dataset.mode)));

// ------------------------------------------------------------------ luz ambiente y hora del día (día / atardecer)
let hora = 'dia';
const SUN_DIA = SUN_DIR.clone();
const SUN_TARDE = new THREE.Vector3(-8.5, 2.3, 6.8).normalize();   // sol bajo del oeste–suroeste, entra por la fachada
function luzAmbiente() {
  const inside = mode !== 'orbit', t = hora === 'atardecer';
  hemi.intensity = inside ? (t ? 0.2 : 0.3) : (t ? 0.55 : 0.85);
  hemi.groundColor.set(inside ? (t ? '#8a6f58' : '#b4a796') : (t ? '#3a2a20' : '#2a2621'));   // dentro: rebote cálido del piso hacia el cielo raso
  // dentro, la luz ambiente es la de una habitación neutra (el HDRI exterior teñiría de verde los cielos rasos);
  // en la maqueta, el HDRI ilumina y se refleja en los materiales
  scene.environment = inside ? roomEnv : (envHDR || roomEnv);
  scene.environmentIntensity = (inside ? 0.30 : 0.45) * (t ? 0.55 : 1);
  renderer.toneMappingExposure = inside ? (t ? 0.98 : 0.88) : (t ? 0.85 : 0.92);
}
function setHora(h) {
  hora = h === 'atardecer' ? 'atardecer' : 'dia';
  const t = hora === 'atardecer';
  SUN_DIR.copy(t ? SUN_TARDE : SUN_DIA);
  sun.color.set(t ? '#ffaa66' : '#fff0d8'); sun.intensity = t ? 2.4 : 2.6;
  hemi.color.set(t ? '#f0c6a0' : '#f6efe2');
  luz.interior = t ? 1.8 : 1; luz.ventana = t ? 0.45 : 1;
  for (const l of poolR) l.color.set(t ? '#ffcf9e' : '#e9eff5');
  if (mats.luz_calida) mats.luz_calida.emissiveIntensity = t ? 3.2 : 2.2;
  entorno.setHora(hora); entorno.sky.material.uniforms.sunPosition.value.copy(SUN_DIR).multiplyScalar(400);
  luzAmbiente(); updateLightPool(0, true); renderer.shadowMap.needsUpdate = true;
  $$('#hora button').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.h === hora)));
  poke(40);
}
$$('#hora button').forEach(b => b.addEventListener('click', () => setHora(b.dataset.h)));
$$('#calidad button').forEach(b => { b.setAttribute('aria-pressed', String(b.dataset.q === quality)); b.addEventListener('click', () => setQuality(b.dataset.q)); });

function updateEnvironment() {
  const inside = mode !== 'orbit';
  const env = inside && !verifiedOnly();
  entorno.group.visible = env;
  scene.fog = env ? entorno.fog : null;
  scene.background = inside ? (env ? null : new THREE.Color('#dfe5ea')) : navy;
  $('#envTag').hidden = !env;
}

// ------------------------------------------------------------------ ciclo de render
function resize() {
  poke(30);
  const w = innerWidth, h = innerHeight;
  renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix();
  composer?.setPixelRatio(renderer.getPixelRatio()); composer?.setSize(w, h);
}
addEventListener('resize', resize); resize();

const tmp = new THREE.Vector3();
function project(v, el, hideBehind = true) {
  tmp.copy(v).project(camera);
  const vis = tmp.z < 1 && Math.abs(tmp.x) < 1.05 && Math.abs(tmp.y) < 1.05;
  if (!vis && hideBehind) { el.style.visibility = 'hidden'; return false; }
  el.style.visibility = '';
  el.style.transform = `translate(${(tmp.x * .5 + .5) * innerWidth}px, ${(-tmp.y * .5 + .5) * innerHeight}px) translate(-50%, -50%)`;
  return true;
}
let frame = 0, last = performance.now(), rendered = 0;
['pointerdown', 'pointermove', 'wheel', 'keydown', 'resize', 'touchmove'].forEach(ev => addEventListener(ev, () => poke(), { passive: true }));
const perf = { fps: 60, muestras: 0, bajadas: [] };
const occl = new THREE.Raycaster();
let wallMeshes = null;
const occluded = (from, to) => {
  wallMeshes ??= groups.arquitectura.filter(o => o.name === 'ARQ_Muros' || o.name === 'ARQ_Dinteles_Antepechos');
  occl.set(from, to.clone().sub(from).normalize()); occl.far = to.distanceTo(from) - 0.25;
  return occl.intersectObjects(wallMeshes, true).length > 0;
};
function tick(now) {
  requestAnimationFrame(tick);
  const rawDt = (now - last) / 1000, dt = Math.min(0.1, rawDt); last = now; frame++;
  if (!ready) return;
  // rendimiento: si la calidad alta no sostiene ~28 fps dentro del apartamento, se baja a media (salvo ?calidad=)
  if (rawDt > 0 && rawDt < 1 && dirty > 0) { perf.fps = perf.fps * 0.95 + (1 / rawDt) * 0.05; perf.muestras++; }
  if (!qualityPinned && quality === 'alta' && mode !== 'orbit' && perf.muestras > 120 && perf.fps < 26) {
    perf.bajadas.push({ fps: +perf.fps.toFixed(1), t: Math.round(now) }); perf.muestras = 0; setQuality('media');
    console.info('[ORA] Calidad ajustada a media por rendimiento:', perf.fps.toFixed(1), 'fps');
  }
  if (Math.abs(camera.fov - fovTarget) > 0.05) { camera.fov += (fovTarget - camera.fov) * Math.min(1, dt * 4); camera.updateProjectionMatrix(); }

  if (flight) {
    const k = Math.min(1, (now - flight.start) / flight.dur), e = ease(k);
    camera.position.lerpVectors(flight.p0, flight.p1, e);
    const t = flight.t0.clone().lerp(flight.t1, e);
    if (mode === 'orbit') { controls.target.copy(t); camera.lookAt(t); } else camera.lookAt(t);
    if (k >= 1) { const done = flight.done; flight = null; done?.(); }
  } else if (mode === 'orbit') {
    if (controls.update()) poke(2);
  } else if (mode === 'tour') {
    if (tourPlaying) tourT += dt;
    if (tourT >= TOUR_LEN) { tourT = TOUR_LEN; setTourPlaying(false); }
    const { u, room, chapter } = tourParam(tourT);
    const P = tourCurve.getPoint(u), L = lookCurve.getPoint(u);
    if (tourBlend) {   // transición suave desde la cámara anterior
      const k = Math.min(1, (now - tourBlend.start) / 2200), e = ease(k);
      P.lerpVectors(tourBlend.p, P, e); L.lerpVectors(tourBlend.l, L, e); if (k >= 1) tourBlend = null;
    }
    camera.position.copy(P); camera.lookAt(L); yawPitchFrom(L.clone().sub(P));
    if (room !== tourRoom) { tourRoom = room; if (room) markRoom(room); }
    if (chapter !== tourChapter) {
      tourChapter = chapter; $('#tourStep').textContent = `${chapter + 1}/12`; $('#tourName').textContent = CHAPTERS[chapter];
      const r = room ? roomById[room] : null;
      caption(r && chapter >= 3 ? r : null, `${chapter + 1} / 12 · ${CHAPTERS[chapter]}${chapter === 4 && balconyOn() ? ' · propuesta' : ''}`);
      clearTimeout(captionTimer); captionTimer = setTimeout(() => caption(null), 3200);
      if (chapter === 4 && !balconyOn()) $('#tourName').textContent = 'Ventana de la sala';
    }
    $('#tourProg').style.width = (tourT / TOUR_LEN * 100).toFixed(2) + '%';
    groups.cielo.forEach(o => { o.visible = camera.position.y < 2.3 && !verifiedOnly(); });
  } else if (mode === 'walk') {
    const fwd = (keys.has('w') || keys.has('arrowup') || pad.has('f') ? 1 : 0) - (keys.has('s') || keys.has('arrowdown') || pad.has('b') ? 1 : 0);
    const side = (keys.has('d') ? 1 : 0) - (keys.has('a') ? 1 : 0);
    const turn = (keys.has('arrowright') || pad.has('r') ? 1 : 0) - (keys.has('arrowleft') || pad.has('l') ? 1 : 0);
    yaw += turn * dt * 1.6;
    const sp = 1.25 * dt;
    if (fwd || side) {
      walkTarget = null;
      const dx = (Math.sin(yaw) * fwd + Math.cos(yaw) * side) * sp, dz = (-Math.cos(yaw) * fwd + Math.sin(yaw) * side) * sp;
      moveBy(dx, -dz);
    } else if (walkTarget) {
      const p = toPlan(camera.position); const dx = walkTarget.x - p.x, dy = walkTarget.y - p.y, dist = Math.hypot(dx, dy);
      if (dist < 0.05) walkTarget = null;
      else {
        const s = Math.min(dist, sp * 1.2); const before = { ...p };
        moveBy(dx / dist * s, dy / dist * s);
        const after = toPlan(camera.position); if (Math.hypot(after.x - before.x, after.y - before.y) < 1e-4) walkTarget = null;
        const targetYaw = Math.atan2(dx, dy); yaw += Math.atan2(Math.sin(targetYaw - yaw), Math.cos(targetYaw - yaw)) * Math.min(1, dt * 3);
      }
    }
    camera.lookAt(lookTarget());
    const r = roomAt(toPlan(camera.position)); if (r && r.id !== current) { markRoom(r.id); flashCaption(r, 2200); }
  }

  const lightsMoving = mode !== 'orbit' && updateLightPool(dt);
  const active = lightsMoving || flight || tourBlend || (mode === 'tour' && tourPlaying) || (mode === 'walk' && (keys.size || pad.size || walkTarget || drag));
  if (!active && dirty <= 0) return;
  dirty = Math.max(0, dirty - 1); rendered++;
  // sombras del sol: el encuadre sigue a la cámara dentro del apartamento
  if (mode !== 'orbit') { sun.target.position.set(camera.position.x * 0.5, 0, camera.position.z * 0.5); sun.position.copy(sun.target.position).addScaledVector(SUN_DIR, 14); }
  else { sun.target.position.set(0, 0, 0); sun.position.copy(SUN_DIR).multiplyScalar(14); }

  // puntos interactivos de espacios
  const camP = camera.position;
  for (const h of hotspots) {
    const show = mode !== 'tour' && !(mode === 'walk' && current === h.room.id);
    h.el.classList.toggle('off', !show);
    if (!show) continue;
    const anchor = mode === 'walk' ? toScene(VIEWS[h.room.id].orbit[0], VIEWS[h.room.id].orbit[1], 1.2) : h.anchor;
    if (!project(anchor, h.el)) continue;
    if (mode === 'walk' && frame % 12 === 0) h.blocked = occluded(camP, anchor);   // en primera persona solo se ven los espacios visibles desde aquí
    if (mode !== 'walk') h.blocked = false;
    h.el.classList.toggle('off', !!h.blocked);
    h.el.classList.toggle('near', mode === 'walk' || current === h.room.id);
  }
  // puntos de información: cerca, a la vista, y según la capa activa
  const zoomed = mode === 'orbit' && camera.position.distanceTo(controls.target) < 9.5 && !flight;
  const inside = mode === 'walk' || (mode === 'tour' && !tourPlaying);
  for (const p of pois) {
    let show = (inside || zoomed) && !(p.bal === true && !balconyOn()) && !(p.bal === false && balconyOn());
    if (verifiedOnly() && (p.cat === 'ilustrativo' || p.cat === 'propuesta')) show = false;
    if (show && inside) show = camP.distanceTo(p.pos) < 4.2;
    if (show && inside && (frame + p.id.length) % 10 === 0) p.blocked = occluded(camP, p.pos);
    if (!inside) p.blocked = false;
    show = show && !p.blocked && project(p.pos, p.el);
    p.el.classList.toggle('off', !show);
  }
  if (poiOpen) { const p = pois.find(q => q.id === poiOpen.id); if (p.el.classList.contains('off') && mode === 'walk' && camP.distanceTo(p.pos) > 5) closePoi(); }
  for (const d of dimLabels) { d.el.hidden = !dimGroup.visible; if (dimGroup.visible) project(d.pos, d.el); }

  for (const d of puertasOcultas) {   // abrir/cerrar con suavidad según la cercanía del visitante
    const pc = toPlan(camera.position);
    const abrir = mode === 'orbit' || (PUERTA_ROPAS && Math.hypot(pc.x - PUERTA_ROPAS.x, pc.y - PUERTA_ROPAS.y) < 1.4) ? 1 : 0;
    if (Math.abs(abrir - d.t) > 0.002) { d.t += (abrir - d.t) * Math.min(1, dt * 3); d.node.position.x = d.rec * d.t; poke(2); }
  }
  renderer.shadowMap.needsUpdate = true;
  if (!envHDR && entorno.estado.hdr) {   // el HDRI del exterior pasa a ser la luz ambiente y los reflejos
    envHDR = pmrem.fromEquirectangular(entorno.estado.hdr).texture;
    scene.environmentRotation.y = entorno.estado.rot; luzAmbiente(); poke(20);
  }
  if (composer) composer.render(dt); else renderer.render(scene, camera);
}
requestAnimationFrame(tick);

// ------------------------------------------------------------------ API para pruebas y consola
window.__ORA = { renderer, scene, camera, get composer() { return composer; } };
window.APTO_API = {
  get ready() { return ready; },
  setHora: h => setHora(h),
  setQuality: q => setQuality(q),
  entorno: () => ({ hdr: !!entorno.estado.hdr, arboles: entorno.estado.arboles, listo: entorno.estado.listo, envHDR: !!envHDR }),
  mat: n => ({ map: !!mats[n]?.map, normal: !!mats[n]?.normalMap, rough: !!mats[n]?.roughnessMap, fisico: !!mats[n]?.isMeshPhysicalMaterial }),
  puertas: () => puertasOcultas.map(d => +d.t.toFixed(2)),
  get state() {
    const p = toPlan(camera.position);
    const q = toPlan(controls.target);
    return {
      mode, balcony: balconyOn(), tourLen: TOUR_LEN, room: current, plan: { x: +p.x.toFixed(3), y: +p.y.toFixed(3) }, target: { x: +q.x.toFixed(3), y: +q.y.toFixed(3) },
      height: +camera.position.y.toFixed(3), tour: +tourT.toFixed(2), tourPlaying, chapter: tourChapter, floor: fin.piso, wall: fin.muros, kitchen: fin.cocina, bath: fin.bano,
      preset: fin.preset, custom: fin.personalizado, flying: !!flight, frame, rendered, quality, technical: techView, environment: entorno.group.visible, poi: poiOpen?.id || null, hora,
    };
  },
  get stats() {
    const i = renderer.info;
    return { ...stats, materiales: Object.keys(mats), texturas: cacheSize(), fps: +perf.fps.toFixed(1), ajustes: perf.bajadas, render: { llamadas: i.render.calls, triangulos: i.render.triangles, geometrias: i.memory.geometries, texturasGPU: i.memory.textures } };
  },
  setMode, goRoom, setFloor: id => setFinish('piso', id), setWall: id => setFinish('muros', id), setKitchen: id => setFinish('cocina', id), setBath: id => setFinish('bano', id), setPreset,
  walkTo, setBalcony, setQuality, exploreHere, setTourPlaying, openPoi: id => openPoi(pois.find(p => p.id === id)),
  move: (dx, dy) => moveBy(dx, dy), free,
  obstacles: () => obstaclesNow(), doorLeaves: () => segsNow(),
  tourSample: (step = 0.05) => { const out = []; for (let t = 0; t <= TOUR_LEN; t += step) { const { u, chapter, room } = tourParam(t); const P = tourCurve.getPoint(u); const q = toPlan(P); out.push({ t: +t.toFixed(2), x: q.x, y: q.y, h: P.y, c: chapter, room }); } return out; },
  chapters: () => CHAPTERS.map((c, i) => ({ c, t: TOUR.find(k => k.c === i)?.t })),
  wallColor: () => '#' + (mats.muro?.color.getHexString() || ''),
  matInfo: n => { const m = mats[n]; return m && { color: '#' + m.color.getHexString(), map: !!m.map, normal: !!m.normalMap, rough: m.roughness, mapId: m.map?.uuid }; },
  floorMap: () => !!mats.piso_madera?.map,
  original: () => original.visible,
  visible: name => { let v = null; model?.traverse(o => { if (o.name === name) v = shown(o); }); return v; },
  tourSeek: t => { tourT = t; tourBlend = null; poke(10); },
  render: (n = 3) => poke(n),
  topView: () => { if (mode !== 'orbit') setMode('orbit'); flight = null; camera.position.set(0, 17 / Math.min(1, camera.aspect), 0.0001); controls.target.set(0, 0, 0); camera.lookAt(0, 0, 0); controls.update(); },
  // distancia horizontal desde un punto de la planta hasta la primera superficie del modelo 3D (para medir pasos)
  rayPlan: (x, y, h, dx, dy) => {
    const o = toScene(x, y, h), d = toScene(x + dx, y + dy, h).sub(o).normalize();
    const hits = new THREE.Raycaster(o, d, 0, 20).intersectObject(model, true).filter(i => shown(i.object) && !/Cielo|Luminarias/.test(i.object.name + (i.object.parent?.name || '')));
    return hits.length ? +hits[0].distance.toFixed(3) : null;
  },
  modelos: () => { const out = {}; model.traverse(o => { if (o.userData?.modelo) { let n = 0; o.traverse(q => { if (q.isMesh) n++; }); out[o.name] = n; } }); return out; },
  // encuadre de arquitectura: cámara nivelada (verticales rectas), lente de ~24 mm y desplazamiento óptico hacia abajo
  arch: (x, y, lx, ly, mm = 24, shift = 0.12, h = 1.45) => {
    APTO_API.pose(x, y, h, lx, ly, h);
    const hf = 2 * Math.atan(18 / mm), vis = 2 * Math.atan(Math.tan(hf / 2) / camera.aspect);
    const full = 2 * Math.atan(Math.tan(vis / 2) * (1 + 2 * shift)) * 180 / Math.PI;
    fovTarget = full; camera.fov = full;
    const w = innerWidth, hh = innerHeight; camera.setViewOffset(w, hh * (1 + 2 * shift), 0, hh * 2 * shift, w, hh); camera.updateProjectionMatrix(); poke(6);
  },
  archOff: () => { camera.clearViewOffset(); fovTarget = mode === 'orbit' ? 42 : (camera.aspect < 0.9 ? 74 : 60); poke(6); },
  pose: (x, y, h, lx, ly, lh) => { flight = null; poke(6); camera.position.copy(toScene(x, y, h)); const l = toScene(lx, ly, lh); camera.lookAt(l); yawPitchFrom(l.clone().sub(camera.position)); if (mode === 'orbit') controls.target.copy(l); },
};
