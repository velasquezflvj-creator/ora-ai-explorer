"""Conjunto de cámaras para un piloto de Gaussian Splatting (sala y cocina del apartamento 102) y su render con Cycles.

    # 1) solo planificar (rápido): crea las cámaras en memoria y escribe transforms.json + un resumen; NO renderiza
    Blender -b blender/Apartamento_102_Render_V3.blend --python blender/scripts/camaras_splat.py -- \
        blender/scripts/apto-102.json blender/splat_sala_cocina --planificar
    # 2) renderizar (PESADO: horas en un Mac M2; ver docs/gaussian-splatting-piloto.md antes de lanzarlo)
    Blender -b blender/Apartamento_102_Render_V3.blend --python blender/scripts/camaras_splat.py -- \
        blender/scripts/apto-102.json blender/splat_sala_cocina --renderizar [--desde N --hasta M]
    # 3) en la nube (paquete de tools/splat/preparar_paquete.sh): GPU NVIDIA con OptiX, muestras propias y las vistas
    #    de control (no se entrenan; sirven de referencia para comparar V5 y splat desde las mismas poses)
    blender -b escena/escena_splat.blend --python blender/scripts/camaras_splat.py -- \
        blender/scripts/apto-102.json datos --renderizar --control --dispositivo OPTIX --muestras 128
Opciones: --dispositivo METAL|OPTIX|CUDA|CPU (por defecto METAL si existe, si no OPTIX, CUDA o CPU),
--muestras N, --control (renderiza también control/<id>.png y escribe control.json), --solo-control.

Diseño: las cámaras recorren la zona navegable (piso libre de sala, comedor-barra y cocina, sin entrar en muebles) en
una rejilla de ~0,45 m, a tres alturas (1,20 / 1,60 / 2,00 m), mirando en 8 direcciones con ligera inclinación hacia
abajo y hacia arriba; más vistas cercanas de mesón, barra y sofá para el detalle. Así cada punto de la escena se ve desde
muchos ángulos, que es lo que necesita el entrenamiento. Salida en formato NeRF/3DGS (transforms.json: camera_angle_x,
matrices cámara→mundo con ejes de OpenGL), que leen nerfstudio, gsplat, OpenSplat y Brush.
El .blend de entrada no se guarda.
"""
import bpy, sys, os, json, math
from mathutils import Vector, Matrix, Euler

argv = sys.argv[sys.argv.index('--') + 1:]
CFG = json.load(open(argv[0])); DEST = os.path.abspath(argv[1]); os.makedirs(os.path.join(DEST, 'images'), exist_ok=True)
RENDER = '--renderizar' in argv
DESDE = int(argv[argv.index('--desde') + 1]) if '--desde' in argv else 0
HASTA = int(argv[argv.index('--hasta') + 1]) if '--hasta' in argv else 10 ** 9
DISP = argv[argv.index('--dispositivo') + 1].upper() if '--dispositivo' in argv else None
MUESTRAS = int(argv[argv.index('--muestras') + 1]) if '--muestras' in argv else None
CONTROL = '--control' in argv or '--solo-control' in argv
SOLO_CONTROL = '--solo-control' in argv
SP = CFG.get('splat', {})
ox, oy = CFG['origen_plano']
sc = bpy.data.scenes[CFG['escena']]
if bpy.context.window: bpy.context.window.scene = sc
geo = json.load(open(os.path.join(os.path.dirname(os.path.abspath(argv[0])), '..', '..', 'apartamento-102', 'data', 'propuesta-102.json')))

# --- zona navegable: rectángulos de los espacios del piloto menos huellas de muebles/aparatos (planta local)
espacios = [e for e in geo['espacios'] if e['id'] in SP.get('espacios', ['social'])]
mob = geo.get('mobiliario', {})
obst = [a['rect'] for a in geo['aparatos'] if a.get('rect')] + [r for r in (mob.values() if isinstance(mob, dict) else []) if isinstance(r, list) and len(r) == 4]
def libre(x, y, r=0.25):
    if not any(any(x0 + r <= x <= x1 - r and y0 + r <= y <= y1 - r for x0, y0, x1, y1 in e['piso_rectangulos']) for e in espacios): return False
    return not any(min(a, c) - r < x < max(a, c) + r and min(b, d) - r < y < max(b, d) + r for a, b, c, d in obst)
paso = SP.get('paso_m', 0.45); alturas = SP.get('alturas_m', [1.2, 1.6, 2.0]); dirs = SP.get('direcciones', 8)
puntos = []
for e in espacios:
    for x0, y0, x1, y1 in e['piso_rectangulos']:
        nx, ny = max(1, int((x1 - x0) / paso)), max(1, int((y1 - y0) / paso))
        for i in range(nx + 1):
            for j in range(ny + 1):
                x, y = x0 + (x1 - x0) * i / nx, y0 + (y1 - y0) * j / ny
                if libre(x, y): puntos.append((x, y))
vistas = []
for k, (x, y) in enumerate(puntos):
    for h_i, h in enumerate(alturas):
        incl = {0: math.radians(-12), 1: math.radians(-4), 2: math.radians(-25)}.get(h_i, 0)
        for d in range(dirs):
            yaw = 2 * math.pi * d / dirs + (k % 3) * 0.17 + h_i * 0.31   # desfase: más diversidad de ángulos
            vistas.append({'plano': (x, y, h), 'yaw': yaw, 'pitch': incl})
