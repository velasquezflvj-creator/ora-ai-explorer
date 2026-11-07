// Diagnóstico del costo de render por componente (sombras, GTAO, densidad de píxeles, árboles, espejos).
// Mide fps caminando en la sala con cada componente desactivado por separado, sin recompilar el visor.
//   node apartamento-102/tools/diagnostico_rendimiento.mjs /apartamento-102/recorrido.html alta 1440x900 2
import { chromium } from 'playwright';

const [ruta = '/apartamento-102/recorrido.html', calidad = 'alta', vp = '1440x900', dprS = '2'] = process.argv.slice(2);
const [w, h] = vp.split('x').map(Number);
const base = process.env.ORA_URL || 'http://127.0.0.1:8768';
const browser = await chromium.launch({ args: ['--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist'] });
const page = await (await browser.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: Number(dprS) })).newPage();
await page.route(/fonts\.(googleapis|gstatic)\.com/, r => r.abort());
await page.goto(`${base}${ruta}${ruta.includes('?') ? '&' : '?'}calidad=${calidad}`);
await page.waitForFunction(() => window.APTO_API?.ready, null, { timeout: 120000 });
await page.waitForFunction(() => APTO_API.entorno().listo, null, { timeout: 120000 }).catch(() => {});
await page.evaluate(() => { APTO_API.setMode('walk'); APTO_API.goRoom('social'); });
await page.waitForFunction(() => !APTO_API.state.flying);
const medir = nombre => page.evaluate(async nombre => {
  await new Promise(r => setTimeout(r, 600));
  document.body.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight', bubbles: true }));
  let n = 0, t0 = 0, ult = 0;
  await new Promise(res => { const f = t => { if (!t0) t0 = ult = t; else { n++; ult = t; } if (t - t0 < 4000) { APTO_API.render(4); requestAnimationFrame(f); } else res(); }; requestAnimationFrame(f); });
  document.body.dispatchEvent(new KeyboardEvent('keyup', { key: 'ArrowRight', bubbles: true }));
  return { caso: nombre, fps: +(n / ((ult - t0) / 1000)).toFixed(1) };
}, nombre);
const r = [];
r.push(await medir('completo'));
// 1) sombras: el visor marca needsUpdate en cada cuadro
await page.evaluate(() => { const sm = __ORA.renderer.shadowMap; Object.defineProperty(sm, 'needsUpdate', { get: () => false, set: () => {}, configurable: true }); });
r.push(await medir('sin_actualizar_sombras'));
await page.evaluate(() => { delete __ORA.renderer.shadowMap.needsUpdate; __ORA.renderer.shadowMap.needsUpdate = true; });
// 2) GTAO
await page.evaluate(() => { const c = __ORA.composer; if (c) c.passes.forEach(p => { if (p.constructor.name.includes('GTAO')) p.enabled = false; }); });
r.push(await medir('sin_gtao'));
await page.evaluate(() => { const c = __ORA.composer; if (c) c.passes.forEach(p => { p.enabled = true; }); });
// 3) densidad de píxeles 1,5×
await page.evaluate(() => { const R = __ORA.renderer; R.userData_pr = R.getPixelRatio(); R.setPixelRatio(1.5); __ORA.composer?.setPixelRatio(1.5); __ORA.composer?.setSize(innerWidth, innerHeight); });
r.push(await medir('densidad_1.5x'));
await page.evaluate(() => { const R = __ORA.renderer; R.setPixelRatio(R.userData_pr); __ORA.composer?.setPixelRatio(R.userData_pr); __ORA.composer?.setSize(innerWidth, innerHeight); });
// 4) árboles y exterior 3D (sombras y geometría)
const tris = await page.evaluate(() => { let t = 0, n = 0; __ORA.scene.traverse(o => { if (o.isMesh && o.castShadow && o.geometry?.index && o.geometry.index.count > 30000) { t += o.geometry.index.count / 3; n++; o.userData._cs = true; o.castShadow = false; } }); return { mallas: n, triangulos: Math.round(t) }; });
r.push({ ...(await medir('arboles_sin_sombra')), ...tris });
// 5) todo lo anterior junto
await page.evaluate(() => { const sm = __ORA.renderer.shadowMap; Object.defineProperty(sm, 'needsUpdate', { get: () => false, set: () => {}, configurable: true }); const R = __ORA.renderer; R.setPixelRatio(1.5); __ORA.composer?.setPixelRatio(1.5); __ORA.composer?.setSize(innerWidth, innerHeight); });
r.push(await medir('sombra_estatica+1.5x+arboles'));
console.log(JSON.stringify({ ruta, calidad, viewport: `${vp}@${dprS}`, resultados: r }, null, 1));
await browser.close();
