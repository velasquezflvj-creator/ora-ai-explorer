// Construye la página del piloto de Gaussian Splatting (recorrido-splat.html) sin tocar la V5:
//   dist/recorrido-splat-app.js = src/app-recorrido-v5.mjs + src/capa-splat.mjs (Spark 2.4.0) en un solo IIFE.
//   Reutiliza dist/recorrido-v5-datos.js (los mismos datos de la V5). El splat se carga aparte (?splat=<url>).
// Requisitos: los de la V5 + Spark aislado en tools/splat (`npm install --prefix tools/splat --legacy-peer-deps`).
//   node apartamento-102/tools/build_recorrido_splat.mjs
import { execFileSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const repo = join(root, '..');
const spark = join(repo, 'tools/splat/node_modules/@sparkjsdev/spark/dist/spark.module.js');
if (!existsSync(spark)) throw new Error('Falta Spark: npm install --prefix tools/splat --legacy-peer-deps');
if (!existsSync(join(root, 'dist/recorrido-v5-datos.js'))) throw new Error('Falta dist/recorrido-v5-datos.js: construya antes la V5');
const esbuild = process.env.ESBUILD || join(repo, 'node_modules/.bin/esbuild');
execFileSync(esbuild, [join(root, 'src/entrada-splat.mjs'), '--bundle', '--format=iife', '--target=es2020', '--minify',
  '--legal-comments=eof', `--alias:@sparkjsdev/spark=${spark}`, `--outfile=${join(root, 'dist/recorrido-splat-app.js')}`], { stdio: 'inherit', cwd: repo });
console.log('recorrido splat listo: dist/recorrido-splat-app.js (V5 + Spark 2.4.0)');
