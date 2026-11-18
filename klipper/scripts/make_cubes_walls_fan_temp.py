#!/usr/bin/env python3
"""4 small hollow cubes, one factor changed per cube vs. the baseline (cube 1).

Cube n has n tally ridges on a small tab at its front (toward the printer's front).
  1: PA 0.11  flow 100 %   2: PA 0.14  flow 100 %   3: PA 0.175 flow 100 %
  4: PA 0.11  flow  90 %   5: PA 0.14  flow  90 %   6: PA 0.175 flow  90 %
Layout seen from the front: cubes 1-3 left->right in the front row, 4-6 in the back row.
Printed object by object (same short layer times as the tower), in shuffled order.
Constant: accel 2500, 100 mm/s walls (8.8 mm3/s), 210 C, fan 100 % from layer 4.

Usage: make_matrix_cubes.py OUT.gcode
"""
import math
import sys

OUT = sys.argv[1]
BED_T, NOZ_T = 60, 210
H, W, W1, FIL_D = 0.20, 0.44, 0.50, 1.75
SIZE, HEIGHT, BASE_LAYERS = 25.0, 15.0, 3
ACCEL = 2500
V_WALL, V_BASE, V_FIRST, V_TAB = 100, 80, 30, 40
SAFE_Z = HEIGHT + 8.0
TRAVEL_F = 200 * 60
RETRACT, RETRACT_F = 0.8, 35 * 60
FAN_FROM = 4
X0, Y0, PITCH_X, PITCH_Y = 62.0, 60.0, 110.0, 100.0   # big gaps: no head/cube collisions
TAB_W, TAB_D, TAB_GAP = 12.0, 8.0, 2.0        # tab: 12 wide, 8 deep, 2 mm in front of the wall
TAB_LAYERS = 10                               # ridge height 2 mm
# n: (walls, fan %, nozzle C)  -- PA 0.11, flow 100 % for all
CUBES = {1: (1, 100, 210),    # baseline: single wall, fan 100 %, 210 C
         2: (2, 100, 210),    # + second wall
         3: (1, 40, 210),     # less fan
         4: (1, 100, 195)}    # cooler nozzle
ORDER = [1, 2, 3, 4]
PA = 0.11
PA_CFG = 0.11

area = math.pi * (FIL_D / 2) ** 2
def em(w):
    return H * w / area

g = []
add = g.append
total_len = 0.0
state = {"retracted": False}

def extrude_to(x, y, v, w, cur):
    global total_len
    d = math.hypot(x - cur[0], y - cur[1])
    total_len += d
    add("G1 X%.3f Y%.3f E%.4f F%d" % (x, y, d * em(w), v * 60))
    return (x, y)

def loop(h, cx, cy):
    return [(cx - h, cy - h), (cx + h, cy - h), (cx + h, cy + h), (cx - h, cy + h), (cx - h, cy - h)]

def retract():
    if not state["retracted"]:
        add("G1 E-%.2f F%d" % (RETRACT, RETRACT_F))
        state["retracted"] = True

def unretract():
    if state["retracted"]:
        add("G1 E%.2f F%d" % (RETRACT, RETRACT_F))
        state["retracted"] = False

