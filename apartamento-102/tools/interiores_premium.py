# Interiores del apartamento 102 en versión de presentación: cocina, baños, ropas, sala, habitaciones,
# corredor y balcón. Se ejecuta dentro de tools/generar_glb.py (comparte sus ayudas: B, RB, SOFT, TU, LA,
# CY, SP, clad, nicho, wall_quad, furn, node102, fx, MOBI, ALT, HP, rng).
#
# Lenguaje común (referencias aprobadas por el cliente, adaptadas a la geometría del 102):
#   roble claro natural (gabinete_cocina, madera_mueble), travertino claro (meson, salpicadero, revestimientos),
#   laca arena mate (laca_mueble, mueble_bano), latón cepillado en la cocina y negro mate en baños y detalles.
# Todo es ILUSTRATIVO: no cambia la distribución ni las huellas de la propuesta.

J = 0.0015   # junta entre frentes de carpintería


def frente(m, mat, x0, y0, x1, y1, z0, z1, cara):
    """Frente de 19 mm (puerta o cajón) con junta perimetral; cara = lado visible ('n','s','e','o')."""
    jx = J if cara in 'ns' else 0.0; jy = J if cara in 'eo' else 0.0
    RB(m, mat, x0 + jx, y0 + jy, x1 - jx, y1 - jy, z0 + J, z1 - J, 0.0025, k=1)


def tirador_v(m, mat, x, y, z0, z1, cara, sep=0.022):
    """Tirador vertical de barra fina con dos patas."""
    d = {'n': (0, 1), 's': (0, -1), 'e': (1, 0), 'o': (-1, 0)}[cara]
    px, py = x + d[0] * sep, y + d[1] * sep
    TU(m, mat, [(px, py, z0), (px, py, z1)], 0.0055, seg=10)
    for z in (z0 + 0.02, z1 - 0.02):
        TU(m, mat, [(x, y, z), (px, py, z)], 0.0045, seg=8)


def tirador_h(m, mat, x0, x1, y, z, cara, sep=0.022, eje='x'):
    d = {'n': (0, 1), 's': (0, -1), 'e': (1, 0), 'o': (-1, 0)}[cara]
    if eje == 'x':
        pts = [(x0, y + d[1] * sep, z), (x1, y + d[1] * sep, z)]; patas = [(x0 + 0.02, y, z), (x1 - 0.02, y, z)]
        TU(m, mat, pts, 0.0055, seg=10)
        for (px, py, pz) in patas:
            TU(m, mat, [(px, py, pz), (px, py + d[1] * sep, pz)], 0.0045, seg=8)
    else:
        pts = [(y + d[0] * sep, x0, z), (y + d[0] * sep, x1, z)]
        TU(m, mat, pts, 0.0055, seg=10)
        for yy in (x0 + 0.02, x1 - 0.02):
            TU(m, mat, [(y, yy, z), (y + d[0] * sep, yy, z)], 0.0045, seg=8)


def ramas(m, x, y, z0, n=5, alto=0.55):
    """Ramas secas en un jarrón (decoración mínima de la referencia de cocina)."""
    LA(m, 'ceramica_deco', x, y, z0, [(0.045, 0), (0.07, 0.06), (0.075, 0.12), (0.05, 0.2), (0.028, 0.24), (0.032, 0.26), (0.0, 0.26)], seg=28)
    for i in range(n):
        a = rng.uniform(0, 2 * math.pi); inc = rng.uniform(0.05, 0.22)
        pts = []
        for k in range(9):
            t = k / 8; zz = z0 + 0.2 + t * alto * rng.uniform(0.85, 1.05)
            pts.append((x + math.cos(a) * inc * t * alto + 0.01 * math.sin(7 * t), y + math.sin(a) * inc * t * alto, zz))
        TU(m, 'rama_seca', pts, [0.004 * (1 - 0.7 * k / 8) for k in range(9)], seg=5)
        for k in (3, 5, 7):   # ramillas con bayas
            px, py, pz = pts[k]; b = a + rng.uniform(-1.2, 1.2)
            q = (px + math.cos(b) * 0.06, py + math.sin(b) * 0.06, pz + 0.05)
            TU(m, 'rama_seca', [(px, py, pz), q], 0.002, seg=4)
            SP(m, 'ceramica_deco', q[0], q[1], q[2], 0.009, seg=8)


