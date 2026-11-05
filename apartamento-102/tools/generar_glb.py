"""Genera el modelo 3D (GLB) de la PROPUESTA DE REDISTRIBUCIÓN del apartamento 102 (Torre 1).

Uso: python3 generar_glb.py <propuesta-102.json> <salida.glb>

REDISEÑO CONCEPTUAL / PROPUESTA COMERCIAL: no es planta verificada del proyecto.
Del DWG se conservan la envolvente (medianeros, corredor, fachada), los vanos de fachada, la puerta
de acceso y los ductos (nodo ARQ_Muros, categoria «verificado»). Los tabiques, baños, cocina, ropas y
puertas interiores son de la propuesta (categoria «propuesta», grupo «rediseno»). Mobiliario y
acabados son ilustrativos. Las primitivas y los materiales son los del modelo del apartamento 104.
"""
import json
from pathlib import Path
import math
import struct
import sys

import numpy as np

g = json.load(open(sys.argv[1]))
OUT = sys.argv[2]
PROP = g['balcon']                                                  # balcón propuesto (NO proviene del DWG)
SALA_V = next(w for w in g['ventanas'] if w['id'] == 'sala')       # ventana de la sala (2,449 m)
W, H = g['envolvente_exterior'][2:]

# Supuestos de visualización (NO provienen del DWG)
SUP = {'altura_libre': 2.40, 'losa': 0.12, 'altura_puerta': 2.10, 'antepecho_ventana': 0.90, 'dintel_ventana': 2.10}
ALT = SUP['altura_libre']


def P(x, y):
    """Planta local (x este, y norte, m) → escena glTF (X este, Z sur, centrada)."""
    return x - W / 2, H / 2 - y


# ------------------------------------------------------------------ primitivas
class Mesh:
    def __init__(self):
        self.parts = {}   # material → [pos, nor, uv, idx]

    def _get(self, mat):
        return self.parts.setdefault(mat, [[], [], [], []])

    def quad(self, mat, a, b, c, d, n, uvs):
        pos, nor, uv, idx = self._get(mat)
        base = len(pos)
        pos += [a, b, c, d]; nor += [n] * 4; uv += uvs
        idx += [base, base + 1, base + 2, base, base + 2, base + 3]

    def box(self, mat, x0, y0, z0, x1, y1, z1, faces='all'):
        """Caja alineada a ejes en coordenadas de escena (y vertical). UV en metros."""
        x0, x1 = min(x0, x1), max(x0, x1); y0, y1 = min(y0, y1), max(y0, y1); z0, z1 = min(z0, z1), max(z0, z1)
        F = {
            'px': ([x1, y0, z1], [x1, y0, z0], [x1, y1, z0], [x1, y1, z1], [1, 0, 0], [(z1, y0), (z0, y0), (z0, y1), (z1, y1)]),
            'nx': ([x0, y0, z0], [x0, y0, z1], [x0, y1, z1], [x0, y1, z0], [-1, 0, 0], [(z0, y0), (z1, y0), (z1, y1), (z0, y1)]),
            'py': ([x0, y1, z1], [x1, y1, z1], [x1, y1, z0], [x0, y1, z0], [0, 1, 0], [(x0, z1), (x1, z1), (x1, z0), (x0, z0)]),
            'ny': ([x0, y0, z0], [x1, y0, z0], [x1, y0, z1], [x0, y0, z1], [0, -1, 0], [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]),
            'pz': ([x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1], [0, 0, 1], [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]),
            'nz': ([x1, y0, z0], [x0, y0, z0], [x0, y1, z0], [x1, y1, z0], [0, 0, -1], [(-x1, y0), (-x0, y0), (-x0, y1), (-x1, y1)]),
        }
        for k, (a, b, c, d, n, uv) in F.items():
            if faces == 'all' or k in faces:
                self.quad(mat, a, b, c, d, n, [list(u) for u in uv])

    def tris(self, mat, P_, N_, U_, T_):
        """Añade triángulos y corrige el sentido de cada uno según las normales de vértice."""
        pos, nor, uv, idx = self._get(mat)
        base = len(pos)
        pos += P_; nor += N_; uv += U_
        Pa = np.array(P_, float); Na = np.array(N_, float)
        for a, b, c in T_:
            gn = np.cross(Pa[b] - Pa[a], Pa[c] - Pa[a])
            if np.dot(gn, Na[a] + Na[b] + Na[c]) < 0:
                b, c = c, b
            idx += [base + a, base + b, base + c]

    def rbox(self, mat, x0, y0, z0, x1, y1, z1, r, k=2):
        """Caja de aristas redondeadas (radio r) en coordenadas de escena."""
        lo = np.array([min(x0, x1), min(y0, y1), min(z0, z1)]); hi = np.array([max(x0, x1), max(y0, y1), max(z0, z1)])
        c = (lo + hi) / 2; h = (hi - lo) / 2
        r = max(1e-4, min(r, h.min() * 0.98))
        off = [r * math.tan(math.pi / 4 * j / k) for j in range(k + 1)]
        def samples(hh):
            inner = hh - r
            if inner > 1e-6:
                return [-inner - o for o in reversed(off)] + [inner + o for o in off]
            return [-o for o in reversed(off)] + off[1:]
        S = [samples(h[i]) for i in range(3)]
        for ax in range(3):
            u_ax, v_ax = [a for a in range(3) if a != ax]
            for sg in (-1, 1):
                Ps, Ns, Us = [], [], []
                nu, nv = len(S[u_ax]), len(S[v_ax])
                for iu in range(nu):
                    for iv in range(nv):
                        v = np.zeros(3); v[ax] = sg * h[ax]; v[u_ax] = S[u_ax][iu]; v[v_ax] = S[v_ax][iv]
                        inner = np.clip(v, -(h - r), h - r)
                        d = v - inner; ln = np.linalg.norm(d); n = d / ln if ln > 1e-9 else np.eye(3)[ax] * sg
                        p = c + inner + n * r
                        Ps.append(p.tolist()); Ns.append(n.tolist()); Us.append([p[u_ax], p[v_ax]])
                T = []
                for iu in range(nu - 1):
                    for iv in range(nv - 1):
                        a = iu * nv + iv; b = a + nv
                        T += [(a, b, b + 1), (a, b + 1, a + 1)]
                self.tris(mat, Ps, Ns, Us, T)

    def cyl(self, mat, cx, y0, cz, r, h, seg=28, rz=None, cap=True):
        rz = rz or r
        pos, nor, uv, idx = self._get(mat)
        for i in range(seg):
            a0, a1 = 2 * math.pi * i / seg, 2 * math.pi * (i + 1) / seg
            p = [(cx + r * math.cos(a), cz + rz * math.sin(a)) for a in (a0, a1)]
            n0 = [math.cos(a0) / r, 0, math.sin(a0) / rz]; n1 = [math.cos(a1) / r, 0, math.sin(a1) / rz]
            base = len(pos)
            pos += [[p[0][0], y0, p[0][1]], [p[1][0], y0, p[1][1]], [p[1][0], y0 + h, p[1][1]], [p[0][0], y0 + h, p[0][1]]]
            nor += [n0, n1, n1, n0]; uv += [[i / seg * 2 * math.pi * r, 0], [(i + 1) / seg * 2 * math.pi * r, 0], [(i + 1) / seg * 2 * math.pi * r, h], [i / seg * 2 * math.pi * r, h]]
            idx += [base, base + 2, base + 1, base, base + 3, base + 2]
            if cap:
                for yy, ny_ in ((y0 + h, 1), (y0, -1)):
                    b = len(pos)
                    pos += [[cx, yy, cz], [p[0][0], yy, p[0][1]], [p[1][0], yy, p[1][1]]]
                    nor += [[0, ny_, 0]] * 3; uv += [[cx, cz], [p[0][0], p[0][1]], [p[1][0], p[1][1]]]
                    idx += [b, b + 2, b + 1] if ny_ > 0 else [b, b + 1, b + 2]

    def cyl_axis(self, mat, c, axis, r, h, seg=28):
        """Cilindro con eje horizontal (axis 0 = X, 2 = Z de escena) que empieza en c y avanza h."""
        Ps, Ns, Us, T = [], [], [], []
        u_, v_ = [a for a in range(3) if a != axis]
        for i in range(seg + 1):
            t = 2 * math.pi * i / seg
            for k in (0, 1):
                p = list(c); p[axis] += h * k; p[u_] += r * math.cos(t); p[v_] += r * math.sin(t)
                n = [0, 0, 0]; n[u_] = math.cos(t); n[v_] = math.sin(t)
                Ps.append(p); Ns.append(n); Us.append([t * r, h * k])
        for i in range(seg):
            a = 2 * i
            T += [(a, a + 2, a + 3), (a, a + 3, a + 1)]
        for k in (0, 1):
            ci = len(Ps); p = list(c); p[axis] += h * k; n = [0, 0, 0]; n[axis] = 1 if k else -1
            Ps.append(p); Ns.append(n); Us.append([0, 0])
            for i in range(seg + 1):
                t = 2 * math.pi * i / seg; q = list(p); q[u_] += r * math.cos(t); q[v_] += r * math.sin(t)
                Ps.append(q); Ns.append(n); Us.append([math.cos(t) * r, math.sin(t) * r])
            T += [(ci, ci + 1 + i, ci + 2 + i) for i in range(seg)]
        self.tris(mat, Ps, Ns, Us, T)

    def lathe(self, mat, cx, y0, cz, prof, seg=32, sx=1.0, sz=1.0):
        """Superficie de revolución. prof = [(radio, altura)] de abajo arriba."""
        Ps, Ns, Us, T = [], [], [], []
        m = len(prof)
        segn = []
        for j in range(m):
            a = prof[max(0, j - 1)]; b = prof[min(m - 1, j + 1)]
            dr, dh = b[0] - a[0], b[1] - a[1]
            ln = math.hypot(dr, dh) or 1
            segn.append((dh / ln, -dr / ln))
        acc = 0.0
        for j in range(m):
            if j:
                acc += math.hypot(prof[j][0] - prof[j - 1][0], prof[j][1] - prof[j - 1][1])
            for i in range(seg + 1):
                t = 2 * math.pi * i / seg
                r, hh = prof[j]; nr, nh = segn[j]
                Ps.append([cx + r * sx * math.cos(t), y0 + hh, cz + r * sz * math.sin(t)])
                n = np.array([nr * math.cos(t) / sx, nh, nr * math.sin(t) / sz]); n /= (np.linalg.norm(n) or 1)
                Ns.append(n.tolist()); Us.append([i / seg * 2 * math.pi * max(r, 0.02), acc])
        for j in range(m - 1):
            for i in range(seg):
                a = j * (seg + 1) + i; b = a + seg + 1
                T += [(a, b, b + 1), (a, b + 1, a + 1)]
        T = [t for t in T if len({tuple(np.round(Ps[q], 7)) for q in t}) == 3]
        self.tris(mat, Ps, Ns, Us, T)

    def tube(self, mat, pts, r, seg=12, cap=True):
        """Tubo de radio r (o lista de radios) a lo largo de una polilínea de puntos de escena (marcos, grifos, mangueras)."""
        Pp = np.array(pts, float); n = len(Pp)
        rr = np.full(n, r, float) if np.isscalar(r) else np.array(r, float)
        T = np.gradient(Pp, axis=0); T /= np.linalg.norm(T, axis=1, keepdims=True)
        ref = np.array([0.0, 1.0, 0.0]) if abs(T[0][1]) < 0.9 else np.array([1.0, 0.0, 0.0])
        Nn = np.cross(T[0], ref); Nn /= np.linalg.norm(Nn)
        Ps, Ns, Us, Tr = [], [], [], []
        acc = 0.0
        for i in range(n):
            if i:
                Nn = Nn - np.dot(Nn, T[i]) * T[i]; Nn /= (np.linalg.norm(Nn) or 1)
                acc += float(np.linalg.norm(Pp[i] - Pp[i - 1]))
            Bn = np.cross(T[i], Nn)
            for j in range(seg + 1):
                a = 2 * math.pi * j / seg; d = math.cos(a) * Nn + math.sin(a) * Bn
                Ps.append((Pp[i] + rr[i] * d).tolist()); Ns.append(d.tolist()); Us.append([a * rr[i], acc])
        for i in range(n - 1):
            for j in range(seg):
                a = i * (seg + 1) + j; b = a + seg + 1
                Tr += [(a, b, b + 1), (a, b + 1, a + 1)]
        if cap:
            for i, sgn in ((0, -1), (n - 1, 1)):
                c = len(Ps); Ps.append(Pp[i].tolist()); Ns.append((T[i] * sgn).tolist()); Us.append([0, 0])
                Bn = np.cross(T[i], Nn)
                for j in range(seg + 1):
                    a = 2 * math.pi * j / seg; d = math.cos(a) * Nn + math.sin(a) * Bn
                    Ps.append((Pp[i] + rr[i] * d).tolist()); Ns.append((T[i] * sgn).tolist()); Us.append([math.cos(a) * rr[i], math.sin(a) * rr[i]])
                Tr += [(c, c + 1 + j, c + 2 + j) for j in range(seg)]
        self.tris(mat, Ps, Ns, Us, Tr)

    def soft(self, mat, cx, cy, cz, hx, hy, hz, e1=0.3, e2=0.18, nu=28, nv=16, deform=None):
        """Volumen blando (superelipsoide) en escena: cojines, almohadas, duvet, tapizados.
        h* = semiejes (y vertical); e1 redondez vertical, e2 en planta (0 = caja, 1 = elipsoide).
        deform(x, y, z) -> (x, y, z) en coordenadas locales, antes de trasladar. Normales por caras."""
        sg = lambda w, m: math.copysign(abs(w) ** m, w)
        th = np.linspace(-math.pi / 2, math.pi / 2, nv + 1); ph = np.linspace(-math.pi, math.pi, nu + 1)
        V = np.zeros((nv + 1, nu + 1, 3))
        for j, t in enumerate(th):
            for i, f in enumerate(ph):
                x = hx * sg(math.cos(t), e1) * sg(math.cos(f), e2); y = hy * sg(math.sin(t), e1); z = hz * sg(math.cos(t), e1) * sg(math.sin(f), e2)
                if deform:
                    x, y, z = deform(x, y, z)
                V[j, i] = (x, y, z)
        N = np.zeros_like(V)
        for j in range(nv):
            for i in range(nu):
                a, b, c, d = V[j, i], V[j, i + 1], V[j + 1, i + 1], V[j + 1, i]
                n = np.cross(c - a, d - b)
                for (jj, ii) in ((j, i), (j, i + 1), (j + 1, i + 1), (j + 1, i)):
                    N[jj, ii] += n
        N[:, 0] += N[:, -1]; N[:, -1] = N[:, 0]                # costura
        ln = np.linalg.norm(N, axis=2, keepdims=True); N = N / np.where(ln == 0, 1, ln)
        if (N * V).sum() < 0:                                   # normales hacia afuera
            N = -N
        N[0, :] = [0, -1, 0]; N[-1, :] = [0, 1, 0]               # polos
        pos, nor, uv, idx = self._get(mat); base = len(pos)
        for j in range(nv + 1):
            for i in range(nu + 1):
                x, y, z = V[j, i]; pos.append([cx + x, cy + y, cz + z]); nor.append(N[j, i].tolist())
                uv.append([(x + z) * 1.0, y * 1.0 + j / nv * 0.2])
        W_ = nu + 1
        for j in range(nv):
            for i in range(nu):
                a = base + j * W_ + i; b = a + 1; c = a + W_ + 1; d = a + W_
                pa, pb, pc = np.array(pos[a]), np.array(pos[b]), np.array(pos[c])
                if np.dot(np.cross(pb - pa, pc - pa), np.array(nor[a]) + nor[b] + nor[c]) < 0:
                    idx += [a, c, b, a, d, c]
                else:
                    idx += [a, b, c, a, c, d]

    def sphere(self, mat, cx, cy, cz, r, sx=1, sy=1, sz=1, seg=18):
        pos, nor, uv, idx = self._get(mat)
        base = len(pos)
        for j in range(seg + 1):
            v = math.pi * j / seg
            for i in range(seg + 1):
                u = 2 * math.pi * i / seg
                n = [math.sin(v) * math.cos(u), math.cos(v), math.sin(v) * math.sin(u)]
                pos.append([cx + r * sx * n[0], cy + r * sy * n[1], cz + r * sz * n[2]])
                nn = np.array([n[0] / sx, n[1] / sy, n[2] / sz]); nn /= (np.linalg.norm(nn) or 1)
                nor.append(nn.tolist()); uv.append([i / seg, j / seg])
        for j in range(seg):
            for i in range(seg):
                a = base + j * (seg + 1) + i; b = a + seg + 1
                idx += [a, a + 1, b, a + 1, b + 1, b]

    def drape(self, mat, a, b, z0, z1, depth, folds, steps_per_fold=8):
        """Cortina plisada entre los puntos de escena a=(x,z) y b=(x,z); `depth` = amplitud del pliegue."""
        ax, az = a; bx, bz = b
        L = math.hypot(bx - ax, bz - az); tx, tz = (bx - ax) / L, (bz - az) / L; nx, nz = -tz, tx
        n = max(2, int(folds * steps_per_fold))
        Ps, Ns, Us, T = [], [], [], []
        for i in range(n + 1):
            s = i / n; ph = 2 * math.pi * folds * s
            off = depth * 0.5 * math.sin(ph); dd = depth * 0.5 * math.cos(ph) * 2 * math.pi * folds / L
            x = ax + tx * L * s + nx * off; zz = az + tz * L * s + nz * off
            nrm = np.array([nx - tx * dd, 0, nz - tz * dd]); nrm /= np.linalg.norm(nrm)
            for y in (z0, z1):
                Ps.append([x, y, zz]); Ns.append(nrm.tolist()); Us.append([L * s, y])
        for i in range(n):
            q = 2 * i
            T += [(q, q + 2, q + 3), (q, q + 3, q + 1)]
        self.tris(mat, Ps, Ns, Us, T)

    def panel(self, mat, corners, n):
        """Cuadrilátero con UV 0..1 (cuadros, pantallas)."""
        self.quad(mat, *corners, n, [[0, 0], [1, 0], [1, 1], [0, 1]])


