"""Turn a plate STL (several models made by `slice_gcode.py A.stl B.stl --name NAME`) into NAME.blend.

Usage: blender -b --python PLATE_build.py -- NAME.stl
Writes NAME.blend next to the STL (metric scene, 1 unit = 1 mm). Then render the preview with
  blender -b NAME.blend --python render_preview.py
"""
import bpy, os, sys

stl = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
bpy.ops.wm.read_factory_settings(use_empty=True)
s = bpy.context.scene
s.unit_settings.system = 'METRIC'
s.unit_settings.scale_length = 0.001
s.unit_settings.length_unit = 'MILLIMETERS'

bpy.ops.wm.stl_import(filepath=stl)
ob = bpy.context.selected_objects[0]
ob.name = os.path.splitext(os.path.basename(stl))[0]

mat = bpy.data.materials.new("PETG_white"); mat.use_nodes = True
bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
bsdf.inputs[0].default_value = (0.9, 0.9, 0.9, 1)
ob.data.materials.append(mat)

d = ob.dimensions
print(f"PLATE {ob.name}: {d.x:.1f} x {d.y:.1f} x {d.z:.1f} mm")
bpy.ops.wm.save_as_mainfile(filepath=os.path.splitext(stl)[0] + ".blend")
