# ORA · Apartamento 102 (PROPUESTA DE REDISTRIBUCIÓN, no planta verificada) · C4: iluminación V4.2 definitiva, vista c01.
# Fuente: v4/escena_v4_2_prueba3.blend (solo lectura) → copia v4/escena_v4_2_final.blend. Cambios: sol 3800 K y luz ambiental
# real 0,35 (módulo común comun/luz_v42.py); exposición calibrada solo en la vista. Nada más cambia.
#
#   prueba     : blender -b v4/escena_v4_2_prueba3.blend --python <ruta>/v4/v4_2_final.py -- prueba <png_960> <blend_copia> <json> [mascaras.npz]
#   final      : blender -b v4/escena_v4_2_final.blend   --python <ruta>/v4/v4_2_final.py -- final <png_1920> <json>
#   sin-render : blender -b v4/escena_v4_2_prueba3.blend --python <ruta>/v4/v4_2_final.py -- sin-render <blend_copia> <json>
#                (CPU, sin GPU: aplica y guarda la copia para verificarla; no renderiza)
import bpy, sys, os, json, time, math
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from comun import luz_v42

a = sys.argv[sys.argv.index('--') + 1:]; MODO = a[0]
sc = bpy.context.scene; vs = sc.view_settings; c = sc.cycles
reg = {'modo': MODO, 'cambios': []}
def cambio(p, x, y): reg['cambios'].append({'parametro': p, 'antes': x, 'despues': y}); print('[c4] CAMBIO', p, ':', x, '→', y)
def r3(v): return round(float(v), 3)

def dispositivo():
    cp = bpy.context.preferences.addons['cycles'].preferences; cp.compute_device_type = 'OPTIX'; cp.refresh_devices()
    for dv in cp.devices: dv.use = dv.type == 'OPTIX'
    gpus = [dv.name for dv in cp.devices if dv.use]
    if not gpus: raise SystemExit('[c4] ERROR: no hay dispositivo OptiX (este modo necesita la GPU)')
    sc.render.engine = 'CYCLES'; c.device = 'GPU'; c.denoiser = 'OPTIX'; c.use_denoising = True; c.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'; sc.render.image_settings.color_depth = '8'
    return gpus

def medir():
    p = '/tmp/ora_c4_eval.png'; bpy.data.images['Render Result'].save_render(p, scene=sc)
    im = bpy.data.images.load(p, check_existing=False); px = np.array(im.pixels[:], np.float32).reshape(-1, 4)[:, :3]; bpy.data.images.remove(im)
    l = px @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    return {'p5': r3(np.percentile(l, 5)), 'p50': r3(np.median(l)), 'p95': r3(np.percentile(l, 95)), 'quemado_%': r3((px.max(1) > 0.98).mean() * 100)}

if MODO in ('prueba', 'sin-render'):
    COPIA, JS = (a[2], a[3]) if MODO == 'prueba' else (a[1], a[2])
    exp0 = r3(vs.exposure)
    reg['luz'] = luz_v42.aplicar(sc, cambio)
    reg['verificacion'] = luz_v42.verificar(sc)          # explícita: falla si cualquier parámetro no coincide
    for f in reg['verificacion']: print('[c4] VERIFICADO', f['parametro'], '=', f['actual'])
    if MODO == 'prueba':
        PNG = a[1]; reg['gpu'] = dispositivo()
        sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 960, 540, 100
        c.samples = 256; c.use_adaptive_sampling = True; c.adaptive_threshold = 0.01
        t = time.time(); bpy.ops.render.render(write_still=False); reg['segundos_prueba'] = round(time.time() - t, 1)
        reg['exposicion_evaluada'] = luz_v42.calibrar_exposicion(sc, medir, inicio=exp0)
        cambio('exposición (EV), solo vista', exp0, r3(vs.exposure))
        m = medir(); reg['medidas'] = m
        reg['cumple_sombras_p5'] = luz_v42.OBJETIVO['p5'][0] <= m['p5'] <= luz_v42.OBJETIVO['p5'][1]
        bpy.data.images['Render Result'].save_render(PNG, scene=sc); reg['png'] = PNG
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, 100
    os.makedirs(os.path.dirname(os.path.abspath(COPIA)), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=COPIA, copy=True, compress=True); reg['blend'] = COPIA
elif MODO == 'final':
    PNG, JS = a[1], a[2]
    try: reg['verificacion'] = luz_v42.verificar(sc)   # la copia debe tener la luz V4.2 definitiva antes de gastar GPU
    except RuntimeError as e: raise SystemExit(f'[c4] ERROR: {e} (abra v4/escena_v4_2_final.blend)')
    reg['gpu'] = dispositivo()
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, 100
    c.samples = 1024; c.use_adaptive_sampling = True; c.adaptive_threshold = 0.006; c.adaptive_min_samples = 64
    sc.render.filepath = PNG; t = time.time(); bpy.ops.render.render(write_still=True); reg['segundos_final'] = round(time.time() - t, 1); reg['png'] = PNG
else:
    raise SystemExit(f'[c4] modo desconocido: {MODO}')
json.dump(reg, open(JS, 'w'), indent=1, ensure_ascii=False, default=str)
print('C4_OK', MODO)
