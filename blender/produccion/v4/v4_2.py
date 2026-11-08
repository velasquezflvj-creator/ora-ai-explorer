# ORA · Apartamento 102 (PROPUESTA DE REDISTRIBUCIÓN) · V4.2: solo iluminación (defecto 1).
#   prueba: blender -b v4/escena_v4_1.blend --python v4/v4_2.py -- prueba <png_prueba> <blend_v4_2> <json>
#   final : blender -b v4/escena_v4_2.blend --python v4/v4_2.py -- final <png_final> <json>
# Cambios: Sol_HDRI existente activado (18° de elevación, entra perpendicular por la puerta-ventana de la sala; verificado
# por trazado de rayos que no cruza sólidos), cielo 1,6 → 1,2, exposición hacia +2,0 EV. Focos, materiales y AgX sin cambio.
import bpy, sys, json, math, time
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
MODO = a[0]
sc = bpy.context.scene; vs = sc.view_settings; c = sc.cycles
cp = bpy.context.preferences.addons['cycles'].preferences; cp.compute_device_type = 'OPTIX'; cp.refresh_devices()
for dv in cp.devices: dv.use = dv.type == 'OPTIX'
gpus = [dv.name for dv in cp.devices if dv.use]; assert gpus
sc.render.engine = 'CYCLES'; c.device = 'GPU'; c.denoiser = 'OPTIX'; c.use_denoising = True; c.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'; sc.render.image_settings.color_depth = '8'

if MODO == 'prueba':
    PNG, BLEND, JS = a[1:4]; reg = {'cambios': []}
    def cambio(p, x, y): reg['cambios'].append({'parametro': p, 'antes': x, 'despues': y}); print('[v4.2] CAMBIO', p, x, '→', y)
    sol = sc.objects['Sol_HDRI']; elev, az = math.radians(18), math.radians(90)
    dl = Vector((math.cos(az) * math.cos(elev), math.sin(az) * math.cos(elev), -math.sin(elev)))
    rot0 = [round(math.degrees(v), 1) for v in sol.rotation_euler]
    sol.rotation_euler = dl.to_track_quat('-Z', 'Y').to_euler()
    cambio('Sol_HDRI: visible en render', 'no (hide_render)', 'sí'); sol.hide_render = False
    cambio('Sol_HDRI: rotación (°)', rot0, [round(math.degrees(v), 1) for v in sol.rotation_euler])
    cambio('Sol_HDRI: dirección', 'elevación 10,4°, azimut 144° (solo rozaba cuadro y muro)', 'elevación 18°, entra perpendicular a la fachada por la puerta-ventana de la sala')
    print('[v4.2] Sol_HDRI conservado: energía', sol.data.energy, 'ángulo', round(math.degrees(sol.data.angle), 2), 'color', [round(x, 2) for x in sol.data.color])
    fb = sc.world.node_tree.nodes['Fondo.001']; cambio('cielo (rama de iluminación Fondo.001)', round(fb.inputs['Strength'].default_value, 3), 1.2); fb.inputs['Strength'].default_value = 1.2
    focos = {(round(o.data.energy, 2), o.data.temperature) for o in sc.objects if o.type == 'LIGHT' and o.data.type == 'SPOT' and o.name.startswith('Luz_')}
    print('[v4.2] 16 focos sin cambio:', focos, '· vista', vs.view_transform, vs.look, '· WB', round(vs.white_balance_temperature), 'K')
    exp0 = round(vs.exposure, 3)
    # prueba única de baja resolución
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 960, 540, 100
    c.samples = 256; c.use_adaptive_sampling = True; c.adaptive_threshold = 0.01
    t = time.time(); bpy.ops.render.render(write_still=False); reg['segundos_prueba'] = round(time.time() - t, 1)
    def medir(e):
        vs.exposure = e; p = '/tmp/ora_v42_eval.png'; bpy.data.images['Render Result'].save_render(p, scene=sc)
        im = bpy.data.images.load(p, check_existing=False); px = np.array(im.pixels[:], dtype=np.float32).reshape(-1, 4)[:, :3]; bpy.data.images.remove(im)
        l = px @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
        return {'exp': round(e, 3), 'quemado_%': round(float((px.max(1) > 0.98).mean() * 100), 3), 'p99_5': round(float(np.percentile(l, 99.5)), 3),
                'p5': round(float(np.percentile(l, 5)), 3), 'p50': round(float(np.median(l)), 3), 'negro_%': round(float((l < 0.03).mean() * 100), 3)}
    # exposición: +2,0 salvo que los blancos pierdan detalle (quemado > 0,6 %): entonces se baja de 0,05 en 0,05 (solo vista)
    ev = [medir(x) for x in (2.447, 2.2, 2.0, 1.9, 1.8)]; reg['evaluacion_exposicion'] = ev
    for r in ev: print('[v4.2] EXPOSICION', r)
    e = 2.0
    while medir(e)['quemado_%'] > 0.6 and e > 1.6: e = round(e - 0.05, 3)
    vs.exposure = e; cambio('exposición (EV)', exp0, e)
    bpy.data.images['Render Result'].save_render(PNG, scene=sc)
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    bpy.ops.wm.save_as_mainfile(filepath=BLEND, copy=True, compress=True)
    reg.update({'prueba_png': PNG, 'blend': BLEND, 'gpu': gpus}); json.dump(reg, open(JS, 'w'), indent=1, ensure_ascii=False)
    print('V42_PRUEBA_OK', reg['segundos_prueba'])
else:
    PNG, JS = a[1:3]; reg = json.load(open(JS))
    assert not sc.objects['Sol_HDRI'].hide_render and abs(sc.world.node_tree.nodes['Fondo.001'].inputs['Strength'].default_value - 1.2) < 1e-6
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, 100
    c.samples = 1024; c.use_adaptive_sampling = True; c.adaptive_threshold = 0.006; c.adaptive_min_samples = 64
    sc.render.filepath = PNG; t = time.time(); bpy.ops.render.render(write_still=True); reg['segundos_final'] = round(time.time() - t, 1)
    reg['final_png'] = PNG; json.dump(reg, open(JS, 'w'), indent=1, ensure_ascii=False)
    print('V42_FINAL_OK', reg['segundos_final'])
