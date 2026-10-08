"""
Niedersachsenhaus (Lower Saxon hall house) - one-shot build for Rainbow Code.

Builds the model, renders check images, saves .blend and exports .glb,
all into OUT_DIR (defaults to the folder this script sits in).

Run inside Blender (PowerShell, from the repo folder):
  & "C:\\Program Files\\Blender Foundation\\Blender 5.1\\blender.exe" --background --python buildings\\niedersachsenhaus\\build_house.py

Scale from Schnitt_Niedersachsenhaus.png: end wall 296 px = 12.0 m  ->  24.7 px/m
1 Blender unit = 1 metre. Origin = ground level, centre of footprint.
Long axis = X, width = Y, up = Z. Front long side faces -Y. Barn-door gable = -X.
"""
import bpy, bmesh, os, sys, math
from mathutils import Vector

# ---------------------------------------------------------------- dimensions
L        = 24.4    # wall length (X)
W        = 12.0    # wall width  (Y)
WALL_H   = 3.60    # side wall height
PLINTH_H = 0.30    # brick footing
WALL_T   = 0.30    # wall thickness
RIDGE_Z  = 10.40   # top of thatch at ridge
EAVE_Z   = 3.30    # thatch eave height (outer edge)
EAVE_OV  = 0.50    # eave overhang past side walls
END_OV   = 0.30    # roof overhang past gable walls
HIP_Z    = 5.00    # bottom of the small hip (half-hip / Kruppelwalm)
RIDGE_IN = 1.90    # ridge ends this far in from the gable walls
THATCH_T = 0.40    # thatch thickness
BAY      = L / 9   # post spacing on long walls (~2.7 m, from drawing)
TIMBER   = 0.20    # timber section
PROUD    = 0.05    # timber sits this far proud of the wall face

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else os.getcwd()
OUT_DIR = HERE
for i, a in enumerate(sys.argv):
    if a == "--out" and i + 1 < len(sys.argv):
        OUT_DIR = sys.argv[i + 1]
os.makedirs(OUT_DIR, exist_ok=True)
NAME = "niedersachsenhaus"

# ---------------------------------------------------------------- scene reset
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'

def make_mat(name, rgb, rough=0.9):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    m.diffuse_color = (*rgb, 1)
    return m

MATS = {
    "daub":   make_mat("Daub",   (0.72, 0.69, 0.60)),
    "brick":  make_mat("Brick",  (0.42, 0.18, 0.12)),
    "timber": make_mat("Timber", (0.16, 0.10, 0.06)),
    "thatch": make_mat("Thatch", (0.30, 0.23, 0.13)),
    "door":   make_mat("Door",   (0.24, 0.16, 0.09)),
    "glass":  make_mat("Glass",  (0.08, 0.10, 0.12), rough=0.2),
}

# one bmesh per part; everything gets joined per part at the end
parts = {k: bmesh.new() for k in ("Walls", "Plinth", "Timber", "Roof", "Doors", "Windows")}
part_mat = {"Walls": "daub", "Plinth": "brick", "Timber": "timber",
            "Roof": "thatch", "Doors": "door", "Windows": "glass"}

def box(part, x0, x1, y0, y1, z0, z1):
    bm = parts[part]
    xs, ys, zs = sorted((x0, x1)), sorted((y0, y1)), sorted((z0, z1))
    v = [bm.verts.new((xs[i], ys[j], zs[k])) for i in (0, 1) for j in (0, 1) for k in (0, 1)]
    # index = i*4 + j*2 + k
    for f in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
        bm.faces.new([v[i] for i in f])

def prism_x(part, x0, x1, poly_yz):
    """Extrude a YZ polygon (CCW seen from +X) between x0 and x1."""
    bm = parts[part]
    a = [bm.verts.new((x0, y, z)) for y, z in poly_yz]
    b = [bm.verts.new((x1, y, z)) for y, z in poly_yz]
    n = len(poly_yz)
    bm.faces.new(list(reversed(a)))
    bm.faces.new(b)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((a[i], a[j], b[j], b[i]))

# ---------------------------------------------------------------- roof geometry
hx, hy = L / 2, W / 2
slope = (RIDGE_Z - EAVE_Z) / (hy + EAVE_OV)          # rise per metre across
def roof_z(y):        # top surface of side slopes
    return RIDGE_Z - slope * abs(y)