# ------------------------------------------------------------------ materiales (nombres estables: el visor los reemplaza en vivo)
# nombre: (color RGBA lineal aprox., rugosidad, metalicidad, opciones)
MATS = {
    'muro': ([0.93, 0.91, 0.87, 1], 0.92, 0, {}), 'muro_corte': ([0.18, 0.17, 0.16, 1], 0.9, 0, {}), 'losa': ([0.42, 0.41, 0.40, 1], 0.95, 0, {}),
    'piso_madera': ([0.73, 0.58, 0.42, 1], 0.62, 0, {}), 'piso_ceramica': ([0.86, 0.85, 0.82, 1], 0.35, 0, {}), 'cielo': ([0.97, 0.97, 0.95, 1], 0.95, 0, {}),
    'vidrio': ([0.72, 0.84, 0.90, 0.22], 0.04, 0, {}), 'marco': ([0.22, 0.22, 0.23, 1], 0.45, 0.6, {}), 'alfeizar': ([0.90, 0.89, 0.86, 1], 0.35, 0, {}),
    'carpinteria': ([0.84, 0.78, 0.69, 1], 0.55, 0, {}), 'marco_puerta': ([0.84, 0.78, 0.69, 1], 0.55, 0, {}), 'puerta_entrada': ([0.30, 0.24, 0.19, 1], 0.5, 0, {}),
    'guardaescoba': ([0.95, 0.94, 0.92, 1], 0.5, 0, {}),
    'meson': ([0.88, 0.87, 0.84, 1], 0.22, 0, {}), 'gabinete_cocina': ([0.70, 0.56, 0.40, 1], 0.5, 0, {}), 'salpicadero': ([0.92, 0.91, 0.88, 1], 0.2, 0, {}),
    'acero': ([0.72, 0.73, 0.74, 1], 0.28, 1.0, {}), 'cromo': ([0.85, 0.85, 0.86, 1], 0.08, 1.0, {}), 'electro': ([0.62, 0.63, 0.64, 1], 0.32, 0.9, {}), 'electro_blanco': ([0.92, 0.92, 0.91, 1], 0.25, 0, {}),
    'vidrio_negro': ([0.02, 0.02, 0.025, 1], 0.06, 0.2, {}),
    'ceramica_blanca': ([0.96, 0.96, 0.95, 1], 0.12, 0, {}), 'vidrio_ducha': ([0.85, 0.92, 0.95, 0.14], 0.03, 0, {}),
    'revestimiento_bano': ([0.88, 0.86, 0.82, 1], 0.25, 0, {}), 'revestimiento_ropas': ([0.93, 0.93, 0.92, 1], 0.2, 0, {}),
    'mueble_bano': ([0.70, 0.56, 0.40, 1], 0.5, 0, {}), 'meson_bano': ([0.90, 0.89, 0.86, 1], 0.2, 0, {}), 'espejo_principal': ([0.95, 0.96, 0.97, 1], 0.02, 1.0, {}), 'espejo_social': ([0.95, 0.96, 0.97, 1], 0.02, 1.0, {}),
    'tela_sofa': ([0.78, 0.74, 0.68, 1], 0.95, 0, {}), 'tela_acento': ([0.55, 0.36, 0.26, 1], 0.95, 0, {}), 'tela_cama': ([0.94, 0.93, 0.90, 1], 0.92, 0, {}),
    'tela_cortina': ([0.92, 0.90, 0.85, 1], 0.95, 0, {'double': True}), 'tela_silla': ([0.62, 0.58, 0.52, 1], 0.95, 0, {}),
    'madera_mueble': ([0.62, 0.47, 0.32, 1], 0.5, 0, {}), 'laca_mueble': ([0.90, 0.89, 0.86, 1], 0.35, 0, {}),
    'metal_negro': ([0.06, 0.06, 0.065, 1], 0.4, 0.8, {}), 'laton': ([0.78, 0.62, 0.36, 1], 0.3, 1.0, {}),
    'textil_tapete': ([0.74, 0.69, 0.60, 1], 1.0, 0, {}), 'planta': ([0.20, 0.36, 0.20, 1], 0.7, 0, {'double': True}), 'planta_2': ([0.30, 0.45, 0.24, 1], 0.7, 0, {'double': True}),
    'maceta': ([0.55, 0.47, 0.40, 1], 0.85, 0, {}), 'ceramica_deco': ([0.86, 0.83, 0.77, 1], 0.4, 0, {}),
    'libro_a': ([0.55, 0.30, 0.22, 1], 0.8, 0, {}), 'libro_b': ([0.25, 0.32, 0.38, 1], 0.8, 0, {}), 'libro_c': ([0.86, 0.82, 0.72, 1], 0.8, 0, {}),
    'cuadro': ([1, 1, 1, 1], 0.85, 0, {}), 'pantalla': ([0.01, 0.01, 0.012, 1], 0.08, 0.1, {}),
    'luz_calida': ([1.0, 0.92, 0.78, 1], 0.4, 0, {'emissive': [1.0, 0.82, 0.55]}), 'pantalla_lampara': ([0.95, 0.90, 0.80, 1], 0.9, 0, {'double': True, 'emissive': [0.35, 0.27, 0.16]}),
    'piso_exterior': ([0.62, 0.60, 0.56, 1], 0.8, 0, {}), 'vidrio_baranda': ([0.80, 0.90, 0.93, 0.18], 0.03, 0, {}),
    'muro_corte_propuesta': ([0.42, 0.30, 0.18, 1], 0.9, 0, {}), 'espejo_vestier': ([0.95, 0.96, 0.97, 1], 0.03, 1.0, {}),
    'cesped_maceta': ([0.42, 0.48, 0.30, 1], 0.9, 0, {}), 'toalla': ([0.93, 0.92, 0.88, 1], 1.0, 0, {}),
    'carcasa': ([0.10, 0.09, 0.08, 1], 0.8, 0, {}), 'tela_visillo': ([0.97, 0.96, 0.93, 0.55], 0.9, 0, {'double': True}), 'vidrio_opal': ([0.97, 0.95, 0.91, 1], 0.3, 0, {'emissive': [0.9, 0.78, 0.6]}),
    'ceramica_calida': ([0.84, 0.80, 0.75, 1], 0.18, 0, {}), 'tela_cabecero': ([0.74, 0.69, 0.62, 1], 0.95, 0, {}),
    'laton_cepillado': ([0.80, 0.68, 0.48, 1], 0.32, 1.0, {}), 'rejilla': ([0.08, 0.08, 0.085, 1], 0.6, 0.5, {}),
    'vegetal': ([0.40, 0.46, 0.30, 1], 0.8, 0, {'double': True}), 'rama_seca': ([0.52, 0.42, 0.32, 1], 0.9, 0, {}),
}

