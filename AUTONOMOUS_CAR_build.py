"""Autonomous 4WD rover: RPi 5 + LD06 LiDAR + Orbbec Astra Pro. Built in meters."""
import bpy, math, os
from mathutils import Vector

OUT = os.path.dirname(os.path.abspath(__file__))
NAME = "AUTONOMOUS_CAR"

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------- helpers ----------
def mat(name, color, metal=0.0, rough=0.5, emit=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = 4.0
    m.diffuse_color = (*color, 1)
    return m

M = {
    "plate": mat("Plate_Acrylic", (0.05, 0.05, 0.06), rough=0.25),
    "top": mat("Plate_Orange", (0.9, 0.32, 0.05), rough=0.35),
    "tire": mat("Rubber", (0.02, 0.02, 0.02), rough=0.9),
    "hub": mat("Hub_Yellow", (0.95, 0.7, 0.05), rough=0.4),
    "motor": mat("TT_Motor", (0.95, 0.75, 0.1), rough=0.5),
    "brass": mat("Brass", (0.8, 0.6, 0.25), metal=1, rough=0.3),
    "pcb": mat("PCB_Green", (0.02, 0.3, 0.08), rough=0.4),
    "pcb_red": mat("PCB_Red", (0.5, 0.03, 0.03), rough=0.4),
    "alu": mat("Aluminium", (0.75, 0.75, 0.78), metal=1, rough=0.25),
    "black": mat("Black_Plastic", (0.015, 0.015, 0.018), rough=0.35),
    "battery": mat("Battery_Blue", (0.05, 0.2, 0.6), rough=0.4),
    "glass": mat("Lens", (0.01, 0.01, 0.02), metal=0.5, rough=0.05),
    "lidar_win": mat("Lidar_Window", (0.05, 0.02, 0.02), rough=0.1),
    "white": mat("White", (0.9, 0.9, 0.9), rough=0.4),
    "led": mat("LED", (1, 1, 1), emit=(1, 0.95, 0.85)),
    "red_led": mat("LED_Red", (1, 0, 0), emit=(1, 0.05, 0.02)),
    "cable": mat("Cable", (0.1, 0.1, 0.1), rough=0.6),
}

coll = {}
def collection(name):
    c = bpy.data.collections.new(name)
    scene.collection.children.link(c)
    coll[name] = c
    return c

def place(obj, c, m=None):
    for cc in obj.users_collection:
        cc.objects.unlink(obj)
    c.objects.link(obj)
    if m:
        obj.data.materials.append(m)
    return obj

def box(name, size, loc, m, c, bevel=0.0, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        mod = o.modifiers.new("Bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 4
    return place(o, c, m)

def cyl(name, r, depth, loc, m, c, rot=(0, 0, 0), verts=48):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=loc, rotation=rot, vertices=verts)
    o = bpy.context.active_object
    o.name = name
    return place(o, c, m)

def apply_mods(o):
    bpy.context.view_layer.objects.active = o
    for mod in list(o.modifiers):
        bpy.ops.object.modifier_apply(modifier=mod.name)

def rounded_plate(name, lx, ly, t, r, loc, m, c):
    o = box(name, (lx, ly, t), loc, m, c)
    mod = o.modifiers.new("Round", "BEVEL")
    mod.affect = "VERTICES"
    mod.width = r
    mod.segments = 10
    # only vertical edges: bevel vertices then later smooth top edges
    apply_mods(o)
    e = o.modifiers.new("Edge", "BEVEL")
    e.width = 0.0008
    e.segments = 2
    return o

def drill(target, holes):
    """holes: list of (x, y, r). Through-holes along Z."""
    cutters = []
    for i, (x, y, r) in enumerate(holes):
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=0.05, location=(x, y, target.location.z), vertices=24)
        cutters.append(bpy.context.active_object)
    for cu in cutters[1:]:
        cu.select_set(True)
    bpy.context.view_layer.objects.active = cutters[0]
    for cu in cutters:
        cu.select_set(True)
    bpy.ops.object.join()
    cutter = bpy.context.active_object
    bm = target.modifiers.new("Holes", "BOOLEAN")
    bm.object = cutter
    bm.operation = "DIFFERENCE"
    # keep bevel after boolean
    target.modifiers.move(len(target.modifiers) - 1, 0)
    apply_mods(target)
    bpy.data.objects.remove(cutter)

def slot(target, x, y, lx, ly):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, target.location.z))
    cu = bpy.context.active_object
    cu.scale = (lx, ly, 0.05)
    bm = target.modifiers.new("Slot", "BOOLEAN")
    bm.object = cu
    bm.operation = "DIFFERENCE"
    target.modifiers.move(len(target.modifiers) - 1, 0)
    apply_mods(target)
    bpy.data.objects.remove(cu)

