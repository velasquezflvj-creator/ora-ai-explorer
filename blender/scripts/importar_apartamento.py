"""Crea el .blend de render de un apartamento a partir de su GLB del visor y de su configuración JSON.

    Blender -b --factory-startup --python blender/scripts/importar_apartamento.py -- \
        blender/scripts/apto-102.json blender/Apartamento_102_Render_Nuevo.blend

Reproduce, sin pasos manuales, la preparación que se hizo para el apartamento 102:
  1. escena propia con unidades métricas; importa el GLB conservando nombres, jerarquía y metadatos (extras →
     propiedades personalizadas: verificado, categoria, fuente, huella...);
  2. coloca los muebles de terceros en los nodos vacíos que traen «modelo» y «escala» en sus extras;
  3. excluye (no borra) los grupos alternativos que el visor oculta por defecto (p. ej. «sin_balcon»);
  4. materiales Principled con las texturas de config['materiales'] a escala real (UV del GLB en metros),
     vidrios con transmisión y emisivos;
  5. mundo HDRI, una luminaria por punto de ILU_Luminarias, portales en los vanos de fachada y la cámara de prueba;
  6. Cycles (GPU Metal si existe), AgX, sello con la advertencia del proyecto y texto LEEME con todas las advertencias.
No modifica el GLB ni ningún archivo de entrada. Las rutas de config son relativas a la raíz del repositorio.
"""
import bpy, sys, os, json, math

argv = sys.argv[sys.argv.index('--') + 1:]
CFG_PATH, SALIDA = argv[0], os.path.abspath(argv[1])
CFG = json.load(open(CFG_PATH))
ROOT = os.path.abspath(os.environ.get('ORA_ROOT') or os.path.join(os.path.dirname(CFG_PATH), '..', '..'))
R = lambda p: p if os.path.isabs(p) else os.path.join(ROOT, p)
I = CFG['importar']; ox, oy = CFG['origen_plano']


def lin(h):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c) + (1.0,)


# ---------------------------------------------------------------- 1. escena e importación
sc = bpy.data.scenes.get(CFG['escena']) or bpy.data.scenes.new(CFG['escena'])
if bpy.context.window: bpy.context.window.scene = sc
sc.unit_settings.system = 'METRIC'; sc.unit_settings.scale_length = 1.0


def coleccion(nombre, padre=None):
    c = bpy.data.collections.get(nombre) or bpy.data.collections.new(nombre)
    p = padre or sc.collection
    if c.name not in p.children: p.children.link(c)
    return c


def activar(c):
    def buscar(l):
        if l.collection == c: return l
        for h in l.children:
            r = buscar(h)
            if r: return r
    vl = sc.view_layers[0]
    lc = buscar(vl.layer_collection)
    if bpy.context.view_layer == vl: bpy.context.view_layer.active_layer_collection = lc
    return lc


c_mod = coleccion(f"APTO_{CFG['apartamento']}_Modelo"); c_mue = coleccion(f"APTO_{CFG['apartamento']}_Muebles_terceros")
activar(c_mod)
with bpy.context.temp_override(scene=sc, collection=c_mod):
    bpy.ops.import_scene.gltf(filepath=R(I['glb']), import_shading='NORMALS', merge_vertices=False)
modelo = list(c_mod.objects)

# ---------------------------------------------------------------- 2. muebles en sus nodos
activar(c_mue)
plantillas = {}
for clave, ruta in I.get('muebles', {}).items():
    antes = set(bpy.data.objects)
    with bpy.context.temp_override(scene=sc, collection=c_mue):
        bpy.ops.import_scene.gltf(filepath=R(ruta), import_shading='NORMALS')
    plantillas[clave] = [o for o in bpy.data.objects if o not in antes]
usadas = set()
for nodo in modelo:
    m = nodo.get('modelo')
    if not m or m not in plantillas: continue
    esc = float(nodo.get('escala', 1.0))
    if m not in usadas: objs = plantillas[m]; usadas.add(m)
    else:
        mapa = {}
        for x in plantillas[m]:
            y = x.copy(); c_mue.objects.link(y); mapa[x] = y
        for x, y in mapa.items():
            if x.parent in mapa: y.parent = mapa[x.parent]
        objs = list(mapa.values())
    for x in objs:
        if x.parent is None or x.parent not in objs:
            x.parent = nodo; x.matrix_parent_inverse.identity()
            x.scale = tuple(v * esc for v in x.scale); x.location = tuple(v * esc for v in x.location)
        x['fuente'] = nodo.get('fuente', ''); x['categoria'] = 'ilustrativo'; x['verificado'] = False

