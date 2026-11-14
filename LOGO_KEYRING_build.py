"""Two-colour logo keyring: graphic traced from a picture + text lines in DejaVu Sans Bold.

Usage: blender -b --python LOGO_KEYRING_build.py -- IMAGE.png NAME "LINE1|LINE2" [WIDTH HEIGHT]
Example (INSTAFRIO):
  blender -b --python LOGO_KEYRING_build.py -- INSTAFRIO_logo.png INSTAFRIO "INSTAFRIO|REFRIGERACIÓN Y CLIMATIZACIÓN"

The picture must be a dark logo on a light background. The topmost block of dark pixels (the
graphic above the text) is traced with marching squares; the text in the picture is ignored and
redrawn from the font, which is much sharper than tracing small low-resolution letters.
Layout from the bottom: last line (small), first line (large), graphic on top, hole top left.
Base PLATE_T mm (colour 1) + logo raised RAISE mm (colour 2): slice with --color-change-z PLATE_T.
Outputs NAME_KEYRING.blend / .stl (one solid) / _BASE.stl / _LOGO.stl.
"""
import bpy, bmesh, sys, os, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "NAME_KEYRING_build.py"), encoding="utf-8").read().split("argv = sys.argv")[0]
exec(src)  # clean, to_mesh, boolean, FONT ...

argv = sys.argv[sys.argv.index("--") + 1:]
IMAGE, NAME, LINES = argv[0], argv[1], argv[2].split("|")
PLATE_W, PLATE_HT = (float(argv[3]), float(argv[4])) if len(argv) > 4 else (84.0, 44.0)
PLATE_T, RAISE = 3.0, 2.0
CORNER_R, EDGE_R = 3.0, 0.5
HOLE_D, HOLE_INSET = 4.5, 5.5          # hole centre from the top and left edges
MARGIN = 3.0
TEXT_W = PLATE_W - 2 * MARGIN
SUB_H, MAIN_H = 3.4, 7.5               # text bounding-box heights (sub includes accents)
GAP_SUB, GAP_GRAPHIC = 1.8, 2.3
THRESH = 0.6                           # luminance threshold: below = ink

# ---------- trace the graphic ----------
def load_luma(path):
    img = bpy.data.images.load(path)
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)   # row 0 = bottom
    lum = 0.3 * px[..., 0] + 0.59 * px[..., 1] + 0.11 * px[..., 2]
    return lum * px[..., 3] + (1 - px[..., 3])                         # transparent = white

def graphic_crop(lum):
    rows = np.where((lum < THRESH).any(axis=1))[0]
    bands, start = [], rows[0]
    for a, b in zip(rows, rows[1:]):
        if b - a > 3:
            bands.append((start, a)); start = b
    bands.append((start, rows[-1]))
    # bottom bands = the text lines (one per line); everything above them is the graphic
    r0, r1 = bands[len(LINES)][0], rows[-1]
    cols = np.where((lum[r0:r1 + 1] < THRESH).any(axis=0))[0]
    p = 2
    return np.pad(lum[r0:r1 + 1, cols[0]:cols[-1] + 1], p, constant_values=1.0)

SEG = {1: [("L", "B")], 2: [("B", "R")], 3: [("L", "R")], 4: [("R", "T")], 6: [("B", "T")],
       7: [("L", "T")], 8: [("T", "L")], 9: [("B", "T")], 11: [("R", "T")], 12: [("L", "R")],
       13: [("B", "R")], 14: [("L", "B")]}

def contours(v):
    inside = v < THRESH
    H, W = v.shape
    def eid(side, i, j):
        return {"B": ("h", i, j), "T": ("h", i + 1, j), "L": ("v", i, j), "R": ("v", i, j + 1)}[side]
    adj = {}
    for i in range(H - 1):
        for j in range(W - 1):
            c = inside[i, j] | inside[i, j + 1] << 1 | inside[i + 1, j + 1] << 2 | inside[i + 1, j] << 3
            if c in (0, 15):
                continue
            if c in (5, 10):
                centre = (v[i, j] + v[i, j + 1] + v[i + 1, j] + v[i + 1, j + 1]) / 4 < THRESH
                segs = [("B", "R"), ("T", "L")] if (c == 5) == centre else [("L", "B"), ("R", "T")]
            else:
                segs = SEG[c]
            for s1, s2 in segs:
                a, b = eid(s1, i, j), eid(s2, i, j)
                adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
    def pos(e):
        k, i, j = e
        if k == "h":
            v0, v1 = v[i, j], v[i, j + 1]; t = (THRESH - v0) / (v1 - v0); return (j + t, i)
        v0, v1 = v[i, j], v[i + 1, j]; t = (THRESH - v0) / (v1 - v0); return (j, i + t)
    loops, seen = [], set()
    for start in adj:
        if start in seen:
            continue
        loop, prev, cur = [], None, start
        while True:
            seen.add(cur); loop.append(pos(cur))
            nxt = [n for n in adj[cur] if n != prev]
            if not nxt:
                break
            prev, cur = cur, nxt[0]
            if cur == start:
                break
        if len(loop) > 2:
            loops.append(loop)
    return loops

