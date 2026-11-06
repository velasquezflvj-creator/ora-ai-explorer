// Fidelidad visual con la versión original de Nicolás (commit 3703753) y proporciones
// de los tableros en móvil y tableta. Usa clics/toques reales y mide la geometría final.
const { test, before, after } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawn, execFileSync } = require('node:child_process');
const { once } = require('node:events');
const { chromium } = require('playwright');

const root = path.resolve(__dirname, '..');
const ORIGINAL = '3703753'; // demo original publicado por Nicolás
const base = 'http://127.0.0.1:18773';
const original = 'http://127.0.0.1:18774';
let browser, temp;
const servers = [];

async function serve(cwd, port) {
  const server = spawn(process.execPath, ['server.mjs'], { cwd, env: { ...process.env, PORT: String(port) }, stdio: ['ignore', 'pipe', 'pipe'] });
  servers.push(server);
  await Promise.race([once(server.stdout, 'data'), once(server, 'exit').then(([code]) => { throw new Error(`Servidor ${port} terminó: ${code}`); })]);
}
before(async () => {
  temp = fs.mkdtempSync(path.join(os.tmpdir(), 'ora-original-'));
  execFileSync('tar', ['-x', '-C', temp], { input: execFileSync('git', ['archive', ORIGINAL], { cwd: root, maxBuffer: 64 * 1024 * 1024 }) });
  await serve(root, 18773); await serve(temp, 18774);
  const executablePath = process.env.CHROMIUM_PATH || (fs.existsSync('/usr/bin/chromium') ? '/usr/bin/chromium' : undefined);
  browser = await chromium.launch({ executablePath, args: ['--no-sandbox'] });
});
after(async () => {
  await browser?.close();
  for (const server of servers) if (server.exitCode === null) { const exited = once(server, 'exit'); server.kill(); await exited; }
  if (temp) fs.rmSync(temp, { recursive: true, force: true });
});

async function open(t, width, height, url = base, query = '?scan=0') {
  const context = await browser.newContext({ viewport: { width, height }, deviceScaleFactor: 1, reducedMotion: 'no-preference', isMobile: width <= 600, hasTouch: width <= 900 });
  t.after(() => context.close());
  const page = await context.newPage();
  const errors = []; page.on('pageerror', e => errors.push(e.message)); t.after(() => assert.deepEqual(errors, []));
  await page.route('https://fonts.googleapis.com/**', r => r.abort());
  await page.goto(url + '/' + query);
  await page.waitForFunction(() => !!window.ORA_API);
  return page;
}
const rect = (page, sel) => page.locator(sel).evaluate(e => { const r = e.getBoundingClientRect(); return { x: r.x, y: r.y, w: r.width, h: r.height, r: r.right, b: r.bottom }; });
const overlap = (a, b) => Math.max(0, Math.min(a.r, b.r) - Math.max(a.x, b.x)) * Math.max(0, Math.min(a.b, b.b) - Math.max(a.y, b.y));
const FLOOR = 'polygon[data-tod="day"][data-plane="T2L"][data-k="5"]';

async function select(page, touch) {
  const floor = page.locator(FLOOR);
  if (touch) await floor.tap(); else await floor.hover();
  await page.waitForFunction(() => +getComputedStyle(document.querySelector('#tip')).opacity > .99);
}
async function enterPlan(page, touch) {
  await select(page, touch);
  if (touch) await page.locator('#tip').tap(); else await page.locator(FLOOR).click();
  await page.waitForFunction(() => ORA_API.state.state === 'int' && !ORA_API.state.busy && ORA_API.state.mode === 'plan' && +getComputedStyle(document.querySelector('#panel')).opacity > .99, null, { timeout: 20000 });
}

for (const [width, height] of [[1440, 900], [1280, 800], [1024, 768]]) {
  test(`escritorio ${width}x${height}: selector y ficha idénticos al original de Nicolás`, async t => {
    const measure = async url => {
      const page = await open(t, width, height, url);
      await select(page, false);
      const tip = await rect(page, '#tip');
      await enterPlan(page, false);
      const panel = await rect(page, '#panel');
      const style = await page.locator('#panel').evaluate(e => { const s = getComputedStyle(e); return [s.padding, s.backgroundColor, s.borderTopColor, getComputedStyle(document.querySelector('#pT')).font]; });
      return { tip, panel, style };
    };
    assert.deepEqual(await measure(base), await measure(original));
  });
}

for (const [width, height] of [[320, 568], [390, 844], [768, 1024], [844, 390], [900, 768]]) {
  test(`selector anclado al piso en ${width}x${height}`, async t => {
    const page = await open(t, width, height);
    await select(page, true);
    const tip = await rect(page, '#tip'), floor = await rect(page, FLOOR), bar = await rect(page, '.bar'), tod = await rect(page, '#tod');
    assert(tip.w <= 270, `tarjeta compacta (${tip.w}px)`);
    assert(tip.x >= 8 && tip.r <= width - 8, 'dentro de la pantalla');
    assert(tip.y >= bar.b - 12, 'no invade la barra superior');
    assert.equal(overlap(tip, tod), 0, 'no tapa el selector día/noche');
    assert.equal(overlap(tip, floor), 0, 'no tapa el piso elegido');
    const distance = tip.b <= floor.y ? floor.y - tip.b : tip.y - floor.b;
    assert(distance >= 0 && distance <= 64, `junto al piso (${distance}px)`);
    assert.equal(await page.locator('#dot').evaluate(e => getComputedStyle(e).opacity), '1', 'marca el piso con el punto de luz');
    // el trazo une el punto con el borde de la tarjeta
    const line = await page.locator('#tipLine').evaluate(e => parseFloat(e.style.width));
    assert(line > 0 && line < 160);
  });
}

