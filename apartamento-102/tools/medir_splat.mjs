// Mide el piloto de Gaussian Splatting frente a la V5 en la misma corrida (Chromium con GPU Metal, como el resto de
// mediciones del proyecto): carga del splat, memoria y fps caminando y girando en la sala, en modo splat y en modo malla.
//   node apartamento-102/tools/medir_splat.mjs <url_splat> [1440x900] [dpr=2] > medicion.json
// Variables: CALIDADES=media,alta  CALENTAR=6000 (ms girando antes de medir, para la resolución dinámica de la V5).
import { chromium } from 'playwright';

const [splat = 'modelo/web/splat/splat_sala_cocina.ply', vp = '1440x900', dprArg = '2'] = process.argv.slice(2);
const [w, h] = vp.split('x').map(Number), dpr = Number(dprArg);
const base = process.env.ORA_URL || 'http://127.0.0.1:8768';
const calidades = (process.env.CALIDADES || 'media,alta').split(',');
const CALENTAR = +(process.env.CALENTAR || 6000);
const browser = await chromium.launch({ args: ['--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist', '--enable-gpu-rasterization'] });
const out = { splat, viewport: `${w}x${h}@${dpr}`, fecha: new Date().toISOString(), casos: [] };

async function medir(page) {
  return page.evaluate(async CALENTAR => {
    const espera = ms => new Promise(r => setTimeout(r, ms));
    APTO_API.setMode('walk'); APTO_API.goRoom('social');
    for (let i = 0; i < 100 && APTO_API.state.flying; i++) await espera(100);
    document.body.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight', bubbles: true }));
    { const fin = performance.now() + CALENTAR; await new Promise(res => { const f = () => { APTO_API.render(4); performance.now() < fin ? requestAnimationFrame(f) : res(); }; requestAnimationFrame(f); }); }
    let n = 0, t0 = 0, peor = 0, ult = 0; const dts = [];
    await new Promise(res => { const f = t => { if (!t0) { t0 = t; ult = t; } else { dts.push(t - ult); peor = Math.max(peor, t - ult); ult = t; n++; } if (t - t0 < 5000) { APTO_API.render(4); requestAnimationFrame(f); } else res(); }; requestAnimationFrame(f); });
    document.body.dispatchEvent(new KeyboardEvent('keyup', { key: 'ArrowRight', bubbles: true }));
    dts.sort((a, b) => a - b);
    return { fps: +(n / ((ult - t0) / 1000)).toFixed(1), p95_ms: +dts[Math.floor(dts.length * 0.95)].toFixed(1), peor_ms: +peor.toFixed(1), densidad: APTO_API.densidad,
      heap_mb: performance.memory ? Math.round(performance.memory.usedJSHeapSize / 1e6) : null };
  }, CALENTAR);
}

try {
  for (const q of calidades) {
    for (const pagina of ['recorrido-v5.html', 'recorrido-splat.html']) {
      const ctx = await browser.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: dpr });
      const page = await ctx.newPage(); const errores = [];
      page.on('pageerror', e => errores.push(e.message));
      await page.route(/fonts\.(googleapis|gstatic)\.com/, r => r.abort());
      const t0 = Date.now();
      await page.goto(`${base}/apartamento-102/${pagina}?calidad=${q}&sincaptura${pagina.includes('splat') ? `&splat=${splat}` : ''}`);
      await page.waitForFunction(() => window.APTO_API?.ready, null, { timeout: 180000 });
      const caso = { pagina, calidad: q, t_listo_ms: Date.now() - t0 };
      if (pagina.includes('splat')) {
        await page.waitForFunction(() => window.SPLAT_API && (SPLAT_API.estado.cargado || SPLAT_API.estado.error), null, { timeout: 300000 });
        caso.t_splat_ms = Date.now() - t0; caso.splat = await page.evaluate(() => SPLAT_API.estado);
        caso.modo_splat = await medir(page);
        await page.evaluate(() => SPLAT_API.activar(false)); caso.modo_malla = await medir(page);
      } else caso.v5 = await medir(page);
      caso.errores = errores; out.casos.push(caso); console.error(JSON.stringify(caso));
      await ctx.close();
    }
  }
} finally { await browser.close(); }
console.log(JSON.stringify(out, null, 1));
