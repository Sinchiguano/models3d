"""Replace the name in an ornament picture (red line art on white) with a new name, for ORNAMENT_KEYRING_build.py.

Usage: blender -b --python ORNAMENT_NAME_SWAP.py -- IMAGE NEW_NAME OUT.png "x,y;x,y;..."
Example: blender -b --python ORNAMENT_NAME_SWAP.py -- "new one.jpeg" Uleam ULEAM_ORNAMENT_picture.png "637,749;540,609;362,731"

The last argument = picture points (pixels from the top left) inside every white part of the OLD name
(letters, accents, closed-in letter insides). What it does:
  1. erases those parts and their red outline (outlines of other shapes, and the ring, are kept)
  2. fits the biggest NEW_NAME (fonts/Lobster-Regular.otf) that keeps one outline width from the
     other shapes and the ring, centred where the old name was
  3. outlines it in red (OUTLINE px, like the picture) and fills small letter insides red
  4. adds red bridges so every red island (snowflakes, Santa ...) is joined to the ring again
Then build: blender -b --python ORNAMENT_KEYRING_build.py -- OUT.png NEW_NAME DIAMETER BASE_T TOP
"""
import bpy, os, sys
import numpy as np
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[sys.argv.index("--") + 1:]
IMAGE, NEW, OUT, PTS = args[0], args[1], args[2], args[3]
FONT = os.path.join(HERE, "fonts", "Lobster-Regular.otf")
THRESH = 0.6
OUTLINE = 17      # red outline width around the letters, px (the picture's strokes are ~15-17 px)
GAP = 20          # min distance from the letters to other shapes / the ring, px
ERASE = 45        # old-name red within this distance is erased
BRIDGE = 9        # bridge half width, px
RED, WHITE = (0.73, 0.04, 0.12), (1.0, 1.0, 1.0)


def dilate(m, k):
    cur = m.copy()
    for step in range(1, k + 1):
        g = cur.copy()
        g[1:] |= cur[:-1]; g[:-1] |= cur[1:]; g[:, 1:] |= cur[:, :-1]; g[:, :-1] |= cur[:, 1:]
        if step % 3 != 0:
            g[1:, 1:] |= cur[:-1, :-1]; g[:-1, :-1] |= cur[1:, 1:]; g[1:, :-1] |= cur[:-1, 1:]; g[:-1, 1:] |= cur[1:, :-1]
        cur = g
    return cur


def label(mask):
    h, w = mask.shape
    lab = np.zeros((h, w), np.int32); n = 0
    for y0 in range(h):
        for x0 in np.nonzero(mask[y0] & (lab[y0] == 0))[0]:
            if lab[y0, x0]:
                continue
            n += 1; lab[y0, x0] = n; q = deque([(y0, x0)])
            while q:
                y, x = q.popleft()
                for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                    if 0 <= yy < h and 0 <= xx < w and mask[yy, xx] and not lab[yy, xx]:
                        lab[yy, xx] = n; q.append((yy, xx))
    return lab, n


def fill_holes(m):
    """m plus every area it encloses."""
    lab, _ = label(~m)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    return ~np.isin(lab, list(border))


