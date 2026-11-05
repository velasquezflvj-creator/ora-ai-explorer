"""Prepara los muebles de terceros que usa el visor del apartamento 102.

Fuente: Khronos glTF-Sample-Assets (https://github.com/KhronosGroup/glTF-Sample-Assets).
  - GlamVelvetSofa  · CC BY 4.0 · Wayfair LLC  → modelo/muebles/sofa.glb
  - SheenChair      · CC0 1.0   · Wayfair LLC  → modelo/muebles/butaca.glb

Qué hace con cada GLB:
  - fija una variante de tela (KHR_materials_variants) y elimina la extensión;
  - elimina luces y etiquetas del modelo;
  - renombra materiales a nombres estables («mueble_tela_sofa», …) para que el visor los tiña según la propuesta de acabados;
  - reduce las texturas a 1024 px (JPEG para color y relieve) para que el visor siga siendo liviano.

Uso: python3 tools/preparar_muebles.py <carpeta glTF-Sample-Assets/Models> modelo/muebles
"""
import io, json, struct, sys
from pathlib import Path
from PIL import Image

SRC, OUT = Path(sys.argv[1]), Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)

SPEC = {
    'sofa': dict(src='GlamVelvetSofa/glTF-Binary/GlamVelvetSofa.glb', variante='Gray',
                 nombres={'GlamVelvetSofa_legs': 'mueble_metal', 'GlamVelvetSofa_feet': 'mueble_laton', 'GlamVelvetSofa_fabric_gray': 'mueble_tela_sofa'}),
    'butaca': dict(src='SheenChair/glTF-Binary/SheenChair.glb', variante='Peacock Velvet', quitar_nodos=('SheenChair_label',),
                   nombres={'fabric Mystere Peacock Velvet': 'mueble_tela_butaca', 'wood Black': 'mueble_madera', 'metal': 'mueble_metal'}),
}


def leer(path):
    b = path.read_bytes(); n = struct.unpack('<I', b[12:16])[0]
    j = json.loads(b[20:20 + n]); off = 20 + n
    bl = struct.unpack('<I', b[off:off + 4])[0]
    return j, bytearray(b[off + 8:off + 8 + bl])


def escribir(path, j, chunks):
    """chunks: lista de bytes por bufferView (en orden)."""
    buf = bytearray(); views = []
    for v, data in zip(j['bufferViews'], chunks):
        while len(buf) % 4:
            buf += b'\0'
        nv = {k: v[k] for k in v if k not in ('byteOffset', 'byteLength', 'buffer')}
        nv.update(buffer=0, byteOffset=len(buf), byteLength=len(data)); buf += data; views.append(nv)
    while len(buf) % 4:
        buf += b'\0'
    j['bufferViews'] = views; j['buffers'] = [{'byteLength': len(buf)}]
    js = json.dumps(j, separators=(',', ':')).encode()
    while len(js) % 4:
        js += b' '
    out = struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(buf)) + struct.pack('<II', len(js), 0x4E4F534A) + js + struct.pack('<II', len(buf), 0x004E4942) + bytes(buf)
    path.write_bytes(out)


def podar(j, chunks):
    """Elimina materiales, texturas, imágenes y bufferViews que ya no se usan."""
    usados_m = sorted({p['material'] for m in j['meshes'] for p in m['primitives'] if 'material' in p})
    remap_m = {o: i for i, o in enumerate(usados_m)}; j['materials'] = [j['materials'][i] for i in usados_m]
    for m in j['meshes']:
        for p in m['primitives']:
            if 'material' in p:
                p['material'] = remap_m[p['material']]
    def refs(o, f):   # llama f(dict) para cada referencia de textura (claves que terminan en «Texture»)
        if isinstance(o, dict):
            for k, v in o.items():
                if k.endswith('Texture') and isinstance(v, dict) and 'index' in v:
                    f(v)
                refs(v, f)
        elif isinstance(o, list):
            for v in o:
                refs(v, f)
    tex_usadas = set(); refs(j['materials'], lambda r: tex_usadas.add(r['index']))
    usadas_t = sorted(tex_usadas); remap_t = {o: i for i, o in enumerate(usadas_t)}
    def fix(o):
        refs(o, lambda r: r.__setitem__('index', remap_t[r['index']]))
    fix(j['materials']); j['textures'] = [j['textures'][i] for i in usadas_t]
    usadas_i = sorted({t['source'] for t in j['textures']}); remap_i = {o: i for i, o in enumerate(usadas_i)}
    j['images'] = [j['images'][i] for i in usadas_i]
    for t in j['textures']:
        t['source'] = remap_i[t['source']]
    usadas_v = sorted({a['bufferView'] for a in j['accessors'] if 'bufferView' in a} | {im['bufferView'] for im in j['images']})
    remap_v = {o: i for i, o in enumerate(usadas_v)}
    for a in j['accessors']:
        if 'bufferView' in a:
            a['bufferView'] = remap_v[a['bufferView']]
    for im in j['images']:
        im['bufferView'] = remap_v[im['bufferView']]
    j['bufferViews'] = [j['bufferViews'][i] for i in usadas_v]
    return [chunks[i] for i in usadas_v]


