"""Propuesta de redistribución del apartamento 102 (Torre 1) — REDISEÑO CONCEPTUAL, no planta verificada.

Uso: python3 disenar_102.py <original-102-dwg.json> <salida propuesta-102.json> <plano.png> <comparacion.png>

Se conserva del DWG lo que un rediseño interior no puede mover sin cambiar el edificio:
  - envolvente 8,074 × 7,60 m: muros medianeros, muro del corredor y muro de fachada;
  - vanos de fachada (ventana de 2,449 m y dos de 1,00 m) y la puerta de acceso P2 de 1,00 m;
  - los dos ductos verticales del núcleo húmedo.
Todo lo interior (muros, baños, cocina, ropas, puertas) es PROPUESTA y se rotula así.
Sistema local: x este, y norte, metros; origen en la esquina exterior suroeste del 102.
"""
import json
import sys

import numpy as np

orig = json.load(open(sys.argv[1]))
OUT, PNG, CMP = sys.argv[2], sys.argv[3], sys.argv[4]
W, H = 8.074, 7.6

# ------------------------------------------------------------------ muros: [x0, y0, x1, y1, origen]
DWG, PRO = 'dwg', 'propuesta'
muros = [
    # envolvente (DWG)
    [0, 0, 0.15, 7.6, DWG], [7.925, 0, W, 7.6, DWG], [1.15, 7.45, 7.925, 7.6, DWG],
    [2.599, 0, 4.25, 0.15, DWG], [5.25, 0, 5.40, 0.15, DWG], [6.40, 0, 7.925, 0.15, DWG],
    # ductos verticales (DWG)
    [3.71, 5.12, 3.96, 5.37, DWG], [4.83, 4.67, 5.08, 4.97, DWG],
    # tabiques de la propuesta
    [2.599, 0.15, 2.75, 3.70, PRO],                         # sala | habitación 2 (sobre el machón de fachada)
    [5.25, 0.15, 5.40, 3.85, PRO],                          # habitación 2 | principal (sobre el machón)
    [2.75, 3.70, 2.90, 3.82, PRO], [3.70, 3.70, 5.25, 3.82, PRO],          # habitación 2 · norte (puerta 2,90–3,70)
    [2.50, 4.67, 2.75, 4.79, PRO], [3.45, 4.67, 3.85, 4.79, PRO], [4.55, 4.67, 5.55, 4.79, PRO],
    [6.30, 4.67, 6.85, 4.79, PRO], [7.75, 4.67, 7.925, 4.79, PRO],         # hall y principal · norte
    [2.50, 4.79, 2.62, 6.07, PRO], [2.50, 5.95, 3.58, 6.07, PRO],          # ropas
    [3.58, 4.79, 3.70, 7.45, PRO],                          # ropas y cocina | baño social
    [4.75, 4.79, 4.87, 7.45, PRO],                          # baño social | baño principal
    [6.65, 4.79, 6.77, 7.45, PRO],                          # baño principal | vestier
]
ventanas = [
    {'id': 'sala', 'x0': 0.15, 'y0': 0, 'x1': 2.599, 'y1': 0.15, 'ancho': 2.449, 'fachada': 'sur', 'origen': DWG},
    {'id': 'habitacion_2', 'x0': 4.25, 'y0': 0, 'x1': 5.25, 'y1': 0.15, 'ancho': 1.0, 'fachada': 'sur', 'origen': DWG},
    {'id': 'principal', 'x0': 5.40, 'y0': 0, 'x1': 6.40, 'y1': 0.15, 'ancho': 1.0, 'fachada': 'sur', 'origen': DWG},
]
# puertas: rect del vano, bisagra (x, y), ángulo de la hoja abierta (desde +x hacia +y), tipo
puertas = [
    {'id': 'entrada', 'rect': [0.15, 7.45, 1.15, 7.6], 'ancho': 1.0, 'tipo': 'batiente', 'bisagra': [0.178, 7.47], 'angulo': -80, 'origen': DWG},
    {'id': 'habitacion_2', 'rect': [2.90, 3.70, 3.70, 3.82], 'ancho': 0.8, 'tipo': 'batiente', 'bisagra': [2.92, 3.71], 'angulo': -95, 'origen': PRO},
    {'id': 'principal', 'rect': [5.25, 3.85, 5.40, 4.67], 'ancho': 0.82, 'tipo': 'batiente', 'bisagra': [5.42, 3.87], 'angulo': -90, 'origen': PRO},
    {'id': 'bano_principal', 'rect': [5.55, 4.67, 6.30, 4.79], 'ancho': 0.75, 'tipo': 'batiente', 'bisagra': [5.57, 4.79], 'angulo': 90, 'origen': PRO},
    {'id': 'bano_social', 'rect': [3.85, 4.67, 4.55, 4.79], 'ancho': 0.7, 'tipo': 'corrediza', 'origen': PRO},
    {'id': 'ropas', 'rect': [2.75, 4.67, 3.45, 4.79], 'ancho': 0.7, 'tipo': 'corrediza', 'acabado': 'oculta en el muro, al ras y con el acabado del muro', 'origen': PRO},
]
vanos = [   # pasos sin hoja
    {'id': 'vestier', 'rect': [6.85, 4.67, 7.75, 4.79], 'ancho': 0.9},
]
aparatos = [   # posición PROPUESTA (no del DWG)
    # cocina en U: mesón norte (estufa y horno) + despensa al ingreso (oeste) + barra-península con lavaplatos (sur)
    {'id': 'meson_norte', 'tipo': 'meson', 'rect': [1.50, 6.85, 2.95, 7.45]},   # arranca en 1,50: paso de 0,95 m frente a la despensa al entrar
    {'id': 'peninsula', 'tipo': 'meson', 'rect': [0.15, 4.50, 1.60, 5.40], 'barra': {'voladizo_sur': 0.30, 'altura': 0.90, 'puestos': 2}},
    {'id': 'nevera', 'tipo': 'nevera', 'rect': [2.97, 6.82, 3.58, 7.45]},
    {'id': 'lavaplatos', 'tipo': 'lavaplatos', 'centro': [1.18, 5.11]},
    {'id': 'estufa', 'tipo': 'estufa', 'rect': [1.92, 6.94, 2.52, 7.38]},
    {'id': 'ducha_social', 'tipo': 'ducha', 'rect': [3.70, 6.55, 4.75, 7.45]},
    {'id': 'sanitario_social', 'tipo': 'sanitario', 'rect': [3.70, 5.50, 4.40, 5.92]},
    {'id': 'lavamanos_social', 'tipo': 'lavamanos', 'rect': [4.30, 5.98, 4.75, 6.48]},
    {'id': 'ducha_principal', 'tipo': 'ducha', 'rect': [4.87, 6.50, 6.65, 7.45]},
    {'id': 'lavamanos_principal', 'tipo': 'lavamanos', 'rect': [4.87, 5.15, 5.40, 6.35]},
    {'id': 'sanitario_principal', 'tipo': 'sanitario', 'rect': [6.15, 5.30, 6.65, 5.72]},
    # zona de ropas junto a los ductos (antiguo cuarto del hall): lavadora-secadora apilada y lavadero, frente al sur
    {'id': 'lavadora_secadora', 'tipo': 'lavadora', 'rect': [2.62, 5.30, 3.22, 5.95]},
    {'id': 'lavadero', 'tipo': 'lavadero', 'rect': [3.22, 5.45, 3.58, 5.95]},
]
mobiliario = {   # huellas ILUSTRATIVAS (el visor las usa como obstáculo al caminar)
    'sofa': [0.15, 1.04, 1.10, 3.16], 'mesa_centro': [1.40, 1.40, 1.70, 2.80], 'tv': [2.55, 1.30, 2.599, 2.90], 'butaca': [0.20, 0.22, 1.05, 0.82],
    'lampara_sala': [0.20, 3.30, 0.48, 3.58], 'banquetas': [0.43, 4.08, 1.41, 4.46], 'despensa': [0.15, 5.40, 0.55, 6.45],
    'cama_2': [2.75, 1.05, 4.65, 2.45], 'noche_2a': [2.75, 0.62, 3.15, 1.00], 'noche_2b': [2.75, 2.50, 3.15, 2.88], 'armario_2': [3.85, 3.10, 5.25, 3.70],
    'comoda_2': [4.30, 0.17, 5.20, 0.62],
    'cama_p': [5.92, 1.75, 7.92, 3.35], 'noche_pa': [7.48, 1.32, 7.92, 1.70], 'noche_pb': [7.48, 3.40, 7.92, 3.78], 'butaca_p': [6.50, 0.22, 7.35, 0.82],
    'closet_v1': [7.35, 5.25, 7.925, 7.45], 'closet_v2': [6.77, 6.85, 7.35, 7.45],
    'balcon_sillas': [0.17, -1.45, 1.25, -0.20], 'balcon_jardinera': [2.27, -1.62, 2.57, -0.85],   # puerta corrediza al este: libre
}
ESPACIOS = [   # id, nombre, semilla
    ('social', 'Sala · cocina · barra', (1.3, 2.0)),
    ('hall', 'Hall de alcobas', (4.0, 4.2)),
    ('habitacion_2', 'Habitación 2', (4.0, 2.0)),
    ('principal', 'Habitación principal', (6.6, 2.5)),
    ('bano_principal', 'Baño principal', (5.8, 6.0)),
    ('vestier', 'Vestier', (7.3, 6.0)),
    ('bano_social', 'Baño social', (4.2, 6.2)),
    ('ropas', 'Ropas', (3.1, 5.4)),
]

