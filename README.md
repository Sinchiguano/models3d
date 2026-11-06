# models3d

My 3D models for the **Creality Ender-3 S1**. They are built with Blender Python scripts and sliced with PrusaSlicer, mostly with help from Claude Code.

This folder is synced with GitHub so I can work from any computer (Linux, Windows or macOS). Everything a model needs is inside the folder: scripts, font and slicer profiles. Nothing points to a path on one specific PC.

## What's here

| Model | Files | Notes |
|---|---|---|
| Name keyrings | `<NAME>_KEYRING.blend / .stl / _preview.png / _Ender3S1_PETG.gcode` | CESAR, JAVIER, NATHALY, SAORI, LEGENDARIO, GABRIELA, ARACELY (mixed-case versions end in `_mixedcase`) |
| CESAR keyring V1–V3 | `CESAR_KEYRING*.blend/.stl` | The first project, and the reference size for all keyrings. V3 has separate base and letter parts. |
| SAORI two-colour keyring | `SAORI_KEYRING_build.py`, `_BASE.stl`, `_LETTERS.stl`, `_2COLOR.gcode` | Black base with white letters, printed with a filament swap (M600) |
| ROBOTIA two-colour keyring | `ROBOTIA_2COLOR_KEYRING.blend / .stl / _BASE.stl / _LETTERS.stl / _preview.png`, `_Ender3S1_PETG_2COLOR.gcode` | Black base with white letters, printed with a filament swap (M600) |
| Saori two-colour keyring | `SAORI_2COLOR_KEYRING.blend / .stl / _BASE.stl / _LETTERS.stl / _preview.png`, `_Ender3S1_PLA_2COLOR.gcode`, `_Ender3S1_PETG_2COLOR.gcode` | Mixed-case version of SAORI. Black base with white letters, printed with a filament swap (M600) |
| Saori script keyring | `SAORI_SCRIPT_KEYRING.blend / .stl / _BASE.stl / _LETTERS.stl / _preview.png`, `_Ender3S1_PLA_2COLOR.gcode` | 60 × 30 × 5 mm, style of `newmodel.jpeg`: Lobster script letters (grey, +2 mm) on a black 3 mm base that follows the letter outline, ring tab top left. M600 swap at Z = 3.0 |
| Cesar script keyring | `CESAR_SCRIPT_KEYRING.blend / .stl / _BASE.stl / _LETTERS.stl / _preview.png`, `_Ender3S1_PLA_2COLOR.gcode` | 80 × 40 × 3 mm overall: 2.04 mm base + 0.96 mm Lobster letters. Fine PLA slicing, M600 swap at Z = 2.04 |
| C & F heart keyring | `CF_HEART_KEYRING.blend / .stl / _preview.png`, `_Ender3S1_PLA.gcode` | Round Ø30 × 3 mm monogram with heart, made from `Gray C&F Heart Pendant CAD Diagram.png` |
| Autonomous car | `AUTONOMOUS_CAR_build.py`, `AUTONOMOUS_CAR.blend`, `AUTONOMOUS_CAR_print_parts/` | 4WD rover: RPi 5, LD06 LiDAR, Orbbec Astra Pro |
| Test cylinder | `CYLINDER_D5_L15.*` | Ø5 × 15 mm |

## Tools