nodes = []   # (nombre, mesh, extras, translation, rotation_y_deg)
CAT = {'arquitectura': 'verificado', 'aparatos': 'verificado', 'ilustrativo': 'ilustrativo', 'acabados': 'ilustrativo', 'mobiliario': 'ilustrativo',
       'cielo': 'provisional', 'propuesta': 'propuesta', 'propuesta_mobiliario': 'propuesta', 'sin_balcon': 'provisional'}


def node(name, mesh, verified, source, t=(0, 0, 0), ry=0.0, group='arquitectura', **extra):
    cat = extra.pop('categoria', None) or ('verificado' if verified else CAT.get(group, 'ilustrativo'))
    if group == 'arquitectura' and not verified:
        cat = 'provisional'
    nodes.append((name, mesh, {'verificado': verified, 'fuente': source, 'grupo': group, 'categoria': cat, **extra}, t, ry))



# ------------------------------------------------------------------ ayudas en coordenadas de planta (x este, y norte, z altura)
def B(m, mat, x0, y0, x1, y1, z0, z1, faces='all'):
    a, b = P(x0, y0), P(x1, y1); m.box(mat, a[0], z0, a[1], b[0], z1, b[1], faces)


def RB(m, mat, x0, y0, x1, y1, z0, z1, r, k=2):
    a, b = P(x0, y0), P(x1, y1); m.rbox(mat, a[0], z0, a[1], b[0], z1, b[1], r, k)


def SOFT(m, mat, x0, y0, x1, y1, z0, z1, e1=0.3, e2=0.18, nu=28, nv=16, deform=None):
    """Volumen blando en coordenadas de planta (caja x0..x1, y0..y1, z0..z1)."""
    a, b = P(x0, y0), P(x1, y1)
    m.soft(mat, (a[0] + b[0]) / 2, (z0 + z1) / 2, (a[1] + b[1]) / 2, abs(b[0] - a[0]) / 2, (z1 - z0) / 2, abs(b[1] - a[1]) / 2, e1, e2, nu, nv, deform)


def pillow(m, mat, x0, y0, x1, y1, z0, z1, lean=0.0):
    """Almohada: bordes pellizcados, centro abombado; lean inclina la almohada hacia el cabecero (m)."""
    hx_, hz_ = abs(x1 - x0) / 2, abs(y1 - y0) / 2
    def d(x, y, z):
        r = max(abs(x) / hx_, abs(z) / hz_) if hx_ and hz_ else 0
        y = y * (1 - 0.38 * r ** 4) + 0.006 * math.sin(7 * x / hx_) * (1 - r)
        return x, y, z
    SOFT(m, mat, x0, y0, x1, y1, z0, z1, 0.55, 0.22, 30, 14, d)


def TU(m, mat, pts, r, seg=12, cap=True):
    """Tubo por puntos de planta (x, y, z)."""
    m.tube(mat, [[P(x, y)[0], z, P(x, y)[1]] for x, y, z in pts], r, seg, cap)


def arco(c, r, a0, a1, n=16, z=None, plano='xz'):
    """Puntos de un arco: plano 'xy' horizontal a la altura z; 'xz'/'yz' vertical. c = centro (x, y, z)."""
    out = []
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n; ca, sa = math.cos(a), math.sin(a)
        if plano == 'xy':
            out.append((c[0] + r * ca, c[1] + r * sa, c[2]))
        elif plano == 'xz':
            out.append((c[0] + r * ca, c[1], c[2] + r * sa))
        else:
            out.append((c[0], c[1] + r * ca, c[2] + r * sa))
    return out


def CY(m, mat, x, y, r, z0, h, seg=24, ry=None, cap=True):
    c = P(x, y); m.cyl(mat, c[0], z0, c[1], r, h, seg, rz=ry, cap=cap)


def LA(m, mat, x, y, z0, prof, seg=32, sx=1.0, sy=1.0):
    c = P(x, y); m.lathe(mat, c[0], z0, c[1], prof, seg, sx, sy)


def SP(m, mat, x, y, z, r, sx=1, sy=1, sz=1, seg=14):
    c = P(x, y); m.sphere(mat, c[0], z, c[1], r, sx, sz, sy, seg)


def DR(m, mat, x0, y0, x1, y1, z0, z1, depth=0.08, folds=None):
    a, b = P(x0, y0), P(x1, y1)
    L = math.hypot(x1 - x0, y1 - y0)
    m.drape(mat, a, b, z0, z1, depth, folds or max(2, round(L / 0.11)))


def wall_quad(m, mat, side, x0, y0, x1, y1, z0, z1, uv01=False):
    """Cuadrilátero vertical sobre un muro. side: 'n','s','e','o' = hacia dónde mira la cara."""
    n = {'n': [0, 0, -1], 's': [0, 0, 1], 'e': [1, 0, 0], 'o': [-1, 0, 0]}[side]
    a, b = P(x0, y0), P(x1, y1)
    pa = [a[0], z0, a[1]]; pb = [b[0], z0, b[1]]; pc = [b[0], z1, b[1]]; pd = [a[0], z1, a[1]]
    L = math.hypot(x1 - x0, y1 - y0)
    uvs = [[0, 0], [1, 0], [1, 1], [0, 1]] if uv01 else [[0, z0], [L, z0], [L, z1], [0, z1]]
    gn = np.cross(np.subtract(pb, pa), np.subtract(pd, pa))
    if np.dot(gn, n) < 0:
        pa, pb, pc, pd = pb, pa, pd, pc; uvs = [uvs[1], uvs[0], uvs[3], uvs[2]]
    m.quad(mat, pa, pb, pc, pd, n, uvs)


ROOMS = {r['id']: r for r in g['espacios']}
WALLS = g['muros_rectangulos']


def in_wall(x, y):
    return any(x0 - 1e-6 <= x <= x1 + 1e-6 and y0 - 1e-6 <= y <= y1 + 1e-6 for x0, y0, x1, y1 in WALLS)


def wall_runs(room_id, step=0.01):
    """Tramos del perímetro de un espacio que dan contra muro (excluye vanos de puertas y ventanas)."""
    rects = ROOMS[room_id]['piso_rectangulos']
    def inside_room(x, y):
        return any(x0 <= x <= x1 and y0 <= y <= y1 for x0, y0, x1, y1 in rects)
    runs = []
    for x0, y0, x1, y1 in rects:
        for side, (ax, ay, bx, by, ox, oy) in {
            's': (x0, y0, x1, y0, 0, -0.03), 'n': (x0, y1, x1, y1, 0, 0.03),
            'o': (x0, y0, x0, y1, -0.03, 0), 'e': (x1, y0, x1, y1, 0.03, 0)}.items():
            L = math.hypot(bx - ax, by - ay); n = max(1, int(round(L / step)))
            cur = None
            for i in range(n + 1):
                t = i / n; x = ax + (bx - ax) * t; y = ay + (by - ay) * t
                ok = in_wall(x + ox, y + oy) and not inside_room(x + ox * 2, y + oy * 2)
                if ok and cur is None:
                    cur = t
                if (not ok or i == n) and cur is not None:
                    t1 = t if ok else (i - 1) / n
                    if t1 - cur > 0.02 / max(L, 1e-6):
                        runs.append((side, ax + (bx - ax) * cur, ay + (by - ay) * cur, ax + (bx - ax) * t1, ay + (by - ay) * t1))
                    cur = None
    return runs


