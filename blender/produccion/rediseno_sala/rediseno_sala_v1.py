# ORA · Apartamento 102 (PROPUESTA DE REDISTRIBUCIÓN, no planta verificada) · Rediseño de la sala, versión independiente.
# Fuente: v4/escena_v4_2_prueba3.blend (solo lectura). Sustituye SOLO mobiliario/decoración de la sala:
#  1) sofá  2) obra de arte  3) mueble del TV. No toca muros, vanos, puertas, ventanas, dimensiones ni distribución:
#  el sofá nuevo ocupa la huella aprobada (propuesta-102.json: sofa [0.15,1.04,1.1,3.16]) y el mueble TV el muro existente.
#   blender -b v4/escena_v4_2_prueba3.blend --python rediseno_sala/rediseno_sala.py -- <blend_salida> <carpeta_previas>
import bpy, bmesh, sys, os, math, json, time
import numpy as np
from mathutils import Vector, Matrix
SAL, PREV = sys.argv[sys.argv.index('--') + 1:][:2]
sc = bpy.context.scene; OX, OY = 4.037, 3.8
reg = {'eliminado': [], 'creado': [], 'previas': []}
col = bpy.data.collections.new('REDISENO_SALA'); sc.collection.children.link(col)

# ---------------------------------------------------------------- materiales
def mat_nuevo(nombre):
    m = bpy.data.materials.new(nombre); m.use_nodes = True; return m, m.node_tree, m.node_tree.nodes['Principled BSDF']
def coords_caja(nt, escala):
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (escala,) * 3
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); return mp
def buscar_img(pref):
    pref = pref.split('.')[0][:18]
    im = next((i for i in bpy.data.images if i.name.startswith(pref)), None)
    assert im, f'imagen no encontrada: {pref}'; return im
def img_caja(nt, imagen, mp, no_color=True):
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = buscar_img(imagen); t.projection = 'BOX'; t.projection_blend = 0.25
    nt.links.new(mp.outputs['Vector'], t.inputs['Vector']); return t
def tela(nombre, rgb, normal_img, escala, fuerza, sheen=0.25, var=0.04, rizo=0):
    m, nt, b = mat_nuevo(nombre); mp = coords_caja(nt, escala)
    tn = img_caja(nt, normal_img, mp); nm = nt.nodes.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = fuerza
    nt.links.new(tn.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], b.inputs['Normal'])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 2.0; nz.inputs['Detail'].default_value = 6
    nt.links.new(mp.outputs['Vector'], nz.inputs['Vector'])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 1 - var; mr.inputs['To Max'].default_value = 1 + var
    nt.links.new(nz.outputs['Fac'], mr.inputs['Value'])
    mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1
    mx.inputs['A'].default_value = (*rgb, 1); nt.links.new(mr.outputs['Result'], mx.inputs['B']); nt.links.new(mx.outputs['Result'], b.inputs['Base Color'])
    if rizo:
        vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = rizo; vo.inputs['Randomness'].default_value = 1.0
        nt.links.new(mp.outputs['Vector'], vo.inputs['Vector'])
        bu = nt.nodes.new('ShaderNodeBump'); bu.inputs['Strength'].default_value = 0.35; bu.inputs['Distance'].default_value = 0.0015
        nt.links.new(vo.outputs['Distance'], bu.inputs['Height']); nt.links.new(nm.outputs['Normal'], bu.inputs['Normal']); nt.links.new(bu.outputs['Normal'], b.inputs['Normal'])
    b.inputs['Roughness'].default_value = 0.92; b.inputs['Sheen Weight'].default_value = sheen; b.inputs['Sheen Roughness'].default_value = 0.5
    b.inputs['Specular IOR Level'].default_value = 0.2; return m
TAPICERIA = tela('sala_tapiceria_premium', (0.44, 0.40, 0.345), 'wool_boucle_nor_gl_2k.jpg', 3.0, 0.7, sheen=0.2, var=0.06, rizo=45)
COJ_CARBON = tela('sala_cojin_carbon', (0.05, 0.048, 0.045), 'wool_boucle_nor_gl_2k.jpg', 3.5, 0.8, sheen=0.35, rizo=55)
COJ_MARFIL = tela('sala_cojin_marfil_lino', (0.62, 0.585, 0.53), 'rough_linen_nor_gl_2k.jpg', 3.0, 1.0)
COJ_TOPO = tela('sala_cojin_topo', (0.24, 0.205, 0.17), 'rough_linen_nor_gl_2k.jpg', 3.0, 1.0)
def metal(nombre, rgb, rug):
    m, nt, b = mat_nuevo(nombre); b.inputs['Base Color'].default_value = (*rgb, 1); b.inputs['Metallic'].default_value = 1; b.inputs['Roughness'].default_value = rug; return m
