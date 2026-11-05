"""Build a name keyring matching CESAR_KEYRING.blend (V1) dimensions.

Usage: blender -b --python NAME_KEYRING_build.py -- NAME [NAME ...]
Same specs as CESAR: plate 25 mm tall x 3 mm thick, R2 corners, 0.5 mm rounded edges,
Ø4 mm hole (CESAR had Ø3) 5 mm from the left edge, DejaVu Sans Bold letters ~9.5 mm cap height,
raised 2 mm with a flat top (rounded tops printed lumpy at 0.2 mm layers). Plate is always 60 x 25 x 5 mm like CESAR;
longer names get smaller letters so they fit the same 48 mm text area.
"""
import bpy, bmesh, sys, os, math

OUT = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(OUT, "fonts", "DejaVuSans-Bold.ttf")  # bundled: same letters on every OS
PLATE_L, PLATE_H, PLATE_T, CORNER_R, EDGE_R = 60.0, 25.0, 3.0, 2.0, 0.5
HOLE_D, HOLE_FROM_EDGE = 4.0, 5.0  # 3 mm printed almost closed
TEXT_SIZE, TEXT_BEVEL, TEXT_TOP = 20.0, 0.3, 5.0
LETTER_SPACING = 1.045
TEXT_GAP_LEFT = 9.25   # plate left edge -> text left edge (as in CESAR)
TEXT_GAP_RIGHT = 2.75  # text right edge -> plate right edge

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
    bm = bmesh.new(); bm.from_mesh(me)   # weld cap/side seams -> watertight
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    return new

def make_text(name, size=TEXT_SIZE):
    cu = bpy.data.curves.new("txt", 'FONT')
    cu.body = name
    cu.font = bpy.data.fonts.load(FONT)
    cu.size = size
    cu.align_x, cu.align_y = 'LEFT', 'CENTER'
    cu.bevel_depth = TEXT_BEVEL
    cu.bevel_resolution = 2
    cu.space_character = LETTER_SPACING
    cu.extrude = 1.1  # bottom bevel stays buried in the plate
    cu.resolution_u = 6
    ob = bpy.data.objects.new("txt", cu)
    bpy.context.collection.objects.link(ob)
    ob.location.z = TEXT_TOP - cu.extrude  # widest outline reaches exactly TEXT_TOP
    m = to_mesh(ob)
    # cut the rounded top off: flat top, same stroke width
    bpy.ops.mesh.primitive_cube_add(size=200, location=(0, 0, TEXT_TOP + 100))
    boolean(m, bpy.context.active_object, 'DIFFERENCE')
    # recenter vertically on actual cap geometry
    ys = [v.co.y for v in m.data.vertices]; xs = [v.co.x for v in m.data.vertices]
    for v in m.data.vertices:
        v.co.y -= (min(ys) + max(ys)) / 2
        v.co.x -= min(xs)
    return m, max(xs) - min(xs)

def make_plate(length):
    # inner rounded rect; curve bevel grows it by EDGE_R to the final size
    L, H, r = length - 2 * EDGE_R, PLATE_H - 2 * EDGE_R, CORNER_R - EDGE_R
    cu = bpy.data.curves.new("plate", 'CURVE'); cu.dimensions = '2D'
    cu.fill_mode = 'BOTH'; cu.extrude = PLATE_T / 2 - EDGE_R
    cu.bevel_depth = EDGE_R; cu.bevel_resolution = 3; cu.resolution_u = 12
    pts = []
    for cx, cy, a0 in [(L/2-r, H/2-r, 0), (-L/2+r, H/2-r, 90), (-L/2+r, -H/2+r, 180), (L/2-r, -H/2+r, 270)]:
        for i in range(13):
            a = math.radians(a0 + 90 * i / 12)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1); sp.use_cyclic_u = True
    for p, (x, y) in zip(sp.points, pts): p.co = (x, y, 0, 1)
    ob = bpy.data.objects.new("plate", cu); bpy.context.collection.objects.link(ob)
    ob.location.z = PLATE_T / 2
    return to_mesh(ob)

def boolean(a, b, op):
    mod = a.modifiers.new("b", 'BOOLEAN'); mod.operation = op; mod.object = b; mod.solver = 'MANIFOLD'
    bpy.context.view_layer.objects.active = a
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(b)

def build(name):
    clean()
    # Same 60 mm plate as CESAR; text shrinks to fit the 48 mm text area if needed
    length = PLATE_L
    area = PLATE_L - TEXT_GAP_LEFT - TEXT_GAP_RIGHT
    text, tw = make_text(name)
    if tw > area:
        bpy.data.objects.remove(text)
        text, tw = make_text(name, TEXT_SIZE * (area - 2 * TEXT_BEVEL) / (tw - 2 * TEXT_BEVEL))
    plate = make_plate(length)
    text.location.x = -length / 2 + TEXT_GAP_LEFT + (area - tw) / 2
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=HOLE_D / 2, depth=10,
                                        location=(-length / 2 + HOLE_FROM_EDGE, 0, 1.5))
    boolean(plate, bpy.context.active_object, 'DIFFERENCE')
    text_dims = tuple(text.dimensions)
    boolean(plate, text, 'UNION')
    if abs(plate.dimensions.z - TEXT_TOP) > 0.01:  # a failed union silently drops the letters
        sys.exit(f"ERROR {name}: letters missing, height {plate.dimensions.z:.2f} mm, expected {TEXT_TOP} mm")
    plate.name = f"{name}_Keychain"
    tag = name.upper()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f"{tag}_KEYRING.blend"))
    bpy.ops.object.select_all(action='DESELECT'); plate.select_set(True)
    bpy.ops.wm.stl_export(filepath=os.path.join(OUT, f"{tag}_KEYRING.stl"), export_selected_objects=True,
                          global_scale=1.0)
    print("BUILT", tag, "dims", tuple(round(d, 2) for d in plate.dimensions), "text", tuple(round(d, 2) for d in text_dims))

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["CESAR"]
for n in argv:
    build(n)
