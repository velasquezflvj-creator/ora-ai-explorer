# ORA · Apartamento 102 (PROPUESTA DE REDISTRIBUCIÓN) · V4.1: calibración fotográfica medida, imagen hero única.
# Abre v4/escena_v4.blend (no lo escribe), mide el color REAL en imagen de muros, techo, sofá y madera con máscaras por
# material, ajusta exposición + balance de blancos (temperatura y tinte) y albedos hasta la paleta objetivo, guarda una
# copia v4/escena_v4_1.blend y renderiza UNA imagen. No toca geometría, mobiliario, encuadre ni campo de visión.
#   blender -b v4/escena_v4.blend --python v4/v4_1_calibracion.py -- <control.json> <id> <png> <blend_copia> [muestras]
import bpy, json, sys, os, time, math, colorsys
import numpy as np
from mathutils import Matrix

a = sys.argv[sys.argv.index('--') + 1:]
CONTROL, VISTA, SALIDA, COPIA = a[:4]
MUESTRAS = int(a[4]) if len(a) > 4 else 1024
sc = bpy.context.scene; vs = sc.view_settings; c = sc.cycles
reg = {'cambios': [], 'medidas': []}
def log(*t): reg['cambios'].append(' '.join(str(x) for x in t)); print('[v4.1]', *t)
def bsdf(n):
    m = bpy.data.materials.get(n)
    return next((x for x in m.node_tree.nodes if x.bl_idname == 'ShaderNodeBsdfPrincipled'), None) if m else None
def hexa(rgb): return '#' + ''.join(f'{int(round(max(0, min(1, v)) * 255)):02X}' for v in rgb)
def s2l(v): v = np.asarray(v, dtype=np.float64); return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)

OBJ = {'muro': (0xE7, 0xE3, 0xDB), 'cielo': (0xF0, 0xEE, 0xEA), 'sofa': (0xC8, 0xBE, 0xB0)}
OBJ = {k: np.array(v) / 255 for k, v in OBJ.items()}
GRUPOS = {'muro': ['muro'], 'cielo': ['cielo'], 'sofa': ['mueble_tela_sofa'], 'madera': ['madera_mueble', 'gabinete_cocina']}
MADERA_SAT_OBJ, MADERA_TONO_OBJ = 0.38, 32.0   # roble natural (mediana en imagen): saturación moderada, tono hacia amarillo, no naranja

# ---------- cámara: exactamente la pose y el FOV de la vista de control (se verifica)
ctl = json.load(open(CONTROL)); fr = next(f for f in ctl['frames'] if f['id'] == VISTA)
cam = sc.camera; M = Matrix(fr['transform_matrix'])
dif = max(abs(cam.matrix_world[i][j] - M[i][j]) for i in range(4) for j in range(4))
assert dif < 1e-4 and abs(cam.data.angle - ctl['camera_angle_x']) < 1e-6, f'cámara distinta de {VISTA}: {dif}'
log(f'cámara {cam.name} = {VISTA} (diferencia de matriz {dif:.1e}, FOV {math.degrees(cam.data.angle):.2f}°)')

# ---------- dispositivo OptiX
cp = bpy.context.preferences.addons['cycles'].preferences; cp.compute_device_type = 'OPTIX'; cp.refresh_devices()
for dv in cp.devices: dv.use = dv.type == 'OPTIX'
gpus = [dv.name for dv in cp.devices if dv.use]; assert gpus
sc.render.engine = 'CYCLES'; c.device = 'GPU'; c.denoiser = 'OPTIX'; sc.render.use_persistent_data = True
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'; sc.render.image_settings.color_depth = '8'

