// Apartamento 104 (Torre 1): geometría verificada, modelo GLB y experiencia 3D navegable (fase 3).
const { test, before, after } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { spawn } = require('node:child_process');
const { once } = require('node:events');
const { chromium } = require('playwright');

const root = path.resolve(__dirname, '..');
const dir = path.join(root, 'apartamento-104');
const geo = JSON.parse(fs.readFileSync(path.join(dir, 'data/geometria-104.json'), 'utf8'));
const prop = JSON.parse(fs.readFileSync(path.join(dir, 'data/propuesta-balcon.json'), 'utf8'));
const glbBuf = fs.readFileSync(path.join(dir, 'modelo/apto-104.glb'));
const gltf = JSON.parse(glbBuf.subarray(20, 20 + glbBuf.readUInt32LE(12)).toString('utf8'));
const nodes = Object.fromEntries(gltf.nodes.map(n => [n.name, n.extras]));
const base = 'http://127.0.0.1:18781/apartamento-104/';
// el render por software (swiftshader) de las pruebas es lento: calidad media y ventanas moderadas
const Q = '?calidad=media';
let browser, server;

before(async () => {
  server = spawn(process.execPath, ['server.mjs'], { cwd: root, env: { ...process.env, PORT: '18781' }, stdio: ['ignore', 'pipe', 'pipe'] });
  await once(server.stdout, 'data');
  const executablePath = process.env.CHROMIUM_PATH || (fs.existsSync('/usr/bin/chromium') ? '/usr/bin/chromium' : undefined);
  browser = await chromium.launch({ executablePath, args: ['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
});
after(async () => { await browser?.close(); if (server?.exitCode === null) { const e = once(server, 'exit'); server.kill(); await e; } });

async function open(t, width = 960, height = 600, url = base + Q) {
  const context = await browser.newContext({ viewport: { width, height }, deviceScaleFactor: 1, isMobile: width < 700, hasTouch: width < 900, reducedMotion: 'no-preference' });
  t.after(() => context.close());
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  page.on('console', m => { if (m.type() === 'error' && !/Failed to load resource/.test(m.text())) errors.push(m.text()); });
  page.on('requestfailed', r => { if (!/fonts\.(googleapis|gstatic)/.test(r.url())) errors.push('recurso: ' + r.url()); });
  t.after(() => assert.deepEqual(errors, [], 'sin errores de JavaScript ni de carga de recursos'));
  await page.route('https://fonts.googleapis.com/**', r => r.abort());
  await page.goto(url);
  await page.waitForFunction(() => window.APTO_API?.ready, null, { timeout: 90000 });
  return page;
}
const settle = page => page.waitForFunction(() => !APTO_API.state.flying, null, { timeout: 60000 });
const frames = async (page, n = 2) => { await page.evaluate(() => APTO_API.render(4)); const f = await page.evaluate(() => APTO_API.state.frame); await page.waitForFunction(v => APTO_API.state.frame >= v, f + n, { timeout: 60000 }); };
const tab = (page, id) => page.locator(`#tabs [data-tab="${id}"]`).click();

// ------------------------------------------------------------------ geometría tomada del DWG
test('identificación y cotas verificables del apartamento 104', () => {
  assert.equal(geo.apartamento, '104'); assert.equal(geo.torre, 'Torre 1');
  assert(geo.identificacion['APTO 104']?.length, 'rótulo APTO 104 del plano');
  assert(geo.identificacion['AREA 60.01m2']?.length, 'rótulo de área del plano');
  const values = new Set(geo.cotas.map(d => d.medida));
  for (const v of [7.45, 7.6, 2.475, 3.6, 2.75, 1.7, 1.65, 1.5, 2.15, 1.525, 1.39, 1.36, 1.21, 1.95, 2.19, 1.16, 1.24, 0.72, 1.28, 0.8, 0.85]) assert(values.has(v), `cota ${v}`);
  assert.deepEqual(geo.envolvente_exterior, [0, 0, 8.1, 7.6]);
  assert.equal(geo.puertas.length, 6); assert.equal(geo.ventanas.length, 4);
  assert.deepEqual(geo.ventanas.map(v => v.ancho).sort(), [1, 1, 1, 2.475]);
});

test('ocho espacios; la diferencia 59,43 / 60,01 m² sigue sin conciliar', () => {
  assert.equal(geo.espacios.length, 8);
  const byId = Object.fromEntries(geo.espacios.map(r => [r.id, r.area_neta_m2]));
  assert(byId.social > 17.5 && byId.social < 18.5);
  for (const id of ['alcoba_2', 'alcoba_3', 'alcoba_principal']) assert(byId[id] > 6 && byId[id] < 9.5, id);
  for (const id of ['bano_social', 'bano_principal']) assert(byId[id] > 1.5 && byId[id] < 3, id);
  const total = +(geo.areas.interior_neta_m2 + geo.areas.muros_dentro_envolvente_m2).toFixed(2);
  assert.equal(total, 59.43, 'interior neta + muros medidos');
  assert(geo.pendientes.some(p => /Altura libre/.test(p)), 'la altura se declara pendiente');
  const medidas = fs.readFileSync(path.join(dir, 'MEDIDAS.md'), 'utf8');
  assert(/59,43/.test(medidas) && /60,01/.test(medidas), 'MEDIDAS.md documenta ambas cifras');
});

// ------------------------------------------------------------------ modelo
test('el GLB clasifica cada nodo: verificado, provisional, ilustrativo o propuesta', () => {
  assert.equal(glbBuf.readUInt32LE(0), 0x46546c67); assert.equal(glbBuf.readUInt32LE(4), 2);
  for (const [name, x] of Object.entries(nodes)) {
    if (name === 'Apto_104_Torre_1') continue;
    assert(['verificado', 'provisional', 'ilustrativo', 'propuesta'].includes(x.categoria), `${name}: ${x.categoria}`);
    if (/^ARQ_(Muros|Piso)/.test(name) || /^APA_/.test(name)) assert.equal(x.categoria, 'verificado', name);
    if (/^ARQ_(Losa|Dinteles|Cielo)/.test(name)) assert.equal(x.categoria, 'provisional', name);
    if (/^(MOB|ILU)_/.test(name) && x.grupo !== 'propuesta_mobiliario' && x.grupo !== 'sin_balcon') assert.equal(x.verificado, false, name);
    if (/^PROP_/.test(name)) assert.equal(x.categoria, 'propuesta', name);
  }
  assert.equal(nodes.MOB_Balcon.categoria, 'propuesta');
  assert.equal(nodes.MOB_Alcoba_2.propuesta_mobiliario, 'estudio', 'la alcoba 2 como estudio se declara propuesta de mobiliario');
  assert.equal(nodes.Apto_104_Torre_1.supuestos_visualizacion.altura_libre, 2.4);
  for (const n of ['MOB_Sofa', 'MOB_Sala', 'MOB_Comedor', 'MOB_Cocina', 'MOB_Ropas', 'MOB_Alcoba_principal', 'MOB_Alcoba_3', 'MOB_Alcoba_2', 'MOB_Banos', 'MOB_Cortinas_sala',
    'ILU_Revestimientos', 'ILU_Guardaescobas', 'ILU_Marcos_puertas', 'ILU_Luminarias']) assert(nodes[n], `existe ${n}`);
});

test('la arquitectura del GLB coincide con la envolvente del DWG (sin cambios de la fase 3)', () => {
  const mesh = gltf.meshes[gltf.nodes.find(n => n.name === 'ARQ_Muros').mesh];
  const acc = gltf.accessors[mesh.primitives.find(p => gltf.materials[p.material].name === 'muro').attributes.POSITION];
  const close = (a, b) => a.every((v, i) => Math.abs(v - b[i]) < 1e-4);
  assert(close(acc.min, [-4.05, 0, -3.8]) && close(acc.max, [4.05, 2.4, 3.8]), `${acc.min} ${acc.max}`);
  const areaMuros = geo.muros_rectangulos.reduce((s, [x0, y0, x1, y1]) => s + (x1 - x0) * (y1 - y0), 0);
  assert(Math.abs(areaMuros - geo.areas.muros_dentro_envolvente_m2) < 0.05);
});

// ------------------------------------------------------------------ circulación con el mobiliario (prueba geométrica)
const R = 0.22;
const huellas = Object.entries(nodes).filter(([n]) => /^(MOB|APA|PROP)_/.test(n)).flatMap(([, x]) => x.huella || []);
const hojas = Object.values(nodes).flatMap(x => x.segmentos || []);
const sala = geo.ventanas.find(w => w.ancho === 2.475);
function segDist(px, py, [ax, ay, bx, by]) { const dx = bx - ax, dy = by - ay, t = Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy))); return Math.hypot(px - ax - t * dx, py - ay - t * dy); }
function libre(x, y, conBalcon = true, r = R) {
  const [bx0, by0, bx1] = prop.rect_util;
  const enBalcon = conBalcon && x >= bx0 + r && x <= bx1 - r && y >= by0 + r && y < r + 0.01;
  if (!enBalcon && (x < r || x > 8.1 - r || y < r || y > 7.6 - r)) return false;
  const obs = [...geo.muros_rectangulos, ...geo.ventanas.filter(w => w !== sala).map(w => [w.x0, w.y0, w.x1, w.y1]), geo.puertas.find(d => d.id === 'entrada').rect, ...huellas,
    conBalcon ? [prop.acceso.hojas_cerradas[0], 0, prop.acceso.hojas_cerradas[1], 0.15] : [sala.x0, sala.y0, sala.x1, sala.y1]];
  if (obs.some(([a, b, c, d]) => x > a - r && x < c + r && y > b - r && y < d + r)) return false;
  return !hojas.some(s => segDist(x, y, s) < r + s[4] / 2);
}
function alcanzables(conBalcon) {
  const st = 0.02, x0 = -0.2, y0 = -1.8, nx = 426, ny = 481, seen = new Uint8Array(nx * ny);
  const id = (x, y) => Math.round((y - y0) / st) * nx + Math.round((x - x0) / st);
  const q = [id(0.65, 7.0)]; seen[q[0]] = 1;
  while (q.length) {
    const k = q.pop(), i = k % nx, j = (k - i) / nx;
    for (const [di, dj] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
      const a = i + di, b = j + dj; if (a < 0 || b < 0 || a >= nx || b >= ny) continue;
      const kk = b * nx + a; if (seen[kk]) continue;
      if (libre(x0 + a * st, y0 + b * st, conBalcon)) { seen[kk] = 1; q.push(kk); }
    }
  }
  return (x, y) => !!seen[id(x, y)];
}

