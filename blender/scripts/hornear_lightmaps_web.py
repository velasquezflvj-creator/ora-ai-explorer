"""Lightmaps completos para el recorrido web (V4): un atlas de luz para todas las superficies fijas del apartamento.

Dos pasos, cada uno en su propio proceso de Blender en segundo plano (nunca toca la sesión abierta ni guarda los .blend):

  1) hornear: abre el .blend del render V3 (solo lectura), crea en cada malla fija un segundo juego de UV «luz»
     (desplegado automático + empaquetado común, densidad uniforme), hornea con Cycles la luz difusa directa +
     indirecta SIN el color del material (irradiancia) en un único atlas y guarda: atlas HDR + las UV «luz» por objeto.
       Blender -b blender/Apartamento_102_Render_V3.blend --python blender/scripts/hornear_lightmaps_web.py -- \
           hornear blender/scripts/apto-102.json apartamento-102/modelo/web/v4

  2) exportar: importa el GLB ORIGINAL en una escena vacía, le añade las UV «luz» por objeto (mismo orden de bucles:
     se verifica) y exporta una COPIA del modelo con TEXCOORD_1. La geometría, nombres, jerarquía y metadatos (extras)
     son los del original; solo se añade el segundo canal UV.
       Blender -b --factory-startup --python blender/scripts/hornear_lightmaps_web.py -- \
           exportar blender/scripts/apto-102.json apartamento-102/modelo/web/v4

Salida en <destino>: atlas_luz.hdr, uv_luz.npz, lightmaps.json, apto-102-v4.glb
"""
import bpy, sys, os, json, math, time
import numpy as np

argv = sys.argv[sys.argv.index('--') + 1:]
PASO, CFG_PATH, DEST = argv[0], argv[1], os.path.abspath(argv[2])
PILOTO = '--piloto' in argv   # V5: aplica blender/scripts/piloto_v5.py (fusión, biseles, decoración CC0) a la copia
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
NOMBRE_GLB = 'apto-102-v5.glb' if PILOTO else 'apto-102-v4.glb'
CFG = json.load(open(CFG_PATH)); os.makedirs(DEST, exist_ok=True)
ROOT = os.path.abspath(os.environ.get('ORA_ROOT') or os.path.join(os.path.dirname(CFG_PATH), '..', '..'))
LM = CFG.get('lightmaps', {})
PX = LM.get('px', 2048); MUESTRAS = LM.get('muestras', 256)
EXCLUIR = tuple(LM.get('excluir_prefijos', ['ARQ_Piso', 'ARQ_Cielo', 'ILU_Cielo_detalles']))
GRAD = CFG['sondas'].get('gradacion', {'exposicion_ev': 0.8, 'balance_k': 5000})


def kelvin_rgb(k):
    t = k / 100.0
    r = 255 if t <= 66 else 329.698727446 * (t - 60) ** -0.1332047592
    g = 99.4708025861 * math.log(t) - 161.1195681661 if t <= 66 else 288.1221695283 * (t - 60) ** -0.0755148492
    b = 255 if t >= 66 else (0 if t <= 19 else 138.5177312231 * math.log(t - 10) - 305.0447927307)
    c = np.clip(np.array([r, g, b], np.float32) / 255, 0, 1)
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return c / c[1]


def objetos_horneables(col):
    out = []
    for o in col.all_objects:
        if o.type != 'MESH' or o.name.startswith(EXCLUIR): continue
        if any(c.name.startswith('Variante_') for c in o.users_collection): continue   # variantes ocultas por defecto
        if not o.data.polygons: continue
        out.append(o)
    return out


def denoise_oidn(img, escena_base):
    """Pasa el atlas por el nodo Denoise (OIDN) del compositor en una escena auxiliar vacía. Devuelve el arreglo o None."""
    try:
        px = img.size[0]
        aux = bpy.data.scenes.new('_denoise'); aux.render.engine = 'BLENDER_WORKBENCH'
        aux.render.resolution_x = aux.render.resolution_y = px; aux.render.resolution_percentage = 100
        cam = bpy.data.objects.new('_cam_den', bpy.data.cameras.new('_cam_den')); aux.collection.objects.link(cam); aux.camera = cam
        aux.render.image_settings.file_format = 'OPEN_EXR'; aux.render.image_settings.color_depth = '32'
        aux.view_settings.view_transform = 'Standard'
        if hasattr(aux, 'compositing_node_group'):   # Blender 5: grupo de nodos del compositor
            ng = bpy.data.node_groups.new('_den', 'CompositorNodeTree'); aux.compositing_node_group = ng
            ng.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
            salida = ng.nodes.new('NodeGroupOutput'); entrada_salida = salida.inputs[0]
        else:
            aux.use_nodes = True; ng = aux.node_tree; ng.nodes.clear()
            salida = ng.nodes.new('CompositorNodeComposite'); entrada_salida = salida.inputs[0]
        n_img = ng.nodes.new('CompositorNodeImage'); n_img.image = img
        n_den = ng.nodes.new('CompositorNodeDenoise')
        for nombre, valor in (('prefilter', 'ACCURATE'), ('use_hdr', True)):
            if hasattr(n_den, nombre): setattr(n_den, nombre, valor)
        for s_ in n_den.inputs:
            if s_.name == 'HDR' and hasattr(s_, 'default_value'): s_.default_value = True
        ng.links.new(n_img.outputs['Image'], n_den.inputs['Image']); ng.links.new(n_den.outputs['Image'], entrada_salida)
        aux.render.use_compositing = True
        ruta = os.path.join(DEST, '_den.exr'); aux.render.filepath = ruta
        bpy.ops.render.render(write_still=True, scene=aux.name)
        res = bpy.data.images.load(ruta); w, h = res.size
        a = np.array(res.pixels[:], np.float32).reshape(h, w, 4); bpy.data.images.remove(res); os.remove(ruta)
        return a if (w, h) == (px, px) and np.isfinite(a).all() and a[..., :3].max() > 0 else None
    except Exception as e:
        print('[lightmaps] OIDN no disponible:', e); return None