face_of = {'s': 'n', 'n': 's', 'o': 'e', 'e': 'o'}   # muro al sur → la cara mira al norte


def clad(m, mat, room_id, z0, z1, inset=0.004, huecos=()):
    """Reviste los muros de un espacio; huecos = [(lado, desde, hasta, z0, z1)] deja abiertos los nichos."""
    for side, xa, ya, xb, yb in wall_runs(room_id):
        dx, dy = {'s': (0, inset), 'n': (0, -inset), 'o': (inset, 0), 'e': (-inset, 0)}[side]
        hs = [h for h in huecos if h[0] == side and ((side in 'ns' and min(xa, xb) < h[1] and max(xa, xb) > h[2]) or (side in 'eo' and min(ya, yb) < h[1] and max(ya, yb) > h[2]))]
        if not hs:
            wall_quad(m, mat, face_of[side], xa + dx, ya + dy, xb + dx, yb + dy, z0, z1)
            continue
        _, h0, h1, hz0, hz1 = hs[0]
        if side in 'ns':
            pts = [(xa, h0), (h1, xb)]; seg = lambda a, b, za, zb: wall_quad(m, mat, face_of[side], a + dx, ya + dy, b + dx, yb + dy, za, zb)
        else:
            pts = [(ya, h0), (h1, yb)]; seg = lambda a, b, za, zb: wall_quad(m, mat, face_of[side], xa + dx, a + dy, xb + dx, b + dy, za, zb)
        seg(pts[0][0], pts[0][1], z0, z1); seg(pts[1][0], pts[1][1], z0, z1)
        seg(h0, h1, z0, hz0); seg(h0, h1, hz1, z1)


def nicho(m, mat, side, h0, h1, linea, z0, z1, prof=0.09, luz=True):
    """Nicho empotrado en un muro: lado = muro respecto del espacio ('n' muro al norte...), linea = cara del muro."""
    s_ = {'n': 1, 's': -1, 'e': 1, 'o': -1}[side]
    if side in 'ns':
        B(m, mat, h0, linea + (prof if s_ > 0 else -prof) - 0.002 * s_, h1, linea + (prof if s_ > 0 else -prof), z0, z1)   # fondo
        for (a, b) in ((h0 - 0.002, h0), (h1, h1 + 0.002)):
            B(m, mat, a, min(linea, linea + s_ * prof), b, max(linea, linea + s_ * prof), z0, z1)
        B(m, mat, h0, min(linea, linea + s_ * prof), h1, max(linea, linea + s_ * prof), z0 - 0.002, z0)
        B(m, mat, h0, min(linea, linea + s_ * prof), h1, max(linea, linea + s_ * prof), z1, z1 + 0.002)
        if luz:
            B(m, 'luz_calida', h0 + 0.01, min(linea, linea + s_ * prof) + 0.01, h1 - 0.01, max(linea, linea + s_ * prof) - 0.01, z1 - 0.004, z1)
    else:
        B(m, mat, linea + (prof if s_ > 0 else -prof) - 0.002 * s_, h0, linea + (prof if s_ > 0 else -prof), h1, z0, z1)
        for (a, b) in ((h0 - 0.002, h0), (h1, h1 + 0.002)):
            B(m, mat, min(linea, linea + s_ * prof), a, max(linea, linea + s_ * prof), b, z0, z1)
        B(m, mat, min(linea, linea + s_ * prof), h0, max(linea, linea + s_ * prof), h1, z0 - 0.002, z0)
        B(m, mat, min(linea, linea + s_ * prof), h0, max(linea, linea + s_ * prof), h1, z1, z1 + 0.002)
        if luz:
            B(m, 'luz_calida', min(linea, linea + s_ * prof) + 0.01, h0 + 0.01, max(linea, linea + s_ * prof) - 0.01, h1 - 0.01, z1 - 0.004, z1)



rng = np.random.default_rng(104)


def plant(m, x, y, z0, h, spread, pot_r, pot_h, pot='maceta'):
    LA(m, pot, x, y, z0, [(pot_r * 0.78, 0), (pot_r, pot_h * 0.85), (pot_r * 1.03, pot_h), (pot_r * 0.95, pot_h)], seg=28)
    CY(m, 'cesped_maceta', x, y, pot_r * 0.94, z0 + pot_h - 0.03, 0.01, seg=24)
    for i in range(3):
        CY(m, 'madera_mueble', x + rng.uniform(-0.03, 0.03), y + rng.uniform(-0.03, 0.03), 0.008, z0 + pot_h, h * rng.uniform(0.5, 0.8), seg=6)
    for i in range(30):   # follaje en racimos ovalados
        a = rng.uniform(0, 2 * math.pi); hf = rng.uniform(0.3, 1.0); rr = spread * math.sqrt(rng.uniform(0.05, 1)) * (0.5 + 0.5 * math.sin(hf * math.pi))
        zz = z0 + pot_h + h * hf
        SP(m, 'planta' if i % 3 else 'planta_2', x + rr * math.cos(a), y + rr * math.sin(a), zz, (0.05 * spread / 0.3 + 0.02),
           sx=rng.uniform(0.8, 1.3), sy=rng.uniform(0.8, 1.3), sz=rng.uniform(0.8, 1.2), seg=7)


def books(m, x0, y, x1, z0, depth=0.20, along='x', facing=1):
    x = x0; mats_ = ['libro_a', 'libro_b', 'libro_c', 'libro_c', 'libro_b']
    i = 0
    while x < x1 - 0.03:
        t = rng.uniform(0.02, 0.045); hh = rng.uniform(0.18, 0.27)
        if along == 'x':
            B(m, mats_[i % 5], x, y, x + t, y + depth * facing, z0, z0 + hh)
        else:
            B(m, mats_[i % 5], y, x, y + depth * facing, x + t, z0, z0 + hh)
        x += t + 0.002; i += 1
        if i % 7 == 6:
            x += 0.12


def art(m, side, x0, y0, x1, y1, z0, z1, frame='metal_negro'):
    """Cuadro con marco delgado sobre un muro."""
    off = {'e': (0.02, 0), 'o': (-0.02, 0), 'n': (0, 0.02), 's': (0, -0.02)}[side]
    if side in ('e', 'o'):
        xw = x0
        B(m, frame, min(xw, xw + off[0]), y0 - 0.02, max(xw, xw + off[0]), y1 + 0.02, z0 - 0.02, z1 + 0.02)
        wall_quad(m, 'cuadro', side, xw + off[0] * 1.05, y1 if side == 'e' else y0, xw + off[0] * 1.05, y0 if side == 'e' else y1, z0, z1, uv01=True)
    else:
        yw = y0
        B(m, frame, x0 - 0.02, min(yw, yw + off[1]), x1 + 0.02, max(yw, yw + off[1]), z0 - 0.02, z1 + 0.02)
        wall_quad(m, 'cuadro', side, x0 if side == 's' else x1, yw + off[1] * 1.05, x1 if side == 's' else x0, yw + off[1] * 1.05, z0, z1, uv01=True)


def chair(m, cx, cy, facing, seat='tela_silla'):
    """Silla de comedor; facing = hacia dónde mira el usuario sentado ('n' o 's')."""
    s = 0.22
    for ex in (-1, 1):
        for ey in (-1, 1):
            CY(m, 'metal_negro', cx + ex * 0.18, cy + ey * 0.18, 0.012, 0, 0.45, seg=8)
    RB(m, seat, cx - s, cy - s, cx + s, cy + s, 0.43, 0.49, 0.025)
    by = cy - s if facing == 'n' else cy + s - 0.05
    RB(m, seat, cx - s + 0.01, by, cx + s - 0.01, by + 0.05, 0.50, 0.88, 0.025)
    for ex in (-1, 1):
        B(m, 'metal_negro', cx + ex * 0.18 - 0.006, by + 0.02, cx + ex * 0.18 + 0.006, by + 0.032, 0.45, 0.75)



def toilet(m, rect, tank_side):
    x0, y0, x1, y1 = rect
    if tank_side == 'o':   # tanque contra el muro oeste, taza hacia el este
        RB(m, 'ceramica_blanca', x0, y0 + 0.04, x0 + 0.17, y1 - 0.04, 0.40, 0.80, 0.03)
        RB(m, 'ceramica_blanca', x0 - 0.005, y0 + 0.03, x0 + 0.18, y1 - 0.03, 0.80, 0.83, 0.012, k=2)
        cx_, cy_ = x0 + 0.40, (y0 + y1) / 2; sxx, syy = 1.18, 0.9
        RB(m, 'ceramica_blanca', x0 + 0.12, cy_ - 0.13, x0 + 0.30, cy_ + 0.13, 0, 0.36, 0.06)
    else:                  # tanque contra el muro norte, taza hacia el sur
        RB(m, 'ceramica_blanca', x0 + 0.04, y1 - 0.17, x1 - 0.04, y1, 0.40, 0.80, 0.03)
        RB(m, 'ceramica_blanca', x0 + 0.03, y1 - 0.18, x1 - 0.03, y1 + 0.005, 0.80, 0.83, 0.012, k=2)
        cx_, cy_ = (x0 + x1) / 2, y1 - 0.40; sxx, syy = 0.9, 1.18
        RB(m, 'ceramica_blanca', cx_ - 0.13, y1 - 0.30, cx_ + 0.13, y1 - 0.12, 0, 0.36, 0.06)
    LA(m, 'ceramica_blanca', cx_, cy_, 0, [(0.11, 0), (0.12, 0.08), (0.15, 0.22), (0.175, 0.34), (0.18, 0.38), (0.17, 0.395)], seg=36, sx=sxx, sy=syy)
    LA(m, 'ceramica_blanca', cx_, cy_, 0.395, [(0.17, 0), (0.18, 0.012), (0.17, 0.028), (0.0, 0.03)], seg=36, sx=sxx, sy=syy)   # asiento cerrado
    if tank_side == 'o':
        CY(m, 'cromo', x0 + 0.09, (y0 + y1) / 2, 0.018, 0.83, 0.006, seg=14)
    else:
        CY(m, 'cromo', (x0 + x1) / 2, y1 - 0.09, 0.018, 0.83, 0.006, seg=14)