test('con el mobiliario puesto se llega caminando a todos los recintos y al balcón', () => {
  const ok = alcanzables(true);
  const puntos = { sala: [1.55, 0.75], comedor: [2.3, 4.5], cocina: [1.7, 6.4], ropas: [3.2, 6.0], circulacion: [3.0, 3.3], bano_social: [3.15, 4.15], alcoba_2: [4.0, 1.6],
    alcoba_3: [6.1, 2.7], alcoba_principal: [5.9, 4.4], cama_principal: [6.8, 5.25], bano_principal: [4.9, 5.4], balcon: [0.8, -0.7] };
  for (const [k, [x, y]] of Object.entries(puntos)) assert(ok(x, y), `se llega a ${k}`);
  assert(alcanzables(false)(4.9, 5.4), 'sin balcón también');
});

test('el mobiliario no ocupa vanos de puerta ni la puerta-ventana del balcón', () => {
  const vanos = [...geo.umbrales, [prop.acceso.paso_libre[0], -0.5, prop.acceso.paso_libre[1], 0.15]];
  const muebles = Object.entries(nodes).filter(([n]) => /^(MOB|PROP)_/.test(n)).flatMap(([n, x]) => (x.huella || []).map(h => [n, h]));
  for (const [n, [a, b, c, d]] of muebles) for (const [e, f, g, h] of vanos) assert(!(a < g && c > e && b < h && d > f), `${n} invade un vano`);
  for (const [n, [a, b, c, d]] of muebles) assert(a >= -0.01 && c <= 8.11 && b >= -1.71 && d <= 7.61, `${n} dentro de la envolvente o del balcón`);
});

