"""Slice an STL to Ender-3 S1 G-code with PrusaSlicer, on Linux, Windows or macOS.

Usage:
  python slice_gcode.py MODEL.stl [--material petg|pla] [--color-change-z 3.0]
  python slice_gcode.py A.stl B.stl --name A_B   (several models on one plate, one G-code)
  python slice_gcode.py MODEL.stl --keyring      (adds slicer_profiles/keyring_overrides.ini: cleaner small letters)

Output: MODEL_Ender3S1_PETG.gcode (or _PLA, plus _2COLOR when --color-change-z is used),
written next to the STL. --color-change-z inserts M600 (filament swap) before the first
layer printed above that height: for two-colour keyrings use 3.0 (top of the 3 mm plate).

PrusaSlicer is looked up in this order: env var PRUSASLICER, PATH, usual install folders.
Profiles come from slicer_profiles/ in this folder, so every computer slices the same way.
"""
import argparse, glob, os, re, shutil, struct, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def find_prusaslicer():
    if os.environ.get("PRUSASLICER"):
        return os.environ["PRUSASLICER"]
    for name in ("prusa-slicer-console", "prusa-slicer", "PrusaSlicer", "prusaslicer"):
        if shutil.which(name):
            return shutil.which(name)
    home = os.path.expanduser("~")
    candidates = (
        glob.glob(os.path.join(home, "Applications", "PrusaSlicer*.AppImage"))      # Linux
        + glob.glob(r"C:\Program Files\Prusa3D\PrusaSlicer\prusa-slicer-console.exe")  # Windows
        + glob.glob("/Applications/PrusaSlicer*.app/Contents/MacOS/PrusaSlicer")    # macOS
    )
    if candidates:
        return sorted(candidates)[-1]
    sys.exit("PrusaSlicer not found. Install it or set PRUSASLICER=/path/to/prusa-slicer")


def insert_color_change(path, z):
    lines = open(path).read().split("\n")
    out, done = [], False
    for line in lines:
        m = re.match(r";Z:([\d.]+)", line)
        if not done and m and float(m.group(1)) > z + 1e-3:
            # put the swap before this layer's ;LAYER_CHANGE block
            i = max(j for j, l in enumerate(out) if l.startswith(";LAYER_CHANGE"))
            out[i:i] = [f";COLOR_CHANGE ===== Z={z} finished, load next colour =====",
                        "M117 Change filament", "M600 ; filament change: park, unload, wait for button",
                        "G92 E0"]
            done = True
        out.append(line)
    if not done:
        sys.exit(f"No layer above Z={z} found; colour change not inserted")
    open(path, "w").write("\n".join(out))


def read_stl(path):
    """Return the triangles of a binary or ASCII STL as lists of 3 (x, y, z) vertices."""
    data = open(path, "rb").read()
    n = struct.unpack("<I", data[80:84])[0] if len(data) >= 84 else -1
    if len(data) == 84 + 50 * n:  # binary
        return [[struct.unpack("<3f", data[96 + 50 * i + 12 * k:108 + 50 * i + 12 * k]) for k in range(3)]
                for i in range(n)]
    v = [tuple(map(float, m)) for m in re.findall(rb"vertex\s+(\S+)\s+(\S+)\s+(\S+)", data)]
    return [v[i:i + 3] for i in range(0, len(v), 3)]


def write_plate(stls, out, gap=10.0):
    """Lay the models out side by side along Y (gap mm apart) in one binary STL.
    PrusaSlicer's --merge crashes on some versions, so we build the plate ourselves."""
    tris, y = [], 0.0
    for path in stls:
        t = read_stl(path)
        xs = [p[0] for tri in t for p in tri]; ys = [p[1] for tri in t for p in tri]
        zs = [p[2] for tri in t for p in tri]
        dx, dy, dz = -(min(xs) + max(xs)) / 2, y - min(ys), -min(zs)
        tris += [[(p[0] + dx, p[1] + dy, p[2] + dz) for p in tri] for tri in t]
        y += max(ys) - min(ys) + gap
    with open(out, "wb") as f:
        f.write(b"plate from slice_gcode.py".ljust(80, b" ") + struct.pack("<I", len(tris)))
        for tri in tris:
            f.write(struct.pack("<3f", 0, 0, 0) + b"".join(struct.pack("<3f", *p) for p in tri) + struct.pack("<H", 0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stl", nargs="+")
    ap.add_argument("--name", help="output base name when slicing several STLs together")
    ap.add_argument("--material", choices=["petg", "pla"], default="petg")
    ap.add_argument("--color-change-z", type=float)
    ap.add_argument("--keyring", action="store_true", help="apply keyring_overrides.ini for small raised letters")
    a = ap.parse_args()
    profile = os.path.join(HERE, "slicer_profiles", f"ender3s1_{a.material}.ini")
    stls = [os.path.abspath(p) for p in a.stl]
    if len(stls) > 1 and not a.name:
        sys.exit("Several STLs: give the output name with --name, e.g. --name NATHALY_LEGENDARIO_KEYRINGS")
    base = os.path.join(os.path.dirname(stls[0]), a.name) if a.name else os.path.splitext(stls[0])[0]
    out = f"{base}_Ender3S1_{a.material.upper()}{'_2COLOR' if a.color_change_z else ''}.gcode"
    if len(stls) > 1:  # several models: one plate STL (NAME.stl) sliced as one file
        write_plate(stls, base + ".stl")
        stls = [base + ".stl"]
    overrides = ["--load", os.path.join(HERE, "slicer_profiles", "keyring_overrides.ini")] if a.keyring else []
    cmd = [find_prusaslicer(), "--export-gcode", "--load", profile, *overrides, "--center", "110,110",
           "--ensure-on-bed", "--output", out, stls[0]]
    subprocess.run(cmd, check=True)
    if a.color_change_z:
        insert_color_change(out, a.color_change_z)
    info = [l for l in open(out) if l.startswith(("; estimated printing time (normal", "; filament used [g]"))]
    print("WROTE", out, *[l.strip() for l in info], sep="\n  ")


if __name__ == "__main__":
    main()
