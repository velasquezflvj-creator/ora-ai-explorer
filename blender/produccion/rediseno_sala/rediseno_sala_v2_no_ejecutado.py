# ORA · Apartamento 102 (PROPUESTA DE REDISTRIBUCIÓN, no planta verificada) · Rediseño de sala V2 (refinamiento fotorrealista).
# Fuente: rediseno_sala/escena_sala_rediseno_v1.blend (copia independiente; no se escribe). Guarda escena_sala_rediseno_v2.blend.
#  - Sofá: cojines por SIMULACIÓN DE TELA (tela casi inextensible + resortes internos = núcleo de espuma), en secuencia con
#    colisiones (asiento → respaldos → decorativos); vivos extraídos de la costura real de cada cojín simulado.
#  - Cuadro: composición 4K con capas de espátula y pincel, relieve REAL (desplazamiento de malla ~1,4 M vértices), brillo
#    variable por zona, marco de latón de una pieza con perfil en L e ingletes.
#  - Mueble TV: piedra apomazada con microrrayado, roble de poro abierto, bronce anisotrópico, cantos redondeados, LED recalibrado.
#  - Iluminación: SOLO se reorientan dos focos existentes (Luz_social_1 y _2) hacia el cuadro; potencia y temperatura sin cambio.
#   blender -b rediseno_sala/escena_sala_rediseno_v1.blend --python rediseno_sala/rediseno_sala_v2.py -- <blend_v2> <carpeta_control>
import bpy, bmesh, sys, os, math, json, time
import numpy as np
from mathutils import Vector, Matrix
SAL, OUT = sys.argv[sys.argv.index('--') + 1:][:2]
sc = bpy.context.scene; OX, OY = 4.037, 3.8; col = bpy.data.collections['REDISENO_SALA']
reg = {'sofa_simulacion': [], 'cuadro': {}, 'mueble_tv': [], 'iluminacion': [], 'tiempos_s': {}}
T0 = time.time()
def obj(n): return sc.objects[n]

# ================================================================ 1. SOFÁ: simulación de tela
def volumen(me):
    bm = bmesh.new(); bm.from_mesh(me); v = bm.calc_volume(); bm.free(); return abs(v)
def anillos_costura(o, umbral_grados):
    """Vértices de las aristas vivas (costuras de caja) alrededor de las dos caras mayores, ordenados por ángulo."""
    bm = bmesh.new(); bm.from_mesh(o.data); bm.edges.ensure_lookup_table()
    co = np.array([v.co[:] for v in bm.verts]); ext = co.max(0) - co.min(0); k = int(np.argmin(ext)); cen = (co.max(0) + co.min(0)) / 2
    vivos = set()
    for e in bm.edges:
        if len(e.link_faces) == 2 and e.link_faces[0].normal.angle(e.link_faces[1].normal) > math.radians(umbral_grados):
            vivos.update(v.index for v in e.verts)
    bm.free(); otros = [i for i in range(3) if i != k]; anillos = []
    for signo in (1, -1):
        ids = [i for i in vivos if (co[i, k] - cen[k]) * signo > 0.55 * ext[k] / 2]
        if len(ids) < 12: continue
        ang = [math.atan2(co[i, otros[1]] - cen[otros[1]], co[i, otros[0]] - cen[otros[0]]) for i in ids]
        anillos.append([i for _, i in sorted(zip(ang, ids))])
    if not anillos:   # cojín decorativo: una sola costura perimetral en el plano medio (no aristas de caja)
        # la superficie cerrada solo corta el plano medio en la banda perimetral: se toma el lazo de esa banda más cercano
        # al plano, de un solo lado (los lazos simétricos ±d producirían un vivo en zigzag)
        d = co[:, k] - cen[k]; lado = d >= 0
        dmin = np.abs(d[lado]).min() if lado.any() else 0.0
        ids = [int(i) for i in np.nonzero(lado & (np.abs(np.abs(d) - dmin) <= 0.0015))[0]]
        if len(ids) >= 12:
            ang = [math.atan2(co[i, otros[1]] - cen[otros[1]], co[i, otros[0]] - cen[otros[0]]) for i in ids]
            anillos.append([i for _, i in sorted(zip(ang, ids))])
    return anillos
