// Comprime un splat .ply a .spz (formato de Niantic, que Spark lee) con el propio Spark 2.4.0 (transcodeSpz), en un
// Chromium sin ventana: no hace falta otra herramienta. Recorta las gaussianas fuera de la caja del apartamento
// (suelen ser «flotantes» del fondo) y puede bajar el grado de armónicos esféricos (reflejos dependientes de la vista).
//   node tools/splat/a_spz.mjs <entrada.ply> <salida.spz> [grado_sh=3]
// El archivo de entrada se lee directamente del disco y la salida se escribe al disco (sin servidor).
import { chromium } from 'playwright';
import { execFileSync } from 'node:child_process';
import { readFileSync, writeFileSync, mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const [entrada, salida, sh = '3'] = process.argv.slice(2);
const repo = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const tmp = mkdtempSync(join(tmpdir(), 'ora-spz-'));
writeFileSync(join(tmp, 'e.mjs'), "import { transcodeSpz } from '@sparkjsdev/spark'; window.transcodeSpz = transcodeSpz;");
execFileSync(join(repo, 'node_modules/.bin/esbuild'), [join(tmp, 'e.mjs'), '--bundle', '--format=iife', `--outfile=${join(tmp, 'spz.js')}`,
  `--alias:@sparkjsdev/spark=${join(repo, 'tools/splat/node_modules/@sparkjsdev/spark/dist/spark.module.js')}`], { cwd: repo, stdio: 'ignore' });
// caja del apartamento en ejes de Blender (m), con margen: lo de fuera se descarta
const cfg = JSON.parse(readFileSync(join(repo, 'blender/scripts/apto-102.json'), 'utf8'));
const [ox, oy] = cfg.origen_plano, M = 1.5;
const caja = { min: [0 - ox - M, -1.8 - oy - M, -0.3], max: [8.0 - ox + M, 7.6 - oy + M, 3.2] };
const bytes = readFileSync(entrada);
const browser = await chromium.launch({ args: ['--use-angle=metal', '--enable-gpu'] });
try {
  const page = await browser.newPage();
  await page.setContent('<html><body></body></html>');
  await page.addScriptTag({ content: readFileSync(join(tmp, 'spz.js'), 'utf8') });
  // los bytes se pasan en trozos base64 para no exceder los límites del canal de Playwright
  await page.evaluate(() => { window._p = []; });
  for (let i = 0; i < bytes.length; i += 32e6) await page.evaluate(s => window._p.push(s), bytes.subarray(i, i + 32e6).toString('base64'));
  const n = await page.evaluate(async ([sh, caja, nombre]) => {
    const partes = window._p.map(s => Uint8Array.from(atob(s), c => c.charCodeAt(0)));
    const total = partes.reduce((a, p) => a + p.length, 0), u = new Uint8Array(total); let o = 0; for (const p of partes) { u.set(p, o); o += p.length; }
    window._p = null;
    const r = await window.transcodeSpz({ inputs: [{ fileBytes: u, pathOrUrl: nombre }], maxSh: sh, clipXyz: caja });
    window._r = r.fileBytes; return { bytes: r.fileBytes.length, recortadas: r.clippedCount };
  }, [Number(sh), caja, entrada.split('/').pop()]);
  const trozos = [];
  for (let i = 0; i < n.bytes; i += 24e6) trozos.push(Buffer.from(await page.evaluate(([a, b]) => { let s = ''; const v = window._r.subarray(a, b); for (let k = 0; k < v.length; k += 65536) s += String.fromCharCode.apply(null, v.subarray(k, k + 65536)); return btoa(s); }, [i, Math.min(n.bytes, i + 24e6)]), 'base64'));
  writeFileSync(salida, Buffer.concat(trozos));
  console.log(JSON.stringify({ entrada, salida, mb_entrada: +(bytes.length / 1e6).toFixed(1), mb_salida: +(n.bytes / 1e6).toFixed(1), grado_sh: Number(sh), recortadas_fuera_de_caja: n.recortadas }));
} finally { await browser.close(); }
