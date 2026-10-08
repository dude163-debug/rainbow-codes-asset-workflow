"""RAINBOW CODES vehicle kit: shared helpers for the 1:1 Warsaw Pact vehicle blockouts.

Every vehicle script in this folder does:
    import rc_vehicle_kit as K
    K.begin('RC_T64A_v001', 'T64')          # clears the scene, makes T64_ROOT > Hull, Turret
    ... K.box / K.cyl / K.prism_x / K.ring_x / K.loft / K.wheel ...
    K.finish_and_export()

RC vehicle standard (same as RC_T72_v001):
  * 1 Blender unit = 1 metre, Z up.
  * FRONT = Blender +Y (glTF/Godot -Z). +X = the vehicle's right-hand side.
  * Origin = ground level directly under the turret ring centre (the turret's yaw pivot).
  * Nodes: <TAG>_ROOT > Hull (all running gear) and <TAG>_ROOT > Turret > Gun > Muzzle.
    Hull and Turret are siblings so the game can yaw them independently.
  * One shared palette, so the game's comic shader styles every vehicle the same way.
"""
import bpy, bmesh, math, os, sys
from mathutils import Vector, Matrix

asset = None
root = hull = turret = gun = None
NAME = ''
OUT = ''

def material(name, rgb, rough=.8, metal=.1):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color = (*rgb, 1); m.use_nodes = True
    bs = m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = (*rgb, 1)
    bs.inputs['Roughness'].default_value = rough; bs.inputs['Metallic'].default_value = metal
    return m

GREEN = GREEN_D = TRACK = RUBBER = OPTIC = DRUM = GLASS = None

def begin(name, tag, out=None, turret_z=0.0):
    """Clear the scene and create <tag>_ROOT > Hull, Turret (pivot at turret_z) > Gun."""
    global asset, root, hull, turret, NAME, OUT, GREEN, GREEN_D, TRACK, RUBBER, OPTIC, DRUM, GLASS
    NAME = name
    OUT = out or os.environ.get('RC_OUT') or os.getcwd()
    for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
    for c in list(bpy.data.collections): bpy.data.collections.remove(c)
    for m in list(bpy.data.meshes): bpy.data.meshes.remove(m)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'; sc.unit_settings.scale_length = 1.0
    asset = bpy.data.collections.new(tag + '_VEHICLE'); sc.collection.children.link(asset)
    # The T-72's palette, so every Warsaw Pact vehicle reads as one family in the game.
    GREEN   = material('T72_Soviet_Green', (.215, .262, .150))
    GREEN_D = material('T72_Green_Shadow', (.150, .185, .105))
    TRACK   = material('T72_Track_Steel',  (.085, .085, .080), .9, .3)
    RUBBER  = material('T72_Rubber',       (.040, .042, .040), .95, 0)
    OPTIC   = material('T72_Optics',       (.060, .090, .100), .3, .4)
    DRUM    = material('T72_Fuel_Drum',    (.180, .215, .125))
    GLASS   = OPTIC
    root = empty(tag + '_ROOT', (0, 0, 0))
    root['rc_standard'] = '1 unit = 1 m; front +Y (Godot -Z); origin ground under turret ring'
    hull = empty('Hull', (0, 0, 0), root)
    turret = empty('Turret', (0, 0, turret_z), root)
    return root, hull, turret

def make_gun(y, z, parent=None):
    """The Gun node (elevation pivot, rotates about local X) under the turret."""
    global gun
    gun = empty('Gun', (0, y, z), parent or turret)
    gun['rotation_axis'] = 'local X (elevation)'
    return gun

# ---------------------------------------------------------------- object helpers
def link(o, parent):
    for c in list(o.users_collection): c.objects.unlink(o)
    asset.objects.link(o)
    if parent:
        bpy.context.view_layer.update()
        mw = o.matrix_world.copy(); o.parent = parent; o.matrix_world = mw
    return o

def empty(name, loc, parent=None):
    o = bpy.data.objects.new(name, None); asset.objects.link(o)
    o.location = loc; o.empty_display_size = .4
    bpy.context.view_layer.update()
    return link(o, parent)

def _finish(o, name, mat, parent, bevel=0.0):
    o.name = name; o.data.name = name
    if bevel:
        m = o.modifiers.new('edge', 'BEVEL'); m.width = bevel; m.segments = 1
        m.limit_method = 'ANGLE'
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_apply(modifier=m.name)
    o.data.materials.clear(); o.data.materials.append(mat)
    for p in o.data.polygons: p.use_smooth = False
    return link(o, parent)

def mesh_object(name, verts, faces):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    return o