# ---------- máscaras por material (render de emisión plana, se restaura todo después)
COL = {'muro': (1, 0, 0), 'cielo': (0, 1, 0), 'sofa': (0, 0, 1), 'madera': (1, 1, 0)}
def mascaras():
    guard = {'vt': vs.view_transform, 'look': vs.look, 'exp': vs.exposure, 'wb': vs.use_white_balance, 's': c.samples,
             'dn': c.use_denoising, 'fw': sc.render.filter_size, 'ad': c.use_adaptive_sampling}
    activos, nuevos = {}, []
    mat_a_grupo = {m: g for g, ms in GRUPOS.items() for m in ms}
    for m in bpy.data.materials:
        if not m.node_tree: continue
        nt = m.node_tree; act = next((n for n in nt.nodes if n.bl_idname == 'ShaderNodeOutputMaterial' and n.is_active_output), None)
        em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (*COL.get(mat_a_grupo.get(m.name), (0, 0, 0)), 1)
        out = nt.nodes.new('ShaderNodeOutputMaterial'); out.target = 'ALL'; nt.links.new(em.outputs[0], out.inputs['Surface'])
        out.is_active_output = True; activos[m.name] = act; nuevos.append((m, em, out))
    vs.view_transform = 'Standard'; vs.look = 'None'; vs.exposure = 0; vs.use_white_balance = False
    c.samples = 1; c.use_denoising = False; c.use_adaptive_sampling = False; sc.render.filter_size = 0.01
    sc.render.resolution_x, sc.render.resolution_y = 480, 270
    p = '/tmp/ora_v41_mask.png'; sc.render.filepath = p; bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(p, check_existing=False); px = np.array(im.pixels[:], dtype=np.float32).reshape(-1, 4)[:, :3]; bpy.data.images.remove(im)
    for m, em, out in nuevos:
        nt = m.node_tree; nt.nodes.remove(out); nt.nodes.remove(em)
        if activos[m.name]: activos[m.name].is_active_output = True
    vs.view_transform, vs.look, vs.exposure, vs.use_white_balance = guard['vt'], guard['look'], guard['exp'], guard['wb']
    c.samples, c.use_denoising, sc.render.filter_size, c.use_adaptive_sampling = guard['s'], guard['dn'], guard['fw'], guard['ad']
    r = {g: np.all(np.abs(px - np.array(col)) < 0.02, axis=1) for g, col in COL.items()}
    log('máscaras (píxeles a 480×270): ' + ', '.join(f'{g} {int(v.sum())}' for g, v in r.items()))
    return r
MASK = mascaras()
os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
np.savez_compressed(os.path.splitext(SALIDA)[0] + '_mascaras_480x270.npz', **MASK)   # para verificar la imagen final

# ---------- medición: render pequeño una vez; la exposición y el balance se re-aplican sin re-renderizar
def render_cal(muestras=96):
    sc.render.resolution_x, sc.render.resolution_y = 480, 270; c.samples = muestras; c.use_denoising = True
    c.use_adaptive_sampling = True; c.adaptive_threshold = 0.01
    sc.render.filepath = '/tmp/ora_v41_beauty.png'; bpy.ops.render.render(write_still=False)
def medir():
    """Color de cada grupo en su zona ILUMINADA (percentil 85–97 de luminancia), como lo leería un fotógrafo; y la mediana."""
    p = '/tmp/ora_v41_eval.png'; bpy.data.images['Render Result'].save_render(p, scene=sc)
    im = bpy.data.images.load(p, check_existing=False); px = np.array(im.pixels[:], dtype=np.float32).reshape(-1, 4)[:, :3]; bpy.data.images.remove(im)
    Y = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32); luma = px @ Y; med = {}
    for g, mk in MASK.items():
        if mk.sum() < 200: continue
        l = luma[mk]; lo, hi = np.percentile(l, 85), np.percentile(l, 97); sel = px[mk][(l >= lo) & (l <= hi)]
        med[g] = sel.mean(0); med[g + '_mediana'] = np.median(px[mk], 0)
    med['_quemado'] = float((px.max(1) > 0.985).mean()); med['_luma'] = float(np.median(luma))
    return med
def ajustar_camara():
    """1) balance de blancos (temperatura, tinte ±15) para la CROMATICIDAD del muro iluminado;
       2) exposición para su LUMINANCIA. Se alternan; no hace falta re-renderizar (es transformación de vista)."""
    Yl = np.array([0.2126, 0.7152, 0.0722])
    def crom(rgb): l = s2l(rgb); return np.log(np.maximum(l[[0, 2]], 1e-4) / max(l[1], 1e-4))
    obj_c = crom(OBJ['muro']); obj_y = float(s2l(OBJ['muro']) @ Yl)
    for vuelta in range(4):
        for it in range(5):
            x = np.array([vs.white_balance_temperature, vs.white_balance_tint]); y = crom(medir()['muro']); e = obj_c - y
            if np.abs(e).max() < 0.008: break
            J = np.zeros((2, 2))
            for k, dk in enumerate((150.0, 2.0)):
                xx = x.copy(); xx[k] += dk; vs.white_balance_temperature, vs.white_balance_tint = xx
                J[:, k] = (crom(medir()['muro']) - y) / dk
            paso = np.linalg.lstsq(J, e, rcond=None)[0] * 0.6
            vs.white_balance_temperature = float(np.clip(x[0] + paso[0], 3500, 7500)); vs.white_balance_tint = float(np.clip(x[1] + paso[1], -15, 15))
        for it in range(6):
            ly = float(s2l(medir()['muro']) @ Yl)
            if abs(math.log2(obj_y / max(ly, 1e-4))) < 0.02: break
            vs.exposure = float(np.clip(vs.exposure + 0.9 * math.log2(obj_y / max(ly, 1e-4)), -2, 6))

