"""Verifica que la conversión de cámaras a COLMAP (nube/splat/a_colmap.py) proyecta EXACTAMENTE igual que la cámara de
Blender: misma imagen para los mismos puntos 3D. Si falla, el splat quedaría desalineado con la malla de colisiones.
    Blender -b --factory-startup --python tools/splat/verificar_poses.py -- <transforms.json o control.json> [más...]
Imprime RESULTADO {"diferencia_max_px": {...}} (aceptable < 0,01 px)."""
import bpy, sys, os, json, numpy as np
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'nube', 'splat'))
import a_colmap
rng = np.random.default_rng(7)
P = np.column_stack([rng.uniform(-4.2, 0.2, 4000), rng.uniform(-4.0, 4.0, 4000), rng.uniform(0, 2.7, 4000)])   # espacio social (Blender)
res = {}
for ruta in sys.argv[sys.argv.index('--') + 1:]:
    t = json.load(open(ruta)); W, H = t['w'], t['h']
    sc = bpy.context.scene; sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, H, 100
    cd = bpy.data.cameras.new('v'); cd.lens_unit = 'FOV'; cd.angle = t['camera_angle_x']
    cam = bpy.data.objects.new('v', cd); sc.collection.objects.link(cam)
    peor, n = 0.0, 0
    for fr in t['frames'][::5]:
        cam.matrix_world = Matrix(fr['transform_matrix']); bpy.context.view_layer.update()
        uv, z = a_colmap.proyectar(fr['transform_matrix'], t, P)
        for (u, v), zz, p in zip(uv, z, P):
            if zz < 0.2: continue
            b = world_to_camera_view(sc, cam, Vector(p)); bu, bv = b.x * W, (1 - b.y) * H
            if 0 <= bu < W and 0 <= bv < H: peor = max(peor, abs(bu - u), abs(bv - v)); n += 1
    res[os.path.basename(ruta)] = {'px': round(peor, 5), 'puntos': n}
print('RESULTADO', json.dumps({'diferencia_max_px': res}))
