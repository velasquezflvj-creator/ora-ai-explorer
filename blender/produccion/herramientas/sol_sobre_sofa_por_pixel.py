import bpy, sys, math, numpy as np
from mathutils import Vector
MASC = sys.argv[sys.argv.index('--') + 1]
sc = bpy.context.scene; dg = bpy.context.evaluated_depsgraph_get()
M = dict(np.load(MASC)); cam = sc.camera; fr = cam.data.view_frame(scene=sc)
tl, tr, br, bl = [cam.matrix_world @ v for v in (fr[0], fr[3], fr[2], fr[1])]; o = cam.matrix_world.translation
def mat_de(ob, i):
    try: return ob.material_slots[ob.data.polygons[i].material_index].material.name
    except Exception: return '?'
def al_sol(loc, nor):
    h = -dl
    if nor.dot(h) <= 0: return False
    p = loc + nor * 1e-3
    for _ in range(12):
        ok, l2, n2, i2, ob, _ = sc.ray_cast(dg, p, h)
        if not ok: return True
        if 'vidrio' in mat_de(ob, i2): p = l2 + h * 1e-3; continue
        return False
    return False
def medir(dl_, clave):
  global dl
  dl = dl_
  zona = M[clave].reshape(270, 480); tot = n = 0
  for j, i in zip(*np.nonzero(zona)):
      jj = 269 - j   # las máscaras están en orden de píxeles de Blender (abajo→arriba)
      p = tl + (tr - tl) * ((i + .5) / 480) + (bl - tl) * ((jj + .5) / 270); ok, loc, nor, idx, ob, _ = sc.ray_cast(dg, o, (p - o).normalized())
      if not ok: continue
      tot += 1
      if al_sol(loc, nor): n += 1
  return round(100 * n / max(tot, 1), 1)

# píxeles de piso: todo lo que no es máscara y queda en la mitad inferior (aprox.) — se mide el sol en el piso con trazado de cámara
W, H = 160, 90; piso_tot = 0
def sol_piso(dl_):
    global dl; dl = dl_; n = t = 0
    for jj in range(H // 2, H):
        for i in range(W):
            p = tl + (tr - tl) * ((i + .5) / W) + (bl - tl) * ((jj + .5) / H); ok, loc, nor, idx, ob, _ = sc.ray_cast(dg, o, (p - o).normalized())
            if ok and 'piso' in mat_de(ob, idx):
                t += 1; n += al_sol(loc, nor)
    return round(100 * n / max(t, 1), 1)
for elev in (18, 20, 22, 24, 26):
    for az in (80, 85, 90, 95):
        e, a_ = math.radians(elev), math.radians(az); v = Vector((math.cos(a_) * math.cos(e), math.sin(a_) * math.cos(e), -math.sin(e)))
        print('SOFA_SOL elev', elev, 'az', az, '| sofá al sol %', medir(v, 'sofa'), '| piso visible al sol %', sol_piso(v))
