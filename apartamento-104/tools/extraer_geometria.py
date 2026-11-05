"""Extrae la geometría verificable del apartamento 104 (Torre 1, Pinares Ártica Home)
desde el DXF obtenido del DWG de planos arquitectónicos.

Uso:
    python3 extraer_geometria.py <planos.dxf> <ruta_ezdxf_src_o_vacio> <salida.json>

Requisitos: ezdxf (lectura DXF) y numpy. El DWG original (AutoCAD 2018, AC1032) se
convierte a DXF con LibreDWG:  dwg2dxf -y -o planos.dxf PLANO_ARQUITECTONICOS_...dwg

Criterio: todo lo que sale de este script proviene de entidades del plano (capas MUROS,
VENTANAS, PUERTA, MOBILIARIO 1, TEXTO 1 y cotas). Las alturas NO existen en el DWG y no
se escriben aquí: se declaran como pendientes en el JSON.
"""
import json
import sys

import numpy as np

if len(sys.argv) > 2 and sys.argv[2]:
    sys.path.insert(0, sys.argv[2])
from ezdxf import recover  # noqa: E402
from matplotlib.path import Path  # noqa: E402

DXF, OUT = sys.argv[1], sys.argv[3]
OX, OY = 1155500.0, 1023100.0          # traslación de trabajo (coordenadas del plano)
X0, Y0 = 83.8812, 5.0854               # esquina exterior suroeste del apartamento
W, H = 91.9812 - X0, 12.6854 - Y0      # 8.100 × 7.600 m (cara exterior a cara exterior)
CELL = 0.005                           # malla de 5 mm para áreas y descomposición de muros

doc, _ = recover.readfile(DXF)
msp = doc.modelspace()


def loc(x, y):
    return (round(x - OX - X0, 4), round(y - OY - Y0, 4))


def in_apto(pts, pad=0.02):
    return any(-pad <= x <= W + pad and -pad <= y <= H + pad for x, y in pts)


# ------------------------------------------------------------------ identificación
ident = {}
for e in msp.query('TEXT MTEXT'):
    txt = (e.plain_text() if e.dxftype() == 'MTEXT' else e.dxf.text).strip()
    p = e.dxf.insert
    if txt in ('APTO 104', 'AREA 60.01m2', 'PLANTA  PISO 1 AL PISO 20', 'TORRE 1'):
        ident.setdefault(txt, []).append({'handle': e.dxf.handle, 'capa': e.dxf.layer, 'xy_plano': [round(p.x, 3), round(p.y, 3)]})

# ------------------------------------------------------------------ muros (capa MUROS)
walls = []
for e in msp.query('LWPOLYLINE[layer=="MUROS"]'):
    pts = [loc(x, y) for x, y in e.get_points('xy')]
    if e.closed and in_apto(pts):
        walls.append({'handle': e.dxf.handle, 'poligono': pts})

# ------------------------------------------------------------------ ventanas (marcos cerrados en VENTANAS)
windows = []
for e in msp.query('LWPOLYLINE[layer=="VENTANAS"]'):
    pts = [loc(x, y) for x, y in e.get_points('xy')]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    if not in_apto(pts) or min(xs) < -0.01 or max(xs) > W + 0.01:
        continue
    # vano completo: rectángulo del espesor del muro (0.15) y ancho ≥ 0.9 m
    if (abs(h - 0.15) < 0.003 and w > 0.9) or (abs(w - 0.15) < 0.003 and h > 0.9):
        windows.append({'handle': e.dxf.handle, 'x0': min(xs), 'y0': min(ys), 'x1': max(xs), 'y1': max(ys),
                        'ancho': round(max(w, h), 3), 'fachada': 'sur' if h < w else 'este'})