def box(name, loc, size, mat=None, parent=None, bevel=.03, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object; o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return _finish(o, name, mat or GREEN, parent or hull, bevel)

def cyl(name, loc, r, depth, axis='X', mat=None, parent=None, n=12, bevel=0.0, r2=None):
    """Cylinder (or cone frustum with r2) along X, Y or Z."""
    rot = {'X': (0, math.pi/2, 0), 'Y': (-math.pi/2, 0, 0), 'Z': (0, 0, 0)}[axis]
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=n, radius=r, depth=depth, location=loc, rotation=rot)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=n, radius1=r, radius2=r2, depth=depth, location=loc, rotation=rot)
    o = bpy.context.object
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    return _finish(o, name, mat or GREEN, parent or hull, bevel)

def prism_x(name, profile, x0, x1, mat=None, parent=None, bevel=.03):
    """Extrude a side profile [(y, z), ...] across X from x0 to x1."""
    n = len(profile)
    verts = [(x0, y, z) for y, z in profile] + [(x1, y, z) for y, z in profile]
    faces = [tuple(range(n)), tuple(range(2*n-1, n-1, -1))]
    faces += [(i, (i+1) % n, n+(i+1) % n, n+i) for i in range(n)]
    return _finish(mesh_object(name, verts, faces), name, mat or GREEN, parent or hull, bevel)

def prism_y(name, profile, y0, y1, mat=None, parent=None, bevel=.03):
    """Extrude a cross-section [(x, z), ...] along Y from y0 to y1."""
    n = len(profile)
    verts = [(x, y0, z) for x, z in profile] + [(x, y1, z) for x, z in profile]
    faces = [tuple(range(n)), tuple(range(2*n-1, n-1, -1))]
    faces += [(i, (i+1) % n, n+(i+1) % n, n+i) for i in range(n)]
    return _finish(mesh_object(name, verts, faces), name, mat or GREEN, parent or hull, bevel)

def hull_solid(name, sections, mat=None, parent=None, bevel=.02):
    """Loft between cross-sections along Y: [(y, [(x, z), ...]), ...], all with the same
    vertex count, listed in the same winding. Good for boat hulls (BTR, BRDM, BMP noses)."""
    n = len(sections[0][1])
    verts = []
    for y, sec in sections:
        verts += [(x, y, z) for x, z in sec]
    faces = [tuple(range(n-1, -1, -1))]
    for s in range(len(sections)-1):
        for i in range(n):
            a, b = s*n+i, s*n+(i+1) % n
            faces.append((a, b, b+n, a+n))
    last = (len(sections)-1)*n
    faces.append(tuple(last+i for i in range(n)))
    return _finish(mesh_object(name, verts, faces), name, mat or GREEN, parent or hull, bevel)

def mirrored_section(half):
    """Build a closed cross-section from its right half [(x>=0, z), ...] listed bottom to top."""
    right = list(half)
    # Mirror every point that is off the centreline, in reverse order (top back to bottom).
    left = [(-x, z) for x, z in reversed(right) if abs(x) > 1e-6]
    return right + left

def ring_x(name, outer, thick, x0, x1, mat=None, parent=None):
    """A closed track belt: convex side profile [(y, z), ...] hollowed by `thick`."""
    n = len(outer)
    cy = sum(p[0] for p in outer)/n; cz = sum(p[1] for p in outer)/n
    def inset(i):
        a, b, c = Vector(outer[i-1]), Vector(outer[i]), Vector(outer[(i+1) % n])
        lines = []
        for p, q in ((a, b), (b, c)):
            d = (q-p).normalized(); nrm = Vector((-d.y, d.x))
            if (Vector((cy, cz))-p).dot(nrm) < 0: nrm = -nrm
            lines.append((p+nrm*thick, d))
        (p1, d1), (p2, d2) = lines
        den = d1.x*d2.y - d1.y*d2.x
        if abs(den) < 1e-6: return p1 + (b-a)
        t = ((p2.x-p1.x)*d2.y - (p2.y-p1.y)*d2.x)/den
        return p1 + d1*t
    inner = [tuple(inset(i)) for i in range(n)]
    verts = []
    for x in (x0, x1):
        verts += [(x, y, z) for y, z in outer] + [(x, y, z) for y, z in inner]
    O0, I0, O1, I1 = 0, n, 2*n, 3*n
    faces = []
    for i in range(n):
        j = (i+1) % n
        faces += [(O0+i, O0+j, O1+j, O1+i), (I0+j, I0+i, I1+i, I1+j),
                  (O0+j, O0+i, I0+i, I0+j), (O1+i, O1+j, I1+j, I1+i)]
    return _finish(mesh_object(name, verts, faces), name, mat or TRACK, parent or hull, 0)

