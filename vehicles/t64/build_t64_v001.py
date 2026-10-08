"""RAINBOW CODES: T-64 blockout v001, true 1:1 scale, from the user's Object 432 3-view.

Run in Blender (Scripting tab, with rc_vehicle_kit.py in the same folder) or headless.
Drawing scale: 91.1 px/m (8,618 mm overall with gun; 2,172 mm to the cupola).
Measured: hull 6.20 m over the fenders, 8.62 m with the gun forward, 3.40 m over the
fenders, 1.92 m to the turret roof, six small road wheels (0.55 m) with return rollers,
raised front idler and rear drive sprocket, the T-64's side-skirt panels.
Origin = ground under the turret ring; the ring sits 0.76 m behind the hull's mid-length.
"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'shared_kit'))
import rc_vehicle_kit as K

K.begin('RC_T64_v001', 'T64', os.path.dirname(os.path.abspath(__file__)), turret_z=1.40)
G, D = K.GREEN, K.GREEN_D

FRONT, REAR = 3.60, -2.60
DECK = 1.40
TRACK_IN, TRACK_OUT = 1.06, 1.60
FENDER = 1.70

# ---------------------------------------------------------------- hull
K.prism_x('Hull_Body', [(FRONT-.10, .62), (FRONT, 1.02), (2.30, 1.40), (REAR+.12, DECK),
                        (REAR, 1.20), (REAR+.05, .62), (REAR+.40, .45), (FRONT-.60, .45)],
          -TRACK_IN, TRACK_IN, G)
for s in (-1, 1):
    side = 'R' if s > 0 else 'L'
    # Sponson shelf over the track, then the thin fender with its curled front.
    K.prism_x(f'Sponson_{side}', [(FRONT-.35, 1.14), (2.30, 1.38), (REAR+.05, 1.38), (REAR+.05, 1.22), (FRONT-.35, 1.10)],
              *sorted((s*TRACK_IN, s*(FENDER-.04))), G)
    K.prism_x(f'Fender_{side}', [(FRONT+.02, 1.22), (FRONT-.10, 1.36), (FRONT-.60, 1.41), (REAR, 1.41),
                                 (REAR, 1.35), (FRONT-.60, 1.35), (FRONT-.15, 1.30), (FRONT-.02, 1.16)],
              *sorted((s*(FENDER-.10), s*FENDER)), D, None, .01)
    # The T-64's hinged side-skirt panels: four plates hanging outside the track's top run.
    for k, (y0, y1) in enumerate(((2.96, 2.15), (2.12, .70), (.67, -.75), (-.78, -2.36))):
        K.box(f'Skirt_{side}_{k}', (s*(TRACK_OUT+.035), (y0+y1)/2, 1.04), (.03, y0-y1-.03, .60), D, None, .01)
    # Fender stowage bins along the deck edge (the boxes with crosses on the plan).
    for k, (y, ln) in enumerate(((2.25, .95), (.60, 1.15), (-.55, .80), (-1.70, 1.25))):
        K.box(f'Fender_Bin_{side}_{k}', (s*1.42, y, 1.48), (.50, ln, .16), D, None, .02)
    # Headlight cluster on the front fender.
    K.cyl(f'Headlight_{side}', (s*1.30, FRONT-.25, 1.50), .08, .12, 'Y', K.OPTIC, None, 8)

# Driver's hatch, splash board and engine deck with the big radiator grille.
K.cyl('Driver_Hatch', (0, 2.30, 1.30+.12), .26, .05, 'Z', D, None, 10)
K.box('Glacis_Splash_Board', (0, 2.80, 1.30), (2.00, .05, .10), D, None, .01, (math.radians(20), 0, 0))
K.box('Engine_Deck', (0, -1.55, DECK+.03), (2.05, 1.95, .06), G, None, .01)
K.box('Radiator_Grille', (0, -1.15, DECK+.07), (1.25, 1.25, .03), K.TRACK, None, .005)
for j in range(6):
    K.box(f'Engine_Louvre_{j}', (0, -2.00 - j*.09, DECK+.07), (1.25, .05, .03), D, None, .005)
K.box('Exhaust_Box', (-.85, -2.15, DECK+.10), (.30, .55, .14), D, None, .02)
# Unditching beam and fuel cylinder carried across the hull rear.
K.cyl('Unditching_Beam', (0, REAR+.05, 1.52), .11, 2.90, 'X', D, None, 8)

# ---------------------------------------------------------------- running gear
WHEEL_R, WHEEL_Z = .275, .35
wheels = (2.45, 1.68, .91, .16, -.63, -1.43)
rollers = (2.78, 2.05, 1.26, .53, -.30, -1.10)
IDLER = (3.13, 1.06, .32)
SPROCKET = (-2.03, 1.01, .38)
xm = (TRACK_IN+TRACK_OUT)/2
for s in (-1, 1):
    side = 'R' if s > 0 else 'L'
    belt = [(3.45, 1.12), (3.20, 1.36), (2.80, .98), (-1.90, .98), (-2.30, 1.30), (-2.42, 1.00),
            (-2.25, .60), (-1.60, .03), (2.70, .03), (3.25, .70)]
    K.ring_x(f'Track_{side}', belt, .07, s*xm-.27, s*xm+.27, K.TRACK)
    for k, y in enumerate(wheels):
        K.road_wheel(f'RoadWheel_{side}_{k}', (s*xm, y, WHEEL_Z), WHEEL_R, .40, side)
    for k, y in enumerate(rollers):
        K.cyl(f'Return_Roller_{side}_{k}', (s*xm, y, .85), .09, .30, 'X', D, None, 8)
    K.cyl(f'Idler_{side}', (s*xm, IDLER[0], IDLER[1]), IDLER[2], .30, 'X', D, None, 12)
    K.cyl(f'Sprocket_{side}', (s*xm, SPROCKET[0], SPROCKET[1]), SPROCKET[2], .30, 'X', D, None, 12)

# ---------------------------------------------------------------- turret (pivot on the ring)
T = K.turret
K.loft('Turret_Body', [
    (1.40, 1.45, 1.80, 1.22, 0), (1.62, 1.59, 1.85, 1.29, 0),
    (1.80, 1.30, 1.83, 1.15, 0), (1.92, .80, 1.70, .88, 0)], 16, G, T)
K.cyl('Turret_Ring_Collar', (0, 0, 1.42), 1.05, .06, 'Z', D, T, 18)
K.box('Turret_Rear_Box', (0, -1.82, 1.70), (1.50, .25, .32), D, T, .02)
# Commander's cupola (right) with the anti-aircraft MG, gunner's hatch and sight (left).
K.cyl('Commander_Cupola', (.46, -.82, 1.98), .50, .16, 'Z', G, T, 14)
K.cyl('Commander_Hatch', (.46, -.82, 2.08), .34, .05, 'Z', D, T, 12)
K.box('AA_MG_Mount', (.46, -.35, 2.12), (.12, .30, .14), D, T, .01)
K.cyl('AA_MG_Barrel', (.46, .20, 2.16), .025, .90, 'Y', K.TRACK, T, 6)
K.cyl('Gunner_Hatch', (-.60, -.95, 1.95), .30, .06, 'Z', D, T, 10)
K.box('Gunner_Sight_Housing', (-.55, .40, 1.98), (.28, .34, .20), D, T, .02)
K.box('Gunner_Sight_Glass', (-.55, .58, 1.99), (.22, .02, .10), K.OPTIC, T, .005)
K.cyl('IR_Searchlight', (.75, .95, 1.88), .17, .28, 'Y', D, T, 12)
K.cyl('IR_Searchlight_Lens', (.75, 1.10, 1.88), .14, .02, 'Y', K.OPTIC, T, 12)
K.cyl('Antenna', (-.30, -.60, 2.40), .012, 1.0, 'Z', K.TRACK, T, 4)
K.cyl('Turret_Rear_Drum', (.35, -2.20, 1.78), .17, .55, 'X', K.DRUM, T, 10)

# ---------------------------------------------------------------- gun
GUN_Y, GUN_Z = 1.45, 1.61
MUZZLE_Y = 6.02
gun = K.make_gun(GUN_Y, GUN_Z)
K.box('Gun_Mantlet', (0, GUN_Y-.05, GUN_Z), (.55, .40, .42), G, gun, .04)
K.barrel('Gun_Barrel', GUN_Y+.15, MUZZLE_Y, GUN_Z, .075)
K.barrel('Gun_Sleeve_Rear', GUN_Y+.15, GUN_Y+1.95, GUN_Z, .105)
K.barrel('Gun_Bore_Evacuator', 3.30, 4.08, GUN_Z, .125, n=12)
K.cyl('Gun_Collar', (0, 4.10, GUN_Z), .135, .06, 'Y', D, gun, 12)
K.barrel('Gun_Muzzle', MUZZLE_Y-.32, MUZZLE_Y, GUN_Z, .085, mat=D)
K.muzzle(MUZZLE_Y, GUN_Z)

K.finish_and_export('T-64 (Object 432) 3-view, 91.1 px/m; 1980 game type "T-64"')