def under_z(y):       # underside of thatch (vertical offset)
    return roof_z(y) - THATCH_T

# ---------------------------------------------------------------- plinth + walls
box("Plinth", -hx - 0.05, hx + 0.05, -hy - 0.05, hy + 0.05, 0, PLINTH_H)
# long walls
box("Walls", -hx, hx, -hy, -hy + WALL_T, PLINTH_H, WALL_H)
box("Walls", -hx, hx,  hy - WALL_T,  hy, PLINTH_H, WALL_H)
# gable walls: pentagon up into the half-hip
gable_top = HIP_Z + 0.5
gy = (RIDGE_Z - THATCH_T - gable_top) / slope        # half-width where wall meets roof underside
gable_poly = [(-hy, PLINTH_H), (hy, PLINTH_H), (hy, WALL_H),
              (gy, gable_top), (-gy, gable_top), (-hy, WALL_H)]
prism_x("Walls", -hx, -hx + WALL_T, gable_poly)
prism_x("Walls",  hx - WALL_T, hx, gable_poly)

# ---------------------------------------------------------------- thatched roof (half-hip)
bm = parts["Roof"]
xe = hx + END_OV
xr = hx - RIDGE_IN
ye = hy + EAVE_OV
yh = (RIDGE_Z - HIP_Z) / slope
V = lambda *c: bm.verts.new(c)
R1, R2 = V(-xr, 0, RIDGE_Z), V(xr, 0, RIDGE_Z)
# +Y slope
p = [V(xe, yh, HIP_Z), V(xe, ye, EAVE_Z), V(-xe, ye, EAVE_Z), V(-xe, yh, HIP_Z)]
# -Y slope
n = [V(xe, -yh, HIP_Z), V(xe, -ye, EAVE_Z), V(-xe, -ye, EAVE_Z), V(-xe, -yh, HIP_Z)]
top = [
    bm.faces.new((R1, R2, p[0], p[1], p[2], p[3])),          # back slope
    bm.faces.new((R2, R1, n[3], n[2], n[1], n[0])),          # front slope
    bm.faces.new((R2, n[0], p[0])),                          # +X hip
    bm.faces.new((R1, p[3], n[3])),                          # -X hip
]
bmesh.ops.recalc_face_normals(bm, faces=top)
ext = bmesh.ops.extrude_face_region(bm, geom=top)
nv = [g for g in ext["geom"] if isinstance(g, bmesh.types.BMVert)]
bmesh.ops.translate(bm, verts=nv, vec=(0, 0, -THATCH_T))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])

# ridge cap
box("Timber", -xr - 0.1, xr + 0.1, -0.18, 0.18, RIDGE_Z - 0.12, RIDGE_Z + 0.10)

# ---------------------------------------------------------------- timber frame
t, pr = TIMBER / 2, PROUD
def long_wall_frame(sign):
    yf = sign * (hy + pr)                 # outer face of timber
    yi = sign * (hy - 0.02)
    # posts
    for i in range(10):
        x = -hx + t + i * (L - TIMBER) / 9
        box("Timber", x - t, x + t, yi, yf, PLINTH_H, WALL_H)
    # sill, mid rail, top plate
    for z0, z1 in ((PLINTH_H, PLINTH_H + 0.2), (2.40, 2.55), (WALL_H - 0.25, WALL_H)):
        box("Timber", -hx, hx, yi, yf, z0, z1)
    # corner braces in the end bays (drawn as thin diagonals approximated by steps -> use rotated boxes)
long_wall_frame(-1)
long_wall_frame(+1)

def gable_frame(sign):
    xf = sign * (hx + pr)
    xi = sign * (hx - 0.02)
    for y in (-hy + t, -2.1, 2.1, hy - t):
        ztop = WALL_H if abs(y) > gy else min(gable_top, under_z(y))
        box("Timber", xi, xf, y - t, y + t, PLINTH_H, ztop)
    for z0, z1 in ((PLINTH_H, PLINTH_H + 0.2), (WALL_H - 0.25, WALL_H)):
        box("Timber", xi, xf, -hy, hy, z0, z1)
    box("Timber", xi, xf, -gy, gy, gable_top - 0.2, gable_top)
gable_frame(-1)
gable_frame(+1)

