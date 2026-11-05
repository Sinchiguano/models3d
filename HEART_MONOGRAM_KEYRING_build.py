"""Build a round two-initial monogram keyring with a heart (from the C & F pendant drawing).

Usage: blender -b --python HEART_MONOGRAM_KEYRING_build.py -- C F
Writes CF_HEART_KEYRING.blend + .stl next to this script.

Layout (mm): Ø30 x 3 disc, rim 1.8 wide, loop with a Ø4.5 hole (prints about Ø4).
The recessed floor and the raised tops sit on 0.12 mm layer boundaries (first layer 0.24),
matching slicer_profiles/keyring_fine_overrides.ini, so both surfaces print perfectly flat.
Relief strokes stay at least 0.55 mm wide and 0.6 mm away from the rim so they survive a 0.4 mm nozzle.
"""
import bpy, bmesh, math, os, sys

OUT = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(OUT, "fonts", "LibreBaskerville-Variable.ttf")

DISC_R, THICK, EDGE = 15.0, 3.0, 0.4
RIM_W, FLOOR_Z = 1.8, 2.04          # 0.24 + 15 x 0.12
RIM_IN = DISC_R - RIM_W
LOOP_Y, LOOP_R, HOLE_R, NECK_R = 17.5, 4.25, 2.25, 1.5
MIN_RIM_GAP = 0.6
LETTER_GROW = 0.12                  # thickens the font's thin strokes
LETTER_CAP = 12.2                   # height of each letter
LETTER1_BOX = (-12.05, 3.15)        # left edge, vertical centre of the first letter
LETTER2_BOX = (11.30, -4.40)        # right edge, vertical centre of the second letter
LETTER2_SLANT = math.tan(math.radians(12))
HEART_W, HEART_STROKE, HEART_CENTRE = 7.6, 0.9, (-0.3, 0.3)

# The drawing is 22.17 pixels per mm, with the disc centre at pixel (557.5, 562)
def px(x, y):
    return (x - 557.5) / 22.17, (562 - y) / 22.17

# Swash centre lines: (pixel x, pixel y, stroke width in mm)
SWASH_TOP = [(580, 462, .55), (610, 425, .70), (650, 392, .90), (695, 373, 1.05), (735, 382, 1.20),
             (772, 415, 1.20), (800, 470, 1.05), (811, 515, .85), (806, 548, .60)]
SWASH_LOW = [(550, 613, .70), (541, 630, .70), (522, 643, .75), (480, 668, .95), (440, 692, 1.20), (405, 722, 1.40), (378, 750, 1.30),
             (345, 790, 1.00)]
# Where a letter's tail runs into the heart, trim the leftover under it so the tail tapers in cleanly (mm)
LETTER_TRIM = {"C": [(-3.10, -2.15), (-2.55, -1.66), (-1.80, -1.16), (-1.20, -0.70), (0.50, -0.70), (0.50, -3.6), (-3.10, -3.6)]}


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


def boolean(a, b, op, keep=False):
    mod = a.modifiers.new("b", 'BOOLEAN'); mod.operation = op; mod.object = b; mod.solver = 'MANIFOLD'
    bpy.context.view_layer.objects.active = a
    bpy.ops.object.modifier_apply(modifier=mod.name)
    if not keep:
        bpy.data.objects.remove(b)


def curve_solid(name, loops, z0, z1, bevel=0.0):
    """Extrude closed 2D polygons from z0 to z1. Nested loops become holes."""
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '2D'; cu.fill_mode = 'BOTH'
    cu.extrude = (z1 - z0) / 2 - bevel
    cu.bevel_depth = bevel; cu.bevel_resolution = 3 if bevel else 0
    for loop in loops:
        sp = cu.splines.new('POLY'); sp.points.add(len(loop) - 1); sp.use_cyclic_u = True
        for p, (x, y) in zip(sp.points, loop):
            p.co = (x, y, 0, 1)
    ob = bpy.data.objects.new(name, cu); bpy.context.collection.objects.link(ob)
    ob.location.z = (z0 + z1) / 2
    return to_mesh(ob)


def circle(cx, cy, r, n=128):
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def arc(cx, cy, r, a0, a1, n):
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def body_outline(grow=0.0):
    """Disc + loop joined by concave fillets, counter-clockwise from the right fillet. grow<0 shrinks it."""
    R1, R2, r = DISC_R + grow, LOOP_R + grow, NECK_R - grow
    d = LOOP_Y
    # fillet centre (fx, fy) is R1+r from the disc centre and R2+r from the loop centre
    fy = ((R1 + r) ** 2 - (R2 + r) ** 2 + d ** 2) / (2 * d)
    fx = math.sqrt((R1 + r) ** 2 - fy ** 2)
    a_disc = math.atan2(fy, fx)                  # disc-side tangent direction
    a_loop = math.atan2(fy - d, fx)              # loop-side tangent direction
    pts = []
    # disc: from the right tangent, clockwise under the bottom, to the left tangent
    pts += arc(0, 0, R1, a_disc, a_disc - (2 * math.pi - (math.pi - 2 * a_disc)), 160)
    # left fillet (concave, mirrored)
    pts += arc(-fx, fy, r, -a_disc, -a_disc - 0 + (a_disc - a_loop) * 1, 10)[1:]
    # loop: from the left tangent over the top to the right tangent
    pts += arc(0, d, R2, math.pi - a_loop, a_loop, 64)[1:]
    # right fillet back to the start
    pts += arc(fx, fy, r, math.pi + a_loop, math.pi + a_disc, 10)[1:-1]
    return pts


