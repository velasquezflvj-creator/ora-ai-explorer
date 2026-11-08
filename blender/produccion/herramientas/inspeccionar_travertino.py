import bpy
for mn in ('salpicadero', 'meson', 'piso_madera'):
    m = bpy.data.materials[mn]; print('=====', mn)
    for n in m.node_tree.nodes:
        ins = {s.name: (round(s.default_value, 3) if isinstance(s.default_value, float) else [round(x, 3) for x in s.default_value]) for s in n.inputs if hasattr(s, 'default_value') and not s.is_linked and s.enabled and not isinstance(s.default_value, (str, bool))} if n.bl_idname != 'ShaderNodeBsdfPrincipled' else {}
        extra = {}
        if n.bl_idname == 'ShaderNodeTexImage': extra = {'img': n.image.name, 'proy': n.projection, 'blend': n.projection_blend, 'interp': n.interpolation}
        if n.bl_idname in ('ShaderNodeMix', 'ShaderNodeMath', 'ShaderNodeVectorMath', 'ShaderNodeMapRange'): extra = {'op': getattr(n, 'blend_type', getattr(n, 'operation', '')), 'tipo': getattr(n, 'data_type', '')}
        if n.bl_idname == 'ShaderNodeTexBrick': extra = {'offset': n.offset, 'squash': n.squash}
        print(f'  {n.name} [{n.bl_idname.replace("ShaderNode","")}] {extra} {ins}')
    for l in m.node_tree.links: print(f'    {l.from_node.name}.{l.from_socket.name} -> {l.to_node.name}.{l.to_socket.name}')
for o in bpy.context.scene.objects:
    if o.type == 'MESH' and any(s.material and s.material.name == 'salpicadero' for s in o.material_slots): print('obj salpicadero:', o.name, [round(d, 2) for d in o.dimensions], 'uv:', [u.name for u in o.data.uv_layers])
