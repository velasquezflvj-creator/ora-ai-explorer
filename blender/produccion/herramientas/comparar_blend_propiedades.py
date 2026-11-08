# Comparación ampliada (solo lectura): todas las propiedades RNA simples de escena/render/cycles/vista/capas, propiedades
# personalizadas, selección, objeto activo, y propiedades de objetos/mallas/materiales/imágenes. Nunca guarda.
import bpy, sys, json

def simples(idb, prof=0, vistos=None):
    out = {}
    if idb is None or prof > 2: return out
    for p in idb.bl_rna.properties:
        k = p.identifier
        if k in ('rna_type', 'pixels', 'bindcode', 'preview'): continue
        try: v = getattr(idb, k)
        except Exception: continue
        if p.type == 'POINTER':
            if v is not None and hasattr(v, 'bl_rna') and not isinstance(v, bpy.types.ID) and prof < 2:
                out[k] = simples(v, prof + 1)
            elif isinstance(v, bpy.types.ID): out[k] = v.name
            continue
        if p.type == 'COLLECTION': continue
        try:
            if hasattr(v, '__len__') and not isinstance(v, str): v = [round(x, 5) if isinstance(x, float) else x for x in v]
            elif isinstance(v, float): v = round(v, 5)
            out[k] = v if isinstance(v, (int, float, str, bool, list, type(None))) else repr(v)
        except Exception: out[k] = repr(v)
    return out

def huella():
    s = bpy.context.scene; vl = bpy.context.view_layer
    d = {'escena': simples(s), 'render': simples(s.render), 'cycles': simples(s.cycles), 'vista': simples(s.view_settings),
         'pantalla': simples(s.display_settings), 'eevee': simples(s.eevee), 'capa': simples(vl),
         'capas': [x.name for x in s.view_layers],
         'activo': vl.objects.active.name if vl.objects.active else None,
         'seleccion': sorted(o.name for o in s.objects if o.select_get()),
         'props_escena': {k: repr(s[k]) for k in s.keys()},
         'objetos': {o.name: {'p': simples(o), 'custom': {k: repr(o[k]) for k in o.keys()}} for o in bpy.data.objects},
         'mallas': {m.name: {'custom': {k: repr(m[k]) for k in m.keys()}, 'auto': m.name} for m in bpy.data.meshes},
         'materiales': {m.name: simples(m) for m in bpy.data.materials},
         'imagenes': {i.name: simples(i) for i in bpy.data.images},
         'luces': {l.name: simples(l) for l in bpy.data.lights},
         'camaras': {c.name: simples(c) for c in bpy.data.cameras},
         'mundos': {w.name: simples(w) for w in bpy.data.worlds}}
    for o in d['objetos'].values():
        for k in ('select', 'is_evaluated', 'session_uid', 'original'): o['p'].pop(k, None)
    return d

args = sys.argv[sys.argv.index('--') + 1:]
salida = args[-1]; res = {}
for ruta in args[:-1]:
    bpy.ops.wm.open_mainfile(filepath=ruta, load_ui=False)
    res[ruta.split('/')[-1]] = huella()
json.dump(res, open(salida, 'w'), indent=1, default=str)
print('EXTRA_OK')
