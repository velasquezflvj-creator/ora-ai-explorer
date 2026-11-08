# Verificación previa (solo lectura, sin render ni simulación) de rediseno_sala_v2_no_ejecutado.py contra la escena v1:
# comprueba que existan los objetos, materiales, nodos, entradas y colecciones que el script V2 usa, para que un error de
# nombre no aparezca recién en la GPU. No guarda nada.
#   blender -b --factory-startup <escena_sala_rediseno_v1.blend> --python verificar_referencias_sala_v2.py
import bpy, json
sc = bpy.context.scene; fallos, avisos = [], []
def exige(cond, texto):
    if not cond: fallos.append(texto)

OBJETOS = ['SOFA_base', 'SOFA_concha_respaldo_brazos', 'SOFA_zocalo_bronce', 'SOFA_asiento_continuo', 'SOFA_cojin_respaldo_1',
           'SOFA_cojin_respaldo_2', 'SOFA_deco_marfil', 'SOFA_deco_carbon', 'SOFA_deco_topo', 'ARTE_lienzo_frente',
           'TV_consola_led_inferior', 'Luz_social_1', 'Luz_social_2']
for n in OBJETOS: exige(n in sc.objects, f'objeto {n}')
exige('REDISENO_SALA' in bpy.data.collections, 'colección REDISENO_SALA')
exige(any(o.name.startswith('ARTE_marco_') for o in sc.objects), 'objetos ARTE_marco_* (se sustituyen por el marco de una pieza)')
exige(any(o.name.startswith('TV_') and o.type == 'MESH' for o in sc.objects), 'objetos TV_* (cantos)')
for n in ('Luz_social_1', 'Luz_social_2'):
    o = sc.objects.get(n); exige(o is not None and o.type == 'LIGHT' and o.data.type == 'SPOT', f'{n} es un foco SPOT existente')
# cojines: malla cerrada (la simulación usa presión/volumen) y modificador de subdivisión que el script relee
import bmesh
for n in ['SOFA_asiento_continuo', 'SOFA_cojin_respaldo_1', 'SOFA_cojin_respaldo_2', 'SOFA_deco_marfil', 'SOFA_deco_carbon', 'SOFA_deco_topo']:
    o = sc.objects.get(n)
    if not o: continue
    exige(o.type == 'MESH', f'{n} es malla')
    bm = bmesh.new(); bm.from_mesh(o.data); cerrada = all(e.is_manifold for e in bm.edges); bm.free()
    exige(cerrada, f'{n} es una malla cerrada (manifold)')
    if not any(m.type == 'SUBSURF' for m in o.modifiers): avisos.append(f'{n} sin SUBSURF (el script usa nivel 2 por defecto)')
# materiales y nodos
MATS = {'sala_arte_abstracto': ['ShaderNodeBsdfPrincipled', 'ShaderNodeTexImage', 'ShaderNodeBump'],
        'sala_laton_satinado': ['ShaderNodeBsdfPrincipled'], 'sala_piedra_grafito_vetada': ['ShaderNodeBsdfPrincipled'],
        'sala_roble_ahumado': ['ShaderNodeBsdfPrincipled', 'ShaderNodeNormalMap'], 'sala_bronce_oscuro': ['ShaderNodeBsdfPrincipled'],
        'sala_led_indirecto_2700K': ['ShaderNodeEmission']}
for m, tipos in MATS.items():
    mat = bpy.data.materials.get(m); exige(mat is not None and mat.use_nodes, f'material {m}')
    if not mat: continue
    presentes = {n.bl_idname for n in mat.node_tree.nodes}
    for t in tipos: exige(t in presentes, f'{m}: nodo {t}')
    if 'ShaderNodeBsdfPrincipled' in tipos: exige('Principled BSDF' in mat.node_tree.nodes, f"{m}: nodo con nombre 'Principled BSDF'")
art = bpy.data.materials.get('sala_arte_abstracto')
if art:
    imgs = [n for n in art.node_tree.nodes if n.bl_idname == 'ShaderNodeTexImage']
    exige(any(n.image and 'color' in n.image.name for n in imgs), "sala_arte_abstracto: textura de color (nombre con 'color')")
    exige(len(imgs) >= 2, 'sala_arte_abstracto: dos texturas (color y datos)')
# entradas del BSDF Principista que el script escribe
p = bpy.data.materials['sala_bronce_oscuro'].node_tree.nodes.get('Principled BSDF') if 'sala_bronce_oscuro' in bpy.data.materials else None
for e in ('Anisotropic', 'Tangent', 'Roughness', 'Coat Weight', 'Coat Roughness', 'Normal', 'Metallic'):
    exige(p is not None and e in p.inputs, f"Principled BSDF: entrada '{e}'")
# nodos creados por el script: existen con las entradas usadas
nt = bpy.data.node_groups.new('_verif', 'ShaderNodeTree')
for tipo, ents in {'ShaderNodeTexNoise': ['Scale', 'Detail', 'Vector'], 'ShaderNodeBump': ['Strength', 'Distance', 'Height', 'Normal'],
                   'ShaderNodeMapping': ['Scale', 'Vector'], 'ShaderNodeTangent': []}.items():
    n = nt.nodes.new(tipo)
    for e in ents: exige(e in n.inputs, f'{tipo}: entrada {e}')
exige(hasattr(nt.nodes.new('ShaderNodeTangent'), 'direction_type'), 'ShaderNodeTangent.direction_type')
bpy.data.node_groups.remove(nt)
# ajustes de tela usados por el script
cl_ok = all(hasattr(bpy.types.ClothSettings, a) or a in bpy.types.ClothSettings.bl_rna.properties for a in
            ('use_pressure', 'uniform_pressure_force', 'use_internal_springs', 'internal_spring_max_length',
             'internal_tension_stiffness', 'internal_compression_stiffness', 'shrink_min'))
exige(cl_ok, 'ClothSettings: presión y resortes internos')
print('VERIF' + json.dumps({'fallos': fallos, 'avisos': avisos, 'comprobaciones_objetos': len(OBJETOS), 'materiales': len(MATS)}, ensure_ascii=False))