def make_graphic(target_h, top_y):
    v = graphic_crop(load_luma(bpy.path.abspath(os.path.join(HERE, IMAGE))))
    loops = contours(v)
    xs = [p[0] for l in loops for p in l]; ys = [p[1] for l in loops for p in l]
    s = target_h / (max(ys) - min(ys)); cx = (min(xs) + max(xs)) / 2
    cu = bpy.data.curves.new("graphic", 'CURVE'); cu.dimensions = '2D'; cu.fill_mode = 'BOTH'
    cu.extrude = (RAISE + 1.0) / 2                                       # 1 mm buried in the plate
    for l in loops:
        sp = cu.splines.new('POLY'); sp.points.add(len(l) - 1); sp.use_cyclic_u = True
        for p, (x, y) in zip(sp.points, l):
            p.co = ((x - cx) * s, (y - max(ys)) * s + top_y, 0, 1)
    ob = bpy.data.objects.new("graphic", cu); bpy.context.collection.objects.link(ob)
    ob.location.z = PLATE_T + RAISE - cu.extrude
    print("TRACED", len(loops), "loops, mm/pixel", round(s, 3))
    return to_mesh(ob)

# ---------- text ----------
def make_line(txt, box_w, box_h, bottom_y, spacing):
    cu = bpy.data.curves.new("txt", 'FONT'); cu.body = txt
    cu.font = bpy.data.fonts.load(FONT); cu.size = 10; cu.space_character = spacing
    cu.align_x = 'CENTER'; cu.extrude = (RAISE + 1.0) / 2; cu.resolution_u = 6
    ob = bpy.data.objects.new("txt", cu); bpy.context.collection.objects.link(ob)
    ob.location.z = PLATE_T + RAISE - cu.extrude
    m = to_mesh(ob)
    xs = [v.co.x for v in m.data.vertices]; ys = [v.co.y for v in m.data.vertices]
    sx, sy = box_w / (max(xs) - min(xs)), box_h / (max(ys) - min(ys))
    for v in m.data.vertices:
        v.co.x = (v.co.x - (min(xs) + max(xs)) / 2) * sx
        v.co.y = (v.co.y - min(ys)) * sy + bottom_y
    print(f"LINE '{txt}' x-stretch {sx / sy:.2f}")
    return m

def make_plate():
    L, H, r = PLATE_W - 2 * EDGE_R, PLATE_HT - 2 * EDGE_R, CORNER_R - EDGE_R
    cu = bpy.data.curves.new("plate", 'CURVE'); cu.dimensions = '2D'
    cu.fill_mode = 'BOTH'; cu.extrude = PLATE_T / 2 - EDGE_R
    cu.bevel_depth = EDGE_R; cu.bevel_resolution = 3
    pts = []
    for cx, cy, a0 in [(L/2-r, H/2-r, 0), (-L/2+r, H/2-r, 90), (-L/2+r, -H/2+r, 180), (L/2-r, -H/2+r, 270)]:
        for i in range(13):
            a = math.radians(a0 + 90 * i / 12); pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1); sp.use_cyclic_u = True
    for p, (x, y) in zip(sp.points, pts): p.co = (x, y, 0, 1)
    ob = bpy.data.objects.new("plate", cu); bpy.context.collection.objects.link(ob)
    ob.location.z = PLATE_T / 2
    return to_mesh(ob)

def mat(name, rgb):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = 0.5
    m.diffuse_color = (*rgb, 1)
    return m

def export(obj, path):
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True)

def copy(obj, name):
    o = bpy.data.objects.new(name, obj.data.copy()); o.matrix_world = obj.matrix_world
    bpy.context.collection.objects.link(o); return o

# ---------- build ----------
clean()
y = -PLATE_HT / 2 + MARGIN
parts = []
if len(LINES) > 1:
    parts.append(make_line(LINES[1], TEXT_W, SUB_H, y, 1.1)); y += SUB_H + GAP_SUB
parts.append(make_line(LINES[0], TEXT_W, MAIN_H, y, 1.0)); y += MAIN_H + GAP_GRAPHIC
top = PLATE_HT / 2 - MARGIN
parts.append(make_graphic(top - y, top))

logo = parts[0]
for p in parts[1:]:
    boolean(logo, p, 'UNION')
plate = make_plate()
bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=HOLE_D / 2, depth=10,
                                    location=(-PLATE_W / 2 + HOLE_INSET, PLATE_HT / 2 - HOLE_INSET, 1.5))
boolean(plate, bpy.context.active_object, 'DIFFERENCE')

# logo part = only what sits above the plate top, so the colours split cleanly at Z = PLATE_T
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, PLATE_T / 2))
cut = bpy.context.active_object; cut.scale = (300, 300, PLATE_T)
boolean(logo, cut, 'DIFFERENCE')

solid = copy(plate, f"{NAME}_Solid")
boolean(solid, copy(logo, "tmp"), 'UNION')
if abs(solid.dimensions.z - (PLATE_T + RAISE)) > 0.01:
    sys.exit(f"ERROR: logo missing, height {solid.dimensions.z:.2f} mm")

plate.name, logo.name = f"{NAME}_Base_WHITE", f"{NAME}_Logo_BLUE"
plate.data.materials.clear(); logo.data.materials.clear()
plate.data.materials.append(mat("White_PETG", (0.92, 0.92, 0.92)))
logo.data.materials.append(mat("Blue_PETG", (0.05, 0.08, 0.45)))
export(solid, os.path.join(HERE, f"{NAME}_KEYRING.stl"))
export(plate, os.path.join(HERE, f"{NAME}_KEYRING_BASE.stl"))
export(logo, os.path.join(HERE, f"{NAME}_KEYRING_LOGO.stl"))
solid.hide_set(True); solid.hide_render = True
for o in (plate, logo, solid):
    print("PART", o.name, tuple(round(d, 2) for d in o.dimensions), "faces", len(o.data.polygons))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, f"{NAME}_KEYRING.blend"))