def vivo(nombre, o, ids, mat, r=0.0042):
    M = o.matrix_world; cu = bpy.data.curves.new(nombre, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = r; cu.bevel_resolution = 3
    sp = cu.splines.new('POLY'); sp.points.add(len(ids) - 1)
    for pt, i in zip(sp.points, ids): pt.co = (*(M @ o.data.vertices[i].co), 1)
    sp.use_cyclic_u = True; cu.materials.append(mat); ob = bpy.data.objects.new(nombre, cu); col.objects.link(ob); return ob
def colisionador(o):
    if not any(m.type == 'COLLISION' for m in o.modifiers): o.modifiers.new('colision', 'COLLISION'); o.collision.thickness_outer = 0.003
def simular(nombre, colis, cortes, elevar, resorte, presion, frames=40):
    o = obj(nombre); t = time.time()
    sub_niv = next((m.levels for m in o.modifiers if m.type == 'SUBSURF'), 2)
    for m in list(o.modifiers): o.modifiers.remove(m)
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cortes, use_grid_fill=True); bm.to_mesh(o.data); bm.free()
    o.location += Vector(elevar)
    anillos = anillos_costura(o, 25)   # 25°: detecta también el lado largo del asiento (con 35° quedaba un tramo de 63 cm sin vivo)
    original = o.data.copy(); v0 = volumen(o.data)
    for c in colis: colisionador(obj(c))
    cl = o.modifiers.new('tela', 'CLOTH'); s = cl.settings
    s.quality = 8; s.mass = 0.002; s.air_damping = 2; s.tension_stiffness = 80; s.compression_stiffness = 80; s.shear_stiffness = 10; s.bending_stiffness = 1.5
    s.use_pressure = presion > 0; s.uniform_pressure_force = presion; s.shrink_min = 0.012
    s.use_internal_springs = True; s.internal_spring_max_length = 0.25; s.internal_tension_stiffness = resorte; s.internal_compression_stiffness = resorte
    cs = cl.collision_settings; cs.distance_min = 0.003; cs.use_self_collision = True; cs.self_distance_min = 0.003
    cl.point_cache.frame_start = 1; cl.point_cache.frame_end = frames
    for f in range(1, frames + 1): sc.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get(); me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    o.modifiers.remove(cl); sc.frame_set(1)
    v1 = volumen(me); desp = max((a.co - b.co).length for a, b in zip(original.vertices, me.vertices))
    ok = 0.85 < v1 / v0 < 1.15 and desp < 0.15
    o.data = me if ok else original
    for p in o.data.polygons: p.use_smooth = True
    sb = o.modifiers.new('sub', 'SUBSURF'); sb.levels = 1; sb.render_levels = sub_niv
    mat = o.data.materials[0] if o.data.materials else None
    for i, ids in enumerate(anillos): vivo(f'{nombre}_vivo_{i+1}', o, ids, mat)
    r = {'cojin': nombre, 'vertices': len(o.data.vertices), 'volumen_conservado': round(v1 / v0, 3), 'desplazamiento_max_m': round(desp, 3),
         'vivos': len(anillos), 'aceptado': ok, 'segundos': round(time.time() - t, 1)}
    reg['sofa_simulacion'].append(r); print('[sala2] TELA', r); return o
for o in [o for o in col.objects if o.name.endswith('_vivo')]: bpy.data.objects.remove(o, do_unlink=True)   # vivos de V1 (se rehacen)
BASES = ['SOFA_base', 'SOFA_concha_respaldo_brazos', 'SOFA_zocalo_bronce']
simular('SOFA_asiento_continuo', BASES, 3, (0, 0, 0.06), 15, 0.5)
for k in (1, 2): simular(f'SOFA_cojin_respaldo_{k}', BASES + ['SOFA_asiento_continuo'], 3, (0.01, 0, 0.05), 12, 0.3)
for n in ('SOFA_deco_marfil', 'SOFA_deco_carbon', 'SOFA_deco_topo'):
    simular(n, BASES + ['SOFA_asiento_continuo', 'SOFA_cojin_respaldo_1', 'SOFA_cojin_respaldo_2'], 2, (0.02, 0, 0.06), 5, 0.3, frames=45)
