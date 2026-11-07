// Recorrido V4 del apartamento 102 (apartamento-102/recorrido-v4.html). PROPUESTA DE REDISTRIBUCIÓN, no planta verificada.
// Además de lo heredado de la V3: atlas de luz en todas las superficies fijas sobre un GLB derivado con la misma
// geometría que el original, losa visible, y caminata con aceleración y frenado.
// Comprueba lo que añade el V3 (luz horneada en piso y cielo raso, sol del render V3, focos, sombras estáticas, resolución
// dinámica, gradación) y que conserva lo del V2 (sondas, navegación, colisiones, móvil), sin tocar V1, V2 ni el modelo.
const { test, before, after } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { spawn, execFileSync } = require('node:child_process');
const { once } = require('node:events');
const { chromium } = require('playwright');

const root = path.resolve(__dirname, '..');
const dir = path.join(root, 'apartamento-102');
const base = 'http://127.0.0.1:18785/apartamento-102/recorrido-v4.html';
const g = JSON.parse(fs.readFileSync(path.join(dir, 'data/propuesta-102.json'), 'utf8'));
let browser, server;
const hayV2 = fs.existsSync(path.join(dir, 'dist/recorrido-v4-datos.js')) && fs.existsSync(path.join(dir, 'dist/recorrido-v4-app.js'));