// ------------------------------------------------------------------ visor
test('el visor carga el GLB, dibuja la escena y ofrece puntos interactivos y leyenda', async t => {
  const page = await open(t);
  const shot = await page.locator('#scene').screenshot({ timeout: 120000 });
  assert(shot.length > 30000, 'la escena tiene contenido');   // un lienzo vacío comprime a pocos KB
  assert.equal(await page.locator('.hs').count(), 9);              // 8 espacios del plano + balcón propuesto
  assert.equal(await page.locator('#rooms button').count(), 9);
  assert.equal(await page.locator('.hs.prop').count(), 1);
  assert.equal(await page.locator('.poi').count(), 13);
  assert.equal(await page.locator('.legend li').count(), 4);
  const stats = await page.evaluate(() => APTO_API.stats);
  assert(stats.verificados >= 12 && stats.ilustrativos >= 20);
  for (const m of ['muro', 'piso_madera', 'meson', 'gabinete_cocina', 'revestimiento_bano', 'tela_sofa', 'espejo_principal']) assert(stats.materiales.includes(m), m);
  assert(stats.categorias.provisional >= 3 && stats.categorias.propuesta >= 4);
});

test('elegir un espacio lleva la cámara hasta él', async t => {
  const page = await open(t);
  await frames(page);
  await page.locator('.hs[data-room="alcoba_2"]').click();      // punto interactivo desde la maqueta completa
  await settle(page);
  assert.equal((await page.evaluate(() => APTO_API.state)).room, 'alcoba_2');
  await page.locator('#rooms button[data-room="alcoba_principal"]').click();
  await settle(page);
  const s = await page.evaluate(() => APTO_API.state);
  assert.equal(s.room, 'alcoba_principal');
  assert(s.target.x > 5.45 && s.target.y > 3.9 && s.target.y < 7.45, `la cámara apunta a la alcoba principal (${s.target.x}, ${s.target.y})`);
});