def catmull(pts, per_seg=10):
    """Smooth curve through (x, y, w) points."""
    p = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for j in range(per_seg):
            t = j / per_seg
            out.append(tuple(0.5 * (2 * p1[k] + (p2[k] - p0[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t * t
                                    + (3 * p1[k] - p0[k] - 3 * p2[k] + p3[k]) * t ** 3) for k in range(3)))
    out.append(tuple(pts[-1]))
    return out


def stroke(pixels, keep_off_rim):
    """Variable-width stroke polygon along a smooth centre line."""
    pts = [px(x, y) + (w,) for x, y, w in pixels]
    line = catmull(pts)
    if keep_off_rim:
        for x, y, w in line:
            if math.hypot(x, y) + w / 2 > RIM_IN - MIN_RIM_GAP + 1e-6:
                sys.exit(f"ERROR swash at ({x:.2f}, {y:.2f}) is closer than {MIN_RIM_GAP} mm to the rim")
    left, right = [], []
    for i, (x, y, w) in enumerate(line):
        ax, ay, _ = line[max(i - 1, 0)]; bx, by, _ = line[min(i + 1, len(line) - 1)]
        tx, ty = bx - ax, by - ay; n = math.hypot(tx, ty) or 1
        left.append((x - ty / n * w / 2, y + tx / n * w / 2))
        right.append((x + ty / n * w / 2, y - tx / n * w / 2))
    return left + right[::-1]


def inset(poly, d):
    """Polygon offset inwards by d: even stroke width, loops at the corners dropped."""
    area = sum(poly[i - 1][0] * p[1] - p[0] * poly[i - 1][1] for i, p in enumerate(poly))
    sign = 1 if area > 0 else -1
    def dist(q):
        best = 1e9
        for i, b in enumerate(poly):
            a = poly[i - 1]; ex, ey = b[0] - a[0], b[1] - a[1]
            t = max(0, min(1, ((q[0] - a[0]) * ex + (q[1] - a[1]) * ey) / (ex * ex + ey * ey or 1)))
            best = min(best, math.hypot(q[0] - a[0] - t * ex, q[1] - a[1] - t * ey))
        return best
    out = []
    for i, p in enumerate(poly):
        a, b = poly[i - 1], poly[(i + 1) % len(poly)]
        tx, ty = b[0] - a[0], b[1] - a[1]; n = math.hypot(tx, ty) or 1
        q = (p[0] - sign * ty / n * d, p[1] + sign * tx / n * d)
        if dist(q) >= d * 0.995:
            out.append(q)
    return out


def heart(width, n=240):
    """Heart outline of the given width, centred on HEART_CENTRE."""
    raw = [(16 * math.sin(t) ** 3, 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
           for t in (2 * math.pi * i / n for i in range(n))]
    k = width / 32
    ys = [p[1] for p in raw]; my = (min(ys) + max(ys)) / 2
    return [(HEART_CENTRE[0] + x * k, HEART_CENTRE[1] + (y - my) * k) for x, y in raw]


def letter(ch, right=None, left=None, cy=0.0, slant=0.0):
    def make(size):
        cu = bpy.data.curves.new("glyph", 'FONT'); cu.body = ch
        cu.font = bpy.data.fonts.load(FONT, check_existing=True); cu.size = size
        cu.resolution_u = 14; cu.bevel_depth = LETTER_GROW; cu.bevel_resolution = 1
        cu.extrude = 1.0
        ob = bpy.data.objects.new("glyph", cu); bpy.context.collection.objects.link(ob)
        ob.location.z = THICK - cu.extrude     # widest outline reaches exactly the top
        return to_mesh(ob)
    probe = make(17.0)
    h = max(v.co.y for v in probe.data.vertices) - min(v.co.y for v in probe.data.vertices)
    bpy.data.objects.remove(probe)
    g = make(17.0 * LETTER_CAP / h)
    # flat top
    bpy.ops.mesh.primitive_cube_add(size=200, location=(0, 0, THICK + 100))
    boolean(g, bpy.context.active_object, 'DIFFERENCE')
    vs = g.data.vertices
    y0 = min(v.co.y for v in vs); y1 = max(v.co.y for v in vs)
    for v in vs:
        v.co.y += cy - (y0 + y1) / 2
        v.co.x += slant * (v.co.y - cy)
    x0 = min(v.co.x for v in vs); x1 = max(v.co.x for v in vs)
    dx = (left - x0) if left is not None else (right - x1)
    for v in vs:
        v.co.x += dx
    return g


def remove_specks(ob, size=0.5):
    """Delete loose fragments smaller than size (mm) left behind by the booleans. Too small to print."""
    bm = bmesh.new(); bm.from_mesh(ob.data)
    seen, removed = set(), 0
    for start in list(bm.verts):
        if start in seen:
            continue
        seen.add(start); stack = [start]; island = []
        while stack:
            v = stack.pop(); island.append(v)
            for e in v.link_edges:
                o = e.other_vert(v)
                if o not in seen:
                    seen.add(o); stack.append(o)
        xs = [v.co.x for v in island]; ys = [v.co.y for v in island]
        if max(max(xs) - min(xs), max(ys) - min(ys)) < size:
            bmesh.ops.delete(bm, geom=island, context='VERTS'); removed += 1
    bm.to_mesh(ob.data); bm.free()
    return removed


def check_solid(ob):
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bad = sum(1 for e in bm.edges if not e.is_manifold)
    shells, seen = [], set()
    for start in bm.verts:
        if start in seen:
            continue
        seen.add(start); stack = [start]; pts = []
        while stack:
            v = stack.pop(); pts.append(v.co.copy())
            for e in v.link_edges:
                o = e.other_vert(v)
                if o not in seen:
                    seen.add(o); stack.append(o)
        shells.append(tuple(round(f(p[k] for p in pts), 2) for k in range(3) for f in (min, max)))
    bm.free()
    return bad, shells


def build(a, b):
    clean()
    tag = f"{a}{b}".upper()
    body = curve_solid("body", [body_outline(-EDGE), circle(0, LOOP_Y, HOLE_R + EDGE, 64)], 0, THICK, bevel=EDGE)
    floor_cut = curve_solid("floor_cut", [circle(0, 0, RIM_IN, 180)], FLOOR_Z, THICK + 2)
    boolean(body, floor_cut, 'DIFFERENCE')

    z0, z1 = FLOOR_Z - 0.3, THICK
    heart_out = heart(HEART_W)
    heart_in = inset(heart_out, HEART_STROKE)
    heart_mask = curve_solid("heart_mask", [heart_out], 0.5, THICK + 2)

    parts = []
    for ch, g in ((a, letter(a, left=LETTER1_BOX[0], cy=LETTER1_BOX[1])),
                  (b, letter(b, right=LETTER2_BOX[0], cy=LETTER2_BOX[1], slant=LETTER2_SLANT))):
        if ch == a and ch in LETTER_TRIM:
            boolean(g, curve_solid("trim", [LETTER_TRIM[ch]], 0.5, THICK + 2), 'DIFFERENCE')
        boolean(g, heart_mask, 'DIFFERENCE', keep=True)   # letters stop at the heart: its centre stays clear
        parts.append(g)
    bpy.data.objects.remove(heart_mask)
    low = curve_solid("swash_low", [stroke(SWASH_LOW, False)], z0, z1)
    boolean(low, curve_solid("heart_mask2", [heart_in], 0.5, THICK + 2), 'DIFFERENCE')
    parts += [curve_solid("swash_top", [stroke(SWASH_TOP, True)], z0, z1), low,
              curve_solid("heart", [heart_out, heart_in], z0, z1)]
    for p in parts:
        boolean(body, p, 'UNION')

    if abs(body.dimensions.z - THICK) > 0.01:
        sys.exit(f"ERROR {tag}: height {body.dimensions.z:.2f} mm, expected {THICK} mm")
    specks = remove_specks(body)
    bad, shells = check_solid(body)
    if bad or len(shells) != 1:
        sys.exit(f"ERROR {tag}: {bad} non-manifold edges, {len(shells)} separate pieces: {shells}")
    body.name = f"{tag}_Heart_Keychain"
    mat = bpy.data.materials.new("PLA"); mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.30, 0.30, 0.32, 1)
    body.data.materials.clear()  # curve conversion leaves an empty slot 0, which all faces use
    body.data.materials.append(mat)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f"{tag}_HEART_KEYRING.blend"))
    bpy.ops.object.select_all(action='DESELECT'); body.select_set(True)
    bpy.ops.wm.stl_export(filepath=os.path.join(OUT, f"{tag}_HEART_KEYRING.stl"), export_selected_objects=True,
                          global_scale=1.0)
    print("BUILT", tag, "dims", tuple(round(d, 2) for d in body.dimensions), "bad edges", bad, "pieces", len(shells), "specks removed", specks)


argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["C", "F"]
if len(argv) != 2:
    sys.exit("Give exactly two initials, e.g. -- C F")
build(*argv)
