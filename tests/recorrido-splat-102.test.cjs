// Piloto de Gaussian Splatting del apartamento 102 (apartamento-102/recorrido-splat.html). PROPUESTA DE REDISTRIBUCIÓN,
// no planta verificada. Comprueba, ANTES de pagar la nube, lo que se puede comprobar en el Mac:
//  - V4, V5, el modelo original y los .blend maestros no cambian;
//  - la conversión de cámaras a COLMAP proyecta igual que Blender (si hay Blender instalado);
//  - la página del piloto carga un splat (sintético) con Spark, lo orienta como el GLB (Z de Blender → Y de three),
//    lo alinea con la malla (parche de calibración en el centro de la vista) y conserva el color sRGB;
//  - la navegación y los rótulos de propuesta de la V5 siguen activos y la tecla M alterna splat ↔ malla.
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
const PRUEBA = 'modelo/web/splat/_prueba_tests.ply';
const base = 'http://127.0.0.1:18787/apartamento-102/recorrido-splat.html';
const hayBuild = fs.existsSync(path.join(dir, 'dist/recorrido-splat-app.js')) && fs.existsSync(path.join(dir, 'dist/recorrido-v5-datos.js'));
let browser, server;

before(async () => {
  // splat sintético mínimo: un piso de gaussianas grises en el espacio social + el parche de calibración (sRGB 200,100,50)
  const pts = path.join(require('node:os').tmpdir(), 'ora_puntos_prueba.txt'); const filas = [];
  for (let x = -4.0; x <= 0; x += 0.04) for (let y = -3.7; y <= 3.7; y += 0.04) filas.push(`${x.toFixed(3)} ${y.toFixed(3)} 0.01 180 175 165`);
  fs.writeFileSync(pts, filas.join('\n') + '\n');
  execFileSync(process.execPath, [path.join(root, 'tools/splat/ply_sintetico.mjs'), pts, path.join(dir, PRUEBA), '0.0186', '--parche'], { cwd: root });
  server = spawn(process.execPath, ['server.mjs'], { cwd: root, env: { ...process.env, PORT: '18787' }, stdio: ['ignore', 'pipe', 'pipe'] });
  await once(server.stdout, 'data');
  const executablePath = process.env.CHROMIUM_PATH || (fs.existsSync('/usr/bin/chromium') ? '/usr/bin/chromium' : undefined);
  browser = await chromium.launch({ executablePath, args: ['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
});
after(async () => {
  await browser?.close(); if (server?.exitCode === null) { const e = once(server, 'exit'); server.kill(); await e; }
  fs.rmSync(path.join(dir, PRUEBA), { force: true });
});

test('el piloto no modifica la V4, la V5, el modelo original ni los .blend maestros', () => {
  if (fs.existsSync(path.join(root, '.git'))) {
    for (const [rama, rutas] of [
      ['feat/apto-102-recorrido-v5', ['apartamento-102/recorrido-v5.html', 'apartamento-102/src/app-recorrido-v5.mjs', 'apartamento-102/css/recorrido-v5.css', 'apartamento-102/tools/build_recorrido_v5.mjs', 'apartamento-102/modelo/web/v5']],
      ['feat/apto-102-recorrido-v4', ['apartamento-102/recorrido-v4.html', 'apartamento-102/src/app-recorrido-v4.mjs', 'apartamento-102/css/recorrido-v4.css', 'apartamento-102/tools/build_recorrido_v4.mjs', 'apartamento-102/modelo/web/v4']],
    ]) {
      let ref = null; try { ref = execFileSync('git', ['rev-parse', '--verify', '-q', rama], { cwd: root }).toString().trim(); } catch {}
      if (!ref) continue;
      const d = execFileSync('git', ['diff', '--name-only', ref, '--', ...rutas], { cwd: root }).toString().trim();
      assert.equal(d, '', `${rama} sin cambios`);
    }
  }
  // hashes de los maestros registrados al empaquetar (tools/splat/maestros.sha256)
  for (const l of fs.readFileSync(path.join(root, 'tools/splat/maestros.sha256'), 'utf8').trim().split('\n')) {
    const [h, f] = l.split(/\s+/); const p = path.join(root, f);
    if (!fs.existsSync(p)) continue;   // los .blend no están en Git: en otra copia del repositorio pueden faltar
    assert.equal(crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex'), h, `${f} intacto`);
  }
});

test('la conversión de cámaras a COLMAP proyecta igual que la cámara de Blender', { skip: !fs.existsSync('/Volumes/Blender/Blender.app') && !process.env.BLENDER }, () => {
  const bl = process.env.BLENDER || '/Volumes/Blender/Blender.app/Contents/MacOS/Blender';
  const t = path.join(root, 'blender/splat_sala_cocina/transforms.json');
  if (!fs.existsSync(t)) return;
  const out = execFileSync(bl, ['-b', '--factory-startup', '--python', path.join(root, 'tools/splat/verificar_poses.py'), '--', t], { cwd: root, timeout: 240000 }).toString();
  const r = JSON.parse(out.split('\n').find(l => l.startsWith('RESULTADO')).slice(10));
  for (const v of Object.values(r.diferencia_max_px)) { assert.ok(v.puntos > 1000); assert.ok(v.px < 0.01, `error ${v.px} px`); }
});

test('la configuración del piloto define vistas de control fuera de muebles y un tope de presupuesto', () => {
  const cfg = JSON.parse(fs.readFileSync(path.join(root, 'blender/scripts/apto-102.json'), 'utf8')).splat;
  assert.equal(cfg.control.vistas.length, 10);
  const g = JSON.parse(fs.readFileSync(path.join(dir, 'data/propuesta-102.json'), 'utf8'));
  const social = g.espacios.find(e => e.id === 'social').piso_rectangulos;
  for (const v of cfg.control.vistas) {
    const [x, y] = v.desde;
    assert.ok(social.some(([a, b, c, d]) => x > a && x < c && y > b && y < d), `${v.id} dentro del espacio social`);
    assert.ok(!Object.values(g.mobiliario).some(r => Array.isArray(r) && r.length === 4 && x > r[0] && x < r[2] && y > r[1] && y < r[3]), `${v.id} fuera de los muebles`);
  }
  assert.ok(cfg.nube.presupuesto_max_usd <= 15 && cfg.nube.limite_horas_gpu <= 4);
});

test('la página del piloto carga el splat con Spark, alineado y con el color correcto; M alterna con la malla V5', { skip: !hayBuild }, async t => {
  const context = await browser.newContext({ viewport: { width: 640, height: 360 }, deviceScaleFactor: 1 });
  t.after(() => context.close());
  const page = await context.newPage(); const errores = [];
  page.on('pageerror', e => errores.push(e.message));
  page.on('console', m => { if (m.type() === 'error' && !/Failed to load resource/.test(m.text())) errores.push(m.text()); });
  await page.route(/fonts\.(googleapis|gstatic)\.com/, r => r.abort());
  await page.goto(`${base}?calidad=media&sincaptura&splat=${PRUEBA}`);
  await page.waitForFunction(() => window.SPLAT_API && (SPLAT_API.estado.cargado || SPLAT_API.estado.error), null, { timeout: 180000 });
  const e = await page.evaluate(() => SPLAT_API.estado);
  assert.equal(e.error, null); assert.ok(e.gaussianas > 15000);
  assert.equal(new URL(page.url()).searchParams.get('densidad'), '1', 'densidad 1,0 por defecto (medida en el M2)');
  assert.match(await page.textContent('body'), /Propuesta de redistribución/i, 'rótulo de propuesta presente');
  // orientación: el splat se gira −90° en X (Blender Z arriba → three Y arriba), sin traslación
  const q = await page.evaluate(() => { let s; __ORA.scene.traverse(o => { if (o.constructor.name === 'SplatMesh' || o.packedSplats) s = o; }); return s && [s.quaternion.x, s.quaternion.w, ...s.position.toArray()]; });
  assert.ok(Math.abs(q[0] + Math.SQRT1_2) < 1e-6 && Math.abs(q[1] - Math.SQRT1_2) < 1e-6 && q.slice(2).every(v => v === 0));
  // alineación y color: mirando el parche (Blender x = −2,0 → planta x = 2,037; y = 3,8; altura 1,2) desde 0,6 m
  await page.evaluate(() => { APTO_API.setMode('walk'); });
  await page.waitForFunction(() => !APTO_API.state.flying, null, { timeout: 60000 });
  await page.evaluate(() => { APTO_API.arch(1.45, 3.8, 2.04, 3.8, 23.457, 0, 1.2); APTO_API.pose(1.45, 3.8, 1.2, 2.04, 3.8, 1.2); });
  await page.waitForTimeout(4000);
  const leer = () => page.evaluate(() => new Promise(r => { APTO_API.render(3); requestAnimationFrame(() => requestAnimationFrame(() => {
    const c = __ORA.renderer.domElement, k = document.createElement('canvas'); k.width = c.width; k.height = c.height;
    const g = k.getContext('2d'); g.drawImage(c, 0, 0); const d = g.getImageData(c.width / 2 - 8, c.height / 2 - 8, 16, 16).data;
    let s = [0, 0, 0]; for (let i = 0; i < d.length; i += 4) { s[0] += d[i]; s[1] += d[i + 1]; s[2] += d[i + 2]; }
    r(s.map(v => Math.round(v / (d.length / 4)))); })); }));
  const cSplat = await leer();
  for (const [v, ref] of cSplat.map((v, i) => [v, [200, 100, 50][i]])) assert.ok(Math.abs(v - ref) <= 14, `color del parche ${cSplat} ≈ 200,100,50`);
  assert.equal(await page.evaluate(() => __ORA.camera.layers.mask), 1 << 5, 'modo splat: la cámara ve solo la capa del splat');
  await page.keyboard.press('m');
  assert.equal(await page.evaluate(() => SPLAT_API.estado.activo), false);
  assert.equal(await page.evaluate(() => __ORA.camera.layers.mask), 1, 'modo malla: la V5 tal cual');
  // las colisiones de la V5 siguen activas en modo splat (no se atraviesan muebles)
  await page.keyboard.press('m');
  assert.equal(await page.evaluate(() => APTO_API.free(0.8, 2.0)), false, 'el sofá sigue siendo un obstáculo');
  assert.deepEqual(errores, []);
});
