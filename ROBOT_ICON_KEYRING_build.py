"""Name keyring with a tiny robot-head logo between the hole and the text.

Usage: blender -b --python ROBOT_ICON_KEYRING_build.py -- NAME
Writes NAME_ROBOT_KEYRING.blend / .stl (file name in capitals, text as typed).
Same standard as NAME_KEYRING_build.py (CESAR V1): 60 x 25 x 3 mm plate, Ø4 hole 5 mm from the
left edge, DejaVu Sans Bold letters raised 2 mm (5 mm total). The robot is raised 2 mm too;
its eyes and mouth are cut down to the plate, so a 2-colour M600 swap at Z = 3.0 shows them.
The text shrinks to fit the area right of the robot.
"""
import bpy, bmesh, sys, os, math

OUT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, OUT)
import NAME_KEYRING_build as nk

# robot head, centred at (ICON_X from plate left edge, 0); all sizes in mm
ICON_X = 15.0
HEAD_W, HEAD_H, HEAD_R, HEAD_Y = 8.0, 7.0, 1.5, -1.2   # head rounded square, centre y
EAR_W, EAR_H = 1.2, 3.0                                # side "ears" (bolts)
EYE_D, EYE_DX, EYE_DY = 1.8, 1.7, 0.9                  # eye holes
MOUTH_W, MOUTH_H, MOUTH_DY = 4.0, 0.9, -1.6            # mouth slot
ANT_W, ANT_H, ANT_BALL_D = 1.0, 2.2, 2.4               # antenna stem + ball
ICON_GAP = 1.8                                         # robot -> text
Z0 = nk.PLATE_T - 1.0                                  # icon bottom, buried in the plate

def prism(pts, z0, z1, name="p"):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    vs = [bm.verts.new((x, y, z0)) for x, y in pts]
    f = bm.faces.new(vs)
    ext = bmesh.ops.extrude_face_region(bm, geom=[f])
    for v in [e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)]:
        v.co.z = z1
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    return ob

def rrect(cx, cy, w, h, r, n=8):
    pts = []
    for qx, qy, a0 in [(1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)]:
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + qx * (w / 2 - r) + r * math.cos(a), cy + qy * (h / 2 - r) + r * math.sin(a)))
    return pts

def circle(cx, cy, d, n=32):
    return [(cx + d / 2 * math.cos(2 * math.pi * i / n), cy + d / 2 * math.sin(2 * math.pi * i / n)) for i in range(n)]

def make_robot(cx):
    top = nk.TEXT_TOP
    head = prism(rrect(cx, HEAD_Y, HEAD_W, HEAD_H, HEAD_R), Z0, top, "robot")
    parts = [
        prism(rrect(cx - HEAD_W / 2 - EAR_W / 2 + 0.3, HEAD_Y, EAR_W + 0.6, EAR_H, 0.4), Z0, top),
        prism(rrect(cx + HEAD_W / 2 + EAR_W / 2 - 0.3, HEAD_Y, EAR_W + 0.6, EAR_H, 0.4), Z0, top),
        prism(rrect(cx, HEAD_Y + HEAD_H / 2 + ANT_H / 2 - 0.3, ANT_W, ANT_H + 0.6, 0.2), Z0, top),
        prism(circle(cx, HEAD_Y + HEAD_H / 2 + ANT_H + ANT_BALL_D / 2 - 0.4, ANT_BALL_D), Z0, top),
    ]
    for p in parts:
        nk.boolean(head, p, 'UNION')
    cut_z0, cut_z1 = Z0 - 1, top + 1
    for c in [prism(circle(cx - EYE_DX, HEAD_Y + EYE_DY, EYE_D), cut_z0, cut_z1),
              prism(circle(cx + EYE_DX, HEAD_Y + EYE_DY, EYE_D), cut_z0, cut_z1),
              prism(rrect(cx, HEAD_Y + MOUTH_DY, MOUTH_W, MOUTH_H, 0.4), cut_z0, cut_z1)]:
        nk.boolean(head, c, 'DIFFERENCE')
    return head

def build(name):
    nk.clean()
    L = nk.PLATE_L
    left = -L / 2
    cx = left + ICON_X
    robot = make_robot(cx)
    text_x0 = cx + HEAD_W / 2 + EAR_W + ICON_GAP
    area = L / 2 - nk.TEXT_GAP_RIGHT - text_x0
    text, tw = nk.make_text(name)
    if tw > area:
        bpy.data.objects.remove(text)
        text, tw = nk.make_text(name, nk.TEXT_SIZE * (area - 2 * nk.TEXT_BEVEL) / (tw - 2 * nk.TEXT_BEVEL))
    text.location.x = text_x0 + (area - tw) / 2
    text_dims = tuple(text.dimensions)
    plate = nk.make_plate(L)
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=nk.HOLE_D / 2, depth=10,
                                        location=(left + nk.HOLE_FROM_EDGE, 0, 1.5))
    nk.boolean(plate, bpy.context.active_object, 'DIFFERENCE')
    nk.boolean(plate, robot, 'UNION')
    nk.boolean(plate, text, 'UNION')
    if abs(plate.dimensions.z - nk.TEXT_TOP) > 0.01:
        sys.exit(f"ERROR {name}: relief missing, height {plate.dimensions.z:.2f} mm")
    plate.name = f"{name}_Keychain"
    tag = f"{name.upper()}_ROBOT_KEYRING"
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f"{tag}.blend"))
    bpy.ops.object.select_all(action='DESELECT'); plate.select_set(True)
    bpy.ops.wm.stl_export(filepath=os.path.join(OUT, f"{tag}.stl"), export_selected_objects=True, global_scale=1.0)
    print("BUILT", tag, "dims", tuple(round(d, 2) for d in plate.dimensions),
          "text", tuple(round(d, 2) for d in text_dims), "text area", round(area, 2))

if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["RobotIA"]
    for n in argv:
        build(n)
