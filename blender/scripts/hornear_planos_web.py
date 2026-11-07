"""Hornea con Cycles la luz del piso y del cielo raso para el visor web (recorrido V3), sin tocar el .blend de entrada.

    Blender -b blender/Apartamento_102_Render_V3.blend --python blender/scripts/hornear_planos_web.py -- \
        blender/scripts/apto-102.json apartamento-102/modelo/web/horneado [--muestras 512] [--px 1024]

Por qué así: el GLB no tiene un segundo juego de UV para lightmaps y no se quiere regenerar el modelo. El piso y el
cielo raso son horizontales, así que su luz se puede capturar con una cámara ortográfica cenital (piso) o desde abajo
(cielo) y proyectarse en el visor con las coordenadas de planta. El resto de objetos sigue en la escena (proyecta
sombras, ocluye y rebota luz) pero es invisible para la cámara.

Salida:
  piso_luz.hdr   irradiancia difusa del piso (directa + indirecta), sin el color del piso: luz = Combined / albedo.
                 En el visor: color del piso × luz (sombras suaves, contacto bajo muebles, manchas de sol, rebotes).
  cielo.hdr      apariencia final del cielo raso (incluye el brillo del foseado y de las luminarias).
  horneado.json  encuadre (centro, lado en metros, orientación de cada imagen) y gradación aplicada.
Ambas con la misma gradación que las sondas (exposición y balance de blancos del render V3).
"""
import bpy, sys, os, json, math
import numpy as np

argv = sys.argv[sys.argv.index('--') + 1:]
CFG = json.load(open(argv[0])); DEST = os.path.abspath(argv[1]); os.makedirs(DEST, exist_ok=True)
MUESTRAS = int(argv[argv.index('--muestras') + 1]) if '--muestras' in argv else 512
PX = int(argv[argv.index('--px') + 1]) if '--px' in argv else 1024
H = CFG.get('horneado', {})
CX, CY = H.get('centro', [0.0, 0.0]); LADO = H.get('lado_m', 8.0)
ALBEDO_PISO = H.get('albedo_piso_lineal', [0.70, 0.64, 0.56])
GRAD = CFG['sondas'].get('gradacion', {'exposicion_ev': 0.8, 'balance_k': 5000})

sc = bpy.data.scenes[CFG['escena']]
if bpy.context.window: bpy.context.window.scene = sc
r = sc.render
r.engine = 'CYCLES'; r.use_stamp = False; r.resolution_x = r.resolution_y = PX; r.resolution_percentage = 100
r.film_transparent = False
r.image_settings.file_format = 'HDR'
sc.cycles.samples = MUESTRAS; sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.01
sc.cycles.use_denoising = True
try:
    cp = bpy.context.preferences.addons['cycles'].preferences; cp.compute_device_type = 'METAL'; cp.refresh_devices()
    for d in cp.devices: d.use = d.type == 'METAL'
    sc.cycles.device = 'GPU'
except Exception as e:
    print('[horneado] sin GPU:', e)

cd = bpy.data.cameras.new('_horneado'); cd.type = 'ORTHO'; cd.ortho_scale = LADO; cd.clip_start = 0.01; cd.clip_end = 10
cam = bpy.data.objects.new('_horneado', cd); sc.collection.objects.link(cam); sc.camera = cam
mallas = [o for o in sc.objects if o.type == 'MESH']


def solo_visibles(nombres):
    for o in mallas:
        o.visible_camera = any(o.name.startswith(n) for n in nombres)


def kelvin_rgb(k):
    t = k / 100.0
    rr = 255 if t <= 66 else 329.698727446 * (t - 60) ** -0.1332047592
    g = 99.4708025861 * math.log(t) - 161.1195681661 if t <= 66 else 288.1221695283 * (t - 60) ** -0.0755148492
    b = 255 if t >= 66 else (0 if t <= 19 else 138.5177312231 * math.log(t - 10) - 305.0447927307)
    c = np.clip(np.array([rr, g, b], np.float32) / 255, 0, 1)
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return c / c[1]


GAN = (2 ** GRAD['exposicion_ev']) / kelvin_rgb(GRAD['balance_k']); GAN = GAN / GAN[1] * (2 ** GRAD['exposicion_ev'])


def render(nombre):
    ruta = os.path.join(DEST, f'_{nombre}_crudo.hdr'); r.filepath = ruta
    bpy.ops.render.render(write_still=True, scene=sc.name)
    im = bpy.data.images.load(ruta); w, h = im.size
    a = np.array(im.pixels[:], np.float32).reshape(h, w, 4); bpy.data.images.remove(im); os.remove(ruta)
    return a


def guardar(a, nombre):
    h, w = a.shape[:2]
    out = bpy.data.images.new('_o', w, h, alpha=False, float_buffer=True); out.pixels[:] = a.ravel()
    ruta = os.path.join(DEST, nombre); out.filepath_raw = ruta; out.file_format = 'HDR'; out.save(); bpy.data.images.remove(out)
    print(f'[horneado] {nombre}: {w}x{h}, media {a[..., :3].mean():.3f}')


# ---------------------------------------------------------------- piso: irradiancia (Combined / albedo constante)
m = bpy.data.materials.new('_piso_hornear'); m.use_nodes = True
b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
b.inputs['Base Color'].default_value = (*ALBEDO_PISO, 1); b.inputs['Roughness'].default_value = 1.0
b.inputs['Specular IOR Level'].default_value = 0.0
for o in mallas:
    if o.name.startswith('ARQ_Piso'):
        for s in o.material_slots: s.material = m
solo_visibles(['ARQ_Piso'])
cam.location = (CX, CY, 3.0); cam.rotation_euler = (0, 0, 0)            # mira hacia −Z; arriba de la imagen = +Y (norte)
a = render('piso')
luz = a.copy(); luz[..., :3] = a[..., :3] / np.array(ALBEDO_PISO, np.float32) * GAN
guardar(luz, 'piso_luz.hdr')

# ---------------------------------------------------------------- cielo raso: apariencia final
solo_visibles(['ARQ_Cielo', 'ILU_Cielo_detalles'])
cam.location = (CX, CY, 0.3); cam.rotation_euler = (math.pi, 0, 0)      # mira hacia +Z; arriba de la imagen = −Y (sur)
a = render('cielo'); a[..., :3] *= GAN
guardar(a, 'cielo.hdr')

json.dump({
    'centro_blender': [CX, CY], 'lado_m': LADO, 'px': PX, 'muestras': MUESTRAS,
    'piso': {'archivo': 'piso_luz.hdr', 'tipo': 'irradiancia (luz sin albedo)', 'albedo_usado': ALBEDO_PISO,
             'orientacion': 'u = (x - cx)/lado + 0.5 ; v = (y - cy)/lado + 0.5 (v hacia el norte)'},
    'cielo': {'archivo': 'cielo.hdr', 'tipo': 'apariencia final (Combined)',
              'orientacion': 'u = (x - cx)/lado + 0.5 ; v = (cy - y)/lado + 0.5 (v hacia el sur)'},
    'gradacion': GRAD, 'coordenadas': 'Blender: x este, y norte, z arriba (= plano local menos origen_plano)',
}, open(os.path.join(DEST, 'horneado.json'), 'w'), indent=1, ensure_ascii=False)
print('[horneado] listo:', DEST, '(el .blend de entrada no se guarda)')