# ====================================================================== COCINA (referencia 2)
m = Mesh()
x0, y0, x1, y1 = fx['meson_norte']['rect']           # 1,50–2,95 × 6,85–7,45
ex0, ey0, ex1, ey1 = fx['estufa']['rect']
B(m, 'carcasa', x0, y0 + 0.02, x1, y1, 0.10, 0.86)
B(m, 'metal_negro', x0 + 0.002, y0 + 0.07, x1 - 0.002, y1, 0.0, 0.10)                       # zócalo retranqueado
RB(m, 'gabinete_cocina', x0, y0 + 0.02, x0 + 0.02, y1, 0.0, 0.86, 0.002, k=1)                 # costado visible al ingreso
mods = [(x0, ex0, 'puerta'), (ex0, ex1, 'horno'), (ex1, x1, 'cajones')]
for a, b, tipo in mods:
    if tipo == 'puerta':
        frente(m, 'gabinete_cocina', a + 0.02, y0, b, y0 + 0.02, 0.10, 0.86, 's'); tirador_v(m, 'laton_cepillado', b - 0.05, y0, 0.58, 0.80, 's')
    elif tipo == 'horno':          # horno integrado con frente de vidrio negro y cajón bajo
        frente(m, 'gabinete_cocina', a, y0, b, y0 + 0.02, 0.10, 0.27, 's')
        RB(m, 'vidrio_negro', a + J, y0 - 0.002, b - J, y0 + 0.02, 0.275, 0.855, 0.004, k=1)
        B(m, 'electro', a + 0.02, y0 - 0.004, b - 0.02, y0, 0.80, 0.84)
        TU(m, 'laton_cepillado', [(a + 0.06, y0 - 0.03, 0.76), (b - 0.06, y0 - 0.03, 0.76)], 0.007, seg=10)
        tirador_h(m, 'laton_cepillado', a + 0.20, b - 0.20, y0, 0.24, 's')
    else:
        for (za, zb) in ((0.10, 0.48), (0.48, 0.86)):
            frente(m, 'gabinete_cocina', a, y0, b, y0 + 0.02, za, zb, 's')
            tirador_h(m, 'laton_cepillado', a + 0.10, b - 0.10, y0, zb - 0.06, 's')
B(m, 'meson', x0, y0 - 0.02, x1, y1, 0.86, 0.90)                                             # mesón de travertino de 4 cm
RB(m, 'vidrio_negro', ex0, ey0, ex1, ey1, 0.899, 0.904, 0.003, k=1)                          # cubierta de inducción enrasada
for i in range(2):
    for j in range(2):
        cx_ = ex0 + 0.15 + i * 0.30; cy_ = ey0 + 0.11 + j * 0.22
        LA(m, 'acero', cx_, cy_, 0.9042, [(0.085 - 0.012 * j, 0), (0.087 - 0.012 * j, 0.0003), (0.0, 0.0003)], seg=36)
        LA(m, 'vidrio_negro', cx_, cy_, 0.9043, [(0.083 - 0.012 * j, 0), (0.0, 0.0002)], seg=36)
# campana integrada en un volumen de roble hasta el cielo, repisas flotantes con luz y travertino de fondo
hx0, hx1 = ex0 - 0.03, ex1 + 0.03
B(m, 'carcasa', hx0, 7.08, hx1, y1, 1.62, ALT - 0.002)
for (a, b) in ((hx0, (hx0 + hx1) / 2), ((hx0 + hx1) / 2, hx1)):
    frente(m, 'gabinete_cocina', a, 7.06, b, 7.08, 1.64, ALT - 0.004, 's')
