import bpy, sys, json, hashlib
def val(v):
    if hasattr(v, 'to_dict'): return v.to_dict()
    if hasattr(v, 'to_list'): return v.to_list()
    if isinstance(v, (list, tuple)) or (hasattr(v, '__len__') and not isinstance(v, str)): return [val(x) for x in v]
    return v
a = sys.argv[sys.argv.index('--') + 1:]
out = {}
for o in bpy.data.objects:
    for k in o.keys(): out[f'{o.name}/{k}'] = hashlib.sha256(json.dumps(val(o[k]), sort_keys=True, default=str).encode()).hexdigest()[:16]
s = bpy.context.scene
out['bake_pass_filter'] = sorted(s.render.bake.pass_filter); out['snap_playhead'] = sorted(s.tool_settings.snap_playhead_element)
json.dump(out, open(a[0], 'w'), indent=1); print('PROPS_OK', len(out))
