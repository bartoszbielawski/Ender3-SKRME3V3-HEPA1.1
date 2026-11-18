#!/usr/bin/env python3
"""Small 20x20x20 tower, ONE wall (0.44), 3 solid bottom layers, open top. Profile defaults:
outer wall 80 mm/s, ACCEL 2000, SCV 5, 210 C, PA 0.11, fan 100 % from layer 4.
Usage: make_tower_20.py OUT.gcode"""
import math, sys
OUT = sys.argv[1]
SIZE, HEIGHT = 20.0, 20.0
H, W, W1, FIL_D = 0.20, 0.44, 0.48, 1.75
V_FIRST, V_BASE, V_WALL = 30, 60, 80
ACCEL, SCV, PA = 2000, 5, 0.11
CX, CY = 117.0, 107.0
BASE = 3
em = lambda d, w: d * H * w / (math.pi * (FIL_D / 2) ** 2)
g = []; add = g.append
def loop(h): return [(CX-h,CY-h),(CX+h,CY-h),(CX+h,CY+h),(CX-h,CY+h),(CX-h,CY-h)]
add("; 20x20x20 tower, 1 wall, outer 80 mm/s, accel 2000")
add("START_PRINT BED_TEMP=60 EXTRUDER_TEMP=210")
add("M83"); add("G90"); add("M106 S0")
add("SET_VELOCITY_LIMIT ACCEL=%d SQUARE_CORNER_VELOCITY=%g" % (ACCEL, SCV))
add("SET_PRESSURE_ADVANCE ADVANCE=%g" % PA)
add("G1 Z2 F3000")
n = int(round(HEIGHT / H)); first = True
for layer in range(1, n + 1):
    z = round(layer * H, 3); w = W1 if layer == 1 else W
    add("; layer %d Z=%.2f" % (layer, z))
    if layer == 4: add("M106 S255")
    add("G1 Z%.3f F600" % z)
    v = V_FIRST if layer == 1 else (V_BASE if layer <= BASE else V_WALL)
    pts = loop(SIZE / 2 - w / 2)
    add("G1 X%.3f Y%.3f F12000" % pts[0])
    if first: first = False
    else: add("G1 E0.6 F2400")
    cur = pts[0]
    for p in pts[1:]:
        add("G1 X%.3f Y%.3f E%.4f F%d" % (p[0], p[1], em(math.hypot(p[0]-cur[0], p[1]-cur[1]), w), v * 60)); cur = p
    if layer <= BASE:
        hi = SIZE / 2 - 1.5 * w; pos = -hi; k = 0
        while pos <= hi + 1e-6:
            a, b = ((CX-hi, CX+hi) if (k % 2 == 0) else (CX+hi, CX-hi)) if layer % 2 == 1 else (None, None)
            if layer % 2 == 1:
                add("G1 X%.3f Y%.3f F12000" % (a, CY+pos)); add("G1 X%.3f Y%.3f E%.4f F%d" % (b, CY+pos, em(abs(b-a), w), v*60))
            else:
                a, b = ((CY-hi, CY+hi) if k % 2 == 0 else (CY+hi, CY-hi))
                add("G1 X%.3f Y%.3f F12000" % (CX+pos, a)); add("G1 X%.3f Y%.3f E%.4f F%d" % (CX+pos, b, em(abs(b-a), w), v*60))
            pos += w; k += 1
    add("G1 E-0.6 F2400")
add("M106 S0"); add("END_PRINT")
add("SET_VELOCITY_LIMIT ACCEL=2500 SQUARE_CORNER_VELOCITY=5")
open(OUT, "w").write("\n".join(g) + "\n"); print("wrote", OUT, len(g))
