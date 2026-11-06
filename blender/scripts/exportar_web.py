"""Exporta desde Blender los recursos del visor web de un apartamento (texturas, piso horneado y sondas).

Uso (Blender 4.2+ / 5.x, en segundo plano; no modifica el .blend de entrada):
    Blender -b blender/Apartamento_102_Render_V3.blend --python blender/scripts/exportar_web.py -- \
        blender/config/apto-102.json apartamento-102/modelo/web [--solo texturas|piso|sondas]

Salida en <destino>:
    texturas/<clave>_{color,normal,rough}.jpg + texturas/escala.json   (mismas claves que usa el visor)
    sondas/<espacio>.hdr + sondas/sondas.json                          (panoramas 360° del interior, Cycles)

Las texturas de origen son CC0 (Poly Haven, ambientCG): ver blender/recursos/descargas/CREDITOS.md.
El piso se hornea en una textura periódica de 4,8 × 4,8 m (piezas de 1,2 × 0,6 m, juntas de 1,2 mm) en la
que cada pieza toma un recorte distinto del travertino: la repetición deja de verse dentro de un espacio.
"""
import bpy, sys, os, json, math, colorsys
import numpy as np

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
CFG_PATH, DEST = argv[0], argv[1]
SOLO = argv[argv.index('--solo') + 1].split(',') if '--solo' in argv else ['texturas', 'piso', 'sondas']
SOLO_SONDAS = argv[argv.index('--sondas') + 1].split(',') if '--sondas' in argv else None
CFG = json.load(open(CFG_PATH))
ROOT = os.path.abspath(os.environ.get('ORA_ROOT') or os.path.join(os.path.dirname(CFG_PATH), '..', '..'))
R = lambda p: p if os.path.isabs(p) else os.path.join(ROOT, p)
os.makedirs(os.path.join(DEST, 'texturas'), exist_ok=True)
os.makedirs(os.path.join(DEST, 'sondas'), exist_ok=True)


# ------------------------------------------------------------------ utilidades de imagen (numpy, sin dependencias)
def leer(path, size=None):
    im = bpy.data.images.load(path)
    if size and tuple(im.size) != tuple(size):
        im.scale(*size)
    w, h = im.size
    a = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)[..., :3]
    bpy.data.images.remove(im)
    return a  # filas de abajo hacia arriba (convención de Blender), valores tal como están codificados


def guardar_jpg(a, path, calidad=86):
    h, w = a.shape[:2]
    im = bpy.data.images.new('_tmp', w, h, alpha=False)
    rgba = np.ones((h, w, 4), np.float32)
    rgba[..., :3] = np.clip(a, 0, 1)
    im.pixels[:] = rgba.ravel()
    # imagen de 8 bits: los valores se escriben tal cual, sin transformación de vista
    im.filepath_raw = path; im.file_format = 'JPEG'
    im.save(filepath=path, quality=calidad)
    bpy.data.images.remove(im)


def hsv_ajuste(a, h_shift=0.0, sat=1.0, val=1.0):
    """Igual que el nodo Hue/Saturation/Value de Blender (hue 0,5 = sin cambio)."""
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx, mn = np.max(a, axis=2), np.min(a, axis=2)
    d = mx - mn + 1e-8
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) / 6.0
    s = np.where(mx > 0, (mx - mn) / (mx + 1e-8), 0)
    v = mx
    h = (h + h_shift) % 1.0; s = np.clip(s * sat, 0, 1); v = v * val
    i = np.floor(h * 6).astype(np.int32) % 6; f = h * 6 - np.floor(h * 6)
    p, q, t = v * (1 - s), v * (1 - f * s), v * (1 - (1 - f) * s)
    out = np.zeros_like(a)
    for k, (x, y, z) in enumerate([(v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q)]):
        m = i == k
        out[..., 0][m], out[..., 1][m], out[..., 2][m] = x[m], y[m], z[m]
    return np.clip(out, 0, 1)


def a_lineal(a):
    return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)


def a_srgb(a):
    a = np.clip(a, 0, 1)
    return np.where(a <= 0.0031308, a * 12.92, 1.055 * a ** (1 / 2.4) - 0.055)