test('caminar: altura de ojos y colisiones con muros, mobiliario y hojas de puerta', async t => {
  const page = await open(t);
  await page.locator('[data-mode="walk"]').click();
  await settle(page); await frames(page);
  let s = await page.evaluate(() => APTO_API.state);
  assert.equal(s.mode, 'walk'); assert.equal(s.height, 1.6); assert.equal(s.room, 'social');
  await page.evaluate(() => APTO_API.move(0, 1.2));         // a la altura del mueble de TV
  await page.evaluate(() => APTO_API.move(3, 0));           // hacia el mueble de TV y el muro
  s = await page.evaluate(() => APTO_API.state);
  assert(s.plan.x <= 2.325 - 0.22 + 1e-3, `se detiene ante el mueble de TV (${s.plan.x})`);
  const doors = await page.evaluate(g => g.puertas.filter(d => d.id !== 'entrada').map(d => { const [x0, y0, x1, y1] = d.rect; return APTO_API.free((x0 + x1) / 2, (y0 + y1) / 2); }), geo);
  assert.deepEqual(doors, [true, true, true, true, true], 'todos los vanos interiores son transitables');
  const walls = await page.evaluate(g => g.muros_rectangulos.filter(([x0, y0, x1, y1]) => (x1 - x0) * (y1 - y0) > .1).map(([x0, y0, x1, y1]) => APTO_API.free((x0 + x1) / 2, (y0 + y1) / 2)), geo);
  assert(walls.every(v => v === false), 'ningún muro es atravesable');
  const muebles = await page.evaluate(() => ({ sofa: APTO_API.free(0.6, 2.0), cama: APTO_API.free(7.0, 6.3), comedor: APTO_API.free(1.4, 4.55), hoja: APTO_API.free(5.95, 4.86), nevera: APTO_API.free(0.5, 6.0) }));
  assert.deepEqual(muebles, { sofa: false, cama: false, comedor: false, hoja: false, nevera: false });
  assert.equal(await page.evaluate(() => APTO_API.free(0.65, 7.55)), false, 'no se sale al corredor');
  await tab(page, 'capas').catch(() => {});
  await page.evaluate(() => { document.querySelector('#layerFurniture').click(); });
  assert.equal(await page.evaluate(() => APTO_API.free(0.6, 2.0)), true, 'sin mobiliario el sofá deja de ser obstáculo');
  assert.equal(await page.locator('#walkpad').isVisible(), true);
  await page.keyboard.press('Escape');
  assert.equal((await page.evaluate(() => APTO_API.state)).mode, 'orbit');
});

