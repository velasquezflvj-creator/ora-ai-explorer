"""Dibuja el plano de validación del apartamento 104: geometría extraída (muros, vanos,
espacios con su área) superpuesta a las líneas originales del DWG.

Uso: python3 plano_validacion.py <geometria-104.json> <salida.png> [lineas_originales.json]
`lineas_originales.json` es el volcado de entidades del DXF (opcional) para superponerlas.
"""
import json
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Polygon, Rectangle  # noqa: E402

g = json.load(open(sys.argv[1]))
OX0, OY0 = g['sistema_local']['origen_plano']
fig, ax = plt.subplots(figsize=(12, 11.4), dpi=150)
ax.set_facecolor('#fbfaf6')

if len(sys.argv) > 3:   # líneas originales del DWG (gris fino)
    raw = json.load(open(sys.argv[3]))
    sx, sy = OX0 - 1155500.0, OY0 - 1023100.0
    for layer, ents in raw.items():
        if layer.startswith('__'):
            continue
        for e in ents:
            if e['t'] in ('LINE', 'LWPOLYLINE') and len(e['pts']) > 1:
                xs = [p[0] - sx for p in e['pts']]; ys = [p[1] - sy for p in e['pts']]
                if e.get('closed'):
                    xs.append(xs[0]); ys.append(ys[0])
                ax.plot(xs, ys, lw=.35, color='#9a9a9a', zorder=1)

palette = ['#e9dcc0', '#d9e4d3', '#d6dce8', '#ead2cf', '#e3d9ea', '#d2e5e4', '#efe6c9', '#dcd6cd']
for i, r in enumerate(g['espacios']):
    x0, y0, x1, y1 = r['caja']
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, color=palette[i % 8], alpha=.55, zorder=0, lw=0))
    cx, cy = r['semilla']
    ax.text(cx, cy, f"{r['nombre']}\n{r['area_neta_m2']:.2f} m²", ha='center', va='center', fontsize=8.5, color='#2b2b2b', zorder=6,
            bbox=dict(boxstyle='round,pad=.25', fc='white', ec='none', alpha=.8))
for w in g['muros_rectangulos']:
    x0, y0, x1, y1 = w
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, color='#2d2a26', zorder=3, lw=0))
for w in g['ventanas']:
    ax.add_patch(Rectangle((w['x0'], w['y0']), w['x1'] - w['x0'], w['y1'] - w['y0'], fc='#8fc1e3', ec='#1f6a9a', lw=.8, zorder=4))
    ax.text((w['x0'] + w['x1']) / 2, (w['y0'] + w['y1']) / 2 + (-.28 if w['fachada'] == 'sur' else 0) , f"V {w['ancho']:.2f}",
            ha='center', va='center', fontsize=7, color='#1f6a9a', rotation=0 if w['fachada'] == 'sur' else 90, zorder=6)
for d in g['puertas']:
    x0, y0, x1, y1 = d['rect']
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc='#f0b54a', ec='#a8711a', lw=.8, zorder=4))
    ax.text((x0 + x1) / 2, (y0 + y1) / 2, f"{d['tipo']} {d['ancho_plano']:.2f}", fontsize=6.5, color='#7a4d06', zorder=7,
            ha='center', va='center', rotation=90 if d['eje'] == 'y' else 0,
            bbox=dict(boxstyle='round,pad=.1', fc='white', ec='none', alpha=.75))
for p in g['pasos']:
    x0, y0, x1, y1 = p['rect']
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc='none', ec='#a8711a', lw=.8, ls='--', zorder=4))
for f in g['aparatos']:
    if 'rect' in f:
        x0, y0, x1, y1 = f['rect']
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc='none', ec='#5b7a4a', lw=.9, zorder=5))
# cotas generales
W, H = g['envolvente_exterior'][2:]
ax.annotate('', (0, -0.35), (W, -0.35), arrowprops=dict(arrowstyle='<->', lw=.8))
ax.text(W / 2, -0.5, f'{W:.2f} m (cara exterior a cara exterior)', ha='center', va='top', fontsize=8)
ax.annotate('', (W + 0.35, 0), (W + 0.35, H), arrowprops=dict(arrowstyle='<->', lw=.8))
ax.text(W + 0.5, H / 2, f'{H:.2f} m', rotation=90, va='center', fontsize=8)
ax.text(0.3, H + 0.15, 'Corredor / acceso ↑', fontsize=8, color='#555')
ax.set_xlim(-0.6, W + 1.0); ax.set_ylim(-0.9, H + 0.5)
ax.set_aspect('equal'); ax.set_xticks(range(0, 9)); ax.set_yticks(range(0, 8)); ax.grid(lw=.2, color='#cccccc')
a = g['areas']
ax.set_title(f"Apto 104 · Torre 1 · Pinares Ártica Home — geometría extraída del DWG (gris = líneas originales)\n"
             f"Interior neta {a['interior_neta_m2']} m² · muros {a['muros_dentro_envolvente_m2']} m² · rótulo del plano {a['rotulo_plano_m2']} m²",
             fontsize=9.5)
fig.savefig(sys.argv[2], bbox_inches='tight')
print(sys.argv[2])
