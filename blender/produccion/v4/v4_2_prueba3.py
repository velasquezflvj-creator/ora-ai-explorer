# ORA · Apartamento 102 (PROPUESTA) · V4.2 prueba 3: dirección aprobada a partir de la referencia visual.
# Fuente: v4/escena_v4_2.blend (no se escribe). Cambios 1–5 aprobados; una sola imagen 960×540; exposición solo en vista.
#   blender -b v4/escena_v4_2.blend --python v4/v4_2_prueba3.py -- <png> <blend_copia> <json> <mascaras.npz>
import bpy, sys, json, math, time
import numpy as np
from mathutils import Vector
PNG, BLEND, JS, MASC = sys.argv[sys.argv.index('--') + 1:][:4]
sc = bpy.context.scene; vs = sc.view_settings; c = sc.cycles
reg = {'cambios': []}
def cambio(p, a, b): reg['cambios'].append({'parametro': p, 'antes': a, 'despues': b}); print('[v4.2c] CAMBIO', p, ':', a, '→', b)
r3 = lambda v: round(float(v), 3)
def bsdf(m): return next(n for n in m.node_tree.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled')

# 1. sol existente: elevación 18°, azimut 85° (entra solo por el vano de la puerta-ventana de la sala; ~6 % del sofá)
sol = sc.objects['Sol_HDRI']; assert not sol.hide_render
d0 = (sol.rotation_euler.to_matrix() @ Vector((0, 0, -1))); az0 = round(math.degrees(math.atan2(d0.y, d0.x)), 1)
e, a = math.radians(18), math.radians(85); dl = Vector((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), -math.sin(e)))
sol.rotation_euler = dl.to_track_quat('-Z', 'Y').to_euler(); cambio('Sol_HDRI azimut (°), elevación 18° y energía 4,0 sin cambio', az0, 85.0)
# 2. luz ambiental REAL del entorno (nodo Fondo: rayos no de cámara). Fondo.001 es solo el fondo visto por ventanas.
fondo = sc.world.node_tree.nodes['Fondo']; cambio('luz ambiental real (Fondo, fuerza)', r3(fondo.inputs['Strength'].default_value), 0.6); fondo.inputs['Strength'].default_value = 0.6
# 4. sofá: tejido fino uniforme
m = bpy.data.materials['mueble_tela_sofa']; b = bsdf(m); nt = m.node_tree
cambio('sofá: sheen', r3(b.inputs['Sheen Weight'].default_value), 0.2); b.inputs['Sheen Weight'].default_value = 0.2
def mapeo_de(tex):
    s = tex.inputs['Vector']
    while s.is_linked:
        n = s.links[0].from_node
        if n.bl_idname == 'ShaderNodeMapping': return n
        s = n.inputs[0] if n.inputs else None
        if s is None: return None
    return None
for tex in [n for n in nt.nodes if n.bl_idname == 'ShaderNodeTexImage' and n.image and n.image.name.startswith('wool_boucle')]:
    mp = mapeo_de(tex)
    if mp and not getattr(mp, '_hecho', False):
        s0 = [r3(v) for v in mp.inputs['Scale'].default_value]
        if s0[0] < 12:
            mp.inputs['Scale'].default_value = (s0[0] * 2, s0[1] * 2, s0[2]); cambio(f'sofá: escala del relieve bouclé ({mp.name})', s0[:2], [r3(v) for v in mp.inputs['Scale'].default_value][:2])
for n in nt.nodes:
    if n.bl_idname == 'ShaderNodeNormalMap': a0 = r3(n.inputs['Strength'].default_value); n.inputs['Strength'].default_value = a0 * 0.5; cambio(f'sofá: intensidad del mapa de normales ({n.name})', a0, r3(a0 * 0.5))
    if n.bl_idname == 'ShaderNodeBump': a0 = r3(n.inputs['Strength'].default_value); n.inputs['Strength'].default_value = a0 * 0.5; cambio(f'sofá: intensidad del relieve ({n.name})', a0, r3(a0 * 0.5))
# 5. travertino de salpicadero y mesón: veta estirada a lo largo (vetas finas y rectas)
for mn in ('salpicadero', 'meson'):
    mp = bpy.data.materials[mn].node_tree.nodes['Mapeo']; s0 = [r3(v) for v in mp.inputs['Scale'].default_value]
    mp.inputs['Scale'].default_value = (1.0, 2.5, 1.0); cambio(f'{mn}: escala del travertino (X a lo largo de la veta, Y transversal)', s0[:2], [1.0, 2.5])
# sin cambio: focos, madera, muros, WB, AgX
focos = {(round(o.data.energy, 2), o.data.temperature) for o in sc.objects if o.type == 'LIGHT' and o.data.type == 'SPOT' and o.name.startswith('Luz_')}
assert focos == {(9.0, 3600.0)} and abs(vs.white_balance_temperature - 4600) < 1e-3 and vs.view_transform == 'AgX'
reg['sin_cambio'] = {'focos': [list(f) for f in focos], 'wb_K': 4600, 'vista': [vs.view_transform, vs.look], 'madera': 'sin cambio', 'muros': 'sin cambio'}

# prueba única
cp = bpy.context.preferences.addons['cycles'].preferences; cp.compute_device_type = 'OPTIX'; cp.refresh_devices()
for dv in cp.devices: dv.use = dv.type == 'OPTIX'
sc.render.engine = 'CYCLES'; c.device = 'GPU'; c.denoiser = 'OPTIX'; c.use_denoising = True; c.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 960, 540, 100
c.samples = 256; c.use_adaptive_sampling = True; c.adaptive_threshold = 0.01
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'; sc.render.image_settings.color_depth = '8'
t = time.time(); bpy.ops.render.render(write_still=False); reg['segundos_prueba'] = round(time.time() - t, 1)
def medir(ev):
    vs.exposure = ev; p = '/tmp/ora_v42c.png'; bpy.data.images['Render Result'].save_render(p, scene=sc)
    im = bpy.data.images.load(p, check_existing=False); px = np.array(im.pixels[:], dtype=np.float32).reshape(-1, 4)[:, :3]; bpy.data.images.remove(im)
    l = px @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    return {'exp': r3(ev), 'p5': r3(np.percentile(l, 5)), 'p50': r3(np.median(l)), 'p95': r3(np.percentile(l, 95)), 'quemado_%': r3((px.max(1) > 0.98).mean() * 100)}
# 3. exposición en vista: mediana 0,50–0,55 y quemado ≤ 1 %, partiendo de +2,0
ev = 2.0; hist = [medir(ev)]
for _ in range(20):
    r = hist[-1]
    if r['quemado_%'] > 1.0 or r['p50'] > 0.55: ev -= 0.05
    elif r['p50'] < 0.50: ev += 0.05
    else: break
    hist.append(medir(ev))
reg['exposicion_evaluada'] = hist; cambio('exposición (EV), solo vista', 2.0, r3(ev))
for h in hist: print('[v4.2c] EXP', h)
bpy.data.images['Render Result'].save_render(PNG, scene=sc)
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
bpy.ops.wm.save_as_mainfile(filepath=BLEND, copy=True, compress=True)
reg.update({'png': PNG, 'blend': BLEND}); json.dump(reg, open(JS, 'w'), indent=1, ensure_ascii=False)
print('V42C_OK', reg['segundos_prueba'])
