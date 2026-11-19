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
| RobotIA robot keyring | `ROBOTIA_ROBOT_KEYRING.blend / .stl / _preview.png`, `_Ender3S1_PETG.gcode` | Standard 60 × 25 × 5 mm plate, one colour PETG: tiny robot-head logo (antenna, ears, cut-out eyes and mouth) + "RobotIA" letters, both raised 2 mm (`ROBOT_ICON_KEYRING_build.py -- RobotIA`) |
| Saori two-colour keyring | `SAORI_2COLOR_KEYRING.blend / .stl / _BASE.stl / _LETTERS.stl / _preview.png`, `_Ender3S1_PLA_2COLOR.gcode`, `_Ender3S1_PETG_2COLOR.gcode` | Mixed-case version of SAORI. Black base with white letters, printed with a filament swap (M600) |
| Saori script keyring | `SAORI_SCRIPT_KEYRING.blend / .stl / _BASE.stl / _LETTERS.stl / _preview.png`, `_Ender3S1_PLA_2COLOR.gcode` | 60 × 30 × 5 mm, style of `newmodel.jpeg`: Lobster script letters (grey, +2 mm) on a black 3 mm base that follows the letter outline, ring tab top left. M600 swap at Z = 3.0 |
| Cesar script keyring | `CESAR_SCRIPT_KEYRING.blend / .stl / _BASE.stl / _LETTERS.stl / _preview.png`, `_Ender3S1_PLA_2COLOR.gcode` | 80 × 40 × 6 mm: 3 mm base + 3 mm Lobster letters. Fine PLA slicing, M600 swap at Z = 3.0. `_v1` is the older 3 mm thick version (2.04 + 0.96 mm) |
| Veker Express script keyring | `VEKER_EXPRESS_SCRIPT_KEYRING.blend / .stl / _BASE.stl / _LETTERS.stl / _preview.png` | 80 × 40 × 8 mm: 4 mm black base + 4 mm grey Lobster letters on two lines ("Veker" / "Express"), PLA, M600 swap at Z = 4.0. Not sliced yet |
| Estefania script keyring | `ESTEFANIA_SCRIPT_KEYRING.blend / .stl / _preview.png`, `_Ender3S1_PETG.gcode` | 70 × 25 × 5 mm, one colour PETG: 3 mm base + 2 mm Lobster letters (`SCRIPT_KEYRING_build.py -- Estefania 70 25.1 3 5`) |
| Gabriela script keyring | `GABRIELA_SCRIPT_KEYRING.blend / .stl / _preview.png`, `_Ender3S1_PETG.gcode` | 70 × 40 × 6 mm, one colour PETG: 3 mm base + 3 mm Lobster letters, stretched 1.58× in height (`SCRIPT_KEYRING_build.py -- Gabriela 70 40 3 6`) |
| Aracely script keyring | `ARACELY_SCRIPT_KEYRING.blend / .stl / _preview.png`, `_Ender3S1_PETG.gcode` | 70 × 40 × 6 mm, one colour PETG: 3 mm base + 3 mm Lobster letters, stretched 1.41× in height (`SCRIPT_KEYRING_build.py -- Aracely 70 40 3 6`) |
| Jorge script keyring | `JORGE_SCRIPT_KEYRING.blend / .stl / _preview.png`, `_Ender3S1_PETG.gcode` | 70 × 40 × 6 mm, one colour PETG: 3 mm base + 3 mm Lobster letters, stretched 1.11× in height (`SCRIPT_KEYRING_build.py -- Jorge 70 40 3 6`) |
| Saori Juliette script keyring | `SAORI_JULIETTE_SCRIPT_KEYRING.blend / .stl / _preview.png`, `_Ender3S1_PETG.gcode` | 70 × 40 × 6 mm, one colour PETG: 3 mm base + 3 mm Lobster letters on two lines ("Saori" / "Juliette"), squashed to 0.83× in height (`LINE_SPACING=0.7 blender -b --python SCRIPT_KEYRING_build.py -- "Saori\|Juliette" 70 40 3 6`; 0.55 made the lines touch) |
| RobotIA robot script keyring | `ROBOTIA_ROBOT_SCRIPT_KEYRING.blend / .stl / _BASE.stl / _LETTERS.stl / _preview.png`, `_Ender3S1_PETG.gcode` | 70 × 50 × 6 mm, one colour PETG, Saori Juliette style: robot head (cut-out eyes and mouth) above "RobotIA" in Lobster letters, 3 mm base + 3 mm relief, ring hole on top of the antenna. Not stretched (`LOGO=robot blender -b --python SCRIPT_KEYRING_build.py -- RobotIA 70 50 3 6`) |
| Verónica Fernanda script keyring | `VERONICA_FERNANDA_SCRIPT_KEYRING.blend / .stl / _BASE.stl / _LETTERS.stl / _preview.png`, `_Ender3S1_PETG.gcode` | 70 × 40 × 6 mm, one colour PETG: 3 mm base + 3 mm Lobster letters on two lines ("Verónica" / "Fernanda"), stretched 1.15× in height (`LINE_SPACING=0.7 blender -b --python SCRIPT_KEYRING_build.py -- "Verónica\|Fernanda" 70 40 3 6`). File names drop accents |
| César Christmas ornament keyring | `CESAR_ORNAMENT_KEYRING.blend / .stl / _BASE.stl / _TOP.stl / _preview.png`, `_Ender3S1_PETG_2COLOR.gcode` | Ø70 mm ornament (70 × 79.5 × 6 mm) traced from `new one.jpeg`: red 3 mm base (ring, line art, hanging loop with Ø4.5 hole) + white bow, snowflakes, "César" and Santa raised 3 mm. PETG, M600 swap at Z = 3.0 (`blender -b --python ORNAMENT_KEYRING_build.py -- "new one.jpeg" César 70 3 6`) |
| C & F heart keyring | `CF_HEART_KEYRING.blend / .stl / _preview.png`, `_Ender3S1_PLA.gcode` | Round Ø30 × 3 mm monogram with heart, made from `Gray C&F Heart Pendant CAD Diagram.png` |
| Calibration tests | `BED_LEVEL_TEST`, `TEMP_TOWER`, `RETRACTION_TEST` (`.blend / .stl / _preview.png / _Ender3S1_PLA.gcode`) | Bed level (5 squares, 1 layer), temperature tower 220→190 °C (8 mm sections), retraction 0.4→2.4 mm (6 mm sections, from 1.6 mm). Grooves mark each section. |
| Autonomous car | `AUTONOMOUS_CAR_build.py`, `AUTONOMOUS_CAR.blend`, `AUTONOMOUS_CAR_print_parts/` | 4WD rover: RPi 5, LD06 LiDAR, Orbbec Astra Pro |
| Test cylinder | `CYLINDER_D5_L15.*` | Ø5 × 15 mm |

