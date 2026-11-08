# ORA · Apartamento 102 (PROPUESTA DE REDISTRIBUCIÓN) · V4.1 según orden de ejecución.
# Fuente: v4/escena_v4.blend (solo lectura). Cambios: balance de blancos (4600 K inicial), exposición evaluada, travertino
# mineral (mismo tratamiento que ya usa el piso). Iluminación V4 conservada. Máximo 3 pruebas pequeñas. Una imagen final.
#   blender -b v4/escena_v4.blend --python v4/v4_1_final.py -- <control.json> <mascaras.npz> <png> <blend_copia>
import bpy, json, sys, os, time, math, colorsys
import numpy as np
from mathutils import Matrix

CONTROL, MASCARAS, SALIDA, COPIA = sys.argv[sys.argv.index('--') + 1:][:4]
sc = bpy.context.scene; vs = sc.view_settings; c = sc.cycles
reg = {'parametros': [], 'pruebas': []}
def cambio(param, antes, despues):
    reg['parametros'].append({'parametro': param, 'antes': antes, 'despues': despues}); print('[v4.1] CAMBIO', param, ':', antes, '→', despues)
def hexa(rgb): return '#' + ''.join(f'{int(round(max(0, min(1, float(v))) * 255)):02X}' for v in rgb)
r3 = lambda v: round(float(v), 3)

# ---------- cámara: igual a la vista de control
ctl = json.load(open(CONTROL)); fr = next(f for f in ctl['frames'] if f['id'] == 'c01_sala_sofa')
M = Matrix(fr['transform_matrix']); cam = sc.camera
assert max(abs(cam.matrix_world[i][j] - M[i][j]) for i in range(4) for j in range(4)) < 1e-4 and abs(cam.data.angle - ctl['camera_angle_x']) < 1e-6

# ---------- iluminación V4: se verifica y se conserva (no se modifica)
focos = {(round(o.data.energy, 2), o.data.temperature) for o in sc.objects if o.type == 'LIGHT' and o.data.type == 'SPOT' and o.name.startswith('Luz_')}
print('[v4.1] iluminación V4 conservada: focos', focos, '· cielo', r3(sc.world.node_tree.nodes['Fondo.001'].inputs['Strength'].default_value))

# ---------- C. travertino: vetas minerales (mismo tratamiento que ya tiene piso_madera: saturación y suavizado de veta)
for mn in ('salpicadero', 'meson', 'alfeizar'):
    m = bpy.data.materials.get(mn)
    if not m: continue
    nt = m.node_tree; img = nt.nodes['Imagen']; mez = nt.nodes['Mezclar']
    assert mez.inputs['A'].links[0].from_node == img
    hs = nt.nodes.new('ShaderNodeHueSaturation'); hs.name = 'mineral_saturacion'
    hs.inputs['Saturation'].default_value = 0.5; hs.inputs['Value'].default_value = 1.05
    sv = nt.nodes.new('ShaderNodeMix'); sv.name = 'suavizar_veta'; sv.data_type = 'RGBA'; sv.blend_type = 'MIX'
    sv.inputs['Factor'].default_value = 0.35; sv.inputs['B'].default_value = (0.70, 0.665, 0.61, 1)
    nt.links.new(img.outputs['Color'], hs.inputs['Color']); nt.links.new(hs.outputs['Color'], sv.inputs['A']); nt.links.new(sv.outputs['Result'], mez.inputs['A'])
    nm = nt.nodes['Mapa de normales']; a0 = r3(nm.inputs['Strength'].default_value); nm.inputs['Strength'].default_value = 0.35
    cambio(f'{mn}: saturación de la textura de travertino', 1.0, 0.5)
    cambio(f'{mn}: contraste de veta (mezcla hacia tono piedra #D9D3C9 lineal 0.70/0.665/0.61)', 0.0, 0.35)
    cambio(f'{mn}: valor de la textura', 1.0, 1.05)
    cambio(f'{mn}: relieve de poros (Normal Map Strength)', a0, 0.35)