def suavizar_normal(n, fuerza):
    """Atenúa un mapa normal OpenGL hacia la normal plana (0,5, 0,5, 1)."""
    plano = np.array([0.5, 0.5, 1.0], np.float32)
    return plano + (n - plano) * fuerza


# ------------------------------------------------------------------ 1. texturas fotográficas por clave del visor
def exportar_texturas():
    escala = {}
    for clave, t in CFG['texturas'].items():
        size = (t.get('px', 1024), t.get('px', 1024))
        for canal in ('color', 'normal', 'rough'):
            src = t.get(canal)
            if not src:
                continue
            a = leer(R(src), size)
            if canal == 'color' and 'hsv' in t:   # como el nodo HSV de Blender: en espacio lineal
                hs = t['hsv']; a = a_srgb(hsv_ajuste(a_lineal(a), hs.get('hue', 0.5) - 0.5, hs.get('sat', 1), hs.get('val', 1)))
            if canal == 'normal' and 'normal' in t.get('atenuar', {}):
                a = suavizar_normal(a, t['atenuar']['normal'])
            guardar_jpg(a, os.path.join(DEST, 'texturas', f'{clave}_{canal}.jpg'))
        escala[clave] = t['metros']
        print(f'[web] textura {clave}: {t["metros"]} m')
    return escala