# diagonal braces (Kopfbaender) on long walls, as rotated boxes
brace_objs = []
def brace(x, sign, direction):
    yf = sign * (hy + pr / 2)
    me = bpy.data.meshes.new("brace")
    bmb = bmesh.new()
    bmesh.ops.create_cube(bmb, size=1.0)
    bmesh.ops.scale(bmb, vec=(1.3, 0.12, 0.14), verts=bmb.verts)
    bmesh.ops.rotate(bmb, verts=bmb.verts, cent=(0, 0, 0),
                     matrix=__import__("mathutils").Matrix.Rotation(math.radians(45 * direction), 3, 'Y'))
    bmesh.ops.translate(bmb, verts=bmb.verts, vec=(x, yf, WALL_H - 0.75))
    for v in bmb.verts:
        parts["Timber"].verts.new(v.co)
    # copy faces
    vm = {}
    off = len(parts["Timber"].verts) - len(bmb.verts)
    parts["Timber"].verts.ensure_lookup_table()
    for f in bmb.faces:
        parts["Timber"].faces.new([parts["Timber"].verts[off + v.index] for v in f.verts])
    bmb.free()

# ---------------------------------------------------------------- doors & windows
def window_long(x, sign, w=1.0, h=1.1, sill=1.0):
    yo = sign * (hy + pr + 0.02)
    yi = sign * (hy - 0.01)
    box("Windows", x - w/2, x + w/2, yi, sign * (hy + 0.02), sill, sill + h)
    f = 0.08
    for a, b_, c, d in ((x - w/2 - f, x - w/2, sill - f, sill + h + f), (x + w/2, x + w/2 + f, sill - f, sill + h + f),
                        (x - w/2, x + w/2, sill - f, sill), (x - w/2, x + w/2, sill + h, sill + h + f),
                        (x - 0.03, x + 0.03, sill, sill + h), (x - w/2, x + w/2, sill + h*0.55, sill + h*0.55 + 0.05)):
        box("Timber", a, b_, yi, yo, c, d)

def window_gable(y, sign, w=0.9, h=1.0, sill=1.1):
    xo = sign * (hx + pr + 0.02)
    xi = sign * (hx - 0.01)
    box("Windows", xi, sign * (hx + 0.02), y - w/2, y + w/2, sill, sill + h)
    f = 0.08
    for a, b_, c, d in ((y - w/2 - f, y - w/2, sill - f, sill + h + f), (y + w/2, y + w/2 + f, sill - f, sill + h + f),
                        (y - w/2, y + w/2, sill - f, sill), (y - w/2, y + w/2, sill + h, sill + h + f),
                        (y - 0.03, y + 0.03, sill, sill + h)):
        box("Timber", xi, xo, a, b_, c, d)

def door_long(x, sign, w=1.1, h=2.1):
    yi = sign * (hy - 0.01)
    box("Doors", x - w/2, x + w/2, yi, sign * (hy + 0.03), PLINTH_H, PLINTH_H + h)
    box("Timber", x - w/2 - 0.1, x + w/2 + 0.1, yi, sign * (hy + pr + 0.03), PLINTH_H + h, PLINTH_H + h + 0.15)

# front (-Y): living end on +X with door + 3 windows (from drawing), stable windows on the barn end
bay_c = lambda i: -hx + (i + 0.5) * BAY     # centre of bay i (0..8)
door_long(bay_c(5), -1)
for i in (6, 7, 8):
    window_long(bay_c(i), -1, w=1.3)
for i in range(1, 5):
    window_long(bay_c(i), -1, w=0.7, h=0.5, sill=1.6)
# back (+Y)
door_long(bay_c(4), 1)
for i in (6, 7, 8):
    window_long(bay_c(i), 1, w=1.3)
for i in range(1, 4):
    window_long(bay_c(i), 1, w=0.7, h=0.5, sill=1.6)

# big barn gate (Grote Door) on -X gable
gw, gh = 3.4, 3.9
xi, xo = -(hx - 0.01), -(hx + 0.03)
box("Doors", xi, xo, -gw/2, gw/2, PLINTH_H, PLINTH_H + gh)
box("Timber", xi, -(hx + pr + 0.04), -0.06, 0.06, PLINTH_H, PLINTH_H + gh)             # centre stile
box("Timber", xi, -(hx + pr + 0.04), -gw/2 - 0.15, gw/2 + 0.15, PLINTH_H + gh, PLINTH_H + gh + 0.25)  # lintel (Dielenbalken)
for y in (-gw/2 - 0.1, gw/2 + 0.1):
    box("Timber", xi, -(hx + pr + 0.04), y - 0.12, y + 0.12, PLINTH_H, PLINTH_H + gh)