B(m, 'electro', hx0 + 0.02, 7.09, hx1 - 0.02, y1 - 0.02, 1.615, 1.62)
B(m, 'luz_calida', hx0 + 0.04, 7.10, hx1 - 0.04, 7.12, 1.612, 1.615)
for (a, b) in ((x0, hx0 - 0.03), (hx1 + 0.03, x1)):
    for zz in (1.30, 1.72):
        RB(m, 'gabinete_cocina', a, 7.20, b, y1, zz, zz + 0.04, 0.004, k=1)
        B(m, 'luz_calida', a + 0.03, 7.22, b - 0.03, 7.24, zz - 0.003, zz)
# objetos en las repisas y el mesón (pocos y escogidos)
LA(m, 'ceramica_deco', x0 + 0.12, 7.32, 1.34, [(0.045, 0), (0.06, 0.05), (0.05, 0.16), (0.02, 0.2), (0.022, 0.22), (0.0, 0.22)], seg=24)
for k in range(4):
    LA(m, 'ceramica_calida', x0 + 0.27, 7.33, 1.34 + k * 0.016, [(0.09, 0), (0.105, 0.014), (0.0, 0.014)], seg=28)
LA(m, 'ceramica_deco', x1 - 0.12, 7.32, 1.76, [(0.04, 0), (0.07, 0.04), (0.065, 0.12), (0.03, 0.17), (0.0, 0.17)], seg=24)
B(m, 'madera_mueble', x1 - 0.30, 7.30, x1 - 0.18, 7.43, 1.76, 1.95)                           # cuadro pequeño apoyado
B(m, 'cuadro', x1 - 0.29, 7.295, x1 - 0.19, 7.30, 1.775, 1.935)
RB(m, 'madera_mueble', x0 + 0.06, 7.40, x0 + 0.40, 7.43, 0.90, 1.32, 0.01, k=1)               # tabla apoyada en el salpicadero
LA(m, 'ceramica_deco', x1 - 0.14, 7.25, 0.90, [(0.06, 0), (0.065, 0.12), (0.05, 0.16), (0.0, 0.16)], seg=24)
# columna de nevera integrada, hasta el cielo
n0, m0, n1, m1 = fx['nevera']['rect']
B(m, 'carcasa', n0, m0 + 0.02, n1, m1, 0.10, ALT - 0.002); B(m, 'metal_negro', n0 + 0.002, m0 + 0.07, n1, m1, 0, 0.10)
RB(m, 'gabinete_cocina', n0, m0 + 0.02, n0 + 0.02, m1, 0.0, ALT - 0.002, 0.002, k=1)
for (za, zb) in ((0.10, 1.48), (1.48, 2.12), (2.12, ALT - 0.004)):
    frente(m, 'gabinete_cocina', n0 + 0.02, m0, n1, m0 + 0.02, za, zb, 's')
tirador_v(m, 'laton_cepillado', n0 + 0.07, m0, 1.06, 1.42, 's'); tirador_v(m, 'laton_cepillado', n0 + 0.07, m0, 1.54, 1.90, 's')
# despensa al ingreso: dos puertas lisas hasta el cielo con apertura por presión
d0, e0, d1, e1 = MOBI['despensa']
B(m, 'carcasa', d0, e0, d1 - 0.02, e1, 0.10, ALT - 0.002); B(m, 'metal_negro', d0, e0 + 0.002, d1 - 0.07, e1 - 0.002, 0, 0.10)
for (a, b) in ((e0, (e0 + e1) / 2), ((e0 + e1) / 2, e1)):
    frente(m, 'gabinete_cocina', d1 - 0.02, a, d1, b, 0.10, ALT - 0.004, 'e')