before(async () => {
  server = spawn(process.execPath, ['server.mjs'], { cwd: root, env: { ...process.env, PORT: '18785' }, stdio: ['ignore', 'pipe', 'pipe'] });
  await once(server.stdout, 'data');
  const executablePath = process.env.CHROMIUM_PATH || (fs.existsSync('/usr/bin/chromium') ? '/usr/bin/chromium' : undefined);
  browser = await chromium.launch({ executablePath, args: ['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
});
after(async () => { await browser?.close(); if (server?.exitCode === null) { const e = once(server, 'exit'); server.kill(); await e; } });

async function open(t, { width = 960, height = 600, q = '?calidad=media', touch = false } = {}) {
  const context = await browser.newContext({ viewport: { width, height }, deviceScaleFactor: 1, isMobile: touch, hasTouch: touch });
  t.after(() => context.close());
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  page.on('console', m => { if (m.type() === 'error' && !/Failed to load resource/.test(m.text())) errors.push(m.text()); });
  t.after(() => assert.deepEqual(errors, [], 'sin errores de JavaScript'));
  await page.route(/fonts\.(googleapis|gstatic)\.com/, r => r.abort());
  await page.goto(base + q);
  await page.waitForFunction(() => window.APTO_API?.ready, null, { timeout: 120000 });
  return page;
}
const settle = page => page.waitForFunction(() => !APTO_API.state.flying, null, { timeout: 60000 });

test('la V4 no modifica V1, V2, V3 ni el modelo original', () => {
  // el visor original sigue cargando sus propios archivos
  const v1 = fs.readFileSync(path.join(dir, 'index.html'), 'utf8');
  assert.match(v1, /dist\/datos\.js/); assert.match(v1, /dist\/app\.js/);
  assert.doesNotMatch(v1, /recorrido-(app|datos)/);
  // con Git: los archivos del V1, el modelo y los datos de planta son idénticos al commit base
  if (fs.existsSync(path.join(root, '.git'))) {
    // referencia del V1: 478d2da = cierre de feat/apartamento-102-rediseno en GitHub (estado descargado);
    // si no existe en este repositorio (copia local sin ese historial), el primer commit
    let base; try { base = execFileSync('git', ['rev-parse', '--verify', '-q', '478d2da^{commit}'], { cwd: root }).toString().trim(); }
    catch { base = execFileSync('git', ['rev-list', '--max-parents=0', 'HEAD'], { cwd: root }).toString().trim().split('\n').pop(); }
    // V3: idéntica al cierre de su rama, si existe en este repositorio
    let v3 = null; try { v3 = execFileSync('git', ['rev-parse', '--verify', '-q', 'feat/apto-102-recorrido-v3'], { cwd: root }).toString().trim(); } catch {}
    if (v3) {
      const d3 = execFileSync('git', ['diff', '--name-only', v3, '--', 'apartamento-102/recorrido-v3.html', 'apartamento-102/src/app-recorrido-v3.mjs', 'apartamento-102/css/recorrido-v3.css', 'apartamento-102/tools/build_recorrido_v3.mjs'], { cwd: root }).toString().trim();
      assert.equal(d3, '', 'V3 sin cambios respecto al cierre de su rama');
    }
    // V2: idéntico al cierre de su rama (feat/apto-102-recorrido-interactivo), si existe en este repositorio
    let v2 = null; try { v2 = execFileSync('git', ['rev-parse', '--verify', '-q', 'feat/apto-102-recorrido-interactivo'], { cwd: root }).toString().trim(); } catch {}
    if (v2) {
      const d2 = execFileSync('git', ['diff', '--name-only', v2, '--', 'apartamento-102/recorrido.html', 'apartamento-102/src/app-recorrido.mjs', 'apartamento-102/css/recorrido.css', 'apartamento-102/tools/build_recorrido.mjs'], { cwd: root }).toString().trim();
      assert.equal(d2, '', 'V2 sin cambios respecto al cierre de su rama');
    }
    const protegidos = ['apartamento-102/index.html', 'apartamento-102/src/app.mjs', 'apartamento-102/src/pbr102.mjs', 'apartamento-102/dist/app.js',
      'apartamento-102/dist/datos.js', 'apartamento-102/modelo/apto-102-propuesta.glb', 'apartamento-102/data/propuesta-102.json', 'apartamento-102/data/original-102-dwg.json'];
    const diff = execFileSync('git', ['diff', '--name-only', base, '--', ...protegidos], { cwd: root }).toString().trim();
    assert.equal(diff, '', 'V1 y modelo sin cambios respecto al commit base');
  }
  // el V2 usa el mismo GLB y los mismos datos de planta
  const build = fs.readFileSync(path.join(dir, 'tools/build_recorrido_v4.mjs'), 'utf8');
  assert.match(build, /apto-102-propuesta\.glb/); assert.match(build, /data\/propuesta-102\.json/);
  const glb = fs.readFileSync(path.join(dir, 'modelo/apto-102-propuesta.glb'));
  assert.equal(crypto.createHash('sha1').update(glb).digest('hex').length, 40);
});

test('carga con sondas de luz, texturas fotográficas y rótulos de propuesta', { skip: !hayV2 && 'falta construir el V2' }, async t => {
  const page = await open(t);
  const s = await page.evaluate(() => ({ sondas: APTO_API.sondas(), piso: APTO_API.matInfo('piso_madera'), banner: document.querySelector('#propBanner').textContent,
    tag: document.querySelector('.brand-tag').textContent, calidad: [...document.querySelectorAll('#calidad button')].map(b => b.textContent) }));
  assert.equal(s.sondas.length, 10, 'una sonda por espacio (dos en la zona social)');
  assert.ok(s.piso.map && s.piso.normal, 'el piso usa el horneado de Blender con relieve');
  assert.match(s.banner, /Propuesta de redistribución/); assert.match(s.banner, /no planta verificada/);
  assert.match(s.tag, /Recorrido V4/);
  assert.deepEqual(s.calidad, ['Móvil', 'Media', 'Alta']);
});

test('caminar empieza en la entrada; «Entrada» vuelve al inicio; la sonda sigue al visitante', { skip: !hayV2 && 'falta construir el V2' }, async t => {
  const page = await open(t);
  await page.evaluate(() => APTO_API.setMode('walk')); await settle(page);
  let st = await page.evaluate(() => APTO_API.state);
  assert.ok(Math.hypot(st.plan.x - 0.95, st.plan.y - 6.95) < 0.3, `inicio junto al acceso (${st.plan.x}, ${st.plan.y})`);
  assert.ok(await page.evaluate(() => APTO_API.free(APTO_API.state.plan.x, APTO_API.state.plan.y)), 'el inicio es un punto libre');
  assert.equal(await page.isVisible('#btnEntrada'), true);
  await page.evaluate(() => APTO_API.goRoom('principal')); await settle(page);
  await page.waitForFunction(() => APTO_API.sonda === 'principal', null, { timeout: 20000 });
  await page.click('#btnEntrada'); await settle(page);
  st = await page.evaluate(() => APTO_API.state);
  assert.ok(Math.hypot(st.plan.x - 0.95, st.plan.y - 6.95) < 0.3, 'el botón devuelve a la entrada');
  await page.waitForFunction(() => APTO_API.sonda === 'cocina' || APTO_API.sonda === 'sala', null, { timeout: 20000 });
});

test('colisiones: no atraviesa muros ni sale por el acceso', { skip: !hayV2 && 'falta construir el V2' }, async t => {
  const page = await open(t);
  await page.evaluate(() => APTO_API.setMode('walk')); await settle(page);
  // muro norte de la envolvente (DWG) y puerta de acceso cerrada al corredor
  const r = await page.evaluate(() => { const a = { ...APTO_API.state.plan }; APTO_API.move(0, 3); const b = APTO_API.state.plan; return { a, b }; });
  assert.ok(r.b.y < 7.45, `se detiene antes del acceso (y = ${r.b.y})`);
  for (const [x0, y0, x1, y1] of g.muros_rectangulos) {
    const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;
    assert.equal(await page.evaluate(([x, y]) => APTO_API.free(x, y), [cx, cy]), false, `muro en (${cx.toFixed(2)}, ${cy.toFixed(2)})`);
  }
});

test('teléfono: perfil Móvil automático y joystick táctil', { skip: !hayV2 && 'falta construir el V2' }, async t => {
  const page = await open(t, { width: 390, height: 844, q: '', touch: true });
  assert.equal(await page.evaluate(() => APTO_API.state.quality), 'baja', 'sin ?calidad= un teléfono usa el perfil Móvil');
  await page.evaluate(() => APTO_API.setMode('walk')); await settle(page);
  assert.equal(await page.isVisible('#joystick'), true);
  const a = await page.evaluate(() => APTO_API.state.plan);
  await page.evaluate(() => APTO_API.joystick(0, -1));
  // con render por software (swiftshader) hay pocos cuadros por segundo: se espera a que avance, no un tiempo fijo
  await page.waitForFunction(a => { const b = APTO_API.state.plan; return Math.hypot(b.x - a.x, b.y - a.y) > 0.3; }, a, { timeout: 30000 });
  await page.evaluate(() => APTO_API.joystick(0, 0));
});

test('luz horneada de día en piso y cielo raso; se apaga al atardecer y en la vista técnica', { skip: !hayV2 && 'falta construir el V3' }, async t => {
  const page = await open(t);
  const leer = () => page.evaluate(() => {
    const r = { piso: null, cielo: null, uv1: 0 };
    __ORA.scene.traverse(o => { if (!o.isMesh) return;
      if (o.material?.name === 'piso_madera') { r.piso = !!o.material.lightMap && o.material.defines?.HORNEADO !== undefined; if (o.geometry.attributes.uv1) r.uv1++; }
      if (o.material?.name === 'cielo') r.cielo = !!o.material.emissiveMap && o.material.defines?.HORNEADO_CIELO !== undefined; });
    return { ...r, activo: APTO_API.horneado };
  });
  let h = await leer();
  assert.equal(h.activo, true); assert.equal(h.piso, true, 'piso con irradiancia horneada'); assert.equal(h.cielo, true, 'cielo raso horneado'); assert.ok(h.uv1 >= 5, 'UV de planta en los pisos');
  await page.evaluate(() => APTO_API.setHora('atardecer'));
  h = await leer(); assert.equal(h.activo, false); assert.equal(h.piso, false); assert.equal(h.cielo, false);
  await page.evaluate(() => APTO_API.setHora('dia'));
  h = await leer(); assert.equal(h.activo, true); assert.equal(h.piso, true);
  // vista técnica (solo envolvente del DWG): cambia materiales y vuelve sin errores
  await page.evaluate(() => { const c = document.querySelector('#layerVerified'); c.checked = true; c.dispatchEvent(new Event('change', { bubbles: true })); });
  await page.evaluate(() => APTO_API.render(6)); await page.waitForTimeout(500);
  await page.evaluate(() => { const c = document.querySelector('#layerVerified'); c.checked = false; c.dispatchEvent(new Event('change', { bubbles: true })); });
  h = await leer(); assert.equal(h.piso, true, 'el horneado vuelve tras la vista técnica');
});

test('sol del render V3, focos dirigidos, sombras estáticas y densidad dentro del rango del perfil', { skip: !hayV2 && 'falta construir el V3' }, async t => {
  const page = await open(t);
  const r = await page.evaluate(() => {
    let sol = null, focos = 0, puntuales = 0;
    __ORA.scene.traverse(o => { if (o.isDirectionalLight && o.castShadow) sol = o.position.clone().normalize().toArray(); if (o.isSpotLight) focos++; if (o.isPointLight) puntuales++; });
    return { sol, focos, puntuales, auto: __ORA.renderer.shadowMap.autoUpdate, densidad: APTO_API.densidad };
  });
  const esperado = [0.352, 0.553, 0.755], n = Math.hypot(...esperado);
  r.sol.forEach((v, i) => assert.ok(Math.abs(v - esperado[i] / n) < 0.02, `sol ${r.sol}`));
  assert.equal(r.focos, 4); assert.equal(r.puntuales, 0); assert.equal(r.auto, false);
  assert.ok(r.densidad >= 0.75 && r.densidad <= 1.25, `densidad media ${r.densidad}`);
});

test('GLB derivado: misma arquitectura que el original (nodos, metadatos, materiales y posiciones)', { skip: !fs.existsSync(path.join(dir, 'modelo/web/v4/apto-102-v4.glb')) && 'sin GLB derivado' }, () => {
  const out = execFileSync(process.execPath, [path.join(dir, 'tools/verificar_glb.mjs'), path.join(dir, 'modelo/apto-102-propuesta.glb'), path.join(dir, 'modelo/web/v4/apto-102-v4.glb')]).toString();
  const r = JSON.parse(out);
  assert.deepEqual(r.problemas, []); assert.ok(r.nodos_con_uv1 >= 25, 'las mallas fijas tienen UV de luz');
});

test('atlas de luz en muros y superficies fijas; vidrios, espejos y emisivos quedan en tiempo real', { skip: !hayV2 && 'falta construir la V4' }, async t => {
  const page = await open(t);
  const r = await page.evaluate(() => {
    const m = {}; __ORA.scene.traverse(o => { if (o.isMesh && o.material?.name && !(o.material.name in m)) m[o.material.name] = { atlas: o.material.userData?.mapaLuz === 'atlas', lm: !!o.material.lightMap, uv1: !!o.geometry.attributes.uv1 }; });
    return { m, stats: APTO_API.lightmaps };
  });
  for (const n of ['muro', 'carpinteria', 'gabinete_cocina', 'meson']) assert.ok(r.m[n]?.atlas && r.m[n]?.lm, `${n} con atlas de luz`);
  for (const n of ['vidrio', 'luz_calida']) assert.ok(!r.m[n]?.atlas, `${n} sin atlas`);
  assert.ok(r.stats.materiales >= 30 && r.stats.atlas);
});

test('caminar: acelera y frena suave, no atraviesa muros', { skip: !hayV2 && 'falta construir la V4' }, async t => {
  const page = await open(t);
  await page.evaluate(() => APTO_API.setMode('walk')); await settle(page);
  const a = await page.evaluate(() => APTO_API.state.plan);
  await page.evaluate(() => APTO_API.joystick(0, -1));
  await page.waitForFunction(a => { const b = APTO_API.state.plan; return Math.hypot(b.x - a.x, b.y - a.y) > 0.4; }, a, { timeout: 30000 });
  await page.evaluate(() => APTO_API.joystick(0, 0));
  // tras soltar, sigue avanzando un poco (inercia) y se detiene
  const b = await page.evaluate(() => APTO_API.state.plan);
  await page.waitForTimeout(1500);
  const c = await page.evaluate(() => APTO_API.state.plan);
  assert.ok(Math.hypot(c.x - b.x, c.y - b.y) < 0.6, 'se detiene');
  assert.ok(await page.evaluate(() => APTO_API.free(APTO_API.state.plan.x, APTO_API.state.plan.y)), 'sigue en un punto libre');
});
