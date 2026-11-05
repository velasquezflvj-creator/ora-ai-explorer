// Catálogo de acabados ILUSTRATIVOS (no contractuales) y las tres propuestas de diseño.
// Cada opción indica qué materiales del GLB cambia; los nombres de material son estables.
import { textura } from './texturas.mjs';

// ---------------------------------------------------------------- recetas de textura
export const RECETAS = {
  roble_claro: { gen: 'madera', claro: '#dccbb0', oscuro: '#a88f6e', seed: 3, rough: 0.55 },
  nogal: { gen: 'madera', claro: '#8a6a52', oscuro: '#4e3a2c', seed: 5, rough: 0.5, nudos: 0.15 },
  fresno: { gen: 'madera', claro: '#e8dcc8', oscuro: '#bea888', seed: 8, rough: 0.6, nudos: 0.1 },
  piedra_gris: { gen: 'piedra', base: '#8f8d88', veta: '#bdbab2', lx: 0.6, ly: 1.2, junta: '#6c6a65', rough: 0.3, vetas: 0.3, seed: 12 },
  porcelanato_arena: { gen: 'piedra', base: '#d8cfbf', veta: '#ebe4d6', lx: 0.6, ly: 0.6, junta: '#b9af9f', rough: 0.3, vetas: 0.2, seed: 14 },
  microcemento_claro: { gen: 'microcemento', base: '#d8d4cc', sombra: '#b6b1a8', seed: 31, rough: 0.55 },
  pintura: { gen: 'pintura' },
  chapa_roble: { gen: 'chapa', claro: '#dac6a6', oscuro: '#b0946c', seed: 51, contraste: 0.7 },
  chapa_roble_medio: { gen: 'chapa', claro: '#b8987a', oscuro: '#7e634b', seed: 52 },
  chapa_nogal: { gen: 'chapa', claro: '#6e5442', oscuro: '#3e2d22', seed: 53, rough: 0.45 },
  chapa_fresno: { gen: 'chapa', claro: '#eee3d0', oscuro: '#cdb999', seed: 54, contraste: 0.7 },
  grafito: { gen: 'chapa', claro: '#4a4b4f', oscuro: '#3a3b3e', seed: 55, contraste: 0.2, rough: 0.6 },
  laca_blanca: { gen: 'chapa', claro: '#f1efea', oscuro: '#e9e6e0', seed: 56, contraste: 0.05, rough: 0.3 },
  cuarzo_blanco: { gen: 'marmol', base: '#f2f0eb', veta: '#c9c4b9', intensidad: 0.15, grano: 0.6, seed: 21, rough: 0.16 },
  nero_marquina: { gen: 'marmol', base: '#2b2b2d', veta: '#d6d3cc', intensidad: 0.9, seed: 23, rough: 0.14 },
  calacatta: { gen: 'marmol', base: '#f5f3ef', veta: '#8f897f', veta2: '#c7b28c', intensidad: 1, seed: 25, rough: 0.12 },
  zellige: { gen: 'baldosa', base: '#f3efe6', base2: '#e2dbcd', lx: 0.075, ly: 0.15, junta: '#d6cfc2', variacion: 0.12, ondas: 1.4, trabada: true, paño: 0.6, rough: 0.12, seed: 42 },
  baldosa_arena: { gen: 'baldosa', base: '#dccfba', base2: '#cfc0a8', lx: 0.3, ly: 0.6, junta: '#c4b8a3', paño: 1.2, seed: 43, rough: 0.22 },
  piedra_bano: { gen: 'piedra', base: '#8f8d88', veta: '#b3b0a8', lx: 0.6, ly: 1.2, junta: '#73716c', rough: 0.25, vetas: 0.4, seed: 16 },
  baldosa_blanca: { gen: 'baldosa', base: '#f6f5f1', base2: '#efeee9', lx: 0.075, ly: 0.30, junta: '#e2e0da', paño: 0.6, ondas: 0.7, seed: 44, rough: 0.08 },
  baldosa_ropas: { gen: 'baldosa', base: '#f0efeb', base2: '#e8e7e2', lx: 0.2, ly: 0.2, junta: '#d7d5cf', paño: 0.8, seed: 45, rough: 0.15 },
  piso_bano_arena: { gen: 'piedra', base: '#c3b7a3', veta: '#d4c9b6', lx: 0.6, ly: 0.6, junta: '#a99d89', rough: 0.35, vetas: 0.15, seed: 17 },
  piso_bano_piedra: { gen: 'piedra', base: '#5f5e5b', veta: '#7e7c77', lx: 0.6, ly: 0.6, junta: '#4c4b48', rough: 0.4, vetas: 0.3, seed: 18 },
  piso_bano_claro: { gen: 'microcemento', base: '#dedad2', sombra: '#c2bdb3', seed: 33, rough: 0.5 },
  deck: { gen: 'deck', claro: '#a77b55', oscuro: '#6e4b31' },
  tela_lino: { gen: 'tela', base: '#ffffff', seed: 61, paño: 0.5 },
  tela_boucle: { gen: 'tela', base: '#ffffff', seed: 62, paño: 0.35, trama: 1.6, moteado: 0.2 },
  tapete_calido: { gen: 'tapete', base: '#d6c8b0', linea: '#b49f7d' },
  tapete_gris: { gen: 'tapete', base: '#6a6863', linea: '#8a877f', seed: 82 },
  tapete_claro: { gen: 'tapete', base: '#ece7dd', linea: '#d8cfbf', seed: 83 },
  cuadro_calido: { gen: 'cuadro', fondo: '#efe6d6', a: '#c9875f', b: '#7d8c6d', c: '#3b3530' },
  cuadro_sofisticado: { gen: 'cuadro', fondo: '#d9d6cf', a: '#2e3a48', b: '#b28b5e', c: '#151515', seed: 102 },
  cuadro_luminoso: { gen: 'cuadro', fondo: '#f4f1ea', a: '#d8c3a5', b: '#b9c4b4', c: '#8a8f88', seed: 103 },
};