test('tocar el piso al caminar desplaza hasta ese punto', async t => {
  const page = await open(t);
  await page.evaluate(() => APTO_API.setMode('walk')); await settle(page);
  await page.evaluate(() => APTO_API.walkTo({ x: 2.0, y: 2.2 }));
  await page.waitForFunction(() => APTO_API.state.plan.y > 2.0, null, { timeout: 90000 });
  assert.equal((await page.evaluate(() => APTO_API.state)).room, 'social');
});

test('la trayectoria del recorrido no atraviesa muros, muebles ni barandas', async t => {
  const page = await open(t);
  for (const conBalcon of [true, false]) {
    await page.evaluate(b => APTO_API.setBalcony(b), conBalcon);
    const pts = await page.evaluate(() => APTO_API.tourSample(0.04));
    const chapters = new Set(pts.map(p => p.c));
    assert.equal(chapters.size, 12, 'doce capítulos');
    const muros = [...geo.muros_rectangulos, ...geo.ventanas.map(w => [w.x0, w.y0, w.x1, w.y1])];
    let prev = null;
    for (const p of pts) {
      const dentro = p.x > 0 && p.x < 8.1 && p.y > 0 && p.y < 7.6;
      if (p.h < 2.55 && dentro) {
        const m = 0.1;
        const choca = muros.find(([a, b, c, d]) => p.x > a - m && p.x < c + m && p.y > b - m && p.y < d + m && !(conBalcon && p.y < 0.3 && p.x < prop.acceso.paso_libre[1] - 0.15 && p.x > prop.acceso.paso_libre[0] + 0.15));
        assert(!choca, `t=${p.t}: la cámara cruza un muro o ventana en (${p.x.toFixed(2)}, ${p.y.toFixed(2)})`);
        const mueble = huellas.find(([a, b, c, d]) => p.x > a - 0.05 && p.x < c + 0.05 && p.y > b - 0.05 && p.y < d + 0.05);
        assert(!mueble, `t=${p.t}: pasa sobre un mueble en (${p.x.toFixed(2)}, ${p.y.toFixed(2)})`);
        assert(!hojas.some(s => segDist(p.x, p.y, s) < 0.1), `t=${p.t}: atraviesa una hoja de puerta`);
      }
      if (conBalcon && p.y < 0 && p.y > -1.75 && p.x > 0 && p.x < 2.8) assert(p.x > 0.15 && p.x < 2.625 && p.y > -1.62 || p.h > 1.2, `t=${p.t}: la cámara cruza la baranda`);
      if (prev) assert(Math.hypot(p.x - prev.x, p.y - prev.y, p.h - prev.h) / 0.04 < (p.h > 2.6 ? 9 : 2.0), `t=${p.t}: movimiento brusco`);
      prev = p;
    }
  }
});

