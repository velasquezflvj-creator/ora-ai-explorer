# Mobiliario de presentación del apartamento 102 (ilustrativo). Se ejecuta dentro de tools/generar_glb.py
# después de definir furn() y los modelos de terceros (sofá y butacas). Mantiene todas las huellas de la
# propuesta: no cambia la distribución.


# ====================================================================== SALA (referencia 1)
def cortina(m, x0, x1, yw, visillo=None, panos=(), riel=True):
    """Cortinas de lino hasta el piso desde un riel empotrado; visillo translúcido entre (a, b)."""
    if riel:
        B(m, 'carcasa', x0, yw + 0.03, x1, yw + 0.15, ALT - 0.025, ALT - 0.001)          # foso del riel en el cielo
    if visillo:
        DR(m, 'tela_visillo', visillo[0], yw + 0.07, visillo[1], yw + 0.07, 0.015, ALT - 0.03, 0.02, max(3, round((visillo[1] - visillo[0]) / 0.09)))
    for (a, b) in panos:
        DR(m, 'tela_cortina', a, yw + 0.115, b, yw + 0.115, 0.01, ALT - 0.03, 0.075, max(3, round((b - a) / 0.085)))


def sala(m):
    for (cx, cy, r, h) in ((1.55, 1.95, 0.15, 0.42), (1.535, 2.42, 0.135, 0.35)):   # mesas redondas de travertino
        LA(m, 'meson', cx, cy, h - 0.03, [(0.0, 0.0), (r - 0.004, 0.0), (r, 0.004), (r, 0.026), (r - 0.004, 0.03), (0.0, 0.03)], seg=48)
        LA(m, 'meson', cx, cy, 0.0, [(0.075, 0.0), (0.08, 0.01), (0.06, 0.05), (0.055, h - 0.06), (0.065, h - 0.03), (0.0, h - 0.03)], seg=36)
    for k, (w, d, c) in enumerate(((0.20, 0.14, 'libro_c'), (0.18, 0.13, 'libro_a'))):
        B(m, c, 1.47, 1.86, 1.47 + w * 0.6, 1.86 + d, 0.42 + k * 0.022, 0.442 + k * 0.022)
    LA(m, 'ceramica_deco', 1.62, 2.02, 0.42, [(0.0, 0.0), (0.05, 0.0), (0.06, 0.02), (0.065, 0.05), (0.0, 0.05)], seg=28)
    ramas(m, 1.535, 2.42, 0.35, n=4, alto=0.42)
    RB(m, 'textil_tapete', 0.30, 1.20, 1.80, 3.05, 0, 0.012, 0.005, k=1)
    # muro del televisor: listones verticales de roble a toda altura, televisor y barra de sonido
    B(m, 'carcasa', 2.579, 1.05, 2.599, 3.15, 0.0, ALT - 0.002)
    for k in range(int((3.15 - 1.05) / 0.042)):
        ya = 1.05 + k * 0.042 + 0.006
        RB(m, 'madera_mueble', 2.577, ya, 2.599, ya + 0.03, 0.0, ALT - 0.002, 0.004, k=1)
    RB(m, 'pantalla', 2.551, 1.49, 2.577, 2.71, 0.96, 1.645, 0.004, k=1)
    B(m, 'luz_calida', 2.575, 1.53, 2.577, 2.67, 1.648, 1.652)
    RB(m, 'metal_negro', 2.556, 1.72, 2.577, 2.48, 0.84, 0.895, 0.012, k=2)
    art(m, 'e', 0.152, 1.50, 0.152, 2.70, 1.10, 1.80, frame='madera_mueble')
    x, y = [(MOBI['lampara_sala'][i] + MOBI['lampara_sala'][i + 2]) / 2 for i in (0, 1)]
    LA(m, 'metal_negro', x, y, 0.0, [(0.0, 0.0), (0.13, 0.0), (0.135, 0.006), (0.12, 0.018), (0.0, 0.02)], seg=36)
    TU(m, 'laton_cepillado', [(x, y, 0.02), (x, y, 1.42)], 0.009, seg=10)
    LA(m, 'pantalla_lampara', x, y, 1.38, [(0.20, 0.0), (0.195, 0.10), (0.17, 0.30)], seg=40)
    cortina(m, 0.15, 2.599, 0.15, visillo=(0.20, 1.38), panos=((0.16, 0.62), (2.42, 2.59)))


