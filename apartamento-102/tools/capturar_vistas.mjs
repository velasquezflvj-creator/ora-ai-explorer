// Captura vistas del visor (V1 o V2) en Chromium con GPU real, para comparar con los renders de Blender.
// Uso (servidor en marcha: `node server.mjs`):
//   node apartamento-102/tools/capturar_vistas.mjs <ruta> <carpeta_salida> [calidad] [espacios]
//   node apartamento-102/tools/capturar_vistas.mjs /apartamento-102/recorrido.html capturas/v2 media social,principal
// Cada captura es la vista a pie del espacio (la misma posición de cámara en V1 y V2: VIEWS del visor).
// «social» coincide con la cámara CAM_Sala_hacia_cocina del render V3 de Blender (plano 2,1 / 0,85 → 1,0 / 6,0).
import { chromium } from 'playwright';
import { mkdirSync } from 'node:fs';
import { join } from 'node:path';

const [ruta = '/apartamento-102/recorrido.html', out = 'capturas-v2', calidad = 'media', lista = 'social'] = process.argv.slice(2);
const base = process.env.ORA_URL || 'http://127.0.0.1:8768';
const [w, h] = (process.env.VIEWPORT || '1600x900').split('x').map(Number);
mkdirSync(out, { recursive: true });
const browser = await chromium.launch({ args: ['--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist'] });
const page = await (await browser.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: 1 })).newPage();
const errores = [];
page.on('pageerror', e => errores.push(e.message));
page.on('console', m => { if (m.type() === 'error') errores.push(m.text()); });
await page.goto(`${base}${ruta}${ruta.includes('?') ? '&' : '?'}calidad=${calidad}`);
await page.waitForFunction(() => window.APTO_API?.ready, null, { timeout: 120000 });
await page.waitForFunction(() => APTO_API.entorno().listo, null, { timeout: 120000 }).catch(() => {});
await page.addStyleTag({ content: '.panel,.card,.bar,.modes,.hint,.walkpad,.caption,#hotspots,#pois,.propbanner,.btn-entrada,.joystick,.envtag{visibility:hidden!important}' });
for (const room of lista.split(',')) {
  await page.evaluate(r => { APTO_API.setMode('walk'); APTO_API.goRoom(r); }, room);
  await page.waitForFunction(() => !APTO_API.state.flying, null, { timeout: 60000 });
  await page.waitForTimeout(1500);
  await page.evaluate(() => APTO_API.render(30));
  await page.waitForTimeout(1200);
  const f = join(out, `${room}.png`);
  await page.screenshot({ path: f });
  const info = await page.evaluate(() => ({ estado: APTO_API.state, sonda: APTO_API.sonda ?? null, render: APTO_API.stats.render }));
  console.log(JSON.stringify({ archivo: f, room, calidad: info.estado.quality, sonda: info.sonda, plano: info.estado.plan, render: info.render }));
}
if (errores.length) console.log(JSON.stringify({ errores }));
await browser.close();