def vanity(m, rect, wall):
    """Mueble de lavamanos flotante con mesón y poceta de sobreponer; grifería desde el muro."""
    x0, y0, x1, y1 = rect
    RB(m, 'mueble_bano', x0 + 0.005, y0 + 0.005, x1 - 0.005, y1 - 0.005, 0.32, 0.80, 0.008, k=1)
    RB(m, 'meson_bano', x0, y0, x1, y1, 0.80, 0.825, 0.004, k=1)
    cx_, cy_ = (x0 + x1) / 2, (y0 + y1) / 2
    if wall == 'o':
        cx_ += 0.03
        B(m, 'cromo', x0 + 0.04, cy_ - 0.15, x0 + 0.05, cy_ + 0.15, 0.58, 0.595)       # tirador
    else:
        cy_ -= 0.03
        B(m, 'cromo', cx_ - 0.15, y0 - 0.01, cx_ + 0.15, y0, 0.58, 0.595)
    LA(m, 'ceramica_blanca', cx_, cy_, 0.825, [(0.12, 0), (0.17, 0.02), (0.19, 0.08), (0.195, 0.12), (0.185, 0.125), (0.17, 0.05), (0.03, 0.03)], seg=36, sx=1.0, sy=0.8)
    if wall == 'o':
        CY(m, 'cromo', x0 + 0.03, cy_, 0.012, 1.05, 0.05, seg=12)
        RB(m, 'cromo', x0 + 0.005, cy_ - 0.011, x0 + 0.17, cy_ + 0.011, 1.07, 1.09, 0.009, k=2)
    else:
        RB(m, 'cromo', cx_ - 0.011, y1 - 0.17, cx_ + 0.011, y1 - 0.005, 1.07, 1.09, 0.009, k=2)


def shower(m, rect, glass_side, opening):
    x0, y0, x1, y1 = rect
    RB(m, 'ceramica_blanca', x0, y0, x1, y1, 0, 0.035, 0.008, k=1)                        # plato de ducha
    B(m, 'acero', (x0 + x1) / 2 - 0.06, (y0 + y1) / 2 - 0.06, (x0 + x1) / 2 + 0.06, (y0 + y1) / 2 + 0.06, 0.035, 0.037)
    if glass_side == 's':      # mampara fija sobre el borde sur, entrada por el este
        gx1 = x1 - opening
        B(m, 'vidrio_ducha', x0, y0 + 0.01, gx1, y0 + 0.018, 0.035, 2.0)
        B(m, 'cromo', x0, y0 + 0.006, gx1, y0 + 0.022, 1.985, 2.0)
        B(m, 'cromo', gx1 - 0.012, y0 + 0.006, gx1, y0 + 0.022, 0.035, 2.0)
        hx, hy = (x0 + x1) / 2, y1 - 0.18; wall_y = y1
        RB(m, 'cromo', hx - 0.012, wall_y - 0.30, hx + 0.012, wall_y, 2.08, 2.10, 0.008, k=2)
        CY(m, 'cromo', hx, hy, 0.11, 2.065, 0.015, seg=32)
        RB(m, 'cromo', hx - 0.05, wall_y - 0.04, hx + 0.05, wall_y, 1.05, 1.15, 0.02)
        B(m, 'revestimiento_bano', x0 + 0.05, wall_y - 0.08, x0 + 0.35, wall_y - 0.002, 1.20, 1.21)   # repisa del nicho
    else:                      # mampara fija sobre el borde oeste, entrada por el norte
        gy1 = y1 - opening
        B(m, 'vidrio_ducha', x0 + 0.01, y0, x0 + 0.018, gy1, 0.035, 2.0)
        B(m, 'cromo', x0 + 0.006, y0, x0 + 0.022, gy1, 1.985, 2.0)
        B(m, 'cromo', x0 + 0.006, gy1 - 0.012, x0 + 0.022, gy1, 0.035, 2.0)
        hx, hy = x1 - 0.18, (y0 + y1) / 2; wall_x = x1
        RB(m, 'cromo', wall_x - 0.30, hy - 0.012, wall_x, hy + 0.012, 2.08, 2.10, 0.008, k=2)
        CY(m, 'cromo', hx, hy, 0.11, 2.065, 0.015, seg=32)
        RB(m, 'cromo', wall_x - 0.04, hy - 0.05, wall_x, hy + 0.05, 1.05, 1.15, 0.02)



# --- dormitorios
def bed(m, x0, y0, x1, y1, head, duvet='tela_cama', accent='tela_acento'):
    """Cama: base tapizada flotante, colchón, duvet blando que cae por los lados, pie de cama doblado,
    almohadas pellizcadas y cabecero tapizado de canales verticales. head = muro del cabecero ('e' u 'o')."""
    sgn = 1 if head == 'e' else -1
    hx = x1 if head == 'e' else x0                      # línea del cabecero
    fx_ = x0 if head == 'e' else x1                      # pie de la cama
    lo, hi = min(hx, fx_), max(hx, fx_)
    RB(m, 'metal_negro', lo + 0.10, y0 + 0.10, hi - 0.10, y1 - 0.10, 0.0, 0.10, 0.01, k=1)            # zócalo retranqueado: base flotante
    RB(m, 'tela_sofa', lo, y0, hi, y1, 0.10, 0.34, 0.035)                                             # base tapizada
    SOFT(m, 'tela_cama', lo + 0.015, y0 + 0.015, hi - 0.015, y1 - 0.015, 0.33, 0.55, 0.22, 0.10, 34, 12)   # colchón
    W_ = y1 - y0
    def duv(x, y, z):                                    # arrugas suaves sobre el duvet
        return x, y + (0.006 * math.sin(9 * x) * math.cos(6 * z) if y > 0 else 0.0), z
    dx0 = fx_ - sgn * 0.03; dx1 = hx - sgn * 0.62       # el duvet cubre hasta 0,62 m del cabecero
    SOFT(m, duvet, min(dx0, dx1), y0 - 0.035, max(dx0, dx1), y1 + 0.035, 0.30, 0.585, 0.12, 0.05, 40, 14, duv)
    tx0 = dx1 - sgn * 0.02; tx1 = dx1 + sgn * 0.20        # embozo doblado hacia las almohadas
    SOFT(m, duvet, min(tx0, tx1), y0 - 0.03, max(tx0, tx1), y1 + 0.03, 0.555, 0.615, 0.5, 0.08, 30, 10)
    px0 = fx_ - sgn * 0.02; px1 = fx_ + sgn * 0.50        # pie de cama doblado
    SOFT(m, accent, min(px0, px1), y0 - 0.05, max(px0, px1), y1 + 0.05, 0.56, 0.60, 0.35, 0.06, 30, 10)
    npil = 2 if W_ > 1.2 else 1
    for k in range(npil):
        a = y0 + 0.06 + k * (W_ - 0.12) / npil; b = a + (W_ - 0.12) / npil - 0.03
        p0, p1 = hx - sgn * 0.08, hx - sgn * 0.44
        pillow(m, 'tela_cama', min(p0, p1), a, max(p0, p1), b, 0.54, 0.74)
        q0, q1 = hx - sgn * 0.30, hx - sgn * 0.58          # cojín decorativo delante
        pillow(m, accent, min(q0, q1), a + 0.10, max(q0, q1), b - 0.10, 0.56, 0.72)
    # cabecero de canales verticales tapizados sobre un panel
    c0, c1 = (hx, hx + 0.03) if head == 'e' else (hx - 0.03, hx)
    RB(m, 'tela_sofa', c0, y0 - 0.08, c1, y1 + 0.08, 0.30, 1.18, 0.006, k=1)
    nch = max(5, int(round((y1 - y0 + 0.16) / 0.20)))
    step = (y1 - y0 + 0.16) / nch
    for k in range(nch):
        ya = y0 - 0.08 + k * step + 0.004; yb = ya + step - 0.008
        a0_, a1_ = (hx - 0.07, hx) if head == 'e' else (hx, hx + 0.07)
        SOFT(m, 'tela_sofa', a0_, ya, a1_, yb, 0.34, 1.18, 0.12, 0.45, 18, 12)


def nightstand(m, x0, y0, x1, y1, lamp=True):
    RB(m, 'madera_mueble', x0, y0, x1, y1, 0.16, 0.52, 0.012, k=1)
    for xx in (x0 + 0.04, x1 - 0.04):
        for yy in (y0 + 0.04, y1 - 0.04):
            CY(m, 'metal_negro', xx, yy, 0.01, 0, 0.16, seg=6)
    cx_, cy_ = (x0 + x1) / 2, (y0 + y1) / 2
    if lamp:
        LA(m, 'ceramica_deco', cx_, cy_, 0.52, [(0.05, 0), (0.07, 0.05), (0.06, 0.15), (0.015, 0.2), (0.012, 0.3)], seg=20)
        LA(m, 'pantalla_lampara', cx_, cy_, 0.74, [(0.13, 0), (0.10, 0.18)], seg=24)


def wardrobe(m, x0, y0, x1, y1, front, h=2.25, doors=None):
    RB(m, 'laca_mueble', x0, y0, x1, y1, 0.0, h, 0.006, k=1)
    L = (x1 - x0) if front in ('n', 's') else (y1 - y0)
    n = doors or max(2, round(L / 0.55))
    for i in range(1, n):
        if front in ('n', 's'):
            xm = x0 + L * i / n; yy = y0 if front == 's' else y1
            B(m, 'metal_negro', xm - 0.002, yy - 0.003, xm + 0.002, yy + 0.003, 0.02, h - 0.02)
        else:
            ym = y0 + L * i / n; xx = x0 if front == 'o' else x1
            B(m, 'metal_negro', xx - 0.003, ym - 0.002, xx + 0.003, ym + 0.002, 0.02, h - 0.02)
    for i in range(n):   # tiradores verticales
        if front in ('n', 's'):
            xm = x0 + L * (i + 0.5) / n + (0.22 if i % 2 == 0 else -0.22) * (L / n) / 0.55
            yy = (y0 - 0.02) if front == 's' else y1
            B(m, 'laton', xm - 0.006, yy, xm + 0.006, yy + 0.02, 0.95, 1.35)
        else:
            ym = y0 + L * (i + 0.5) / n + (0.22 if i % 2 == 0 else -0.22) * (L / n) / 0.55
            xx = (x0 - 0.02) if front == 'o' else x1
            B(m, 'laton', xx, ym - 0.006, xx + 0.02, ym + 0.006, 0.95, 1.35)


