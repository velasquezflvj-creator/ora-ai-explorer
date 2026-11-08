# ORA · Apartamento 102 (PROPUESTA) · V4.2 prueba 2. ÚNICO cambio: cielo (Fondo.001) 1,2 → 0,8.
# Fuente: v4/escena_v4_2.blend (no se escribe). Guarda copia nueva y una sola imagen 960×540 a exposición +2,0 exacta.
#   blender -b v4/escena_v4_2.blend --python v4/v4_2_prueba2.py -- <png> <blend_copia> <json> <mascaras.npz>
import bpy, sys, json, math, time
import numpy as np
from mathutils import Vector
PNG, BLEND, JS, MASC = sys.argv[sys.argv.index('--') + 1:][:4]
sc = bpy.context.scene; vs = sc.view_settings; c = sc.cycles; dg = bpy.context.evaluated_depsgraph_get()
sol = sc.objects['Sol_HDRI']; dl = (sol.rotation_euler.to_matrix() @ Vector((0, 0, -1))).normalized()
elev = round(math.degrees(math.asin(-dl.z)), 2); az = round(math.degrees(math.atan2(dl.y, dl.x)), 2)
fb = sc.world.node_tree.nodes['Fondo.001']
# comprobaciones: todo igual a la prueba 1 salvo el cielo
assert not sol.hide_render and abs(elev - 18) < 0.01 and abs(az - 90) < 0.01, (elev, az)
assert abs(vs.exposure - 2.0) < 1e-6 and abs(vs.white_balance_temperature - 4600) < 1e-3 and vs.view_transform == 'AgX'
assert abs(fb.inputs['Strength'].default_value - 1.2) < 1e-6
focos = {(round(o.data.energy, 2), o.data.temperature) for o in sc.objects if o.type == 'LIGHT' and o.data.type == 'SPOT' and o.name.startswith('Luz_')}
assert focos == {(9.0, 3600.0)}
fb.inputs['Strength'].default_value = 0.8
reg = {'cambio_unico': {'parametro': 'cielo (Fondo.001 Strength)', 'antes': 1.2, 'despues': 0.8},
       'sin_cambio': {'exposicion': vs.exposure, 'wb_K': vs.white_balance_temperature, 'look': vs.look, 'sol': {'elev': elev, 'az': az, 'energia': sol.data.energy}, 'focos': list(map(list, focos))}}
print('[v4.2b] CAMBIO cielo 1.2 → 0.8 · exposición', vs.exposure, '· sol', elev, az)
# sol directo sobre el sofá (píxel a píxel con la máscara del sofá, 480×270): ¿qué fracción del sofá visible recibe sol?
M = dict(np.load(MASC)); cam = sc.camera; fr = cam.data.view_frame(scene=sc)
tl, tr, br, bl = [cam.matrix_world @ v for v in (fr[0], fr[3], fr[2], fr[1])]; o = cam.matrix_world.translation
def mat_de(ob, i):
    try: return ob.material_slots[ob.data.polygons[i].material_index].material.name
    except Exception: return '?'
def al_sol(loc, nor):
    h = -dl
    if nor.dot(h) <= 0: return False
    p = loc + nor * 1e-3
    for _ in range(12):
        ok, l2, n2, i2, ob, _ = sc.ray_cast(dg, p, h)
        if not ok: return True
        if 'vidrio' in mat_de(ob, i2): p = l2 + h * 1e-3; continue
        return False
    return False
sofa = M['sofa'].reshape(270, 480); tot = sol_sofa = 0; filas = []
for j, i in zip(*np.nonzero(sofa)):
    jj = 269 - j   # las máscaras están en orden de píxeles de Blender (abajo→arriba)
    p = tl + (tr - tl) * ((i + .5) / 480) + (bl - tl) * ((jj + .5) / 270); ok, loc, nor, idx, ob, _ = sc.ray_cast(dg, o, (p - o).normalized())
    if not ok: continue
    tot += 1
    if al_sol(loc, nor): sol_sofa += 1; filas.append(round(loc.z, 2))
reg['sofa_al_sol'] = {'pixeles_sofa': tot, 'con_sol_directo': sol_sofa, 'porcentaje': round(100 * sol_sofa / max(tot, 1), 2),
                      'altura_z_m': [min(filas), max(filas)] if filas else None}
print('[v4.2b] SOFA_SOL', reg['sofa_al_sol'])
# render de prueba único
cp = bpy.context.preferences.addons['cycles'].preferences; cp.compute_device_type = 'OPTIX'; cp.refresh_devices()
for dv in cp.devices: dv.use = dv.type == 'OPTIX'
sc.render.engine = 'CYCLES'; c.device = 'GPU'; c.denoiser = 'OPTIX'; c.use_denoising = True; c.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 960, 540, 100
c.samples = 256; c.use_adaptive_sampling = True; c.adaptive_threshold = 0.01
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'; sc.render.image_settings.color_depth = '8'
sc.render.filepath = PNG; t = time.time(); bpy.ops.render.render(write_still=True); reg['segundos_prueba'] = round(time.time() - t, 1)
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
bpy.ops.wm.save_as_mainfile(filepath=BLEND, copy=True, compress=True)
reg.update({'png': PNG, 'blend': BLEND}); json.dump(reg, open(JS, 'w'), indent=1, ensure_ascii=False)
print('V42B_OK', reg['segundos_prueba'])