BRONCE = metal('sala_bronce_oscuro', (0.11, 0.085, 0.06), 0.38)
LATON = metal('sala_laton_satinado', (0.78, 0.60, 0.36), 0.28)
LACA, nt, b = mat_nuevo('sala_laca_grafito_mate'); b.inputs['Base Color'].default_value = (0.032, 0.031, 0.03, 1); b.inputs['Roughness'].default_value = 0.6
b.inputs['Coat Weight'].default_value = 0.05
SOMBRA, nt, b = mat_nuevo('sala_ranura_negra'); b.inputs['Base Color'].default_value = (0.01, 0.01, 0.01, 1); b.inputs['Roughness'].default_value = 0.9
# roble ahumado: mismo chapado de roble del proyecto, oscurecido
ROBLE, nt, b = mat_nuevo('sala_roble_ahumado'); mp = coords_caja(nt, 1.6)
td = img_caja(nt, 'oak_veneer_01_Diffuse_2k.jpg', mp, False); tr = img_caja(nt, 'oak_veneer_01_Rough_2k.jpg', mp); tn = img_caja(nt, 'oak_veneer_01_nor_gl_2k.jpg', mp)
hs = nt.nodes.new('ShaderNodeHueSaturation'); hs.inputs['Value'].default_value = 0.2; hs.inputs['Saturation'].default_value = 0.8
nt.links.new(td.outputs['Color'], hs.inputs['Color']); nt.links.new(hs.outputs['Color'], b.inputs['Base Color'])
mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 0.42; mr.inputs['To Max'].default_value = 0.62
nt.links.new(tr.outputs['Color'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], b.inputs['Roughness'])
nm = nt.nodes.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = 0.4; nt.links.new(tn.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], b.inputs['Normal'])
b.inputs['Coat Weight'].default_value = 0.1; b.inputs['Coat Roughness'].default_value = 0.35
# piedra natural oscura con vetas marfil (eco del negro y marfil de la obra), procedural
PIEDRA, nt, b = mat_nuevo('sala_piedra_grafito_vetada'); mp = coords_caja(nt, 1.0)
nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 1.6; nz.inputs['Detail'].default_value = 14; nz.inputs['Distortion'].default_value = 2.5
nt.links.new(mp.outputs['Vector'], nz.inputs['Vector'])
dsp = nt.nodes.new('ShaderNodeVectorMath'); dsp.operation = 'MULTIPLY_ADD'; dsp.inputs[1].default_value = (0.35, 0.35, 0.35)
nt.links.new(nz.outputs['Color'], dsp.inputs[0]); nt.links.new(mp.outputs['Vector'], dsp.inputs[2])
def vetas(escala, ancho, peso, sem):
    vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.feature = 'DISTANCE_TO_EDGE'; vo.inputs['Scale'].default_value = escala
    nt.links.new(dsp.outputs['Vector'], vo.inputs['Vector'])
    m1 = nt.nodes.new('ShaderNodeMapRange'); m1.inputs['From Min'].default_value = 0.0; m1.inputs['From Max'].default_value = ancho
    m1.inputs['To Min'].default_value = peso; m1.inputs['To Max'].default_value = 0.0; nt.links.new(vo.outputs['Distance'], m1.inputs['Value'])
    nm_ = nt.nodes.new('ShaderNodeTexNoise'); nm_.noise_dimensions = '4D'; nm_.inputs['Scale'].default_value = 2.2; nm_.inputs['Detail'].default_value = 4
    [i for i in nm_.inputs if i.identifier == 'W'][0].default_value = sem; nt.links.new(mp.outputs['Vector'], nm_.inputs['Vector'])
    mk = nt.nodes.new('ShaderNodeMapRange'); mk.inputs['From Min'].default_value = 0.48; mk.inputs['From Max'].default_value = 0.62; nt.links.new(nm_.outputs['Fac'], mk.inputs['Value'])
    mu_ = nt.nodes.new('ShaderNodeMath'); mu_.operation = 'MULTIPLY'; nt.links.new(m1.outputs['Result'], mu_.inputs[0]); nt.links.new(mk.outputs['Result'], mu_.inputs[1])
    return mu_
v1 = vetas(2.2, 0.010, 1.0, 1.3); v2 = vetas(6.5, 0.0045, 0.55, 7.7)
mxv = nt.nodes.new('ShaderNodeMath'); mxv.operation = 'MAXIMUM'; nt.links.new(v1.outputs[0], mxv.inputs[0]); nt.links.new(v2.outputs[0], mxv.inputs[1])
mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.inputs['A'].default_value = (0.026, 0.025, 0.025, 1); mx.inputs['B'].default_value = (0.36, 0.345, 0.32, 1)
nt.links.new(mxv.outputs[0], mx.inputs['Factor']); nt.links.new(mx.outputs['Result'], b.inputs['Base Color'])
mr2 = nt.nodes.new('ShaderNodeMapRange'); mr2.inputs['To Min'].default_value = 0.22; mr2.inputs['To Max'].default_value = 0.34
nt.links.new(nz.outputs['Fac'], mr2.inputs['Value']); nt.links.new(mr2.outputs['Result'], b.inputs['Roughness'])
LED, nt, b = mat_nuevo('sala_led_indirecto_2700K')
nt.nodes.remove(b); em = nt.nodes.new('ShaderNodeEmission'); bb_ = nt.nodes.new('ShaderNodeBlackbody'); bb_.inputs[0].default_value = 2700
nt.links.new(bb_.outputs[0], em.inputs['Color']); em.inputs['Strength'].default_value = 6.0; nt.links.new(em.outputs[0], nt.nodes['Material Output'].inputs['Surface'])

