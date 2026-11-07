// Mide carga y fotogramas por segundo del visor del apartamento 102 en un Chromium con GPU real (Metal en Mac).
// Uso (con el servidor del proyecto en marcha: `node server.mjs`):
//   node apartamento-102/tools/medir_rendimiento.mjs [ruta] [ancho]x[alto] [dpr]
//   node apartamento-102/tools/medir_rendimiento.mjs /apartamento-102/recorrido.html 1440x900 2
// Imprime JSON: tiempo hasta «listo», y por calidad: fps al girar caminando, llamadas de dibujo, triángulos,
// geometrías y texturas en GPU. Los fps se miden con la página visible en primer plano (no en una pestaña oculta).
import { chromium } from 'playwright';

const ruta = process.argv[2] || '/apartamento-102/';
const [w, h] = (process.argv[3] || '1440x900').split('x').map(Number);
const dpr = Number(process.argv[4] || 2);
const base = process.env.ORA_URL || 'http://127.0.0.1:8768';
const calidades = (process.env.CALIDADES || 'baja,media,alta').split(',');

const browser = await chromium.launch({
  headless: process.env.HEADED ? false : true,
  args: ['--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist', '--enable-gpu-rasterization', '--disable-frame-rate-limit=false'],
});
const resultados = { ruta, viewport: `${w}x${h}@${dpr}`, calidades: [] };
try {
  for (const q of calidades) {
    const ctx = await browser.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: dpr });
    const page = await ctx.newPage();
    const errores = [];
    page.on('pageerror', e => errores.push(e.message));
    page.on('console', m => { if (m.type() === 'error') errores.push(m.text()); });
    // las fuentes de Google no influyen en el render y dependen de la red: se bloquean para que la medición sea estable
    await page.route(/fonts\.(googleapis|gstatic)\.com/, r => r.abort());
    const sep = ruta.includes('?') ? '&' : '?';
    const t0 = Date.now();
    await page.goto(`${base}${ruta}${sep}calidad=${q}`);
    await page.waitForFunction(() => window.APTO_API?.ready, null, { timeout: 120000 });
    const tListo = Date.now() - t0;
    const gpu = await page.evaluate(() => { const g = __ORA.renderer.getContext(); const d = g.getExtension('WEBGL_debug_renderer_info'); return d ? g.getParameter(d.UNMASKED_RENDERER_WEBGL) : 'n/a'; });
    const medir = async (modo, extra) => page.evaluate(async ([modo, extra, CALENTAR]) => {
      APTO_API.setMode(modo);
      if (extra?.room) APTO_API.goRoom(extra.room);
      const espera = ms => new Promise(r => setTimeout(r, ms));
      for (let i = 0; i < 100 && APTO_API.state.flying; i++) await espera(100);
      const tecla = modo === 'walk' ? 'ArrowRight' : null;
      if (tecla) document.body.dispatchEvent(new KeyboardEvent('keydown', { key: tecla, bubbles: true }));
      // calentamiento girando (renderizando): da tiempo a la resolución dinámica del V3 (p. ej. CALENTAR=6000)
      { const fin = performance.now() + +(CALENTAR || 800); await new Promise(res => { const f = () => { APTO_API.render(4); performance.now() < fin ? requestAnimationFrame(f) : res(); }; requestAnimationFrame(f); }); }
      let n = 0, t0 = 0, peor = 0, ult = 0;
      await new Promise(res => {
        const f = t => { if (!t0) { t0 = t; ult = t; } else { peor = Math.max(peor, t - ult); ult = t; n++; } if (t - t0 < 5000) { APTO_API.render(4); requestAnimationFrame(f); } else res(); };
        requestAnimationFrame(f);
      });
      if (tecla) document.body.dispatchEvent(new KeyboardEvent('keyup', { key: tecla, bubbles: true }));
      const s = APTO_API.stats;
      return { modo, room: extra?.room || null, fps: +(n / ((ult - t0) / 1000)).toFixed(1), peor_ms: +peor.toFixed(1), calidad_final: APTO_API.state.quality, densidad: APTO_API.densidad ?? null, ...s.render, texturas_cache: s.texturas };
    }, [modo, extra, +(process.env.CALENTAR || 800)]);
    const r = { calidad: q, gpu, t_listo_ms: tListo, mediciones: [] };
    r.mediciones.push(await medir('orbit'));
    r.mediciones.push(await medir('walk', { room: 'social' }));
    r.mediciones.push(await medir('walk', { room: 'principal' }));
    r.mediciones.push(await medir('tour'));
    r.heap_mb = await page.evaluate(() => performance.memory ? Math.round(performance.memory.usedJSHeapSize / 1e6) : null);
    r.errores = errores;
    resultados.calidades.push(r);
    await ctx.close();
  }
} finally {
  await browser.close();
}
console.log(JSON.stringify(resultados, null, 1));
