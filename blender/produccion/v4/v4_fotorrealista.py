# ORA · Apartamento 102 (PROPUESTA DE REDISTRIBUCIÓN, no planta verificada) · V4 fotorrealista, imagen hero única.
# Se ejecuta sobre escena/escena_splat_v2.blend abierta en segundo plano. NO guarda sobre el original:
# guarda una copia independiente (save_as_mainfile copy=True) y renderiza UNA imagen con OptiX.
# No cambia geometría, dimensiones, mobiliario ni distribución: solo materiales, luces, color y render.
#   blender -b escena/escena_splat_v2.blend --python v4/v4_fotorrealista.py -- <control.json> <id_vista> <png_salida> <blend_copia> [muestras] [ancho] [alto]
import bpy, json, sys, os, time, math
import numpy as np
from mathutils import Matrix

a = sys.argv[sys.argv.index('--') + 1:]
CONTROL, VISTA, SALIDA, COPIA = a[:4]
MUESTRAS = int(a[4]) if len(a) > 4 else 1024
W = int(a[5]) if len(a) > 5 else 1920
H = int(a[6]) if len(a) > 6 else 1080
sc = bpy.context.scene
cambios = []
def log(*t): cambios.append(' '.join(str(x) for x in t)); print('[v4]', *t)

def bsdf(m):
    return next((n for n in m.node_tree.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled'), None) if m and m.node_tree else None
def mat(n): return bpy.data.materials.get(n)

# ---------- 1. albedos neutros realistas (la causa principal de la dominante amarilla y del contraste plano)
ALBEDO = {   # lineal; pintura blanca real ≈ 0,6–0,75. Antes: muros 0,88/0,86/0,81, cielo 0,91, sofá 0,86/0,79/0,69
    'muro': (0.66, 0.655, 0.64), 'cielo': (0.73, 0.73, 0.72), 'carpinteria': (0.63, 0.62, 0.60), 'marco_puerta': (0.63, 0.62, 0.60),
    'guardaescoba': (0.60, 0.59, 0.57), 'ceramica_calida': (0.70, 0.69, 0.66), 'electro_blanco': (0.75, 0.75, 0.74),
    'laca_mueble': (0.56, 0.51, 0.45), 'mueble_bano': (0.52, 0.46, 0.38),
    'mueble_tela_sofa': (0.63, 0.60, 0.55), 'tela_silla': (0.62, 0.595, 0.55), 'tela_cortina': (0.56, 0.53, 0.48),
    'tela_visillo': (0.76, 0.75, 0.72), 'pantalla_lampara': (0.80, 0.78, 0.74), 'libro_c': (0.70, 0.67, 0.60),
    'ceramica_deco': (0.68, 0.645, 0.58), 'toalla': (0.70, 0.67, 0.61),
}
for n, rgb in ALBEDO.items():
    b = bsdf(mat(n))
    if b and not b.inputs['Base Color'].is_linked:
        antes = [round(v, 3) for v in b.inputs['Base Color'].default_value[:3]]
        b.inputs['Base Color'].default_value = (*rgb, 1); log(f'albedo {n}: {antes} → {list(rgb)}')
# tope general de albedo 0,8 en lo no metálico/no vidrio/no emisivo
for m in bpy.data.materials:
    b = bsdf(m)
    if not b or m.name in ALBEDO or b.inputs['Base Color'].is_linked: continue
    if b.inputs['Metallic'].default_value > 0.5 or 'vidrio' in m.name or 'espejo' in m.name or 'luz' in m.name: continue
    c = b.inputs['Base Color'].default_value; mx = max(c[:3])
    if mx > 0.8: b.inputs['Base Color'].default_value = (*(v * 0.8 / mx for v in c[:3]), 1); log(f'tope albedo {m.name}: {mx:.2f} → 0.80')

# ---------- 2. textiles: brillo de fibra (sheen) y sin reflejo especular de plástico
for n, sh in {'mueble_tela_sofa': 0.6, 'tela_silla': 0.5, 'tela_cortina': 0.35, 'tela_visillo': 0.25, 'textil_tapete': 0.6,
              'mueble_tela_butaca': 0.5, 'tela_cama': 0.4, 'tela_cabecero': 0.4, 'tela_acento': 0.4, 'toalla': 0.5}.items():
    b = bsdf(mat(n))
    if b:
        b.inputs['Sheen Weight'].default_value = sh; b.inputs['Sheen Roughness'].default_value = 0.45
        b.inputs['Specular IOR Level'].default_value = 0.25; log(f'textil {n}: sheen {sh}, especular 0.25')

# ---------- 3. madera: veta a escala real, variación por objeto, acabado satinado; tonos diferenciados
def nodos(m, tipo): return [n for n in m.node_tree.nodes if n.bl_idname == tipo]
def desplazamiento_aleatorio(m, amp=(13.7, 7.3, 0.0)):
    nt = m.node_tree
    for mp in nodos(m, 'ShaderNodeMapping'):
        if mp.inputs['Location'].is_linked: continue
        oi = nt.nodes.new('ShaderNodeObjectInfo'); vm = nt.nodes.new('ShaderNodeVectorMath'); vm.operation = 'MULTIPLY'
        vm.inputs[1].default_value = amp
        nt.links.new(oi.outputs['Random'], vm.inputs[0]); nt.links.new(vm.outputs[0], mp.inputs['Location'])
def escalar_mapeo(m, f):
    for mp in nodos(m, 'ShaderNodeMapping'):
        s = mp.inputs['Scale'].default_value; antes = [round(v, 3) for v in s]
        mp.inputs['Scale'].default_value = (s[0] * f, s[1] * f, s[2]); log(f'escala {m.name}: {antes} → {[round(v, 3) for v in mp.inputs["Scale"].default_value]} (tesela {1/ (antes[0]*f):.2f} m)')
def variar_rugosidad(m, amp=0.18, escala=3.5):
    """Imperfección: modula la rugosidad con ruido (huellas, desgaste, polvo) para evitar superficies uniformes."""
    b = bsdf(m); nt = m.node_tree
    if not b: return
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = escala; nz.inputs['Detail'].default_value = 8
    tc = nt.nodes.new('ShaderNodeTexCoord'); nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 1 - amp; mr.inputs['To Max'].default_value = 1 + amp
    nt.links.new(nz.outputs['Fac'], mr.inputs['Value'])
    mu = nt.nodes.new('ShaderNodeMath'); mu.operation = 'MULTIPLY'; mu.use_clamp = True
    ent = b.inputs['Roughness']
    if ent.is_linked: nt.links.new(ent.links[0].from_socket, mu.inputs[0])
    else: mu.inputs[0].default_value = ent.default_value
    nt.links.new(mr.outputs['Result'], mu.inputs[1]); nt.links.new(mu.outputs[0], ent); log(f'imperfección de rugosidad {m.name}: ±{int(amp*100)} %')

for n, (valor, sat) in {'madera_mueble': (1.0, 0.9), 'gabinete_cocina': (0.82, 0.85), 'puerta_entrada': (0.9, 0.9)}.items():
    m = mat(n)
    if not m: continue
    escalar_mapeo(m, 3.0); desplazamiento_aleatorio(m)
    for hs in nodos(m, 'ShaderNodeHueSaturation'):
        hs.inputs['Value'].default_value *= valor; hs.inputs['Saturation'].default_value *= sat
    b = bsdf(m); b.inputs['Coat Weight'].default_value = 0.12; b.inputs['Coat Roughness'].default_value = 0.3
    variar_rugosidad(m, 0.12, 2.5); log(f'madera {n}: valor ×{valor}, saturación ×{sat}, laca satinada (coat 0.12)')

# ---------- 4. piedra (travertino): escala real, variación por objeto, mesón sellado con reflejo suave
for n, f in {'meson': 2.0, 'salpicadero': 2.0, 'alfeizar': 2.0}.items():
    m = mat(n)
    if m: escalar_mapeo(m, f); desplazamiento_aleatorio(m)
for n in ('meson', 'salpicadero'):
    b = bsdf(mat(n))
    if b: b.inputs['Coat Weight'].default_value = 0.25; b.inputs['Coat Roughness'].default_value = 0.18; log(f'piedra {n}: sellado (coat 0.25 / 0.18)')
if mat('piso_madera'): desplazamiento_aleatorio(mat('piso_madera'))
for n, amp in {'meson': 0.2, 'piso_madera': 0.15, 'laca_mueble': 0.12, 'carpinteria': 0.1, 'muro': 0.08, 'ceramica_calida': 0.15}.items():
    if mat(n): variar_rugosidad(mat(n), amp)

# ---------- 5. metales: rugosidad y tono creíbles
for n, (rgb, r) in {'laton_cepillado': ((0.80, 0.62, 0.38), 0.32), 'mueble_laton': ((0.80, 0.62, 0.38), 0.3),
                    'cromo': ((0.62, 0.62, 0.63), 0.12), 'acero': ((0.62, 0.62, 0.62), 0.3), 'metal_negro': ((0.03, 0.03, 0.03), 0.42)}.items():
    b = bsdf(mat(n))
    if b and not b.inputs['Base Color'].is_linked:
        b.inputs['Base Color'].default_value = (*rgb, 1)
        if not b.inputs['Roughness'].is_linked: b.inputs['Roughness'].default_value = r
        log(f'metal {n}: color {rgb}, rugosidad {r}')

# ---------- 6. iluminación: luz natural dominante, artificial como acento (3 600 K), sin luminarias quemadas
for o in sc.objects:
    if o.type != 'LIGHT': continue
    d = o.data
    if d.type == 'SPOT' and o.name.startswith('Luz_'):
        d.energy = 9.0; d.use_temperature = True; d.temperature = 3600; d.shadow_soft_size = 0.04
    if d.type == 'AREA' and o.name.startswith('CTX'): d.energy *= 0.6
log('focos empotrados: 14 W/4200 K → 9 W/3600 K, fuente de 4 cm (sombras más suaves y creíbles)')
for m in bpy.data.materials:
    if not m.node_tree: continue
    fac = {'vidrio_opal': 0.35, 'luz_calida': 0.6, 'pantalla_lampara': 0.6}.get(m.name)
    if not fac: continue
    for nd in m.node_tree.nodes:
        for s in nd.inputs:
            if s.name in ('Emission Strength', 'Strength') and not s.is_linked and isinstance(s.default_value, float) and nd.bl_idname != 'ShaderNodeBackground':
                antes = s.default_value; s.default_value *= fac; log(f'emisión {m.name}/{nd.name}: {antes:.2f} → {s.default_value:.2f}')
w = sc.world
if w and w.node_tree:
    fb = w.node_tree.nodes.get('Fondo.001')
    if fb: fb.inputs['Strength'].default_value *= 1.6; log(f'luz del cielo (rama de iluminación del HDRI) ×1.6 → {fb.inputs["Strength"].default_value:.2f}')

# ---------- 7. cámara: misma pose y campo de visión que la vista de control V3
ctl = json.load(open(CONTROL)); fr = next(f for f in ctl['frames'] if f['id'] == VISTA)
cd = bpy.data.cameras.new('_v4'); cd.lens_unit = 'FOV'; cd.angle = ctl['camera_angle_x']; cd.clip_start = 0.05; cd.sensor_fit = 'HORIZONTAL'
cam = bpy.data.objects.new('_v4', cd); sc.collection.objects.link(cam); sc.camera = cam; cam.matrix_world = Matrix(fr['transform_matrix'])

# ---------- 8. render: OptiX, muestreo alto, ruido controlado
cp = bpy.context.preferences.addons['cycles'].preferences; cp.compute_device_type = 'OPTIX'; cp.refresh_devices()
for dv in cp.devices: dv.use = dv.type == 'OPTIX'
gpus = [dv.name for dv in cp.devices if dv.use]
assert gpus, 'sin dispositivo OptiX'
c = sc.cycles; sc.render.engine = 'CYCLES'; c.device = 'GPU'
c.use_denoising = True; c.denoiser = 'OPTIX'; c.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
c.use_adaptive_sampling = True; c.adaptive_threshold = 0.008; c.adaptive_min_samples = 64
c.max_bounces = 12; c.diffuse_bounces = 6; c.glossy_bounces = 6; c.transmission_bounces = 12; c.transparent_max_bounces = 16
c.sample_clamp_direct = 0; c.sample_clamp_indirect = 10; c.blur_glossy = 0.5; c.caustics_reflective = False; c.caustics_refractive = False
c.use_light_tree = True
sc.render.use_persistent_data = True; sc.render.film_transparent = False; sc.render.use_stamp = False
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'; sc.render.image_settings.color_depth = '8'

# ---------- 9. color: AgX con contraste medio-alto; exposición y balance de blancos calibrados con renders pequeños
vs = sc.view_settings; vs.view_transform = 'AgX'; vs.look = 'AgX - Medium High Contrast'
tiene_wb = hasattr(vs, 'use_white_balance')
if tiene_wb: vs.use_white_balance = True; vs.white_balance_temperature = 6500; vs.white_balance_tint = 0
def medir():
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 480, 270, 100; c.samples = 48
    p = '/tmp/ora_v4_cal.png'; sc.render.filepath = p; bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(p, check_existing=False); px = np.array(im.pixels[:], dtype=np.float32).reshape(-1, 4)[:, :3]; bpy.data.images.remove(im)
    luma = px @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    mx, mn = px.max(1), px.min(1); sat = (mx - mn) / np.maximum(mx, 1e-4)
    neutros = (sat < 0.3) & (luma > 0.2) & (luma < 0.92)
    rb = float(px[neutros, 0].mean() / max(px[neutros, 2].mean(), 1e-4)) if neutros.sum() > 500 else 1.0
    return float(np.median(luma)), rb, float((luma > 0.98).mean())
vs.exposure = 0.0
OBJ_LUMA, OBJ_RB = 0.46, 1.07   # mediana de luminancia de foto interior bien expuesta; blancos apenas cálidos
for it in range(4):
    med, rb, quemado = medir()
    log(f'calibración {it}: exposición {vs.exposure:+.2f}, WB {getattr(vs, "white_balance_temperature", "-")} K → mediana {med:.3f}, R/B neutros {rb:.3f}, quemado {quemado*100:.1f} %')
    dexp = 0.8 * 2.2 * math.log2(OBJ_LUMA / max(med, 1e-3)); vs.exposure = max(-2, min(2, vs.exposure + dexp))
    if tiene_wb: vs.white_balance_temperature = max(3800, min(7500, vs.white_balance_temperature * (OBJ_RB / rb) ** 1.2))
    if abs(dexp) < 0.06 and abs(rb - OBJ_RB) < 0.015: break
med, rb, quemado = medir()
log(f'calibración final: exposición {vs.exposure:+.2f}, WB {getattr(vs, "white_balance_temperature", "-")} K → mediana {med:.3f}, R/B {rb:.3f}, quemado {quemado*100:.1f} %')

# ---------- 10. copia independiente de la escena V4 (el .blend de origen no se escribe)
os.makedirs(os.path.dirname(COPIA), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=COPIA, copy=True, compress=True); log(f'copia V4 guardada: {COPIA}')

# ---------- 11. render hero
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, H, 100; c.samples = MUESTRAS
os.makedirs(os.path.dirname(SALIDA), exist_ok=True); sc.render.filepath = SALIDA
t0 = time.time(); bpy.ops.render.render(write_still=True); dt = time.time() - t0
log(f'render hero {W}×{H}, {MUESTRAS} muestras máx. (adaptativo 0.008), OptiX en {gpus}: {dt:.1f} s')
json.dump({'vista': VISTA, 'salida': SALIDA, 'copia_blend': COPIA, 'segundos_render': round(dt, 1), 'gpu': gpus, 'muestras_max': MUESTRAS,
           'resolucion': [W, H], 'exposicion': vs.exposure, 'wb_k': getattr(vs, 'white_balance_temperature', None), 'cambios': cambios},
          open(os.path.splitext(SALIDA)[0] + '_cambios.json', 'w'), indent=1, ensure_ascii=False)
print('V4_OK', round(dt, 1))
