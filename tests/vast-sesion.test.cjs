// tools/vast/sesion.sh en modo simulación (ORA_VAST_LOCAL=1): no se conecta a Vast.ai ni usa GPU.
// Construye un /workspace falso con escenas protegidas, un Blender simulado y datos; comprueba cada protección del
// protocolo de sesión de GPU (docs/coordinacion-claude-codex.md). Apartamento 102: propuesta de redistribución.
const { test, beforeEach, afterEach } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync, execFileSync } = require('node:child_process');

const repo = path.resolve(__dirname, '..');
const script = path.join(repo, 'tools/vast/sesion.sh');
const esRepoGit = fs.existsSync(path.join(repo, '.git'));
let raiz, ws, paquete, env;

beforeEach(() => {
  raiz = fs.mkdtempSync(path.join(os.tmpdir(), 'ora-vast-'));
  ws = path.join(raiz, 'workspace'); paquete = path.join(ws, 'ora_restore_4080/proyecto_ora/paquete');
  for (const d of ['escena', 'v4', 'datos/prueba/sub']) fs.mkdirSync(path.join(paquete, d), { recursive: true });
  for (const f of ['escena/escena_splat.blend', 'escena/escena_splat_v2.blend', 'v4/escena_v4.blend', 'v4/escena_v4_1.blend'])
    fs.writeFileSync(path.join(paquete, f), require('node:crypto').randomBytes(4096));
  fs.writeFileSync(path.join(paquete, 'datos/prueba/a.png'), require('node:crypto').randomBytes(2048));
  fs.writeFileSync(path.join(paquete, 'datos/prueba/sub/b.json'), '{"ok":true}\n');
  fs.writeFileSync(path.join(ws, 'fakeblender'), '#!/bin/bash\n[ "$1" = "--version" ] && { echo "Blender 5.2.3 LTS (simulado)"; exit 0; }\n' +
    'echo "args: $*"; mkdir -p datos/salida; echo render > datos/salida/resultado.txt; [ -n "${FALLAR:-}" ] && exit 7; exit 0\n', { mode: 0o755 });
  env = { ...process.env, ORA_VAST_LOCAL: '1', ORA_VAST_RAIZ_LOCAL: ws, VAST_ENV: '/dev/null', VAST_BLENDER: '/workspace/fakeblender',
          RESPALDO_MAC: path.join(raiz, 'respaldo'), ORA_ESTADO: path.join(raiz, 'estado'), ORA_REGISTRO: path.join(raiz, 'registro.md') };
});
afterEach(() => fs.rmSync(raiz, { recursive: true, force: true }));
const correr = (...args) => {
  const r = spawnSync('bash', [script, ...args], { env, encoding: 'utf8', cwd: repo });
  return { rc: r.status, out: (r.stdout || '') + (r.stderr || '') };
};

test('estado informa bloqueo libre y la versión de Blender', () => {
  const r = correr('estado');
  assert.equal(r.rc, 0, r.out); assert.match(r.out, /bloqueo: libre/); assert.match(r.out, /Blender 5\.2\.3/);
});

test('subir copia el código del commit a una carpeta inmutable y no la sobrescribe', { skip: !esRepoGit }, () => {
  const commit = execFileSync('git', ['rev-parse', '--short', 'HEAD'], { cwd: repo, encoding: 'utf8' }).trim();
  const limpio = spawnSync('git', ['diff', '--quiet', '--', 'blender/produccion'], { cwd: repo }).status === 0;
  const r = correr('subir');
  if (!limpio) { assert.notEqual(r.rc, 0); assert.match(r.out, /cambios sin commit/); return; }
  assert.equal(r.rc, 0, r.out);
  const dest = fs.readdirSync(path.join(paquete, '_codigo'))[0];
  assert.ok(dest.endsWith(commit), dest);
  assert.ok(fs.existsSync(path.join(paquete, '_codigo', dest, 'v4/v4_2.py')));
  const r2 = correr('subir'); assert.notEqual(r2.rc, 0); assert.match(r2.out, /inmutable/);
});

test('preflight detecta una escena protegida alterada', () => {
  assert.equal(correr('preflight').rc, 0);
  fs.appendFileSync(path.join(paquete, 'v4/escena_v4.blend'), 'x');
  const r = correr('preflight'); assert.equal(r.rc, 14, r.out); assert.match(r.out, /escena protegida cambió/);
});