def curtain(m, side, a, b, w=0.30, sheer=False):
    """Cortinas recogidas a ambos lados de una ventana. side = muro de la ventana."""
    z0, z1 = 0.02, ALT - 0.06
    if side == 's':
        y = 0.15 + 0.07
        DR(m, 'tela_cortina', a - 0.05, y, a + w - 0.05, y, z0, z1, 0.07); DR(m, 'tela_cortina', b - w + 0.05, y, b + 0.05, y, z0, z1, 0.07)
        a_, b_ = P(a - 0.10, y), P(b + 0.10, y)
        m.box('metal_negro', a_[0], z1 + 0.01, a_[1] - 0.008, b_[0], z1 + 0.026, a_[1] + 0.008)
    else:   # ventana en el muro este
        x = 7.95 - 0.07
        DR(m, 'tela_cortina', x, a - 0.05, x, a + w - 0.05, z0, z1, 0.07); DR(m, 'tela_cortina', x, b - w + 0.05, x, b + 0.05, z0, z1, 0.07)
        a_, b_ = P(x, a - 0.10), P(x, b + 0.10)
        m.box('metal_negro', a_[0] - 0.008, z1 + 0.01, a_[1], a_[0] + 0.008, z1 + 0.026, b_[1])



# ------------------------------------------------------------------ ARQUITECTURA: envolvente del DWG y tabiques de la PROPUESTA
ORIG = g['muros_origen']
HP = SUP['altura_puerta']


def node102(name, mesh, cat, source, group, **extra):
    nodes.append((name, mesh, {'verificado': cat == 'verificado', 'fuente': source, 'grupo': group, 'categoria': cat, **extra}, extra.pop('t', (0, 0, 0)) if False else (0, 0, 0), 0.0))


m = Mesh(); mp_ = Mesh()
for (x0, y0, x1, y1), o in zip(g['muros_rectangulos'], ORIG):
    a, b = P(x0, y0), P(x1, y1)
    tgt = m if o == 'dwg' else mp_
    tgt.box('muro', a[0], 0, a[1], b[0], ALT, b[1], faces=['px', 'nx', 'pz', 'nz', 'ny'])
    tgt.box('muro_corte' if o == 'dwg' else 'muro_corte_propuesta', a[0], ALT, a[1], b[0], ALT + 0.001, b[1], faces=['py'])
node102('ARQ_Muros', m, 'verificado', 'Envolvente del DWG: medianeros, muro del corredor, fachada y ductos; altura supuesta', 'arquitectura')
# dinteles de las puertas de la propuesta (y vano del vestier)
for d in [*g['puertas'], *g['vanos']]:
    if d.get('origen') == 'dwg':
        continue
    x0, y0, x1, y1 = d['rect']; a, b = P(x0, y0), P(x1, y1)
    mp_.box('muro', a[0], HP, a[1], b[0], ALT, b[1], faces=['px', 'nx', 'pz', 'nz', 'ny'])
node102('PRO_Muros_interiores', mp_, 'propuesta', 'Tabiques de la propuesta de redistribución (no figuran en el DWG)', 'rediseno')

m = Mesh(); m_sala = Mesh()
ent = next(d for d in g['puertas'] if d['id'] == 'entrada')
x0, y0, x1, y1 = ent['rect']; a, b = P(x0, y0), P(x1, y1)
m.box('muro', a[0], HP, a[1], b[0], ALT, b[1], faces=['px', 'nx', 'pz', 'nz', 'ny']); m.box('muro_corte', a[0], ALT, a[1], b[0], ALT + 0.001, b[1], faces=['py'])
for w in g['ventanas']:
    a, b = P(w['x0'], w['y0']), P(w['x1'], w['y1'])
    (m_sala if w is SALA_V else m).box('muro', a[0], 0, a[1], b[0], SUP['antepecho_ventana'], b[1])
    m.box('muro', a[0], SUP['dintel_ventana'], a[1], b[0], ALT, b[1], faces=['px', 'nx', 'pz', 'nz', 'ny'])
    m.box('muro_corte', a[0], ALT, a[1], b[0], ALT + 0.001, b[1], faces=['py'])
node102('ARQ_Dinteles_Antepechos', m, 'provisional', 'Vanos del DWG; alturas de dintel y antepecho supuestas', 'arquitectura')
node102('ILU_Antepecho_sala', m_sala, 'provisional', 'Antepecho supuesto de la ventana de la sala (se retira con el balcón propuesto)', 'sin_balcon')

WET = ('bano_social', 'bano_principal', 'ropas')
for r in g['espacios']:
    m = Mesh()
    for x0, y0, x1, y1 in r['piso_rectangulos']:
        a, b = P(x0, y0), P(x1, y1)
        m.box('piso_ceramica' if r['id'] in WET else 'piso_madera', a[0], -0.02, a[1], b[0], 0, b[1], faces=['py'])
    node102(f"ARQ_Piso_{r['id']}", m, 'propuesta', f"{r['nombre']} ({r['area_neta_m2']} m² netos) · espacio de la propuesta", 'arquitectura')
m = Mesh()
for x0, y0, x1, y1 in g['umbrales']:
    a, b = P(x0, y0), P(x1, y1)
    m.box('piso_madera', a[0], -0.02, a[1], b[0], 0, b[1], faces=['py'])
node102('ARQ_Piso_umbrales', m, 'propuesta', 'Umbrales de los vanos de la propuesta', 'arquitectura')
m = Mesh(); a, b = P(0, 0), P(W, H); m.box('losa', a[0], -SUP['losa'], a[1], b[0], -0.02, b[1])
node102('ARQ_Losa', m, 'provisional', 'Losa ilustrativa: espesor no indicado en el DWG', 'arquitectura')
m = Mesh()
for r in g['espacios']:
    for x0, y0, x1, y1 in r['piso_rectangulos']:
        a, b = P(x0, y0), P(x1, y1); m.box('cielo', a[0], ALT - 0.005, a[1], b[0], ALT, b[1], faces=['ny'])
node102('ARQ_Cielo', m, 'provisional', 'Cielo raso a altura supuesta', 'cielo')

# ------------------------------------------------------------------ ventanas, puertas y marcos
def window(m, w):
    a, b = P(w['x0'], w['y0']), P(w['x1'], w['y1'])
    y0, y1 = SUP['antepecho_ventana'], SUP['dintel_ventana']
    zc = (a[1] + b[1]) / 2
    m.box('marco', a[0], y0, zc - 0.035, b[0], y0 + 0.05, zc + 0.035); m.box('marco', a[0], y1 - 0.05, zc - 0.035, b[0], y1, zc + 0.035)
    m.box('marco', a[0], y0, zc - 0.035, a[0] + 0.05, y1, zc + 0.035); m.box('marco', b[0] - 0.05, y0, zc - 0.035, b[0], y1, zc + 0.035)
    n = max(1, round((b[0] - a[0]) / 1.0))
    for i in range(1, n):
        xm = a[0] + (b[0] - a[0]) * i / n; m.box('marco', xm - 0.025, y0, zc - 0.035, xm + 0.025, y1, zc + 0.035)
    m.box('vidrio', a[0] + 0.05, y0 + 0.05, zc - 0.005, b[0] - 0.05, y1 - 0.05, zc + 0.005)
    zi = min(a[1], b[1])
    m.box('alfeizar', a[0] - 0.03, y0 - 0.025, zi - 0.045, b[0] + 0.03, y0, zc - 0.035)


m = Mesh()
for w in g['ventanas']:
    if w is not SALA_V:
        window(m, w)
node102('ILU_Ventaneria', m, 'ilustrativo', 'Marcos y vidrios ilustrativos en vanos de fachada del DWG', 'ilustrativo')
m = Mesh(); window(m, SALA_V)
node102('ILU_Ventana_sala', m, 'provisional', 'Ventana ilustrativa de la sala en el vano de 2,449 m del DWG', 'sin_balcon')

for d in g['puertas']:
    ent = d['id'] == 'entrada'
    if d['tipo'] == 'batiente':
        hx, hy = d['bisagra']; ang = d['angulo']
        wid = d['ancho'] - 0.02; th = 0.025 if ent else 0.02; mat = 'puerta_entrada' if ent else 'carpinteria'
        m = Mesh()
        m.rbox(mat, 0, 0.005, -th, wid, HP - 0.01, th, 0.004, k=1)
        if ent:
            for yy in (0.55, 1.05, 1.55):
                m.box('metal_negro', 0.08, yy, -th - 0.002, wid - 0.08, yy + 0.008, th + 0.002)
        for s in (-1, 1):
            m.cyl('cromo', wid - 0.07, 1.0, s * (th + 0.012), 0.025, 0.006, seg=16)
            m.rbox('cromo', wid - 0.20, 0.99, s * (th + 0.025) - 0.009, wid - 0.06, 1.01, s * (th + 0.025) + 0.009, 0.008, k=2)
        t = P(hx, hy)
        ex_, ey_ = hx + wid * math.cos(math.radians(ang)), hy + wid * math.sin(math.radians(ang))
        seg = [round(hx, 3), round(hy, 3), round(ex_, 3), round(ey_, 3), 0.045]
        nodes.append((f"ILU_Puerta_{d['id']}", m, {'verificado': False, 'fuente': f"Hoja ilustrativa de {d['ancho']} m" + (' en el vano de acceso del DWG' if ent else ' (puerta de la propuesta)'),
                      'grupo': 'ilustrativo' if ent else 'rediseno', 'categoria': 'ilustrativo' if ent else 'propuesta', 'segmentos': [] if ent else [seg]},
                      (t[0], 0, t[1]), ang))
    else:   # corrediza
        x0, y0, x1, y1 = d['rect']; m = Mesh()
        yc = y0 - 0.025   # cara del hall
        if d['id'] == 'bano_social':   # corrediza de granero estacionada sobre el muro, a la derecha del vano
            B(m, 'carpinteria', x1 - 0.03, yc - 0.03, x1 + d['ancho'] + 0.02, yc, 0.01, HP)
            B(m, 'metal_negro', x0 - 0.05, yc - 0.035, x1 + d['ancho'] + 0.08, yc - 0.01, HP + 0.02, HP + 0.06)
            B(m, 'metal_negro', x1 + 0.03, yc - 0.06, x1 + 0.05, yc - 0.03, 0.85, 1.25)
        elif d.get('acabado'):         # oculta: hoja cerrada al ras del muro, con su acabado; el visor la abre al acercarse
            yc_ = (y0 + y1) / 2
            B(m, 'muro', x0, yc_ - 0.018, x1 - 0.002, yc_ + 0.018, 0.0, ALT - 0.004)
            B(m, 'metal_negro', x0 + 0.03, yc_ - 0.0185, x0 + 0.045, yc_ - 0.017, 0.90, 1.20)   # uñero vertical
            B(m, 'metal_negro', x0 + 0.03, yc_ + 0.017, x0 + 0.045, yc_ + 0.0185, 0.90, 1.20)
            nodes.append((f"ILU_Puerta_{d['id']}", m, {'verificado': False, 'fuente': f"Puerta corrediza oculta de {d['ancho']} m (propuesta): se abre al acercarse",
                          'grupo': 'rediseno', 'categoria': 'propuesta', 'corrediza': {'recorrido': round(x1 - x0 - 0.02, 3)}}, (0, 0, 0), 0.0))
            continue
        else:                          # de bolsillo: la hoja se guarda dentro del muro, solo se ve el canto
            B(m, 'carpinteria', x1 - 0.04, (y0 + y1) / 2 - 0.02, x1, (y0 + y1) / 2 + 0.02, 0.01, HP)
        node102(f"ILU_Puerta_{d['id']}", m, 'propuesta', f"Puerta corrediza de {d['ancho']} m (propuesta)", 'rediseno')