RB(m, 'gabinete_cocina', d0, e1 - 0.02, d1, e1, 0.0, ALT - 0.002, 0.002, k=1)                # costado hacia el acceso
# península: travertino en cascada, frentes de roble hacia la cocina y panel acanalado hacia la barra
px0, py0, px1, py1 = fx['peninsula']['rect']; vol = fx['peninsula']['barra']['voladizo_sur']
sx0, sy0, sx1, sy1 = 0.96, 4.95, 1.40, 5.27                                                    # hueco del lavaplatos bajo encimera
B(m, 'carcasa', px0, py0 + vol, px1 - 0.04, py1 - 0.02, 0.10, 0.86)
B(m, 'metal_negro', px0, py0 + vol + 0.05, px1 - 0.04, py1 - 0.07, 0.0, 0.10)
frente(m, 'gabinete_cocina', px0, py1 - 0.02, 0.75, py1, 0.10, 0.86, 'n')                     # lavavajillas integrado
tirador_h(m, 'laton_cepillado', px0 + 0.15, 0.60, py1, 0.80, 'n')
for (a, b) in ((0.75, 1.155), (1.155, px1 - 0.04)):
    frente(m, 'gabinete_cocina', a, py1 - 0.02, b, py1, 0.10, 0.86, 'n')
tirador_v(m, 'laton_cepillado', 1.12, py1, 0.58, 0.80, 'n'); tirador_v(m, 'laton_cepillado', 1.19, py1, 0.58, 0.80, 'n')
B(m, 'gabinete_cocina', px0, py0 + vol - 0.02, px1 - 0.04, py0 + vol, 0.0, 0.86)              # panel de rodillas
for k in range(int((px1 - 0.04 - px0 - 0.02) / 0.036)):                                     # acanalado de roble
    CY(m, 'gabinete_cocina', px0 + 0.03 + k * 0.036, py0 + vol - 0.02, 0.015, 0.0, 0.855, seg=10)
B(m, 'luz_calida', px0 + 0.03, py0 + vol - 0.04, px1 - 0.06, py0 + vol - 0.02, 0.852, 0.856)  # luz rasante sobre el acanalado
RB(m, 'meson', px1 - 0.04, py0, px1, py1, 0.0, 0.90, 0.003, k=1)                              # cascada de travertino
for (a, b, c, d) in ((px0, py0, px1 - 0.04, sy0), (px0, sy1, px1 - 0.04, py1), (px0, sy0, sx0, sy1), (sx1, sy0, px1 - 0.04, sy1)):
    B(m, 'meson', a, b, c, d, 0.86, 0.90)
B(m, 'acero', sx0, sy0, sx1, sy1, 0.70, 0.705)                                                # poceta bajo encimera
for (a, b, c, d) in ((sx0, sy0, sx1, sy0 + 0.004), (sx0, sy1 - 0.004, sx1, sy1), (sx0, sy0, sx0 + 0.004, sy1), (sx1 - 0.004, sy0, sx1, sy1)):
    B(m, 'acero', a, b, c, d, 0.70, 0.86)
CY(m, 'metal_negro', (sx0 + sx1) / 2, (sy0 + sy1) / 2, 0.035, 0.705, 0.002, seg=24)
gx, gy = fx['lavaplatos']['centro'][0], 4.89                                                  # grifo de cuello de cisne en latón
CY(m, 'laton_cepillado', gx, gy, 0.026, 0.90, 0.05, seg=24)
TU(m, 'laton_cepillado', [(gx, gy, 0.94)] + [(gx, gy + 0.10 - 0.10 * math.cos(a), 1.22 + 0.10 * math.sin(a)) for a in np.linspace(0, math.pi, 14)] + [(gx, gy + 0.20, 1.13)], 0.013, seg=16)
TU(m, 'laton_cepillado', [(gx + 0.026, gy, 0.98), (gx + 0.075, gy - 0.01, 1.03)], 0.006, seg=8)
node102('APA_Cocina', m, 'propuesta', 'Cocina en U de la propuesta: roble claro, mesones de travertino de 4 cm, península con cascada y 2 puestos, inducción, horno y nevera integrados', 'aparatos',
        huella=[fx['meson_norte']['rect'], fx['peninsula']['rect'], fx['nevera']['rect'], MOBI['despensa']])

