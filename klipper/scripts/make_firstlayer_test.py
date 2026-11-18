#!/usr/bin/env python3
"""First-layer test: 5 pads with different Z offsets (SET_GCODE_OFFSET Z_ADJUST), two rows
(row 1 = 210 C, row 2 = 200 C). Pad n (left->right) has n tally lines in front.
Offsets (mm, + = nozzle higher): -0.03 0 +0.03 +0.06 +0.09. 1 layer, 30 mm/s, line 0.48, no fan.
Usage: make_firstlayer_test.py OUT.gcode"""
import math, sys
OUT = sys.argv[1]
OFFS = [-0.03, 0.0, 0.03, 0.06, 0.09]
ROWS = [(210, 70.0), (200, 125.0)]
PAD, GAP, X0 = 30.0, 8.0, 26.0
H, W, FIL_D, V = 0.20, 0.48, 1.75, 30
RET, RET_F, TRAVEL_F = 0.6, 40 * 60, 150 * 60
em = lambda d: d * H * W / (math.pi * (FIL_D / 2) ** 2)
g = []; add = g.append
st = {"off": 0.0, "ret": False}
def retract():
    if not st["ret"]: add("G1 E-%.2f F%d" % (RET, RET_F)); st["ret"] = True
def unretract():
    if st["ret"]: add("G1 E%.2f F%d" % (RET, RET_F)); st["ret"] = False
def go(x, y, hop=False):
    if hop: retract(); add("G1 Z0.8 F3000")
    add("G1 X%.3f Y%.3f F%d" % (x, y, TRAVEL_F))
    if hop: add("G1 Z0.2 F3000")
def line(x0, y0, x1, y1, first=False):
    go(x0, y0)
    unretract()
    add("G1 X%.3f Y%.3f E%.4f F%d" % (x1, y1, em(math.hypot(x1 - x0, y1 - y0)), V * 60))
add("; First-layer test, Z offsets %s, rows %s" % (OFFS, [r[0] for r in ROWS]))
add("START_PRINT BED_TEMP=60 EXTRUDER_TEMP=%d" % ROWS[0][0])
add("M83"); add("G90"); add("M106 S0")
add("G1 Z2 F3000")
first = True
for temp, cy in ROWS:
    if not first:
        retract(); add("G1 Z2 F3000"); add("M109 S%d" % temp)
    for i, off in enumerate(OFFS):
        cx = X0 + PAD / 2 + i * (PAD + GAP)
        add("; pad %d row temp %d offset %+.2f" % (i + 1, temp, off))
        add("SET_GCODE_OFFSET Z_ADJUST=%.3f" % (off - st["off"])); st["off"] = off
        h = PAD / 2 - W / 2
        go(cx - h, cy - h, hop=not first or i > 0)
        if first and i == 0: add("G1 Z0.2 F3000")
        first = False
        pts = [(cx - h, cy - h), (cx + h, cy - h), (cx + h, cy + h), (cx - h, cy + h), (cx - h, cy - h)]
        for a, b in zip(pts, pts[1:]): line(a[0], a[1], b[0], b[1])
        hi = h - W; pos = -hi; k = 0
        while pos <= hi + 1e-6:
            a, b = ((cx - hi, cx + hi) if k % 2 == 0 else (cx + hi, cx - hi))
            line(a, cy + pos, b, cy + pos); pos += W; k += 1
        retract()
        for r in range(i + 1):           # tally ridges in front of the pad
            y = cy - PAD / 2 - 4 - 1.5 * r
            go(cx - 6, y, hop=True); line(cx - 6, y, cx + 6, y); retract()
add("G1 Z2 F3000")
add("SET_GCODE_OFFSET Z_ADJUST=%.3f" % (-st["off"]))
add("END_PRINT")
open(OUT, "w").write("\n".join(g) + "\n")
print("wrote", OUT, len(g), "lines")
