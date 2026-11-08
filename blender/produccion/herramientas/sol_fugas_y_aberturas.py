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
for elev, az in ((10.4, 144.0), (20, 90), (20, 120), (28, 105), (35, 100)):
    a, e = math.radians(az), math.radians(elev); dl = Vector((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), -math.sin(e)))
    if elev == 10.4: dl = dsol
    res = [(m, traza(l, n, dl)) for l, n, on, m in pts]; res = [(m, t) for m, t in res if t]
    # punto de salida: intersección con el plano de fachada y = -3.65 (dónde cruza la fachada) para rayos sin vidrio
    sal = {}
    for m, t in res:
        if t['cruces']: continue
        # reconstruir la salida exacta: último punto + dirección hasta y=-3.65
        p = Vector(t['sale']); h = -dl
        if abs(h.y) > 1e-6:
            k = (-3.65 - p.y) / h.y
            q = p + h * k if k > 0 else None
        else: q = None
        clave = f'fachada x={q.x:.1f} z={q.z:.1f}' if q else f'sin cruzar fachada, sale por {t["sale"]}'
        sal[clave] = sal.get(clave, 0) + 1
    con_vidrio = sum(1 for m, t in res if t['cruces']); sin_vidrio = len(res) - con_vidrio
    mats = {}
    for m, t in res: mats[m] = mats.get(m, 0) + 1
    print(f'DIR elev {elev} az {az}: puntos al sol {len(res)} (con vidrio {con_vidrio}, sin vidrio {sin_vidrio}) materiales {mats}')
    for k, v in sorted(sal.items(), key=lambda x: -x[1])[:8]: print('    salida', k, v)
# objetos en la fachada y = -3.65
for ob in sc.objects:
    if ob.type == 'MESH' and not ob.hide_render:
        bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]; ys = [v.y for v in bb]
        if min(ys) < -3.3: print('FACHADA', ob.name, 'x', round(min(v.x for v in bb), 2), round(max(v.x for v in bb), 2), 'y', round(min(ys), 2), round(max(ys), 2), 'z', round(min(v.z for v in bb), 2), round(max(v.z for v in bb), 2), [s.material.name for s in ob.material_slots if s.material][:6])