add("; Cubes: 1 baseline(1 wall,fan100,210C) 2 two walls 3 fan40 4 nozzle195C; PA 0.11. Tally ridges = cube number")
for n in sorted(CUBES):
    cx = X0 + ((n - 1) % 2) * PITCH_X
    cy = Y0 + ((n - 1) // 2) * PITCH_Y
    add("; cube %d: walls %d fan %d%% %dC at X%.0f Y%.0f" % (n, CUBES[n][0], CUBES[n][1], CUBES[n][2], cx, cy))
add("START_PRINT BED_TEMP=%d EXTRUDER_TEMP=%d" % (BED_T, NOZ_T))
add("M83")
add("G90")
add("M106 S0")
add("SET_VELOCITY_LIMIT ACCEL=%d" % ACCEL)

nlayers = int(round(HEIGHT / H))
first = True
for n in ORDER:
    walls, fan, temp = CUBES[n]
    cx = X0 + ((n - 1) % 2) * PITCH_X
    cy = Y0 + ((n - 1) // 2) * PITCH_Y
    add("; ===== cube %d  walls=%d fan=%d%% nozzle=%dC PA=%g =====" % (n, walls, fan, temp, PA))
    add("SET_PRESSURE_ADVANCE ADVANCE=%g" % PA)
    add("M221 S100")
    add("M106 S0")
    if first:
        add("G1 Z2 F3000")
        first = False
    else:
        retract()
        add("G1 Z%.1f F3000" % SAFE_Z)
    inner0 = (loop(SIZE / 2 - 1.5 * W1, cx, cy)[0] if walls == 2
              else loop(SIZE / 2 - 0.5 * W1, cx, cy)[0])
    add("G1 X%.3f Y%.3f F%d" % (inner0[0], inner0[1], TRAVEL_F))
    if temp != state.get("temp", NOZ_T):
        add("M104 S%d" % temp)
        add("M109 S%d" % temp)
    state["temp"] = temp
    add("G1 Z2 F3000")
    for layer in range(1, nlayers + 1):
        z = round(layer * H, 3)
        w = W1 if layer == 1 else W
        add("; cube %d layer %d Z=%.2f" % (n, layer, z))
        if layer == FAN_FROM:
            add("M106 S%d" % round(255 * fan / 100))
        add("G1 Z%.3f F600" % z)
        inner = loop(SIZE / 2 - 1.5 * w, cx, cy)
        outer = loop(SIZE / 2 - 0.5 * w, cx, cy)
        v_wall = V_FIRST if layer == 1 else (V_BASE if layer <= BASE_LAYERS else V_WALL)
        if walls == 2:
            add("G1 X%.3f Y%.3f F%d" % (inner[0][0], inner[0][1], TRAVEL_F))
            unretract()
            cur = inner[0]
            for p in inner[1:]:
                cur = extrude_to(p[0], p[1], v_wall, w, cur)
            add("G1 X%.3f Y%.3f F%d" % (outer[0][0], outer[0][1], TRAVEL_F))
        else:
            add("G1 X%.3f Y%.3f F%d" % (outer[0][0], outer[0][1], TRAVEL_F))
            unretract()
        cur = outer[0]
        for p in outer[1:]:
            cur = extrude_to(p[0], p[1], v_wall, w, cur)
        if layer <= BASE_LAYERS:                       # solid infill of the base
            hi = SIZE / 2 - (2.5 if walls == 2 else 1.5) * w
            k, v = 0, (V_FIRST if layer == 1 else V_BASE)
            if layer % 2 == 1:
                pos = cy - hi
                while pos <= cy + hi + 1e-6:
                    a, b = ((cx - hi, cx + hi) if k % 2 == 0 else (cx + hi, cx - hi))
                    add("G1 X%.3f Y%.3f F%d" % (a, pos, TRAVEL_F))
                    cur = extrude_to(b, pos, v, w, (a, pos))
                    pos += w; k += 1
            else:
                pos = cx - hi
                while pos <= cx + hi + 1e-6:
                    a, b = ((cy - hi, cy + hi) if k % 2 == 0 else (cy + hi, cy - hi))
                    add("G1 X%.3f Y%.3f F%d" % (pos, a, TRAVEL_F))
                    cur = extrude_to(pos, b, v, w, (pos, a))
                    pos += w; k += 1
        if layer <= TAB_LAYERS:                        # tally tab in front of the cube
            retract()
            y_hi = cy - SIZE / 2 - TAB_GAP
            y_lo = y_hi - TAB_D
            xa, xb = cx - TAB_W / 2, cx + TAB_W / 2
            v = V_FIRST if layer == 1 else V_TAB
            if layer <= BASE_LAYERS:                   # solid base of the tab
                pos, k = y_lo + w / 2, 0
                first_line = True
                while pos <= y_hi - w / 2 + 1e-6:
                    a, b = ((xa, xb) if k % 2 == 0 else (xb, xa))
                    if first_line:
                        add("G1 X%.3f Y%.3f F%d" % (a, pos, TRAVEL_F))
                        unretract()
                        first_line = False
                    else:
                        add("G1 X%.3f Y%.3f F%d" % (a, pos, TRAVEL_F))
                    extrude_to(b, pos, v, w, (a, pos))
                    pos += w; k += 1
            else:                                      # n ridges, 1.2 mm apart
                for r in range(n):
                    y = y_lo + 1.0 + 1.2 * r
                    a, b = ((xa + 1, xb - 1) if r % 2 == 0 else (xb - 1, xa + 1))
                    add("G1 X%.3f Y%.3f F%d" % (a, y, TRAVEL_F))
                    if r == 0:
                        unretract()
                    extrude_to(b, y, v, W, (a, y))
            retract()
add("; end")
retract()
add("G1 Z%.1f F3000" % (SAFE_Z + 5))
add("M221 S100")
add("SET_PRESSURE_ADVANCE ADVANCE=%g" % PA_CFG)
add("M106 S0")
add("END_PRINT")
add("SET_VELOCITY_LIMIT ACCEL=2500")
with open(OUT, "w") as f:
    f.write("\n".join(g) + "\n")
print("wrote %s: %d lines, %d cubes x %d layers, extrusion path %.0f m" % (OUT, len(g), len(ORDER), nlayers, total_len / 1000))
print("max flow walls: %.1f mm3/s" % (V_WALL * H * W))