# ------------------------------------------------------------------ cotas dentro del apartamento
dims = []
for e in msp.query('DIMENSION'):
    try:
        a, b = loc(e.dxf.defpoint2.x, e.dxf.defpoint2.y), loc(e.dxf.defpoint3.x, e.dxf.defpoint3.y)
        if not (in_apto([a], 0.06) and in_apto([b], 0.06)):
            continue
        dims.append({'handle': e.dxf.handle, 'capa': e.dxf.layer, 'a': a, 'b': b,
                     'medida': round(float(e.get_measurement()), 4), 'texto': e.dxf.get('text', '') or None})
    except Exception:
        pass

# ------------------------------------------------------------------ rótulos de espacios
labels = []
for e in msp.query('TEXT MTEXT'):
    p = loc(e.dxf.insert.x, e.dxf.insert.y)
    txt = (e.plain_text() if e.dxftype() == 'MTEXT' else e.dxf.text).strip()
    if e.dxf.layer in ('TEXTO1', 'TEXTO 1') and in_apto([p], 0) and txt:
        labels.append({'texto': txt, 'xy': p, 'handle': e.dxf.handle})

# ------------------------------------------------------------------ vanos de puerta (derivados de muros y cotas)
# Coordenadas locales: cada vano es el hueco entre dos tramos de muro medido en el plano.
O = lambda x, y: (round(x - X0, 4), round(y - Y0, 4))  # noqa: E731
doors = [
    {'id': 'entrada', 'tipo': 'P2', 'ancho_plano': 1.00, 'rect': [*O(84.0312, 12.5354), *O(85.0315, 12.6854)], 'eje': 'x',
     'hoja': {'bisagra': O(84.059, 12.555), 'abre_hacia': 'interior', 'radio': 0.954}, 'fuente': 'cota 1.0004 + arco PUERTA'},
    {'id': 'bano_social', 'tipo': 'P1', 'ancho_plano': 0.80, 'rect': [*O(86.6562, 8.8354), *O(87.4562, 8.9854)], 'eje': 'x', 'fuente': 'cota 0.80'},
    {'id': 'alcoba_2', 'tipo': 'P1', 'ancho_plano': 0.80, 'rect': [*O(88.3562, 7.8354), *O(89.1562, 7.9854)], 'eje': 'x', 'fuente': 'hueco entre muros (cota 1.70 + muro 89.1562)'},
    {'id': 'alcoba_3', 'tipo': 'P1', 'ancho_plano': 0.80, 'rect': [*O(89.5362, 8.0354), *O(89.6862, 8.8354)], 'eje': 'y', 'fuente': 'cota 0.80 entre remate de muro (89.5362–89.6862) y muro norte'},
    {'id': 'alcoba_principal', 'tipo': 'P1', 'ancho_plano': 0.80, 'rect': [*O(89.3262, 8.9854), *O(89.5362, 9.8354)], 'eje': 'y', 'fuente': 'cota 0.85 (vano), hoja 0.80'},
    {'id': 'bano_principal', 'tipo': 'P1', 'ancho_plano': 0.80, 'rect': [*O(89.1762, 9.9854), *O(89.3262, 10.7854)], 'eje': 'y', 'fuente': 'cota 0.80'},
]
passages = [
    {'id': 'paso_circulacion', 'rect': [*O(86.5062, 7.9854), *O(86.6562, 8.8354)], 'fuente': 'cota 0.85, sin hoja dibujada'},
    {'id': 'ropas_abierta', 'rect': [*O(86.5062, 10.2254), *O(86.6562, 12.0354)], 'fuente': 'muro interrumpido; zona de ropas abierta a cocina'},
]

# ------------------------------------------------------------------ rasterizado a 5 mm
nx, ny = int(round(W / CELL)), int(round(H / CELL))
cx = (np.arange(nx) + 0.5) * CELL
cy = (np.arange(ny) + 0.5) * CELL
gx, gy = np.meshgrid(cx, cy)
pts_grid = np.column_stack([gx.ravel(), gy.ravel()])