# ====================================================================== BAÑOS (referencia 3)
def lavamanos(m, rect, muro, n=1):
    """Mueble suspendido de laca arena con dos cajones, encimera integrada con poceta y grifería mural negra."""
    x0, y0, x1, y1 = rect
    if muro == 'o':      # contra el muro oeste, frente hacia el este
        B(m, 'mueble_bano', x0, y0 + 0.01, x1 - 0.02, y1 - 0.01, 0.38, 0.80)
        for (za, zb) in ((0.38, 0.60), (0.60, 0.80)):
            frente(m, 'mueble_bano', x1 - 0.02, y0 + 0.01, x1, y1 - 0.01, za, zb, 'e')
        B(m, 'luz_calida', x0 + 0.02, y0 + 0.03, x1 - 0.04, y1 - 0.03, 0.376, 0.38)           # luz bajo el mueble flotante
        cs = [y0 + (y1 - y0) * (k + 0.5) / n for k in range(n)]
        huecos = [(x0 + 0.12, c - 0.19, x1 - 0.08, c + 0.19) for c in cs]
        top = (x0, y0, x1 + 0.005, y1)
    else:                # contra el muro este, frente hacia el oeste
        B(m, 'mueble_bano', x0 + 0.02, y0 + 0.01, x1, y1 - 0.01, 0.38, 0.80)
        for (za, zb) in ((0.38, 0.60), (0.60, 0.80)):
            frente(m, 'mueble_bano', x0, y0 + 0.01, x0 + 0.02, y1 - 0.01, za, zb, 'o')
        B(m, 'luz_calida', x0 + 0.04, y0 + 0.03, x1 - 0.02, y1 - 0.03, 0.376, 0.38)
        cs = [(y0 + y1) / 2]
        huecos = [(x0 + 0.07, cs[0] - 0.17, x1 - 0.11, cs[0] + 0.17)]
        top = (x0 - 0.005, y0, x1, y1)
    tx0, ty0, tx1, ty1 = top
    # encimera de 4 cm con pocetas rebajadas (se arma alrededor de los huecos)
    ys_ = sorted({ty0, ty1, *[h[1] for h in huecos], *[h[3] for h in huecos]})
    for a, b in zip(ys_[:-1], ys_[1:]):
        h = next((h for h in huecos if h[1] <= a and b <= h[3]), None)
        if h is None:
            B(m, 'ceramica_calida', tx0, a, tx1, b, 0.80, 0.84)
        else:
            B(m, 'ceramica_calida', tx0, a, h[0], b, 0.80, 0.84); B(m, 'ceramica_calida', h[2], a, tx1, b, 0.80, 0.84)
    for (a, b, c, d) in huecos:
        SOFT(m, 'ceramica_calida', a, b, c, d, 0.70, 0.86, 0.35, 0.25, 28, 10)                 # cuenco (se ve desde arriba como poceta)
        B(m, 'ceramica_calida', a + 0.01, b + 0.01, c - 0.01, d - 0.01, 0.744, 0.746)
        CY(m, 'metal_negro', (a + c) / 2, (b + d) / 2, 0.018, 0.746, 0.002, seg=16)
        # grifería mural negra mate
        wx = x0 if muro == 'o' else x1; s_ = 1 if muro == 'o' else -1; cy_ = (b + d) / 2
        TU(m, 'metal_negro', [(wx, cy_, 1.02), (wx + s_ * 0.17, cy_, 1.02)], 0.011, seg=14)
        TU(m, 'metal_negro', [(wx + s_ * 0.17, cy_, 1.02), (wx + s_ * 0.17, cy_, 1.005)], 0.011, seg=14, cap=True)
        TU(m, 'metal_negro', [(wx, cy_ + 0.12, 1.02), (wx + s_ * 0.05, cy_ + 0.12, 1.02)], 0.013, seg=14)


def espejo_halo(m, mat, muro, a, b, z0, z1, linea):
    """Espejo de esquinas redondeadas con luz indirecta perimetral."""
    s_ = 1 if muro == 'o' else -1
    RB(m, 'luz_calida', min(linea + s_ * 0.004, linea + s_ * 0.012), a + 0.03, max(linea + s_ * 0.004, linea + s_ * 0.012), b - 0.03, z0 + 0.03, z1 - 0.03, 0.002, k=1)
    RB(m, 'metal_negro', min(linea + s_ * 0.012, linea + s_ * 0.022), a, max(linea + s_ * 0.012, linea + s_ * 0.022), b, z0, z1, 0.004, k=1)
    B(m, mat, min(linea + s_ * 0.022, linea + s_ * 0.026), a + 0.006, max(linea + s_ * 0.022, linea + s_ * 0.026), b - 0.006, z0 + 0.006, z1 - 0.006)