# ---------- dimensions ----------
L, W = 0.26, 0.17          # chassis plate
T = 0.004                  # plate thickness
WHEEL_R, WHEEL_W = 0.0325, 0.027
AXLE_Z = WHEEL_R
Z0 = 0.050                 # bottom plate center height
DECK = 0.060               # standoff height
Z1 = Z0 + T / 2 + DECK + T / 2   # top plate center
WX = 0.085                 # axle x-offset
WY = W / 2 + 0.020         # wheel center y

C_chassis = collection("Chassis")
C_drive = collection("Drivetrain")
C_elec = collection("Electronics")
C_sens = collection("Sensors")

# ---------- chassis plates ----------
standoffs = [(x, y) for x in (-0.115, 0.0, 0.115) for y in (-0.072, 0.072)]

bottom = rounded_plate("Bottom_Plate", L, W, T, 0.015, (0, 0, Z0), M["plate"], C_chassis)
drill(bottom, [(x, y, 0.0017) for x, y in standoffs]
      + [(sx * WX + dx, sy * 0.062, 0.0016) for sx in (-1, 1) for sy in (-1, 1) for dx in (-0.012, 0.012)])
slot(bottom, -0.02, 0, 0.03, 0.012)   # wiring pass-through

top = rounded_plate("Top_Plate", L, W, T, 0.015, (0, 0, Z1), M["top"], C_chassis)
drill(top, [(x, y, 0.0017) for x, y in standoffs]
      + [(-0.03 + dx, dy, 0.0017) for dx in (-0.02, 0.02) for dy in (-0.02, 0.02)])
slot(top, -0.03, 0.0, 0.016, 0.03)    # LiDAR cable pass-through
slot(top, 0.07, 0.0, 0.03, 0.01)      # camera USB pass-through

for i, (x, y) in enumerate(standoffs):
    s = cyl(f"Standoff_{i}", 0.003, DECK, (x, y, Z0 + T / 2 + DECK / 2), M["brass"], C_chassis, verts=6)
    for z in (Z0 - T / 2 - 0.0015, Z1 + T / 2 + 0.0015):
        cyl(f"Nut_{i}", 0.0028, 0.003, (x, y, z), M["alu"], C_chassis, verts=6)

# front bumper
bump = box("Front_Bumper", (0.012, W * 0.95, 0.022), (L / 2 + 0.004, 0, Z0 - 0.004), M["black"], C_chassis, bevel=0.004)