## Tools

| File | What it does |
|---|---|
| `NAME_KEYRING_build.py` | Builds a one-colour name keyring (`.blend` + `.stl`) |
| `SAORI_KEYRING_build.py` | Example of a two-colour keyring (base and letters as separate parts) |
| `TWOCOLOR_KEYRING_build.py` | Builds a two-colour name keyring: `blender -b --python TWOCOLOR_KEYRING_build.py -- NAME` |
| `ROBOT_ICON_KEYRING_build.py` | Standard name keyring with a small robot-head logo between the hole and the text: `blender -b --python ROBOT_ICON_KEYRING_build.py -- RobotIA` → `NAME_ROBOT_KEYRING.*`. Text shrinks to fit the area right of the robot. Eyes/mouth go down to the plate, so `--color-change-z 3.0` makes them show in the base colour |
| `SCRIPT_KEYRING_build.py` | Builds a two-colour cursive name keyring with an outline-shaped base: `blender -b --python SCRIPT_KEYRING_build.py -- Saori [WIDTH HEIGHT [BASE_T TOP]]` (default 60 × 30 mm, base 3 mm, overall 5 mm). The ring tab joins the letters with a neck at least `NECK_W` = 6 mm wide, and holes left inside the base (wide gaps between letters or lines) are filled. Name is used as typed; `|` starts a second line (e.g. `"Veker|Express"`, lines centred, spacing `LINE_SPACING` = 0.55). `LOGO=robot` adds a robot head above the name with the ring hole on its antenna (→ `NAME_ROBOT_SCRIPT_KEYRING`). |
| `LOGO_KEYRING_build.py` | Builds a two-colour logo keyring from a picture (dark logo on light background): the graphic above the text is traced, the text lines are redrawn in DejaVu Sans Bold: `blender -b --python LOGO_KEYRING_build.py -- IMAGE.png NAME "BIG LINE\|small line" [WIDTH HEIGHT]` (default 84 × 44 mm). The base follows the logo outline with a ring tab; `SHAPE=rect` gives a rounded rectangle instead. To leave out text lines that are in the picture, set `IMAGE_LINES` to the picture's number of text lines |
| `ORNAMENT_KEYRING_build.py` | Builds a two-colour ornament keyring by tracing a picture of line art on white: `blender -b --python ORNAMENT_KEYRING_build.py -- IMAGE NAME [DIAMETER [BASE_T TOP]]` (default 70 mm, 3 + 3 mm). White areas along the inside of the outer ring become open holes, the other white shapes are raised in colour 2, the line art is the base; the hanging loop gets a round Ø4.5 hole. Output `NAME_ORNAMENT_KEYRING.*` |
| `HEART_MONOGRAM_KEYRING_build.py` | Builds a round monogram keyring with a heart: `blender -b --python HEART_MONOGRAM_KEYRING_build.py -- C F`. The tail trim is tuned for C, so check other initials where they meet the heart. |
| `CALIBRATION_build.py` | Builds the three calibration test models: `blender -b --python CALIBRATION_build.py` |
| `calibration_gcode.py` | Slices the tests and writes the temperature / retraction steps into the G-code: `python calibration_gcode.py [--material pla] [--retraction-temp 200]` |
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
