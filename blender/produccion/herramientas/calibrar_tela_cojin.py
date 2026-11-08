# Calibración de la simulación de tela sobre UN cojín (no guarda nada). Mide volumen conservado, hundimiento y arrugas.
import bpy, bmesh, sys, time, json
from mathutils import Vector
sc = bpy.context.scene
def preparar(o, cortes):
    for m in list(o.modifiers): o.modifiers.remove(m)
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cortes, use_grid_fill=True)
    bm.to_mesh(o.data); bm.free()
def volumen(me):
    bm = bmesh.new(); bm.from_mesh(me); v = bm.calc_volume(); bm.free(); return abs(v)
def simular(o, colis, pres, masa, frames=45, ten=15, resortes=False):
    for c in colis:
        if not any(m.type == 'COLLISION' for m in c.modifiers):
            cm = c.modifiers.new('col', 'COLLISION'); c.collision.thickness_outer = 0.003
    cl = o.modifiers.new('tela', 'CLOTH'); s = cl.settings
    s.quality = 8; s.mass = masa; s.air_damping = 2; s.tension_stiffness = ten; s.compression_stiffness = ten; s.shear_stiffness = 8; s.bending_stiffness = 1.5
    s.use_pressure = pres > 0; s.uniform_pressure_force = pres; s.shrink_min = 0.012
    if resortes: s.use_internal_springs = True; s.internal_spring_max_length = 0.25; s.internal_tension_stiffness = 15; s.internal_compression_stiffness = 15
    cs = cl.collision_settings; cs.distance_min = 0.003; cs.use_self_collision = True; cs.self_distance_min = 0.003
    cl.point_cache.frame_start = 1; cl.point_cache.frame_end = frames
    v0 = volumen(o.data); zmin0 = min((o.matrix_world @ v.co).z for v in o.data.vertices)
    t = time.time()
    for f in range(1, frames + 1): sc.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get(); me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    v1 = volumen(me); zs = [(o.matrix_world @ v.co).z for v in me.vertices]
    desp = max((a.co - b.co).length for a, b in zip(o.data.vertices, me.vertices))
    r = {'tension': ten, 'resortes': resortes, 'presion': pres, 'masa': masa, 'vol_ratio': round(v1 / v0, 3), 'zmin_antes': round(zmin0, 3), 'zmin_despues': round(min(zs), 3), 'desp_max_m': round(desp, 3), 'seg': round(time.time() - t, 1), 'verts': len(me.vertices)}
    o.modifiers.remove(cl); sc.frame_set(1); return r, me
base = sc.objects['SOFA_base']; concha = sc.objects['SOFA_concha_respaldo_brazos']
asiento = sc.objects['SOFA_asiento_continuo']
preparar(asiento, 2); asiento.location.z += 0.06
orig = asiento.data.copy()
for pres, masa, ten, res in ((1.0, 0.002, 80, False), (0.5, 0.002, 200, False), (0.0, 0.002, 80, True), (0.5, 0.002, 80, True)):
    asiento.data = orig.copy()
    r, me = simular(asiento, [base], pres, masa, frames=30, ten=ten, resortes=res)
    print('TELA', json.dumps(r))
