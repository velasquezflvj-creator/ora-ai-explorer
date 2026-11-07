"""Exporta la transformación de vista de Blender (AgX + look del render V3) como tabla de color 3D para el visor web.

    Blender -b --factory-startup --python blender/scripts/exportar_lut_agx.py -- apartamento-102/modelo/web/v5/lut_agx.json

La tabla mapea luz de escena lineal → color de pantalla sRGB, igual que la vista de Blender. Dominio de entrada
logarítmico: s = (log2(x / 0,18) − LO) / (HI − LO), con LO = −10 y HI = +7 (de 0,0002 a 23 veces el gris medio).
Salida: JSON { n, lo, hi, look, datos (base64 de n³×3 bytes, índice r + g·n + b·n²) }.
"""
import bpy, sys, os, json, base64
import numpy as np
out = os.path.abspath(sys.argv[sys.argv.index('--') + 1]); os.makedirs(os.path.dirname(out), exist_ok=True)
N, LO, HI = 33, -10.0, 7.0
LOOK = 'AgX - Medium High Contrast'
sc = bpy.context.scene
vs = sc.view_settings; vs.view_transform = 'AgX'; vs.look = LOOK; vs.exposure = 0.0; vs.gamma = 1.0
if hasattr(vs, 'use_white_balance'): vs.use_white_balance = False
sc.display_settings.display_device = 'sRGB'
s = np.linspace(0, 1, N, dtype=np.float32); x = 0.18 * np.power(2.0, LO + s * (HI - LO)); x[0] = 0.0
# imagen (N·N) × N: columna = r + b·N, fila = g
W, H = N * N, N
r = np.tile(np.arange(N), N); b = np.repeat(np.arange(N), N)
px = np.ones((H, W, 4), np.float32)
for g in range(N):
    px[g, :, 0] = x[r]; px[g, :, 1] = x[g]; px[g, :, 2] = x[b]
img = bpy.data.images.new('_lut', W, H, alpha=False, float_buffer=True); img.colorspace_settings.name = 'Linear Rec.709'
img.pixels[:] = px.ravel()
st = sc.render.image_settings; st.file_format = 'PNG'; st.color_depth = '16'; st.color_mode = 'RGB'
tmp = out + '.png'; img.save_render(tmp, scene=sc)
res = bpy.data.images.load(tmp); res.colorspace_settings.name = 'Non-Color'
a = np.array(res.pixels[:], np.float32).reshape(H, W, 4)[..., :3]; os.remove(tmp)
lut = np.zeros((N, N, N, 3), np.uint8)   # [b][g][r]
for g in range(N):
    fila = a[g].reshape(N, N, 3)   # [b][r]
    lut[:, g, :, :] = np.clip(np.round(fila * 255), 0, 255).astype(np.uint8)
mid = int(round((np.log2(1.0) - LO) / (HI - LO) * (N - 1)))
json.dump({'n': N, 'lo': LO, 'hi': HI, 'gris_medio': 0.18, 'vista': 'AgX', 'look': LOOK,
           'nota': 'Generada desde la gestión de color de Blender (misma vista que el render V3, sin exposición ni balance: ya vienen en las sondas y horneados)',
           'muestra_gris_medio_srgb': lut[mid, mid, mid].tolist(), 'datos': base64.b64encode(lut.tobytes()).decode()}, open(out, 'w'))
print('[lut] listo', out, 'gris medio →', lut[mid, mid, mid].tolist())
