"""Slice an STL to Ender-3 S1 G-code with PrusaSlicer, on Linux, Windows or macOS.

Usage:
  python slice_gcode.py MODEL.stl [--material petg|pla] [--color-change-z 3.0]

Output: MODEL_Ender3S1_PETG.gcode (or _PLA, plus _2COLOR when --color-change-z is used),
written next to the STL. --color-change-z inserts M600 (filament swap) before the first
layer printed above that height: for two-colour keyrings use 3.0 (top of the 3 mm plate).

PrusaSlicer is looked up in this order: env var PRUSASLICER, PATH, usual install folders.
Profiles come from slicer_profiles/ in this folder, so every computer slices the same way.
"""
import argparse, glob, os, re, shutil, subprocess, sys

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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stl")
    ap.add_argument("--material", choices=["petg", "pla"], default="petg")
    ap.add_argument("--color-change-z", type=float)
    a = ap.parse_args()
    profile = os.path.join(HERE, "slicer_profiles", f"ender3s1_{a.material}.ini")
    base = os.path.splitext(os.path.abspath(a.stl))[0]
    out = f"{base}_Ender3S1_{a.material.upper()}{'_2COLOR' if a.color_change_z else ''}.gcode"
    cmd = [find_prusaslicer(), "--export-gcode", "--load", profile, "--center", "110,110",
           "--ensure-on-bed", "--output", out, os.path.abspath(a.stl)]
    subprocess.run(cmd, check=True)
    if a.color_change_z:
        insert_color_change(out, a.color_change_z)
    info = [l for l in open(out) if l.startswith(("; estimated printing time (normal", "; filament used [g]"))]
    print("WROTE", out, *[l.strip() for l in info], sep="\n  ")


if __name__ == "__main__":
    main()
