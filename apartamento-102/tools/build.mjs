// Construye dist/app.js (script clásico IIFE, funciona también abriendo index.html con file://)
// y dist/datos.js (GLB en base64 + geometría), para que el visor no dependa de fetch.
//
// Requisitos: three 0.180.0 resoluble como paquete "three" (p. ej. `npm i --no-save three@0.180.0`
// en la raíz del repositorio) y esbuild (`npx esbuild` o variable ESBUILD con su ruta).
//   node apartamento-102/tools/build.mjs
import { execFileSync } from 'node:child_process';
import { readFileSync, writeFileSync, mkdirSync, readdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
mkdirSync(join(root, 'dist'), { recursive: true });

const glb = readFileSync(join(root, 'modelo/apto-102-propuesta.glb')).toString('base64');
const geo = JSON.parse(readFileSync(join(root, 'data/propuesta-102.json'), 'utf8'));
delete geo.original.rotulos;
// propuesta de balcón (no figura en el DWG): se embebe aparte para que el visor la rotule como tal
const propuesta = geo.balcon;
// muebles de terceros preparados con tools/preparar_muebles.py (créditos en modelo/muebles/CREDITOS.md)
const muebles = Object.fromEntries(readdirSync(join(root, 'modelo/muebles')).filter(f => f.endsWith('.glb'))
  .map(f => [f.replace(/\.glb$/, ''), readFileSync(join(root, 'modelo/muebles', f)).toString('base64')]));
// texturas PBR propias (tools/texturas_pbr.py) y exterior conceptual (HDRI CC0 y hojas/corteza para ez-tree)
const tdir = join(root, 'modelo/texturas'), edir = join(root, 'modelo/exterior');
const b64 = p => readFileSync(p).toString('base64');
const texturas = { escala: JSON.parse(readFileSync(join(tdir, 'escala.json'), 'utf8')),
  img: Object.fromEntries(readdirSync(tdir).filter(f => f.endsWith('.jpg')).map(f => [f.replace(/\.jpg$/, ''), b64(join(tdir, f))])) };
const exterior = { ...JSON.parse(readFileSync(join(edir, 'hdri.json'), 'utf8')), hdr: b64(join(edir, 'parque.hdr')),
  hojas: Object.fromEntries(readdirSync(edir).filter(f => /^hoja_.*\.png$/.test(f)).map(f => [f.slice(5, -4), b64(join(edir, f))])),
  corteza: { color: b64(join(edir, 'corteza_color.jpg')), normal: b64(join(edir, 'corteza_normal.jpg')), rough: b64(join(edir, 'corteza_rough.jpg')) } };
writeFileSync(join(root, 'dist/datos.js'),
  '/* Generado por tools/build.mjs: modelo GLB y propuesta de redistribución del apartamento 102 (rediseño conceptual). */\n' +
  `window.APTO102=${JSON.stringify({ glb, geo, propuesta, muebles, texturas, exterior })};\n`);

const esbuild = process.env.ESBUILD || 'esbuild';
execFileSync(esbuild, [join(root, 'src/app.mjs'), '--bundle', '--format=iife', '--target=es2020', '--minify',
  '--legal-comments=eof', `--outfile=${join(root, 'dist/app.js')}`],
  { stdio: 'inherit', env: { ...process.env } });
console.log('dist/app.js y dist/datos.js listos');
