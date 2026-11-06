const { test, before, after } = require('node:test');
const assert = require('node:assert/strict');
const { spawn } = require('node:child_process');
const { once } = require('node:events');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright');

const root = path.resolve(__dirname, '..');
const port = 18768;
const base = `http://127.0.0.1:${port}`;
let server, browser;
before(async () => {
  server = spawn(process.execPath, ['server.mjs'], { cwd: root, env: { ...process.env, PORT: String(port) }, stdio: ['ignore', 'pipe', 'pipe'] });
  await Promise.race([
    once(server.stdout, 'data'),
    once(server, 'exit').then(([code]) => { throw new Error(`Servidor terminó: ${code}`); }),
  ]);
  const executablePath = process.env.CHROMIUM_PATH || (fs.existsSync('/usr/bin/chromium') ? '/usr/bin/chromium' : undefined);
  browser = await chromium.launch({ executablePath, args: ['--no-sandbox'] });
});
after(async () => { await browser?.close(); server?.kill(); });

async function open(t, options = {}, query = '?scan=0') {
  const context = await browser.newContext({ reducedMotion: 'reduce', ...options });
  t.after(() => context.close());
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  t.after(() => assert.deepEqual(errors, [], 'sin errores JavaScript'));
  await page.route('https://fonts.googleapis.com/**', route => route.abort());
  await page.goto(base + '/' + query);
  await page.waitForFunction(() => !!window.ORA_API);
  return page;
}
async function plan(page, k = 5) {
  await page.evaluate(k => ORA_API.enter('day', 'T1', k), k);
  await page.waitForFunction(() => ORA_API.state.state === 'int' && !ORA_API.state.busy && ORA_API.state.mode === 'plan');
  await expandPanel(page);
}
async function expandPanel(page) {
  await page.locator('#panel').waitFor({ state: 'visible' });
  const toggle = page.locator('#panelToggle');
  if (await toggle.isVisible() && await toggle.getAttribute('aria-expanded') === 'false') await toggle.click();
}
async function exterior(page) {
  await page.waitForFunction(() => ORA_API.state.state === 'ext' && !ORA_API.state.busy && ORA_API.state.mode === null);
  assert.equal(await page.locator('#mediaLoading').isVisible(), false);
  assert.equal(await page.locator('#int').getAttribute('aria-busy'), 'false');
  assert.equal(await page.locator('#nav').evaluate(e => e.hidden || e.inert), false);
}
async function shortMediaTimeout(page) {
  await page.addInitScript(() => {
    const original = window.setTimeout;
    window.setTimeout = (fn, delay, ...args) => original(fn, delay === 15000 ? 250 : delay, ...args);
  });
}

test('recursos y Range de los tres videos', async () => {
  for (const file of ['index.html', 'css/style.css', 'js/config.js', 'js/app.js', 'js/vendor/gsap.min.js', 'img/day.webp', 'img/night.webp']) {
    const response = await fetch(`${base}/${file}`);
    assert.equal(response.status, 200);
    assert.deepEqual(Buffer.from(await response.arrayBuffer()), fs.readFileSync(path.join(root, file)));
  }
  for (const file of ['media/interior-residencia.mp4', 'media/interior-penthouse.mp4', 'video/ora-ai-reel.mp4']) {
    const response = await fetch(`${base}/${file}`, { headers: { Range: 'bytes=1024-2047' } });
    assert.equal(response.status, 206);
    assert.equal(response.headers.get('content-type'), 'video/mp4');
    assert.deepEqual(Buffer.from(await response.arrayBuffer()), fs.readFileSync(path.join(root, file)).subarray(1024, 2048));
  }
});

test('ambos recorridos completos, día/noche y sin precarga de videos ajenos', async t => {
  const page = await open(t);
  const requested = [];
  page.on('request', r => { if (r.url().endsWith('.mp4')) requested.push(r.url()); });
  await page.waitForTimeout(1400);
  assert.equal(await page.locator('polygon.fl').count(), 94);
  assert.equal(requested.length, 0, 'no descarga videos al cargar la fachada');
  await page.locator('button[data-tod="night"]').click();
  assert.equal(await page.evaluate(() => ORA_API.state.tod), 'night');
  await page.locator('button[data-tod="day"]').click();
  for (const [k, name] of [[5, 'Residencia A'], [15, 'Penthouse']]) {
    await plan(page, k);
    assert.equal(await page.locator('#pT').textContent(), name);
    assert(await page.locator('#vid').evaluate(v => v.videoWidth > 0 && !v.error));
    if (k === 5) assert(requested.every(url => url.includes('interior-residencia')));
    for (let i = 0; i < 3; i++) {
      await page.locator(i === 0 ? '#pRooms button' : '#chips button').nth(i).click();
      await page.waitForFunction(i => ORA_API.state.mode === 'room' && document.querySelector('#chips button.on')?.dataset.i === String(i), i);
    }
    await page.locator('#back').click();
    await page.waitForFunction(() => ORA_API.state.mode === 'plan');
    await page.locator('#pBack').click();
    await exterior(page);
  }
});