// ---------------------------------------------------------------- opciones por elemento
// m: material → { t: receta, c: color (multiplica la textura), r: rugosidad, n: intensidad de relieve, mt: metalicidad }
export const OPCIONES = {
  piso: [
    { id: 'roble', nombre: 'Roble claro', muestra: 'linear-gradient(90deg,#dccbb0,#b39a78)', m: { piso_madera: { t: 'roble_claro', n: 0.6 }, guardaescoba: { c: '#f3efe7', r: 0.5 } } },
    { id: 'nogal', nombre: 'Nogal', muestra: 'linear-gradient(90deg,#86603f,#5a3c26)', m: { piso_madera: { t: 'nogal', n: 0.6 }, guardaescoba: { c: '#f1eee8', r: 0.5 } } },
    { id: 'piedra', nombre: 'Porcelanato piedra gris 60 × 120', muestra: 'linear-gradient(135deg,#97958f,#7d7b76)', m: { piso_madera: { t: 'piedra_gris', n: 0.5 }, guardaescoba: { c: '#7f7d78', r: 0.35 } } },
    { id: 'arena', nombre: 'Porcelanato arena 60 × 60', muestra: 'linear-gradient(135deg,#ddd4c5,#cbbfab)', m: { piso_madera: { t: 'porcelanato_arena', n: 0.5 }, guardaescoba: { c: '#d0c6b6', r: 0.35 } } },
    { id: 'microcemento', nombre: 'Microcemento claro', muestra: 'linear-gradient(135deg,#dad6ce,#bcb7ae)', m: { piso_madera: { t: 'microcemento_claro', n: 0.4 }, guardaescoba: { c: '#f2f0eb', r: 0.5 } } },
  ],
  muros: [
    { id: 'marfil', nombre: 'Marfil', muestra: '#ece5d6', m: { muro: { t: 'pintura', c: '#f3ecdd', n: 0.5 } } },
    { id: 'blanco', nombre: 'Blanco cálido', muestra: '#f2f0eb', m: { muro: { t: 'pintura', c: '#faf8f3', n: 0.5 } } },
    { id: 'arena', nombre: 'Arena', muestra: '#e0d1b8', m: { muro: { t: 'pintura', c: '#e7d8bf', n: 0.5 } } },
    { id: 'greige', nombre: 'Greige', muestra: '#c9c2b6', m: { muro: { t: 'pintura', c: '#cfc8bc', n: 0.5 } } },
    { id: 'niebla', nombre: 'Gris niebla', muestra: '#cfd2cf', m: { muro: { t: 'pintura', c: '#d5d8d5', n: 0.5 } } },
    { id: 'salvia', nombre: 'Salvia', muestra: '#b9c2ad', m: { muro: { t: 'pintura', c: '#bfc8b3', n: 0.5 } } },
  ],
  cocina: [
    { id: 'roble_cuarzo', nombre: 'Roble y cuarzo blanco', muestra: 'linear-gradient(90deg,#c9a57a 50%,#efede8 50%)',
      m: { gabinete_cocina: { t: 'chapa_roble', r: 0.5 }, meson: { t: 'cuarzo_blanco', n: 0.2 }, salpicadero: { t: 'zellige', n: 0.8 } } },
    { id: 'grafito_piedra', nombre: 'Grafito y piedra negra', muestra: 'linear-gradient(90deg,#45464a 50%,#2b2b2d 50%)',
      m: { gabinete_cocina: { t: 'grafito', r: 0.62 }, meson: { t: 'nero_marquina', n: 0.2 }, salpicadero: { t: 'nero_marquina', n: 0.2 } } },
    { id: 'blanco_marmol', nombre: 'Laca blanca y mármol', muestra: 'linear-gradient(90deg,#f0eee9 50%,#d9d3c6 50%)',
      m: { gabinete_cocina: { t: 'laca_blanca', r: 0.3 }, meson: { t: 'calacatta', n: 0.2 }, salpicadero: { t: 'calacatta', n: 0.2 } } },
  ],
  bano: [
    { id: 'arena', nombre: 'Cerámica arena y roble', muestra: 'linear-gradient(90deg,#d6c9b3 50%,#b08659 50%)',
      m: { revestimiento_bano: { t: 'baldosa_arena', n: 0.8 }, piso_ceramica: { t: 'piso_bano_arena', n: 0.5 }, mueble_bano: { t: 'chapa_roble', r: 0.5 }, meson_bano: { t: 'cuarzo_blanco', n: 0.2 } } },
    { id: 'piedra', nombre: 'Piedra gris y nogal', muestra: 'linear-gradient(90deg,#8f8d88 50%,#5a3c26 50%)',
      m: { revestimiento_bano: { t: 'piedra_bano', n: 0.6 }, piso_ceramica: { t: 'piso_bano_piedra', n: 0.5 }, mueble_bano: { t: 'chapa_nogal', r: 0.45 }, meson_bano: { t: 'nero_marquina', n: 0.2 } } },
    { id: 'blanco', nombre: 'Enchape blanco y laca', muestra: 'linear-gradient(90deg,#f5f4f0 50%,#dad6ce 50%)',
      m: { revestimiento_bano: { t: 'baldosa_blanca', n: 0.8 }, piso_ceramica: { t: 'piso_bano_claro', n: 0.4 }, mueble_bano: { t: 'laca_blanca', r: 0.3 }, meson_bano: { t: 'calacatta', n: 0.2 } } },
  ],
};

