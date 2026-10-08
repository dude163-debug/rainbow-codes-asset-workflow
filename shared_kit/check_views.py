"""Render orthographic views of a vehicle .blend at its reference drawing's scale and build a
check sheet: reference | render | overlay (red = reference lines over the faded render).

    python3 -c "import sys;sys.argv=['x','spec.json'];exec(open('check_views.py').read())"

spec.json:
{"blend": "RC_X_v001.blend", "ref": "refs/x.png", "sheet": "RC_X_v001_check.png",
 "views": [{"name": "side", "box": [x0, y0, x1, y1], "pxm": 40.0, "dir": "left",
            "anchor_px": [px, py], "anchor": [X, Y, Z]}, ...]}

dir: the side of the vehicle the drawing shows, and which way the nose points on paper:
  left / right   - side elevation seen from the vehicle's left (nose on the left of the paper)
                   or from its right (nose on the right of the paper)
  top_noseleft / top_noseright / top_noseup - plan view
  front / rear   - end elevations
anchor_px is a pixel in the drawing that shows the world point `anchor` (metres, Blender axes),
for example the ground line under the hull nose, or the turret ring centre in plan.
"""
import bpy, json, math, os, sys
from mathutils import Vector, Matrix
from PIL import Image, ImageDraw, ImageOps

spec_path = sys.argv[-1]
base = os.path.dirname(os.path.abspath(spec_path))
spec = json.load(open(spec_path))
K = spec.get('upscale', 3)

bpy.ops.wm.open_mainfile(filepath=os.path.join(base, spec['blend']))
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_object_outline = True
sh.object_outline_color = (0, 0, 0); sh.show_cavity = False
if sc.world is None: sc.world = bpy.data.worlds.new('W')
sc.world.color = (1, 1, 1)
sc.render.film_transparent = False
cam_data = bpy.data.cameras.new('CHECK'); cam_data.type = 'ORTHO'
cam_data.clip_start = .1; cam_data.clip_end = 200
cam = bpy.data.objects.new('CHECK', cam_data); sc.collection.objects.link(cam); sc.camera = cam

# (screen right, screen up) in world axes for each drawing direction.
AXES = {
    'left':          (Vector((0, -1, 0)), Vector((0, 0, 1))),
    'right':         (Vector((0, 1, 0)),  Vector((0, 0, 1))),
    'top_noseleft':  (Vector((0, -1, 0)), Vector((1, 0, 0))),
    'top_noseright': (Vector((0, 1, 0)),  Vector((-1, 0, 0))),
    'top_noseup':    (Vector((1, 0, 0)),  Vector((0, 1, 0))),
    'front':         (Vector((-1, 0, 0)), Vector((0, 0, 1))),
    'rear':          (Vector((1, 0, 0)),  Vector((0, 0, 1))),
}

ref = Image.open(os.path.join(base, spec['ref'])).convert('RGB')
rows = []
for v in spec['views']:
    x0, y0, x1, y1 = v['box']; w, h = x1-x0, y1-y0; pxm = v['pxm']
    right, up = AXES[v['dir']]
    toward = right.cross(up)                # from the scene toward the camera
    cx, cy = (x0+x1)/2, (y0+y1)/2
    ax, ay = v['anchor_px']
    centre = Vector(v['anchor']) + right*((cx-ax)/pxm) + up*((ay-cy)/pxm)
    cam.matrix_world = Matrix.Translation(centre + toward*60) @ Matrix((
        (right.x, up.x, toward.x, 0), (right.y, up.y, toward.y, 0),
        (right.z, up.z, toward.z, 0), (0, 0, 0, 1)))
    sc.render.resolution_x, sc.render.resolution_y = w*K, h*K
    cam_data.ortho_scale = max(w, h)/pxm
    path = os.path.join(base, f'_check_{spec["blend"][:-6]}_{v["name"]}.png'); sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    render = Image.open(path).convert('RGB')
    drawing = ref.crop((x0, y0, x1, y1)).resize((w*K, h*K), Image.LANCZOS)
    lines = ImageOps.invert(drawing.convert('L')).point(lambda p: 255 if p > 90 else 0)
    over = Image.blend(render, Image.new('RGB', render.size, 'white'), .45)
    over.paste(Image.new('RGB', render.size, (220, 30, 30)), (0, 0), lines)
    rows.append((v['name'], drawing, render, over))
    over.save(os.path.join(base, f'_over_{spec["blend"][:-6]}_{v["name"]}.png'))
    os.remove(path)

width = max(r[1].width for r in rows)*3 + 40
height = sum(r[1].height + 40 for r in rows)
sheet = Image.new('RGB', (width, height), 'white')
d = ImageDraw.Draw(sheet); y = 0
for name, drawing, render, over in rows:
    d.text((6, y+10), f'{name.upper()}: reference | {spec["blend"]} | overlay (red = reference lines)', fill=(0, 0, 0))
    y += 34
    for i, im in enumerate((drawing, render, over)):
        sheet.paste(im, (i*(drawing.width+20), y))
    y += drawing.height + 6
sheet.save(os.path.join(base, spec['sheet']))
print('sheet', spec['sheet'], sheet.size)
