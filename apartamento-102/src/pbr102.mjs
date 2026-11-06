// Materiales PBR propios del apartamento 102: texturas generadas con tools/texturas_pbr.py (sin licencias de
// terceros), embebidas en dist/datos.js. Cada textura cubre una superficie real (escala.json) y se repite
// según las UV del modelo, que están en metros.
import * as THREE from 'three';
import { aplicar as aplicarBase } from '../../apartamento-104/src/acabados.mjs';

let DATOS = null, ANISO = 4, onCarga = () => {};
const cache = new Map();

export function initPBR(texturas, { anisotropy = 4, poke = () => {} } = {}) { DATOS = texturas; ANISO = anisotropy; onCarga = poke; }

function tex(nombre, tipo) {
  const k = `${nombre}_${tipo}`;
  if (cache.has(k)) return cache.get(k);
  const b64 = DATOS?.img?.[k]; if (!b64) { cache.set(k, null); return null; }
  const img = new Image(); const t = new THREE.Texture(img);
  img.onload = () => { t.needsUpdate = true; onCarga(8); };
  img.src = `data:image/jpeg;base64,${b64}`;
  const [w, h] = DATOS.escala[nombre] || [1, 1];
  t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(1 / w, 1 / h);
  t.colorSpace = tipo === 'color' ? THREE.SRGBColorSpace : THREE.NoColorSpace;
  t.anisotropy = ANISO;
  cache.set(k, t); return t;
}

// entrada: { img: 'travertino', c: '#ffffff', n: 0.8 (relieve), r: rugosidad base, mt: metalicidad }
function aplicarImg(m, s) {
  const had = [!!m.map, !!m.normalMap, !!m.roughnessMap];
  const col = tex(s.img, 'color'), nor = tex(s.img, 'normal'), rou = tex(s.img, 'rough');
  m.map = col; m.normalMap = nor; m.roughnessMap = rou;
  m.color.set(s.c || '#ffffff');
  if (nor) m.normalScale.set(s.n ?? 0.8, s.n ?? 0.8);        // mapas OpenGL (Y+)
  m.roughness = rou ? (s.r ?? 1) : (s.r ?? m.roughness);
  if (s.mt != null) m.metalness = s.mt;
  if (had[0] !== !!col || had[1] !== !!nor || had[2] !== !!rou) m.needsUpdate = true;
}

/** Igual que aplicar() del 104, pero entiende las entradas con imagen propia ({ img }). */
export function aplicar102(mats, mapa) {
  const base = {};
  for (const [nombre, s] of Object.entries(mapa)) {
    const m = mats[nombre]; if (!m) continue;
    if (s.img) aplicarImg(m, s); else base[nombre] = s;
  }
  aplicarBase(mats, base);
}

export const texturaPBR = tex;

// ---------------------------------------------------------------- propuesta «Monocromática cálida» (por defecto)
// Paleta del cliente: blanco cálido y marfil, greige y arena, travertino claro, roble claro con moderación,
// gris cálido y negro mate solo como acento.
export const OPC_PREMIUM = {
  piso: { id: 'piedra_calida', nombre: 'Porcelanato piedra caliza 60 × 120', muestra: 'linear-gradient(135deg,#e2d9cb,#cdc1ae)',
    m: { piso_madera: { img: 'piso_piedra', n: 0.6 }, guardaescoba: { c: '#efe8dd', r: 0.6 } } },
  muros: { id: 'blanco_calido', nombre: 'Blanco cálido', muestra: '#f2ece2', m: { muro: { img: 'yeso', c: '#f3ede3', n: 0.15 }, cielo: { c: '#f7f3ec', r: 0.95 } } },
  cocina: { id: 'roble_travertino', nombre: 'Roble claro y travertino', muestra: 'linear-gradient(90deg,#c9a97f 50%,#e6dccb 50%)',
    m: { gabinete_cocina: { img: 'roble', c: '#efe9e0', n: 0.5 }, meson: { img: 'travertino', n: 0.5 }, salpicadero: { img: 'travertino', n: 0.2 } } },
  bano: { id: 'travertino_arena', nombre: 'Travertino y laca arena', muestra: 'linear-gradient(90deg,#e3d8c6 50%,#d6c6b0 50%)',
    m: { revestimiento_bano: { img: 'travertino_enchape', n: 0.18 }, piso_ceramica: { img: 'travertino_enchape', n: 0.25 }, mueble_bano: { img: 'laca_mate', c: '#d8c9b3', n: 0.3 }, meson_bano: { img: 'travertino', n: 0.5 } } },
};
export const AMB_PREMIUM = {
  tela_sofa: { img: 'lino', c: '#d5cab9', n: 0.9 }, tela_cabecero: { img: 'lino', c: '#cbbda8', n: 1.0 }, tela_cama: { img: 'lino', c: '#f2ede4', n: 0.7 },
  tela_acento: { img: 'lino', c: '#a99a87', n: 0.9 }, tela_silla: { img: 'boucle', c: '#efe8dc', n: 1.4 }, tela_cortina: { img: 'lino', c: '#e6ddd0', n: 0.8 },
  tela_visillo: { img: 'lino', c: '#faf7f1', n: 0.4 }, toalla: { img: 'boucle', c: '#ece5d9', n: 1.2 }, textil_tapete: { img: 'tapete', n: 1.0 },
  madera_mueble: { img: 'roble', c: '#efe9e0', n: 0.5 }, puerta_entrada: { img: 'roble', c: '#d9c3a3', n: 0.5 },
  laca_mueble: { img: 'laca_mate', c: '#ddd1bf', n: 0.3 }, carpinteria: { img: 'laca_mate', c: '#efe9df', n: 0.25 }, marco_puerta: { img: 'laca_mate', c: '#efe9df', n: 0.25 },
  revestimiento_ropas: { img: 'travertino_enchape', n: 0.18 }, alfeizar: { img: 'travertino', n: 0.4 }, piso_exterior: { img: 'deck', n: 0.8 },
  ceramica_calida: { c: '#ece6dc', r: 0.28 }, ceramica_deco: { c: '#e7dfd1', r: 0.45 }, laton_cepillado: { c: '#c8ab7d', r: 0.34, mt: 1 },
  laton: { c: '#c8ab7d', r: 0.34, mt: 1 }, metal_negro: { c: '#1d1c1b', r: 0.6, mt: 0.5 }, rejilla: { c: '#2a2928', r: 0.7, mt: 0.3 },
  maceta: { c: '#cfc5b6', r: 0.85 }, cuadro: { img: 'arte', n: 0.6 }, carcasa: { c: '#3a3530', r: 0.9 }, electro_blanco: { c: '#f2f1ee', r: 0.3 },
  vegetal: { c: '#7d8a5a', r: 0.8 }, rama_seca: { c: '#8b7660', r: 0.9 }, marco: { c: '#2b2a29', r: 0.45, mt: 0.6 },
};
export const PRESET_PREMIUM = { id: 'calida_premium', nombre: 'Monocromática cálida', corto: 'Cálida premium', descripcion: 'Blanco cálido, greige, travertino claro, roble con moderación y negro mate como acento',
  piso: 'piedra_calida', muros: 'blanco_calido', cocina: 'roble_travertino', bano: 'travertino_arena' };