for o in sc.objects:
    for m in [m for m in o.modifiers if m.type == 'COLLISION']: o.modifiers.remove(m)
reg['tiempos_s']['sofa'] = round(time.time() - T0, 1)

# ================================================================ 2. CUADRO: composición 4K, relieve real, marco con ingletes
t = time.time()
AW, AH = 1.90, 1.05; YC = (1.04 + 3.16) / 2 - OY; ACZ = 1.50; XW = -3.86
PH, PW = 2112, 3820
def ruido(h, w, oct_, base, sem):
    rng = np.random.default_rng(sem); out = np.zeros((h, w), np.float32); amp = 1.0; tot = 0
    for o_ in range(oct_):
        gh, gw = base * 2 ** o_, int(base * 2 ** o_ * w / h) + 1; g = rng.random((gh + 2, gw + 2)).astype(np.float32)
        yy = np.linspace(0, gh, h, dtype=np.float32); xx = np.linspace(0, gw, w, dtype=np.float32)
        y0 = yy.astype(int); x0 = xx.astype(int); fy = (yy - y0)[:, None]; fx = (xx - x0)[None, :]
        fy = fy * fy * (3 - 2 * fy); fx = fx * fx * (3 - 2 * fx)
        out += amp * ((g[y0][:, x0] * (1 - fx) + g[y0][:, x0 + 1] * fx) * (1 - fy) + (g[y0 + 1][:, x0] * (1 - fx) + g[y0 + 1][:, x0 + 1] * fx) * fy); tot += amp; amp *= 0.5
    return out / tot
yy, xx = np.mgrid[0:PH, 0:PW].astype(np.float32); u = xx / PH; v = 1 - yy / PH          # u ∈ [0,1.81], v ∈ [0,1]
n1 = ruido(PH, PW, 6, 3, 1); n2 = ruido(PH, PW, 6, 5, 2); n3 = ruido(PH, PW, 7, 16, 3); fino = ruido(PH, PW, 4, 120, 9)
wu, wv = u + 0.06 * (n1 - .5), v + 0.06 * (n2 - .5)
r = np.sqrt((wu - 1.55) ** 2 + (wv + 0.55) ** 2); grosor = 0.15 + 0.11 * np.clip((1.3 - wu) / 1.3, 0, 1) + 0.03 * (n3 - .5)
negro = (np.abs(r - 1.12) < grosor) & (wu > 0.15)
negro |= (np.abs(wu - 0.42 - 0.05 * (wv - .5)) < 0.075 + 0.02 * wv + 0.025 * (n1 - .5)) & (wv < 0.80 + 0.08 * n2)
color = np.zeros((PH, PW, 3), np.float32); alt = np.zeros((PH, PW), np.float32); rug = np.zeros((PH, PW), np.float32)
color[:] = np.stack([0.74 + 0.04 * (n3 - .5), 0.715 + 0.04 * (n3 - .5), 0.655 + 0.04 * (n3 - .5)], -1); alt[:] = 0.25 * n3 + 0.1 * fino; rug[:] = 0.8
veladura = np.clip((n2 - 0.40) / 0.22, 0, 1) * (r < 1.12 - grosor) * (~negro) * 0.7
color = color * (1 - veladura[..., None]) + np.array([0.12, 0.12, 0.125]) * veladura[..., None]
rng = np.random.default_rng(42)
def trazo(cu_, cv_, ang, largo, ancho, rgb, h_, rug_, opac, mascara=None):
    """Una pincelada/espátula: rectángulo orientado con extremos suaves, estrías longitudinales y cordón de pintura en el borde."""
    R = int((largo + ancho) * PH / 2) + 2; ci, cj = int((1 - cv_) * PH), int(cu_ * PH)
    i0, i1, j0, j1 = max(0, ci - R), min(PH, ci + R), max(0, cj - R), min(PW, cj + R)
    if i0 >= i1 or j0 >= j1: return
    pu = xx[i0:i1, j0:j1] / PH - cu_; pv = (1 - yy[i0:i1, j0:j1] / PH) - cv_
    a_ = pu * math.cos(ang) + pv * math.sin(ang); b_ = -pu * math.sin(ang) + pv * math.cos(ang)
    da = np.abs(a_) / (largo / 2); db = np.abs(b_) / (ancho / 2)
    m = np.clip(1 - da ** 6, 0, 1) * np.clip(1 - db ** 4, 0, 1)
    if mascara is not None: m *= mascara[i0:i1, j0:j1]
    m *= opac; est = 0.5 + 0.5 * np.sin(b_ * 900 + rng.random() * 6) * (0.4 + 0.6 * fino[i0:i1, j0:j1])
    borde = np.exp(-((db - 0.95) / 0.08) ** 2) * (da < 1)
    color[i0:i1, j0:j1] = color[i0:i1, j0:j1] * (1 - m[..., None]) + np.asarray(rgb, np.float32)[None, None] * (0.9 + 0.2 * est[..., None]) * m[..., None]
    alt[i0:i1, j0:j1] = alt[i0:i1, j0:j1] * (1 - 0.6 * m) + m * (h_ * (0.75 + 0.25 * est)) + 0.35 * h_ * borde * opac
    rug[i0:i1, j0:j1] = rug[i0:i1, j0:j1] * (1 - m) + rug_ * m
