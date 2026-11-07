"""Paquete autónomo de la escena para el piloto de Gaussian Splatting en una GPU en la nube.

Abre el .blend del render V3 en un proceso de Blender en segundo plano (solo lectura), le aplica el piloto V5
(blender/scripts/piloto_v5.py: biseles y decoración CC0, la misma geometría que ve la V5), empaqueta dentro del
archivo todas las texturas y modelos externos y guarda una COPIA (save_as_mainfile copy=True) en el paquete.
El .blend de entrada NO se guarda ni se modifica (el script de preparación compara su hash antes y después).

    Blender -b blender/Apartamento_102_Render_V3.blend --python blender/scripts/empaquetar_splat.py -- \
        blender/scripts/apto-102.json <carpeta_paquete>

Salida en <carpeta_paquete>/escena/:
  escena_splat.blend      copia autónoma (texturas empaquetadas), con el piloto aplicado
  puntos_iniciales.txt    nube de puntos muestreada de las superficies (x y z r g b, ejes de Blender) para
                          inicializar las gaussianas (equivale a la nube «SfM» que se obtendría con COLMAP)
  escena.json             resumen: objetos, imágenes empaquetadas, faltantes, piloto, versión de Blender
"""
import bpy, sys, os, json
import numpy as np

argv = sys.argv[sys.argv.index('--') + 1:]
CFG_PATH, DEST = argv[0], os.path.abspath(os.path.join(argv[1], 'escena'))
os.makedirs(DEST, exist_ok=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(CFG_PATH))
ROOT = os.path.abspath(os.path.join(os.path.dirname(CFG_PATH), '..', '..'))
EXCLUIR = tuple(CFG.get('lightmaps', {}).get('excluir_prefijos', ['ARQ_Piso', 'ARQ_Cielo', 'ILU_Cielo_detalles']))
N_PUNTOS = int(CFG['splat'].get('puntos_iniciales', 250000))

sc = bpy.data.scenes[CFG['escena']]
if bpy.context.window: bpy.context.window.scene = sc
col = bpy.data.collections[f"APTO_{CFG['apartamento']}_Modelo"]

# --- 1) piloto V5 (mismo criterio que hornear_lightmaps_web.py --piloto)
import piloto_v5
objs = [o for o in col.all_objects if o.type == 'MESH' and not o.name.startswith(EXCLUIR) and o.data.polygons
        and not any(c.name.startswith('Variante_') for c in o.users_collection)]
cfgp = dict(CFG['piloto']); cfgp['fusionar'] = [o.name for o in objs]
raiz = next((o for o in col.objects if o.parent is None and o.type == 'EMPTY'), None)
nuevos, res = piloto_v5.aplicar(cfgp, ROOT, col, raiz)
print(f"[paquete] piloto: {len(res['biselados'])} biseladas, {len(res['reemplazos'])} cerámicas, {len(res['utileria'])} utilería")

# --- 2) nube de puntos inicial: superficies visibles en render cerca del espacio social (área ponderada)
ox, oy = CFG['origen_plano']
geo = json.load(open(os.path.join(ROOT, 'apartamento-102', 'data', 'propuesta-102.json')))
rects = [r for e in geo['espacios'] if e['id'] in CFG['splat'].get('espacios', ['social']) for r in e['piso_rectangulos']]
M = 1.2   # margen: muros, ventanas y lo que se ve a través de los vanos cercanos
x0 = min(r[0] for r in rects) - ox - M; x1 = max(r[2] for r in rects) - ox + M
y0 = min(r[1] for r in rects) - oy - M; y1 = max(r[3] for r in rects) - oy + M
dg = bpy.context.evaluated_depsgraph_get()
tris, cols = [], []


def color_material(m):
    if not m: return (0.6, 0.6, 0.6)
    try:
        bsdf = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        c = bsdf.inputs['Base Color']
        if c.is_linked:
            img = next((n.image for n in m.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image and n.image.size[0]), None)
            if img:
                a = np.array(img.pixels[:min(len(img.pixels), 4 * 65536)], np.float32).reshape(-1, 4)
                return tuple(a[:, :3].mean(0))
            return (0.6, 0.6, 0.6)
        return tuple(c.default_value[:3])
    except Exception:
        return tuple(m.diffuse_color[:3])