// Textiles, carpintería y metales: acompañan a cada propuesta (no tienen selector propio).
const AMBIENTE = {
  calida: {
    tela_sofa: { t: 'tela_lino', c: '#d3c7b5' }, tela_acento: { t: 'tela_lino', c: '#a8603e' }, tela_cama: { t: 'tela_lino', c: '#f3efe6' },
    tela_silla: { t: 'tela_boucle', c: '#c2b39b' }, tela_cortina: { t: 'tela_lino', c: '#f1eadf' }, toalla: { t: 'tela_boucle', c: '#efe9de' },
    madera_mueble: { t: 'chapa_roble_medio' }, laca_mueble: { t: 'laca_blanca', c: '#efe8dc' }, carpinteria: { t: 'chapa_roble' }, marco_puerta: { t: 'chapa_roble' },
    puerta_entrada: { t: 'chapa_nogal' }, laton: { c: '#c9a26a', r: 0.32, mt: 1 }, textil_tapete: { t: 'tapete_calido' }, cuadro: { t: 'cuadro_calido' },
    maceta: { c: '#b7876a', r: 0.85 }, ceramica_deco: { c: '#e4d9c6', r: 0.4 },
  },
  sofisticada: {
    tela_sofa: { t: 'tela_lino', c: '#5d5e62' }, tela_acento: { t: 'tela_lino', c: '#8e5b36' }, tela_cama: { t: 'tela_lino', c: '#e4e2de' },
    tela_silla: { t: 'tela_boucle', c: '#47484c' }, tela_cortina: { t: 'tela_lino', c: '#cdc8bf' }, toalla: { t: 'tela_boucle', c: '#8b8984' },
    madera_mueble: { t: 'chapa_nogal' }, laca_mueble: { t: 'grafito', c: '#ffffff' }, carpinteria: { t: 'chapa_nogal' }, marco_puerta: { t: 'chapa_nogal' },
    puerta_entrada: { t: 'grafito' }, laton: { c: '#202022', r: 0.4, mt: 0.8 }, textil_tapete: { t: 'tapete_gris' }, cuadro: { t: 'cuadro_sofisticado' },
    maceta: { c: '#3c3b39', r: 0.6 }, ceramica_deco: { c: '#2f2f31', r: 0.3 },
  },
  luminosa: {
    tela_sofa: { t: 'tela_lino', c: '#ece8e0' }, tela_acento: { t: 'tela_lino', c: '#aab69f' }, tela_cama: { t: 'tela_lino', c: '#f8f7f3' },
    tela_silla: { t: 'tela_boucle', c: '#e5e0d6' }, tela_cortina: { t: 'tela_lino', c: '#f8f6f1' }, toalla: { t: 'tela_boucle', c: '#f5f3ee' },
    madera_mueble: { t: 'chapa_fresno' }, laca_mueble: { t: 'laca_blanca' }, carpinteria: { t: 'laca_blanca' }, marco_puerta: { t: 'laca_blanca' },
    puerta_entrada: { t: 'chapa_fresno' }, laton: { c: '#cfcfcf', r: 0.25, mt: 1 }, textil_tapete: { t: 'tapete_claro' }, cuadro: { t: 'cuadro_luminoso' },
    maceta: { c: '#e6e1d8', r: 0.7 }, ceramica_deco: { c: '#f1eee8', r: 0.35 },
  },
};

