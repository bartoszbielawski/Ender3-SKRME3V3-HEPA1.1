#!/usr/bin/env python3
"""Two realistic test cubes: 2 walls, 15 % zigzag infill, 3 solid bottom / 4 solid top layers.

Cube 1 (1 tally ridge, left):  outer wall 60 mm/s, ACCEL 1500
Cube 2 (2 tally ridges, right): outer wall 100 mm/s, ACCEL 2500
Both: inner wall 100 mm/s, infill 100 mm/s, SCV 5, 210 C, PA 0.11, flow 100 %, fan 100 % from layer 4.
Printed object by object, big gap between the cubes.

Usage: make_cubes_2wall_infill.py OUT.gcode
"""
import math
import sys

OUT = sys.argv[1]
BED_T, NOZ_T = 60, 210
H, W, W1, FIL_D = 0.20, 0.44, 0.50, 1.75
SIZE, HEIGHT = 30.0, 20.0
BASE_LAYERS, TOP_LAYERS = 3, 4
V_FIRST, V_BASE, V_INNER, V_INFILL, V_TOP, V_TAB = 30, 80, 100, 100, 60, 40
INFILL = 0.15
SAFE_Z = HEIGHT + 8.0
TRAVEL_F = 200 * 60
RETRACT, RETRACT_F = 0.8, 35 * 60
FAN_FROM = 4
TAB_W, TAB_D, TAB_GAP, TAB_LAYERS = 12.0, 8.0, 2.0, 10
PA = 0.11
CUBES = {1: (60, 1500, 5), 2: (100, 2500, 5)}      # n: (outer wall mm/s, accel, scv)
POS = {1: (70.0, 105.0), 2: (165.0, 105.0)}
ORDER = [1, 2]

area = math.pi * (FIL_D / 2) ** 2
def em(w):
    return H * w / area

g = []
add = g.append
state = {"retracted": False}
total = [0.0]

def extrude_to(x, y, v, w, cur):
    d = math.hypot(x - cur[0], y - cur[1])
    total[0] += d
    add("G1 X%.3f Y%.3f E%.4f F%d" % (x, y, d * em(w), v * 60))
    return (x, y)

def move(x, y):
    add("G1 X%.3f Y%.3f F%d" % (x, y, TRAVEL_F))
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

def solid_fill(cx, cy, hi, w, v, layer, cur):
    k = 0
    if layer % 2 == 1:                       # lines along X, stepping Y
        pos = cy - hi
        while pos <= cy + hi + 1e-6:
            a, b = ((cx - hi, cx + hi) if k % 2 == 0 else (cx + hi, cx - hi))
            move(a, pos)
            cur = extrude_to(b, pos, v, w, (a, pos))
            pos += w; k += 1
    else:                                    # lines along Y, stepping X
        pos = cx - hi
        while pos <= cx + hi + 1e-6:
            a, b = ((cy - hi, cy + hi) if k % 2 == 0 else (cy + hi, cy - hi))
            move(pos, a)
            cur = extrude_to(pos, b, v, w, (pos, a))
            pos += w; k += 1
    return cur