for o in sc.objects:
    if o.type != 'MESH' or o.hide_render or not o.visible_get(): continue
    oe = o.evaluated_get(dg); me = oe.to_mesh()
    me.calc_loop_triangles()
    if not me.loop_triangles: oe.to_mesh_clear(); continue
    mw = np.array(o.matrix_world, np.float64)
    v = np.empty(len(me.vertices) * 3, np.float64); me.vertices.foreach_get('co', v); v = v.reshape(-1, 3)
    v = v @ mw[:3, :3].T + mw[:3, 3]
    t = np.empty(len(me.loop_triangles) * 3, np.int64); me.loop_triangles.foreach_get('vertices', t); t = t.reshape(-1, 3)
    mi = np.empty(len(me.loop_triangles), np.int64); me.loop_triangles.foreach_get('material_index', mi)
    P = v[t]; c = P.mean(1)
    dentro = (c[:, 0] > x0) & (c[:, 0] < x1) & (c[:, 1] > y0) & (c[:, 1] < y1) & (c[:, 2] > -0.2) & (c[:, 2] < 3.2)
    if dentro.any():
        paleta = np.array([color_material(s.material) for s in o.material_slots] or [(0.6, 0.6, 0.6)], np.float32)
        tris.append(P[dentro]); cols.append(paleta[np.clip(mi[dentro], 0, len(paleta) - 1)])
    oe.to_mesh_clear()
T = np.concatenate(tris); C = np.concatenate(cols)
area = 0.5 * np.linalg.norm(np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]), axis=1)
rng = np.random.default_rng(102)
k = rng.choice(len(T), N_PUNTOS, p=area / area.sum())
u, w = rng.random(N_PUNTOS), rng.random(N_PUNTOS); f = u + w > 1; u[f], w[f] = 1 - u[f], 1 - w[f]
pts = T[k, 0] + u[:, None] * (T[k, 1] - T[k, 0]) + w[:, None] * (T[k, 2] - T[k, 0])
rgb = np.clip(C[k] ** (1 / 2.2) * 255, 0, 255).astype(np.uint8)   # lineal → sRGB aproximado
with open(os.path.join(DEST, 'puntos_iniciales.txt'), 'w') as fh:
    for p, c in zip(pts, rgb): fh.write(f'{p[0]:.5f} {p[1]:.5f} {p[2]:.5f} {c[0]} {c[1]} {c[2]}\n')
print(f'[paquete] {N_PUNTOS} puntos iniciales de {len(T)} triángulos ({area.sum():.1f} m²)')

# --- 3) empaquetar recursos externos y guardar una COPIA autónoma
bpy.ops.file.make_paths_absolute()
try:
    bpy.ops.file.pack_all()
except RuntimeError as e:
    print('[paquete] aviso pack_all:', e)
faltan = [i.name for i in bpy.data.images if i.source == 'FILE' and not i.packed_file and i.users]
ruta = os.path.join(DEST, 'escena_splat.blend')
bpy.ops.wm.save_as_mainfile(filepath=ruta, copy=True, compress=True)
json.dump({'blender': bpy.app.version_string, 'escena': sc.name, 'piloto': res,
           'imagenes_empaquetadas': sorted(i.name for i in bpy.data.images if i.packed_file),
           'imagenes_faltantes': faltan, 'objetos_render': sum(1 for o in sc.objects if o.type == 'MESH' and not o.hide_render),
           'puntos_iniciales': N_PUNTOS, 'caja_puntos_blender': [x0, y0, x1, y1],
           'nota': 'Copia autónoma para la nube; el .blend de origen no se guardó.'},
          open(os.path.join(DEST, 'escena.json'), 'w'), indent=1, ensure_ascii=False, default=str)
print(f'[paquete] copia guardada: {ruta} ({os.path.getsize(ruta) / 1e6:.1f} MB); imágenes faltantes: {faltan}')