export const PRESETS = [
  { id: 'calida', nombre: 'Contemporánea cálida', corto: 'Cálida', descripcion: 'Madera clara, tonos neutros y acabados naturales', piso: 'roble', muros: 'marfil', cocina: 'roble_cuarzo', bano: 'arena' },
  { id: 'sofisticada', nombre: 'Moderna sofisticada', corto: 'Sofisticada', descripcion: 'Piedra, tonos grises y carpintería oscura', piso: 'piedra', muros: 'greige', cocina: 'grafito_piedra', bano: 'piedra' },
  { id: 'luminosa', nombre: 'Minimalista luminosa', corto: 'Luminosa', descripcion: 'Superficies claras y materiales de apariencia ligera', piso: 'microcemento', muros: 'blanco', cocina: 'blanco_marmol', bano: 'blanco' },
];

// Materiales fijos (no dependen de la propuesta).
export const FIJOS = {
  revestimiento_ropas: { t: 'baldosa_ropas', n: 0.6 }, piso_exterior: { t: 'deck', n: 0.8 },
  ceramica_blanca: { c: '#f7f7f5', r: 0.08 }, cromo: { c: '#e2e3e5', r: 0.06, mt: 1 }, acero: { c: '#c9cacc', r: 0.3, mt: 1 },
  electro: { c: '#bfc0c2', r: 0.32, mt: 0.9 }, alfeizar: { t: 'cuarzo_blanco', n: 0.2 },
};

export function aplicar(mats, mapa) {
  for (const [nombre, s] of Object.entries(mapa)) {
    const m = mats[nombre]; if (!m) continue;
    const had = !!m.map, hadN = !!m.normalMap, hadR = !!m.roughnessMap;
    if (s.t) {
      const tx = textura(s.t, RECETAS[s.t]);
      m.map = tx.map; m.normalMap = tx.normalMap || null; m.roughnessMap = tx.roughnessMap || null;
      m.color.set(s.c || '#ffffff');
      if (m.normalMap) m.normalScale.set(s.n ?? 0.7, s.n ?? 0.7);
      m.roughness = tx.roughnessMap ? 1 : (s.r ?? m.userData.baseRough ?? m.roughness);
      if (s.r != null && !tx.roughnessMap) m.roughness = s.r;
    } else {
      m.map = null; m.normalMap = null; m.roughnessMap = null;
      if (s.c) m.color.set(s.c);
      if (s.r != null) m.roughness = s.r;
    }
    if (s.mt != null) m.metalness = s.mt;
    if (had !== !!m.map || hadN !== !!m.normalMap || hadR !== !!m.roughnessMap) m.needsUpdate = true;
  }
}
export const opcion = (tipo, id) => OPCIONES[tipo].find(o => o.id === id);
export const ambiente = id => AMBIENTE[id];