def sanitario(m, rect, muro):
    """Sanitario suspendido de líneas suaves, cisterna empotrada tras un murete revestido y pulsador negro."""
    x0, y0, x1, y1 = rect; cy_ = (y0 + y1) / 2
    if muro == 'o':
        B(m, 'revestimiento_bano', x0, y0 - 0.05, x0 + 0.14, y1 + 0.05, 0.0, 1.10); wx = x0 + 0.14; s_ = 1
    else:
        B(m, 'revestimiento_bano', x1 - 0.14, y0 - 0.05, x1, y1 + 0.05, 0.0, 1.10); wx = x1 - 0.14; s_ = -1
    B(m, 'metal_negro', min(wx, wx + s_ * 0.004), cy_ - 0.11, max(wx, wx + s_ * 0.004), cy_ + 0.11, 0.86, 1.00)          # pulsador
    B(m, 'carcasa', min(wx, wx + s_ * 0.0045), cy_ - 0.002, max(wx, wx + s_ * 0.0045), cy_ + 0.002, 0.87, 0.99)
    bx0, bx1 = (wx, wx + 0.52) if s_ > 0 else (wx - 0.52, wx)
    def taza(x, y, z):                                  # se estrecha hacia el frente
        f = (x - (-0.26 if s_ > 0 else 0.26)) / 0.52 * s_
        return x, y, z * (1 - 0.22 * max(0.0, f) ** 2)
    SOFT(m, 'ceramica_calida', bx0, cy_ - 0.18, bx1, cy_ + 0.18, 0.22, 0.40, 0.45, 0.55, 36, 12, taza)
    SOFT(m, 'ceramica_calida', bx0 + (0.02 if s_ > 0 else 0.02), cy_ - 0.175, bx1 - 0.02, cy_ + 0.175, 0.395, 0.425, 0.6, 0.55, 36, 8, taza)   # tapa fina


def ducha(m, rect, abertura, nicho_x):
    """Ducha a nivel de piso con rejilla lineal, mampara de vidrio con perfil negro, brazo de techo y termostática."""
    x0, y0, x1, y1 = rect
    B(m, 'rejilla', x0 + 0.05, y1 - 0.08, x1 - 0.05, y1 - 0.03, 0.0, 0.003)                   # rejilla lineal junto al muro
    gx1 = x1 - abertura
    B(m, 'vidrio_ducha', x0, y0 + 0.006, gx1, y0 + 0.014, 0.0, 2.02)
    B(m, 'metal_negro', x0, y0, x0 + 0.02, y0 + 0.02, 0.0, 2.02)                                  # perfil de muro
    B(m, 'metal_negro', x0, y0 + 0.004, gx1, y0 + 0.016, 0.0, 0.012)
    TU(m, 'metal_negro', [(gx1 - 0.01, y0 + 0.01, 2.0), (gx1 - 0.01, y1, 2.0)], 0.009, seg=10)  # barra estabilizadora en L
    B(m, 'metal_negro', gx1 - 0.012, y0 + 0.004, gx1, y0 + 0.016, 0.0, 2.02)
    hx = (x0 + x1) / 2
    TU(m, 'metal_negro', [(hx, y1, 2.18), (hx, y1 - 0.28, 2.18)], 0.011, seg=12)                # brazo de pared
    LA(m, 'metal_negro', hx, y1 - 0.38, 2.15, [(0.0, 0.0), (0.11, 0.0), (0.12, 0.006), (0.11, 0.018), (0.0, 0.03)], seg=40)
    mx = x1 - 0.30 if x1 - x0 > 1.2 else x1 - 0.22                                              # termostática y teleducha
    m.cyl_axis('metal_negro', [P(mx, y1)[0], 1.05, P(mx, y1)[1]], 2, 0.035, 0.012, seg=28)
    TU(m, 'metal_negro', [(mx, y1 - 0.012, 1.05), (mx, y1 - 0.06, 1.05)], 0.01, seg=12)
    TU(m, 'metal_negro', [(mx - 0.12, y1 - 0.004, 1.35), (mx - 0.12, y1 - 0.06, 1.35), (mx - 0.12, y1 - 0.06, 1.48)], 0.012, seg=12)
    TU(m, 'metal_negro', [(mx - 0.12, y1 - 0.06, 1.35)] + [(mx - 0.12 + 0.05 * math.sin(t), y1 - 0.04, 1.30 - 0.32 * math.sin(t / 2)) for t in np.linspace(0, math.pi * 2, 18)] +
       [(mx - 0.04, y1 - 0.02, 1.05)], 0.006, seg=8)                                              # manguera


