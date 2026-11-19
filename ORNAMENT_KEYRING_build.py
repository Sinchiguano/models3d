"""Two-colour ornament keyring traced from a picture (style of "new one.jpeg": red line art on white).

Usage: blender -b --python ORNAMENT_KEYRING_build.py -- IMAGE NAME [DIAMETER [BASE_T TOP]]
Example: OPEN=317,728 blender -b --python ORNAMENT_KEYRING_build.py -- "new one.jpeg" César 70 3 6

How the picture is read:
  * dark (red) pixels are the line art; white areas are split into connected regions
  * the white region touching the picture border is the outside
  * "pockets" = white regions running along the inside of the outer ring (big contact): open holes
  * every other white region (letters, bow, snowflakes, faces ...) is a raised shape
  * OPEN="x,y;..." (env var, picture pixels from the top left) cuts more white regions through
  * the hanging loop's hole is replaced by a round HOLE_D hole at the same place
Result: base (colour 1, z 0..BASE_T) = line art + raised shapes; top (colour 2, BASE_T..TOP) = raised
shapes, so the line art shows as grooves between them, like the picture. DIAMETER is the overall width.
Slice with: python slice_gcode.py NAME_ORNAMENT_KEYRING.stl --material petg --keyring --color-change-z BASE_T
Outputs NAME_ORNAMENT_KEYRING.blend / .stl (one solid) / _BASE.stl / _TOP.stl
"""
import bpy, bmesh, os, sys, math, unicodedata
import numpy as np
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[sys.argv.index("--") + 1:]
IMAGE, NAME = args[0], args[1]
DIAMETER = float(args[2]) if len(args) > 2 else 70.0
BASE_T, TOP = (float(args[3]), float(args[4])) if len(args) > 4 else (3.0, 6.0)
THRESH = 0.6            # luminance below this = line art
POCKET_CONTACT = 1500   # white pixels near the outer ring needed to count as a pocket (open hole)
HOLE_D = 4.5            # ring hole (prints ~4)
BASE_RGB, TOP_RGB = (0.62, 0.02, 0.07), (0.95, 0.94, 0.9)
TAG = "_".join(unicodedata.normalize("NFKD", NAME.upper()).encode("ascii", "ignore").decode().split()) + "_ORNAMENT_KEYRING"


def clean():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.unit_settings.system = 'METRIC'
    s.unit_settings.scale_length = 0.001
    s.unit_settings.length_unit = 'MILLIMETERS'


# ---------- read the picture ----------
def load_red(path):
    img = bpy.data.images.load(path)
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)     # row 0 = bottom
    lum = 0.3 * px[..., 0] + 0.59 * px[..., 1] + 0.11 * px[..., 2]
    lum = lum * px[..., 3] + (1 - px[..., 3])                            # transparent = white
    return np.pad(lum < THRESH, 3, constant_values=False)


def label(white):
    h, w = white.shape
    lab = np.zeros((h, w), np.int32); n = 0
    for y0 in range(h):
        for x0 in np.nonzero(white[y0] & (lab[y0] == 0))[0]:
            if lab[y0, x0]:
                continue
            n += 1; lab[y0, x0] = n; q = deque([(y0, x0)])
            while q:
                y, x = q.popleft()
                for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                    if 0 <= yy < h and 0 <= xx < w and white[yy, xx] and not lab[yy, xx]:
                        lab[yy, xx] = n; q.append((yy, xx))
    return lab, n


def distance_from(m, k):
    """Approximate (octagonal) distance in px from mask m, capped at k."""
    d = np.where(m, 0, k).astype(np.int32); cur = m.copy()
    for step in range(1, k):
        g = cur.copy()
        g[1:] |= cur[:-1]; g[:-1] |= cur[1:]; g[:, 1:] |= cur[:, :-1]; g[:, :-1] |= cur[:, 1:]
        if step % 3 != 0:                                   # diagonals 2 of 3 steps: ~ round distance
            g[1:, 1:] |= cur[:-1, :-1]; g[:-1, :-1] |= cur[1:, 1:]; g[1:, :-1] |= cur[:-1, 1:]; g[:-1, 1:] |= cur[1:, :-1]
        d[g & ~cur] = step; cur = g
    return d


