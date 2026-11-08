import bpy, os, json
r = {'imagenes': 0, 'empaquetadas': 0, 'generadas': 0, 'externas_ok': [], 'faltantes': [], 'librerias': [p.filepath for p in bpy.data.libraries],
     'otros_externos': [f.filepath for f in bpy.data.fonts if f.filepath and not f.packed_file and f.filepath != '<builtin>'] + [s.filepath for s in bpy.data.sounds if not s.packed_file]}
for im in bpy.data.images:
    if im.source in ('VIEWER', 'GENERATED') or im.type in ('RENDER_RESULT', 'COMPOSITING'): r['generadas'] += 1; continue
    r['imagenes'] += 1
    if im.packed_file: r['empaquetadas'] += 1
    else:
        p = bpy.path.abspath(im.filepath)
        (r['externas_ok'] if os.path.exists(p) else r['faltantes']).append(im.filepath)
print('DEPS' + json.dumps(r))
