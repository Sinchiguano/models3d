"""Two-colour script-name keyring: cursive letters on a base that follows the letter outline,
with a round tab and ring hole at the top left (style of newmodel.jpeg, the "Nicole" keyring).

Usage: blender -b --python SCRIPT_KEYRING_build.py -- NAME [WIDTH HEIGHT [BASE_T TOP]]
  NAME is used exactly as typed (e.g. Saori). WIDTH x HEIGHT is the overall size in mm (default 60 x 30).
  BASE_T is the base thickness and TOP the overall thickness in mm (default 3 and 5). Slice with
  --color-change-z BASE_T; pick a BASE_T that is a layer boundary (--fine: 0.24 + 0.12 n, e.g. 2.04 or 3.0).
Writes next to this script:
  NAME_SCRIPT_KEYRING.blend                  base + letters as two coloured objects
  NAME_SCRIPT_KEYRING.stl                    single solid for slicing (M600 colour change at Z = BASE_T)
  NAME_SCRIPT_KEYRING_BASE.stl / _LETTERS.stl   separate parts (for a multi-material slicer)

How the outline is made: the letters are turned into a signed-distance grid (geometry nodes),
grown by OUTLINE + CLOSE and shrunk back by CLOSE. That gives a smooth border of OUTLINE mm
and fills the small gaps inside and between the letters, like the original.
Colours only affect the Blender view: the real ones are the filaments you load.
"""
import bpy, bmesh, os, sys, math

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "fonts", "Lobster-Regular.otf")  # bundled script font (OFL)
OUTLINE = 2.5                  # base border around the letters
CLOSE = 2.0                    # extra radius that fills gaps inside/between letters
HOLE_D, TAB_WALL = 4.0, 2.5    # ring hole (4 mm prints ~3.5) and the wall around it
HOLE_CLEAR = 1.2               # minimum distance from the hole to the letters
TAB_RISE = 0.5                 # hole centre this far above the top of the letters
LETTER_SPACING = 1.0
VOXEL_BASE, VOXEL_LETTERS = 0.08, 0.05
BASE_RGB, LETTERS_RGB = (0.02, 0.02, 0.02), (0.45, 0.45, 0.47)  # black base, grey letters

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["Saori"]
NAME = args[0]
WIDTH, HEIGHT = (float(args[1]), float(args[2])) if len(args) >= 3 else (60.0, 30.0)
# base (colour 1) and overall thickness; the letters (colour 2) rise from BASE_T to TOP
BASE_T, TOP = (float(args[3]), float(args[4])) if len(args) >= 5 else (3.0, 5.0)
# keep the mesh, and so the STL size, about constant on bigger keyrings (GitHub limit: 100 MB per file)
VOXEL_BASE, VOXEL_LETTERS = (v * max(1.0, WIDTH / 60.0) for v in (VOXEL_BASE, VOXEL_LETTERS))
TAG = f"{NAME.upper()}_SCRIPT_KEYRING"


def clean():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.unit_settings.system = 'METRIC'
    s.unit_settings.scale_length = 0.001
    s.unit_settings.length_unit = 'MILLIMETERS'


def to_mesh(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
    new = bpy.data.objects.new(obj.name + "_m", me)
    new.matrix_world = obj.matrix_world
    bpy.context.collection.objects.link(new)
    bpy.data.objects.remove(obj)
    return new


def text_mesh(size, z0, z1):
    """Letters as a mesh spanning z0..z1, left edge at x = 0, centred on y = 0."""
    cu = bpy.data.curves.new("txt", 'FONT')
    cu.body = NAME
    cu.font = bpy.data.fonts.load(FONT)
    cu.size = size
    cu.align_x, cu.align_y = 'LEFT', 'CENTER'
    cu.space_character = LETTER_SPACING
    cu.extrude = (z1 - z0) / 2
    cu.resolution_u = 8
    ob = bpy.data.objects.new("txt", cu)
    bpy.context.collection.objects.link(ob)
    ob.location.z = (z0 + z1) / 2
    m = to_mesh(ob)
    bpy.context.view_layer.objects.active = m; m.select_set(True)
    bpy.ops.object.transform_apply(location=True)
    xs = [v.co.x for v in m.data.vertices]; ys = [v.co.y for v in m.data.vertices]
    dx, dy = -min(xs), -(min(ys) + max(ys)) / 2
    for v in m.data.vertices:
        v.co.x += dx; v.co.y += dy
    return m


def sdf(obj, voxel, offset=0.0):
    """Rebuild obj through a signed-distance grid, grown by offset mm (negative shrinks).
    Also unions overlapping glyphs into one watertight solid. The surface is read at
    distance = offset, which is much faster than SDF Grid Offset."""
    ng = bpy.data.node_groups.new("sdf", 'GeometryNodeTree')
    ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    gi, go = ng.nodes.new("NodeGroupInput"), ng.nodes.new("NodeGroupOutput")
    m2s = ng.nodes.new("GeometryNodeMeshToSDFGrid")
    m2s.inputs["Voxel Size"].default_value = voxel
    m2s.inputs["Band Width"].default_value = int(abs(offset) / voxel) + 3
    g2m = ng.nodes.new("GeometryNodeGridToMesh")
    g2m.inputs["Threshold"].default_value = offset
    g2m.inputs["Adaptivity"].default_value = 0.0
    ng.links.new(gi.outputs[0], m2s.inputs["Mesh"])
    ng.links.new(m2s.outputs[0], g2m.inputs["Grid"])
    ng.links.new(g2m.outputs[0], go.inputs[0])
    mod = obj.modifiers.new("sdf", 'NODES'); mod.node_group = ng
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)