m = Mesh()
for d in [*g['puertas'], *g['vanos']]:
    if d.get('acabado'):
        continue                     # puerta oculta: vano a toda altura, sin marco
    x0, y0, x1, y1 = d['rect']; mat = 'marco_puerta'
    if (x1 - x0) > (y1 - y0):
        B(m, mat, x0, y0 - 0.012, x0 + 0.02, y1 + 0.012, 0, HP); B(m, mat, x1 - 0.02, y0 - 0.012, x1, y1 + 0.012, 0, HP)
        B(m, mat, x0, y0 - 0.012, x1, y1 + 0.012, HP - 0.02, HP)
    else:
        B(m, mat, x0 - 0.012, y0, x1 + 0.012, y0 + 0.02, 0, HP); B(m, mat, x0 - 0.012, y1 - 0.02, x1 + 0.012, y1, 0, HP)
        B(m, mat, x0 - 0.012, y0, x1 + 0.012, y1, HP - 0.02, HP)
node102('ILU_Marcos_puertas', m, 'ilustrativo', 'Marcos enrasados al muro, sin molduras (ilustrativos)', 'ilustrativo')

# ------------------------------------------------------------------ acabados
m = Mesh()
clad(m, 'revestimiento_bano', 'bano_principal', 0, ALT - 0.002, huecos=[('n', 5.20, 5.90, 1.05, 1.38)])   # travertino a toda altura, nicho en la ducha
clad(m, 'revestimiento_bano', 'bano_social', 0, ALT - 0.002, huecos=[('n', 3.95, 4.50, 1.05, 1.38)])
clad(m, 'revestimiento_ropas', 'ropas', 0, 1.30)
wall_quad(m, 'salpicadero', 's', 1.50, 7.445, 2.95, 7.445, 0.90, ALT - 0.002)   # travertino hasta el cielo
node102('ILU_Revestimientos', m, 'ilustrativo', 'Revestimientos de travertino: baños a toda altura, ropas (1,30 m) y fondo de la cocina hasta el cielo', 'acabados')
m = Mesh()
for rid in ('social', 'hall', 'habitacion_2', 'principal', 'vestier'):
    for side, xa, ya, xb, yb in wall_runs(rid):
        t = 0.008                     # zócalo bajo y delgado, del color del muro
        if side == 's':
            B(m, 'guardaescoba', xa, ya, xb, ya + t, 0, 0.05)
        elif side == 'n':
            B(m, 'guardaescoba', xa, ya - t, xb, ya, 0, 0.05)
        elif side == 'o':
            B(m, 'guardaescoba', xa, ya, xa + t, yb, 0, 0.05)
        else:
            B(m, 'guardaescoba', xa - t, ya, xa, yb, 0, 0.05)
node102('ILU_Guardaescobas', m, 'ilustrativo', 'Guardaescobas ilustrativos', 'acabados')
m = Mesh()
DOWN = {'social': [(1.37, 1.0), (1.37, 2.3), (1.15, 3.75), (2.1, 5.6), (1.6, 6.4), (2.9, 6.8)], 'hall': [(3.4, 4.25), (4.6, 4.25)], 'habitacion_2': [(3.4, 1.8), (4.6, 1.8)],
        'principal': [(6.0, 1.2), (7.0, 4.1)], 'bano_principal': [(5.75, 5.6), (5.75, 7.0)], 'vestier': [(7.05, 5.9)], 'bano_social': [(4.22, 5.6)], 'ropas': [(3.1, 5.0)]}
for pts in DOWN.values():
    for x, y in pts:
        CY(m, 'cromo', x, y, 0.055, ALT - 0.012, 0.008, seg=20); CY(m, 'luz_calida', x, y, 0.042, ALT - 0.016, 0.006, seg=20)
node102('ILU_Luminarias', m, 'ilustrativo', 'Luminarias empotradas ilustrativas', 'cielo', puntos=DOWN)

# ------------------------------------------------------------------ APARATOS EN POSICIÓN PROPUESTA
fx = {f['id']: f for f in g['aparatos']}
MOBI = g['mobiliario']

# Cocina, baños y ropas en versión de presentación (ver tools/interiores_premium.py)
exec(open(Path(__file__).with_name('interiores_premium.py'), encoding='utf-8').read())

# ------------------------------------------------------------------ MOBILIARIO ILUSTRATIVO
def furn(name, build, huella=(), nota='Mobiliario de presentación ilustrativo', group='mobiliario', **kw):
    mm = Mesh(); build(mm); node102(name, mm, 'ilustrativo' if group == 'mobiliario' else 'propuesta', nota, group, huella=[list(map(float, h)) for h in huella], **kw)


# Muebles de terceros (Khronos glTF-Sample-Assets, ver modelo/muebles/CREDITOS.md): el nodo solo lleva la
# posición; el visor coloca el modelo. Caja del modelo con el frente hacia +Z (convención glTF).
MODELOS = {'sofa': ([-1.114, 0.0, -0.628], [1.074, 0.788, 0.395]), 'butaca': ([-0.414, 0.0, -0.277], [0.413, 0.686, 0.294])}
RY = {'s': 0.0, 'e': 90.0, 'n': 180.0, 'o': -90.0}


def modelo(name, clave, rect, frente, nota, escala_max=1.0):
    (mx0, my0, mz0), (mx1, my1, mz1) = MODELOS[clave]
    x0, y0, x1, y1 = rect; ry = RY[frente]
    ancho, fondo = mx1 - mx0, mz1 - mz0                       # ancho a lo largo del frente
    lx, ly = (fondo, ancho) if frente in ('e', 'o') else (ancho, fondo)
    sc = min(escala_max, (x1 - x0) / lx, (y1 - y0) / ly)
    c, s_ = math.cos(math.radians(ry)), math.sin(math.radians(ry))
    cx_, cz_ = (mx0 + mx1) / 2 * sc, (mz0 + mz1) / 2 * sc
    rx, rz = cx_ * c + cz_ * s_, -cx_ * s_ + cz_ * c           # centro de la caja tras girar
    tx, tz = P((x0 + x1) / 2, (y0 + y1) / 2)
    fx0, fy0 = (x0 + x1) / 2 - lx * sc / 2, (y0 + y1) / 2 - ly * sc / 2
    hue = [round(fx0, 3), round(fy0, 3), round(fx0 + lx * sc, 3), round(fy0 + ly * sc, 3)]
    nodes.append((name, Mesh(), {'verificado': False, 'fuente': nota, 'grupo': 'mobiliario', 'categoria': 'ilustrativo', 'modelo': clave,
                                 'escala': round(sc, 4), 'huella': [hue]}, (tx - rx, 0.0, tz - rz), ry))


modelo('MOB_Sofa', 'sofa', MOBI['sofa'], 'e', 'Sofá ilustrativo (modelo GlamVelvetSofa, CC BY 4.0, Wayfair LLC / Khronos)')
modelo('MOB_Butaca_sala', 'butaca', MOBI['butaca'], 'n', 'Butaca ilustrativa (modelo SheenChair, CC0, Wayfair LLC / Khronos)')
modelo('MOB_Butaca_principal', 'butaca', MOBI['butaca_p'], 'n', 'Butaca ilustrativa (modelo SheenChair, CC0, Wayfair LLC / Khronos)')


# Mobiliario, cortinas y cielos de presentación (ver tools/mobiliario_premium.py)
exec(open(Path(__file__).with_name('mobiliario_premium.py'), encoding='utf-8').read())

