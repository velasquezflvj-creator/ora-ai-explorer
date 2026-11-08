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
// ORA_SIN_BLENDER_LOCAL=1 omite las pruebas que abren Blender en el Mac (p. ej. mientras la GPU remota trabaja)
const blenderLocal = !process.env.ORA_SIN_BLENDER_LOCAL && fs.existsSync(blender);
const hayBlender = blenderLocal && fs.existsSync(escenaV1);
const escenaP3 = path.join(respaldo, 'v4/escena_v4_2_prueba3.blend');

test('C3 y C4 usan el mismo módulo de luz V4.2 definitiva', () => {
  const c4 = fs.readFileSync(path.join(prod, 'v4/v4_2_final.py'), 'utf8');
  const c3 = fs.readFileSync(v2, 'utf8');
  for (const [n, s] of [['v4_2_final.py', c4], ['rediseno_sala_v2', c3]]) {
    assert.match(s, /from comun import luz_v42/, `${n} importa comun/luz_v42.py`);
    assert.match(s, /luz_v42\.aplicar\(sc/, `${n} aplica la luz común`);
  }
  assert.match(c3, /--sin-render/); assert.match(c4, /sin-render/);
  const luz = fs.readFileSync(path.join(prod, 'comun/luz_v42.py'), 'utf8');
  assert.match(luz, /SOL_K = 3800\.0/); assert.match(luz, /FONDO_LUZ = 0\.35/);
});

test('C4: la luz V4.2 definitiva se aplica en CPU sin render y la escena fuente no cambia', { skip: !(blenderLocal && fs.existsSync(escenaP3)) && 'sin Blender local o sin respaldo' }, () => {
  const antes = sha(escenaP3); const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'ora-c4-'));
  try {
    const copia = path.join(tmp, 'escena_v4_2_final.blend');
    let r = spawnSync(blender, ['-b', '--factory-startup', escenaP3, '--python', path.join(prod, 'v4/v4_2_final.py'), '--', 'sin-render', copia, path.join(tmp, 'c4.json')], { encoding: 'utf8', timeout: 240000 });
    assert.match(r.stdout || '', /C4_OK sin-render/, r.stderr);
    const ver = path.join(tmp, 'ver.py');
    fs.writeFileSync(ver, `import bpy, json\nsc = bpy.context.scene; d = sc.objects['Sol_HDRI'].data\nprint('VER' + json.dumps({'k': d.use_temperature and d.temperature, 'oculto': sc.objects['Sol_HDRI'].hide_render, 'fondo': round(sc.world.node_tree.nodes['Fondo'].inputs['Strength'].default_value, 4), 'focos': sorted({(round(o.data.energy, 2), o.data.temperature) for o in sc.objects if o.type == 'LIGHT' and o.data.type == 'SPOT' and o.name.startswith('Luz_')}), 'wb': sc.view_settings.white_balance_temperature, 'look': sc.view_settings.look}))\n`);
    r = spawnSync(blender, ['-b', '--factory-startup', copia, '--python', ver], { encoding: 'utf8', timeout: 240000 });
    const v = JSON.parse((r.stdout || '').split('\n').find(l => l.startsWith('VER')).slice(3));
    assert.equal(v.k, 3800); assert.equal(v.oculto, false); assert.equal(v.fondo, 0.35);
    assert.deepEqual(v.focos, [[9, 3600]]); assert.equal(v.wb, 4600); assert.equal(v.look, 'AgX - Medium High Contrast');
    // verificación explícita registrada en el JSON: 10 parámetros, todos correctos
    const js = JSON.parse(fs.readFileSync(path.join(tmp, 'c4.json'), 'utf8'));
    assert.equal(js.verificacion.length, 10); assert.ok(js.verificacion.every(f => f.ok), JSON.stringify(js.verificacion));
    // control negativo: sobre la escena de la prueba 3 (sin cambios) la verificación debe fallar
    const neg = path.join(tmp, 'neg.py');
    fs.writeFileSync(neg, `import bpy, sys\nsys.path.insert(0, ${JSON.stringify(prod)})\nfrom comun import luz_v42\ntry:\n    luz_v42.verificar(bpy.context.scene); print('NEG_PASA')\nexcept RuntimeError as e:\n    print('NEG_FALLA', e)\n`);
    r = spawnSync(blender, ['-b', '--factory-startup', escenaP3, '--python', neg], { encoding: 'utf8', timeout: 240000 });
    assert.match(r.stdout || '', /NEG_FALLA .*temperatura \(K\).*Fondo/s, (r.stdout || '') + r.stderr);
    // modo final sobre una escena sin la luz definitiva: se niega antes de tocar la GPU
    r = spawnSync(blender, ['-b', '--factory-startup', escenaP3, '--python', path.join(prod, 'v4/v4_2_final.py'), '--', 'final', path.join(tmp, 'x.png'), path.join(tmp, 'x.json')], { encoding: 'utf8', timeout: 240000 });
    assert.match((r.stdout || '') + r.stderr, /\[c4\] ERROR: luz V4\.2 no verificada/); assert.ok(!fs.existsSync(path.join(tmp, 'x.png')));
  } finally { fs.rmSync(tmp, { recursive: true, force: true }); }
  assert.equal(sha(escenaP3), antes, 'escena_v4_2_prueba3 del respaldo intacta');
});
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