# ------------------------------------------------------------------ áreas por relleno sobre una malla de 1 cm
st = 0.01
nx, ny = int(round(W / st)), int(round(H / st))
occ = np.zeros((ny, nx), bool)
def fill(r, v=True):
    x0, y0, x1, y1 = r[:4]
    occ[int(round(y0 / st)):int(round(y1 / st)), int(round(x0 / st)):int(round(x1 / st))] = v
for m in muros:
    fill(m)
for w in ventanas:
    fill([w['x0'], w['y0'], w['x1'], w['y1']])
cierres = [d['rect'] for d in puertas] + [v['rect'] for v in vanos] + [[2.599, 3.70, 2.75, 4.67]]   # el paso sala→hall separa espacios
for r in cierres:
    fill(r)
from collections import deque
lab = np.zeros((ny, nx), np.int16)
espacios = []
for k, (rid, nombre, (sx, sy)) in enumerate(ESPACIOS, 1):
    j, i = int(sy / st), int(sx / st); assert not occ[j, i], rid
    q = deque([(j, i)]); lab[j, i] = k; n = 0
    while q:
        a, b = q.popleft(); n += 1
        for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            c, d = a + da, b + db
            if 0 <= c < ny and 0 <= d < nx and not occ[c, d] and not lab[c, d]:
                lab[c, d] = k; q.append((c, d))
    ys, xs = np.nonzero(lab == k)
    # rectángulos de piso: filas agrupadas
    rects = []
    cur = None
    for row in range(ys.min(), ys.max() + 1):
        cols = np.nonzero(lab[row] == k)[0]
        if not len(cols):
            continue
        runs = np.split(cols, np.where(np.diff(cols) != 1)[0] + 1)
        key = tuple((int(r[0]), int(r[-1])) for r in runs)
        if cur and cur[0] == key:
            cur[2] = row
        else:
            if cur:
                rects += [[c0 * st, cur[1] * st, (c1 + 1) * st, (cur[2] + 1) * st] for c0, c1 in cur[0]]
            cur = [key, row, row]
    rects += [[c0 * st, cur[1] * st, (c1 + 1) * st, (cur[2] + 1) * st] for c0, c1 in cur[0]]
    rects = [[round(v, 3) for v in r] for r in rects]
    area = n * st * st
    espacios.append({'id': rid, 'nombre': nombre, 'area_neta_m2': round(area, 2), 'piso_rectangulos': rects,
                     'caja': [round(xs.min() * st, 3), round(ys.min() * st, 3), round((xs.max() + 1) * st, 3), round((ys.max() + 1) * st, 3)]})