# ---------- drivetrain: 4x TT gear motor + wheel ----------
for sx in (-1, 1):
    for sy in (-1, 1):
        tag = ("F" if sx > 0 else "R") + ("L" if sy > 0 else "R")
        # TT motor: gearbox + motor can, axle along Y
        mx = sx * WX
        box(f"Motor_{tag}", (0.070, 0.019, 0.022), (mx - sx * 0.018, sy * 0.062, Z0 - T / 2 - 0.011),
            M["motor"], C_drive, bevel=0.002)
        cyl(f"MotorCan_{tag}", 0.0105, 0.025, (mx - sx * 0.058, sy * 0.062, Z0 - T / 2 - 0.011),
            M["alu"], C_drive, rot=(0, math.pi / 2, 0))
        cyl(f"Axle_{tag}", 0.0027, 0.03, (mx, sy * (0.062 + 0.02), AXLE_Z), M["white"], C_drive,
            rot=(math.pi / 2, 0, 0), verts=12)
        # wheel: tire (torus-ish via bevelled cylinder) + hub + spokes
        t = cyl(f"Tire_{tag}", WHEEL_R, WHEEL_W, (mx, sy * WY, AXLE_Z), M["tire"], C_drive,
                rot=(math.pi / 2, 0, 0), verts=64)
        b = t.modifiers.new("Bevel", "BEVEL"); b.width = 0.006; b.segments = 6
        # tread blocks
        for k in range(24):
            a = 2 * math.pi * k / 24
            box(f"Tread_{tag}_{k}", (0.006, WHEEL_W * 0.75, 0.003),
                (mx + math.cos(a) * WHEEL_R, sy * WY, AXLE_Z + math.sin(a) * WHEEL_R),
                M["tire"], C_drive, rot=(0, -a + math.pi / 2, 0))
        cyl(f"Hub_{tag}", WHEEL_R * 0.62, WHEEL_W + 0.002, (mx, sy * WY, AXLE_Z), M["hub"], C_drive,
            rot=(math.pi / 2, 0, 0))
        cyl(f"HubCap_{tag}", 0.006, WHEEL_W + 0.004, (mx, sy * WY, AXLE_Z), M["alu"], C_drive,
            rot=(math.pi / 2, 0, 0), verts=6)

# ---------- electronics (lower deck) ----------
zb = Z0 + T / 2
# 3S Li-ion pack (18650 x3) with holder
box("Battery_3S", (0.080, 0.062, 0.022), (0.045, 0, zb + 0.011), M["battery"], C_elec, bevel=0.003)
for i, y in enumerate((-0.0205, 0, 0.0205)):
    cyl(f"Cell_{i}", 0.0092, 0.067, (0.045, y, zb + 0.0225 + 0.0045), M["battery"], C_elec,
        rot=(0, math.pi / 2, 0))
box("Battery_Label", (0.04, 0.0625, 0.0005), (0.045, 0, zb + 0.032), M["white"], C_elec)

# Raspberry Pi 5 + active cooler
rpi_x = -0.065
box("RPi5_PCB", (0.085, 0.056, 0.0016), (rpi_x, 0, zb + 0.008), M["pcb"], C_elec)
box("RPi5_Cooler", (0.04, 0.04, 0.009), (rpi_x + 0.005, -0.004, zb + 0.0135), M["alu"], C_elec)
cyl("RPi5_Fan", 0.014, 0.002, (rpi_x + 0.005, -0.004, zb + 0.0185), M["black"], C_elec)
for i, y in enumerate((-0.018, 0.0, 0.018)):
    box(f"RPi5_USB_{i}", (0.017, 0.013, 0.015), (rpi_x - 0.036, y if i < 2 else 0.018, zb + 0.0165),
        M["alu"], C_elec)
box("RPi5_ETH", (0.021, 0.016, 0.013), (rpi_x - 0.034, -0.019, zb + 0.0155), M["alu"], C_elec)
box("RPi5_GPIO", (0.051, 0.005, 0.0085), (rpi_x + 0.003, 0.025, zb + 0.013), M["black"], C_elec)
for i, (x, y) in enumerate([(rpi_x + dx, dy) for dx in (-0.029, 0.029) for dy in (-0.0245, 0.0245)]):
    cyl(f"RPi5_Spacer_{i}", 0.0025, 0.007, (x, y, zb + 0.0035), M["brass"], C_elec, verts=6)

# Motor driver (TB6612/L298-style) + buck converter
box("Motor_Driver", (0.043, 0.043, 0.0016), (0.045, 0.0, zb + 0.040), M["pcb_red"], C_elec)
box("Driver_Heatsink", (0.023, 0.016, 0.02), (0.045, 0.0, zb + 0.051), M["black"], C_elec)
for i in range(3):
    box(f"Driver_Terminal_{i}", (0.008, 0.011, 0.01), (0.062, -0.012 + i * 0.012, zb + 0.046), M["battery"], C_elec)
for i, (x, y) in enumerate([(0.045 + dx, dy) for dx in (-0.018, 0.018) for dy in (-0.018, 0.018)]):
    cyl(f"Driver_Standoff_{i}", 0.0015, 0.016, (x, y, zb + 0.031), M["brass"], C_elec, verts=6)