# espátula en el marfil (capas cruzadas, empaste)
for _ in range(520):
    cu_, cv_ = rng.random() * 1.81, rng.random(); ang = rng.normal(0.35, 0.5)
    c = np.array([0.745, 0.72, 0.66]) * (1 + rng.normal(0, 0.025)); trazo(cu_, cv_, ang, rng.uniform(0.08, 0.30), rng.uniform(0.02, 0.06), c, rng.uniform(0.45, 0.75), 0.82, rng.uniform(0.5, 0.9), (~negro).astype(np.float32))
# masa negra: pinceladas gestuales que siguen el arco (y el pilar en vertical)
mneg = negro.astype(np.float32)
for _ in range(700):
    cu_, cv_ = rng.random() * 1.81, rng.random(); i, j = int((1 - cv_) * (PH - 1)), int(cu_ / 1.81 * (PW - 1))
    if not negro[i, j]: continue
    tang = math.atan2(cv_ + 0.55, cu_ - 1.55) + math.pi / 2 if abs(cu_ - 0.42) > 0.12 else math.pi / 2
    k_ = rng.uniform(0.018, 0.04); trazo(cu_, cv_, tang + rng.normal(0, 0.12), rng.uniform(0.12, 0.45), rng.uniform(0.03, 0.09), (k_, k_ * 0.97, k_ * 0.94), rng.uniform(0.75, 1.0), rng.uniform(0.28, 0.5), rng.uniform(0.7, 1.0), mneg)
# pincel seco en los bordes del negro (deja ver el marfil) y salpicado mínimo
borde_n = negro & ~np.roll(negro, 6, 1) | negro & ~np.roll(negro, -6, 0)
seco = borde_n & (fino > 0.55); color[seco] = color[seco] * 0.3 + np.array([0.70, 0.68, 0.62]) * 0.7
# pan de oro con craquelado
oro = (np.abs(r - (1.12 + grosor + 0.035)) < 0.009 + 0.012 * n3 * (wu > 0.9)) | ((wu > 1.42) & (wv > 0.74) & (n3 > 0.5) & (np.abs(r - 1.55) < 0.10))
oro &= ~negro; craq = oro & (np.abs(ruido(PH, PW, 5, 40, 11) - 0.5) < 0.012)
color[oro] = np.array([0.80, 0.64, 0.38]) * (1 + 0.15 * (n1[oro, None] - .5)); color[craq] *= 0.55
alt[oro] = 0.5 + 0.05 * fino[oro]; rug[oro] = 0.18 + 0.14 * fino[oro]; rug[craq] = 0.6
metal = oro & ~craq
alt = (alt - alt.min()) / (alt.max() - alt.min())
def a_srgb(c): return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(np.clip(c, 0, 1), 1 / 2.4) - 0.055)
def imagen(nombre, rgb, no_color):
    im = bpy.data.images.new(nombre, PW, PH); im.colorspace_settings.name = 'Non-Color' if no_color else 'sRGB'
    px = np.ones((PH, PW, 4), np.float32); px[..., :3] = np.clip(rgb, 0, 1); im.pixels.foreach_set(np.ascontiguousarray(px[::-1]).ravel()); im.update(); im.pack(); return im