umbrales = [r for r in cierres]
interior = sum(e['area_neta_m2'] for e in espacios) + sum((r[2] - r[0]) * (r[3] - r[1]) for r in umbrales)
muros_area = occ.sum() * st * st - sum((r[2] - r[0]) * (r[3] - r[1]) for r in umbrales)

balcon = {
    'id': 'balcon', 'estado': 'propuesta', 'verificado': False,
    'fuente': 'Propuesta de diseño (rediseño conceptual del 102). No figura en los planos DWG.',
    'rect_util': [0.15, -1.65, 2.599, 0.0], 'ancho_util': 2.449, 'fondo_util': 1.65, 'area_util_m2': round(2.449 * 1.65, 2),
    'losa': {'rect': [0.10, -1.73, 2.649, 0.0], 'espesor': 0.15, 'desnivel': 0.03},
    'baranda': {'altura': 1.05, 'tipo': 'vidrio templado con pasamanos metálico'},
    'acceso': {'tipo': 'puerta-ventana corrediza en el vano de 2,449 m de la sala', 'vano': [0.15, 0, 2.599, 0.15], 'altura': 2.10,
               'paso_libre': [1.40, 2.599], 'hojas_cerradas': [0.15, 1.40]},
    'requiere_validacion': ['diseño estructural del voladizo', 'viabilidad urbanística y modificación de licencia', 'aprobación del arquitecto del proyecto'],
}
data = {
    'proyecto': 'Pinares Ártica Home', 'torre': 'Torre 1', 'apartamento': '102', 'estado': 'rediseño conceptual / propuesta comercial',
    'rotulo': 'Propuesta de redistribución – apto 102',
    'advertencia': 'No es planta verificada ni aprobada del proyecto. Conserva del DWG la envolvente, los vanos de fachada, la puerta de acceso y los ductos; la distribución interior es una propuesta.',
    'area_rotulada_dwg_m2': 60.42, 'programa_original': '2 alcobas + estudio, 2 baños, sala-comedor, cocina, ropas (DWG)',
    'programa_propuesto': '2 habitaciones (principal con baño y vestier), 2 baños, sala con cocina en U y barra de 2 puestos (sin comedor), despensa al ingreso, ropas junto a los ductos, balcón propuesto',
    'ropas': {'ubicacion': 'antiguo cuarto junto a los ductos, con acceso desde el hall de alcobas', 'medidas': [0.96, 1.16], 'cerramiento': 'puerta corrediza oculta en el muro, al ras y con el acabado del muro', 'frente_libre_m': 0.51,
              'redes': {'desague_a_ducto_m': 0.4, 'agua_desde': 'baño social (≈1 m)', 'ventilacion': 'extracción al ducto D1'},
              'pendientes': ['confirmar con el ingeniero hidrosanitario la conexión al ducto D1 y la extracción', 'circuito eléctrico dedicado', 'impermeabilización del piso del cuarto'],
              'alternativa_descartada': 'columna junto al acceso: desagüe ≈3,2 m al ducto, sin ventilación cercana y ruido en la zona social'},
    'ingreso': {'paso_frente_a_frente_m': 0.95, 'paso_medido_m': 1.0, 'limita': 'la puerta de acceso de 1,00 m'},
    'sistema_local': orig['sistema_local'], 'envolvente_exterior': [0, 0, W, H],
    'muros_rectangulos': [m[:4] for m in muros], 'muros_origen': [m[4] for m in muros],
    'ventanas': ventanas, 'puertas': puertas, 'vanos': vanos, 'umbrales': umbrales, 'aparatos': aparatos,
    'ductos': [m[:4] for m in muros[6:8]], 'espacios': espacios, 'mobiliario': mobiliario,
    'cotas': [   # medidas principales de la propuesta (las del DWG original están en original-102-dwg.json)
        {'medida': 2.449, 'a': [0.15, 3.85], 'b': [2.599, 3.85]}, {'medida': 1.45, 'a': [0.15, 5.0], 'b': [1.60, 5.0]}, {'medida': 0.90, 'a': [1.60, 4.9], 'b': [2.50, 4.9]},
        {'medida': 0.85, 'a': [1.70, 2.0], 'b': [2.55, 2.0]}, {'medida': 1.20, 'a': [1.40, -0.3], 'b': [2.599, -0.3]}, {'medida': 0.95, 'a': [0.55, 6.65], 'b': [1.50, 6.65]}, {'medida': 1.45, 'a': [2.3, 5.40], 'b': [2.3, 6.85]},
        {'medida': 2.50, 'a': [2.75, 2.95], 'b': [5.25, 2.95]}, {'medida': 3.55, 'a': [3.6, 0.15], 'b': [3.6, 3.70]},
        {'medida': 2.525, 'a': [5.40, 3.6], 'b': [7.925, 3.6]}, {'medida': 4.52, 'a': [7.6, 0.15], 'b': [7.6, 4.67]},
        {'medida': 1.78, 'a': [4.87, 6.0], 'b': [6.65, 6.0]},
    ],
    'areas': {'interior_neta_m2': round(interior, 2), 'muros_dentro_envolvente_m2': round(muros_area, 2), 'envolvente_bruta_m2': round(W * H, 2)},
    'supuestos': {'altura_libre': 2.40, 'altura_puerta': 2.10, 'antepecho_ventana': 0.90, 'dintel_ventana': 2.10, 'tabique': 0.12},
    'original': orig, 'balcon': balcon,
}
json.dump(data, open(OUT, 'w'), ensure_ascii=False, indent=1)
for e in espacios:
    print(f"{e['nombre']:26s} {e['area_neta_m2']:6.2f} m²  caja {e['caja']}")