def hornear():
    sc = bpy.data.scenes[CFG['escena']]
    if bpy.context.window: bpy.context.window.scene = sc
    col = bpy.data.collections[f"APTO_{CFG['apartamento']}_Modelo"]
    objs = objetos_horneables(col)
    if PILOTO:
        import piloto_v5
        cfgp = dict(CFG['piloto']); cfgp['fusionar'] = [o.name for o in objs]
        raiz = next((o for o in col.objects if o.parent is None and o.type == 'EMPTY'), None)
        nuevos, res = piloto_v5.aplicar(cfgp, ROOT, col, raiz)
        objs = objetos_horneables(col)
        print(f"[lightmaps] piloto: {len(res['fusionados'])} fusionadas, {len(res['biselados'])} biseladas, {len(res['reemplazos'])} cerámicas, {len(res['utileria'])} utilería")
        json.dump(res, open(os.path.join(DEST, 'piloto.json'), 'w'), indent=1, ensure_ascii=False, default=str)
    print(f'[lightmaps] {len(objs)} mallas a hornear')
    # --- UV «luz»: desplegado automático por objeto y empaquetado común (densidad uniforme)
    vl = bpy.context.view_layer
    for o in vl.objects: o.select_set(False)
    for o in objs:
        me = o.data
        if 'luz' not in me.uv_layers:
            uv0 = me.uv_layers.active_index; me.uv_layers.new(name='luz'); me.uv_layers.active_index = uv0
        me.uv_layers.active = me.uv_layers['luz']
        for i, l in enumerate(me.uv_layers): l.active_render = (l.name != 'luz' and i == 0)   # los materiales siguen usando las UV originales
        o.select_set(True)
    vl.objects.active = objs[0]
    t0 = time.time()
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.0, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.average_islands_scale()
    try:   # Blender 3.6+: empaquetado por forma (cóncavo), más denso que por cajas
        bpy.ops.uv.pack_islands(rotate=True, rotate_method='ANY', margin_method='FRACTION', margin=LM.get('margen', 0.003), shape_method='CONCAVE')
    except TypeError:
        bpy.ops.uv.pack_islands(rotate=True, margin=LM.get('margen', 0.003))
    bpy.ops.object.mode_set(mode='OBJECT')
    print(f'[lightmaps] UV «luz» desplegadas y empaquetadas en {time.time() - t0:.0f} s')
    # --- imagen destino activa en cada material (sin conectar)
    atlas = bpy.data.images.new('_atlas_luz', PX, PX, alpha=True, float_buffer=True)
    atlas.generated_color = (0, 0, 0, 0)
    mats = {s.material for o in objs for s in o.material_slots if s.material}
    for m in mats:
        nt = m.node_tree; n = nt.nodes.new('ShaderNodeTexImage'); n.image = atlas; n.name = '_destino_luz'
        nt.nodes.active = n
    # --- horneado de irradiancia (difusa directa + indirecta, sin color)
    r = sc.render; r.engine = 'CYCLES'
    sc.cycles.samples = MUESTRAS; sc.cycles.use_denoising = False
    try:
        cp = bpy.context.preferences.addons['cycles'].preferences; cp.compute_device_type = 'METAL'; cp.refresh_devices()
        for d in cp.devices: d.use = d.type == 'METAL'
        sc.cycles.device = 'GPU'
    except Exception as e: print('[lightmaps] sin GPU:', e)
    bk = r.bake; bk.use_pass_direct = True; bk.use_pass_indirect = True; bk.use_pass_color = False; bk.margin = 6; bk.use_clear = True
    t0 = time.time()
    bpy.ops.object.bake(type='DIFFUSE', pass_filter={'DIRECT', 'INDIRECT'}, margin=6, use_clear=True, target='IMAGE_TEXTURES')
    print(f'[lightmaps] horneado {PX}x{PX}, {MUESTRAS} muestras en {time.time() - t0:.0f} s')
    a = np.array(atlas.pixels[:], np.float32).reshape(PX, PX, 4)
    metodo = 'desenfoque'
    den = denoise_oidn(atlas, sc)
    if den is not None:
        a = np.concatenate([den[..., :3], a[..., 3:4]], axis=2); metodo = 'OIDN'
    print(f'[lightmaps] reducción de ruido: {metodo}')
    # --- reducción de ruido (y suavizado residual tras OIDN): desenfoque normalizado dentro de las islas
    m = (a[..., 3] > 0.5).astype(np.float32); rgb = a[..., :3] * m[..., None]
    k = np.array([1, 4, 6, 4, 1], np.float32); k /= k.sum()
    def conv(x):
        for ax in (0, 1):
            x = sum(np.roll(x, s - 2, axis=ax) * k[s] for s in range(5))
        return x
    num = conv(rgb); den = conv(m)[..., None]
    lis = np.where(den > 1e-4, num / np.maximum(den, 1e-4), 0)
    mezcla = 0.25 if metodo == 'OIDN' else 0.65
    lis = (rgb * (1 - mezcla) + lis * mezcla) * m[..., None]   # conserva el detalle de las sombras de contacto
    gan = (2 ** GRAD['exposicion_ev']) / kelvin_rgb(GRAD['balance_k']); gan = gan / gan[1] * (2 ** GRAD['exposicion_ev'])
    out = np.ones((PX, PX, 4), np.float32); out[..., :3] = lis * gan
    img = bpy.data.images.new('_out', PX, PX, alpha=False, float_buffer=True); img.pixels[:] = out.ravel()
    ruta = os.path.join(DEST, 'atlas_luz.hdr'); img.filepath_raw = ruta; img.file_format = 'HDR'; img.save()
    cobertura = float(m.mean())
    # --- UV «luz» por objeto (en el orden de bucles del objeto)
    datos = {}
    for o in objs:
        me = o.data; uv = np.empty(len(me.loops) * 2, np.float32); me.uv_layers['luz'].data.foreach_get('uv', uv)
        datos[o.name] = uv; datos[o.name + '__loops'] = np.array([len(me.loops), len(me.vertices)], np.int64)
    np.savez_compressed(os.path.join(DEST, 'uv_luz.npz'), **datos)
    json.dump({'atlas': 'atlas_luz.hdr', 'px': PX, 'muestras': MUESTRAS, 'cobertura_atlas': round(cobertura, 3),
               'objetos': sorted(o.name for o in objs), 'materiales': sorted(m.name for m in mats),
               'tipo': 'irradiancia difusa directa + indirecta (sin color del material)', 'gradacion': GRAD, 'reduccion_ruido': metodo,
               'uv': f'TEXCOORD_1 del GLB derivado {NOMBRE_GLB}', 'piloto': PILOTO}, open(os.path.join(DEST, 'lightmaps.json'), 'w'), indent=1, ensure_ascii=False)
    print(f'[lightmaps] atlas guardado (cobertura {cobertura:.0%}); el .blend de entrada no se guarda')