furn('MOB_Sala', sala, [MOBI[k] for k in ('mesa_centro', 'tv', 'lampara_sala')])


# ====================================================================== BARRA (referencia 2)
def banqueta(m, cx, cy):
    """Banqueta de barra: estructura negra de varilla, asiento y respaldo envolvente en bouclé."""
    zs = 0.63
    for sx in (-1, 1):
        for sy in (-1, 1):
            TU(m, 'metal_negro', [(cx + sx * 0.155, cy + sy * 0.15, zs), (cx + sx * 0.19, cy + sy * 0.185, 0.0)], 0.0085, seg=10)
    f = 0.155 + (0.19 - 0.155) * (1 - 0.28 / zs); g_ = 0.15 + (0.185 - 0.15) * (1 - 0.28 / zs)
    TU(m, 'metal_negro', [(cx - f, cy - g_, 0.28), (cx + f, cy - g_, 0.28), (cx + f, cy + g_, 0.28), (cx - f, cy + g_, 0.28), (cx - f, cy - g_, 0.28)], 0.007, seg=8)
    SOFT(m, 'tela_silla', cx - 0.21, cy - 0.20, cx + 0.21, cy + 0.20, zs - 0.01, zs + 0.075, 0.45, 0.6, 34, 10)
    curva = lambda x, y, z: (x, y, z - 0.075 * (x / 0.19) ** 2)
    SOFT(m, 'tela_silla', cx - 0.20, cy - 0.235, cx + 0.20, cy - 0.155, zs + 0.10, zs + 0.33, 0.38, 0.5, 32, 12, curva)
    xs = np.linspace(-0.205, 0.205, 15)
    TU(m, 'metal_negro', [(cx + x, cy - 0.20 + 0.075 * (x / 0.19) ** 2, zs + 0.335) for x in xs], 0.006, seg=8)
    for sx in (-1, 1):
        TU(m, 'metal_negro', [(cx + sx * 0.205, cy - 0.20 + 0.075 * (0.205 / 0.19) ** 2, zs + 0.335), (cx + sx * 0.155, cy - 0.15, zs)], 0.006, seg=8)


def barra(m):
    for cx in (0.62, 1.22):
        banqueta(m, cx, 4.27)
    for cx in (0.52, 1.18):                                                              # colgantes de vidrio opalino
        CY(m, 'metal_negro', cx, 4.95, 0.045, ALT - 0.012, 0.012, seg=24)
        TU(m, 'metal_negro', [(cx, 4.95, ALT - 0.012), (cx, 4.95, 1.74)], 0.0018, seg=5)
        LA(m, 'laton_cepillado', cx, 4.95, 1.715, [(0.0, 0.0), (0.02, 0.0), (0.02, 0.03), (0.0, 0.03)], seg=16)
        SP(m, 'vidrio_opal', cx, 4.95, 1.585, 0.135, seg=28)
    ramas(m, 0.36, 4.72, 0.90, n=6, alto=0.52)
    LA(m, 'ceramica_deco', 0.42, 5.18, 0.90, [(0.0, 0.0), (0.07, 0.0), (0.12, 0.035), (0.13, 0.05), (0.0, 0.05)], seg=32)
    for i, (dx, dy) in enumerate(((-0.03, 0.02), (0.04, -0.02), (0.0, 0.05), (0.05, 0.04))):
        SP(m, 'ceramica_deco' if i % 2 else 'laton_cepillado', 0.42 + dx, 5.18 + dy, 0.965, 0.034, seg=12)


furn('MOB_Barra', barra, [MOBI['banquetas']], nota='Banquetas y lámparas ilustrativas de la barra')