for clave, sp in SPEC.items():
    j, bin_ = leer(SRC / sp['src'])
    chunks = [bytes(bin_[v.get('byteOffset', 0):v.get('byteOffset', 0) + v['byteLength']]) for v in j['bufferViews']]
    variantes = [v['name'] for v in j.get('extensions', {}).get('KHR_materials_variants', {}).get('variants', [])]
    vi = variantes.index(sp['variante']) if sp.get('variante') in variantes else None
    for m in j['meshes']:
        for p in m['primitives']:
            ext = p.get('extensions', {}).pop('KHR_materials_variants', None)
            if ext and vi is not None:
                p['material'] = next(mp['material'] for mp in ext['mappings'] if vi in mp['variants'])
            if 'extensions' in p and not p['extensions']:
                del p['extensions']
    # nodos: sin luces ni etiquetas
    quitar = {i for i, n in enumerate(j['nodes']) if 'extensions' in n and 'KHR_lights_punctual' in n['extensions'] or n.get('name') in sp.get('quitar_nodos', ())}
    keep = [i for i in range(len(j['nodes'])) if i not in quitar]; rn = {o: i for i, o in enumerate(keep)}
    j['nodes'] = [j['nodes'][i] for i in keep]
    for n in j['nodes']:
        if 'children' in n:
            n['children'] = [rn[c] for c in n['children'] if c in rn]
    for s in j['scenes']:
        s['nodes'] = [rn[c] for c in s['nodes'] if c in rn]
    usados_mesh = sorted({n['mesh'] for n in j['nodes'] if 'mesh' in n}); rm = {o: i for i, o in enumerate(usados_mesh)}
    j['meshes'] = [j['meshes'][i] for i in usados_mesh]
    for n in j['nodes']:
        if 'mesh' in n:
            n['mesh'] = rm[n['mesh']]
    for k in ('extensions',):
        j.pop(k, None)
    j['extensionsUsed'] = [e for e in j.get('extensionsUsed', []) if e not in ('KHR_materials_variants', 'KHR_lights_punctual')]
    j['extensionsRequired'] = [e for e in j.get('extensionsRequired', []) if e in j['extensionsUsed']] or None
    if j['extensionsRequired'] is None:
        del j['extensionsRequired']
    chunks = podar(j, chunks)
    for mt in j['materials']:
        mt['name'] = sp['nombres'].get(mt.get('name'), mt.get('name'))
    # texturas a 1024 px como JPEG (sin canal alfa)
    for im in j['images']:
        v = im['bufferView']; img = Image.open(io.BytesIO(chunks[v]))
        img.thumbnail((1024, 1024), Image.LANCZOS)
        bio = io.BytesIO(); img.convert('RGB').save(bio, 'JPEG', quality=88); chunks[v] = bio.getvalue(); im['mimeType'] = 'image/jpeg'
    j['asset'] = {**j.get('asset', {}), 'copyright': j.get('asset', {}).get('copyright', 'Wayfair LLC'),
                  'extras': {'origen': 'Khronos glTF-Sample-Assets', 'modelo': sp['src'].split('/')[0], 'licencia': 'CC0 1.0' if clave == 'butaca' else 'CC BY 4.0',
                             'preparado_por': 'tools/preparar_muebles.py (variante fija, texturas 1024 px)'}}
    escribir(OUT / f'{clave}.glb', j, chunks)
    print(clave, (OUT / f'{clave}.glb').stat().st_size // 1024, 'KB', [m['name'] for m in j['materials']])
