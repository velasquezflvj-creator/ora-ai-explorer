"""Prepara el recorrido cinematográfico de un apartamento en un .blend aparte (no toca el de entrada).

    Blender -b blender/Apartamento_102_Render_V3.blend --python blender/scripts/camara_video.py -- \
        blender/scripts/apto-102.json blender/Apartamento_102_Video.blend [--vista-previa salida.mp4] [--estimar N]

· Crea la cámara CAM_Video con una toma por entrada de config['video']['tomas'] (corte entre tomas, movimiento
  suave con entrada y salida lentas dentro de cada toma) y guarda el .blend de video.
· --vista-previa: renderiza el recorrido completo con EEVEE a 640×360 en MP4 (H.264) para revisar el movimiento.
· --estimar N: renderiza N cuadros de muestra con la configuración final (Cycles 1920×1080) e imprime el tiempo
  estimado del render completo, sin lanzarlo.
"""
import bpy, sys, os, json, math, time

argv = sys.argv[sys.argv.index('--') + 1:]
CFG = json.load(open(argv[0])); SALIDA = os.path.abspath(argv[1])
PREVIA = argv[argv.index('--vista-previa') + 1] if '--vista-previa' in argv else None
ESTIMAR = int(argv[argv.index('--estimar') + 1]) if '--estimar' in argv else 0
PASO = int(argv[argv.index('--paso') + 1]) if '--paso' in argv else 2          # vista previa: 1 de cada N cuadros
MUESTRAS_PREVIA = int(argv[argv.index('--muestras') + 1]) if '--muestras' in argv else 4
V = CFG['video']; ox, oy = CFG['origen_plano']
sc = bpy.data.scenes[CFG['escena']]
if bpy.context.window: bpy.context.window.scene = sc
P = lambda q: (q[0] - ox, q[1] - oy, q[2])

col = bpy.data.collections.get('VIDEO') or bpy.data.collections.new('VIDEO')
if col.name not in sc.collection.children: sc.collection.children.link(col)
cd = bpy.data.cameras.get('CAM_Video') or bpy.data.cameras.new('CAM_Video')
cd.lens = V['lente_mm']; cd.sensor_width = V['sensor_mm']; cd.clip_start = 0.05
cam = bpy.data.objects.get('CAM_Video') or bpy.data.objects.new('CAM_Video', cd)
mira = bpy.data.objects.get('CAM_Video_mira') or bpy.data.objects.new('CAM_Video_mira', None)
for o in (cam, mira):
    if o.name not in col.objects: col.objects.link(o)
    o.animation_data_clear()
cam.constraints.clear()
c = cam.constraints.new('TRACK_TO'); c.target = mira; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
sc.camera = cam
fps = V['fps']; sc.render.fps = fps; f = 1
marcas = []
sc.timeline_markers.clear()
for nombre, seg, a, b, la, lb in V['tomas']:
    n = int(round(seg * fps)); f0, f1 = f, f + n - 1
    for fr, pc, pm in ((f0, a, la), (f1, b, lb)):
        cam.location = P(pc); cam.keyframe_insert('location', frame=fr)
        mira.location = P(pm); mira.keyframe_insert('location', frame=fr)
    sc.timeline_markers.new(nombre, frame=f0)
    marcas.append((nombre, f0, f1)); f = f1 + 1
for o in (cam, mira):   # movimiento lento con entrada/salida suaves; corte seco entre tomas
    for fc in o.animation_data.action.fcurves if hasattr(o.animation_data.action, 'fcurves') else []:
        for k in fc.keyframe_points: k.interpolation = 'BEZIER'; k.easing = 'AUTO'
sc.frame_start, sc.frame_end = 1, f - 1
# exterior visto por las ventanas (solo rayos de cámara): más desenfocado y sobreexpuesto que en el V3
ex = V.get('exterior')
if ex and sc.world and sc.world.use_nodes:
    for n in sc.world.node_tree.nodes:
        if n.type == 'VECT_MATH' and n.operation == 'SCALE': n.inputs['Scale'].default_value = ex['desenfoque']
        if n.type == 'HUE_SAT': n.inputs['Value'].default_value = ex['brillo']; n.inputs['Saturation'].default_value = ex['saturacion']
r = sc.render
r.use_stamp = True; r.use_stamp_note = True
r.stamp_note_text = 'Apto 102 · Propuesta de redistribución conceptual – no es planta verificada ni aprobada. Balcón, acabados, muebles y exterior ilustrativos.'
bpy.ops.wm.save_as_mainfile(filepath=SALIDA, copy=False)
print(f'[video] {len(marcas)} tomas, {sc.frame_end} cuadros a {fps} fps = {sc.frame_end / fps:.1f} s')
for m in marcas: print('[video] toma', m)

def gpu():
    try:
        cp = bpy.context.preferences.addons['cycles'].preferences; cp.compute_device_type = 'METAL'; cp.refresh_devices()
        for d in cp.devices: d.use = d.type == 'METAL'
        sc.cycles.device = 'GPU'
    except Exception as e: print('[video] sin GPU:', e)

if ESTIMAR:
    gpu(); r.engine = 'CYCLES'; r.resolution_x, r.resolution_y, r.resolution_percentage = 1920, 1080, 100
    sc.cycles.samples = V.get('muestras_final', 128); sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.02
    sc.cycles.use_denoising = True
    r.image_settings.file_format = 'PNG'
    tiempos = []
    destino = os.path.join(os.path.dirname(SALIDA), 'render', 'video_muestras'); os.makedirs(destino, exist_ok=True)
    for i in range(ESTIMAR):
        fr = int(1 + (sc.frame_end - 1) * (i + 0.5) / ESTIMAR); sc.frame_set(fr)
        r.filepath = os.path.join(destino, f'muestra_{fr:04d}.png')
        t0 = time.time(); bpy.ops.render.render(write_still=True, scene=sc.name); tiempos.append(time.time() - t0)
        print(f'[video] cuadro {fr}: {tiempos[-1]:.1f} s')
    prom = sum(tiempos) / len(tiempos)
    print(f'[video] ESTIMACION Cycles 1920x1080 {sc.cycles.samples} muestras: {prom:.1f} s/cuadro -> {prom * sc.frame_end / 3600:.1f} h para {sc.frame_end} cuadros')

if PREVIA:
    r.engine = 'BLENDER_EEVEE' if 'BLENDER_EEVEE' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE_NEXT'
    r.resolution_x, r.resolution_y, r.resolution_percentage = 640, 360, 100
    try: sc.eevee.taa_render_samples = MUESTRAS_PREVIA
    except Exception: pass
    sc.frame_step = PASO; r.fps = max(1, fps // PASO)   # misma duración, menos cuadros
    if hasattr(r.image_settings, 'media_type'): r.image_settings.media_type = 'VIDEO'   # Blender 5: el video es otro tipo de medio
    r.image_settings.file_format = 'FFMPEG'
    r.ffmpeg.format = 'MPEG4'; r.ffmpeg.codec = 'H264'; r.ffmpeg.constant_rate_factor = 'MEDIUM'
    r.filepath = os.path.abspath(PREVIA); r.use_stamp_note = True
    t0 = time.time(); bpy.ops.render.render(animation=True, scene=sc.name)
    dt = time.time() - t0
    print(f'[video] vista previa EEVEE 640x360: {dt:.0f} s en total, {dt / sc.frame_end:.2f} s/cuadro -> {PREVIA}')
