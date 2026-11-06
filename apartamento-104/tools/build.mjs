// Construye dist/app.js (script clásico IIFE, funciona también abriendo index.html con file://)
// y dist/datos.js (GLB en base64 + geometría), para que el visor no dependa de fetch.
//
// Requisitos: three 0.180.0 resoluble como paquete "three" (p. ej. `npm i --no-save three@0.180.0`
// en la raíz del repositorio) y esbuild (`npx esbuild` o variable ESBUILD con su ruta).
//   node apartamento-104/tools/build.mjs
import { execFileSync } from 'node:child_process';
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
mkdirSync(join(root, 'dist'), { recursive: true });

const glb = readFileSync(join(root, 'modelo/apto-104.glb')).toString('base64');
const geo = JSON.parse(readFileSync(join(root, 'data/geometria-104.json'), 'utf8'));
for (const k of ['muros_poligonos', 'rotulos', 'identificacion']) delete geo[k];   // el visor no los usa
// propuesta de balcón (no figura en el DWG): se embebe aparte para que el visor la rotule como tal
const propuesta = JSON.parse(readFileSync(join(root, 'data/propuesta-balcon.json'), 'utf8'));
writeFileSync(join(root, 'dist/datos.js'),
  '/* Generado por tools/build.mjs: modelo GLB y geometría verificada del apartamento 104. */\n' +
  `window.APTO104=${JSON.stringify({ glb, geo, propuesta })};\n`);

const esbuild = process.env.ESBUILD || 'esbuild';
execFileSync(esbuild, [join(root, 'src/app.mjs'), '--bundle', '--format=iife', '--target=es2020', '--minify',
  '--legal-comments=eof', `--outfile=${join(root, 'dist/app.js')}`],
  { stdio: 'inherit', env: { ...process.env } });
console.log('dist/app.js y dist/datos.js listos');
