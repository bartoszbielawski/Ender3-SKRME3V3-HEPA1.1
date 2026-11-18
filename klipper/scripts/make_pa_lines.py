#!/usr/bin/env python3
"""Pressure advance line test (single layer) for Klipper.

Each line: slow 30 mm -> fast 100 mm -> slow 30 mm, with its own PA value.
Good PA = uniform line width at the speed changes (no bulge at the slow-down,
no thin/gap section at the speed-up). Every 5th line gets a tick mark on the
right so lines can be counted.

Usage: make_pa_lines.py OUT.gcode [PA_START PA_STEP COUNT [NOZZLE_T SLOW_MMS FAST_MMS ACCEL]]
(defaults: 200 C, 20 -> 120 mm/s, ACCEL 1500)
"""
import math
import sys

OUT = sys.argv[1]
PA_START = float(sys.argv[2]) if len(sys.argv) > 2 else 0.12
PA_STEP = float(sys.argv[3]) if len(sys.argv) > 3 else 0.01
COUNT = int(sys.argv[4]) if len(sys.argv) > 4 else 17

BED_T = 60
NOZ_T = int(sys.argv[5]) if len(sys.argv) > 5 else 200
SLOW_V = float(sys.argv[6]) if len(sys.argv) > 6 else 20      # mm/s
FAST_V = float(sys.argv[7]) if len(sys.argv) > 7 else 120     # mm/s
ACCEL = int(sys.argv[8]) if len(sys.argv) > 8 else 1500
LAYER_H, WIDTH, FIL_D = 0.25, 0.5, 1.75
X0, SLOW_LEN, FAST_LEN = 30.0, 30.0, 100.0
Y0, PITCH = 40.0, 6.0
SLOW_F, FAST_F, TRAVEL_F = SLOW_V * 60, FAST_V * 60, 150 * 60
RETRACT, RETRACT_F = 0.8, 35 * 60

e_per_mm = LAYER_H * WIDTH / (math.pi * (FIL_D / 2) ** 2)
x1 = X0 + SLOW_LEN
x2 = x1 + FAST_LEN
x3 = x2 + SLOW_LEN

pa_values = [round(PA_START + i * PA_STEP, 4) for i in range(COUNT)]

g = []
g.append("; PA line test: PA %s .. %s step %s (%d lines, bottom = first, Y from %.0f every %.0f mm)"
         % (pa_values[0], pa_values[-1], PA_STEP, COUNT, Y0, PITCH))
g.append("; lines: " + ", ".join("#%d Y=%.0f PA=%.3f" % (i + 1, Y0 + i * PITCH, pa)
                                  for i, pa in enumerate(pa_values)))
g.append("START_PRINT BED_TEMP=%d EXTRUDER_TEMP=%d" % (BED_T, NOZ_T))
g.append("M83")
g.append("G90")
g.append("M106 S0")
g.append("SET_VELOCITY_LIMIT ACCEL=%d" % ACCEL)
g.append("G1 Z2 F3000")
for i, pa in enumerate(pa_values):
    y = Y0 + i * PITCH
    g.append("; line %d PA=%.3f" % (i + 1, pa))
    g.append("SET_PRESSURE_ADVANCE ADVANCE=%.4f" % pa)
    g.append("G1 X%.2f Y%.2f F%d" % (X0, y, TRAVEL_F))
    g.append("G1 Z%.2f F600" % LAYER_H)
    g.append("G1 E%.3f F%d" % (RETRACT, RETRACT_F))
    g.append("G1 X%.2f E%.4f F%d" % (x1, SLOW_LEN * e_per_mm, SLOW_F))
    g.append("G1 X%.2f E%.4f F%d" % (x2, FAST_LEN * e_per_mm, FAST_F))
    g.append("G1 X%.2f E%.4f F%d" % (x3, SLOW_LEN * e_per_mm, SLOW_F))
    if (i + 1) % 5 == 0:  # tick mark to the right of every 5th line
        g.append("G1 X%.2f E%.4f F%d" % (x3 + 8, 8 * e_per_mm, SLOW_F))
    g.append("G1 E-%.3f F%d" % (RETRACT, RETRACT_F))
    g.append("G1 Z%.2f F3000" % (LAYER_H + 1.0))
g.append("G1 Z10 F3000")
g.append("SET_PRESSURE_ADVANCE ADVANCE=0.175")   # back to the value in printer.cfg
g.append("END_PRINT")

with open(OUT, "w") as f:
    f.write("\n".join(g) + "\n")
print("wrote %s: %d lines, PA %s..%s" % (OUT, COUNT, pa_values[0], pa_values[-1]))