for c in SP.get('detalles', []):   # vistas cercanas de mesón, barra y sofá
    vistas.append({'plano': tuple(c['desde']), 'mira': tuple(c['hacia'])})

cd = bpy.data.cameras.new('_splat'); cd.lens_unit = 'FOV'; cd.angle = math.radians(SP.get('fov_grados', 75)); cd.clip_start = 0.05
cam = bpy.data.objects.new('_splat', cd); sc.collection.objects.link(cam); sc.camera = cam
W, H = SP.get('px', [1280, 720])
r = sc.render; r.resolution_x, r.resolution_y, r.resolution_percentage = W, H, 100; r.use_stamp = False
r.image_settings.file_format = 'PNG'
frames = []
for i, v in enumerate(vistas):
    x, y, h = v['plano']; pos = Vector((x - ox, y - oy, h))
    if 'mira' in v:
        mx, my, mh = v['mira']; rot = (Vector((mx - ox, my - oy, mh)) - pos).to_track_quat('-Z', 'Y').to_euler()
    else:
        d = Vector((math.cos(v['yaw']) * math.cos(v['pitch']), math.sin(v['yaw']) * math.cos(v['pitch']), math.sin(v['pitch'])))
        rot = d.to_track_quat('-Z', 'Y').to_euler()
    m = Matrix.Translation(pos) @ rot.to_matrix().to_4x4()
    frames.append({'file_path': f'images/{i:04d}.png', 'transform_matrix': [list(fila) for fila in m]})
json.dump({'camera_angle_x': cd.angle_x if hasattr(cd, 'angle_x') else cd.angle, 'w': W, 'h': H,
           'nota': 'Cámaras del piloto de Gaussian Splatting (sala y cocina). Ejes Blender: z arriba; matrices cámara→mundo (OpenGL: la cámara mira a −Z).',
           'frames': frames}, open(os.path.join(DEST, 'transforms.json'), 'w'), indent=1)
print(f'[splat] {len(puntos)} puntos libres × {len(alturas)} alturas × {dirs} direcciones + {len(SP.get("detalles", []))} detalles = {len(frames)} vistas ({W}×{H})')
# --- vistas de control (no entrenan): mismas poses que capturan la V5 y el splat en el navegador
control = []
for c in SP.get('control', {}).get('vistas', []):
    (x, y, h), (lx, ly, lh) = c['desde'], c['hacia']
    pos = Vector((x - ox, y - oy, h)); rot = (Vector((lx - ox, ly - oy, lh)) - pos).to_track_quat('-Z', 'Y').to_euler()
    control.append({'id': c['id'], 'file_path': f"control/{c['id']}.png", 'desde': c['desde'], 'hacia': c['hacia'],
                    'transform_matrix': [list(fila) for fila in Matrix.Translation(pos) @ rot.to_matrix().to_4x4()]})
if control:
    json.dump({'camera_angle_x': cd.angle_x, 'w': W, 'h': H, 'nota': 'Vistas de control (no entrenan). Mismas convenciones que transforms.json.',
               'frames': control}, open(os.path.join(DEST, 'control.json'), 'w'), indent=1)


def configurar_dispositivo():
    sc.render.engine = 'CYCLES'; sc.cycles.samples = MUESTRAS or SP.get('muestras', 64); sc.cycles.use_denoising = True
    sc.render.use_persistent_data = True   # no reconstruye la escena (BVH, texturas) en cada vista
    cp = bpy.context.preferences.addons['cycles'].preferences
    for tipo in ([DISP] if DISP else ['METAL', 'OPTIX', 'CUDA']):
        if tipo == 'CPU': break
        try:
            cp.compute_device_type = tipo; cp.refresh_devices()
            gpus = [d for d in cp.devices if d.type == tipo]
            if not gpus: continue
            for d in cp.devices: d.use = d.type == tipo
            sc.cycles.device = 'GPU'
            if tipo == 'OPTIX': sc.cycles.denoiser = 'OPTIX'
            print(f'[splat] dispositivo {tipo}: {[d.name for d in gpus]}'); return tipo
        except TypeError:
            continue
    if DISP and DISP != 'CPU': raise SystemExit(f'[splat] ERROR: no hay dispositivo {DISP}')
    sc.cycles.device = 'CPU'; print('[splat] dispositivo CPU'); return 'CPU'


if RENDER:
    import time
    disp = configurar_dispositivo()
    os.makedirs(os.path.join(DEST, 'control'), exist_ok=True)
    trabajo = [] if SOLO_CONTROL else [(i, f) for i, f in enumerate(frames) if DESDE <= i < HASTA]
    if CONTROL: trabajo += [(None, f) for f in control]
    t0, hechos, log = time.time(), 0, open(os.path.join(DEST, 'render_log.csv'), 'a')
    for i, f in trabajo:
        ruta = os.path.join(DEST, f['file_path'])
        if os.path.exists(ruta): continue   # reanudable
        cam.matrix_world = Matrix(f['transform_matrix'])
        r.filepath = ruta; t1 = time.time(); bpy.ops.render.render(write_still=True, scene=sc.name); hechos += 1
        log.write(f"{f['file_path']},{disp},{sc.cycles.samples},{time.time() - t1:.2f}\n"); log.flush()
        print(f"[splat] {f['file_path']} {time.time() - t1:.1f} s · {hechos}/{len(trabajo)} · media {(time.time() - t0) / hechos:.1f} s/vista")
