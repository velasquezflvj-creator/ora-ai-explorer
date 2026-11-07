"""Piloto V5 (sala, comedor y cocina del apartamento 102): mejoras de geometría y decoración sobre una COPIA del modelo.

Se aplica igual en los dos procesos de hornear_lightmaps_web.py (hornear sobre el V3 en memoria; exportar sobre una
importación limpia del GLB original), para que ambas copias tengan exactamente la misma geometría y orden de bucles.
No modifica muros, puertas, ventanas ni la distribución: solo
  1. fusiona vértices coincidentes (la importación deja cada cara suelta) y marca como vivas las aristas de más de 30°
     — misma forma y mismo sombreado plano; permite desplegar las UV de luz en islas grandes y biselar;
  2. bisela (4–6 mm) muebles, cocina, marcos y puerta de la zona piloto: los bordes atrapan la luz como en la realidad;
  3. reemplaza las cerámicas decorativas procedurales por jarrones CC0 de Poly Haven del mismo alto, en el mismo sitio;
  4. añade utilería CC0 (tabla de cortar, peras) rotulada como decoración ilustrativa.
Todo lo añadido lleva extras: categoria «ilustrativo», verificado false y su fuente.
"""
import bpy, bmesh, math, os
from mathutils import Vector


def _malla(o):
    return o is not None and o.type == 'MESH'


def fusionar_y_aristas(o, angulo=30.0):
    me = o.data
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bm.to_mesh(me); bm.free()
    if hasattr(me, 'set_sharp_from_angle'): me.set_sharp_from_angle(angle=math.radians(angulo))
    for p in me.polygons: p.use_smooth = True


def biselar(o, ancho, segmentos=2, angulo=30.0):
    m = o.modifiers.new('_bisel', 'BEVEL')
    m.width = ancho; m.segments = segmentos; m.limit_method = 'ANGLE'; m.angle_limit = math.radians(angulo)
    m.use_clamp_overlap = True; m.harden_normals = True; m.miter_outer = 'MITER_ARC'
    with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o]):
        bpy.ops.object.modifier_apply(modifier=m.name)


def piezas_por_material(o, material, alto_min):
    """Piezas sueltas (componentes conexos) cuyas caras son todas del material indicado."""
    me = o.data; idx = [i for i, s in enumerate(o.material_slots) if s.material and s.material.name.split('.')[0] == material]
    if not idx: return []
    bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
    vistos, piezas = set(), []
    for f in bm.faces:
        if f.index in vistos or f.material_index not in idx: continue
        pila, comp = [f], []
        while pila:
            g = pila.pop()
            if g.index in vistos: continue
            vistos.add(g.index); comp.append(g.index)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in vistos and h.material_index in idx: pila.append(h)
        pts = [o.matrix_world @ bm.faces[i].verts[k].co for i in comp for k in range(len(bm.faces[i].verts))]
        mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
        mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
        if mx.z - mn.z >= alto_min: piezas.append({'caras': comp, 'min': mn, 'max': mx})
    bm.free()
    return piezas


def borrar_caras(o, indices):
    bm = bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.faces[i] for i in sorted(set(indices))], context='FACES_ONLY')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(o.data); bm.free()


def importar_modelo(ruta, nombre, coleccion):
    antes = set(bpy.data.objects)
    with bpy.context.temp_override(collection=coleccion):
        bpy.ops.import_scene.gltf(filepath=ruta, import_shading='NORMALS')
    nuevos = [o for o in bpy.data.objects if o not in antes]
    mallas = [o for o in nuevos if o.type == 'MESH']
    for o in mallas:   # transformaciones aplicadas a la malla (el objeto final queda con identidad)
        mw = o.matrix_world.copy(); o.parent = None; o.data.transform(mw); o.matrix_world.identity()
    if len(mallas) > 1:
        with bpy.context.temp_override(active_object=mallas[0], selected_editable_objects=mallas, selected_objects=mallas, object=mallas[0]):
            bpy.ops.object.join()
    obj = mallas[0]
    for o in nuevos:   # vacíos de la jerarquía importada (las mallas unidas ya las eliminó Blender)
        try:
            if o != obj and o.name in bpy.data.objects: bpy.data.objects.remove(o)
        except ReferenceError:
            pass
    obj.name = nombre; obj.data.name = nombre
    for c in list(obj.users_collection):
        if c != coleccion: c.objects.unlink(obj)
    if obj.name not in coleccion.objects: coleccion.objects.link(obj)
    return obj


