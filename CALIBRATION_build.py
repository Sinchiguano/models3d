"""Calibration test models for the Ender-3 S1 (slice them with calibration_gcode.py).

Usage: blender -b --python CALIBRATION_build.py
Writes next to this script (.blend + .stl each):
  BED_LEVEL_TEST     five 25 x 25 mm squares, one layer (0.2 mm): four corners + centre
  TEMP_TOWER         two Ø6 pillars 24 mm apart on a base; one 8 mm section per temperature
  RETRACTION_TEST    two Ø6 pillars 30 mm apart on a base; one 6 mm section per retraction length
A shallow groove on each pillar marks where a new section starts, so you can count them.
Section heights must match calibration_gcode.py (it imports the constants below).
"""
import os

BASE_T = 1.6                      # base under the pillars
PILLAR_D, GROOVE_DEPTH, GROOVE_H = 6.0, 0.6, 0.8
TEMPS = [220, 215, 210, 205, 200, 195, 190]   # bottom -> top
TEMP_SECTION = 8.0
RETRACTS = [0.4, 0.8, 1.2, 1.6, 2.0, 2.4]     # mm, bottom -> top
RETRACT_SECTION = 6.0
BED_SQUARE, BED_OFFSET, BED_LAYER = 25.0, 80.0, 0.2

try:
    import bpy          # inside Blender: build the models
except ImportError:
    bpy = None          # imported by calibration_gcode.py: constants only

if bpy is not None and __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))

    def clean():
        bpy.ops.wm.read_factory_settings(use_empty=True)
        s = bpy.context.scene
        s.unit_settings.system = 'METRIC'
        s.unit_settings.scale_length = 0.001
        s.unit_settings.length_unit = 'MILLIMETERS'

    def boolean(a, b, op):
        mod = a.modifiers.new("b", 'BOOLEAN'); mod.operation = op; mod.object = b; mod.solver = 'MANIFOLD'
        bpy.context.view_layer.objects.active = a
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(b)

    def box(sx, sy, sz, x=0.0, y=0.0, z0=0.0):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z0 + sz / 2))
        o = bpy.context.active_object; o.scale = (sx, sy, sz)
        bpy.ops.object.transform_apply(scale=True)
        return o

    def cyl(d, h, x=0.0, y=0.0, z0=0.0):
        bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=d / 2, depth=h, location=(x, y, z0 + h / 2))
        return bpy.context.active_object

    def ring_cutter(x, z0):
        outer = cyl(PILLAR_D + 2, GROOVE_H, x, 0, z0)
        boolean(outer, cyl(PILLAR_D - 2 * GROOVE_DEPTH, GROOVE_H + 1, x, 0, z0 - 0.5), 'DIFFERENCE')
        return outer

    def save(obj, tag):
        obj.name = tag
        bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
        bpy.ops.wm.stl_export(filepath=os.path.join(HERE, f"{tag}.stl"), export_selected_objects=True)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, f"{tag}.blend"))
        print("BUILT", tag, tuple(round(d, 2) for d in obj.dimensions))

    def towers(tag, spacing, n, section):
        clean()
        base = box(spacing + PILLAR_D + 6, PILLAR_D + 4, BASE_T)
        for x in (-spacing / 2, spacing / 2):
            boolean(base, cyl(PILLAR_D, n * section, x, 0, BASE_T - 0.01), 'UNION')
            for k in range(1, n):  # groove just above each section boundary
                boolean(base, ring_cutter(x, BASE_T + k * section), 'DIFFERENCE')
        save(base, tag)

    # bed level: squares at the four corners and the centre of the bed
    clean()
    plate = box(BED_SQUARE, BED_SQUARE, BED_LAYER)
    for sx in (-1, 1):
        for sy in (-1, 1):
            boolean(plate, box(BED_SQUARE, BED_SQUARE, BED_LAYER, sx * BED_OFFSET, sy * BED_OFFSET), 'UNION')
    save(plate, "BED_LEVEL_TEST")

    towers("TEMP_TOWER", 24.0, len(TEMPS), TEMP_SECTION)
    towers("RETRACTION_TEST", 30.0, len(RETRACTS), RETRACT_SECTION)
