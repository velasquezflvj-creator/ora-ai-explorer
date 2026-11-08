# Análisis de solo lectura de la escena V2 (no guarda nada)
import bpy, json
sc = bpy.context.scene; out = {}
vs = sc.view_settings
out['color'] = dict(vista=vs.view_transform, look=vs.look, expo=vs.exposure, gamma=vs.gamma, display=sc.display_settings.display_device,
                   curva=vs.use_curve_mapping, secuenciador=sc.sequencer_colorspace_settings.name)
c = sc.cycles
out['cycles'] = dict(samples=c.samples, denoise=c.use_denoising, clamp_d=c.sample_clamp_direct, clamp_i=c.sample_clamp_indirect,
    filter_glossy=c.blur_glossy, caustics=(c.caustics_reflective, c.caustics_refractive), bounces=(c.max_bounces, c.diffuse_bounces, c.glossy_bounces),
    light_tree=c.use_light_tree, film_exposure=sc.cycles.film_exposure if hasattr(c,'film_exposure') else None, fast_gi=c.use_fast_gi, ao=getattr(c,'ao_bounces_render',None))
w = sc.world
def nodos(nt):
    r = []
    for n in nt.nodes:
        d = {'t': n.bl_idname, 'n': n.name}
        if n.bl_idname == 'ShaderNodeTexImage' and n.image: d['img'] = (n.image.name, tuple(n.image.size), n.image.colorspace_settings.name)
        if n.bl_idname == 'ShaderNodeMapping': d['escala'] = [round(v,3) for v in n.inputs['Scale'].default_value]
        if n.bl_idname == 'ShaderNodeBlackbody': d['K'] = n.inputs[0].default_value
        if n.bl_idname in ('ShaderNodeBsdfPrincipled', 'ShaderNodeEmission', 'ShaderNodeBackground', 'ShaderNodeMix', 'ShaderNodeMixRGB', 'ShaderNodeHueSaturation', 'ShaderNodeBrightContrast', 'ShaderNodeRGB', 'ShaderNodeBump', 'ShaderNodeTexCoord'):
            d['in'] = {s.name: (round(s.default_value,3) if isinstance(s.default_value,float) else [round(x,3) for x in s.default_value]) if hasattr(s,'default_value') and not s.is_linked else ('LINK:'+s.links[0].from_node.name if s.is_linked else None)
                       for s in n.inputs if s.enabled and s.name in ('Base Color','Roughness','Metallic','Specular IOR Level','Coat Weight','Sheen Weight','Transmission Weight','Normal','Color','Strength','Emission Color','Emission Strength','Fac','Factor','A','B','Hue','Saturation','Value','Bright','Contrast','Height','Distance','Subsurface Weight','IOR')}
        r.append(d)
    return r
out['mundo'] = {'nombre': w.name, 'nodos': nodos(w.node_tree) if w and w.node_tree else None}
out['luces'] = [dict(o=o.name, tipo=o.data.type, E=round(o.data.energy,2), color=[round(x,3) for x in o.data.color], K=getattr(o.data,'temperature',None), usa_K=getattr(o.data,'use_temperature',None),
                     tam=round(getattr(o.data,'size',0),3), visible=not o.hide_render, loc=[round(v,2) for v in o.location]) for o in sc.objects if o.type=='LIGHT']
usos = {}
for o in sc.objects:
    if o.type == 'MESH' and not o.hide_render:
        for s in o.material_slots:
            if s.material: usos.setdefault(s.material.name, []).append(o.name)
out['materiales'] = {m.name: {'objetos': usos.get(m.name, [])[:6], 'n_obj': len(usos.get(m.name, [])), 'nodos': nodos(m.node_tree) if m.node_tree else None}
                     for m in bpy.data.materials if m.name in usos}
out['imagenes'] = {i.name: (tuple(i.size), i.colorspace_settings.name, i.filepath) for i in bpy.data.images}
# objetos con UV sin mapeo: escala de UV aproximada (tamaño del objeto vs rango UV)
uvs = {}
for o in sc.objects:
    if o.type == 'MESH' and o.data.uv_layers.active and not o.hide_render:
        u = [l.uv for l in o.data.uv_layers.active.data]
        if u: uvs[o.name] = dict(rango_u=round(max(x[0] for x in u)-min(x[0] for x in u),2), rango_v=round(max(x[1] for x in u)-min(x[1] for x in u),2), dim=[round(d,2) for d in o.dimensions])
out['uv'] = uvs
json.dump(out, open('/tmp/ora_v4_analisis.json', 'w'), indent=1, default=str); print('ANALISIS_OK', len(out['materiales']), 'materiales', len(out['luces']), 'luces')
