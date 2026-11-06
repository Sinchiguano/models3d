"""Slice the calibration tests (from CALIBRATION_build.py) to Ender-3 S1 G-code.

Usage:
  python calibration_gcode.py [--material pla|petg] [--retraction-temp 205]
Writes next to this script:
  BED_LEVEL_TEST_Ender3S1_PLA.gcode       one layer: check the five squares
  TEMP_TOWER_Ender3S1_PLA.gcode           nozzle temperature changes every section (M104)
  RETRACTION_TEST_Ender3S1_PLA.gcode      retraction length changes every section
Each G-code prints a table "height -> setting" so you can read the result on the print.
Run the temperature tower first, then pass the best temperature with --retraction-temp.
"""
import argparse, os, re, subprocess

from CALIBRATION_build import (BASE_T, TEMPS, TEMP_SECTION, RETRACTS, RETRACT_SECTION)
from slice_gcode import find_prusaslicer

HERE = os.path.dirname(os.path.abspath(__file__))


def section(z, size, n):
    """Section index for a layer at height z (the base belongs to section 0)."""
    return min(n - 1, max(0, int((z - BASE_T - 1e-3) // size)))


def slice_one(name, material, extra=()):
    profile = os.path.join(HERE, "slicer_profiles", f"ender3s1_{material}.ini")
    overrides = os.path.join(HERE, "slicer_profiles", "calibration_overrides.ini")
    out = os.path.join(HERE, f"{name}_Ender3S1_{material.upper()}.gcode")
    cmd = [find_prusaslicer(), "--export-gcode", "--load", profile, "--load", overrides, *extra,
           "--center", "110,110", "--ensure-on-bed", "--output", out, os.path.join(HERE, f"{name}.stl")]
    subprocess.run(cmd, check=True, capture_output=True)
    return out


def per_section(path, size, values, edit, label):
    """Walk the layers; edit(line, value) changes lines; a note is added at each new section."""
    lines, out, z, current = open(path).read().split("\n"), [], 0.0, None
    for line in lines:
        m = re.match(r";Z:([\d.]+)", line)
        if m:
            z = float(m.group(1))
            k = section(z, size, len(values))
            if k != current and z > 0.21:   # leave the first layer alone
                current = k
                out.append(f";CALIBRATION section {k + 1}/{len(values)}: {label} {values[k]}")
                out.append(f"M117 {label} {values[k]}")
                extra = edit(None, values[k])
                if extra:
                    out.append(extra)
        new = edit(line, values[current]) if current is not None and line else line
        out.append(new)
    open(path, "w").write("\n".join(out))


def table(size, values, unit):
    rows = []
    for k, v in enumerate(values):
        lo, hi = BASE_T + k * size, BASE_T + (k + 1) * size
        rows.append(f"  section {k + 1}  {lo:5.1f} - {hi:5.1f} mm   {v} {unit}")
    return "\n  ".join(rows)


def info(path):
    return [l.strip() for l in open(path) if l.startswith(("; estimated printing time (normal", "; filament used [g]"))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--material", choices=["pla", "petg"], default="pla")
    ap.add_argument("--retraction-temp", type=int, help="nozzle temperature for the retraction test")
    a = ap.parse_args()

    bed = slice_one("BED_LEVEL_TEST", a.material)
    print("WROTE", bed, *info(bed), sep="\n  ")

    # temperature tower: M104 (no wait) at the start of each section
    tower = slice_one("TEMP_TOWER", a.material)
    def set_temp(line, t):
        if line is None:
            return f"M104 S{t} ; calibration temperature"
        # the slicer's own switch to the normal temperature would override section 1
        return "; (removed) " + line if line.startswith("M104") and "; set temperature" in line else line
    per_section(tower, TEMP_SECTION, TEMPS, set_temp, "Temp")
    print("WROTE", tower, *info(tower), "sections (bottom -> top), grooves mark each start:",
          table(TEMP_SECTION, TEMPS, "C"), sep="\n  ")

    # retraction test: rewrite every retract / unretract ("G1 E-0.8 F2400" / "G1 E.8 F2400")
    extra = ["--temperature", str(a.retraction_temp)] if a.retraction_temp else []
    retr = slice_one("RETRACTION_TEST", a.material, extra)
    pat = re.compile(r"^G1 E(-?)[\d.]+ F(\d+)$")

    def set_retract(line, length):
        if line is None:
            return None
        m = pat.match(line)
        return f"G1 E{m.group(1)}{length:.3f} F{m.group(2)}" if m else line
    per_section(retr, RETRACT_SECTION, RETRACTS, set_retract, "Retract")
    temp = a.retraction_temp or "profile"
    print("WROTE", retr, *info(retr), f"nozzle temperature: {temp}",
          "sections (bottom -> top), grooves mark each start:",
          table(RETRACT_SECTION, RETRACTS, "mm"), sep="\n  ")


if __name__ == "__main__":
    main()