def fill(poly):
    # Path(closed=True) descarta el último vértice (lo usa como CLOSEPOLY): se repite el primero.
    return Path(list(poly) + [poly[0]], closed=True).contains_points(pts_grid).reshape(ny, nx)


def rect_mask(r):
    x0, y0, x1, y1 = r
    return (gx >= x0) & (gx <= x1) & (gy >= y0) & (gy <= y1)


wall = np.zeros((ny, nx), bool)
for w_ in walls:
    wall |= fill(w_['poligono'])
win = np.zeros_like(wall)
for w_ in windows:
    win |= rect_mask([w_['x0'], w_['y0'], w_['x1'], w_['y1']])


def flood(blocked, seed):
    from collections import deque
    out = np.zeros_like(blocked)
    sx, sy = int(seed[0] / CELL), int(seed[1] / CELL)
    if blocked[sy, sx]:
        raise ValueError(f'semilla dentro de muro {seed}')
    q = deque([(sy, sx)]); out[sy, sx] = True
    while q:
        j, i = q.popleft()
        for dj, di in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a, b = j + dj, i + di
            if 0 <= a < ny and 0 <= b < nx and not out[a, b] and not blocked[a, b]:
                out[a, b] = True; q.append((a, b))
    return out


entrada = rect_mask(doors[0]['rect'])
apto = flood(wall | win | entrada, (1.4, 1.5))          # semilla en la sala
cells_open = [rect_mask(d['rect']) for d in doors] + [rect_mask(p['rect']) for p in passages]
closed = wall | win
for m in cells_open:
    closed |= m
seeds = {
    'social': ('Sala · comedor · cocina', (1.4, 1.5)),
    'ropas': ('Ropas', (3.4, 6.2)),
    'circulacion': ('Circulación', (4.1, 3.3)),
    'bano_social': ('Baño', (3.0, 4.4)),
    'alcoba_2': ('Alcoba', (3.9, 1.5)),
    'alcoba_3': ('Alcoba', (6.6, 1.8)),
    'alcoba_principal': ('Alcoba principal', (6.6, 5.6)),
    'bano_principal': ('Baño de alcoba', (4.6, 5.8)),
}
# ------------------------------------------------------------------ descomposición de muros en rectángulos (para el modelo 3D)
def rectangles(mask):
    m = mask.copy(); out = []
    for j in range(ny):
        i = 0
        while i < nx:
            if not m[j, i]:
                i += 1; continue
            i1 = i
            while i1 < nx and m[j, i1]:
                i1 += 1
            j1 = j + 1
            while j1 < ny and m[j1, i:i1].all():
                j1 += 1
            m[j:j1, i:i1] = False
            out.append([round(i * CELL, 4), round(j * CELL, 4), round(i1 * CELL, 4), round(j1 * CELL, 4)])
            i = i1
    return out


rooms = []
for rid, (name, seed) in seeds.items():
    m = flood(closed, seed)
    ys_, xs_ = np.nonzero(m)
    rooms.append({'id': rid, 'nombre': name, 'semilla': seed, 'area_neta_m2': round(m.sum() * CELL * CELL, 2),
                  'piso_rectangulos': rectangles(m),
                  'caja': [round(xs_.min() * CELL, 3), round(ys_.min() * CELL, 3), round((xs_.max() + 1) * CELL, 3), round((ys_.max() + 1) * CELL, 3)]})

wall_rects = rectangles(wall)