# ---------- dispositivo
cp = bpy.context.preferences.addons['cycles'].preferences; cp.compute_device_type = 'OPTIX'; cp.refresh_devices()
for dv in cp.devices: dv.use = dv.type == 'OPTIX'
gpus = [dv.name for dv in cp.devices if dv.use]; assert gpus
sc.render.engine = 'CYCLES'; c.device = 'GPU'; c.denoiser = 'OPTIX'; c.use_denoising = True; c.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
sc.render.use_persistent_data = True
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'; sc.render.image_settings.color_depth = '8'

# ---------- A. balance de blancos: 4600 K inicial; D. AgX conservado
look0 = vs.look; assert vs.view_transform == 'AgX'
cambio('balance de blancos (temperatura)', r3(vs.white_balance_temperature), 4600.0); vs.white_balance_temperature = 4600.0
t0_tinte = r3(vs.white_balance_tint)

MASK = dict(np.load(MASCARAS))
EMIS = None
def prueba(nombre, muestras=128):
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 480, 270, 100
    c.samples = muestras; c.use_adaptive_sampling = True; c.adaptive_threshold = 0.01
    t = time.time(); bpy.ops.render.render(write_still=False); reg['pruebas'].append({'prueba': nombre, 'segundos': round(time.time() - t, 1)})
def medir():
    p = '/tmp/ora_v41f_eval.png'; bpy.data.images['Render Result'].save_render(p, scene=sc)
    im = bpy.data.images.load(p, check_existing=False); px = np.array(im.pixels[:], dtype=np.float32).reshape(-1, 4)[:, :3]; bpy.data.images.remove(im)
    luma = px @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32); out = {}
    for g, mk in MASK.items():
        l = luma[mk]; lo, hi = np.percentile(l, 85), np.percentile(l, 97)
        out[g] = px[mk][(l >= lo) & (l <= hi)].mean(0); out[g + '_med'] = np.median(px[mk], 0)
    sup = MASK['muro'] | MASK['cielo'] | MASK['sofa'] | MASK['madera']   # superficies (excluye emisores)
    out['quemado_sup_%'] = float((px[sup].max(1) > 0.98).mean() * 100); out['quemado_total_%'] = float((px.max(1) > 0.98).mean() * 100)
    out['negro_empastado_%'] = float((luma < 0.02).mean() * 100); out['mediana_luma'] = float(np.median(luma))
    out['p5_luma'] = float(np.percentile(luma, 5)); out['p95_luma'] = float(np.percentile(luma, 95))
    return out
def informe(et):
    m = medir(); f = {'etapa': et, 'exposicion': r3(vs.exposure), 'wb_K': round(vs.white_balance_temperature), 'tinte': r3(vs.white_balance_tint)}
    for k in ('mediana_luma', 'p5_luma', 'p95_luma', 'quemado_sup_%', 'quemado_total_%', 'negro_empastado_%'): f[k] = r3(m[k])
    for g in ('muro', 'cielo', 'sofa', 'madera'):
        h, s, v = colorsys.rgb_to_hsv(*m[g + '_med']); f[g] = hexa(m[g]); f[g + '_mediana'] = hexa(m[g + '_med']); f[g + '_tono°'] = round(h * 360); f[g + '_sat'] = r3(s)
    rw = m['muro'] * 255; f['muro_R-B'] = r3(rw[0] - rw[2]); f['muro_G-(R+B)/2'] = r3(rw[1] - (rw[0] + rw[2]) / 2)
    reg['pruebas'][-1].setdefault('medidas', []).append(f); print('[v4.1] MEDIDA', json.dumps(f, ensure_ascii=False)); return m, f

# criterios de evaluación (fotografía inmobiliaria: blanco roto natural, sin lila ni amarillo; no lavada; detalle en blancos/sombras)
def neutros_ok(f):  # muro iluminado: ligeramente cálido (R−B entre +5 y +14 de 255), sin tinte verde/magenta; sofá beige (tono 25–45°)
    return 5 <= f['muro_R-B'] <= 14 and abs(f['muro_G-(R+B)/2']) <= 2.5 and 25 <= f['sofa_tono°'] <= 45