def boolean(a, b, op):
    mod = a.modifiers.new("b", 'BOOLEAN'); mod.operation = op; mod.object = b; mod.solver = 'MANIFOLD'
    bpy.context.view_layer.objects.active = a
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(b)


def slab(obj, z0, z1):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, (z0 + z1) / 2))
    box = bpy.context.active_object; box.scale = (500, 500, z1 - z0)
    boolean(obj, box, 'INTERSECT')


def outline_pts(m):
    return [(v.co.x, v.co.y) for v in m.data.vertices]


def bbox2d(objs):
    xs = [(o.matrix_world @ v.co).x for o in objs for v in o.data.vertices]
    ys = [(o.matrix_world @ v.co).y for o in objs for v in o.data.vertices]
    return min(xs), max(xs), min(ys), max(ys)


def hole_centre(pts, hole_r):
    """Ring hole on a tab sticking out at the top left (like the photo),
    as close to the letters as the clearance allows."""
    xmin = min(p[0] for p in pts); ymax = max(p[1] for p in pts)
    need = hole_r + HOLE_CLEAR
    y = ymax + TAB_RISE
    x = xmin + 3.0
    while min(math.hypot(px - x, py - y) for px, py in pts) < need:
        x -= 0.1
    return x, y


def build_base(size):
    """Base outline (mesh, z 0..BASE_T) with the tab, and the hole centre."""
    tall = text_mesh(size, -2.0, BASE_T + 2.0)
    hx, hy = hole_centre(outline_pts(tall), HOLE_D / 2)
    # tab disc: after growing by OUTLINE it has radius HOLE_D/2 + TAB_WALL
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=HOLE_D / 2 + TAB_WALL - OUTLINE,
                                        depth=BASE_T + 4.0, location=(hx, hy, BASE_T / 2))
    tab = bpy.context.active_object
    bpy.ops.object.select_all(action='DESELECT'); tall.select_set(True); tab.select_set(True)
    bpy.context.view_layer.objects.active = tall; bpy.ops.object.join()
    sdf(tall, VOXEL_BASE, OUTLINE + CLOSE)   # grow ...
    sdf(tall, VOXEL_BASE, -CLOSE)            # ... and shrink back: gaps stay filled
    slab(tall, 0.0, BASE_T)
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=HOLE_D / 2, depth=20, location=(hx, hy, 0))
    boolean(tall, bpy.context.active_object, 'DIFFERENCE')
    return tall


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
# 1) text size that makes the keyring WIDTH wide: estimated from the letters and the tab
#    (border and tab don't scale with the text), so the slow outline is built only once
def estimated_width(size):
    t = text_mesh(size, 0.0, 1.0)
    pts = outline_pts(t)
    hx, _ = hole_centre(pts, HOLE_D / 2)
    bpy.data.objects.remove(t)
    left = min(min(p[0] for p in pts), hx - (HOLE_D / 2 + TAB_WALL - OUTLINE))
    return max(p[0] for p in pts) - left + 2 * OUTLINE


size = 20.0
for _ in range(6):
    w = estimated_width(size)
    if abs(w - WIDTH) < 0.02:
        break
    size *= (WIDTH - 2 * OUTLINE) / (w - 2 * OUTLINE)
base = build_base(size)

# 2) letters: one watertight solid from BASE_T to TOP
letters = text_mesh(size, BASE_T - 0.5, TOP)
sdf(letters, VOXEL_LETTERS)
slab(letters, BASE_T, TOP)

# 3) stretch Y so the overall size is exactly WIDTH x HEIGHT, then centre on the origin
x0, x1, y0, y1 = bbox2d([base])
sx, sy = WIDTH / (x1 - x0), HEIGHT / (y1 - y0)
print(f"FIT text size {size:.2f}, before stretch {x1 - x0:.2f} x {y1 - y0:.2f} mm, scale x {sx:.3f} y {sy:.3f}")
for o in (base, letters):
    for v in o.data.vertices:
        v.co.x = (v.co.x - (x0 + x1) / 2) * sx
        v.co.y = (v.co.y - (y0 + y1) / 2) * sy

# 4) single solid for one-extruder printing
solid = bpy.data.objects.new(f"{NAME}_Solid", base.data.copy())
bpy.context.collection.objects.link(solid)
tmp = bpy.data.objects.new("tmp", letters.data.copy())
bpy.context.collection.objects.link(tmp)
boolean(solid, tmp, 'UNION')
bpy.context.view_layer.update()
if abs(solid.dimensions.z - TOP) > 0.01 or abs(letters.dimensions.z - (TOP - BASE_T)) > 0.01:
    sys.exit(f"ERROR {NAME}: parts wrong, solid {solid.dimensions.z:.2f} mm, letters {letters.dimensions.z:.2f} mm")

base.name, letters.name = f"{NAME}_Base", f"{NAME}_Letters"
for part, mat in ((base, material("Base_colour", BASE_RGB)), (letters, material("Letters_colour", LETTERS_RGB))):
    part.data.materials.clear()
    part.data.materials.append(mat)
    bpy.context.view_layer.objects.active = part
    bpy.ops.object.shade_flat()
export(solid, os.path.join(HERE, f"{TAG}.stl"))
export(base, os.path.join(HERE, f"{TAG}_BASE.stl"))
export(letters, os.path.join(HERE, f"{TAG}_LETTERS.stl"))
solid.hide_set(True); solid.hide_render = True
for o in (base, letters, solid):
    print("PART", o.name, tuple(round(d, 2) for d in o.dimensions), len(o.data.polygons), "faces")
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, f"{TAG}.blend"))