# ------------------------------------------------------------------ aparatos fijos (posición del plano, capa MOBILIARIO 1)
fixtures = [
    {'id': 'meson_cocina', 'tipo': 'meson', 'rect': [*O(85.0315, 12.0354), *O(86.5062, 12.5354)], 'fuente': 'MOBILIARIO 1'},
    {'id': 'lavaplatos', 'tipo': 'lavaplatos', 'centro': O(85.29, 12.30), 'fuente': 'MOBILIARIO 1'},
    {'id': 'estufa', 'tipo': 'estufa', 'rect': [*O(85.80, 12.06), *O(86.40, 12.48)], 'fuente': 'MOBILIARIO 1'},
    {'id': 'ducha_principal', 'tipo': 'ducha', 'rect': [*O(88.0162, 11.3754), *O(89.1762, 12.1754)], 'fuente': 'MOBILIARIO 1'},
    {'id': 'sanitario_principal', 'tipo': 'sanitario', 'rect': [*O(88.04, 10.83), *O(88.73, 11.24)], 'orientacion': 'este', 'fuente': 'MOBILIARIO 1'},
    {'id': 'lavamanos_principal', 'tipo': 'lavamanos', 'rect': [*O(88.0162, 10.14), *O(88.43, 10.66)], 'orientacion': 'este', 'fuente': 'MOBILIARIO 1'},
    {'id': 'ducha_social', 'tipo': 'ducha', 'rect': [*O(87.8662, 8.9854), *O(88.5862, 9.8354)], 'fuente': 'MOBILIARIO 1'},
    {'id': 'sanitario_social', 'tipo': 'sanitario', 'rect': [*O(87.33, 9.36), *O(87.80, 10.0754)], 'orientacion': 'sur', 'fuente': 'MOBILIARIO 1'},
    {'id': 'lavamanos_social', 'tipo': 'lavamanos', 'rect': [*O(86.70, 9.68), *O(87.20, 10.0754)], 'orientacion': 'sur', 'fuente': 'MOBILIARIO 1'},
]

thresholds = [rectangles(m)[0] for m in cells_open]
wall_area = wall.sum() * CELL * CELL
out = {
    'proyecto': 'Pinares Ártica Home', 'torre': 'Torre 1', 'apartamento': '104', 'planta': 'Piso 1 al piso 20 (planta tipo)',
    'fuente': 'PLANO_ARQUITECTONICOS_TORRES_PINARES_ARTICA_HOME.dwg (AC1032) → DXF con LibreDWG; contraste con modelo_torre_1.dwg',
    'unidades': 'metros', 'sistema_local': {'origen_plano': [OX + X0, OY + Y0], 'x': 'este', 'y': 'norte'},
    'identificacion': ident,
    'envolvente_exterior': [0, 0, round(W, 4), round(H, 4)],
    'muros_poligonos': walls, 'muros_rectangulos': wall_rects,
    'ventanas': windows, 'puertas': doors, 'umbrales': thresholds, 'pasos': passages, 'aparatos': fixtures,
    'espacios': rooms, 'rotulos': labels, 'cotas': dims,
    'areas': {
        'rotulo_plano_m2': 60.01,
        'interior_neta_m2': round(apto.sum() * CELL * CELL, 2),
        'muros_dentro_envolvente_m2': round(wall_area, 2),
        'envolvente_bruta_m2': round(W * H, 2),
        'nota': 'El plano no indica el criterio de medición del área rotulada (60.01 m²).',
    },
    'pendientes': [
        'Altura libre piso–cielo raso (no hay cortes ni fachadas en los DWG).',
        'Espesor de losa/entrepiso y nivel de piso terminado del piso modelado.',
        'Altura de puertas (dintel) y sentido de giro de puertas interiores (hojas dibujadas sin arco).',
        'Altura de antepecho y dintel de ventanas; tipo de ventanería (corrediza/proyectante).',
        'Acabados de pisos, muros, cielos y carpintería (no especificados en el DWG).',
        'Ubicación de lavadora/calentador en zona de ropas (no dibujados).',
    ],
}
json.dump(out, open(OUT, 'w'), ensure_ascii=False, indent=1)
print('muros', len(walls), 'rect', len(wall_rects), 'ventanas', len(windows), 'cotas', len(dims))
print('áreas', out['areas'])
for r in rooms:
    print(f"  {r['id']:18s} {r['area_neta_m2']:6.2f} m²  caja {r['caja']}")
