"""Render a quick preview PNG of a keyring/model .blend.

Usage: blender -b MODEL.blend --python render_preview.py
Writes MODEL_preview.png next to the .blend.
"""
import bpy, math, os
from mathutils import Vector

s = bpy.context.scene
meshes = [o for o in s.objects if o.type == 'MESH' and not o.hide_render]
for ob in meshes:
    if not ob.data.materials:
        mat = bpy.data.materials.new("Preview"); mat.use_nodes = True
        b = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        b.inputs[0].default_value = (0.1, 0.35, 0.8, 1)
        ob.data.materials.append(mat)

# frame all meshes (scene units are mm for the keyrings)
pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
center, size = (lo + hi) / 2, max((hi - lo).x, (hi - lo).y)

cam = bpy.data.objects.new("PreviewCam", bpy.data.cameras.new("PreviewCam"))
s.collection.objects.link(cam); s.camera = cam
cam.location = center + Vector((0, -0.92, 1.25)) * size
cam.rotation_euler = (math.radians(36), 0, 0); cam.data.lens = 50
cam.data.clip_end = size * 100
for d, e in [((30, -30, 60), 3), ((-40, 20, 50), 1.5)]:
    l = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN')); l.data.energy = e
    s.collection.objects.link(l)
    l.rotation_euler = (-Vector(d)).to_track_quat('-Z', 'Y').to_euler()
w = bpy.data.worlds.new("PreviewWorld"); s.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.9, 0.9, 0.92, 1)
for eng in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
    try:
        s.render.engine = eng; break
    except TypeError:
        pass
s.render.resolution_x, s.render.resolution_y = 1000, 600
s.render.filepath = os.path.splitext(bpy.data.filepath)[0] + "_preview.png"
bpy.ops.render.render(write_still=True)
