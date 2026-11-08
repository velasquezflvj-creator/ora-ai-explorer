# Huella de solo lectura de dos .blend: abre cada uno (sin guardar nunca) y compara datos relevantes.
import bpy, sys, json, hashlib, os

def h(x): return hashlib.sha256(repr(x).encode()).hexdigest()[:12]
def r(v, n=5): return tuple(round(float(a), n) for a in v)

def sock_val(s):
    v = getattr(s, 'default_value', None)
    if v is None: return None
    try: return r(v, 4)
    except TypeError:
        try: return round(float(v), 4)
        except Exception: return str(v)

def arbol(nt):
    if not nt: return None
    nodos = {}
    for n in nt.nodes:
        props = {}
        for p in n.bl_rna.properties:
            if p.identifier in ('rna_type','location','width','height','dimensions','select','name','label','location_absolute','warning_propagation','color_tag'): continue
            if p.type in ('POINTER','COLLECTION'):
                if p.identifier in ('image','node_tree','object'):
                    o = getattr(n, p.identifier, None); props[p.identifier] = o.name if o else None
                continue
            try: props[p.identifier] = repr(getattr(n, p.identifier))
            except Exception: pass
        nodos[n.name] = (n.bl_idname, props, [(s.identifier, sock_val(s)) for s in n.inputs if not s.is_linked])
    enl = sorted((l.from_node.name, l.from_socket.identifier, l.to_node.name, l.to_socket.identifier) for l in nt.links)
    return {'nodos': nodos, 'enlaces': enl}

def huella():
    d = {'objetos': {}, 'mallas': {}, 'materiales': {}, 'imagenes': {}, 'camaras': {}, 'luces': {}, 'mundo': {}, 'escena': {}, 'colecciones': {}}
    dg = bpy.context.evaluated_depsgraph_get()
    for o in bpy.data.objects:
        e = o.evaluated_get(dg) if o.name in bpy.context.scene.objects else o
        d['objetos'][o.name] = {
            'tipo': o.type, 'datos': o.data.name if o.data else None,
            'matriz': h([r(f, 4) for f in o.matrix_world]),
            'matriz_val': [r(f, 4) for f in o.matrix_world],
            'oculto_render': o.hide_render, 'oculto_vista': o.hide_viewport,
            'en_escena': o.name in bpy.context.scene.objects,
            'colecciones': sorted(c.name for c in o.users_collection),
            'materiales': [s.material.name if s.material else None for s in o.material_slots],
            'modificadores': [(m.type, m.name, m.show_render) for m in o.modifiers],
            'padre': o.parent.name if o.parent else None,
            'visible_camara': getattr(o, 'visible_camera', None),
        }
        if o.type == 'MESH':
            m = e.data
            vs = [r(v.co, 4) for v in m.vertices]
            uv = None
            if m.uv_layers.active: uv = h([r(l.uv, 4) for l in m.uv_layers.active.data])
            d['mallas'][o.name] = {'v': len(m.vertices), 'c': len(m.polygons), 'geo': h(vs), 'caras': h([tuple(p.vertices) for p in m.polygons]), 'uv': uv,
                                   'mat_idx': h([p.material_index for p in m.polygons])}
    for m in bpy.data.materials:
        d['materiales'][m.name] = {'usuarios': m.users, 'nodos': h(arbol(m.node_tree)), 'arbol': arbol(m.node_tree)}
    for i in bpy.data.images:
        ruta = bpy.path.abspath(i.filepath) if i.filepath else ''
        st = os.stat(ruta) if ruta and os.path.exists(ruta) else None
        d['imagenes'][i.name] = {'ruta': i.filepath, 'empaquetada': bool(i.packed_file), 'tam': tuple(i.size), 'espacio': i.colorspace_settings.name,
                                 'archivo_mtime': st.st_mtime if st else None, 'archivo_bytes': st.st_size if st else None, 'usuarios': i.users}
    for c in bpy.data.cameras:
        d['camaras'][c.name] = {'lente': round(c.lens, 4), 'sensor': round(c.sensor_width, 4), 'tipo': c.type, 'shift': (round(c.shift_x, 4), round(c.shift_y, 4)), 'clip': (c.clip_start, c.clip_end)}
    for l in bpy.data.lights:
        d['luces'][l.name] = {'tipo': l.type, 'energia': round(l.energy, 4), 'color': r(l.color, 4), 'tam': round(getattr(l, 'size', 0), 4), 'nodos': h(arbol(l.node_tree))}
    for w in bpy.data.worlds:
        d['mundo'][w.name] = {'nodos': h(arbol(w.node_tree)), 'arbol': arbol(w.node_tree)}
    s = bpy.context.scene
    d['escena'] = {'nombre': s.name, 'camara': s.camera.name if s.camera else None, 'motor': s.render.engine,
                   'res': (s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage),
                   'muestras': getattr(s.cycles, 'samples', None), 'vista': s.view_settings.view_transform, 'look': s.view_settings.look,
                   'exposicion': round(s.view_settings.exposure, 4), 'frame': s.frame_current, 'escenas': [x.name for x in bpy.data.scenes]}
    for c in bpy.data.collections:
        d['colecciones'][c.name] = {'objetos': sorted(o.name for o in c.objects), 'excl_render': c.hide_render, 'hijos': sorted(x.name for x in c.children)}
    d['conteos'] = {k: len(getattr(bpy.data, k)) for k in ('objects','meshes','materials','images','node_groups','cameras','lights','worlds','texts','actions')}
    d['textos'] = {t.name: h(t.as_string()) for t in bpy.data.texts}
    d['grupos_nodos'] = {g.name: h(arbol(g)) for g in bpy.data.node_groups}
    return d

a, b, salida = sys.argv[sys.argv.index('--') + 1:]
res = {}
for etiqueta, ruta in (('empaquetada', a), ('actual', b)):
    bpy.ops.wm.open_mainfile(filepath=ruta, load_ui=False)
    res[etiqueta] = huella()
json.dump(res, open(salida, 'w'), indent=1, default=str)
print('HUELLA_OK', salida)
