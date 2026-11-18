#!/usr/bin/env python3
"""Retraction (stringing) tower for Klipper firmware_retraction.

Two hollow 10x10 mm pillars, 40 mm apart, printed layer by layer with a G10/G11
retract + travel between them on every layer.  TUNING_TOWER raises RETRACT_LENGTH
with height:  retract = START + FACTOR * (Z - SKIP)   (default 0.2 + 0.06*(Z-1)).
Look for the height where strings between the pillars disappear -> retract length there.

Usage: make_retraction_tower.py OUT.gcode [START FACTOR HEIGHT_MM NOZZLE_C]
"""
import math
import sys

OUT = sys.argv[1]
START = float(sys.argv[2]) if len(sys.argv) > 2 else 0.2
FACTOR = float(sys.argv[3]) if len(sys.argv) > 3 else 0.06
HEIGHT = float(sys.argv[4]) if len(sys.argv) > 4 else 30.0
NOZ_T = int(sys.argv[5]) if len(sys.argv) > 5 else 210
BED_T = 60
SKIP = 1.0
H, W, W1, FIL_D = 0.20, 0.44, 0.50, 1.75
SIZE, BASE_LAYERS = 10.0, 3
V_FIRST, V_BASE, V_WALL = 30, 60, 60
TRAVEL_F = 150 * 60
ACCEL, SCV, PA = 1500, 5, 0.11
FAN_FROM = 4
CY = 105.0
CENTERS = [95.0, 135.0]

area = math.pi * (FIL_D / 2) ** 2
def em(w):
    return H * w / area

g = []
add = g.append

def loop(h, cx):
    return [(cx - h, CY - h), (cx + h, CY - h), (cx + h, CY + h), (cx - h, CY + h), (cx - h, CY - h)]

def draw(points, v, w):
    cur = points[0]
    for p in points[1:]:
        d = math.hypot(p[0] - cur[0], p[1] - cur[1])
        add("G1 X%.3f Y%.3f E%.4f F%d" % (p[0], p[1], d * em(w), v * 60))
        cur = p

add("; Retraction tower: RETRACT_LENGTH = %g + %g * (Z - %g)  (mm, Z in mm), nozzle %d C" % (START, FACTOR, SKIP, NOZ_T))
add("START_PRINT BED_TEMP=%d EXTRUDER_TEMP=%d" % (BED_T, NOZ_T))
add("M83")
add("G90")
add("M106 S0")
add("SET_VELOCITY_LIMIT ACCEL=%d SQUARE_CORNER_VELOCITY=%g" % (ACCEL, SCV))
add("SET_PRESSURE_ADVANCE ADVANCE=%g" % PA)
add("SET_RETRACTION RETRACT_LENGTH=%g" % START)
add("G1 Z2 F3000")
nlayers = int(round(HEIGHT / H))
for layer in range(1, nlayers + 1):
    z = round(layer * H, 3)
    w = W1 if layer == 1 else W
    add("; layer %d Z=%.2f" % (layer, z))
    if layer == FAN_FROM:
        add("M106 S255")
        add("TUNING_TOWER COMMAND=SET_RETRACTION PARAMETER=RETRACT_LENGTH START=%g FACTOR=%g SKIP=%g" % (START, FACTOR, SKIP))
    add("G1 Z%.3f F600" % z)
    for i, cx in enumerate(CENTERS):
        inner = loop(SIZE / 2 - 1.5 * w, cx)
        outer = loop(SIZE / 2 - 0.5 * w, cx)
        v = V_FIRST if layer == 1 else (V_BASE if layer <= BASE_LAYERS else V_WALL)
        add("G1 X%.3f Y%.3f F%d" % (inner[0][0], inner[0][1], TRAVEL_F))
        if layer > 1 or i > 0:
            add("G11")
        draw(inner, v, w)
        add("G1 X%.3f Y%.3f F%d" % (outer[0][0], outer[0][1], TRAVEL_F))
        draw(outer, v, w)
        if layer <= BASE_LAYERS:             # solid base inside the pillar
            hi = SIZE / 2 - 2.5 * w
            pos, k = -hi, 0
            while pos <= hi + 1e-6:
                if layer % 2 == 1:
                    a, b = ((cx - hi, cx + hi) if k % 2 == 0 else (cx + hi, cx - hi))
                    add("G1 X%.3f Y%.3f F%d" % (a, CY + pos, TRAVEL_F))
                    d = abs(b - a)
                    add("G1 X%.3f Y%.3f E%.4f F%d" % (b, CY + pos, d * em(w), v * 60))
                else:
                    a, b = ((CY - hi, CY + hi) if k % 2 == 0 else (CY + hi, CY - hi))
                    add("G1 X%.3f Y%.3f F%d" % (cx + pos, a, TRAVEL_F))
                    d = abs(b - a)
                    add("G1 X%.3f Y%.3f E%.4f F%d" % (cx + pos, b, d * em(w), v * 60))
                pos += w; k += 1
        add("G10")                            # retract before the travel to the other pillar
add("G11")
add("M106 S0")
add("TUNING_TOWER COMMAND=SET_RETRACTION PARAMETER=RETRACT_LENGTH START=0.8 FACTOR=0")
add("END_PRINT")
add("SET_RETRACTION RETRACT_LENGTH=0.8")
add("SET_VELOCITY_LIMIT ACCEL=2500 SQUARE_CORNER_VELOCITY=5")
with open(OUT, "w") as f:
    f.write("\n".join(g) + "\n")
print("wrote %s: %d layers, %d lines, retraction %.2f..%.2f mm" % (OUT, nlayers, len(g), START, START + FACTOR * (HEIGHT - SKIP)))
