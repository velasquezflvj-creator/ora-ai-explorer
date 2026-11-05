"""Texturas PBR propias del apartamento 102 (color, normal y rugosidad), sin licencias de terceros.

Se generan con ruido periódico (FFT), de modo que todas repiten sin costura. Cada textura cubre una
superficie real conocida (ver ESCALA), y el visor la repite según las UV del modelo, que están en metros.

Uso: python3 tools/texturas_pbr.py modelo/texturas
"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
RNG = np.random.default_rng(102)
ESCALA = {}   # nombre -> [ancho_m, alto_m] que cubre la textura


def campo(n, m=None, beta=2.0, fx=1.0, fy=1.0, seed=None):
    """Ruido gaussiano periódico con espectro 1/f^beta; fx/fy estiran el ruido (anisotropía)."""
    m = m or n
    r = np.random.default_rng(seed) if seed is not None else RNG
    ky = np.fft.fftfreq(n)[:, None] * n / fy; kx = np.fft.fftfreq(m)[None, :] * m / fx
    k = np.sqrt(kx ** 2 + ky ** 2); k[0, 0] = 1
    spec = (r.normal(size=(n, m)) + 1j * r.normal(size=(n, m))) / k ** (beta / 2); spec[0, 0] = 0
    f = np.real(np.fft.ifft2(spec)); f -= f.mean(); f /= f.std() + 1e-9
    return f


def muestrear(f, y, x):
    """Muestreo bilineal periódico de f en coordenadas de píxel (y, x)."""
    n, m = f.shape
    y0 = np.floor(y).astype(int); x0 = np.floor(x).astype(int); fy = y - y0; fx = x - x0
    y0 %= n; x0 %= m; y1 = (y0 + 1) % n; x1 = (x0 + 1) % m
    return (f[y0, x0] * (1 - fx) * (1 - fy) + f[y0, x1] * fx * (1 - fy) + f[y1, x0] * (1 - fx) * fy + f[y1, x1] * fx * fy)


def normal_de(h, fuerza):
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * fuerza; gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * fuerza
    n = np.dstack([-gx, gy, np.ones_like(h)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
    return ((n * 0.5 + 0.5) * 255).astype(np.uint8)


def mezcla(c0, c1, t):
    t = np.clip(t, 0, 1)[..., None]
    return np.array(c0)[None, None] * (1 - t) + np.array(c1)[None, None] * t


def hexrgb(h):
    h = h.lstrip('#'); return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


LADO = {'deck': 512, 'tapete': 768, 'arte': 768}   # resolución final por textura (las demás quedan como se generan)


def guardar(nombre, color=None, normal=None, rough=None, escala=(1, 1), q=80):
    lado = LADO.get(nombre)
    def g_(im, sufijo):
        if lado and im.width > lado:
            im = im.resize((lado, int(im.height * lado / im.width)), Image.LANCZOS)
        im.save(OUT / f'{nombre}_{sufijo}.jpg', quality=q)
    if color is not None:
        g_(Image.fromarray(np.clip(color, 0, 255).astype(np.uint8)), 'color')
    if normal is not None:
        g_(Image.fromarray(normal), 'normal')
    if rough is not None:
        g_(Image.fromarray((np.clip(rough, 0, 1) * 255).astype(np.uint8)).convert('L'), 'rough')
    ESCALA[nombre] = list(escala)


N = 1024
yy, xx = np.mgrid[0:N, 0:N].astype(float)

# ------------------------------------------------------------------ travertino (corte transversal, vetas suaves horizontales)
def lineas(v, periodo, fmin, fmax, nf, seed, pot=0.8):
    """Suma de senos periódicos en v (líneas finas paralelas de frecuencias variadas)."""
    r = np.random.default_rng(seed); out = np.zeros_like(v)
    for f in r.integers(fmin, fmax, nf):
        out += np.sin(2 * np.pi * f * v / periodo + r.uniform(0, 6.3)) / f ** pot
    return out / (out.std() + 1e-9)


def travertino(seed, n=N, m=N, cA='#e9dfcf', cB='#c9b598', cC='#f3ece0', poros=True):
    """Travertino claro en corte transversal: vetas finas horizontales, ondulación suave y poros rellenos."""
    yy_, xx_ = np.mgrid[0:n, 0:m].astype(float)
    w = campo(n, m, 3.4, fx=3, seed=seed)
    v = yy_ + 9 * w + 2.5 * campo(n, m, 2.6, fx=8, seed=seed + 1)
    finas = lineas(v, n, 30, 260, 70, seed + 2)
    modul = 0.6 + 0.4 * campo(n, m, 3.0, fx=6, seed=seed + 3)      # zonas con más y menos veta
    nube = campo(n, m, 3.2, seed=seed + 4)
    t = 0.42 + 0.16 * finas * modul + 0.07 * nube
    col = mezcla(hexrgb(cA), hexrgb(cB), t)
    col += (np.array(hexrgb(cC)) - col) * (0.25 * np.clip(-finas - 1.2, 0, 1))[..., None]
    h = 0.35 * finas * modul + 0.1 * campo(n, m, 1.4, seed=seed + 5)
    rough = 0.40 + 0.04 * nube
    if poros:   # poros alargados en el sentido de las vetas, rellenos (apenas hundidos)
        p = muestrear(campo(n, m, 1.0, fx=10, fy=1, seed=seed + 6), v, xx_)
        mp = np.clip((p - 2.4) * 1.5, 0, 1)
        col = col * (1 - 0.18 * mp[..., None]); h = h - 1.2 * mp; rough = rough + 0.2 * mp
    return col, h, rough


c, h, r = travertino(11)
guardar('travertino', c, normal_de(h, 1.6), r, (1.2, 1.2))          # mesones y piezas macizas

# enchape de travertino 60 × 120 en vertical, con juntas de 2 mm (baños)
c2, h2, r2 = travertino(21, cA='#e3d8c6', cB='#c9b89e')
jx = (xx % (N / 2)) < 1.8; jy = (yy % N) < 1.8                       # 2 piezas de 0,60 × 1,20 m
junta = jx | jy
c2[junta] = hexrgb('#cfc6b8'); h2[junta] -= 2.5; r2[junta] = 0.75
guardar('travertino_enchape', c2, normal_de(h2, 1.6), r2, (1.2, 1.2))

# ------------------------------------------------------------------ piso: porcelanato tipo piedra caliza cálida 60 × 120
w = campo(N, N, 3.0, seed=31); nube = campo(N, N, 2.6, seed=32); fino = campo(N, N, 1.3, seed=33)
t = 0.5 + 0.18 * nube + 0.08 * muestrear(campo(N, N, 2.0, fx=12, seed=34), yy + 10 * w, xx)
col = mezcla(hexrgb('#e2d9cb'), hexrgb('#cdc1ae'), t) * (1 + 0.025 * fino[..., None])
# cada pieza con un leve cambio de tono, como en una obra real
pieza = ((xx // (N / 2)).astype(int) * 7 + (yy // N).astype(int) * 3) % 5
col *= (1 + (pieza[..., None] - 2) * 0.012)
h = 0.25 * nube + 0.15 * fino; rough = 0.55 + 0.06 * nube
junta = ((xx % (N / 2)) < 2.0) | ((yy % N) < 2.0)
col[junta] = hexrgb('#c4baab'); h[junta] -= 2.0; rough[junta] = 0.8
guardar('piso_piedra', col, normal_de(h, 1.2), rough, (1.2, 1.2))

# ------------------------------------------------------------------ roble claro natural (chapa, fibra vertical)
def roble(seed, base='#c9a97f', oscuro='#a3805a', claro='#dcc3a0', n=1024, m=512):
    """Chapa de roble claro de corte rift: fibra recta vertical con líneas de crecimiento y poros finos."""
    yy_, xx_ = np.mgrid[0:n, 0:m].astype(float)
    w = campo(n, m, 4.2, fx=1, fy=10, seed=seed)
    u = xx_ + 3.5 * w
    crec = lineas(u, m, 18, 120, 40, seed + 1, pot=0.6)
    crec = np.sign(crec) * np.abs(crec) ** 0.7
    poros = campo(n, m, 1.0, fx=1, fy=40, seed=seed + 2)
    mancha = campo(n, m, 3.0, fx=1, fy=3, seed=seed + 3)
    t = 0.48 + 0.12 * crec + 0.06 * mancha
    col = mezcla(hexrgb(claro), hexrgb(oscuro), t)
    pm = np.clip(-poros - 1.4, 0, 1)
    col = col * (1 - 0.25 * pm[..., None]); col = col * 0.7 + np.array(hexrgb(base)) * 0.3
    h = 0.25 * crec - 1.2 * pm
    rough = 0.58 + 0.12 * pm
    return col, h, rough


c, h, r = roble(41)
guardar('roble', c, normal_de(h, 1.1), r, (0.6, 1.2))

# ------------------------------------------------------------------ laca mate (gabinetes): piel de naranja muy fina
h = campo(512, 512, 1.6, seed=51)
guardar('laca_mate', None, normal_de(h * 0.25, 1.0), 0.62 + 0.03 * h, (0.4, 0.4))

# ------------------------------------------------------------------ yeso / pintura de muros: ondulación casi imperceptible
h = campo(512, 512, 2.8, seed=61) + 0.15 * campo(512, 512, 1.2, seed=62)
guardar('yeso', None, normal_de(h * 0.35, 1.0), 0.88 + 0.03 * h, (1.5, 1.5))

# ------------------------------------------------------------------ bouclé (bucles de lana) y lino
M = 512
h = np.zeros((M, M))
k = RNG.integers(0, M, size=(5200, 2)); rad = RNG.uniform(2.2, 4.2, 5200)
yy5, xx5 = np.mgrid[0:M, 0:M]
for (cy, cx), rr in zip(k, rad):
    y0, y1 = int(cy - 6), int(cy + 7); x0, x1 = int(cx - 6), int(cx + 7)
    ys = np.arange(y0, y1) % M; xs = np.arange(x0, x1) % M
    dy = (np.arange(y0, y1) - cy)[:, None]; dx = (np.arange(x0, x1) - cx)[None, :]
    d = np.sqrt(dx ** 2 + dy ** 2)
    bucle = np.exp(-((d - rr * 0.7) ** 2) / 1.6)       # anillo: el bucle de la lana
    h[np.ix_(ys, xs)] = np.maximum(h[np.ix_(ys, xs)], bucle)
h += 0.15 * campo(M, M, 1.5, seed=71)
guardar('boucle', None, normal_de(h, 2.2), 0.95 - 0.05 * h, (0.12, 0.12))

tr = np.sin(xx5 / M * 2 * np.pi * 96) * np.sin(yy5 / M * 2 * np.pi * 96)          # tejido tafetán
slub = campo(M, M, 1.8, fx=1, fy=20, seed=81)
h = 0.6 * np.abs(tr) + 0.3 * slub
guardar('lino', None, normal_de(h, 1.4), 0.92 + 0.03 * slub, (0.25, 0.25))

# ------------------------------------------------------------------ tapete de lana con líneas onduladas en relieve (referencia de la habitación)
M = 1024
w = campo(M, M, 3.2, seed=91)
yy6, xx6 = np.mgrid[0:M, 0:M].astype(float)
ondas = np.sin((yy6 + 40 * np.sin(xx6 / M * 2 * np.pi * 2) + 18 * w) / M * 2 * np.pi * 34)
lana = campo(M, M, 1.1, seed=92)
t = 0.5 + 0.25 * np.sign(ondas) * np.abs(ondas) ** 0.4 + 0.08 * lana
col = mezcla(hexrgb('#b7ada0'), hexrgb('#8e857a'), t)
guardar('tapete', col, normal_de(0.6 * ondas + 0.4 * lana, 1.6), None, (1.0, 1.0))

# ------------------------------------------------------------------ deck del balcón (madera de exterior, tablas de 0,14 m)
M = 1024
c, h, r = roble(101, base='#9c7a58', oscuro='#7a5a3e', claro='#b8936c', n=M, m=M)
tabla = (xx6 % (M / 8.57)) < 3.0                      # 1,2 m / 0,14 m ≈ 8,57 tablas
c[tabla] = hexrgb('#3a2d22'); h[tabla] -= 3; r = np.where(tabla, 0.9, r + 0.1)
guardar('deck', c, normal_de(h, 1.0), r, (1.2, 1.2))

# ------------------------------------------------------------------ arte abstracto sobrio (lienzo con arcos en relieve)
M = 1024
yy7, xx7 = np.mgrid[0:M, 0:M].astype(float) / M
lienzo = campo(M, M, 1.2, seed=111) * 0.5 + campo(M, M, 2.6, seed=112)
col = mezcla(hexrgb('#ece5d8'), hexrgb('#ddd2c0'), 0.5 + 0.12 * lienzo)
h = 0.2 * campo(M, M, 1.1, seed=113)
formas = [((0.36, 0.62), 0.30, '#c8b8a0', 0.0), ((0.66, 0.40), 0.22, '#b9a58a', 0.7), ((0.50, 0.52), 0.42, None, 0.0)]
for (cx, cy), r, c, rot in formas:
    d = np.sqrt((xx7 - cx) ** 2 + (yy7 - cy) ** 2)
    if c:
        mask = np.clip((r - d) * 300, 0, 1) * (yy7 > cy - 0.02 + 0.2 * rot * (xx7 - cx))
        col = col * (1 - mask[..., None]) + np.array(hexrgb(c)) * mask[..., None] * (0.97 + 0.03 * lienzo[..., None])
        h += 1.6 * mask
    else:
        ring = np.exp(-((d - r) * 220) ** 2)
        col = col * (1 - 0.25 * ring[..., None]) + np.array(hexrgb('#8f7d66')) * 0.25 * ring[..., None]; h += 0.8 * ring
linea = np.exp(-((yy7 - 0.80 + 0.05 * np.sin(xx7 * 6)) * 400) ** 2) * (xx7 > 0.15) * (xx7 < 0.85)
col = col * (1 - 0.6 * linea[..., None]) + np.array(hexrgb('#2c2925')) * 0.6 * linea[..., None]
guardar('arte', col, normal_de(h, 2.0), 0.9 - 0.1 * linea, (1.0, 1.0))

json.dump(ESCALA, open(OUT / 'escala.json', 'w'), indent=1)
print('texturas', sorted(ESCALA), sum(f.stat().st_size for f in OUT.glob('*.jpg')) // 1024, 'KB')