def ajustar_exposicion():
    """Muro iluminado ≈ 0,80 de luminancia (blanco roto luminoso sin quemar), y después se impone: mediana ≤ 0,56
    (no lavada) y superficies quemadas ≤ 0,5 %. Solo transformación de vista: no requiere renders adicionales."""
    Y = np.array([0.2126, 0.7152, 0.0722])
    for _ in range(10):
        lw = float(medir()['muro'] @ Y); paso = 1.2 * math.log2(0.80 / max(lw, 1e-3))
        if abs(paso) < 0.02: break
        vs.exposure = float(np.clip(vs.exposure + paso, 0.5, 4.0))
    for _ in range(20):
        m = medir()
        if m['mediana_luma'] <= 0.56 and m['quemado_sup_%'] <= 0.5: break
        vs.exposure -= 0.08
def ajustar_wb(f):
    """Solo si los neutros fallan: temperatura para R−B (objetivo +9); tinte (±12) por búsqueda para el eje verde–magenta."""
    for _ in range(10):
        if neutros_ok(f): break
        e_rb = f['muro_R-B'] - 9.0
        if not (5 <= f['muro_R-B'] <= 14): vs.white_balance_temperature = float(np.clip(vs.white_balance_temperature - 18 * e_rb, 3800, 6500))
        if abs(f['muro_G-(R+B)/2']) > 2.5:
            t0 = vs.white_balance_tint; mejor = (abs(f['muro_G-(R+B)/2']), t0)
            for d in (-3, 3):
                vs.white_balance_tint = float(np.clip(t0 + d, -12, 12)); m = medir(); rw = m['muro'] * 255
                mejor = min(mejor, (abs(rw[1] - (rw[0] + rw[2]) / 2), vs.white_balance_tint))
            vs.white_balance_tint = mejor[1]
        _, f = informe('ajuste WB (vista)')
    return f

# ---------- prueba 1: estado V4 + travertino + WB 4600 K, a la exposición V4
exp_v4 = r3(vs.exposure)
prueba('1: V4 + travertino + 4600 K')
_, f = informe('4600 K, exposición V4 +1,93')
f = ajustar_wb(f)
ajustar_exposicion(); _, f = informe('exposición evaluada')
f = ajustar_wb(f)
# ---------- prueba 2: confirmación con más muestras a los valores elegidos (verifica ruido/medidas)
prueba('2: confirmación', 256); _, f = informe('confirmación')
if not neutros_ok(f) or f['mediana_luma'] > 0.58 or f['quemado_sup_%'] > 0.8:
    f = ajustar_wb(f); ajustar_exposicion(); prueba('3: verificación final', 256); _, f = informe('verificación')
cambio('exposición (EV)', exp_v4, r3(vs.exposure))
if r3(vs.white_balance_temperature) != 4600.0: cambio('balance de blancos (temperatura) tras evaluación de neutros', 4600.0, r3(vs.white_balance_temperature))
if r3(vs.white_balance_tint) != t0_tinte: cambio('balance de blancos (tinte)', t0_tinte, r3(vs.white_balance_tint))
reg['vista'] = {'transformacion': vs.view_transform, 'look': vs.look, 'look_V4': look0}

# ---------- copia independiente y render final
bpy.ops.wm.save_as_mainfile(filepath=COPIA, copy=True, compress=True)
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
c.samples = 1024; c.adaptive_threshold = 0.006; c.adaptive_min_samples = 64
cambio('render: resolución / muestras máx. / umbral adaptativo', '1920×1080 / 1024 / 0,008 (V4)', '1920×1080 / 1024 / 0,006')
sc.render.filepath = SALIDA; t = time.time(); bpy.ops.render.render(write_still=True); dt = round(time.time() - t, 1)
reg.update({'segundos_render_final': dt, 'gpu': gpus, 'salida': SALIDA, 'copia': COPIA, 'pruebas_pequenas': len(reg['pruebas'])})
json.dump(reg, open(os.path.splitext(SALIDA)[0] + '_parametros.json', 'w'), indent=1, ensure_ascii=False, default=float)
print('V41F_OK', dt, 'pruebas', len(reg['pruebas']))
