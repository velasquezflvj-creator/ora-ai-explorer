// Construye el recorrido V2 del apartamento 102 sin tocar el visor original:
//   dist/recorrido-app.js   (src/app-recorrido.mjs empaquetado, IIFE; funciona también con file://)
//   dist/recorrido-datos.js (GLB, geometría, muebles, texturas y sondas en base64)
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
//   node apartamento-102/tools/build_recorrido.mjs
import { execFileSync } from 'node:child_process';
import { readFileSync, writeFileSync, mkdirSync, readdirSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const repo = join(root, '..');
mkdirSync(join(root, 'dist'), { recursive: true });
const b64 = p => readFileSync(p).toString('base64');
const jpgs = dir => (existsSync(dir) ? readdirSync(dir).filter(f => f.endsWith('.jpg')) : []);

const glb = b64(join(root, 'modelo/apto-102-propuesta.glb'));
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

const edir = join(root, 'modelo/exterior');
const exterior = { ...JSON.parse(readFileSync(join(edir, 'hdri.json'), 'utf8')), hdr: b64(join(edir, 'parque.hdr')),
  hojas: Object.fromEntries(readdirSync(edir).filter(f => /^hoja_.*\.png$/.test(f)).map(f => [f.slice(5, -4), b64(join(edir, f))])),
  corteza: { color: b64(join(edir, 'corteza_color.jpg')), normal: b64(join(edir, 'corteza_normal.jpg')), rough: b64(join(edir, 'corteza_rough.jpg')) } };

writeFileSync(join(root, 'dist/recorrido-datos.js'),
  '/* Generado por tools/build_recorrido.mjs: recorrido V2 del apartamento 102 (rediseño conceptual, no planta verificada). */\n' +
  `window.APTO102=${JSON.stringify({ glb, geo, propuesta, muebles, texturas, exterior, sondas })};\n`);

const esbuild = process.env.ESBUILD || join(repo, 'node_modules/.bin/esbuild');
execFileSync(esbuild, [join(root, 'src/app-recorrido.mjs'), '--bundle', '--format=iife', '--target=es2020', '--minify',
  '--legal-comments=eof', `--outfile=${join(root, 'dist/recorrido-app.js')}`], { stdio: 'inherit', cwd: repo });
console.log(`recorrido V2 listo: ${reemplazos.length} texturas fotográficas, ${sondas ? Object.keys(sondas.meta).length : 0} sondas`);