print('interior', data['areas'])

# ------------------------------------------------------------------ planos
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Arc, Polygon
import math
COL = {'social': '#efe6d3', 'hall': '#e6e8ea', 'habitacion_2': '#e3e7ef', 'principal': '#eae3ec', 'bano_principal': '#e0ecec',
       'vestier': '#efe8df', 'bano_social': '#e0ecec', 'ropas': '#f6e6cf'}
def plano(ax, titulo):
    for e in espacios:
        for x0, y0, x1, y1 in e['piso_rectangulos']:
            ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, color=COL[e['id']], lw=0))
    for r in umbrales:
        ax.add_patch(Rectangle((r[0], r[1]), r[2] - r[0], r[3] - r[1], color='#f4efe6', lw=0))
    x0, y0, x1, y1 = balcon['rect_util']
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc='#f6eedd', ec='#c99a3a', ls='--', lw=1.2))
    ax.text((x0 + x1) / 2, (y0 + y1) / 2, f"Balcón propuesto\n{balcon['area_util_m2']:.2f} m²".replace('.', ','), ha='center', va='center', fontsize=8, color='#8a6a2a')
    for m in muros:
        ax.add_patch(Rectangle((m[0], m[1]), m[2] - m[0], m[3] - m[1], color='#2b2a28' if m[4] == DWG else '#7a5c3a', lw=0))
    for w in ventanas:
        ax.add_patch(Rectangle((w['x0'], w['y0']), w['x1'] - w['x0'], w['y1'] - w['y0'], fc='#9cc7e6', ec='#2c6f9e', lw=.8))
    for d in puertas:
        x0, y0, x1, y1 = d['rect']
        if d['tipo'] == 'batiente':
            hx, hy = d['bisagra']; a = d['angulo']; L = d['ancho'] - 0.02
            ax.plot([hx, hx + L * math.cos(math.radians(a))], [hy, hy + L * math.sin(math.radians(a))], color='#c98b2a', lw=1.2)
            if (x1 - x0) > (y1 - y0):   # vano a lo largo de x: hoja cerrada hacia el otro extremo
                cl = 0 if abs(hx - x0) < abs(hx - x1) else 180
            else:
                cl = 90 if abs(hy - y0) < abs(hy - y1) else -90
            d_ = (a - cl + 180) % 360 - 180
            t1, t2 = (cl, cl + d_) if d_ > 0 else (cl + d_, cl)
            ax.add_patch(Arc((hx, hy), 2 * L, 2 * L, theta1=t1, theta2=t2, color='#c98b2a', lw=.7))
        else:
            ax.plot([x0, x1], [(y0 + y1) / 2] * 2, color='#c98b2a', lw=2.2)
    for a in aparatos:
        if 'rect' in a:
            x0, y0, x1, y1 = a['rect']
            ropas = a['tipo'] in ('ropas', 'lavadora', 'lavadero')
            ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc='#fbe9d0' if a['tipo'] == 'ropas' else 'white', ec='#d98c1f' if ropas else '#5f8a6a', lw=1.2 if a['tipo'] == 'ropas' else .7))
            if a['tipo'] == 'ropas':
                ax.text(x0 - 0.02, y1 + 0.06, 'Ropas', fontsize=7, color='#a35f00', weight='bold')
            if a['tipo'] == 'ducha':
                ax.plot([x0, x1], [y0, y1], color='#5f8a6a', lw=.4); ax.plot([x0, x1], [y1, y0], color='#5f8a6a', lw=.4)
        else:
            ax.add_patch(plt.Circle(a['centro'], 0.17, fc='white', ec='#5f8a6a', lw=.7))
    for k, (x0, y0, x1, y1) in mobiliario.items():
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc='none', ec='#9a8a78', lw=.6, ls='-' if not k.startswith('balcon') else ':'))
    for d in ductos_draw:
        ax.plot([d[0], d[2]], [d[1], d[3]], color='w', lw=.6); ax.plot([d[0], d[2]], [d[3], d[1]], color='w', lw=.6)
    for e in espacios:
        x0, y0, x1, y1 = e['caja']
        cx, cy = {'social': (1.25, 3.75), 'hall': (4.0, 4.24), 'ropas': (3.1, 4.95), 'vestier': (7.05, 6.2), 'bano_social': (4.22, 5.15), 'bano_principal': (5.75, 5.95)}.get(e['id'], ((x0 + x1) / 2, (y0 + y1) / 2))
        fs = 8.5 if e['area_neta_m2'] > 5 else 6.5
        nm = e['nombre'].replace(' · ', '\n') if e['id'] == 'social' else e['nombre'].replace(' ', '\n') if e['area_neta_m2'] < 5 else e['nombre']
        ax.text(cx, cy, f"{nm}\n{e['area_neta_m2']:.2f} m²".replace('.', ','), ha='center', va='center', fontsize=fs, color='#2b2a28',
                bbox=dict(fc='white', ec='none', alpha=.7, pad=1.5))
    ax.text(0.65, 7.75, 'Acceso', ha='center', fontsize=7.5, color='#555')
    ax.set_xlim(-0.4, W + 0.4); ax.set_ylim(-2.1, H + 0.45); ax.set_aspect('equal'); ax.axis('off'); ax.set_title(titulo, fontsize=11)