# ---------------------------------------------------------------- utilidades de geometría
def objeto(nombre, bm, mats, suave=False, sub=0):
    me = bpy.data.meshes.new(nombre); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(nombre, me); col.objects.link(o)
    for m in mats: o.data.materials.append(m)
    if suave:
        for p in me.polygons: p.use_smooth = True
    if sub: s = o.modifiers.new('sub', 'SUBSURF'); s.levels = sub; s.render_levels = sub
    reg['creado'].append(nombre); return o
def caja(nombre, x0, x1, y0, y1, z0, z1, mat, bisel=0.002):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1)
    for v in bm.verts: v.co = Vector(((x0 + x1) / 2 + v.co.x * (x1 - x0), (y0 + y1) / 2 + v.co.y * (y1 - y0), (z0 + z1) / 2 + v.co.z * (z1 - z0)))
    o = objeto(nombre, bm, [mat])
    if bisel: bv = o.modifiers.new('bisel', 'BEVEL'); bv.width = bisel; bv.segments = 3; bv.limit_method = 'ANGLE'
    return o
def cojin(nombre, centro, dim, mat, abomb=(0.02, 0.02, 0.03), cortes=6, rot=None, sub=2, cintura=0.0):
    """Volumen tapizado: cubo subdividido con abombado suave en cada cara (más lleno en el centro) + Catmull-Clark."""
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=2)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cortes, use_grid_fill=True)
    bx, by, bz = abomb
    for v in bm.verts:
        u, w_, h = v.co.x, v.co.y, v.co.z
        d = Vector((u * bx * (1 - w_ * w_) * (1 - h * h), w_ * by * (1 - u * u) * (1 - h * h), h * bz * (1 - u * u) * (1 - w_ * w_)))
        if cintura:   # silueta de cojín real: bordes curvados hacia dentro y esquinas marcadas
            w_ *= 1 - cintura * (1 - h * h); h *= 1 - cintura * (1 - v.co.y * v.co.y)
        v.co = Vector((u * dim[0] / 2, w_ * dim[1] / 2, h * dim[2] / 2)) + d
    o = objeto(nombre, bm, [mat], suave=True, sub=sub)
    o.location = centro
    if rot: o.rotation_euler = rot
    return o

# ---------------------------------------------------------------- 0. retirar lo que se sustituye
def eliminar_obj(n):
    o = sc.objects.get(n)
    if o: bpy.data.objects.remove(o, do_unlink=True); reg['eliminado'].append(n)
for n in ('GlamVelvetSofa_fabric', 'GlamVelvetSofa_feet', 'GlamVelvetSofa_legs', 'MOB_Sofa'): eliminar_obj(n)
ms = sc.objects['MOB_Sala']; bm = bmesh.new(); bm.from_mesh(ms.data); bm.faces.ensure_lookup_table(); Mw = ms.matrix_world
vis, borrar, cont = set(), [], {}
for f in bm.faces:
    if f.index in vis: continue
    pila, grupo = [f], []
    while pila:
        g = pila.pop()
        if g.index in vis: continue
        vis.add(g.index); grupo.append(g)
        for e in g.edges:
            for h in e.link_faces:
                if h.index not in vis: pila.append(h)
    vs = [Mw @ v.co for g in grupo for v in g.verts]; xs = [p.x for p in vs]; ys = [p.y for p in vs]; zs = [p.z for p in vs]
    mats = {ms.material_slots[g.material_index].material.name for g in grupo}
    muro_tv = min(xs) > -1.50 and max(xs) < -1.43 and min(ys) > -2.80 and max(ys) < -0.60
    cuadro = ('cuadro' in mats) or ('madera_mueble' in mats and min(xs) > -3.90 and max(xs) < -3.85 and min(zs) > 1.0)
    tv_mueble = muro_tv and (mats & {'madera_mueble', 'carcasa', 'luz_calida', 'metal_negro'})
    if cuadro or tv_mueble:
        clave = 'cuadro actual (lienzo y marco de madera)' if cuadro else 'mueble TV actual: ' + ', '.join(sorted(mats))
        cont[clave] = cont.get(clave, 0) + 1; borrar += grupo
bmesh.ops.delete(bm, geom=list({f for f in borrar}), context='FACES'); bm.to_mesh(ms.data); bm.free()
for k, v in cont.items(): reg['eliminado'].append(f'MOB_Sala → {k}: {v} pieza(s)')