test('ejecutar sin --confirmar solo muestra el plan y no ejecuta', () => {
  fs.mkdirSync(env.ORA_ESTADO, { recursive: true }); fs.writeFileSync(path.join(env.ORA_ESTADO, 'codigo_remoto'), '/workspace/codigo\n');
  const r = correr('ejecutar', '--agente', 'claude', '--escena', 'v4/escena_v4_1.blend', '--script', 'v4/v4_2.py', '--', 'prueba');
  assert.equal(r.rc, 0); assert.match(r.out, /PLAN \(sin --confirmar/);
  assert.ok(!fs.existsSync(path.join(paquete, 'datos/salida')));
});

test('ejecutar respeta el bloqueo de otro agente y lo libera tras ejecutar, incluso si Blender falla', () => {
  fs.mkdirSync(env.ORA_ESTADO, { recursive: true }); fs.writeFileSync(path.join(env.ORA_ESTADO, 'codigo_remoto'), '/workspace/codigo\n');
  const args = ['ejecutar', '--agente', 'claude', '--escena', 'v4/escena_v4_1.blend', '--script', 'v4/v4_2.py', '--confirmar', '--', 'prueba'];
  fs.mkdirSync(path.join(ws, 'ora.lock')); fs.writeFileSync(path.join(ws, 'ora.lock/info'), 'codex · otra tarea');
  let r = correr(...args); assert.equal(r.rc, 11, r.out); assert.match(r.out, /codex · otra tarea/);
  fs.rmSync(path.join(ws, 'ora.lock'), { recursive: true });
  r = correr(...args); assert.equal(r.rc, 0, r.out);
  assert.ok(!fs.existsSync(path.join(ws, 'ora.lock')), 'bloqueo liberado');
  assert.equal(fs.readFileSync(path.join(paquete, 'datos/salida/resultado.txt'), 'utf8'), 'render\n');
  const reg = fs.readdirSync(path.join(paquete, '_registros'))[0];
  assert.match(fs.readFileSync(path.join(paquete, '_registros', reg, 'resumen.txt'), 'utf8'), /rc=0 .*agente=claude/);
  env.FALLAR = '1'; r = correr(...args); assert.equal(r.rc, 7, r.out);
  assert.ok(!fs.existsSync(path.join(ws, 'ora.lock')), 'bloqueo liberado tras un fallo de Blender');
});

test('traer copia sin sobrescribir, verifica SHA-256 y rechaza rutas peligrosas', () => {
  let r = correr('traer', 'datos/prueba'); assert.equal(r.rc, 0, r.out); assert.match(r.out, /traído y verificado: 2 archivos/);
  const dest = fs.readFileSync(path.join(env.ORA_ESTADO, 'verificado'), 'utf8').trim();
  assert.equal(fs.readFileSync(path.join(dest, 'datos/prueba/sub/b.json'), 'utf8'), '{"ok":true}\n');
  assert.ok(fs.existsSync(path.join(dest, 'MANIFIESTO.sha256')));
  for (const malo of ['../../etc', '/etc/passwd']) { r = correr('traer', malo); assert.notEqual(r.rc, 0); assert.match(r.out, /ruta no permitida/); }
  assert.ok(fs.existsSync(path.join(env.ORA_ESTADO, 'verificado')), 'una ruta rechazada no invalida el respaldo verificado');
});

test('detener se niega sin respaldo verificado; cerrar trae, detiene y registra', () => {
  let r = correr('detener'); assert.notEqual(r.rc, 0); assert.match(r.out, /no hay respaldo verificado/);
  r = correr('cerrar', 'datos/prueba'); assert.equal(r.rc, 0, r.out);
  assert.match(r.out, /deteniendo \(no destruyendo\)/);
  const reg = fs.readFileSync(env.ORA_REGISTRO, 'utf8');
  assert.match(reg, /\| Fecha \(UTC\) \| Instancia \|/); assert.equal(reg.trim().split('\n').filter(l => l.startsWith('| 20')).length, 1);
});

test('--seco no ejecuta nada', () => {
  const r = correr('--seco', 'traer', 'datos/prueba'); assert.equal(r.rc, 0, r.out); assert.match(r.out, /\(seco\)/);
  assert.ok(!fs.existsSync(env.RESPALDO_MAC));
});
