# Instructions for Claude in this folder

This is my 3D model library. It is synced with GitHub and I use it on several computers (Linux, Windows, macOS). Follow these rules on every machine so I never have to repeat them. See README.md for the full specs and commands.

## Goal and workflow
- I design models for my **Creality Ender-3 S1**: 220 × 220 × 270 mm bed, one 0.4 mm nozzle, no multi-material unit.
- Build models with **Blender Python scripts run headless** (`blender -b --python script.py`). Don't build them by hand. Keep a reusable `*_build.py` for every new kind of model.
- Every finished model gets these files, saved here (not in subfolders, except multi-part prints):
  `NAME.blend`, `NAME.stl`, `NAME_preview.png` (`render_preview.py`) and `NAME_Ender3S1_<MATERIAL>.gcode` (`slice_gcode.py`).
- After building, look at the preview image yourself, then tell me the size, print time and grams of filament.
- When I ask for "the G-code", it means sliced with `slice_gcode.py` using my profiles in `slicer_profiles/`.

## Portability rules (important)
- **No absolute paths** in scripts. Use the script's own folder: `os.path.dirname(os.path.abspath(__file__))`.
- Use only resources inside this folder: the font in `fonts/` and the profiles in `slicer_profiles/`.
  If you add something new (a font, a profile), copy it into the folder.
- Don't hardcode the Blender or PrusaSlicer locations. Find them on PATH or through the `PRUSASLICER` env var, like `slice_gcode.py` does.
- If you tune the slicer profiles, edit the `.ini` files in `slicer_profiles/` so every computer gets the change.

## Keyrings (most common request)
- "Same size as before" means the CESAR V1 standard in README.md: 60 × 25 × 3 mm plate, Ø4 hole, letters +2 mm, DejaVu Sans Bold.
  Use `NAME_KEYRING_build.py`. Long names shrink the letters; the plate stays 60 mm unless I ask otherwise.
- Ask me only for anything I haven't said: the **name** (and capitals or as typed), **one or two colours**, and **PLA or PETG** (default PETG).
- Two colours = one extruder + M600 swap: `slice_gcode.py --color-change-z 3.0`. See `SAORI_KEYRING_build.py` for separate base and letter parts.
- Don't overwrite an existing model's files: rename the old version first (e.g. `_mixedcase`, `_v1`).

## Design rules for printing
- Walls ≥ 0.8 mm and details ≥ 0.4 mm. Holes print smaller than designed, so add about 0.5–1 mm.
- Parts must fit about 215 × 215 mm; split bigger ones (like the autonomous car chassis).
- Blender gotcha: the EXACT boolean solver breaks text meshes, so use the **MANIFOLD** solver.
- Blender scene units: metric, `scale_length = 0.001`, millimetres (1 unit = 1 mm in the STL).

## Git
- Commit the sources and outputs: `.blend`, `.stl`, `.png`, `.gcode`, `.py`, `.ini`.
- Don't commit Blender backup files (`*.blend1`); `.gitignore` handles them.
- Commit or push only when I ask.
