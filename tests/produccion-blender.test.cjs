// Scripts de producción de Blender (blender/produccion): comprobaciones sin GPU, sin render y sin simulación.
// Estáticas (siempre): sintaxis Python, guardado solo como copia, ningún maestro como destino, identidad con el respaldo de
// la instancia Vast (manifiesto SHA-256). Con Blender 5.2.3 local y el respaldo en el Mac: verificación previa del script V2
// del rediseño de sala contra la escena v1 (referencias, anillos de costura y generación de la obra a 1/5).
// Apartamento 102: propuesta de redistribución conceptual (no planta verificada).
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');
const { spawnSync } = require('node:child_process');

const repo = path.resolve(__dirname, '..');
const prod = path.join(repo, 'blender/produccion');
const blender = process.env.BLENDER || '/Volumes/Blender/Blender.app/Contents/MacOS/Blender';
const respaldo = process.env.ORA_RESPALDO_VAST || path.join(os.homedir(), 'Downloads/ora-vast-respaldo-C59621459-2026-11-08/workspace/ora_restore_4080/proyecto_ora/paquete');
const escenaV1 = path.join(respaldo, 'rediseno_sala/escena_sala_rediseno_v1.blend');
const v2 = path.join(prod, 'rediseno_sala/rediseno_sala_v2_no_ejecutado.py');
const hayBlender = fs.existsSync(blender) && fs.existsSync(escenaV1);
const scripts = (d => { const out = []; const rec = p => fs.readdirSync(p, { withFileTypes: true }).forEach(e =>
  e.isDirectory() ? rec(path.join(p, e.name)) : e.name.endsWith('.py') && out.push(path.join(p, e.name))); rec(d); return out; })(prod);
const sha = f => crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex');

test('todos los scripts de producción son Python válido', () => {
  assert.ok(scripts.length >= 19, `${scripts.length} scripts`);
  const r = spawnSync('python3', ['-c', 'import ast,sys\nfor f in sys.argv[1:]: ast.parse(open(f,encoding="utf-8").read(), f)', ...scripts], { encoding: 'utf8' });
  assert.equal(r.status, 0, r.stderr);
});

test('los scripts solo guardan copias y nunca escriben un archivo maestro', () => {
  for (const f of scripts) {
    const s = fs.readFileSync(f, 'utf8'); const rel = path.relative(repo, f);
    assert.ok(!/save_mainfile\s*\(/.test(s), `${rel}: save_mainfile sobre la escena abierta`);
    for (const m of s.matchAll(/save_as_mainfile\(([^)]*)\)/g)) assert.match(m[1], /copy\s*=\s*True/, `${rel}: save_as_mainfile sin copy=True`);
    assert.ok(!/Apartamento_102_(Render_Master|Render_V3|Video)\.blend/.test(s), `${rel}: menciona un .blend maestro`);
  }
});

test('los scripts ejecutados son idénticos a los del respaldo verificado de la instancia', () => {
  const man = fs.readFileSync(path.join(prod, 'manifiestos/respaldo_C59621459_paquete.sha256'), 'utf8').trim().split('\n')
    .map(l => l.split(/\s+/)).reduce((a, [h, p]) => (a[p.replace(/^paquete\//, '')] = h, a), {});
  assert.equal(Object.keys(man).length, 186);
  const pares = [['v4/v4_fotorrealista.py', 'v4/v4_fotorrealista.py'], ['v4/v4_1_calibracion.py', 'v4/v4_1_calibracion.py'], ['v4/v4_1_final.py', 'v4/v4_1_final.py'],
    ['v4/v4_2.py', 'v4/v4_2.py'], ['v4/v4_2_prueba2.py', 'v4/v4_2_prueba2.py'], ['v4/v4_2_prueba3.py', 'v4/v4_2_prueba3.py'], ['rediseno_sala/rediseno_sala_v1.py', 'rediseno_sala/rediseno_sala.py']];
  for (const [local, remoto] of pares) assert.equal(sha(path.join(prod, local)), man[remoto], `${local} ≠ respaldo`);
});

test('V2 de la sala: referencias, costuras y obra verificadas contra la escena v1 (CPU, solo lectura)', { skip: !hayBlender && 'sin Blender local o sin respaldo' }, () => {
  const antes = sha(escenaV1);
  const corre = (script, ...args) => spawnSync(blender, ['-b', '--factory-startup', escenaV1, '--python', path.join(prod, 'herramientas', script), '--', ...args],
    { encoding: 'utf8', timeout: 240000, maxBuffer: 64 * 1024 * 1024 });
  const json = (r, marca) => { const l = (r.stdout || '').split('\n').find(x => x.startsWith(marca)); assert.ok(l, (r.stdout || '') + r.stderr); return JSON.parse(l.slice(marca.length)); };
  const ref = json(corre('verificar_referencias_sala_v2.py'), 'VERIF');
  assert.deepEqual(ref.fallos, []);
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'ora-sala-v2-'));
  try {
    const seco = json(corre('prueba_seco_sala_v2.py', v2, tmp), 'SECO');
    for (const [cojin, anillos] of Object.entries(seco.anillos_por_cojin)) {
      assert.ok(anillos.length >= 1, `${cojin}: sin costura`);
      for (const a of anillos) { assert.ok(a.tramo_max_mm < 60, `${cojin}: vivo discontinuo (${a.tramo_max_mm} mm)`); assert.ok(a.perimetro_m > 1.0, `${cojin}: perímetro ${a.perimetro_m}`); }
    }
    assert.equal(seco.obra.nan, false);
    assert.ok(seco.obra.color_min_max[0] >= 0 && seco.obra.color_min_max[1] <= 1);
    assert.deepEqual(seco.obra.altura_min_max, [0, 1]);
    assert.ok(seco.obra.fraccion_negro > 0.2 && seco.obra.fraccion_negro < 0.5);
    assert.ok(seco.obra.fraccion_oro_metal > 0.005 && seco.obra.fraccion_oro_metal < 0.1);
  } finally { fs.rmSync(tmp, { recursive: true, force: true }); }
  assert.equal(sha(escenaV1), antes, 'la escena v1 del respaldo no cambia');
});