def mostrar(et):
    m = medir(); fila = {'etapa': et, 'exposicion': round(vs.exposure, 3), 'wb_K': round(vs.white_balance_temperature), 'tinte': round(vs.white_balance_tint, 1),
                         'quemado_%': round(m['_quemado'] * 100, 2), 'mediana_luma': round(m['_luma'], 3)}
    for g in ('muro', 'cielo', 'sofa', 'madera'):
        if g in m:
            fila[g + '_mediana'] = hexa(m[g + '_mediana'])
            h_, s_, v_ = colorsys.rgb_to_hsv(*m[g]); fila[g] = hexa(m[g]); fila[g + '_sat'] = round(float(s_), 3); fila[g + '_tono°'] = round(float(h_) * 360)
    reg['medidas'].append(fila); log(json.dumps(fila, ensure_ascii=False, default=float)); return m

vs.use_white_balance = True
# curva fotográfica con más contraste en medios tonos (las paredes se recalibran a su HEX igualmente)
vs.view_transform = 'AgX'; vs.look = 'AgX - High Contrast'; log('curva de vista: AgX - High Contrast (antes Medium High Contrast)')
# luminarias con detalle en altas luces (pantalla de lámpara de pie y tiras LED)
for mn, f in (('pantalla_lampara', 0.5), ('luz_calida', 0.7)):
    for nd in bpy.data.materials[mn].node_tree.nodes:
        s_ = nd.inputs.get('Emission Strength')
        if s_ is not None and not s_.is_linked and s_.default_value > 0:
            a0 = s_.default_value; s_.default_value *= f; log(f'emisión {mn}: {a0:.2f} → {s_.default_value:.2f}')
render_cal(); mostrar('V4 (punto de partida)')

# ---------- bucle: cámara (exposición/WB) ↔ albedos (techo, sofá) ↔ saturación de madera
for k in range(4):
    ajustar_camara(); m = mostrar(f'iteración {k}: cámara ajustada al muro iluminado')
    listo = True
    for g, mat in (('cielo', 'cielo'), ('sofa', 'mueble_tela_sofa')):
        if g not in m: continue
        b = bsdf(mat); bc = np.array(b.inputs['Base Color'].default_value[:3])
        r = s2l(OBJ[g]) / np.maximum(s2l(m[g]), 1e-4)
        if np.abs(np.log(r)).max() > 0.03: listo = False
        nuevo = np.clip(bc * r ** 0.85, 0.03, 0.85); b.inputs['Base Color'].default_value = (*nuevo, 1)
        log(f'albedo {mat}: {np.round(bc, 3).tolist()} → {np.round(nuevo, 3).tolist()}')
    if 'madera_mediana' in m:
        h_, s_, _ = colorsys.rgb_to_hsv(*m['madera_mediana']); h_ *= 360
        if abs(s_ - MADERA_SAT_OBJ) > 0.02 or abs(h_ - MADERA_TONO_OBJ) > 1.5:
            listo = False; f = (MADERA_SAT_OBJ / max(s_, 0.05)) ** 0.9; dh = (MADERA_TONO_OBJ - h_) / 360 * 0.8
            for mn in GRUPOS['madera']:
                for hs in [n for n in bpy.data.materials[mn].node_tree.nodes if n.bl_idname == 'ShaderNodeHueSaturation']:
                    hs.inputs['Saturation'].default_value = float(np.clip(hs.inputs['Saturation'].default_value * f, 0.3, 1.2))
                    hs.inputs['Hue'].default_value = float(np.clip(hs.inputs['Hue'].default_value + dh, 0.45, 0.56))
            log(f'madera (mediana): saturación {s_:.3f} → ×{f:.3f}; tono {h_:.1f}° → desplazamiento {dh*360:+.1f}°')
    if listo and k > 0: break
    render_cal()
ajustar_camara(); final = mostrar('V4.1 calibrada (480×270)')

# ---------- copia independiente
bpy.ops.wm.save_as_mainfile(filepath=COPIA, copy=True, compress=True); log(f'copia guardada: {COPIA}')

# ---------- render hero
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, 100
c.samples = MUESTRAS; c.adaptive_threshold = 0.006; c.adaptive_min_samples = 64; c.use_denoising = True; c.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
os.makedirs(os.path.dirname(SALIDA), exist_ok=True); sc.render.filepath = SALIDA
t0 = time.time(); bpy.ops.render.render(write_still=True); dt = time.time() - t0
reg.update({'segundos_render': round(dt, 1), 'gpu': gpus, 'resolucion': [1920, 1080], 'muestras_max': MUESTRAS, 'copia': COPIA, 'salida': SALIDA,
            'objetivos': {k: hexa(v) for k, v in OBJ.items()} | {'madera_saturacion': MADERA_SAT_OBJ, 'madera_tono': MADERA_TONO_OBJ}})
json.dump(reg, open(os.path.splitext(SALIDA)[0] + '_calibracion.json', 'w'), indent=1, ensure_ascii=False, default=float)
log(f'render hero 1920×1080 en {dt:.1f} s'); print('V41_OK', round(dt, 1))