# ---------------------------------------------------------------- 3. variantes ocultas por defecto en el visor
for grupo in I.get('excluir_grupos', []):
    c = coleccion(f'Variante_{grupo} (oculta)')
    for o in modelo:
        if o.get('grupo') == grupo:
            for u in list(o.users_collection): u.objects.unlink(o)
            c.objects.link(o)
    activar(c).exclude = True

# ---------------------------------------------------------------- 4. materiales
MAT = CFG['materiales']; ESC = MAT['escala']; TEX = MAT['texturas']


def imagen(p, color):
    if not p or not os.path.exists(R(p)): return None
    im = bpy.data.images.load(R(p), check_existing=True); im.colorspace_settings.name = 'sRGB' if color else 'Non-Color'; return im


mats = {s.material for o in modelo for s in getattr(o, 'material_slots', []) if s.material}
for m in mats:
    nt = m.node_tree; b0 = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    base = tuple(b0.inputs['Base Color'].default_value) if b0 else (0.8, 0.8, 0.8, 1)
    rough = b0.inputs['Roughness'].default_value if b0 else 0.5
    metal = b0.inputs['Metallic'].default_value if b0 else 0
    alpha = b0.inputs['Alpha'].default_value if b0 else 1
    nt.nodes.clear(); N, L = nt.nodes, nt.links
    out = N.new('ShaderNodeOutputMaterial'); b = N.new('ShaderNodeBsdfPrincipled')
    s = MAT['mapa'].get(m.name, {})
    b.inputs['Base Color'].default_value = lin(s['c']) if 'c' in s else base
    b.inputs['Roughness'].default_value = s.get('r', rough); b.inputs['Metallic'].default_value = s.get('mt', metal)
    b.inputs['Alpha'].default_value = alpha
    if 'img' in s and s['img'] in TEX:
        t = TEX[s['img']]; w, h = ESC.get(s['img'], [1, 1])
        tc = N.new('ShaderNodeTexCoord'); mp = N.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1 / w, 1 / h, 1)
        L.new(tc.outputs['UV'], mp.inputs['Vector'])
        def nodo(p, color):
            im = imagen(p, color)
            if not im: return None
            n = N.new('ShaderNodeTexImage'); n.image = im; L.new(mp.outputs[0], n.inputs[0]); return n
        tcol, trou, tnor = nodo(t.get('color'), True), nodo(t.get('rough'), False), nodo(t.get('normal'), False)
        if tcol:
            mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = 1
            src = tcol.outputs['Color']
            if 'hsv' in t:
                hs = N.new('ShaderNodeHueSaturation'); hs.inputs['Hue'].default_value = t['hsv'].get('hue', 0.5)
                hs.inputs['Saturation'].default_value = t['hsv'].get('sat', 1); hs.inputs['Value'].default_value = t['hsv'].get('val', 1)
                L.new(src, hs.inputs['Color']); src = hs.outputs['Color']
            L.new(src, mx.inputs[6]); mx.inputs[7].default_value = lin(s.get('c', '#ffffff')); L.new(mx.outputs[2], b.inputs['Base Color'])
        if trou: L.new(trou.outputs['Color'], b.inputs['Roughness'])
        if tnor:
            nm = N.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = s.get('n_blender', s.get('n', 0.5))
            L.new(tnor.outputs['Color'], nm.inputs['Color']); L.new(nm.outputs[0], b.inputs['Normal'])
    salida = b.outputs[0]
    if m.name in MAT.get('vidrios', []):
        b.inputs['Base Color'].default_value = (0.92, 0.97, 0.95, 1); b.inputs['Transmission Weight'].default_value = 1
        b.inputs['Roughness'].default_value = 0; b.inputs['IOR'].default_value = 1.52; b.inputs['Alpha'].default_value = 1
        lp = N.new('ShaderNodeLightPath'); tr = N.new('ShaderNodeBsdfTransparent'); mx = N.new('ShaderNodeMixShader')
        L.new(lp.outputs['Is Shadow Ray'], mx.inputs[0]); L.new(b.outputs[0], mx.inputs[1]); L.new(tr.outputs[0], mx.inputs[2]); salida = mx.outputs[0]
    if m.name in MAT.get('emisivos', {}):
        k, st = MAT['emisivos'][m.name]
        bb = N.new('ShaderNodeBlackbody'); bb.inputs['Temperature'].default_value = k
        L.new(bb.outputs[0], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = st
    L.new(salida, out.inputs['Surface'])
    if b.inputs['Alpha'].default_value < 1 or m.name in MAT.get('vidrios', []):
        try: m.surface_render_method = 'BLENDED'
        except Exception: pass

# ---------------------------------------------------------------- 5. luz, cámara
Lz = CFG['luces']
w = bpy.data.worlds.new(f"Exterior_{CFG['apartamento']}"); sc.world = w; w.use_nodes = True; wn = w.node_tree; wn.nodes.clear()
env = wn.nodes.new('ShaderNodeTexEnvironment'); env.image = bpy.data.images.load(R(Lz['hdri']), check_existing=True)
tc = wn.nodes.new('ShaderNodeTexCoord'); mp = wn.nodes.new('ShaderNodeMapping'); mp.inputs['Rotation'].default_value[2] = math.radians(Lz.get('hdri_rotacion_grados', 0))
bg = wn.nodes.new('ShaderNodeBackground'); out = wn.nodes.new('ShaderNodeOutputWorld')
wn.links.new(tc.outputs['Generated'], mp.inputs['Vector']); wn.links.new(mp.outputs[0], env.inputs['Vector'])
wn.links.new(env.outputs['Color'], bg.inputs['Color']); wn.links.new(bg.outputs[0], out.inputs['Surface'])
c_luz = coleccion('ILUMINACION'); c_int = coleccion('Luminarias_interiores', c_luz); c_por = coleccion('Portales_fachada', c_luz)
dl = bpy.data.lights.new(f"Downlight_{Lz['temperatura_k']}K", 'SPOT'); dl.energy = Lz['potencia_w']
dl.use_temperature = True; dl.temperature = Lz['temperatura_k']; dl.spot_size = math.radians(100); dl.spot_blend = 0.75; dl.shadow_soft_size = 0.05
nodo_lum = bpy.data.objects.get(Lz['nodo_luminarias'])
puntos = nodo_lum.get('puntos').to_dict() if nodo_lum and nodo_lum.get('puntos') else {}
for esp, pts in puntos.items():
    for k, (x, y) in enumerate(pts):
        o = bpy.data.objects.new(f'Luz_{esp}_{k + 1}', dl); c_int.objects.link(o); o.location = (x - ox, y - oy, Lz['altura_m'])
for nombre, (x0, x1, z0, z1, y) in Lz.get('portales', {}).items():
    ld = bpy.data.lights.new(nombre, 'AREA'); ld.shape = 'RECTANGLE'; ld.size = x1 - x0; ld.size_y = z1 - z0; ld.cycles.is_portal = True
    o = bpy.data.objects.new(nombre, ld); c_por.objects.link(o); o.location = ((x0 + x1) / 2, y, (z0 + z1) / 2); o.rotation_euler = (math.radians(90), 0, 0)
Cm = CFG['camara_prueba']
cd = bpy.data.cameras.new(Cm['nombre']); cd.lens = Cm['lente_mm']; cd.sensor_width = 36; cd.clip_start = 0.05
cam = bpy.data.objects.new(Cm['nombre'], cd); coleccion('CAMARAS').objects.link(cam)
from mathutils import Vector
cam.location = (Cm['desde'][0] - ox, Cm['desde'][1] - oy, Cm['desde'][2])
cam.rotation_euler = (Vector((Cm['hacia'][0] - ox, Cm['hacia'][1] - oy, Cm['hacia'][2])) - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.camera = cam

# ---------------------------------------------------------------- 6. render y advertencias
sc.render.engine = 'CYCLES'; sc.cycles.samples = 512; sc.cycles.use_adaptive_sampling = True; sc.cycles.use_denoising = True
try:
    cp = bpy.context.preferences.addons['cycles'].preferences; cp.compute_device_type = 'METAL'; cp.refresh_devices()
    for d in cp.devices: d.use = d.type == 'METAL'
    sc.cycles.device = 'GPU'
except Exception: pass
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
sc.view_settings.view_transform = 'AgX'
raiz = next((o for o in modelo if o.parent is None), None)
adv = (raiz.get('advertencia', '') if raiz else '') or CFG.get('estado', '')
sc['advertencia'] = adv
t = bpy.data.texts.new(f"LEEME_Advertencias_apto_{CFG['apartamento']}")
t.write(f"APARTAMENTO {CFG['apartamento']} · {CFG.get('torre', '')}\n{CFG.get('estado', '')}\n\n{adv}\n\n"
        "Cada objeto conserva sus metadatos del GLB (verificado, categoria, fuente). Acabados, muebles y exterior: ilustrativos.\n")
r = sc.render; r.use_stamp = True
for a in ('use_stamp_date', 'use_stamp_time', 'use_stamp_render_time', 'use_stamp_frame', 'use_stamp_camera', 'use_stamp_lens', 'use_stamp_scene',
          'use_stamp_filename', 'use_stamp_memory', 'use_stamp_hostname', 'use_stamp_marker', 'use_stamp_frame_range'):
    if hasattr(r, a): setattr(r, a, False)
r.use_stamp_note = True; r.stamp_note_text = CFG.get('sello', adv)[:240]
os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=SALIDA)
print(f'[importar] {len(modelo)} objetos, {len(mats)} materiales, {sum(len(p) for p in puntos.values())} luminarias -> {SALIDA}')