def ring_width(red):
    """Thickness of the outer ring: first run of line pixels along the middle row."""
    row = red[red.shape[0] // 2]; i = int(np.argmax(row)); j = i
    while row[j]:
        j += 1
    return j - i


# ---------- trace masks (marching squares) ----------
SEG = {1: [("L", "B")], 2: [("B", "R")], 3: [("L", "R")], 4: [("R", "T")], 6: [("B", "T")],
       7: [("L", "T")], 8: [("T", "L")], 9: [("B", "T")], 11: [("R", "T")], 12: [("L", "R")],
       13: [("B", "R")], 14: [("L", "B")]}


def contours(mask):
    """Closed outlines of a boolean mask, at sub-pixel precision (slightly blurred field)."""
    f = mask.astype(np.float32)
    f = (f + np.roll(f, 1, 0) + np.roll(f, -1, 0) + np.roll(f, 1, 1) + np.roll(f, -1, 1)) / 5
    f = np.pad(f, 1)
    ins = f > 0.5
    code = (ins[:-1, :-1] * 1 + ins[:-1, 1:] * 2 + ins[1:, 1:] * 4 + ins[1:, :-1] * 8)
    adj = {}
    def eid(side, i, j):
        return {"B": ("h", i, j), "T": ("h", i + 1, j), "L": ("v", i, j), "R": ("v", i, j + 1)}[side]
    for i, j in zip(*np.nonzero((code != 0) & (code != 15))):
        c = int(code[i, j])
        if c in (5, 10):
            centre = (f[i, j] + f[i, j + 1] + f[i + 1, j] + f[i + 1, j + 1]) / 4 > 0.5
            segs = [("B", "R"), ("T", "L")] if (c == 5) == centre else [("L", "B"), ("R", "T")]
        else:
            segs = SEG[c]
        for s1, s2 in segs:
            a, b = eid(s1, i, j), eid(s2, i, j)
            adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
    def pos(e):
        k, i, j = e
        if k == "h":
            v0, v1 = f[i, j], f[i, j + 1]; return (j + (0.5 - v0) / (v1 - v0), i)
        v0, v1 = f[i, j], f[i + 1, j]; return (j, i + (0.5 - v0) / (v1 - v0))
    loops, seen = [], set()
    for start in adj:
        if start in seen:
            continue
        loop, prev, cur = [], None, start
        while True:
            seen.add(cur); loop.append(pos(cur))
            nxt = [n for n in adj[cur] if n != prev and (n not in seen or n == start)]
            if not nxt:
                break
            prev, cur = cur, nxt[0]
            if cur == start:
                break
        if len(loop) > 3:
            loops.append(loop)
    return loops


def to_mesh(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(obj.evaluated_get(dg))
    new = bpy.data.objects.new(obj.name + "_m", me)
    new.matrix_world = obj.matrix_world
    bpy.context.collection.objects.link(new)
    bpy.data.objects.remove(obj)
    bm = bmesh.new(); bm.from_mesh(new.data)       # weld caps to walls: MANIFOLD needs closed meshes
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bad = sum(not e.is_manifold for e in bm.edges)
    bm.to_mesh(new.data); bm.free()
    print(f"MESH {new.name}: {len(new.data.vertices)} verts, non-manifold edges {bad}")
    return new


def prism_from_mask(mask, scale, ox, oy, z0, z1, name):
    loops = contours(mask)
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '2D'; cu.fill_mode = 'BOTH'
    cu.extrude = (z1 - z0) / 2
    for l in loops:
        sp = cu.splines.new('POLY'); sp.points.add(len(l) - 1); sp.use_cyclic_u = True
        for p, (x, y) in zip(sp.points, l):
            p.co = ((x - ox) * scale, (y - oy) * scale, 0, 1)
    ob = bpy.data.objects.new(name, cu); bpy.context.collection.objects.link(ob)
    ob.location.z = (z0 + z1) / 2
    m = to_mesh(ob); m.name = name
    bpy.context.view_layer.objects.active = m; m.select_set(True)
    bpy.ops.object.transform_apply(location=True); m.select_set(False)
    print(f"TRACED {name}: {len(loops)} loops")
    return m


def boolean(a, b, op):
    mod = a.modifiers.new("b", 'BOOLEAN'); mod.operation = op; mod.object = b; mod.solver = 'MANIFOLD'
    bpy.context.view_layer.objects.active = a
    nf = len(a.data.polygons)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    print(f"BOOLEAN {op} {a.name}: faces {nf} -> {len(a.data.polygons)}")
    bpy.data.objects.remove(b)


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


# ---------- build ----------
clean()
red = load_red(os.path.join(HERE, IMAGE) if not os.path.isabs(IMAGE) else IMAGE)
lab, n = label(~red)
outside = lab == lab[0, 0]
rw = ring_width(red)
# pockets lie just inside the outer ring: a full ring width from the outside, along a long stretch
# (shapes drawn on the edge, like the bow, are only one thin line away from the outside)
dist = distance_from(outside, rw + 12)
white_in = (lab > 0) & ~outside
contact = np.bincount(lab[white_in & (dist <= rw + 8)], minlength=n + 1)
too_close = np.bincount(lab[white_in & (dist < 0.6 * rw)], minlength=n + 1)
sizes = np.bincount(lab.ravel(), minlength=n + 1)
pockets = [k for k in range(1, n + 1) if k != lab[0, 0] and contact[k] >= POCKET_CONTACT and too_close[k] == 0]
# OPEN="x,y;x,y": extra white regions to cut through, picked by a point in the picture
# (pixels from the top-left corner, e.g. the inside of a letter C)
for xy in filter(None, os.environ.get("OPEN", "").split(";")):
    x, y = (int(float(c)) for c in xy.split(","))
    k = lab[red.shape[0] - 4 - y, x + 3]                 # picture is padded by 3 px and stored bottom-up
    if k and k != lab[0, 0] and k not in pockets:
        pockets.append(k); print(f"OPEN region {k} at {x},{y}: {sizes[k]} px")
# hanging-loop hole: the region closest to the top of the outline (small, above everything else)
ys, xs = np.nonzero(~outside)
top_y = ys.max()
others = [k for k in range(1, n + 1) if k != lab[0, 0] and k not in pockets]
hole_k = max(others, key=lambda k: np.nonzero(lab == k)[0].mean())
hy, hx = [a.mean() for a in np.nonzero(lab == hole_k)]
print(f"REGIONS {n}, ring {rw} px, pockets {pockets} (sizes {[int(sizes[k]) for k in pockets]}), loop hole region {hole_k}")

base_mask = ~outside & ~np.isin(lab, pockets)            # loop hole stays filled, cut round below
top_mask = (lab > 0) & ~outside & ~np.isin(lab, pockets + [hole_k])
scale = DIAMETER / (xs.max() - xs.min() + 1)
ox, oy = (xs.max() + xs.min()) / 2, (ys.max() + ys.min()) / 2
print(f"SCALE {scale:.4f} mm/px: ring {rw * scale:.2f} mm, size {DIAMETER:.1f} x {(ys.max() - ys.min() + 1) * scale:.1f} mm")

base = prism_from_mask(base_mask, scale, ox, oy, 0.0, BASE_T, "base")
top = prism_from_mask(top_mask, scale, ox, oy, BASE_T, TOP, "top")
bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=HOLE_D / 2, depth=20,
                                    location=((hx - ox) * scale, (hy - oy) * scale, 0))
boolean(base, bpy.context.active_object, 'DIFFERENCE')

solid = bpy.data.objects.new(f"{TAG}_Solid", base.data.copy()); bpy.context.collection.objects.link(solid)
# same shapes, sunk 0.5 mm into the base for a clean union
boolean(solid, prism_from_mask(top_mask, scale, ox, oy, BASE_T - 0.5, TOP, "tmp"), 'UNION')
bpy.context.view_layer.update()
if abs(solid.dimensions.z - TOP) > 0.01:
    sys.exit(f"ERROR: solid height {solid.dimensions.z:.2f} mm")

base.name, top.name = f"{TAG}_Base_RED", f"{TAG}_Top_WHITE"
for part, mat in ((base, material("Red", BASE_RGB)), (top, material("White", TOP_RGB))):
    part.data.materials.clear(); part.data.materials.append(mat)
export(solid, os.path.join(HERE, f"{TAG}.stl"))
export(base, os.path.join(HERE, f"{TAG}_BASE.stl"))
export(top, os.path.join(HERE, f"{TAG}_TOP.stl"))
solid.hide_set(True); solid.hide_render = True
for o in (base, top, solid):
    print("PART", o.name, tuple(round(d, 2) for d in o.dimensions), len(o.data.polygons), "faces")
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, f"{TAG}.blend"))