test('recorrido de 12 capítulos: se pausa al tocar y se pasa a explorar desde ahí', async t => {
  const page = await open(t);
  await page.locator('[data-mode="tour"]').click();
  assert.equal(await page.locator('#tourbar').isVisible(), true);
  const chapters = await page.evaluate(() => APTO_API.chapters());
  assert.equal(chapters.length, 12);
  const seen = [];
  for (const time of [25, 42, 60, 69, 85, 99, 112.6, 131]) {
    await page.evaluate(v => APTO_API.tourSeek(v), time); await frames(page);
    const s = await page.evaluate(() => APTO_API.state);
    seen.push(s.room);
  }
  for (const id of ['social', 'ropas', 'alcoba_principal', 'bano_principal', 'alcoba_3', 'alcoba_2', 'bano_social', 'balcon']) assert(seen.includes(id), `visita ${id}: ${seen}`);
  await page.evaluate(() => APTO_API.tourSeek(30)); await frames(page);
  await page.locator('#scene').click({ position: { x: 300, y: 300 } });
  assert.equal((await page.evaluate(() => APTO_API.state)).tourPlaying, false, 'tocar la escena pausa');
  assert.equal(await page.locator('#tourName').textContent(), 'Sala y comedor');
  await page.locator('#tourPlay').click();
  assert.equal((await page.evaluate(() => APTO_API.state)).tourPlaying, true);
  await page.locator('#tourExplore').click(); await frames(page);
  const s = await page.evaluate(() => APTO_API.state);
  assert.equal(s.mode, 'walk'); assert.equal(s.height, 1.6); assert.equal(s.room, 'social');
  assert.equal(await page.evaluate(p => APTO_API.free(p.x, p.y), s.plan), true, 'empieza a caminar en un punto libre');
  await page.evaluate(() => APTO_API.setMode('tour'));
  await page.evaluate(() => APTO_API.tourSeek(APTO_API.state.tourLen - 0.05)); await frames(page, 4);
  const end = await page.evaluate(() => APTO_API.state);
  assert.equal(end.tourPlaying, false, 'al terminar queda en pausa sobre la vista exterior');
});

test('tres propuestas de acabados y cambios por elemento sobre el mismo modelo', async t => {
  const page = await open(t);
  await tab(page, 'acabados');
  assert.match(await page.locator('[data-pane="acabados"] .note').textContent(), /ilustrativos y no contractuales/);
  assert.equal(await page.locator('#presets button').count(), 3);
  const leer = () => page.evaluate(() => ({ muro: APTO_API.wallColor(), piso: APTO_API.matInfo('piso_madera').mapId, cocina: APTO_API.matInfo('gabinete_cocina').mapId, bano: APTO_API.matInfo('revestimiento_bano').mapId, sofa: APTO_API.matInfo('tela_sofa').color }));
  const looks = [];
  for (const id of ['calida', 'sofisticada', 'luminosa']) {
    await page.locator(`#presets button[data-id="${id}"]`).click();
    const s = await page.evaluate(() => APTO_API.state);
    assert.equal(s.preset, id); assert.equal(s.custom, false);
    looks.push(await leer());
  }
  for (const k of ['muro', 'piso', 'cocina', 'bano', 'sofa']) assert.equal(new Set(looks.map(l => l[k])).size, 3, `${k} cambia entre propuestas`);
  await page.locator('#walls button[data-id="salvia"]').click();
  await page.locator('#kitchen button[data-id="roble_cuarzo"]').click();
  await page.locator('#bath button[data-id="piedra"]').click();
  await page.locator('#floors button[data-id="nogal"]').click();
  const s = await page.evaluate(() => APTO_API.state);
  assert.deepEqual([s.wall, s.kitchen, s.bath, s.floor, s.custom], ['salvia', 'roble_cuarzo', 'piedra', 'nogal', true]);
  assert.equal(await page.evaluate(() => APTO_API.wallColor()), '#bfc8b3');
  assert.equal(await page.evaluate(() => APTO_API.matInfo('piso_madera').normal), true, 'el piso tiene relieve (normal map)');
  assert.match(await page.locator('#presetNote').textContent(), /Personalizada/);
});

test('«Solo arquitectura verificada» oculta acabados, muebles, balcón y entorno', async t => {
  const page = await open(t);
  await tab(page, 'capas');
  await page.evaluate(() => APTO_API.setMode('walk')); await settle(page);
  assert.equal(await page.evaluate(() => APTO_API.state.environment), true);
  await page.locator('#panelToggle').click();
  await page.locator('#layerVerified').check();
  const v = n => page.evaluate(n => APTO_API.visible(n), n);
  for (const n of ['MOB_Sofa', 'PROP_Balcon_losa', 'MOB_Balcon', 'ILU_Ventaneria', 'ILU_Revestimientos', 'ILU_Puerta_entrada']) assert.equal(await v(n), false, n);
  for (const n of ['ARQ_Muros', 'APA_Cocina', 'ARQ_Dinteles_Antepechos']) assert.equal(await v(n), true, n);
  const s = await page.evaluate(() => APTO_API.state);
  assert.equal(s.technical, true); assert.equal(s.environment, false); assert.equal(s.balcony, false);
  assert.equal(await page.locator('#techTag').isVisible(), true);
  assert.equal(await page.locator('#layerBalcony').isDisabled(), true);
  assert.equal(await page.evaluate(() => APTO_API.free(1.4, 4.55)), true, 'sin muebles el comedor es transitable');
  await page.locator('#layerVerified').uncheck();
  assert.equal(await v('MOB_Sofa'), true);
  assert.equal((await page.evaluate(() => APTO_API.state)).technical, false);
  assert.notEqual(await page.evaluate(() => APTO_API.wallColor()), '#e7e5e0', 'vuelven los acabados');
  await page.locator('#layerDims').check(); await page.evaluate(() => APTO_API.setMode('orbit')); await settle(page); await frames(page);
  assert(await page.locator('.dim:not([hidden])').count() > 10, 'cotas del plano visibles');
});