# ------------------------------------------------------------------ 2. piso horneado (periódico, sin repetición visible)
def hornear_piso():
    p = CFG['piso']
    PX = p['px']                         # lado de la textura
    M = p['metros']                      # lado en metros (múltiplo del módulo)
    bw, bh = p['pieza']                  # pieza en metros
    ppm = PX / M
    src_m = p['origen_metros']           # metros que cubre la textura de origen
    src_px = int(round(src_m * ppm))
    col = leer(R(p['color']), (src_px, src_px))
    rou = leer(R(p['rough']), (src_px, src_px))[..., 0]
    nor = leer(R(p['normal']), (src_px, src_px))
    hs = p.get('hsv', {})
    # mismas operaciones que el material del render V3 (espacio lineal), y vuelta a sRGB para el JPG
    col = hsv_ajuste(a_lineal(col), hs.get('hue', 0.5) - 0.5, hs.get('sat', 1), hs.get('val', 1))
    col = col * np.array(p.get('tinte', [1, 1, 1]), np.float32)
    suav = p.get('suavizar_veta', 0)
    col = a_srgb(col * (1 - suav) + np.array(p.get('tono_medio', [0.70, 0.64, 0.56]), np.float32) * suav)
    rng = np.random.default_rng(p.get('semilla', 102))
    out_c = np.zeros((PX, PX, 3), np.float32); out_r = np.zeros((PX, PX), np.float32); out_n = np.zeros((PX, PX, 3), np.float32)
    pw, ph = int(round(bw * ppm)), int(round(bh * ppm))
    filas, cols = PX // ph, PX // pw
    yy, xx = np.mgrid[0:PX, 0:PX]
    fila = yy // ph
    desfase = (fila % 2) * (pw // 2) if p.get('trabado', True) else 0
    xs = (xx + desfase) % PX
    col_idx = xs // pw
    pieza = fila * cols + col_idx                              # índice periódico de pieza
    n_piezas = filas * cols
    ox = rng.integers(0, src_px, n_piezas); oy = rng.integers(0, src_px, n_piezas)
    gira = rng.integers(0, 2, n_piezas).astype(bool)
    var = rng.uniform(*p.get('variacion', [0.95, 1.03]), n_piezas).astype(np.float32)
    lx = xs - col_idx * pw; ly = yy - fila * ph               # coordenadas locales en la pieza
    g = gira[pieza]
    lx2 = np.where(g, pw - 1 - lx, lx); ly2 = np.where(g, ph - 1 - ly, ly)
    sx = (lx2 + ox[pieza]) % src_px; sy = (ly2 + oy[pieza]) % src_px
    out_c = col[sy, sx] * var[pieza][..., None]
    out_r = rou[sy, sx]
    nn = nor[sy, sx].copy()
    nn[..., 0] = np.where(g, 1 - nn[..., 0], nn[..., 0]); nn[..., 1] = np.where(g, 1 - nn[..., 1], nn[..., 1])   # pieza girada 180°
    out_n = suavizar_normal(nn, p.get('normal_fuerza', 0.15))
    rmin, rmax = p.get('rugosidad', [0.30, 0.50])
    out_r = rmin + (rmax - rmin) * out_r
    # juntas: 1 px (≈ 2 mm a esta resolución) en el borde inferior e izquierdo de cada pieza
    junta = ((ly == 0) | (lx == 0)).astype(np.float32)
    osc = p.get('junta_oscurece', 0.22) * p.get('junta_cobertura', 0.6)
    out_c = out_c * (1 - junta[..., None] * osc)
    out_r = out_r * (1 - junta) + p.get('junta_rugosidad', 0.85) * junta
    # relieve de la junta: la normal se inclina hacia dentro en los dos píxeles vecinos
    alt = 1 - junta
    gx = (np.roll(alt, -1, axis=1) - np.roll(alt, 1, axis=1)) * 0.5
    gy = (np.roll(alt, -1, axis=0) - np.roll(alt, 1, axis=0)) * 0.5
    k = p.get('junta_relieve', 0.25)
    out_n[..., 0] = np.clip(out_n[..., 0] - gx * k, 0, 1)
    out_n[..., 1] = np.clip(out_n[..., 1] - gy * k, 0, 1)
    clave = p['clave']
    guardar_jpg(out_c, os.path.join(DEST, 'texturas', f'{clave}_color.jpg'), 88)
    guardar_jpg(np.repeat(out_r[..., None], 3, axis=2), os.path.join(DEST, 'texturas', f'{clave}_rough.jpg'), 88)
    guardar_jpg(out_n, os.path.join(DEST, 'texturas', f'{clave}_normal.jpg'), 92)
    print(f'[web] piso {clave}: {M} m, {filas}×{cols} piezas de {bw}×{bh} m, {PX}px')
    return {clave: [M, M]}


# ------------------------------------------------------------------ 3. sondas de reflexión e iluminación (Cycles, 360°)
def renderizar_sondas():
    sc = bpy.data.scenes[CFG['escena']]
    if bpy.context.window:
        bpy.context.window.scene = sc
    ox, oy = CFG['origen_plano']
    s = CFG['sondas']
    r = sc.render
    r.engine = 'CYCLES'; r.use_stamp = False; r.resolution_x, r.resolution_y = s['px']; r.resolution_percentage = 100
    r.image_settings.file_format = 'HDR'
    sc.cycles.samples = s.get('muestras', 96); sc.cycles.use_denoising = True
    try:
        cp = bpy.context.preferences.addons['cycles'].preferences
        cp.compute_device_type = 'METAL'; cp.refresh_devices()
        for d in cp.devices: d.use = d.type == 'METAL'
        sc.cycles.device = 'GPU'
    except Exception as e:
        print('[web] GPU no disponible, CPU:', e)
    cd = bpy.data.cameras.new('_sonda'); cd.type = 'PANO'
    try:
        cd.panorama_type = 'EQUIRECTANGULAR'
    except Exception:
        cd.cycles.panorama_type = 'EQUIRECTANGULAR'
    cam = bpy.data.objects.new('_sonda', cd); sc.collection.objects.link(cam); sc.camera = cam
    meta_path = os.path.join(DEST, 'sondas', 'sondas.json')
    previo = json.load(open(meta_path)) if os.path.exists(meta_path) else {}
    meta = previo.get('sondas', {}) if SOLO_SONDAS else {}
    graduadas = previo.get('gradacion_aplicada', {}) if SOLO_SONDAS else {}
    for nombre, (x, y, z) in s['puntos'].items():
        if SOLO_SONDAS and nombre not in SOLO_SONDAS:
            continue
        cam.location = (x - ox, y - oy, z)
        # Panorama equirectangular de Cycles: la cámara mira a lo largo de su −Z; rotación (90°, 0, −90°) deja
        # el centro de la imagen mirando a +X (este) y el horizonte nivelado, como espera three.js con rotación 0.
        cam.rotation_euler = (math.radians(90), 0, math.radians(-90))
        out = os.path.join(DEST, 'sondas', f'{nombre}.hdr')
        r.filepath = out
        bpy.ops.render.render(write_still=True, scene=sc.name)
        meta[nombre] = {'plano': [x, y, z], 'archivo': f'{nombre}.hdr', 'espacio': s.get('espacios', {}).get(nombre, nombre)}
        graduadas.pop(nombre, None)   # recién renderizada: aún sin gradación
        print(f'[web] sonda {nombre} en plano ({x}, {y}, {z})')
    json.dump({'px': s['px'], 'muestras': s.get('muestras', 96), 'convencion': 'centro = +X Blender (este); arriba = +Z', 'sondas': meta, 'gradacion_aplicada': graduadas},
              open(os.path.join(DEST, 'sondas', 'sondas.json'), 'w'), indent=1, ensure_ascii=False)


# ------------------------------------------------------------------ 4. gradación de las sondas (como el render V3)
def kelvin_rgb(k):
    """Color de un cuerpo negro en sRGB lineal (aproximación de Tanner Helland), normalizado a G = 1."""
    t = k / 100.0
    r = 255 if t <= 66 else 329.698727446 * (t - 60) ** -0.1332047592
    g = 99.4708025861 * math.log(t) - 161.1195681661 if t <= 66 else 288.1221695283 * (t - 60) ** -0.0755148492
    b = 255 if t >= 66 else (0 if t <= 19 else 138.5177312231 * math.log(t - 10) - 305.0447927307)
    c = a_lineal(np.clip(np.array([r, g, b], np.float32) / 255, 0, 1))
    return c / c[1]


def ajustar_sondas():
    """Aplica a los HDR de las sondas la exposición y el balance de blancos del render V3 (que Blender aplica solo
    en la vista), para que la luz que reciben los materiales en la web tenga el mismo nivel y la misma neutralidad."""
    meta_path = os.path.join(DEST, 'sondas', 'sondas.json'); meta = json.load(open(meta_path))
    aj = CFG['sondas'].get('gradacion', {'exposicion_ev': 0.8, 'balance_k': 5000})
    previos = meta.get('gradacion_aplicada', {})
    for nombre, s in meta['sondas'].items():
        if previos.get(nombre) == aj:
            continue
        ruta = os.path.join(DEST, 'sondas', s['archivo'])
        im = bpy.data.images.load(ruta); w, h = im.size
        a = np.array(im.pixels[:], np.float32).reshape(h, w, 4)
        ganancia = (2 ** aj['exposicion_ev']) / kelvin_rgb(aj['balance_k'])     # blanco de balance_k → neutro
        ganancia = ganancia / ganancia[1] * (2 ** aj['exposicion_ev'])
        a[..., :3] *= ganancia
        out = bpy.data.images.new('_sonda', w, h, alpha=False, float_buffer=True); out.pixels[:] = a.ravel()
        out.filepath_raw = ruta; out.file_format = 'HDR'; out.save()
        bpy.data.images.remove(out); bpy.data.images.remove(im)
        previos[nombre] = aj
        print(f'[web] sonda {nombre}: +{aj["exposicion_ev"]} EV, balance {aj["balance_k"]} K, ganancia {np.round(ganancia, 3).tolist()}')
    meta['gradacion_aplicada'] = previos
    json.dump(meta, open(meta_path, 'w'), indent=1, ensure_ascii=False)


escala_path = os.path.join(DEST, 'texturas', 'escala.json')
escala = json.load(open(escala_path)) if os.path.exists(escala_path) else {}
if 'texturas' in SOLO: escala.update(exportar_texturas())
if 'piso' in SOLO: escala.update(hornear_piso())
json.dump(escala, open(escala_path, 'w'), indent=1)
if 'sondas' in SOLO: renderizar_sondas()
if 'sondas' in SOLO or 'gradacion' in SOLO: ajustar_sondas()
print('[web] listo:', DEST)