# ---------------------------------------------------------------- 1. SOFÁ ESCULTÓRICO (huella aprobada: plano x 0,15–1,10 · y 1,04–3,16)
# Concha continua respaldo-brazos en U con radios generosos y brazos que se afinan hacia el frente; base tapizada sobre
# zócalo de bronce rehundido (sombra flotante); asiento continuo y cojines de respaldo blandos.
X0, X1 = 0.15 - OX + 0.025, 1.10 - OX
Y0, Y1 = 1.04 - OY, 3.16 - OY
D, L = X1 - X0, Y1 - Y0; YC = (Y0 + Y1) / 2
caja('SOFA_zocalo_bronce', X0 + 0.09, X1 - 0.09, Y0 + 0.09, Y1 - 0.09, 0.0, 0.06, BRONCE, 0.004)
base = caja('SOFA_base', X0 + 0.005, X1 - 0.005, Y0 + 0.005, Y1 - 0.005, 0.06, 0.26, TAPICERIA, 0.0)
bv = base.modifiers.new('radios', 'BEVEL'); bv.width = 0.07; bv.segments = 8; bv.limit_method = 'ANGLE'
for pl in base.data.polygons: pl.use_smooth = True
def trayecto_u(x0, x1, y0, y1, rad, n=14):
    """Trayecto en planta: frente brazo izq → muro → a lo largo del muro → frente brazo der, con esquinas redondeadas."""
    pts = [(x1, y0)]
    for k in range(n + 1):                                   # esquina (x0, y0)
        a_ = math.pi + k / n * (math.pi / 2); pts.append((x0 + rad + rad * math.cos(a_), y0 + rad + rad * math.sin(a_)))
    for k in range(n + 1):                                   # esquina (x0, y1)
        a_ = math.pi / 2 + k / n * (math.pi / 2); pts.append((x0 + rad + rad * math.cos(a_), y1 - rad + rad * math.sin(a_)))
    pts.append((x1, y1)); return pts[::-1][::-1]
W_C, H_C, ZC = 0.26, 0.42, 0.40
pts = trayecto_u(X0 + W_C / 2 + 0.005, X1 - 0.03, Y0 + W_C / 2 + 0.005, Y1 - W_C / 2 - 0.005, 0.30)
# perfil: rectángulo de esquinas muy redondeadas
pc = bpy.data.curves.new('SOFA_perfil', 'CURVE'); pc.dimensions = '2D'; sp = pc.splines.new('POLY'); prof = []
for k in range(4):
    cx, cy = (W_C / 2 - 0.10) * (1 if k in (0, 3) else -1), (H_C / 2 - 0.12) * (1 if k in (0, 1) else -1)
    for j in range(9):
        a_ = (k * 90 + j * 90 / 8) * math.pi / 180; rx, ry = 0.10, 0.12
        prof.append((cx + rx * math.cos(a_), cy + ry * math.sin(a_)))
sp.points.add(len(prof) - 1)
for pt, (px_, py_) in zip(sp.points, prof): pt.co = (px_, py_, 0, 1)
sp.use_cyclic_u = True; perfil = bpy.data.objects.new('SOFA_perfil', pc)
cu = bpy.data.curves.new('SOFA_concha', 'CURVE'); cu.dimensions = '3D'; cu.twist_mode = 'Z_UP'; cu.bevel_mode = 'OBJECT'; cu.bevel_object = perfil
cu.use_fill_caps = True; cu.resolution_u = 2
s2 = cu.splines.new('POLY'); s2.points.add(len(pts) - 1)
nps = len(pts)
for i, (pt, (x_, y_)) in enumerate(zip(s2.points, pts)):
    # afinado escultórico: 1,0 en el respaldo, 0,74 en el frente de los brazos
    dist_frente = min(i, nps - 1 - i) / 9.0
    pt.co = (x_, y_, ZC, 1); pt.radius = 0.60 + 0.40 * min(1.0, dist_frente) ** 0.8
oc = bpy.data.objects.new('SOFA_concha_tmp', cu); col.objects.link(oc); col.objects.link(perfil)
dg = bpy.context.evaluated_depsgraph_get(); me = bpy.data.meshes.new_from_object(oc.evaluated_get(dg))
bpy.data.objects.remove(oc, do_unlink=True); bpy.data.objects.remove(perfil, do_unlink=True)
zs = [v.co.z for v in me.vertices]; ext_z = max(zs) - min(zs)
if ext_z < 0.3: raise SystemExit(f'[sala] ERROR orientación del perfil: altura de la concha {ext_z:.2f} m')
concha = bpy.data.objects.new('SOFA_concha_respaldo_brazos', me); col.objects.link(concha); me.materials.append(TAPICERIA)
for pl in me.polygons: pl.use_smooth = True
sb = concha.modifiers.new('sub', 'SUBSURF'); sb.levels = 1; sb.render_levels = 2
reg['creado'].append(concha.name); reg['concha_altura_z'] = [round(min(zs), 3), round(max(zs), 3)]
# asiento continuo entre brazos, frente generosamente redondeado
LI = L - 2 * W_C - 0.02; DI = D - W_C - 0.05
cojin('SOFA_asiento_continuo', (X0 + W_C + 0.01 + DI / 2, YC, 0.26 + 0.085), (DI, LI, 0.17), TAPICERIA, (0.06, 0.012, 0.028), 9)
for k in range(2):
    yc = YC - LI / 4 + k * LI / 2
    cojin(f'SOFA_cojin_respaldo_{k+1}', (X0 + W_C + 0.11, yc, 0.43 + 0.16), (0.17, LI / 2 - 0.03, 0.32), TAPICERIA, (0.05, 0.02, 0.02), 8, rot=(0, math.radians(-14), 0))
