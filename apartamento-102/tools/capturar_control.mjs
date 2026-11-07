// Captura un visor (V5 o la página del splat) desde las vistas de control del piloto de Gaussian Splatting: la misma
// pose y el mismo campo de visión (75° horizontal, 1280×720) con que Cycles renderiza la referencia en la nube.
// Uso (servidor en marcha: `node server.mjs`):
//   node apartamento-102/tools/capturar_control.mjs /apartamento-102/recorrido-v5.html <carpeta_salida> [alta|media]
// No modifica el visor: usa su API pública (APTO_API.arch fija el FOV con un lente equivalente; APTO_API.pose la mirada).
// Verifica la pose resultante contra blender/scripts/apto-102.json (posición y dirección) y la informa.
import { chromium } from 'playwright';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const [ruta = '/apartamento-102/recorrido-v5.html', out = 'capturas/control-v5', calidad = 'alta'] = process.argv.slice(2);
const base = process.env.ORA_URL || 'http://127.0.0.1:8768';
const cfg = JSON.parse(readFileSync(new URL('../../blender/scripts/apto-102.json', import.meta.url)));
const FOV_H = cfg.splat.fov_grados || 75, [W, H] = cfg.splat.px || [1280, 720];
const MM = 18 / Math.tan((FOV_H * Math.PI / 180) / 2);   // lente equivalente (sensor de 36 mm) para APTO_API.arch
mkdirSync(out, { recursive: true });
const browser = await chromium.launch({ args: ['--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist'] });
const page = await (await browser.newContext({ viewport: { width: W, height: H }, deviceScaleFactor: 1 })).newPage();
const errores = [];
page.on('pageerror', e => errores.push(e.message));
await page.goto(`${base}${ruta}${ruta.includes('?') ? '&' : '?'}calidad=${calidad}&sincaptura`);
await page.waitForFunction(() => window.APTO_API?.ready, null, { timeout: 180000 });
await page.waitForFunction(() => APTO_API.entorno().listo, null, { timeout: 120000 }).catch(() => {});
await page.addStyleTag({ content: '.panel,.card,.bar,.modes,.hint,.walkpad,.caption,#hotspots,#pois,.propbanner,.btn-entrada,.joystick,.envtag,#splatBar,#splatInfo{visibility:hidden!important}' });
await page.evaluate(() => APTO_API.setMode('walk'));
await page.waitForFunction(() => !APTO_API.state.flying, null, { timeout: 60000 });
const informe = [];
for (const v of cfg.splat.control.vistas) {
  const [x, y, h] = v.desde, [lx, ly, lh] = v.hacia;
  await page.evaluate(([x, y, h, lx, ly, lh, mm]) => { APTO_API.arch(x, y, lx, ly, mm, 0, h); APTO_API.pose(x, y, h, lx, ly, lh); }, [x, y, h, lx, ly, lh, MM]);
  await page.waitForTimeout(600);
  // con la cámara quieta la V5 acumula muestras (TAA): esperar a que termine
  await page.waitForFunction(() => !APTO_API.acumulando, null, { timeout: 8000 }).catch(() => {});
  await page.waitForTimeout(2500);
  const pose = await page.evaluate(() => { const c = __ORA.camera; const d = c.getWorldDirection(new c.position.constructor()); return { p: c.position.toArray(), d: d.toArray(), fov: c.fov, aspect: c.aspect }; });
  // esperado en coordenadas de three: (x − ox, h, oy − y) con el mismo origen que el visor
  const [ox, oy] = cfg.origen_plano, e = [x - ox, h, oy - y], le = [lx - ox, lh, oy - ly];
  const de = le.map((c, i) => c - e[i]), n = Math.hypot(...de), du = de.map(c => c / n);
  const errPos = Math.hypot(...pose.p.map((c, i) => c - e[i])), errAng = Math.acos(Math.min(1, pose.d.reduce((s, c, i) => s + c * du[i], 0))) * 180 / Math.PI;
  const fovH = 2 * Math.atan(Math.tan(pose.fov * Math.PI / 360) * pose.aspect) * 180 / Math.PI;
  const f = join(out, `${v.id}.png`);
  await page.screenshot({ path: f });
  informe.push({ id: v.id, archivo: f, error_posicion_mm: +(errPos * 1000).toFixed(2), error_direccion_grados: +errAng.toFixed(3), fov_horizontal: +fovH.toFixed(2) });
  console.log(JSON.stringify(informe.at(-1)));
}
writeFileSync(join(out, 'poses.json'), JSON.stringify({ ruta, calidad, viewport: [W, H], informe, errores }, null, 1));
if (errores.length) console.log(JSON.stringify({ errores }));
await browser.close();
