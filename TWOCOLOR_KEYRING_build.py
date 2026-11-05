"""Two-colour name keyring for one extruder (filament swap with M600 at Z = 3.0 mm).

Same standard size as NAME_KEYRING_build.py: 60 x 25 mm plate, 3 mm base, flat letters +2 mm, Hole 4 mm.

Usage: blender -b --python TWOCOLOR_KEYRING_build.py -- NAME
Writes next to this script:
  NAME_2COLOR_KEYRING.blend                base + letters as two coloured objects
  NAME_2COLOR_KEYRING.stl                  single solid for slicing
  NAME_2COLOR_KEYRING_BASE.stl / _LETTERS.stl   separate parts (for a multi-material slicer)
The colours below only affect the Blender view: the real ones are the filaments you load.
"""
import bpy, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "NAME_KEYRING_build.py")).read().split("argv = sys.argv")[0])

BASE_RGB, LETTERS_RGB = (0.02, 0.02, 0.02), (0.95, 0.95, 0.95)  # black base, white letters
NAME = sys.argv[sys.argv.index("--") + 1]
TAG = f"{NAME.upper()}_2COLOR_KEYRING"


def material(name, rgb):
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
letters, tw = make_text(NAME)
if tw > area:
    bpy.data.objects.remove(letters)
    letters, tw = make_text(NAME, TEXT_SIZE * (area - 2 * TEXT_BEVEL) / (tw - 2 * TEXT_BEVEL))
letters.location.x = -PLATE_L / 2 + TEXT_GAP_LEFT + (area - tw) / 2
plate = make_plate(PLATE_L)
bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=HOLE_D / 2, depth=10,
                                    location=(-PLATE_L / 2 + HOLE_FROM_EDGE, 0, 1.5))
boolean(plate, bpy.context.active_object, 'DIFFERENCE')

# keep only the letters above the plate top, so the two colours split cleanly at Z = 3
bpy.ops.mesh.primitive_cube_add(size=200, location=(0, 0, PLATE_T - 100))
boolean(letters, bpy.context.active_object, 'DIFFERENCE')

# single solid for printing with one extruder
solid = bpy.data.objects.new(f"{NAME}_Solid", plate.data.copy()); solid.matrix_world = plate.matrix_world
bpy.context.collection.objects.link(solid)
tmp = bpy.data.objects.new("tmp", letters.data.copy()); tmp.matrix_world = letters.matrix_world
bpy.context.collection.objects.link(tmp)
boolean(solid, tmp, 'UNION')
bpy.context.view_layer.update()
if abs(solid.dimensions.z - TEXT_TOP) > 0.01 or abs(letters.dimensions.z - (TEXT_TOP - PLATE_T)) > 0.01:
    sys.exit(f"ERROR {NAME}: letters missing, solid {solid.dimensions.z:.2f} mm, letters {letters.dimensions.z:.2f} mm")

plate.name, letters.name = f"{NAME}_Base", f"{NAME}_Letters"
for part, mat in ((plate, material("Base_colour", BASE_RGB)), (letters, material("Letters_colour", LETTERS_RGB))):
    part.data.materials.clear()  # curve conversion leaves an empty slot 0, which all faces use
    part.data.materials.append(mat)
export(solid, os.path.join(HERE, f"{TAG}.stl"))
export(plate, os.path.join(HERE, f"{TAG}_BASE.stl"))
export(letters, os.path.join(HERE, f"{TAG}_LETTERS.stl"))
solid.hide_set(True); solid.hide_render = True
for o in (plate, letters, solid):
    print("PART", o.name, tuple(round(d, 2) for d in o.dimensions))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, f"{TAG}.blend"))