| File | What it does |
|---|---|
| `NAME_KEYRING_build.py` | Builds a one-colour name keyring (`.blend` + `.stl`) |
| `SAORI_KEYRING_build.py` | Example of a two-colour keyring (base and letters as separate parts) |
| `TWOCOLOR_KEYRING_build.py` | Builds a two-colour name keyring: `blender -b --python TWOCOLOR_KEYRING_build.py -- NAME` |
| `SCRIPT_KEYRING_build.py` | Builds a two-colour cursive name keyring with an outline-shaped base: `blender -b --python SCRIPT_KEYRING_build.py -- Saori [WIDTH HEIGHT [BASE_T TOP]]` (default 60 × 30 mm, base 3 mm, overall 5 mm). Name is used as typed. |
| `HEART_MONOGRAM_KEYRING_build.py` | Builds a round monogram keyring with a heart: `blender -b --python HEART_MONOGRAM_KEYRING_build.py -- C F`. The tail trim is tuned for C, so check other initials where they meet the heart. |
| `render_preview.py` | Renders `<model>_preview.png` from a `.blend` |
| `slice_gcode.py` | Slices an STL to Ender-3 S1 G-code with the profiles in `slicer_profiles/` and can add a colour change |
| `slicer_profiles/ender3s1_{petg,pla}.ini` | My tuned PrusaSlicer profiles |
| `slicer_profiles/keyring_overrides.ini` | Extra settings for keyrings (`slice_gcode.py --keyring`) |
| `slicer_profiles/keyring_fine_overrides.ini` | Best quality for small relief keyrings in PLA: 0.12 mm layers, slow walls, ironed tops (`--keyring --fine`) |
| `fonts/DejaVuSans-Bold.ttf` | Keyring font, included so the letters are the same on every OS |
| `fonts/LibreBaskerville-Variable.ttf` | Serif font for the monogram keyring (SIL Open Font License) |

## Standard keyring size (from CESAR V1)

- **Plate:** 60 × 25 × 3 mm, with 2 mm rounded corners and 0.5 mm rounded edges
- **Hole:** Ø4 mm, centred 5 mm from the left edge. Ø3 printed almost closed.
- **Letters:** DejaVu Sans Bold, about 9.5 mm cap height, raised 2 mm with a flat top, so the keyring is **5 mm** thick in total
- **Long names:** the plate stays 60 mm and the letters shrink to fit the 48 mm text area. For example, LEGENDARIO's letters are 5.4 mm tall.
- **Lowercase i and j:** the dot is lifted to leave a 0.6 mm gap above the stem, otherwise it prints fused
- **Two colours:** base in colour 1 and letters in colour 2, with an M600 filament swap after Z = 3.0 mm

## How to make a new keyring

Run these commands from inside this folder:

```bash
# 1. Build the model -> NAME_KEYRING.blend + NAME_KEYRING.stl
blender -b --python NAME_KEYRING_build.py -- NAME

# 2. Preview image -> NAME_KEYRING_preview.png
blender -b NAME_KEYRING.blend --python render_preview.py

# 3. G-code -> NAME_KEYRING_Ender3S1_PETG.gcode
python slice_gcode.py NAME_KEYRING.stl --material petg --keyring
#    two colours (one extruder, filament swap at the letters):
python slice_gcode.py NAME_KEYRING.stl --material petg --keyring --color-change-z 3.0
#    several models on one plate, one G-code (also writes NAME.stl; then PLATE_build.py -> NAME.blend):
python slice_gcode.py A_KEYRING.stl B_KEYRING.stl --name A_B_KEYRINGS --material petg --keyring
blender -b --python PLATE_build.py -- A_B_KEYRINGS.stl
```

The name is used exactly as typed (`Legendario` and `LEGENDARIO` give different results). File names are always in capitals.

## Printer and materials

Creality Ender-3 S1: 220 × 220 × 270 mm bed, a single 0.4 mm direct-drive nozzle and CR Touch.

| Material | Nozzle | Bed | Notes |
|---|---|---|---|
| PETG (default) | 240 °C first layer, then 225 °C | 80 °C | Tuned against stringing: 1.8 mm retract, 0.2 mm Z-hop, wipe, no ironing. Dry the filament if it still strings (about 65 °C for 4–6 h). |
| PLA | 210 °C | 60 °C | |

## Setting up a new computer

1. **Blender:** version 4.2 or newer (I use 5.2 LTS). `blender` must be on the PATH.
   - Windows: `"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"`
   - macOS: `/Applications/Blender.app/Contents/MacOS/Blender`
2. **PrusaSlicer:** version 2.8 or newer. `slice_gcode.py` finds it automatically in its usual install locations (`~/Applications/*.AppImage` on Linux, `Program Files\Prusa3D` on Windows, `/Applications` on macOS). Otherwise, set the `PRUSASLICER` environment variable to its path.
3. **Python 3:** used for `slice_gcode.py` (standard library only).

Claude Code reads its working rules for this folder from [`CLAUDE.md`](CLAUDE.md).
