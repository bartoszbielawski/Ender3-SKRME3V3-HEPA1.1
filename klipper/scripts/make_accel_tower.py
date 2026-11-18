#!/usr/bin/env python3
"""Acceleration / ringing tower for Klipper (PLA, 0.4 nozzle, 0.2 layers).

A hollow 40 x 40 mm box with sharp corners, 2 perimeters, solid 3-layer base.
TUNING_TOWER raises max_accel with height:  accel = START + FACTOR * (Z - SKIP).
Look at the corners/walls: ringing ("ghosts" after corners) starts at some
height -> accel there = START + FACTOR * (Z - SKIP)  (default 1500 + 50*(Z-4)).

Usage: make_accel_tower.py OUT.gcode [ACCEL_START ACCEL_FACTOR HEIGHT_MM]
Flow is capped well below the tested limit: 100 mm/s * 0.2 * 0.44 = 8.8 mm3/s.
"""
import math
import sys

OUT = sys.argv[1]
ACC0 = float(sys.argv[2]) if len(sys.argv) > 2 else 1500
FACTOR = float(sys.argv[3]) if len(sys.argv) > 3 else 50
HEIGHT = float(sys.argv[4]) if len(sys.argv) > 4 else 40.0
# optional 5th arg "pa": pressure-advance tower at constant ACCEL=ACC0 instead
# (args 6, 7: PA_START, PA_FACTOR per mm of Z above SKIP): PA = START + FACTOR*(Z-4)
MODE = sys.argv[5] if len(sys.argv) > 5 else "accel"
PA0 = float(sys.argv[6]) if len(sys.argv) > 6 else 0.08
PAF = float(sys.argv[7]) if len(sys.argv) > 7 else 0.0033

BED_T, NOZ_T = 60, 210
H, W, W1, FIL_D = 0.20, 0.44, 0.50, 1.75
SIZE = 40.0
CX, CY = 117.0, 105.0
BASE_LAYERS = 3
SKIP = 4.0                       # tuning tower starts after the base
V_OUT, V_IN, V_BASE, V_FIRST = 100, 100, 80, 30       # mm/s
TRAVEL_F = 200 * 60
FAN_FROM_LAYER = 4

area = math.pi * (FIL_D / 2) ** 2
def e_per_mm(layer_h, width):
    return layer_h * width / area

def loop(h):
    """clockwise square, half-width h, starts at front-left corner"""
    return [(CX - h, CY - h), (CX + h, CY - h), (CX + h, CY + h), (CX - h, CY + h), (CX - h, CY - h)]

g = []
add = g.append
total_len = 0.0
add("; Acceleration tower: accel = %g + %g * (Z - %g)  (Z in mm)" % (ACC0, FACTOR, SKIP))
add("; box %gx%g mm at (%g,%g), %g mm tall, 2 perimeters, base %d layers" % (SIZE, SIZE, CX, CY, HEIGHT, BASE_LAYERS))
add("START_PRINT BED_TEMP=%d EXTRUDER_TEMP=%d" % (BED_T, NOZ_T))
add("M83")
add("G90")
add("M106 S0")
add("SET_VELOCITY_LIMIT ACCEL=%d" % ACC0)
add("SET_PRESSURE_ADVANCE ADVANCE=%g" % (PA0 if MODE == "pa" else 0.175))  # 0.175 = printer.cfg

def draw(points, v, layer_h, width):
    global total_len
    em = e_per_mm(layer_h, width)
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        d = math.hypot(x1 - x0, y1 - y0)
        total_len += d
        add("G1 X%.3f Y%.3f E%.4f F%d" % (x1, y1, d * em, v * 60))

nlayers = int(round(HEIGHT / H))
for n in range(1, nlayers + 1):
    z = round(n * H, 3)
    w = W1 if n == 1 else W
    add("; layer %d Z=%.2f" % (n, z))
    if n == FAN_FROM_LAYER:
        add("M106 S255")
    if n == BASE_LAYERS + 1:      # tower starts after the solid base
        if MODE == "pa":
            add("TUNING_TOWER COMMAND=SET_PRESSURE_ADVANCE PARAMETER=ADVANCE START=%g FACTOR=%g SKIP=%g" % (PA0, PAF, SKIP))
        else:
            add("TUNING_TOWER COMMAND=SET_VELOCITY_LIMIT PARAMETER=ACCEL START=%g FACTOR=%g SKIP=%g" % (ACC0, FACTOR, SKIP))
    add("G1 Z%.3f F600" % z)
    inner = loop(SIZE / 2 - w * 1.5)
    outer = loop(SIZE / 2 - w * 0.5)
    v_o = V_FIRST if n == 1 else (V_BASE if n <= BASE_LAYERS else V_OUT)
    v_i = V_FIRST if n == 1 else (V_BASE if n <= BASE_LAYERS else V_IN)
    add("G1 X%.3f Y%.3f F%d" % (inner[0][0], inner[0][1], TRAVEL_F))
    draw(inner, v_i, H, w)
    add("G1 X%.3f Y%.3f F%d" % (outer[0][0], outer[0][1], TRAVEL_F))
    draw(outer, v_o, H, w)
    if n <= BASE_LAYERS:           # solid infill, alternating direction
        hi = SIZE / 2 - w * 2.5
        v = V_FIRST if n == 1 else V_BASE
        em = e_per_mm(H, w)
        pts = []
        k = 0
        if n % 2 == 1:             # lines along X, stepping Y
            y = CY - hi
            while y <= CY + hi + 1e-6:
                xs = (CX - hi, CX + hi) if k % 2 == 0 else (CX + hi, CX - hi)
                pts.append(((xs[0], y), (xs[1], y)))
                y += w; k += 1
        else:                      # lines along Y, stepping X
            x = CX - hi
            while x <= CX + hi + 1e-6:
                ys = (CY - hi, CY + hi) if k % 2 == 0 else (CY + hi, CY - hi)
                pts.append(((x, ys[0]), (x, ys[1])))
                x += w; k += 1
        for (a, b) in pts:
            add("G1 X%.3f Y%.3f F%d" % (a[0], a[1], TRAVEL_F))
            d = math.hypot(b[0] - a[0], b[1] - a[1])
            total_len += d
            add("G1 X%.3f Y%.3f E%.4f F%d" % (b[0], b[1], d * em, v * 60))

add("; end: leave tuning tower at config accel")
if MODE == "pa":
    add("TUNING_TOWER COMMAND=SET_PRESSURE_ADVANCE PARAMETER=ADVANCE START=0.175 FACTOR=0")
else:
    add("TUNING_TOWER COMMAND=SET_VELOCITY_LIMIT PARAMETER=ACCEL START=2500 FACTOR=0")
add("M106 S0")
add("END_PRINT")
add("SET_VELOCITY_LIMIT ACCEL=2500")     # tuning tower leaves the last tower value otherwise
add("SET_PRESSURE_ADVANCE ADVANCE=0.175")

with open(OUT, "w") as f:
    f.write("\n".join(g) + "\n")
print("wrote %s: %d layers, %d lines, extrusion path %.0f m, accel %g..%g mm/s2"
      % (OUT, nlayers, len(g), total_len / 1000, ACC0, ACC0 + FACTOR * (HEIGHT - SKIP)))
print("max flow outer/inner: %.1f mm3/s" % (V_OUT * H * W))
