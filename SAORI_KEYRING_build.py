"""Two-colour SAORI keyring (black base, white letters) for a single-extruder printer.

Same CESAR V1 geometry (60x25 plate, 3 mm base, letters +2 mm) except the key-ring hole
is 4 mm instead of 3 mm (3 mm prints almost closed). Produces:
  SAORI_KEYRING.blend            base + letters as two coloured objects (for viewing)
  SAORI_KEYRING.stl              single solid for slicing (colour change at Z=3.0 mm)
  SAORI_KEYRING_BASE.stl / _LETTERS.stl   separate parts (for a multi-material slicer)
Run: blender -b --python SAORI_KEYRING_build.py
"""
import bpy, os
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "NAME_KEYRING_build.py")).read().split("argv = sys.argv")[0]
exec(src)
HOLE_D = 4.0  # (now also the default in NAME_KEYRING_build.py)
NAME = "SAORI"

def mat(name, rgb):
    m = bpy.data.materials.new(name); m.use_nodes = True
    bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*rgb, 1); bsdf.inputs["Roughness"].default_value = 0.5
    m.diffuse_color = (*rgb, 1)
    return m

def export(obj, path):
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True)

clean()
area = PLATE_L - TEXT_GAP_LEFT - TEXT_GAP_RIGHT
text, tw = make_text(NAME)
if tw > area:
    bpy.data.objects.remove(text)
    text, tw = make_text(NAME, TEXT_SIZE * (area - 2 * TEXT_BEVEL) / (tw - 2 * TEXT_BEVEL))
text.location.x = -PLATE_L / 2 + TEXT_GAP_LEFT + (area - tw) / 2
plate = make_plate(PLATE_L)
bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=HOLE_D / 2, depth=10,
                                    location=(-PLATE_L / 2 + HOLE_FROM_EDGE, 0, 1.5))
boolean(plate, bpy.context.active_object, 'DIFFERENCE')

# letters part = text above the plate top (Z>=3) so the two colours split cleanly
cutter_me = bpy.data.meshes.new("cut")
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, PLATE_T / 2))
cut = bpy.context.active_object; cut.scale = (200, 200, PLATE_T)
letters = text
mod = letters.modifiers.new("b", 'BOOLEAN'); mod.operation = 'DIFFERENCE'; mod.object = cut; mod.solver = 'MANIFOLD'
bpy.context.view_layer.objects.active = letters; bpy.ops.object.modifier_apply(modifier=mod.name)
bpy.data.objects.remove(cut)

# single solid for single-extruder printing
solid = bpy.data.objects.new("SAORI_Solid", plate.data.copy()); solid.matrix_world = plate.matrix_world
bpy.context.collection.objects.link(solid)
l2 = bpy.data.objects.new("tmp", letters.data.copy()); l2.matrix_world = letters.matrix_world
bpy.context.collection.objects.link(l2)
boolean(solid, l2, 'UNION')

plate.name, letters.name = "SAORI_Base_BLACK", "SAORI_Letters_WHITE"
plate.data.materials.append(mat("Black_PETG", (0.02, 0.02, 0.02)))
letters.data.materials.append(mat("White_PETG", (0.95, 0.95, 0.95)))
export(solid, os.path.join(HERE, "SAORI_KEYRING.stl"))
export(plate, os.path.join(HERE, "SAORI_KEYRING_BASE.stl"))
export(letters, os.path.join(HERE, "SAORI_KEYRING_LETTERS.stl"))
solid.hide_set(True); solid.hide_render = True
for o in (plate, letters, solid):
    print("PART", o.name, tuple(round(d, 2) for d in o.dimensions), "zmin", round(min((o.matrix_world @ v.co).z for v in o.data.vertices), 2))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "SAORI_KEYRING.blend"))