# ====================================================================== HABITACIONES (referencia 5)
def cama(m, x0, y0, x1, y1, head, mesas):
    """Cama de plataforma flotante en roble, textiles de lino y cabecero de dos paneles tapizados; mesas de
    noche suspendidas con panel superior y luz indirecta, y lámparas colgantes de lectura."""
    sgn = 1 if head == 'e' else -1
    hx = x1 if head == 'e' else x0; fx_ = x0 if head == 'e' else x1; lo, hi = min(hx, fx_), max(hx, fx_)
    RB(m, 'metal_negro', lo + 0.15, y0 + 0.15, hi - 0.15, y1 - 0.15, 0.0, 0.13, 0.004, k=1)
    RB(m, 'madera_mueble', lo, y0, hi, y1, 0.13, 0.32, 0.006, k=2)
    SOFT(m, 'tela_cama', lo + 0.04, y0 + 0.04, hi - 0.04, y1 - 0.04, 0.31, 0.52, 0.20, 0.08, 34, 12)
    arr = lambda x, y, z: (x, y + (0.004 * math.sin(11 * x + 2 * z) * math.cos(7 * z) if y > 0 else 0.0), z)
    d0, d1 = fx_ - sgn * 0.025, hx - sgn * 0.66
    SOFT(m, 'tela_cama', min(d0, d1), y0 - 0.03, max(d0, d1), y1 + 0.03, 0.29, 0.56, 0.10, 0.04, 46, 16, arr)
    t0, t1 = d1 - sgn * 0.02, d1 + sgn * 0.22
    SOFT(m, 'tela_cama', min(t0, t1), y0 - 0.025, max(t0, t1), y1 + 0.025, 0.535, 0.60, 0.5, 0.07, 32, 10)
    p0, p1 = fx_ - sgn * 0.12, fx_ + sgn * 0.62                                               # pie de cama de lana
    SOFT(m, 'tela_acento', min(p0, p1), y0 - 0.07, max(p0, p1), y1 + 0.07, 0.30, 0.60, 0.12, 0.05, 32, 12)          # cae por los costados como el duvet
    W_ = y1 - y0; npil = 2 if W_ > 1.2 else 1
    for k in range(npil):
        a = y0 + 0.05 + k * (W_ - 0.10) / npil; b = a + (W_ - 0.10) / npil - 0.03
        q0, q1 = hx - sgn * 0.09, hx - sgn * 0.45
        pillow(m, 'tela_cama', min(q0, q1), a, max(q0, q1), b, 0.52, 0.72)
        r0, r1 = hx - sgn * 0.27, hx - sgn * 0.55
        pillow(m, 'tela_acento', min(r0, r1), a + 0.08, max(r0, r1), b - 0.08, 0.55, 0.74)
    c0, c1 = (hx - 0.075, hx) if head == 'e' else (hx, hx + 0.075)
    mid = (y0 + y1) / 2
    for (a, b) in ((y0 - 0.04, mid - 0.006), (mid + 0.006, y1 + 0.04)):
        SOFT(m, 'tela_cabecero', c0, a, c1, b, 0.30, 1.32, 0.10, 0.08, 22, 14)
    for (a0, b0, a1, b1) in mesas:                                                        # mesas de noche flotantes
        wall = a1 if head == 'e' else a0; s_ = -1 if head == 'e' else 1
        B(m, 'madera_mueble', min(wall, wall + s_ * 0.02), b0, max(wall, wall + s_ * 0.02), b1, 0.40, 0.95)
        RB(m, 'madera_mueble', a0, b0, a1, b1, 0.40, 0.56, 0.006, k=2)
        RB(m, 'laca_mueble', min(wall, wall + s_ * 0.13), b0, max(wall, wall + s_ * 0.13), b1, 0.95, 1.32, 0.006, k=1)
        B(m, 'luz_calida', min(wall + s_ * 0.025, wall + s_ * 0.12), b0 + 0.02, max(wall + s_ * 0.025, wall + s_ * 0.12), b1 - 0.02, 0.946, 0.95)
        cx, cy = (a0 + a1) / 2, (b0 + b1) / 2
        LA(m, 'ceramica_deco', cx + s_ * 0.06, cy, 0.56, [(0.0, 0.0), (0.045, 0.0), (0.06, 0.05), (0.035, 0.16), (0.02, 0.2), (0.0, 0.2)], seg=24)
        B(m, 'libro_c', cx - 0.07, cy - 0.10, cx + 0.07, cy + 0.08, 0.56, 0.585)
        lx = cx - s_ * 0.18                                                              # colgante de lectura
        TU(m, 'metal_negro', [(lx, cy, ALT - 0.01), (lx, cy, 1.30)], 0.0018, seg=5)
        CY(m, 'metal_negro', lx, cy, 0.035, ALT - 0.012, 0.012, seg=20)
        LA(m, 'madera_mueble', lx, cy, 1.215, [(0.0, 0.0), (0.035, 0.0), (0.05, 0.03), (0.035, 0.06), (0.012, 0.085), (0.0, 0.085)], seg=24)
        LA(m, 'ceramica_deco', lx, cy, 1.13, [(0.0, 0.0), (0.075, 0.005), (0.08, 0.035), (0.04, 0.085), (0.0, 0.085)], seg=28)
        SP(m, 'luz_calida', lx, cy, 1.135, 0.03, seg=10)