test('menú móvil: modos, Escape, clic exterior y cambio de tamaño', async t => {
  const page = await open(t, { viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
  const toggle = page.locator('#menuToggle');
  for (const mode of ['pent', 'amen', 'res']) {
    await toggle.click();
    assert.equal(await toggle.getAttribute('aria-expanded'), 'true');
    await page.locator(`[data-mode="${mode}"]`).click();
    assert.equal(await toggle.getAttribute('aria-expanded'), 'false');
    assert(await page.locator(`[data-mode="${mode}"]`).evaluate(e => e.classList.contains('on')));
  }
  await toggle.click(); await page.keyboard.press('Escape');
  assert.equal(await toggle.getAttribute('aria-expanded'), 'false');
  await toggle.click(); await page.locator('button[data-tod="night"]').click();
  assert.equal(await toggle.getAttribute('aria-expanded'), 'false');
  await toggle.click(); await page.setViewportSize({ width: 1200, height: 800 });
  await page.waitForFunction(() => document.querySelector('#menuToggle').getAttribute('aria-expanded') === 'false');
  assert.equal(await toggle.getAttribute('aria-expanded'), 'false');
  assert(await page.locator('[data-mode="amen"]').isVisible());
});

test('scan=0 permanece desactivado tras cambiar de modo y volver del interior', async t => {
  const page = await open(t);
  await plan(page);
  await page.locator('#pBack').click(); await exterior(page);
  await page.clock.install();
  await page.locator('[data-mode="pent"]').click();
  await page.locator('button[data-tod="night"]').click();
  await page.clock.fastForward(16000);
  assert.equal(await page.locator('#tip').evaluate(e => e.classList.contains('show')), false);
});

test('recorrido de penthouses usa pisos existentes y amenidades detiene el recorrido', async t => {
  const page = await open(t, {}, '');
  await page.clock.install();
  await page.locator('[data-mode="pent"]').click();
  const seen = new Set();
  for (let i = 0; i < 4; i++) {
    await page.clock.runFor(i === 0 ? 600 : 1050);
    const floor = await page.locator('polygon.fl.on').evaluate(e => ({ key: `${e.dataset.plane}:${e.dataset.k}`, pent: e.dataset.pent }));
    assert.equal(floor.pent, '1'); seen.add(floor.key);
  }
  assert.equal(seen.size, 4);
  assert(seen.has('T1:14') && seen.has('T1:15'));
  await page.locator('[data-mode="amen"]').click();
  await page.clock.fastForward(16000);
  assert.equal(await page.locator('polygon.fl.on').count(), 0);
});

test('error de descarga permite reintentar y completar otro recorrido', async t => {
  const page = await open(t);
  await page.route('**/media/*.mp4', r => r.abort());
  await page.evaluate(() => ORA_API.enter('day', 'T1', 5));
  await exterior(page);
  assert(await page.locator('#mediaStatus').isVisible());
  await page.unroute('**/media/*.mp4');
  await plan(page, 15);
  assert.equal(await page.locator('#mediaStatus').isVisible(), false);
});

test('carga pendiente se puede cancelar sin callbacks tardíos', async t => {
  const page = await open(t);
  await page.route('**/media/*.mp4', () => {});
  await page.evaluate(() => ORA_API.enter('day', 'T1', 5));
  await page.locator('#back').click(); await exterior(page);
  assert.equal(await page.locator('#mediaStatus').isVisible(), false);
  await page.unroute('**/media/*.mp4');
  await plan(page, 15);
});

test('carga sin respuesta termina por timeout y recupera la fachada', async t => {
  const page = await open(t);
  await shortMediaTimeout(page); await page.reload();
  await page.route('**/media/*.mp4', () => {});
  await page.evaluate(() => ORA_API.enter('day', 'T1', 5));
  await page.locator('#mediaStatus').waitFor({ state: 'visible' }); await exterior(page);
});

test('búsqueda de video sin seeked recupera la navegación', async t => {
  const page = await open(t);
  await plan(page);
  await page.evaluate(() => {
    const timeout = window.setTimeout;
    window.setTimeout = (fn, ms, ...args) => timeout(fn, ms === 15000 ? 250 : ms, ...args);
    const video = document.querySelector('#vid');
    const current = video.currentTime;
    Object.defineProperty(video, 'currentTime', { configurable: true, get: () => current, set: () => {} });
  });
  await page.locator('#pRooms button').nth(1).click();
  await page.locator('#mediaStatus').waitFor({ state: 'visible' }); await exterior(page);
});

for (const [device, options] of [
  ['escritorio', {}],
  ['móvil con restricciones de autoplay', { viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true }],
]) {
  test(`autoplay rechazado permite plano y todas las habitaciones en ${device}`, async t => {
    const page = await open(t, options);
    await page.evaluate(() => {
      const video = document.querySelector('#vid');
      video.play = () => Promise.reject(new DOMException('Autoplay bloqueado', 'NotAllowedError'));
    });
    for (const [k, unit] of [[5, 'res'], [15, 'pent']]) {
      await plan(page, k);
      assert.equal(await page.locator('#mediaStatus').isVisible(), false);
      assert.equal(await page.locator('#mediaLoading').isVisible(), false);
      assert(await page.locator('#vid').evaluate((v, unit) =>
        v.paused && v.videoWidth > 0 && v.readyState >= 2 && Math.abs(v.currentTime - ORA.units[unit].plan.hold) < .1, unit));
      for (let i = 0; i < 3; i++) {
        await page.locator(i === 0 ? '#pRooms button' : '#chips button').nth(i).click();
        await page.waitForFunction(({ i, unit }) =>
          ORA_API.state.mode === 'room' &&
          document.querySelector('#chips button.on')?.dataset.i === String(i) &&
          document.querySelector('#vid').paused &&
          Math.abs(ORA_API.state.t - ORA.units[unit].rooms[i].hold) < .1, { i, unit });
      }
      await page.locator('#back').click();
      await page.waitForFunction(() => ORA_API.state.mode === 'plan');
      await page.locator('#pBack').click(); await exterior(page);
    }
  });
}

test('fallo real de reproducción conserva la recuperación a la fachada', async t => {
  const page = await open(t);
  await page.evaluate(() => { document.querySelector('#vid').play = () => Promise.reject(new DOMException('Formato no compatible', 'NotSupportedError')); });
  await page.evaluate(() => ORA_API.enter('day', 'T1', 5));
  await page.locator('#mediaStatus').waitFor({ state: 'visible' }); await exterior(page);
});

for (const width of [390, 1440]) {
  test(`menú oculto e indicador de carga durante la entrada a ${width}px`, async t => {
    const page = await open(t, { viewport: { width, height: 844 }, isMobile: width < 900, hasTouch: width < 900 });
    let release;
    const gate = new Promise(resolve => { release = resolve; });
    t.after(() => release());
    await page.route('**/media/*.mp4', async route => { await gate; await route.continue(); });
    if (width < 900) await page.locator('#menuToggle').click();
    await page.evaluate(() => ORA_API.enter('day', 'T1', 5));
    await page.locator('#mediaLoading').waitFor({ state: 'visible' });
    assert.equal(await page.locator('#int').getAttribute('aria-busy'), 'true');
    assert.equal(await page.locator('#nav').isVisible(), false);
    assert.equal(await page.locator('#menuToggle').isVisible(), false);
    assert.equal(await page.locator('#menuToggle').getAttribute('aria-expanded'), 'false');
    assert(await page.locator('#nav').evaluate(e => e.inert));
    assert(await page.locator('#back').isVisible(), 'se puede cancelar durante la carga');
    release();
    await page.waitForFunction(() => ORA_API.state.mode === 'plan' && ORA_API.state.state === 'int');
    assert.equal(await page.locator('#mediaLoading').isVisible(), false);
    assert.equal(await page.locator('#int').getAttribute('aria-busy'), 'false');
    assert.equal(await page.locator('#nav').isVisible(), false);
    await expandPanel(page);
    await page.locator('#pRooms button').nth(1).click();
    await page.waitForFunction(() => ORA_API.state.mode === 'room');
    assert.equal(await page.locator('#nav').isVisible(), false);
    assert.equal(await page.locator('#menuToggle').isVisible(), false);
    await page.locator('#back').click();
    await page.waitForFunction(() => ORA_API.state.mode === 'plan');
    await page.locator('#pBack').click(); await exterior(page);
    if (width < 900) {
      assert(await page.locator('#menuToggle').isVisible());
      await page.locator('#menuToggle').click();
      await page.locator('[data-mode="amen"]').click();
      assert(await page.locator('body').evaluate(e => e.classList.contains('mode-amen')));
    } else assert(await page.locator('[data-mode="amen"]').isVisible());
  });
}

test('animaciones normales y recorrido en pantalla móvil', async t => {
  const page = await open(t, { reducedMotion: 'no-preference', viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
  await plan(page);
  assert(await page.evaluate(() => ORA_API.timeline().duration() > 2));
  await page.locator('#pRooms button').first().click();
  await page.waitForFunction(() => ORA_API.state.mode === 'room');
  assert(await page.locator('#vid').evaluate(v => v.videoWidth > 0));
  await page.locator('#back').click();
  await page.waitForFunction(() => ORA_API.state.mode === 'plan');
  await page.locator('#pBack').click(); await exterior(page);
  assert.equal(await page.locator('#fx').evaluate(e => getComputedStyle(e).visibility), 'hidden');
});


test('volver cancela una búsqueda pendiente sin esperar al timeout', async t => {
  const page = await open(t);
  await plan(page);
  await page.evaluate(() => {
    const video = document.querySelector('#vid');
    const current = video.currentTime;
    Object.defineProperty(video, 'currentTime', { configurable: true, get: () => current, set: () => {} });
  });
  await page.locator('#pRooms button').nth(1).click();
  await page.locator('#back').click();
  await page.waitForFunction(() => ORA_API.state.state === 'ext' && !ORA_API.state.busy, null, { timeout: 2000 });
  assert.equal(await page.locator('#mediaStatus').isVisible(), false);
});