IMC = imagen('sala_arte_color_4k', a_srgb(color), False); IMD = imagen('sala_arte_datos_4k', np.stack([alt, metal.astype(np.float32), rug], -1), True)
os.makedirs(OUT, exist_ok=True)
rv = bpy.data.images.new('rev', PW, PH); rv.pixels.foreach_set(np.array(IMC.pixels[:], np.float32)); rv.filepath_raw = os.path.join(OUT, 'obra_de_arte_4k.png'); rv.file_format = 'PNG'; rv.save(); bpy.data.images.remove(rv)
ARTE = bpy.data.materials['sala_arte_abstracto']; nt = ARTE.node_tree
for n in nt.nodes:
    if n.bl_idname == 'ShaderNodeTexImage': n.image = IMC if n.image and 'color' in n.image.name else IMD
    if n.bl_idname == 'ShaderNodeBump': n.inputs['Strength'].default_value = 0.35; n.inputs['Distance'].default_value = 0.0015
b = nt.nodes['Principled BSDF']; b.inputs['Coat Weight'].default_value = 0.0
# lienzo con malla fina para relieve real
viejo = obj('ARTE_lienzo_frente'); bpy.data.objects.remove(viejo, do_unlink=True)
x_f = XW + 0.045 + 0.04
bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap'); NU, NV = 420, 232
vs = [[bm.verts.new((x_f, YC - AW / 2 + AW * i / NU, ACZ - AH / 2 + AH * j / NV)) for j in range(NV + 1)] for i in range(NU + 1)]
for i in range(NU):
    for j in range(NV):
        f = bm.faces.new((vs[i][j], vs[i + 1][j], vs[i + 1][j + 1], vs[i][j + 1]))
        for lp, (a_, b_) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))): lp[uvl].uv = (a_ / NU, b_ / NV)
me = bpy.data.meshes.new('ARTE_lienzo_frente'); bm.to_mesh(me); bm.free(); lienzo = bpy.data.objects.new('ARTE_lienzo_frente', me); col.objects.link(lienzo); me.materials.append(ARTE)
sb = lienzo.modifiers.new('fino', 'SUBSURF'); sb.subdivision_type = 'SIMPLE'; sb.levels = 0; sb.render_levels = 2
tx = bpy.data.textures.new('arte_altura_4k', 'IMAGE'); tx.image = IMD; tx.extension = 'EXTEND'
d = lienzo.modifiers.new('relieve', 'DISPLACE'); d.texture = tx; d.texture_coords = 'UV'; d.strength = 0.0045; d.direction = 'X'; d.mid_level = 0.0
for p in me.polygons: p.use_smooth = True
reg['cuadro'] = {'textura': f'{PW}×{PH}', 'malla_render_vertices_aprox': (NU * 4 + 1) * (NV * 4 + 1), 'relieve_mm': 4.5, 'trazos': 1220}
# marco de una pieza: perfil en L (labio frontal 8 mm, profundidad hasta el muro), ingletes continuos
for n in [o.name for o in col.objects if o.name.startswith('ARTE_marco_')]: bpy.data.objects.remove(obj(n), do_unlink=True)
g, lab, xl = 0.012, 0.008, x_f + 0.004
def rect(x, mw, mh): return [(x, YC - mw / 2, ACZ - mh / 2), (x, YC + mw / 2, ACZ - mh / 2), (x, YC + mw / 2, ACZ + mh / 2), (x, YC - mw / 2, ACZ + mh / 2)]
ext_f = rect(xl, AW + 2 * (g + lab), AH + 2 * (g + lab)); int_f = rect(xl, AW + 2 * g, AH + 2 * g)
ext_b = rect(XW + 0.002, AW + 2 * (g + lab), AH + 2 * (g + lab)); int_b = rect(xl - 0.006, AW + 2 * g, AH + 2 * g)
bm = bmesh.new(); EF = [bm.verts.new(p) for p in ext_f]; IF = [bm.verts.new(p) for p in int_f]; EB = [bm.verts.new(p) for p in ext_b]; IB = [bm.verts.new(p) for p in int_b]
for k in range(4):
    k2 = (k + 1) % 4
    bm.faces.new((EF[k], EF[k2], IF[k2], IF[k])); bm.faces.new((EB[k], EB[k2], EF[k2], EF[k])); bm.faces.new((IF[k], IF[k2], IB[k2], IB[k]))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