def cojin_deco(nombre, centro, lado, mat, rot):
    o = cojin(nombre, centro, (0.03, lado, lado), mat, (0.115, 0.0, 0.0), 10, rot=rot, cintura=0.09)
    # vivo (cordón de costura) siguiendo el perímetro del cojín
    cu_ = bpy.data.curves.new(nombre + '_vivo', 'CURVE'); cu_.dimensions = '3D'; cu_.bevel_depth = 0.0042; cu_.bevel_resolution = 3
    sp_ = cu_.splines.new('POLY'); h_ = lado / 2; rr = 0.035; ptsv = []
    for k in range(4):
        cy_, cz_ = (h_ - rr) * (1 if k in (0, 3) else -1), (h_ - rr) * (1 if k in (0, 1) else -1)
        for j in range(7):
            a_ = (k * 90 + j * 15) * math.pi / 180; yv, zv = cy_ + rr * math.cos(a_), cz_ + rr * math.sin(a_)
            yn, zn = yv / (lado / 2), zv / (lado / 2)       # misma cintura que el cojín: el vivo sigue el borde curvado
            ptsv.append((0, yv * (1 - 0.09 * (1 - zn * zn)) - 0.004 * math.copysign(1, yv), zv * (1 - 0.09 * (1 - yn * yn)) - 0.004 * math.copysign(1, zv)))
    sp_.points.add(len(ptsv) - 1)
    for pt, c_ in zip(sp_.points, ptsv): pt.co = (*c_, 1)
    sp_.use_cyclic_u = True; cu_.materials.append(mat)
    v_ = bpy.data.objects.new(nombre + '_vivo', cu_); col.objects.link(v_); v_.parent = o; reg['creado'].append(v_.name)
    return o
for n, (y, lado, mat, inc, gz) in {'SOFA_deco_marfil': (Y0 + W_C + 0.24, 0.45, COJ_MARFIL, -18, 0.12),
                                    'SOFA_deco_carbon': (Y0 + W_C + 0.50, 0.40, COJ_CARBON, -14, 0.25),
                                    'SOFA_deco_topo': (Y1 - W_C - 0.26, 0.43, COJ_TOPO, -19, -0.18)}.items():
    cojin_deco(n, (X0 + W_C + 0.30, y, 0.43 + lado / 2 - 0.03), lado, mat, (0, math.radians(inc), gz))

# ---------------------------------------------------------------- 2. OBRA DE ARTE abstracta de gran formato (original, generada)
AW, AH = 1.90, 1.05; ACX, ACY, ACZ = -3.86 + 0.045, YC, 1.50
def ruido(h, w, oct_, base, sem):
    rng = np.random.default_rng(sem); out = np.zeros((h, w), np.float32); amp = 1.0; tot = 0
    for o in range(oct_):
        gh, gw = base * 2 ** o, int(base * 2 ** o * w / h) + 1
        g = rng.random((gh + 2, gw + 2)).astype(np.float32)
        yy = np.linspace(0, gh, h, dtype=np.float32); xx = np.linspace(0, gw, w, dtype=np.float32)
        y0 = yy.astype(int); x0 = xx.astype(int); fy = (yy - y0)[:, None]; fx = (xx - x0)[None, :]
        fy = fy * fy * (3 - 2 * fy); fx = fx * fx * (3 - 2 * fx)
        a = g[y0][:, x0]; b_ = g[y0][:, x0 + 1]; c_ = g[y0 + 1][:, x0]; d_ = g[y0 + 1][:, x0 + 1]
        out += amp * ((a * (1 - fx) + b_ * fx) * (1 - fy) + (c_ * (1 - fx) + d_ * fx) * fy); tot += amp; amp *= 0.5
    return out / tot