def track_belt(side, x_centre, width, front_y, rear_y, top_z, idler, sprocket, thick=.07, name='Track'):
    """Standard track run: ground run from the first to the last road wheel, rising to the
    idler (front, (y, z, r)) and the drive sprocket (rear, (y, z, r)), flat top run."""
    iy, iz, ir = idler; sy, sz, sr = sprocket
    belt = [(iy+ir*.95, iz+ir*.15), (iy+ir*.55, top_z), (sy-sr*.55, top_z), (sy-sr*.95, sz+sr*.15),
            (sy-sr*.6, sz-sr*.9), (rear_y, .02), (front_y, .02), (iy+ir*.6, iz-ir*.9)]
    return ring_x(f'{name}_{side}', belt, thick, x_centre-width/2, x_centre+width/2, TRACK, hull)

def loft(name, rings, sides, mat=None, parent=None, bevel=0.0):
    """Rings of (z, front_r, rear_r, half_width, y_centre): a cast-turret-style solid."""
    verts = []
    for z, fr, rr, hw, yc in rings:
        for i in range(sides):
            a = 2*math.pi*i/sides
            c, s = math.cos(a), math.sin(a)
            verts.append((hw*s, yc + (fr if c > 0 else rr)*c, z))
    faces = [tuple(range(sides-1, -1, -1))]
    for r in range(len(rings)-1):
        for i in range(sides):
            a, b = r*sides+i, r*sides+(i+1) % sides
            faces.append((a, b, b+sides, a+sides))
    top = (len(rings)-1)*sides
    faces.append(tuple(top+i for i in range(sides)))
    return _finish(mesh_object(name, verts, faces), name, mat or GREEN, parent or turret, bevel)

def road_wheel(name, loc, r, width, side, spokes=False):
    """Tracked-vehicle road wheel: steel disc, rubber tyre, hub cap on the outside face."""
    s = 1 if side == 'R' else -1
    cyl(f'{name}', loc, r-.02, width, 'X', GREEN, hull, 14)
    cyl(f'{name}_Tyre', loc, r, width*.7, 'X', RUBBER, hull, 14)
    cyl(f'{name}_Hub', (loc[0]+s*(width/2+.01), loc[1], loc[2]), r*.32, .04, 'X', GREEN_D, hull, 8)

def tyre_wheel(name, loc, r, width, side, hub_r=None):
    """Wheeled-vehicle wheel: chunky rubber tyre with a recessed steel hub."""
    s = 1 if side == 'R' else -1
    cyl(f'{name}_Tyre', loc, r, width, 'X', RUBBER, hull, 18, .02)
    cyl(f'{name}_Rim', (loc[0]+s*(width/2-.02), loc[1], loc[2]), hub_r or r*.55, .06, 'X', GREEN, hull, 12)
    cyl(f'{name}_Hub', (loc[0]+s*(width/2+.01), loc[1], loc[2]), (hub_r or r*.55)*.4, .06, 'X', GREEN_D, hull, 8)

def barrel(name, y0, y1, z, r, parent=None, mat=None, n=10, x=0.0):
    """A gun tube along +Y from y0 to y1 at height z."""
    return cyl(name, (x, (y0+y1)/2, z), r, y1-y0, 'Y', mat or GREEN, parent or gun, n)

def muzzle(y, z, parent=None, x=0.0):
    """Projectile spawn point for the game (an empty named Muzzle)."""
    return empty('Muzzle', (x, y, z), parent or gun)

# ---------------------------------------------------------------- report + export
def finish_and_export(source_note=''):
    bpy.context.view_layer.update()
    lo = Vector((1e9,)*3); hi = Vector((-1e9,)*3); tris = 0
    for o in asset.objects:
        if o.type != 'MESH': continue
        for c in o.bound_box:
            v = o.matrix_world @ Vector(c); lo = Vector(map(min, lo, v)); hi = Vector(map(max, hi, v))
        tris += sum(len(p.vertices) - 2 for p in o.data.polygons)
    size = hi - lo
    root['measured_size_m'] = f'{size.x:.2f} W x {size.y:.2f} L x {size.z:.2f} H'
    root['bounds_y'] = f'{lo.y:.2f} .. {hi.y:.2f}'
    root['triangles'] = tris
    if source_note: root['source'] = source_note
    print(f'{NAME}: width {size.x:.2f} m, length {size.y:.2f} m (y {lo.y:.2f}..{hi.y:.2f}), '
          f'height {size.z:.2f} m, {tris} triangles')
    os.makedirs(OUT, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, NAME + '.blend'))
    for o in bpy.data.objects: o.select_set(o.name in asset.objects)
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, NAME + '.glb'), export_format='GLB',
                              use_selection=True, export_yup=True, export_apply=True)
    return size, lo, hi, tris