# ---------- picture ----------
img = bpy.data.images.load(os.path.join(HERE, IMAGE) if not os.path.isabs(IMAGE) else IMAGE)
W, H = img.size
px = np.array(img.pixels[:], dtype=np.float32).reshape(H, W, 4)[::-1]          # row 0 = top
lum = 0.3 * px[..., 0] + 0.59 * px[..., 1] + 0.11 * px[..., 2]
red = lum < THRESH
lab, n = label(~red)
outside = np.isin(lab, list(set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}))
row = red[H // 2]; i = int(np.argmax(row)); j = i
while row[j]:
    j += 1
rw = j - i                                                                        # outer ring width
ring = red & dilate(outside, rw + 2)
name_ids = {int(lab[int(p.split(",")[1]), int(p.split(",")[0])]) for p in PTS.split(";") if p}
name_ids.discard(0)
# pockets (see-through holes), same rule as ORNAMENT_KEYRING_build.py: long contact with the inside
# of the ring, never closer to the outside than 0.6 ring width
white_in = (lab > 0) & ~outside
contact = np.bincount(lab[white_in & dilate(outside, rw + 8)], minlength=n + 1)
too_close = np.bincount(lab[white_in & dilate(outside, int(0.6 * rw))], minlength=n + 1)
pocket_ids = {k for k in range(1, n + 1) if contact[k] >= 1500 and too_close[k] == 0} - name_ids
name = np.isin(lab, list(name_ids))
raised = (lab > 0) & ~outside & ~name & ~np.isin(lab, list(pocket_ids))          # bow, snowflakes, Santa ...
print("name regions", sorted(name_ids), "pockets", sorted(pocket_ids))

keep = ring | dilate(raised, OUTLINE + 2)                                         # red that must stay
erase = dilate(name, ERASE) & ~keep
red = red & ~erase
ys, xs = np.nonzero(name)
cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
print(f"old name box x {xs.min()}-{xs.max()} y {ys.min()}-{ys.max()}")

# ---------- new name as triangles ----------
cu = bpy.data.curves.new("t", 'FONT'); cu.body = NEW
cu.font = bpy.data.fonts.load(FONT); cu.align_x = 'CENTER'; cu.align_y = 'CENTER'
ob = bpy.data.objects.new("t", cu); bpy.context.scene.collection.objects.link(ob)
me = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
me.calc_loop_triangles()
V = np.array([v.co[:2] for v in me.vertices])
T = np.array([t.vertices[:] for t in me.loop_triangles])
V[:, 0] -= (V[:, 0].min() + V[:, 0].max()) / 2; V[:, 1] -= (V[:, 1].min() + V[:, 1].max()) / 2


def raster(s, ox, oy):
    m = np.zeros((H, W), bool)
    P = np.c_[ox + V[:, 0] * s, oy - V[:, 1] * s]
    for a, b, c in P[T]:
        x0, x1 = int(max(min(a[0], b[0], c[0]), 0)), int(min(max(a[0], b[0], c[0]), W - 1)) + 1
        y0, y1 = int(max(min(a[1], b[1], c[1]), 0)), int(min(max(a[1], b[1], c[1]), H - 1)) + 1
        if x1 <= x0 or y1 <= y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
        d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(d) < 1e-9:
            continue
        l1 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / d
        l2 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / d
        m[y0:y1, x0:x1] |= (l1 >= 0) & (l2 >= 0) & (l1 + l2 <= 1)
    return m


forbid = dilate(raised, GAP) | dilate(ring | outside, OUTLINE - 3)   # outline overlaps the ring a little
best = None
for oy in np.arange(cy - 40, cy + 41, 10):
    lo, hi = 5.0, 2000.0                                     # px per text unit
    for _ in range(18):
        s = (lo + hi) / 2
        if (raster(s, cx, oy) & forbid).any():
            hi = s
        else:
            lo = s
    if best is None or lo > best[0]:
        best = (lo, oy)
s, oy = best
text = raster(s, cx, oy)
ty, tx = np.nonzero(text)
print(f"new name box x {tx.min()}-{tx.max()} y {ty.min()}-{ty.max()} (scale {s:.1f})")

outline = dilate(text, OUTLINE)
red |= (fill_holes(outline) & ~text)
red &= ~text

# ---------- bridges: join every red island to the ring ----------
raised_all = raised | text
for it in range(30):
    rl, rn = label(red)
    main = set(np.unique(rl[ring])) - {0}
    if rn == len(main):
        break
    src = np.isin(rl, list(main))
    prev = np.full((H, W), -1, np.int64)
    q = deque(map(tuple, np.argwhere(src)))
    for y, x in q:
        prev[y, x] = y * W + x
    hit = None
    while q and hit is None:
        y, x = q.popleft()
        for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
            if 0 <= yy < H and 0 <= xx < W and prev[yy, xx] < 0 and not raised_all[yy, xx] and not outside[yy, xx]:
                prev[yy, xx] = y * W + x
                if red[yy, xx]:
                    hit = (yy, xx); break
                q.append((yy, xx))
    if hit is None:
        print(f"{rn - len(main)} red islands left inside raised shapes (eyes, nose ...): fine, they become grooves"); break
    path = np.zeros((H, W), bool); y, x = hit
    while not src[y, x]:
        path[y, x] = True; p = prev[y, x]; y, x = divmod(int(p), W)
    red |= dilate(path, BRIDGE) & ~raised_all & ~outside
    print(f"bridge {it + 1}: {path.sum()} px long, ends at x {hit[1]} y {hit[0]}")

# ---------- save ----------
outimg = np.ones((H, W, 4), np.float32)
outimg[red, :3] = RED
outimg[~red, :3] = WHITE
im = bpy.data.images.new("out", W, H, alpha=False)
im.pixels[:] = outimg[::-1].ravel()
im.filepath_raw = os.path.join(HERE, OUT); im.file_format = 'PNG'; im.save()
print("WROTE", OUT)