for (const [width, height] of [[320, 568], [390, 844]]) {
  test(`barra superior de una sola línea en ${width}x${height}`, async t => {
    const page = await open(t, width, height);
    const bar = await rect(page, '.bar'), name = await rect(page, '.brand-name'), cta = await rect(page, '#cta'), menu = await rect(page, '#menuToggle');
    assert(bar.h <= 84, `altura de la barra (${bar.h}px)`);
    assert(name.h <= 20 && cta.h <= 31 && menu.h <= 31, 'marca, menú y Tour privado sin saltos de línea');
    assert(menu.r <= cta.x, 'menú y CTA no se superponen');
    assert.equal(await page.locator('#menuToggle').getAttribute('aria-label'), 'Menú');
  });
}

for (const [width, height] of [[320, 568], [390, 844], [768, 1024]]) {
  test(`interior vertical ${width}x${height}: arquitectura libre de la ficha y pestañas completas`, async t => {
    const page = await open(t, width, height);
    await enterPlan(page, true);
    const vid = await page.locator('#vid').evaluate(v => {
      const r = v.getBoundingClientRect(), k = Math.min(r.width / v.videoWidth, r.height / v.videoHeight);
      const w = v.videoWidth * k, h = v.videoHeight * k;
      return { x: r.x + (r.width - w) / 2, y: r.y + (r.height - h) / 2, w, h, r: r.x + (r.width + w) / 2, b: r.y + (r.height + h) / 2 };
    });
    const panel = await rect(page, '#panel');
    assert(vid.y >= 76, 'la imagen no queda bajo la barra');
    assert.equal(overlap(vid, panel), 0, 'la ficha no tapa el plano');
    assert(panel.h <= (width <= 600 ? 140 : 320), `ficha compacta (${panel.h}px)`);
    const toggle = page.locator('#panelToggle');
    if (await toggle.isVisible() && await toggle.getAttribute('aria-expanded') === 'false') await toggle.tap();
    const room = page.locator('#pRooms button').nth(2);
    await room.scrollIntoViewIfNeeded(); await room.tap();
    await page.waitForFunction(() => ORA_API.state.mode === 'room' && !ORA_API.state.busy);
    await page.waitForTimeout(700);
    const chips = await page.locator('#chips button').evaluateAll(list => list.map(b => { const r = b.getBoundingClientRect(); return { x: r.x, r: r.right, scroll: b.scrollWidth <= b.clientWidth + 1 }; }));
    for (const c of chips) assert(c.x >= 0 && c.r <= width && c.scroll, 'cada habitación visible completa');
    const cap = await rect(page, '#cap');
    const photoBottom = await page.locator('#vid').evaluate(v => { const r = v.getBoundingClientRect(), k = Math.min(r.width / v.videoWidth, r.height / v.videoHeight); return r.y + (r.height + v.videoHeight * k) / 2; });
    assert(cap.y >= photoBottom - 1, 'el título de la habitación no tapa la fotografía');
  });
}

test('el interior queda operativo antes de terminar la animación de las mitades', async t => {
  const page = await open(t, 1440, 900);
  await enterPlan(page, false);
  const progress = await page.evaluate(() => ORA_API.timeline().progress());
  assert(progress <= 1);
  // Un clic inmediato en una habitación funciona: no hay controles visibles que descarten clics.
  await page.locator('#pRooms button').nth(1).click();
  await page.waitForFunction(() => ORA_API.state.mode === 'room' && !ORA_API.state.busy);
  assert.equal(await page.locator('#capT').textContent(), 'Habitación principal');
});

test('volver durante el tramo final de la entrada regresa a la fachada', async t => {
  const page = await open(t, 1440, 900);
  await page.evaluate(() => ORA_API.enter('day', 'T2L', 5));
  await page.waitForFunction(() => ORA_API.state.state === 'int');
  await page.evaluate(() => ORA_API.exit());
  await page.waitForFunction(() => ORA_API.state.state === 'ext' && !ORA_API.state.busy && ORA_API.state.mode === null, null, { timeout: 10000 });
  assert.equal(await page.locator('#nav').evaluate(e => e.hidden || e.inert), false);
});

test('el recorrido automático en teléfono solo señala pisos visibles', async t => {
  const page = await open(t, 390, 844, base, '');
  const seen = [];
  for (let i = 0; i < 9; i++) {
    await page.waitForFunction(n => document.querySelectorAll('#hot .fl.on').length && window.__steps !== n, i, { timeout: 4000 }).catch(() => {});
    const r = await page.evaluate(() => { const f = document.querySelector('#hot .fl.on'); if (!f) return null; const b = f.getBoundingClientRect(); window.__steps = (window.__steps || 0) + 1; return { cx: b.x + b.width / 2, key: f.dataset.plane + f.dataset.k }; });
    if (r) seen.push(r);
    await page.waitForTimeout(1050);
  }
  assert(new Set(seen.map(s => s.key)).size >= 3, 'el recorrido avanza');
  for (const s of seen) assert(s.cx >= 0 && s.cx <= 390, `piso ${s.key} visible`);
});
