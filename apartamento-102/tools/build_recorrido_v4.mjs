// Construye el recorrido V4 del apartamento 102 sin tocar V1, V2 ni V3:
//   dist/recorrido-v4-app.js   (src/app-recorrido-v4.mjs empaquetado, IIFE; funciona también con file://)
//   dist/recorrido-v4-datos.js (GLB derivado con UV de luz, muebles, texturas, sondas, horneados y atlas de luz)
//   Usa modelo/web/v4/ (blender/scripts/hornear_lightmaps_web.py): apto-102-v4.glb + atlas_luz.hdr + lightmaps.json.
//   Si no existe, usa el GLB original sin atlas (el visor funciona igual que la V3).
//   Además de las entradas del V2 usa modelo/web/horneado/ (blender/scripts/hornear_planos_web.py).
//
// Entradas:
//   modelo/apto-102-propuesta.glb, data/propuesta-102.json, modelo/muebles/*.glb, modelo/exterior/*  (las mismas del V1)
//   modelo/texturas/*.jpg                    texturas procedurales del V1 (base)
//   modelo/web/texturas/*.jpg + escala.json  texturas fotográficas CC0 exportadas desde Blender (reemplazan a las del V1
//                                            con la misma clave); se generan con blender/scripts/exportar_web.py
//   modelo/web/sondas/*.hdr + sondas.json    sondas de luz 360° (Cycles), mismo script
// Si modelo/web no existe, el V2 se construye con las texturas del V1 y sin sondas.
//
// Requisitos: three 0.180.0 y esbuild 0.25 resolubles desde la raíz (`npm i --no-save three@0.180.0 esbuild@0.25.10`).
//   node apartamento-102/tools/build_recorrido_v4.mjs
import { execFileSync } from 'node:child_process';
import { readFileSync, writeFileSync, mkdirSync, readdirSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const repo = join(root, '..');
mkdirSync(join(root, 'dist'), { recursive: true });
const b64 = p => readFileSync(p).toString('base64');
const jpgs = dir => (existsSync(dir) ? readdirSync(dir).filter(f => f.endsWith('.jpg')) : []);

// V4: copia derivada del modelo con TEXCOORD_1 (misma geometría que el original: tools/verificar_glb.mjs)
const v4dir = join(root, 'modelo/web/v4');
const usarV4 = existsSync(join(v4dir, 'apto-102-v4.glb')) && existsSync(join(v4dir, 'atlas_luz.hdr'));
const glb = b64(join(usarV4 ? v4dir : join(root, 'modelo'), usarV4 ? 'apto-102-v4.glb' : 'apto-102-propuesta.glb'));
const lightmaps = usarV4 ? { meta: JSON.parse(readFileSync(join(v4dir, 'lightmaps.json'), 'utf8')), atlas: b64(join(v4dir, 'atlas_luz.hdr')) } : null;
const geo = JSON.parse(readFileSync(join(root, 'data/propuesta-102.json'), 'utf8'));
delete geo.original.rotulos;
const propuesta = geo.balcon;
const muebles = Object.fromEntries(readdirSync(join(root, 'modelo/muebles')).filter(f => f.endsWith('.glb'))
  .map(f => [f.replace(/\.glb$/, ''), b64(join(root, 'modelo/muebles', f))]));

// texturas: base del V1 + reemplazos fotográficos de Blender
const tdir = join(root, 'modelo/texturas'), wdir = join(root, 'modelo/web/texturas');
const escala = JSON.parse(readFileSync(join(tdir, 'escala.json'), 'utf8'));
const img = Object.fromEntries(jpgs(tdir).map(f => [f.replace(/\.jpg$/, ''), b64(join(tdir, f))]));
const reemplazos = [];
if (existsSync(join(wdir, 'escala.json'))) {
  Object.assign(escala, JSON.parse(readFileSync(join(wdir, 'escala.json'), 'utf8')));
  // una clave con foto pierde los canales del V1 que la foto no trae (p. ej. yeso: solo relieve y rugosidad)
  const claves = new Set(jpgs(wdir).map(f => f.replace(/_(color|normal|rough)\.jpg$/, '')));
  for (const k of claves) for (const c of ['color', 'normal', 'rough']) delete img[`${k}_${c}`];
  for (const f of jpgs(wdir)) { img[f.replace(/\.jpg$/, '')] = b64(join(wdir, f)); reemplazos.push(f); }
}
const texturas = { escala, img, fotograficas: reemplazos.length > 0 };

// sondas de luz y reflejos
const sdir = join(root, 'modelo/web/sondas');
let sondas = null;
if (existsSync(join(sdir, 'sondas.json'))) {
  const s = JSON.parse(readFileSync(join(sdir, 'sondas.json'), 'utf8'));
  sondas = { meta: s.sondas, px: s.px, hdr: Object.fromEntries(Object.entries(s.sondas).map(([k, v]) => [k, b64(join(sdir, v.archivo))])) };
}

// luz horneada del piso y del cielo raso (V3)
const hdir = join(root, 'modelo/web/horneado');
let horneado = null;
if (existsSync(join(hdir, 'horneado.json'))) {
  const meta = JSON.parse(readFileSync(join(hdir, 'horneado.json'), 'utf8'));
  horneado = { meta, piso: b64(join(hdir, meta.piso.archivo)), cielo: b64(join(hdir, meta.cielo.archivo)) };
}

const edir = join(root, 'modelo/exterior');
const exterior = { ...JSON.parse(readFileSync(join(edir, 'hdri.json'), 'utf8')), hdr: b64(join(edir, 'parque.hdr')),
  hojas: Object.fromEntries(readdirSync(edir).filter(f => /^hoja_.*\.png$/.test(f)).map(f => [f.slice(5, -4), b64(join(edir, f))])),
  corteza: { color: b64(join(edir, 'corteza_color.jpg')), normal: b64(join(edir, 'corteza_normal.jpg')), rough: b64(join(edir, 'corteza_rough.jpg')) } };

writeFileSync(join(root, 'dist/recorrido-v4-datos.js'),
  '/* Generado por tools/build_recorrido_v4.mjs: recorrido V4 del apartamento 102 (rediseño conceptual, no planta verificada). */\n' +
  `window.APTO102=${JSON.stringify({ glb, geo, propuesta, muebles, texturas, exterior, sondas, horneado, lightmaps })};\n`);

const esbuild = process.env.ESBUILD || join(repo, 'node_modules/.bin/esbuild');
execFileSync(esbuild, [join(root, 'src/app-recorrido-v4.mjs'), '--bundle', '--format=iife', '--target=es2020', '--minify',
  '--legal-comments=eof', `--outfile=${join(root, 'dist/recorrido-v4-app.js')}`], { stdio: 'inherit', cwd: repo });
console.log(`recorrido V4 listo: atlas de luz ${lightmaps ? lightmaps.meta.objetos.length + ' mallas' : 'NO (GLB original)'}, luz horneada ${horneado ? 'sí' : 'no'}, ${reemplazos.length} texturas fotográficas, ${sondas ? Object.keys(sondas.meta).length : 0} sondas`);