me = bpy.data.meshes.new('ARTE_marco_laton'); bm.to_mesh(me); bm.free(); marco = bpy.data.objects.new('ARTE_marco_laton', me); col.objects.link(marco)
me.materials.append(bpy.data.materials['sala_laton_satinado']); sl = marco.modifiers.new('espesor', 'SOLIDIFY'); sl.thickness = 0.0015
bv = marco.modifiers.new('cantos', 'BEVEL'); bv.width = 0.0006; bv.segments = 2
reg['tiempos_s']['cuadro'] = round(time.time() - t, 1)

# ================================================================ 3. MUEBLE TV: cantos, espesores y respuesta física
t = time.time()
for o in col.objects:
    if o.name.startswith('TV_') and o.type == 'MESH':
        for m in [m for m in o.modifiers if m.type == 'BEVEL']:
            m.width = 0.0015 if 'piedra' in o.name else 0.001; m.segments = 3; m.limit_method = 'ANGLE'; m.harden_normals = True
        if o.modifiers: o.data.shade_smooth() if hasattr(o.data, 'shade_smooth') else None
reg['mueble_tv'].append('cantos: radio 1,5 mm en piedra y 1 mm en roble, normales endurecidas (canto definido sin facetas)')
# piedra apomazada con microrrayado
P = bpy.data.materials['sala_piedra_grafito_vetada']; nt = P.node_tree; bp = nt.nodes['Principled BSDF']
mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (900, 25, 900); tc = nt.nodes.new('ShaderNodeTexCoord'); nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
rz = nt.nodes.new('ShaderNodeTexNoise'); rz.inputs['Detail'].default_value = 2; nt.links.new(mp.outputs['Vector'], rz.inputs['Vector'])
bu = nt.nodes.new('ShaderNodeBump'); bu.inputs['Strength'].default_value = 0.04; bu.inputs['Distance'].default_value = 0.0002; nt.links.new(rz.outputs['Fac'], bu.inputs['Height'])
nt.links.new(bu.outputs['Normal'], bp.inputs['Normal'])
reg['mueble_tv'].append('piedra: apomazada (rugosidad 0,22–0,34 variable) + microrrayado direccional en relieve')
# roble: poro abierto a lo largo de la veta + barniz satinado
R = bpy.data.materials['sala_roble_ahumado']; nt = R.node_tree; br = nt.nodes['Principled BSDF']
mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (260, 260, 6); tc = nt.nodes.new('ShaderNodeTexCoord'); nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
po = nt.nodes.new('ShaderNodeTexNoise'); po.inputs['Detail'].default_value = 3; nt.links.new(mp.outputs['Vector'], po.inputs['Vector'])
bu = nt.nodes.new('ShaderNodeBump'); bu.inputs['Strength'].default_value = 0.18; bu.inputs['Distance'].default_value = 0.0004; bu.invert = True
nt.links.new(po.outputs['Fac'], bu.inputs['Height']); nm = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeNormalMap')
nt.links.new(nm.outputs['Normal'], bu.inputs['Normal']); nt.links.new(bu.outputs['Normal'], br.inputs['Normal'])
br.inputs['Coat Weight'].default_value = 0.18; br.inputs['Coat Roughness'].default_value = 0.32
reg['mueble_tv'].append('roble ahumado: poro abierto vertical en relieve, barniz satinado (coat 0,18 / 0,32); veta continua entre frentes (coordenadas comunes)')
# bronce cepillado anisotrópico
B = bpy.data.materials['sala_bronce_oscuro']; nt = B.node_tree; bb = nt.nodes['Principled BSDF']
bb.inputs['Anisotropic'].default_value = 0.65; bb.inputs['Roughness'].default_value = 0.3
tg = nt.nodes.new('ShaderNodeTangent'); tg.direction_type = 'RADIAL'; tg.axis = 'Z'; nt.links.new(tg.outputs['Tangent'], bb.inputs['Tangent'])
reg['mueble_tv'].append('bronce: cepillado anisotrópico (0,65)')
# LED inferior: tira más ancha y retranqueada, gradiente suave sin punto caliente
led = obj('TV_consola_led_inferior'); co = np.array([vv.co[:] for vv in led.data.vertices])
x0_, x1_ = co[:, 0].min(), co[:, 0].max()
for vv in led.data.vertices: vv.co.x = (x0_ - 0.01) if vv.co.x < (x0_ + x1_) / 2 else (x0_ + 0.018)
em = next(n for n in bpy.data.materials['sala_led_indirecto_2700K'].node_tree.nodes if n.bl_idname == 'ShaderNodeEmission'); em.inputs['Strength'].default_value = 3.0
reg['mueble_tv'].append('LED inferior 2700 K: 28 mm de ancho, retranqueado 5 cm, intensidad 6 → 3 (gradiente suave)')
reg['tiempos_s']['mueble_tv'] = round(time.time() - t, 1)

