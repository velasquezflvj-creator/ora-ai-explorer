import bpy, math, json
from mathutils import Vector, Euler
sc = bpy.context.scene; dg = bpy.context.evaluated_depsgraph_get(); cam = sc.camera
sol = sc.objects['Sol_HDRI']
dsol = (sol.rotation_euler.to_matrix() @ Vector((0, 0, -1))).normalized()
print('SOL dir_luz', [round(v, 3) for v in dsol], 'elev', round(math.degrees(math.asin(-dsol.z)), 1), 'az_prop', round(math.degrees(math.atan2(dsol.y, dsol.x)), 1), 'parent', sol.parent, 'constraints', [c.type for c in sol.constraints], 'mw', [round(v,2) for v in sol.matrix_world.col[2][:3]])
def mat_de(o, i):
    try: return o.material_slots[o.data.polygons[i].material_index].material.name
    except Exception: return '?'
W, H = 96, 54; fr = cam.data.view_frame(scene=sc); tl, tr, br, bl = [cam.matrix_world @ v for v in (fr[0], fr[3], fr[2], fr[1])]
o = cam.matrix_world.translation; pts = []
for j in range(H):
    for i in range(W):
        p = tl + (tr - tl) * ((i + .5) / W) + (bl - tl) * ((j + .5) / H); ok, loc, nor, idx, ob, _ = sc.ray_cast(dg, o, (p - o).normalized())
        if ok: pts.append((loc, nor, ob.name, mat_de(ob, idx)))
def traza(loc, nor, dl):
    hacia = -dl
    if nor.dot(hacia) <= 0: return None
    p = loc + nor * 1e-3; cruces = []
    for _ in range(12):
        ok, l2, n2, idx, ob, _ = sc.ray_cast(dg, p, hacia)
        if not ok: return {'cruces': cruces, 'sale': [round(v, 2) for v in p], 'cielo': True}
        m = mat_de(ob, idx)
        if 'vidrio' in m: cruces.append((ob.name, m, [round(v, 2) for v in l2])); p = l2 + hacia * 1e-3; continue
        return None
APERTURA = (-3.89, -1.44, 0.0, 2.1)   # vano puerta-ventana de la sala (x, z) en la fachada y = -3.65
filas = []
for elev in (16, 18, 20, 22, 24, 26, 28, 30):
    for az in range(70, 136, 5):
        a, e = math.radians(az), math.radians(elev); dl = Vector((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), -math.sin(e)))
        res = [(m, traza(l, n, dl)) for l, n, on, m in pts]; res = [(m, t) for m, t in res if t]
        fuera = 0
        for m, t in res:
            p = Vector(t['sale']); h = -dl; k = (-3.65 - p.y) / h.y if abs(h.y) > 1e-6 else -1
            q = p + h * k if k > 0 else None
            if not q or not (APERTURA[0] <= q.x <= APERTURA[1] and APERTURA[2] <= q.z <= APERTURA[3]): fuera += 1
        mats = {}
        for m, t in res: mats[m] = mats.get(m, 0) + 1
        n = len(res); sofa = mats.get('mueble_tela_sofa', 0); piso = mats.get('piso_madera', 0)
        filas.append((elev, az, n, round(100 * n / len(pts), 2), fuera, piso, sofa, mats))
for f in sorted(filas, key=lambda f: (-(f[5] - 2 * f[6]) if f[4] == 0 else 1e9))[:14]: print('CAND elev', f[0], 'az', f[1], 'puntos', f[2], f'{f[3]} %', 'fuera_de_vano', f[4], 'piso', f[5], 'sofa', f[6], f[7])