PH, PW = 1100, 1990
yy, xx = np.mgrid[0:PH, 0:PW].astype(np.float32); u = xx / PW * (AW / AH); v = 1 - yy / PH   # u en [0, 1.81], v en [0,1] (arriba = 1)
n1 = ruido(PH, PW, 6, 3, 1); n2 = ruido(PH, PW, 6, 5, 2); n3 = ruido(PH, PW, 7, 14, 3)
wu, wv = u + 0.06 * (n1 - .5), v + 0.06 * (n2 - .5)
# masa negra: gran arco gestual que nace abajo a la izquierda y se abre hacia arriba a la derecha, borde irregular
r = np.sqrt((wu - 1.55) ** 2 + (wv + 0.55) ** 2)
grosor = 0.15 + 0.11 * np.clip((1.3 - wu) / 1.3, 0, 1) + 0.03 * (n3 - .5)
negro = (np.abs(r - 1.12) < grosor) & (wu > 0.15)
# pilar negro vertical a la izquierda, afinado y con remate superior desgarrado
estria = np.repeat(ruido(PH, PW // 14 + 1, 5, 30, 7), 14, axis=1)[:, :PW]      # pinceladas horizontales (trazo de espátula)
estria_v = np.repeat(ruido(PH // 14 + 1, PW, 5, 3, 8), 14, axis=0)[:PH, :]     # pinceladas verticales
negro |= (np.abs(wu - 0.42 - 0.05 * (wv - .5)) < 0.075 + 0.02 * wv + 0.025 * (n1 - .5)) & (wv < 0.80 + 0.08 * n2 + 0.05 * (estria_v - .5) * 3)
# banda de pan de oro siguiendo el borde exterior del arco + campo dorado arriba a la derecha, con bordes de lámina
oro = (np.abs(r - (1.12 + grosor + 0.035)) < 0.009 + 0.012 * n3 * (wu > 0.9)) | ((wu > 1.42) & (wv > 0.74) & (n3 + 0.15 * (estria - .5) > 0.5) & (np.abs(r - 1.55) < 0.10))
oro &= ~negro
grietas = (np.abs(ruido(PH, PW, 6, 4, 4) - 0.5) < 0.0035) & ~negro & (n1 > 0.55)  # craquelado fino y escaso
# colores en lineal (albedos físicos): marfil 0,74, grafito 0,12, negro acrílico 0,028
marfil = np.stack([0.74 + 0.05 * (n3 - .5), 0.715 + 0.05 * (n3 - .5), 0.655 + 0.05 * (n3 - .5)], -1)
colr = marfil.copy()
veladura = np.clip((n2 - 0.40) / 0.22, 0, 1) * (r < 1.12 - grosor) * (~negro) * 0.75   # veladura grafito transparente
colr = colr * (1 - veladura[..., None]) + np.array([0.12, 0.12, 0.125]) * veladura[..., None]
colr[negro] = (np.array([0.028, 0.027, 0.026]) * (1 + 0.6 * (estria[negro, None] - .5) + 0.3 * (n3[negro, None] - .5)))
colr[oro] = np.array([0.80, 0.64, 0.38]) * (1 + 0.12 * (n1[oro, None] - .5))
colr[grietas] *= 0.78
altura = 0.35 * n3 + 0.25 * estria + 0.15 * n1                               # empaste con trazo de espátula
altura[negro] = 0.70 + 0.25 * estria[negro] + 0.1 * n3[negro]; altura[oro] = 0.55 + 0.08 * n3[oro]; altura[grietas] -= 0.2
rug = np.full((PH, PW), 0.8, np.float32); rug[negro] = 0.38 + 0.15 * estria[negro]; rug[oro] = 0.22 + 0.1 * n3[oro]
metalico = oro.astype(np.float32)
grafito = veladura > 0.3
def imagen(nombre, rgb, no_color):
    im = bpy.data.images.new(nombre, PW, PH, float_buffer=False); px = np.ones((PH, PW, 4), np.float32); px[..., :3] = np.clip(rgb, 0, 1)
    im.colorspace_settings.name = 'Non-Color' if no_color else 'sRGB'; im.pixels.foreach_set(np.ascontiguousarray(px[::-1]).ravel()); im.update(); im.pack(); return im
# la imagen de color se escribe en sRGB (gamma) para que el lienzo reproduzca los tonos marfil/negro/oro tal cual
def a_srgb(c): return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(np.clip(c, 0, 1), 1 / 2.4) - 0.055)
IM_COL = imagen('sala_arte_color', a_srgb(colr), False)
os.makedirs(PREV, exist_ok=True)
_r = bpy.data.images.new('arte_revision', PW, PH); _r.pixels.foreach_set(np.array(IM_COL.pixels[:], np.float32)); _r.filepath_raw = os.path.join(PREV, 'obra_de_arte_textura.png'); _r.file_format = 'PNG'; _r.save(); bpy.data.images.remove(_r)
IM_DAT = imagen('sala_arte_datos', np.stack([np.clip(altura, 0, 1), metalico, rug], -1), True)
ARTE, nt, b = mat_nuevo('sala_arte_abstracto'); uvn = nt.nodes.new('ShaderNodeUVMap')
tc_ = nt.nodes.new('ShaderNodeTexImage'); tc_.image = IM_COL; td_ = nt.nodes.new('ShaderNodeTexImage'); td_.image = IM_DAT
nt.links.new(tc_.outputs['Color'], b.inputs['Base Color'])
sp = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(td_.outputs['Color'], sp.inputs['Color'])
nt.links.new(sp.outputs['Green'], b.inputs['Metallic']); nt.links.new(sp.outputs['Blue'], b.inputs['Roughness'])
bu = nt.nodes.new('ShaderNodeBump'); bu.inputs['Strength'].default_value = 0.7; bu.inputs['Distance'].default_value = 0.004
nt.links.new(sp.outputs['Red'], bu.inputs['Height']); nt.links.new(bu.outputs['Normal'], b.inputs['Normal'])
# lienzo: cara frontal con UV + cantos pintados marfil
bm = bmesh.new(); uv = bm.loops.layers.uv.new('UVMap')
x_f = ACX + 0.04
vs = [bm.verts.new((x_f, ACY - AW / 2, ACZ - AH / 2)), bm.verts.new((x_f, ACY + AW / 2, ACZ - AH / 2)), bm.verts.new((x_f, ACY + AW / 2, ACZ + AH / 2)), bm.verts.new((x_f, ACY - AW / 2, ACZ + AH / 2))]
f = bm.faces.new(vs)
for lp, (uu, vv) in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): lp[uv].uv = (uu, vv)
bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=60, use_grid_fill=True)
o_art = objeto('ARTE_lienzo_frente', bm, [ARTE])
d = o_art.modifiers.new('relieve', 'DISPLACE'); tx = bpy.data.textures.new('arte_altura', 'IMAGE'); tx.image = IM_DAT
d.texture = tx; d.texture_coords = 'UV'; d.strength = 0.003; d.direction = 'X'; d.mid_level = 0.0
caja('ARTE_lienzo_cantos', ACX + 0.001, x_f - 0.006, ACY - AW / 2, ACY + AW / 2, ACZ - AH / 2, ACZ + AH / 2, bpy.data.materials['sala_cojin_marfil_lino'], 0.001)
# marco flotante de latón satinado, perfil en L fino, con sombra de 12 mm
g, t_, p_ = 0.012, 0.01, 0.055
for n, (a0, a1, b0, b1) in {'sup': (ACY - AW / 2 - g - t_, ACY + AW / 2 + g + t_, ACZ + AH / 2 + g, ACZ + AH / 2 + g + t_), 'inf': (ACY - AW / 2 - g - t_, ACY + AW / 2 + g + t_, ACZ - AH / 2 - g - t_, ACZ - AH / 2 - g),
                             'izq': (ACY - AW / 2 - g - t_, ACY - AW / 2 - g, ACZ - AH / 2 - g, ACZ + AH / 2 + g), 'der': (ACY + AW / 2 + g, ACY + AW / 2 + g + t_, ACZ - AH / 2 - g, ACZ + AH / 2 + g)}.items():
    caja(f'ARTE_marco_{n}', -3.86 + 0.002, -3.86 + p_, a0, a1, b0, b1, LATON, 0.0015)
caja('ARTE_fondo_sombra', -3.86 + 0.001, -3.86 + 0.012, ACY - AW / 2 - g, ACY + AW / 2 + g, ACZ - AH / 2 - g, ACZ + AH / 2 + g, SOMBRA, 0)

# ---------------------------------------------------------------- 3. MUEBLE TV a medida: panel de roble ahumado + consola suspendida
XM = -1.444; YA, YB = -2.75, -0.65                     # muro del TV (cara interior) y ancho del muro de TV existente
NT = 4; wtab = (YB - YA) / NT
caja('TV_panel_fondo_ranuras', XM - 0.006, XM, YA, YB, 0.0, 2.38, SOMBRA, 0)
for k in range(NT):
    caja(f'TV_panel_roble_{k+1}', XM - 0.018, XM - 0.004, YA + k * wtab + 0.002, YA + (k + 1) * wtab - 0.002, 0.0, 2.38, ROBLE, 0.001)
CZ0, CH, CD = 0.24, 0.28, 0.40                         # suspendida a 24 cm del piso, 28 cm de alto, 40 cm de fondo
XC1 = XM - 0.018; XC0 = XC1 - CD
caja('TV_consola_cuerpo', XC0 + 0.02, XC1, YA + 0.05, YB - 0.05, CZ0 + 0.01, CZ0 + CH - 0.036, ROBLE, 0.002)
nf = 3; wf = (YB - YA - 0.1) / nf
for k in range(nf):
    caja(f'TV_consola_frente_{k+1}', XC0, XC0 + 0.02, YA + 0.05 + k * wf + 0.0015, YA + 0.05 + (k + 1) * wf - 0.0015, CZ0 + 0.012, CZ0 + CH - 0.038, ROBLE, 0.0015)
caja('TV_consola_filete_bronce', XC0 - 0.002, XC1, YA + 0.04, YB - 0.04, CZ0 + CH - 0.036, CZ0 + CH - 0.03, BRONCE, 0.0005)
caja('TV_consola_tapa_piedra', XC0 - 0.01, XC1, YA + 0.03, YB - 0.03, CZ0 + CH - 0.03, CZ0 + CH, PIEDRA, 0.002)
caja('TV_consola_led_inferior', XC0 + 0.06, XC0 + 0.075, YA + 0.12, YB - 0.12, CZ0 + 0.004, CZ0 + 0.008, LED, 0)
reg['dimensiones'] = {'sofa_m': [round(D, 3), round(L, 3), 'altura respaldo ~0,80'], 'arte_m': [AW, AH], 'consola_m': [round(YB - YA - 0.06, 2), CD + 0.01, CH, f'suspendida a {CZ0} m'],
                      'panel_tv_m': [round(YB - YA, 2), 2.38]}

# ---------------------------------------------------------------- guardar versión independiente
os.makedirs(os.path.dirname(SAL), exist_ok=True)
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=SAL, copy=True, compress=True)