def colocar(obj, base, alto=None, ancho=None, giro=0.0):
    """Escala uniforme al alto (o ancho) pedido y apoya la base del objeto en «base» (centro inferior)."""
    pts = [Vector(c) for c in obj.bound_box]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))); mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    dim = mx - mn
    k = (alto / dim.z) if alto else (ancho / max(dim.x, dim.y))
    centro = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
    obj.data.transform(__import__('mathutils').Matrix.Translation(-centro))
    obj.scale = (k, k, k); obj.rotation_euler = (0, 0, giro); obj.location = base


def aplicar(cfg, root, coleccion, raiz_modelo=None, solo_geometria=False):
    """cfg: sección «piloto» de apto-NNN.json. Devuelve la lista de objetos añadidos y un resumen."""
    P = cfg; R = lambda p: p if os.path.isabs(p) else os.path.join(root, p)
    res = {'fusionados': [], 'biselados': [], 'reemplazos': [], 'utileria': []}
    # 1) fusión de vértices y aristas vivas (todas las mallas fijas indicadas; misma forma)
    for n in P.get('fusionar', []):
        o = bpy.data.objects.get(n)
        if _malla(o): fusionar_y_aristas(o); res['fusionados'].append(n)
    # 2) reemplazo de cerámicas (antes del bisel, para no biselar lo que se va a quitar)
    nuevos = []
    reemp = P.get('ceramicas', {}); modelos = reemp.get('modelos', [])
    k = 0
    for n in reemp.get('objetos', []):
        o = bpy.data.objects.get(n)
        if not _malla(o): continue
        piezas = piezas_por_material(o, 'ceramica_deco', reemp.get('alto_min', 0.1))
        if not piezas: continue
        borrar_caras(o, [i for p in piezas for i in p['caras']])
        for p in piezas:
            m = modelos[k % len(modelos)]; k += 1
            dec = importar_modelo(R(m['gltf']), f"DEC_{m['id']}_{k:02d}", coleccion)
            alto = (p['max'].z - p['min'].z) * reemp.get('escala_alto', 1.0)
            colocar(dec, Vector(((p['min'].x + p['max'].x) / 2, (p['min'].y + p['max'].y) / 2, p['min'].z)), alto=alto, giro=k * 1.37)
            nuevos.append((dec, m)); res['reemplazos'].append({'en': n, 'modelo': m['id'], 'alto_m': round(alto, 3)})
    # 3) biseles
    for b in P.get('biseles', []):
        for n in b['objetos']:
            o = bpy.data.objects.get(n)
            if _malla(o): biselar(o, b['ancho_m'], b.get('segmentos', 2)); res['biselados'].append(n)
    # 4) utilería
    for u in P.get('utileria', []):
        dec = importar_modelo(R(u['gltf']), f"DEC_{u['id']}", coleccion)
        colocar(dec, Vector(u['base_blender']), alto=u.get('alto_m'), ancho=u.get('ancho_m'), giro=math.radians(u.get('giro_grados', 0)))
        if u.get('inclinacion_grados'): dec.rotation_euler.x = math.radians(u['inclinacion_grados'])
        nuevos.append((dec, u)); res['utileria'].append(u['id'])
    for dec, m in nuevos:
        if raiz_modelo is not None:
            mw = dec.matrix_world.copy(); dec.parent = raiz_modelo; dec.matrix_parent_inverse = raiz_modelo.matrix_world.inverted()
        dec['verificado'] = False; dec['categoria'] = 'ilustrativo'; dec['grupo'] = 'mobiliario'
        dec['fuente'] = f"Decoración ilustrativa: {m.get('nombre', m['id'])} (Poly Haven, CC0)"
    return [d for d, _ in nuevos], res