test('los puntos de información explican la categoría de cada elemento', async t => {
  const page = await open(t);
  await page.evaluate(() => APTO_API.openPoi('balcon'));
  assert.equal(await page.locator('#poiCard').isVisible(), true);
  assert.match(await page.locator('#poiCat').textContent(), /Propuesta/);
  assert.match(await page.locator('#poiD').textContent(), /licencia/);
  await page.locator('#poiClose').click();
  assert.equal(await page.locator('#poiCard').isVisible(), false);
  await page.evaluate(() => APTO_API.setMode('walk')); await settle(page);
  await page.evaluate(() => APTO_API.pose(1.6, 5.9, 1.6, 1.9, 7.3, 1.2)); await frames(page, 3);
  const cocina = page.locator('.poi[data-poi="cocina"]');
  await page.waitForFunction(() => !document.querySelector('.poi[data-poi="cocina"]').classList.contains('off'), null, { timeout: 60000 });
  await cocina.click();
  assert.match(await page.locator('#poiCat').textContent(), /Verificado/);
  await page.evaluate(() => APTO_API.openPoi('acabados'));
  await page.locator('#poiAct').click();
  assert.equal(await page.locator('[data-pane="acabados"]').isVisible(), true, 'el punto abre los acabados');
});

test('calidad alta: oclusión ambiental sin errores', async t => {
  const page = await open(t, 640, 400, base + '?calidad=alta');
  await frames(page, 2);
  assert.equal((await page.evaluate(() => APTO_API.state)).quality, 'alta');
  await page.evaluate(() => APTO_API.setQuality('media')); await frames(page, 1);
  assert.equal((await page.evaluate(() => APTO_API.state)).quality, 'media');
});

for (const [width, height] of [[390, 844], [320, 568], [844, 390], [768, 1024]]) {
  test(`proporciones compactas en ${width}x${height}`, async t => {
    const page = await open(t, width, height);
    const box = sel => page.locator(sel).evaluate(e => { const r = e.getBoundingClientRect(); return { x: r.x, y: r.y, w: r.width, h: r.height, r: r.right, b: r.bottom }; });
    const card = await box('#card'), modes = await box('#modes'), panel = await box('#panel');
    assert(card.w <= 330 && card.h <= 110, `ficha pequeña (${card.w}×${card.h})`);
    assert(panel.h <= 50, `opciones plegadas (${panel.h}px)`);
    assert(modes.r <= width && modes.x >= 0, 'modos dentro de la pantalla');
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    await page.locator('#panelToggle').click();
    const open_ = await box('#panel');
    assert(open_.y >= 60 && open_.b <= height, 'opciones desplegadas dentro de la pantalla');
    await tab(page, 'acabados');
    const fin = await box('#panel');
    assert(fin.y >= 60 && fin.b <= height && fin.r <= width, 'acabados dentro de la pantalla');
    await page.locator('#panelToggle').click();
    await page.evaluate(() => APTO_API.setMode('tour'));
    const bar = await box('#tourbar'), m2 = await box('#modes');
    assert(bar.x >= 0 && bar.r <= width && bar.h <= 56, `barra del recorrido compacta (${bar.w}×${bar.h})`);
    assert(bar.b <= m2.y + 1, 'la barra no tapa los modos');
  });
}