box("Buck_Converter", (0.043, 0.021, 0.0016), (-0.005, -0.05, zb + 0.004), M["battery"], C_elec)
cyl("Buck_Inductor", 0.006, 0.007, (-0.005, -0.05, zb + 0.0085), M["black"], C_elec)

# power switch & headlights & tail lights
box("Power_Switch", (0.012, 0.019, 0.013), (-L / 2 + 0.012, 0.05, Z1 + T / 2 + 0.0065), M["black"], C_elec, bevel=0.0015)
box("Switch_Rocker", (0.008, 0.012, 0.004), (-L / 2 + 0.012, 0.05, Z1 + T / 2 + 0.015), M["red_led"], C_elec)
for sy in (-1, 1):
    cyl(f"Headlight_{'L' if sy > 0 else 'R'}", 0.005, 0.004, (L / 2 + 0.0105, sy * 0.055, Z0 - 0.004),
        M["led"], C_elec, rot=(0, math.pi / 2, 0))
    box(f"Taillight_{'L' if sy > 0 else 'R'}", (0.003, 0.02, 0.006), (-L / 2 + 0.0005, sy * 0.06, Z0),
        M["red_led"], C_elec)

# ---------- sensors (top deck) ----------
zt = Z1 + T / 2

# LiDAR riser tower so scan plane clears the camera
RISER_H = 0.072
lid_x = -0.03
riser = box("LiDAR_Riser", (0.05, 0.05, RISER_H), (lid_x, 0, zt + RISER_H / 2), M["black"], C_sens, bevel=0.003)
# hollow window in riser for cable
slot(riser, lid_x, 0, 0.034, 0.034)
riser_top = box("LiDAR_Riser_Plate", (0.056, 0.056, 0.003), (lid_x, 0, zt + RISER_H + 0.0015), M["black"], C_sens, bevel=0.001)

# LD06: base + rotating head with optical window
zl = zt + RISER_H + 0.003
box("LD06_Base", (0.0386, 0.0386, 0.010), (lid_x, 0, zl + 0.005), M["black"], C_sens, bevel=0.004)
cyl("LD06_Head", 0.0185, 0.017, (lid_x, 0, zl + 0.010 + 0.0085), M["black"], C_sens, verts=64)
cyl("LD06_Window", 0.0187, 0.007, (lid_x, 0, zl + 0.010 + 0.009), M["lidar_win"], C_sens, verts=64)
cyl("LD06_Cap", 0.0175, 0.002, (lid_x, 0, zl + 0.0285), M["alu"], C_sens, verts=64)

# Orbbec Astra Pro on a bracket at the front
cam_x = 0.098
CAM_STAND = 0.004
box("Camera_Bracket", (0.03, 0.06, CAM_STAND), (cam_x, 0, zt + CAM_STAND / 2), M["alu"], C_sens, bevel=0.0015)
box("Astra_Base", (0.04, 0.07, 0.006), (cam_x, 0, zt + CAM_STAND + 0.003), M["black"], C_sens, bevel=0.002)
cyl("Astra_Neck", 0.006, 0.006, (cam_x, 0, zt + CAM_STAND + 0.009), M["black"], C_sens)
zc = zt + CAM_STAND + 0.012 + 0.02
box("Astra_Body", (0.03, 0.165, 0.040), (cam_x, 0, zc), M["black"], C_sens, bevel=0.008)
box("Astra_Face", (0.001, 0.13, 0.02), (cam_x + 0.0151, 0, zc), M["glass"], C_sens)
for nm, y, r in (("IR_Projector", 0.037, 0.005), ("RGB_Lens", -0.012, 0.0045), ("IR_Camera", -0.037, 0.005)):
    cyl(f"Astra_{nm}", r, 0.002, (cam_x + 0.016, y, zc), M["glass"] if nm != "RGB_Lens" else M["alu"], C_sens,
        rot=(0, math.pi / 2, 0))
cyl("Astra_RGB_Glass", 0.003, 0.0025, (cam_x + 0.0165, -0.012, zc), M["glass"], C_sens, rot=(0, math.pi / 2, 0))