def exportar():
    datos = np.load(os.path.join(DEST, 'uv_luz.npz'))
    meta = json.load(open(os.path.join(DEST, 'lightmaps.json')))
    for o in list(bpy.data.objects): bpy.data.objects.remove(o)
    glb = os.path.join(ROOT, CFG['importar']['glb'])
    bpy.ops.import_scene.gltf(filepath=glb, import_shading='NORMALS', merge_vertices=False)
    if PILOTO:
        import piloto_v5
        cfgp = dict(CFG['piloto']); cfgp['fusionar'] = [n for n in meta['objetos'] if not n.startswith('DEC_')]
        raiz = next((o for o in bpy.data.objects if o.parent is None and o.type == 'EMPTY' and o.name.startswith('Apto_')), None)
        piloto_v5.aplicar(cfgp, ROOT, bpy.context.scene.collection, raiz)
    faltan, ok = [], 0
    for nombre in meta['objetos']:
        o = bpy.data.objects.get(nombre)
        if not o or o.type != 'MESH': faltan.append(nombre); continue
        me = o.data; n_loops, n_verts = datos[nombre + '__loops']
        if len(me.loops) != n_loops or len(me.vertices) != n_verts:
            raise SystemExit(f'[lightmaps] {nombre}: la malla importada no coincide ({len(me.loops)} vs {n_loops} bucles)')
        lay = me.uv_layers.new(name='luz'); lay.data.foreach_set('uv', datos[nombre]); ok += 1
        me.uv_layers.active_index = 0
        for i, l in enumerate(me.uv_layers): l.active_render = i == 0
    if faltan: raise SystemExit(f'[lightmaps] objetos no encontrados en el GLB original: {faltan}')
    salida = os.path.join(DEST, NOMBRE_GLB)
    kw = dict(filepath=salida, export_format='GLB', export_extras=True, export_yup=True, export_texcoords=True, export_normals=True,
              export_materials='EXPORT', export_cameras=False, export_lights=False, export_apply=False, export_animations=False)
    try: bpy.ops.export_scene.gltf(**kw, export_image_format='AUTO' if PILOTO else 'NONE')
    except TypeError: bpy.ops.export_scene.gltf(**kw)
    print(f'[lightmaps] {ok} mallas con UV «luz»; GLB derivado: {salida}')


hornear() if PASO == 'hornear' else exportar()