# ================================================================ 4. ILUMINACIÓN: dos focos existentes reorientados al cuadro
for n, ytg in (('Luz_social_1', YC - 0.55), ('Luz_social_2', YC + 0.55)):
    L = obj(n); antes = [round(math.degrees(a), 1) for a in L.rotation_euler]
    d_ = (Vector((XW + 0.05, ytg, ACZ - 0.05)) - L.location).normalized(); L.rotation_euler = d_.to_track_quat('-Z', 'Y').to_euler()
    reg['iluminacion'].append({'foco': n, 'rotacion_antes': antes, 'rotacion_despues': [round(math.degrees(a), 1) for a in L.rotation_euler],
                               'energia_W': L.data.energy, 'K': L.data.temperature, 'apunta_a': [round(XW, 2), round(ytg, 2), round(ACZ - 0.05, 2)]})

# ================================================================ guardar y vista de control
bpy.ops.file.pack_all(); bpy.ops.wm.save_as_mainfile(filepath=SAL, copy=True, compress=True)
cp = bpy.context.preferences.addons['cycles'].preferences; cp.compute_device_type = 'OPTIX'; cp.refresh_devices()
for dv in cp.devices: dv.use = dv.type == 'OPTIX'
c = sc.cycles; sc.render.engine = 'CYCLES'; c.device = 'GPU'; c.denoiser = 'OPTIX'; c.use_denoising = True; c.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
c.samples = 512; c.use_adaptive_sampling = True; c.adaptive_threshold = 0.008
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 720, 100
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'; sc.render.image_settings.color_depth = '8'
def camara(nombre, desde, hacia, fov):
    p = Vector((desde[0] - OX, desde[1] - OY, desde[2])); t_ = Vector((hacia[0] - OX, hacia[1] - OY, hacia[2])); dh = Vector((t_.x - p.x, t_.y - p.y))
    cd = bpy.data.cameras.new(nombre); cd.lens_unit = 'FOV'; cd.angle = math.radians(fov); cd.sensor_fit = 'HORIZONTAL'; cd.clip_start = 0.03
    cd.shift_y = ((t_.z - p.z) / dh.length) / (2 * math.tan(math.radians(fov) / 2))
    ob = bpy.data.objects.new(nombre, cd); col.objects.link(ob); ob.location = p; ob.rotation_euler = (math.radians(90), 0, math.atan2(dh.y, dh.x) - math.radians(90)); return ob
sc.camera = camara('CAM_control_sala_v2', (1.65, 4.45, 1.35), (1.25, 0.6, 1.05), 76)
sc.view_settings.exposure = 2.1
t = time.time(); sc.render.filepath = os.path.join(OUT, 'vista_control_sala_v2.png'); bpy.ops.render.render(write_still=True); reg['tiempos_s']['render_control'] = round(time.time() - t, 1)
reg['tiempos_s']['total'] = round(time.time() - T0, 1); reg['blend'] = SAL
json.dump(reg, open(os.path.join(OUT, 'rediseno_sala_v2.json'), 'w'), indent=1, ensure_ascii=False, default=str)
print('[sala2] TIEMPOS', reg['tiempos_s']); print('SALA2_OK')