m = Mesh()
NICHO_P = ('n', 5.20, 5.90, 1.05, 1.38); NICHO_S = ('n', 3.95, 4.50, 1.05, 1.38)
sanitario(m, fx['sanitario_principal']['rect'], 'e')
lavamanos(m, fx['lavamanos_principal']['rect'], 'o', n=2)
ducha(m, fx['ducha_principal']['rect'], 0.62, None)
nicho(m, 'revestimiento_bano', 'n', NICHO_P[1], NICHO_P[2], 7.45, NICHO_P[3], NICHO_P[4])
node102('APA_Bano_principal', m, 'propuesta', 'Baño principal de la propuesta: ducha a nivel de 1,78 m con mampara y nicho, doble lavamanos suspendido y sanitario suspendido', 'aparatos',
        huella=[fx['sanitario_principal']['rect'], fx['lavamanos_principal']['rect']])
m = Mesh()
sanitario(m, fx['sanitario_social']['rect'], 'o')
lavamanos(m, fx['lavamanos_social']['rect'], 'e')
ducha(m, fx['ducha_social']['rect'], 0.45, None)
nicho(m, 'revestimiento_bano', 'n', NICHO_S[1], NICHO_S[2], 7.45, NICHO_S[3], NICHO_S[4])
node102('APA_Bano_social', m, 'propuesta', 'Baño social de la propuesta: ducha a nivel con mampara y nicho, lavamanos suspendido y sanitario suspendido', 'aparatos',
        huella=[fx['sanitario_social']['rect'], fx['lavamanos_social']['rect']])

# ====================================================================== ROPAS junto a los ductos (referencia 4)
m = Mesh()
x0, y0, x1, y1 = fx['lavadora_secadora']['rect']                # 2,62–3,22 × 5,30–5,95
B(m, 'metal_negro', x0 + 0.01, y0 + 0.02, x1 - 0.01, y1 - 0.02, 0, 0.012)                       # bandeja antiderrame
for (za, zb) in ((0.02, 0.86), (0.87, 1.71)):
    RB(m, 'electro_blanco', x0 + 0.015, y0 + 0.03, x1 - 0.015, y1, za, zb, 0.025)
    c = P((x0 + x1) / 2, y0 + 0.03)
    m.cyl_axis('acero', [c[0], (za + zb) / 2 - 0.04, c[1] + 0.004], 2, 0.20, 0.026, seg=48)
    m.cyl_axis('vidrio_negro', [c[0], (za + zb) / 2 - 0.04, c[1] + 0.018], 2, 0.165, 0.012, seg=48)
    B(m, 'vidrio_negro', x0 + 0.06, y0 + 0.024, x1 - 0.06, y0 + 0.03, zb - 0.11, zb - 0.045)