ductos_draw = data['ductos']
fig, ax = plt.subplots(figsize=(8.5, 9.5))
plano(ax, 'Propuesta de redistribución – apto 102 (rediseño conceptual, no planta verificada)')
ax.text(W / 2, -2.0, 'Negro: envolvente, vanos de fachada, acceso y ductos del DWG · Café: tabiques propuestos · Balcón: propuesta sin validar',
        ha='center', fontsize=7, color='#555')
plt.savefig(PNG, dpi=150, bbox_inches='tight')

fig, (a1, a2) = plt.subplots(1, 2, figsize=(16, 9))
for (p, q) in orig['segmentos']['muros']:
    a1.plot([p[0], q[0]], [p[1], q[1]], color='#2b2a28', lw=1.1)
for (p, q) in orig['segmentos']['ventanas']:
    a1.plot([p[0], q[0]], [p[1], q[1]], color='#2c6f9e', lw=.9)
for (p, q) in orig['segmentos']['aparatos']:
    a1.plot([p[0], q[0]], [p[1], q[1]], color='#4b8a4b', lw=.6)
for t, x, y in orig['rotulos']:
    if t in ('P2', '1.00'):
        continue
    a1.text(x, y, t, fontsize=8, color='#6a3d8a', ha='center')
a1.set_xlim(-0.4, W + 0.4); a1.set_ylim(-2.1, H + 0.45); a1.set_aspect('equal'); a1.axis('off')
a1.set_title('Original (DWG): 2 alcobas + estudio · 60,42 m² rotulados', fontsize=11)
plano(a2, 'Propuesta: 2 habitaciones amplias, sin estudio')
plt.savefig(CMP, dpi=120, bbox_inches='tight')
