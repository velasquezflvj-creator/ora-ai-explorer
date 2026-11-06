"""Prepara los recursos del exterior conceptual del apartamento 102 (modelo/exterior/).

Fuentes (descargadas aparte; no se versionan los originales):
  - HDRI «park» de Poly Haven (CC0), en la selección de pmndrs/assets (CC0): src/hdri/park.hdr
  - ez-tree de Daniel Greenheck (MIT): hojas en src/app/public/textures/leaves/*.png y corteza
    Bark013 de ambientCG (CC0) en src/app/public/textures/bark/Bark013_1K-JPG/

Uso: python3 tools/preparar_exterior.py <pmndrs-assets> <ez-tree> modelo/exterior
"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image

PM, EZ, OUT = map(Path, sys.argv[1:4]); OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'parque.hdr').write_bytes((PM / 'src/hdri/park.hdr').read_bytes())
for n in ('oak', 'ash'):
    Image.open(EZ / f'src/app/public/textures/leaves/{n}.png').convert('RGBA').resize((512, 512), Image.LANCZOS).save(OUT / f'hoja_{n}.png', optimize=True)
B = EZ / 'src/app/public/textures/bark/Bark013_1K-JPG'
for k, src in (('color', 'Color'), ('normal', 'NormalGL'), ('rough', 'Roughness')):
    Image.open(B / f'Bark013_1K-JPG_{src}.jpg').resize((512, 512), Image.LANCZOS).save(OUT / f'corteza_{k}.jpg', quality=82)


def leer_hdr(p):
    b = p.read_bytes(); i = b.index(b'\n\n'); rest = b[i + 2:]; j = rest.index(b'\n'); hdr = rest[:j].decode(); data = rest[j + 1:]
    H, W = int(hdr.split()[1]), int(hdr.split()[3]); out = np.zeros((H, W, 4), np.uint8); k = 0
    for y in range(H):
        k += 4
        for c in range(4):
            x = 0
            while x < W:
                n = data[k]; k += 1
                if n > 128:
                    n -= 128; out[y, x:x + n, c] = data[k]; k += 1
                else:
                    out[y, x:x + n, c] = np.frombuffer(data[k:k + n], np.uint8); k += n
                x += n
    e = out[..., 3].astype(np.int32) - 136
    return (out[..., :3].astype(np.float32) * np.ldexp(1.0, e)[..., None]).sum(2)


L = leer_hdr(OUT / 'parque.hdr'); yy, xx = np.unravel_index(np.argmax(L), L.shape)
json.dump({'sol_uv': [round(xx / L.shape[1], 4), round(yy / L.shape[0], 4)], 'altura_camara': 4.0,
           'fuente': 'Poly Haven (CC0) vía pmndrs/assets: park.hdr, 1024 × 512'}, open(OUT / 'hdri.json', 'w'), indent=1)
print('listo', sorted(p.name for p in OUT.iterdir()))