# ---------------------------------------------------------------- vistas previas (cámara nivelada + desplazamiento óptico, como en fotografía de arquitectura)
cp = bpy.context.preferences.addons['cycles'].preferences; cp.compute_device_type = 'OPTIX'; cp.refresh_devices()
for dv in cp.devices: dv.use = dv.type == 'OPTIX'
c = sc.cycles; sc.render.engine = 'CYCLES'; c.device = 'GPU'; c.denoiser = 'OPTIX'; c.use_denoising = True; c.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
c.samples = 384; c.use_adaptive_sampling = True; c.adaptive_threshold = 0.01
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 720, 100
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'; sc.render.image_settings.color_depth = '8'
vs_ = sc.view_settings
def camara(nombre, desde, hacia, fov):
    p = Vector((desde[0] - OX, desde[1] - OY, desde[2])); t = Vector((hacia[0] - OX, hacia[1] - OY, hacia[2]))
    dh = Vector((t.x - p.x, t.y - p.y)); yaw = math.atan2(dh.y, dh.x)
    cd = bpy.data.cameras.new(nombre); cd.lens_unit = 'FOV'; cd.angle = math.radians(fov); cd.sensor_fit = 'HORIZONTAL'; cd.clip_start = 0.03
    cd.shift_y = ((t.z - p.z) / dh.length) / (2 * math.tan(math.radians(fov) / 2))
    ob = bpy.data.objects.new(nombre, cd); col.objects.link(ob); ob.location = p; ob.rotation_euler = (math.radians(90), 0, yaw - math.radians(90)); return ob