def armario(m, x0, y0, x1, y1, frente_, n=2, corredizo=True):
    """Armario empotrado hasta el cielo en laca arena, puertas con junta vertical y uñero continuo."""
    B(m, 'carcasa', x0, y0, x1, y1, 0.0, ALT - 0.002)
    L = (x1 - x0) if frente_ in 'ns' else (y1 - y0)
    for i in range(n):
        a = i / n; b = (i + 1) / n; ofs = (0.02 if (corredizo and i % 2) else 0.0)
        if frente_ in 'ns':
            yy = (y0 - 0.02 - ofs, y0 - ofs) if frente_ == 's' else (y1 + ofs, y1 + 0.02 + ofs)
            frente(m, 'laca_mueble', x0 + L * a, yy[0], x0 + L * b, yy[1], 0.02, ALT - 0.012, frente_)
            ux = x0 + L * (b - 0.04) if i % 2 == 0 else x0 + L * (a + 0.04)
            B(m, 'laton_cepillado', ux - 0.006, min(yy) - 0.004, ux + 0.006, min(yy), 0.30, 1.90)
        else:
            xx = (x0 - 0.02 - ofs, x0 - ofs) if frente_ == 'o' else (x1 + ofs, x1 + 0.02 + ofs)
            frente(m, 'laca_mueble', xx[0], y0 + L * a, xx[1], y0 + L * b, 0.02, ALT - 0.012, frente_)
            uy = y0 + L * (b - 0.04) if i % 2 == 0 else y0 + L * (a + 0.04)
            B(m, 'laton_cepillado', min(xx) - 0.004, uy - 0.006, min(xx), uy + 0.006, 0.30, 1.90)
    if corredizo:
        if frente_ in 'ns':
            B(m, 'metal_negro', x0, (y0 - 0.05) if frente_ == 's' else y1, x1, y0 if frente_ == 's' else y1 + 0.05, ALT - 0.012, ALT - 0.002)
        else:
            B(m, 'metal_negro', (x0 - 0.05) if frente_ == 'o' else x1, y0, x0 if frente_ == 'o' else x1 + 0.05, y1, ALT - 0.012, ALT - 0.002)


def tapete(m, x0, y0, x1, y1):
    RB(m, 'textil_tapete', x0, y0, x1, y1, 0, 0.014, 0.006, k=1)


def habitacion_2(m):
    x0, y0, x1, y1 = MOBI['cama_2']
    cama(m, x0 + 0.06, y0, x1, y1, 'o', [MOBI['noche_2a'], MOBI['noche_2b']])
    armario(m, *MOBI['armario_2'], 's', n=2)
    a0, b0, a1, b1 = MOBI['comoda_2']                                                     # cómoda baja suspendida bajo la ventana
    b0 = 0.32
    RB(m, 'madera_mueble', a0, b0, a1, b1, 0.26, 0.74, 0.006, k=2)
    for k in range(1, 3):
        B(m, 'carcasa', a0 + 0.02, b0 - 0.001, a1 - 0.02, b0, 0.26 + k * 0.16 - 0.002, 0.26 + k * 0.16 + 0.002)
    B(m, 'luz_calida', a0 + 0.04, b0 + 0.04, a1 - 0.04, b1 - 0.04, 0.256, 0.26)
    LA(m, 'ceramica_deco', a0 + 0.15, (b0 + b1) / 2, 0.74, [(0.0, 0.0), (0.05, 0.0), (0.065, 0.06), (0.04, 0.2), (0.0, 0.2)], seg=24)
    LA(m, 'pantalla_lampara', a0 + 0.15, (b0 + b1) / 2, 0.94, [(0.12, 0.0), (0.10, 0.16)], seg=28)
    ramas(m, a1 - 0.18, (b0 + b1) / 2, 0.74, n=3, alto=0.32)
    tapete(m, 3.20, 0.75, 4.95, 2.75)
    cortina(m, 4.10, 5.40, 0.15, visillo=(4.25, 5.25), panos=((4.00, 4.26), (5.24, 5.50)))