RB(m, 'gabinete_cocina', x1, y0 + 0.02, x1 + 0.02, y1, 0.0, ALT - 0.002, 0.002, k=1)            # costado de roble entre equipos y lavadero
a0, b0, a1, b1 = fx['lavadero']['rect']                          # 3,22–3,58 × 5,45–5,95
B(m, 'carcasa', a0 + 0.02, b0 + 0.02, a1, b1, 0.10, 0.86); B(m, 'metal_negro', a0 + 0.02, b0 + 0.07, a1, b1, 0, 0.10)
frente(m, 'gabinete_cocina', a0 + 0.02, b0, a1, b0 + 0.02, 0.10, 0.86, 's'); tirador_v(m, 'laton_cepillado', a1 - 0.05, b0, 0.60, 0.80, 's')
for (a, b, c, d) in ((a0 + 0.02, b0, a1, b0 + 0.06), (a0 + 0.02, b1 - 0.05, a1, b1), (a0 + 0.02, b0 + 0.06, a0 + 0.05, b1 - 0.05), (a1 - 0.03, b0 + 0.06, a1, b1 - 0.05)):
    B(m, 'ceramica_calida', a, b, c, d, 0.86, 0.90)
SOFT(m, 'ceramica_calida', a0 + 0.05, b0 + 0.06, a1 - 0.03, b1 - 0.05, 0.66, 0.90, 0.3, 0.2, 24, 8)
TU(m, 'laton_cepillado', [((a0 + a1) / 2 + 0.01, b1 - 0.02, 0.90), ((a0 + a1) / 2 + 0.01, b1 - 0.02, 1.12), ((a0 + a1) / 2 + 0.01, b1 - 0.16, 1.12), ((a0 + a1) / 2 + 0.01, b1 - 0.16, 1.07)], 0.011, seg=12)
for zz in (1.30, 1.58):                                          # repisas abiertas con cestas y toallas dobladas
    RB(m, 'gabinete_cocina', a0 + 0.02, b0 + 0.12, a1, b1, zz, zz + 0.03, 0.003, k=1)
    B(m, 'luz_calida', a0 + 0.04, b0 + 0.14, a1 - 0.02, b0 + 0.16, zz - 0.003, zz)
RB(m, 'laca_mueble', a0 + 0.05, b0 + 0.18, a0 + 0.30, b1 - 0.03, 1.33, 1.50, 0.01, k=1)
for k in range(3):
    SOFT(m, 'toalla', a0 + 0.05, b0 + 0.20, a1 - 0.04, b1 - 0.04, 1.61 + k * 0.045, 1.65 + k * 0.045, 0.6, 0.15, 20, 6)
B(m, 'carcasa', 2.62, 5.60, 3.58, y1, 1.80, ALT - 0.002)                                        # gabinete alto de lado a lado
for (a, b) in ((2.62, 3.10), (3.10, 3.58)):
    frente(m, 'gabinete_cocina', a, 5.58, b, 5.60, 1.80, ALT - 0.004, 's')
B(m, 'luz_calida', 2.66, 5.62, 3.54, 5.64, 1.796, 1.80)
# ventilación y registro de mantenimiento hacia el ducto D1 (muro este del cuarto, x = 3,58)
B(m, 'rejilla', 3.575, 5.05, 3.58, 5.45, 2.22, 2.32)
for k in range(9):
    B(m, 'carcasa', 3.574, 5.06 + k * 0.042, 3.576, 5.07 + k * 0.042, 2.23, 2.31)
B(m, 'metal_negro', 3.574, 5.02, 3.58, 5.40, 0.06, 0.07); B(m, 'metal_negro', 3.574, 5.02, 3.58, 5.40, 0.44, 0.45)
B(m, 'metal_negro', 3.574, 5.02, 3.58, 5.03, 0.06, 0.45); B(m, 'metal_negro', 3.574, 5.39, 3.58, 5.40, 0.06, 0.45)
node102('APA_Ropas', m, 'propuesta', 'Zona de ropas junto a los ductos: lavadora-secadora apilada, lavadero, repisas y gabinete alto en roble, rejilla de extracción y registro de mantenimiento hacia el ducto D1. Tras puerta corrediza oculta desde el hall.', 'aparatos',
        huella=[fx['lavadora_secadora']['rect'], fx['lavadero']['rect']])