VISTAS = [('previa_1_sofa', (2.05, 3.45, 1.05), (0.55, 1.95, 0.55), 58, 'Sofá: vista 3/4 desde la cocina'),
          ('previa_2_obra_de_arte', (2.15, 2.10, 1.20), (0.0, 2.10, 1.12), 80, 'Obra de arte y sofá: vista frontal del muro oeste'),
          ('previa_3_mueble_tv', (0.95, 3.30, 1.20), (2.60, 1.85, 0.85), 62, 'Mueble del TV: vista 3/4')]
os.makedirs(PREV, exist_ok=True)
for nombre, desde, hacia, fov, desc in VISTAS:
    sc.camera = camara('CAM_' + nombre, desde, hacia, fov)
    t0 = time.time(); bpy.ops.render.render(write_still=False); dt = round(time.time() - t0, 1)
    # exposición solo de vista para mediana 0,48–0,54 (misma curva AgX y balance de la escena)
    e = 2.1
    for _ in range(0):
        vs_.exposure = e; p = '/tmp/ora_prev.png'; bpy.data.images['Render Result'].save_render(p, scene=sc)
        im = bpy.data.images.load(p, check_existing=False); px = np.array(im.pixels[:], np.float32).reshape(-1, 4)[:, :3]; bpy.data.images.remove(im)
        med = float(np.median(px @ np.array([0.2126, 0.7152, 0.0722], np.float32)))
        if med < 0.48: e += 0.1
        elif med > 0.54: e -= 0.1
        else: break
    vs_.exposure = e; med = -1
    salida = os.path.join(PREV, nombre + '.png'); bpy.data.images['Render Result'].save_render(salida, scene=sc)
    reg['previas'].append({'archivo': salida, 'descripcion': desc, 'segundos': dt, 'exposicion': round(e, 2), 'mediana': round(med, 3)})
    print('[sala] PREVIA', nombre, dt, 's · exposición', round(e, 2))
vs_.exposure = 1.9
json.dump(reg, open(os.path.join(PREV, 'rediseno_sala.json'), 'w'), indent=1, ensure_ascii=False)
print('[sala] ELIMINADO', reg['eliminado']); print('[sala] CREADO', len(reg['creado']), 'objetos'); print('SALA_OK')