# living gable (+X) windows
for y in (-3.6, -1.2, 1.2, 3.6):
    window_gable(y, 1)

# ---------------------------------------------------------------- build objects
root = bpy.data.objects.new("Niedersachsenhaus", None)
scene.collection.objects.link(root)
for pname, bmp in parts.items():
    bmesh.ops.remove_doubles(bmp, verts=bmp.verts, dist=1e-5)
    me = bpy.data.meshes.new(pname)
    bmp.to_mesh(me)
    bmp.free()
    me.materials.append(MATS[part_mat[pname]])
    ob = bpy.data.objects.new(pname, me)
    scene.collection.objects.link(ob)
    ob.parent = root
    # flat shading is right for this blocky style
    for poly in me.polygons:
        poly.use_smooth = False

tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in scene.objects if o.type == 'MESH')

# ---------------------------------------------------------------- save + export
blend_path = os.path.join(OUT_DIR, NAME + ".blend")
glb_path = os.path.join(OUT_DIR, NAME + ".glb")
bpy.ops.object.select_all(action='DESELECT')
for o in scene.objects:
    o.select_set(True)
bpy.ops.export_scene.gltf(filepath=glb_path, export_format='GLB', use_selection=False,
                          export_apply=True, export_yup=True)
bpy.ops.wm.save_as_mainfile(filepath=blend_path, compress=True)

# ---------------------------------------------------------------- check renders
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 24
scene.cycles.use_denoising = False
scene.view_settings.view_transform = 'Standard'
scene.render.film_transparent = False
world = bpy.data.worlds.new("World"); scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.85, 0.87, 0.9, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.8
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", 'SUN'))
sun.data.energy = 3.5
sun.rotation_euler = (math.radians(50), 0, math.radians(-35))
scene.collection.objects.link(sun)
# ground
gm = bpy.data.meshes.new("Ground"); gbm = bmesh.new()
bmesh.ops.create_grid(gbm, x_segments=1, y_segments=1, size=40); gbm.to_mesh(gm); gbm.free()
gm.materials.append(make_mat("GroundMat", (0.35, 0.40, 0.28)))
ground = bpy.data.objects.new("Ground", gm); scene.collection.objects.link(ground)

PX_PER_M = 24.7   # drawing scale, used for the comparison render
def render(name, loc, rot, ortho=None, res=(1600, 900), lens=35):
    cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
    scene.collection.objects.link(cam)
    cam.location, cam.rotation_euler = loc, [math.radians(a) for a in rot]
    if ortho:
        cam.data.type = 'ORTHO'; cam.data.ortho_scale = ortho
    else:
        cam.data.lens = lens
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.filepath = os.path.join(OUT_DIR, name + ".png")
    bpy.ops.render.render(write_still=True)
    return scene.render.filepath

ground.hide_render = True
# front elevation at drawing scale: 650 px wide = 26.3 m
front = render("check_front", (0, -40, RIDGE_Z / 2), (90, 0, 0), ortho=650 / PX_PER_M, res=(650, 325))
end = render("check_end", (-40, 0, RIDGE_Z / 2), (90, 0, -90), ortho=330 / PX_PER_M, res=(330, 325))
ground.hide_render = False
render("check_3d", (-22, -26, 12), (68, 0, -38), res=(1600, 1000), lens=30)
render("check_3d_back", (24, 22, 10), (72, 0, 135), res=(1600, 1000), lens=30)

ground.hide_render = True  # keep .blend tidy

# side-by-side with the source drawing, if it is next to this script
drawing = os.path.join(HERE, "refs", "Schnitt_Niedersachsenhaus.png")
if os.path.exists(drawing):
    try:
        from PIL import Image
        d = Image.open(drawing).convert("RGB")
        f = Image.open(front).convert("RGB"); e = Image.open(end).convert("RGB")
        sheet = Image.new("RGB", (d.width, d.height + 340), "white")
        sheet.paste(d, (0, 0))
        sheet.paste(f, (3, d.height + 5)); sheet.paste(e, (667, d.height + 5))
        sheet.save(os.path.join(OUT_DIR, "check_vs_drawing.png"))
    except ImportError:
        print("PIL not available - skipped check_vs_drawing.png")
print(f"\nDONE  tris={tris}  ->  {OUT_DIR}")