def sparse_fill(cx, cy, hi, w, v, layer):
    """continuous zigzag, spacing for INFILL density, direction alternates per layer"""
    step = w / INFILL
    n = int(2 * hi // step)
    offs = [-hi + i * (2 * hi / n) for i in range(n + 1)]
    if layer % 2 == 1:
        cur = move(cx - hi, cy + offs[0])
        for i, o in enumerate(offs):
            x_end = cx + hi if i % 2 == 0 else cx - hi
            cur = extrude_to(x_end, cy + o, v, w, cur)
            if i + 1 < len(offs):
                cur = extrude_to(x_end, cy + offs[i + 1], v, w, cur)
    else:
        cur = move(cx + offs[0], cy - hi)
        for i, o in enumerate(offs):
            y_end = cy + hi if i % 2 == 0 else cy - hi
            cur = extrude_to(cx + o, y_end, v, w, cur)
            if i + 1 < len(offs):
                cur = extrude_to(cx + offs[i + 1], y_end, v, w, cur)
    return cur

add("; Two cubes, 2 walls + 15 %% infill. 1: outer 60 mm/s accel 1500 (left)  2: outer 100 mm/s accel 2500 (right); tally ridges = cube number")
add("START_PRINT BED_TEMP=%d EXTRUDER_TEMP=%d" % (BED_T, NOZ_T))
add("M83")
add("G90")
add("M106 S0")
nlayers = int(round(HEIGHT / H))
first = True
for n in ORDER:
    v_out, accel, scv = CUBES[n]
    cx, cy = POS[n]
    add("; ===== cube %d outer=%d mm/s accel=%d scv=%g PA=%g =====" % (n, v_out, accel, scv, PA))
    add("SET_PRESSURE_ADVANCE ADVANCE=%g" % PA)
    add("SET_VELOCITY_LIMIT ACCEL=%d SQUARE_CORNER_VELOCITY=%g" % (accel, scv))
    add("M106 S0")
    if first:
        add("G1 Z2 F3000")
        first = False
    else:
        retract()
        add("G1 Z%.1f F3000" % SAFE_Z)
    start = loop(SIZE / 2 - 1.5 * W1, cx, cy)[0]
    move(*start)
    add("G1 Z2 F3000")
    for layer in range(1, nlayers + 1):
        z = round(layer * H, 3)
        w = W1 if layer == 1 else W
        add("; cube %d layer %d Z=%.2f" % (n, layer, z))
        if layer == FAN_FROM:
            add("M106 S255")
        add("G1 Z%.3f F600" % z)
        inner = loop(SIZE / 2 - 1.5 * w, cx, cy)
        outer = loop(SIZE / 2 - 0.5 * w, cx, cy)
        is_base = layer <= BASE_LAYERS
        is_top = layer > nlayers - TOP_LAYERS
        v_in = V_FIRST if layer == 1 else (V_BASE if is_base else V_INNER)
        v_o = V_FIRST if layer == 1 else (V_BASE if is_base else v_out)
        move(*inner[0])
        unretract()
        cur = inner[0]
        for p in inner[1:]:
            cur = extrude_to(p[0], p[1], v_in, w, cur)
        cur = move(*outer[0])
        for p in outer[1:]:
            cur = extrude_to(p[0], p[1], v_o, w, cur)
        hi = SIZE / 2 - 2.5 * w
        if is_base or is_top:
            cur = solid_fill(cx, cy, hi, w, (V_FIRST if layer == 1 else (V_BASE if is_base else V_TOP)), layer, cur)
        else:
            cur = sparse_fill(cx, cy, hi, w, V_INFILL, layer)
        if layer <= TAB_LAYERS:                        # tally tab in front of the cube
            retract()
            y_hi = cy - SIZE / 2 - TAB_GAP
            y_lo = y_hi - TAB_D
            xa, xb = cx - TAB_W / 2, cx + TAB_W / 2
            v = V_FIRST if layer == 1 else V_TAB
            if layer <= BASE_LAYERS:
                pos, k, firstline = y_lo + w / 2, 0, True
                while pos <= y_hi - w / 2 + 1e-6:
                    a, b = ((xa, xb) if k % 2 == 0 else (xb, xa))
                    move(a, pos)
                    if firstline:
                        unretract(); firstline = False
                    extrude_to(b, pos, v, w, (a, pos))
                    pos += w; k += 1
            else:
                for r in range(n):
                    y = y_lo + 1.0 + 1.2 * r
                    a, b = ((xa + 1, xb - 1) if r % 2 == 0 else (xb - 1, xa + 1))
                    move(a, y)
                    if r == 0:
                        unretract()
                    extrude_to(b, y, v, W, (a, y))
            retract()
add("; end")
retract()
add("G1 Z%.1f F3000" % (SAFE_Z + 5))
add("M106 S0")
add("END_PRINT")
add("SET_VELOCITY_LIMIT ACCEL=2500 SQUARE_CORNER_VELOCITY=5")
add("SET_PRESSURE_ADVANCE ADVANCE=%g" % PA)
with open(OUT, "w") as f:
    f.write("\n".join(g) + "\n")
print("wrote %s: %d lines, %d layers/cube, extrusion path %.0f m" % (OUT, len(g), nlayers, total[0] / 1000))
print("max flow: %.1f mm3/s" % (100 * H * W))