furn('MOB_Habitacion_2', habitacion_2, [MOBI[k] for k in ('cama_2', 'noche_2a', 'noche_2b', 'armario_2', 'comoda_2')])


def principal(m):
    x0, y0, x1, y1 = MOBI['cama_p']
    cama(m, x0, y0, x1 - 0.06, y1, 'e', [MOBI['noche_pa'], MOBI['noche_pb']])
    a0, b0, a1, b1 = MOBI['butaca_p']
    LA(m, 'metal_negro', a1 + 0.14, b1 - 0.05, 0.0, [(0.0, 0.0), (0.12, 0.0), (0.125, 0.006), (0.11, 0.016), (0.0, 0.018)], seg=32)
    TU(m, 'laton_cepillado', [(a1 + 0.14, b1 - 0.05, 0.02), (a1 + 0.14, b1 - 0.05, 1.36)], 0.008, seg=10)
    LA(m, 'pantalla_lampara', a1 + 0.14, b1 - 0.05, 1.33, [(0.18, 0.0), (0.175, 0.08), (0.15, 0.26)], seg=36)
    tapete(m, 5.55, 1.45, 7.30, 3.65)
    cortina(m, 5.00, 6.45, 0.15, visillo=(5.40, 6.40), panos=((5.02, 5.42),))


furn('MOB_Habitacion_principal', principal, [MOBI[k] for k in ('cama_p', 'noche_pa', 'noche_pb')] + [[MOBI['butaca_p'][2] + 0.02, MOBI['butaca_p'][3] - 0.17, MOBI['butaca_p'][2] + 0.26, MOBI['butaca_p'][3] + 0.07]])


def vestier(m):
    armario(m, *MOBI['closet_v1'], 'o', n=3, corredizo=False)
    armario(m, *MOBI['closet_v2'], 's', n=1, corredizo=False)
    B(m, 'madera_mueble', 6.775, 4.98, 6.795, 6.42, 0.20, 2.08)
    B(m, 'espejo_vestier', 6.795, 5.0, 6.80, 6.40, 0.22, 2.06)
    SOFT(m, 'tela_cabecero', 6.85, 5.85, 7.25, 6.35, 0.0, 0.44, 0.25, 0.3, 24, 10)


furn('MOB_Vestier', vestier, [MOBI['closet_v1'], MOBI['closet_v2'], [6.85, 5.85, 7.25, 6.35]])