# cables (simple curves)
def cable(name, pts, r=0.0018):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = r
    cu.bevel_resolution = 4
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(pts) - 1)
    for bp, p in zip(sp.bezier_points, pts):
        bp.co = p
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    o = bpy.data.objects.new(name, cu)
    C_elec.objects.link(o)
    o.data.materials.append(M["cable"])
cable("Cable_LiDAR", [(lid_x, 0, zl + 0.002), (lid_x, 0, zt + 0.01), (lid_x, 0, zt - 0.03), (rpi_x - 0.02, 0.01, zb + 0.025), (rpi_x - 0.036, 0.018, zb + 0.017)])
cable("Cable_Camera", [(cam_x - 0.016, 0.0, zc), (0.07, 0.0, zt + 0.01), (0.07, 0.0, zt - 0.02), (rpi_x - 0.01, -0.01, zb + 0.03), (rpi_x - 0.036, -0.003, zb + 0.017)], r=0.0025)

# ---------- scene: ground, lights, camera, render ----------
bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, 0))
ground = bpy.context.active_object
ground.name = "Ground"
ground.data.materials.append(mat("Ground", (0.55, 0.57, 0.6), rough=0.8))

world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs["Color"].default_value = (0.75, 0.8, 0.88, 1)
bg.inputs["Strength"].default_value = 0.6

def light(name, kind, loc, energy, rot=(0, 0, 0), size=1.0):
    ld = bpy.data.lights.new(name, kind)
    ld.energy = energy
    if kind == "AREA":
        ld.size = size
    o = bpy.data.objects.new(name, ld)
    o.location = loc
    o.rotation_euler = rot
    scene.collection.objects.link(o)
    return o
light("Key", "AREA", (0.6, -0.5, 0.8), 120, rot=(math.radians(45), 0, math.radians(50)), size=0.8)
light("Fill", "AREA", (-0.6, 0.6, 0.5), 40, rot=(math.radians(60), 0, math.radians(-135)), size=1.0)
light("Sun", "SUN", (0, 0, 2), 2.0, rot=(math.radians(30), math.radians(10), 0))

cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 50
cam_data.clip_start = 0.01
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

def aim(loc, target):
    cam.location = loc
    d = Vector(target) - Vector(loc)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

engines = [i.identifier for i in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
for e in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT", "CYCLES"):
    if e in engines:
        try:
            scene.render.engine = e
            break
        except TypeError:
            pass
scene.render.resolution_x, scene.render.resolution_y = 1600, 1100
scene.render.image_settings.file_format = "PNG"
try:
    scene.view_settings.view_transform = "AgX"; scene.view_settings.exposure = -0.8
except TypeError:
    pass

views = {
    "preview": ((0.58, -0.48, 0.42), (0.0, 0.0, 0.08)),
    "front": ((0.62, 0.18, 0.18), (0.0, 0.0, 0.09)),
    "top": ((-0.25, -0.0, 0.85), (0.0, 0.0, 0.05)),
}
for tag, (loc, tgt) in views.items():
    aim(loc, tgt)
    scene.render.filepath = os.path.join(OUT, f"{NAME}_{tag}.png")
    bpy.ops.render.render(write_still=True)
aim(*views["preview"])

# ---------- export printable parts (mm) ----------
def export_stl(objs, path):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True, global_scale=1000, apply_modifiers=True)

parts_dir = os.path.join(OUT, f"{NAME}_print_parts")
os.makedirs(parts_dir, exist_ok=True)
for nm in ("Bottom_Plate", "Top_Plate", "LiDAR_Riser", "LiDAR_Riser_Plate", "Camera_Bracket", "Front_Bumper"):
    export_stl([bpy.data.objects[nm]], os.path.join(parts_dir, f"{nm}.stl"))

# open in colour, looking through the scene camera
for scr in bpy.data.screens:
    for area in scr.areas:
        for sp in area.spaces:
            if sp.type == "VIEW_3D":
                sp.shading.type = "MATERIAL"
                sp.overlay.show_floor = False
                sp.region_3d.view_perspective = "CAMERA"

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f"{NAME}.blend"))
print("DONE", len(bpy.data.objects), "objects")
