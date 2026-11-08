# Prueba en seco (CPU, sin render, sin simulación, sin guardar) de dos secciones del script V2 del rediseño de sala, usando
# su código real extraído del archivo: (a) generación de la obra a 1/5 de resolución; (b) extracción de los anillos de
# costura de cada cojín de la escena v1 (con la misma subdivisión que aplicaría la simulación).
#   blender -b --factory-startup <escena_sala_rediseno_v1.blend> --python prueba_seco_sala_v2.py -- <rediseno_sala_v2.py> <carpeta_tmp>
import bpy, bmesh, sys, os, math, json, time
import numpy as np
from mathutils import Vector, Matrix
V2, OUT = sys.argv[sys.argv.index('--') + 1:][:2]
src = open(V2, encoding='utf-8').read()
def seccion(desde, hasta):
    a = src.index(desde); return src[a:src.index(hasta, a)]
res = {}
# (b) anillos de costura (sin simular)
ns = {'bpy': bpy, 'bmesh': bmesh, 'np': np, 'math': math}
exec(seccion('def volumen(me):', 'def vivo('), ns)
anillos = {}
for nombre, cortes in (('SOFA_asiento_continuo', 3), ('SOFA_cojin_respaldo_1', 3), ('SOFA_cojin_respaldo_2', 3),
                       ('SOFA_deco_marfil', 2), ('SOFA_deco_carbon', 2), ('SOFA_deco_topo', 2)):
    o = bpy.context.scene.objects[nombre]; me = o.data.copy(); tmp = bpy.data.objects.new('_tmp', me)
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cortes, use_grid_fill=True); bm.to_mesh(me); bm.free()
    umbral = int(src.split('anillos = anillos_costura(o, ')[1].split(')')[0])   # el mismo umbral que usa el script
    co = np.array([v.co[:] for v in me.vertices]); anillos[nombre] = []
    for r in ns['anillos_costura'](tmp, umbral):
        P = co[r]; seg = np.linalg.norm(np.diff(np.vstack([P, P[:1]]), axis=0), axis=1)
        anillos[nombre].append({'vertices': len(r), 'perimetro_m': round(float(seg.sum()), 3), 'tramo_max_mm': round(float(seg.max()) * 1000, 1)})
    bpy.data.objects.remove(tmp); bpy.data.meshes.remove(me)
res['anillos_por_cojin'] = anillos
# (a) obra de arte a 1/5 de resolución
codigo = seccion('AW, AH = 1.90', "ARTE = bpy.data.materials['sala_arte_abstracto']").replace('PH, PW = 2112, 3820', 'PH, PW = 422, 764')
codigo = codigo.replace("range(520)", "range(104)").replace("range(700)", "range(140)")   # misma densidad de trazos por área
na = {'bpy': bpy, 'np': np, 'math': math, 'os': os, 'time': time, 'OX': 4.037, 'OY': 3.8, 'OUT': OUT}
t = time.time(); exec(codigo, na); res['obra_segundos'] = round(time.time() - t, 1)
c, al, rg, me_ = na['color'], na['alt'], na['rug'], na['metal']
res['obra'] = {'color_min_max': [round(float(c.min()), 3), round(float(c.max()), 3)], 'nan': bool(np.isnan(c).any() or np.isnan(al).any()),
               'altura_min_max': [round(float(al.min()), 3), round(float(al.max()), 3)], 'rugosidad_min_max': [round(float(rg.min()), 3), round(float(rg.max()), 3)],
               'fraccion_negro': round(float(na['negro'].mean()), 3), 'fraccion_oro_metal': round(float(me_.mean()), 4),
               'imagenes': [na['IMC'].name, na['IMD'].name, list(na['IMC'].size)]}
print('SECO' + json.dumps(res, ensure_ascii=False))