# ====================================================================== BAÑOS: espejos, toalleros y accesorios
def banos(m):
    l = fx['lavamanos_principal']['rect']
    espejo_halo(m, 'espejo_principal', 'o', l[1] + 0.03, l[3] - 0.03, 1.05, 1.85, 4.87)
    l2 = fx['lavamanos_social']['rect']
    espejo_halo(m, 'espejo_social', 'e', l2[1] + 0.02, l2[3] - 0.02, 1.05, 1.80, 4.75)
    TU(m, 'metal_negro', [(6.645, 5.92, 1.20), (6.60, 5.92, 1.20), (6.60, 6.40, 1.20), (6.645, 6.40, 1.20)], 0.007, seg=8)      # toallero principal
    SOFT(m, 'toalla', 6.575, 5.95, 6.625, 6.37, 0.78, 1.215, 0.5, 0.2, 18, 12)
    TU(m, 'metal_negro', [(3.705, 6.00, 1.20), (3.75, 6.00, 1.20), (3.75, 6.42, 1.20), (3.705, 6.42, 1.20)], 0.007, seg=8)      # toallero social
    SOFT(m, 'toalla', 3.725, 6.03, 3.775, 6.39, 0.80, 1.215, 0.5, 0.2, 18, 12)
    for (x, y, s_) in ((6.645, 5.80, -1), (3.705, 5.42, 1)):                                                                    # portarrollos
        TU(m, 'metal_negro', [(x, y, 0.70), (x + s_ * 0.06, y, 0.70), (x + s_ * 0.06, y + 0.12, 0.70)], 0.005, seg=8)
    for (cx, cy) in ((5.30, 7.40), (4.12, 7.40)):                                                                               # frascos en los nichos
        for k, dx in enumerate((-0.12, -0.04, 0.05)):
            LA(m, 'ceramica_deco' if k != 1 else 'ceramica_calida', cx + dx, cy, 1.05, [(0.0, 0.0), (0.03, 0.0), (0.03, 0.15 - 0.03 * k), (0.012, 0.17 - 0.03 * k), (0.0, 0.17 - 0.03 * k)], seg=18)
    LA(m, 'ceramica_deco', 5.10, l[1] + 0.12, 0.84, [(0.0, 0.0), (0.035, 0.0), (0.04, 0.08), (0.02, 0.12), (0.0, 0.12)], seg=18)
    ramas(m, 5.12, l[3] - 0.10, 0.84, n=3, alto=0.25)
    RB(m, 'textil_tapete', 4.95, 5.25, 5.55, 6.25, 0, 0.012, 0.006, k=1)


furn('MOB_Banos', banos, nota='Espejos con luz indirecta, toalleros y accesorios ilustrativos de los baños')


# ====================================================================== CIELO: foseado de la sala, buñas y luz lineal del corredor
m = Mesh()
cx0, cy0, cx1, cy1, ancho = 0.15, 0.15, 2.599, 3.90, 0.30                                    # foseado perimetral de la sala
for (a, b, c, d) in ((cx0, cy0, cx1, cy0 + ancho), (cx0, cy1 - ancho, cx1, cy1), (cx0, cy0 + ancho, cx0 + ancho, cy1 - ancho), (cx1 - ancho, cy0 + ancho, cx1, cy1 - ancho)):
    B(m, 'cielo', a, b, c, d, ALT - 0.10, ALT - 0.002)
for (a, b, c, d) in ((cx0 + ancho, cy0 + ancho - 0.01, cx1 - ancho, cy0 + ancho), (cx0 + ancho, cy1 - ancho, cx1 - ancho, cy1 - ancho + 0.01),
                     (cx0 + ancho - 0.01, cy0 + ancho, cx0 + ancho, cy1 - ancho), (cx1 - ancho, cy0 + ancho, cx1 - ancho + 0.01, cy1 - ancho)):
    B(m, 'luz_calida', a, b, c, d, ALT - 0.085, ALT - 0.075)
for rid in ('hall', 'habitacion_2', 'principal'):                                             # buña perimetral en el encuentro muro–cielo
    for side, xa, ya, xb, yb in wall_runs(rid):
        t = 0.012
        if side == 's':
            B(m, 'carcasa', xa, ya, xb, ya + t, ALT - 0.014, ALT - 0.002)
        elif side == 'n':
            B(m, 'carcasa', xa, ya - t, xb, ya, ALT - 0.014, ALT - 0.002)
        elif side == 'o':
            B(m, 'carcasa', xa, ya, xa + t, yb, ALT - 0.014, ALT - 0.002)
        else:
            B(m, 'carcasa', xa - t, ya, xa, yb, ALT - 0.014, ALT - 0.002)
B(m, 'luz_calida', 2.70, 4.60, 5.20, 4.64, ALT - 0.006, ALT - 0.002)                          # luz lineal rasante en el corredor
node102('ILU_Cielo_detalles', m, 'ilustrativo', 'Foseado con luz indirecta en la sala, buñas perimetrales y luz lineal del corredor (ilustrativos)', 'cielo')