test('se abre también directamente desde el archivo (sin servidor)', async t => {
  const page = await open(t, 960, 600, 'file://' + path.join(dir, 'index.html') + Q);
  assert.equal(await page.locator('.hs').count(), 9);
});

// ------------------------------------------------------------------ propuesta de balcón (no figura en el DWG)
test('el balcón propuesto mide 4,01 m², es exterior y no altera la geometría verificada', () => {
  assert.equal(prop.verificado, false); assert.equal(prop.estado, 'propuesta');
  assert.equal(+(prop.ancho_util * prop.fondo_util).toFixed(2), prop.area_util_m2);
  assert(prop.area_util_m2 >= 3.9 && prop.area_util_m2 <= 4.1);
  const [x0, y0, x1, y1] = prop.rect_util;
  assert(y1 <= 0 && y0 < 0, 'en voladizo, fuera de la envolvente');
  assert.equal(x0, sala.x0); assert.equal(x1, sala.x1); assert.equal(prop.acceso.vano.join(), [sala.x0, sala.y0, sala.x1, sala.y1].join());
  assert.equal(geo.espacios.find(r => r.id === 'social').area_neta_m2, 18.07, 'la sala no cambia');
  assert(!geo.espacios.some(r => r.id === 'balcon'), 'el balcón no entra en la geometría verificada');
  for (const n of gltf.nodes.filter(n => /^PROP_/.test(n.name))) assert.equal(n.extras.verificado, false, n.name);
  assert.equal(gltf.nodes.filter(n => /^PROP_/.test(n.name)).length, 3);
});

test('se sale al balcón por la puerta-ventana, se vuelve y la propuesta se puede desactivar', async t => {
  const page = await open(t);
  assert.equal(await page.locator('#chipProp').isVisible(), true);
  await page.evaluate(() => APTO_API.setMode('walk')); await settle(page);
  await page.locator('#panelToggle').click();                   // dentro del apartamento las opciones van plegadas
  await page.locator('#rooms button[data-room="balcon"]').click();
  await settle(page); await frames(page);
  let s = await page.evaluate(() => APTO_API.state);
  assert.equal(s.room, 'balcon'); assert(s.plan.y < 0, 'la cámara está en el balcón');
  assert.equal(await page.locator('#envTag').isVisible(), true, 'el entorno exterior se rotula como conceptual');
  const f = await page.evaluate(() => ({
    paso: APTO_API.free(0.75, 0.07), hojas: APTO_API.free(2.0, 0.07), balcon: APTO_API.free(0.8, -0.6),
    baranda: APTO_API.free(0.8, -1.55), afuera: APTO_API.free(0.6, -2.5), sillas: APTO_API.free(2.0, -0.5), jardinera: APTO_API.free(0.3, -1.2),
  }));
  assert.deepEqual(f, { paso: true, hojas: false, balcon: true, baranda: false, afuera: false, sillas: false, jardinera: false });
  await page.evaluate(() => APTO_API.walkTo({ x: 0.8, y: 0.9 }));   // regreso a la sala por la puerta-ventana
  await page.waitForFunction(() => APTO_API.state.plan.y > 0.5, null, { timeout: 90000 });
  assert.equal((await page.evaluate(() => APTO_API.state)).room, 'social');
  assert.equal(await page.evaluate(() => APTO_API.visible('ILU_Ventana_sala')), false);
  // sin la propuesta vuelve la ventana original y el balcón desaparece
  await tab(page, 'capas');
  await page.locator('#layerBalcony').uncheck();
  s = await page.evaluate(() => APTO_API.state);
  assert.equal(s.balcony, false);
  assert.equal(await page.evaluate(() => APTO_API.free(0.75, 0.07)), false);
  assert.equal(await page.evaluate(() => APTO_API.visible('PROP_Balcon_losa')), false);
  assert.equal(await page.evaluate(() => APTO_API.visible('ILU_Ventana_sala')), true);
  assert.equal(await page.evaluate(() => APTO_API.visible('ILU_Antepecho_sala')), true);
  assert.equal(await page.locator('#chipProp').isVisible(), false);
  assert(s.tourLen < 138, 'el recorrido termina en la ventana de la sala');
});
