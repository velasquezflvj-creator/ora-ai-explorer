import bpy, bmesh
from mathutils import Vector
sc = bpy.context.scene
def bb(o):
    v = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return [round(min(p[i] for p in v), 2) for i in range(3)] + [round(max(p[i] for p in v), 2) for i in range(3)]
X0, X1, Y0, Y1 = -4.0, -0.4, -3.7, 3.7   # zona social (Blender)
for o in sc.objects:
    if o.type not in ('MESH', 'EMPTY', 'CURVE') or o.hide_render: continue
    b = bb(o)
    if b[3] < X0 or b[0] > X1 or b[1] > -0.2 and b[4] > 3.7: pass
    if b[0] < -0.4 and not o.name.startswith(('ARQ', 'CTX', 'ILU_Cielo', 'ILU_Guarda')):
        print('OBJ', o.name, o.type, 'bb', b, 'padre', o.parent.name if o.parent else None, 'mats', [s.material.name for s in o.material_slots if s.material][:8], 'caras', len(o.data.polygons) if o.type == 'MESH' else '-', 'mods', [m.type for m in o.modifiers])
# partes de MOB_Sala por material (piezas sueltas)
o = sc.objects['MOB_Sala']; bm = bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table()
vis = set(); M = o.matrix_world
for f in bm.faces:
    if f.index in vis: continue
    pila = [f]; grupo = []
    while pila:
        g = pila.pop()
        if g.index in vis: continue
        vis.add(g.index); grupo.append(g)
        for e in g.edges:
            for h in e.link_faces:
                if h.index not in vis: pila.append(h)
    vs = [M @ v.co for g in grupo for v in g.verts]; mats = sorted({o.material_slots[g.material_index].material.name for g in grupo})
    print('PIEZA MOB_Sala', mats, 'caras', len(grupo), 'bb', [round(min(p[i] for p in vs), 2) for i in range(3)] + [round(max(p[i] for p in vs), 2) for i in range(3)])