# ------------------------------------------------------------------ BALCÓN PROPUESTO (no figura en el DWG)
if PROP:
    src = PROP['fuente']
    lx0, ly0, lx1, ly1 = PROP['losa']['rect']; esp = PROP['losa']['espesor']; dn = PROP['losa']['desnivel']
    m = Mesh(); a, b = P(lx0, ly0), P(lx1, ly1)
    m.box('losa', a[0], -dn - esp, a[1], b[0], -dn - 0.02, b[1])
    m.box('piso_exterior', a[0], -dn - 0.02, a[1], b[0], -dn, b[1], faces=['py', 'pz', 'px', 'nx'])
    m.box('marco', a[0], -dn - esp - 0.01, a[1], b[0], -dn - esp, a[1] + 0.06)
    node102('PROP_Balcon_losa', m, 'propuesta', src, 'propuesta')
    m = Mesh(); hb = PROP['baranda']['altura'] - dn
    ux0, uy0, ux1, uy1 = PROP['rect_util']
    xw, xe, ys = ux0 - 0.01, ux1 + 0.01, uy0 - 0.01
    for (x0_, y0_, x1_, y1_) in ((xw - 0.012, ys, xw, uy1), (xe, ys, xe + 0.012, uy1), (xw, ys - 0.012, xe, ys)):
        p0, p1 = P(x0_, y0_), P(x1_, y1_)
        m.box('vidrio_baranda', p0[0], -dn + 0.06, p0[1], p1[0], -dn + hb - 0.03, p1[1])
        m.box('marco', p0[0] - 0.012, -dn, p0[1] - 0.012, p1[0] + 0.012, -dn + 0.06, p1[1] + 0.012)
        lo = np.minimum(p0, p1); hi = np.maximum(p0, p1)
        m.rbox('metal_negro', lo[0] - 0.012, -dn + hb - 0.03, lo[1] - 0.012, hi[0] + 0.012, -dn + hb, hi[1] + 0.012, 0.004, k=1)   # perfil superior fino
    node102('PROP_Balcon_baranda', m, 'propuesta', src + ' Baranda ilustrativa de 1,05 m.', 'propuesta')
    m = Mesh(); ac = PROP['acceso']; vx0, vy0, vx1, vy1 = ac['vano']; hp = ac['altura']
    a, b = P(vx0, vy0), P(vx1, vy1); z0_, z1_ = min(a[1], b[1]), max(a[1], b[1])
    m.box('marco', a[0], 0, z0_, b[0], 0.03, z1_); m.box('marco', a[0], hp - 0.05, z0_, b[0], hp, z1_)
    m.box('marco', a[0], 0, z0_, a[0] + 0.05, hp, z1_); m.box('marco', b[0] - 0.05, 0, z0_, b[0], hp, z1_)
    cx0, cx1 = ac['hojas_cerradas']; mid = (cx0 + cx1) / 2
    for k, (hx0, hx1) in enumerate(((cx0, mid + 0.03), (mid - 0.03, cx1))):
        za = z0_ + 0.035 + k * 0.05; p0, p1 = P(hx0, 0), P(hx1, 0)
        for (fx0, fy0, fx1, fy1) in ((p0[0], 0.03, p0[0] + 0.05, hp - 0.05), (p1[0] - 0.05, 0.03, p1[0], hp - 0.05), (p0[0], 0.03, p1[0], 0.10), (p0[0], hp - 0.12, p1[0], hp - 0.05)):
            m.box('marco', fx0, fy0, za, fx1, fy1, za + 0.04)
        m.box('vidrio', p0[0] + 0.05, 0.10, za + 0.014, p1[0] - 0.05, hp - 0.12, za + 0.026)
    node102('PROP_Puerta_ventana_sala', m, 'propuesta', src + ' Puerta-ventana corrediza en el vano de 2,449 m del DWG.', 'propuesta')

    def balcon(m):
        """Dos tumbonas bajas de teca con cojines de exterior, mesa de travertino y jardinera de gramíneas."""
        z = -dn
        for x0_ in (0.20, 0.72):
            x1_ = x0_ + 0.48; y0_, y1_ = -0.82, -0.22
            for xx in (x0_ + 0.03, x1_ - 0.03):                                           # laterales de teca
                TU(m, 'madera_mueble', [(xx, y0_ + 0.03, z), (xx, y0_ + 0.03, z + 0.30), (xx, y1_ - 0.05, z + 0.32), (xx, y1_ - 0.03, z + 0.72)], 0.018, seg=10)
                TU(m, 'madera_mueble', [(xx, y1_ - 0.05, z), (xx, y1_ - 0.05, z + 0.32)], 0.018, seg=10)
            RB(m, 'madera_mueble', x0_ + 0.03, y0_ + 0.02, x1_ - 0.03, y1_ - 0.04, z + 0.28, z + 0.31, 0.01, k=1)
            SOFT(m, 'tela_cama', x0_ + 0.045, y0_ + 0.03, x1_ - 0.045, y1_ - 0.06, z + 0.30, z + 0.42, 0.35, 0.25, 26, 10)
            SOFT(m, 'tela_cama', x0_ + 0.05, y1_ - 0.20, x1_ - 0.05, y1_ - 0.05, z + 0.38, z + 0.74, 0.4, 0.3, 24, 12,
                 lambda x, y, zz: (x, y, zz - 0.25 * (y + 0.18) if y > -0.18 else zz))
            SOFT(m, 'tela_acento', x0_ + 0.12, y1_ - 0.30, x1_ - 0.12, y1_ - 0.18, z + 0.42, z + 0.66, 0.5, 0.3, 20, 10)
        LA(m, 'meson', 0.70, -1.17, z, [(0.0, 0.0), (0.12, 0.0), (0.10, 0.04), (0.08, 0.38), (0.21, 0.40), (0.22, 0.43), (0.0, 0.43)], seg=40)
        LA(m, 'ceramica_deco', 0.70, -1.17, z + 0.43, [(0.0, 0.0), (0.04, 0.0), (0.05, 0.06), (0.03, 0.12), (0.0, 0.12)], seg=18)
        a0, b0, a1, b1 = MOBI['balcon_jardinera']
        RB(m, 'laca_mueble', a0, b0, a1, b1, z, z + 0.42, 0.01, k=1)
        B(m, 'cesped_maceta', a0 + 0.02, b0 + 0.02, a1 - 0.02, b1 - 0.02, z + 0.40, z + 0.405)
        for i in range(70):                                                                 # gramíneas: hojas largas que se arquean
            bx = rng.uniform(a0 + 0.04, a1 - 0.04); by = rng.uniform(b0 + 0.05, b1 - 0.05); h = rng.uniform(0.35, 0.75)
            ang = rng.uniform(0, 2 * math.pi); lean = rng.uniform(0.08, 0.30)
            pts = [(bx + math.cos(ang) * lean * h * t * t, by + math.sin(ang) * lean * h * t * t, z + 0.40 + h * t - 0.15 * h * t ** 3) for t in np.linspace(0, 1, 6)]
            TU(m, 'vegetal', pts, [0.004 * (1 - 0.85 * t) for t in np.linspace(0, 1, 6)], seg=4)
        RB(m, 'textil_tapete', 0.17, -1.52, 1.27, -0.18, z, z + 0.008, 0.004, k=1)

    furn('MOB_Balcon', balcon, [MOBI['balcon_sillas'], MOBI['balcon_jardinera']], nota='Mobiliario ilustrativo del balcón propuesto', group='propuesta_mobiliario')

# ------------------------------------------------------------------ escritura GLB
buf = bytearray(); views = []; accessors = []; meshes = []; gl_nodes = []; materials = []; mat_index = {}


def add_view(data, target):
    global buf
    while len(buf) % 4:
        buf += b'\0'
    off = len(buf); buf += data
    views.append({'buffer': 0, 'byteOffset': off, 'byteLength': len(data), 'target': target})
    return len(views) - 1


def mat_id(name):
    if name not in mat_index:
        col, rough, metal, opt = MATS[name]
        mt = {'name': name, 'pbrMetallicRoughness': {'baseColorFactor': col, 'roughnessFactor': rough, 'metallicFactor': metal}}
        if col[3] < 1:
            mt['alphaMode'] = 'BLEND'; mt['doubleSided'] = True
        if opt.get('double'):
            mt['doubleSided'] = True
        if opt.get('emissive'):
            mt['emissiveFactor'] = opt['emissive']
        mat_index[name] = len(materials); materials.append(mt)
    return mat_index[name]


tri_count = 0
for name, mesh, extras, t, ry in nodes:
    prims = []
    for mname, (pos, nor, uv, idx) in mesh.parts.items():
        if not idx:
            continue
        p = np.array(pos, np.float32); n = np.array(nor, np.float32); u = np.array(uv, np.float32)
        ln = np.linalg.norm(n, axis=1, keepdims=True); n = n / np.where(ln == 0, 1, ln)
        it = np.array(idx, np.uint32); tri_count += len(it) // 3
        vp, vn, vu = (add_view(a.tobytes(), 34962) for a in (p, n, u))
        vi = add_view(it.tobytes(), 34963)
        a0 = len(accessors)
        accessors += [
            {'bufferView': vp, 'componentType': 5126, 'count': len(p), 'type': 'VEC3', 'min': p.min(0).tolist(), 'max': p.max(0).tolist()},
            {'bufferView': vn, 'componentType': 5126, 'count': len(n), 'type': 'VEC3'},
            {'bufferView': vu, 'componentType': 5126, 'count': len(u), 'type': 'VEC2'},
            {'bufferView': vi, 'componentType': 5125, 'count': len(it), 'type': 'SCALAR'},
        ]
        prims.append({'attributes': {'POSITION': a0, 'NORMAL': a0 + 1, 'TEXCOORD_0': a0 + 2}, 'indices': a0 + 3, 'material': mat_id(mname)})
    if not prims and not extras.get('modelo'):
        continue
    nd = {'name': name, 'extras': extras}
    if prims:
        meshes.append({'name': name, 'primitives': prims}); nd['mesh'] = len(meshes) - 1
    if any(t):
        nd['translation'] = list(t)
    if ry:
        h = math.radians(ry) / 2
        nd['rotation'] = [0, math.sin(h), 0, math.cos(h)]
    gl_nodes.append(nd)

root = {'name': 'Apto_102_Torre_1_Propuesta', 'children': list(range(len(gl_nodes))),
        'extras': {'proyecto': g['proyecto'], 'torre': g['torre'], 'apartamento': g['apartamento'], 'supuestos_visualizacion': SUP,
                   'estado': g['estado'], 'rotulo': g['rotulo'], 'advertencia': g['advertencia'],
                   'propuestas': ([{k: PROP[k] for k in ('id', 'estado', 'fuente', 'area_util_m2', 'requiere_validacion')}] if PROP else []),
                   'areas': g['areas'], 'espacios': {e['id']: e['area_neta_m2'] for e in g['espacios']}, 'sistema': 'X este, Z sur, Y arriba; metros; centro = centro de la envolvente',
                   'categorias': {'verificado': 'Envolvente, vanos de fachada, acceso y ductos del DWG', 'provisional': 'Medida no documentada en el DWG (alturas, losa, cielo)',
                                  'ilustrativo': 'Mobiliario, acabados y carpintería de presentación', 'propuesta': 'Redistribución interior y balcón propuestos, sin validar'}}}
gl_nodes.append(root)
gltf = {'asset': {'version': '2.0', 'generator': 'ORA AI Explorer · apartamento-102/tools/generar_glb.py'}, 'scene': 0,
        'scenes': [{'name': 'Apartamento 102 · propuesta de redistribución', 'nodes': [len(gl_nodes) - 1]}], 'nodes': gl_nodes, 'meshes': meshes,
        'materials': materials, 'accessors': accessors, 'bufferViews': views, 'buffers': [{'byteLength': len(buf)}]}
js = json.dumps(gltf, ensure_ascii=False, separators=(',', ':')).encode('utf8')
js += b' ' * ((4 - len(js) % 4) % 4)
while len(buf) % 4:
    buf += b'\0'
with open(OUT, 'wb') as f:
    f.write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(buf)))
    f.write(struct.pack('<II', len(js), 0x4E4F534A)); f.write(js)
    f.write(struct.pack('<II', len(buf), 0x004E4942)); f.write(buf)
print(OUT, len(gl_nodes) - 1, 'nodos', len(materials), 'materiales', tri_count, 'triángulos', round((len(js) + len(buf)) / 1024), 'KB')
