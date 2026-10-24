#!/usr/bin/env python3
"""
Build the app icons named in manifest.webmanifest (owner 24.10: the map installable on a phone).

One-time tool, like make_oblasts.py: rerun only when the sign changes. The sign (owner's pick, 24.10) is
drone.svg in the repo root - a royal-blue map pin with a white drone, stuck into three rings in the map's
zone colours (red inside, orange, yellow outside); the README title and the page's favicon use that file.
This draws the same numbers (a 1024 grid; the sign's box = drone.svg's viewBox, centre 512, 550, half 470):
  icons/icon-192.png, icons/icon-512.png - purpose "any": TRANSPARENT around the sign (a computer's
                                          taskbar / dock shows no white square)
  icons/icon-maskable-512.png           - purpose "maskable", WHITE: Android shows it in a circle (or another
                                          shape) - the sign reaches 88 % (the owner's phone shows ~90 %; only
                                          the central 80 % is guaranteed on every shape)
  icons/apple-touch-icon.png (180)      - WHITE: iOS fills transparency with black and rounds the corners
A changed icon also needs a new `?v=` on its URLs in manifest.webmanifest + make_3d.py (apple-touch-icon):
Chrome re-reads an installed app's icon only when its URL changes.
Drawn 4x larger and scaled down (smooth edges). Needs Pillow.

Usage: python tools/make_icons.py [out_dir]   (default: icons/ next to tools/)
"""
import math, os, sys
from PIL import Image, ImageDraw

BLUE, WHITE = (65, 105, 225), (255, 255, 255)           # royalblue (#4169e1)
RED, ORANGE, YELLOW = (255, 32, 32), (255, 128, 0), (255, 204, 0)   # make_3d.py COL
SS = 4                                                    # supersampling
# drone.svg on the 1024 grid: the rings round (512, 640) - Pillow draws a ring's width INWARD from its radius,
# so these OUTER radii give drone.svg's stroke centres 348 / 263 / 178; the pin's head (512, 300) r 210, tip
# (512, 640); the white drone 252 wide in the head; the sign's box centre and half-side; its farthest point
RINGS, RING_W = ((370, YELLOW), (285, ORANGE), (200, RED)), 44
HEAD, HEAD_R, TIP, DRONE_SPAN = (512, 300), 210, (512, 640), 252
BOX_C, BOX_HALF, REACH = (512, 550), 470, 460

def drone(d, cx, cy, span, col):
    """The favicon drone (48-unit grid, 41 units wide) centred at cx, cy, span px wide."""
    k = span / 41.0
    P = lambda ux, uy: (cx + (ux - 24) * k, cy + (uy - 24) * k)
    w = 3 * k                                             # the arms: stroke 3, round caps
    for (x1, y1, x2, y2) in ((14, 14, 34, 34), (34, 14, 14, 34)):
        d.line([P(x1, y1), P(x2, y2)], fill=col, width=round(w))
        for (x, y) in ((x1, y1), (x2, y2)):
            px, py = P(x, y)
            d.ellipse([px - w / 2, py - w / 2, px + w / 2, py + w / 2], fill=col)
    r, sw = 7 * k, 3 * k                                  # the rotors: r 7, stroke 3
    for (ux, uy) in ((12, 12), (36, 12), (12, 36), (36, 36)):
        px, py = P(ux, uy)
        d.ellipse([px - r - sw / 2, py - r - sw / 2, px + r + sw / 2, py + r + sw / 2], outline=col, width=round(sw))
    a, b = P(18, 18), P(30, 30)
    d.rounded_rectangle([a[0], a[1], b[0], b[1]], radius=3 * k, fill=col)

def icon(size, scale, white):
    """A size x size icon; scale = icon px per grid unit at the final size."""
    S = size * SS
    img = Image.new('RGBA', (S, S), WHITE + (255,) if white else (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    k = scale * SS
    G = lambda x, y: (S / 2 + (x - BOX_C[0]) * k, S / 2 + (y - BOX_C[1]) * k)   # grid -> pixels
    cx, cy = G(*TIP)
    for r, col in RINGS:                                  # the rings round the pin's tip
        d.ellipse([cx - r * k, cy - r * k, cx + r * k, cy + r * k], outline=col, width=round(RING_W * k))
    hx, hy = G(*HEAD); hr = HEAD_R * k; tx, ty = G(*TIP)
    tl = math.sqrt((ty - hy) ** 2 - hr ** 2); a = math.atan2(hr, tl)   # the pin: head + the tangent sides to the tip
    d.polygon([(hx - hr * math.cos(a), hy + hr * math.sin(a)), (hx + hr * math.cos(a), hy + hr * math.sin(a)), (tx, ty)], fill=BLUE)
    d.ellipse([hx - hr, hy - hr, hx + hr, hy + hr], fill=BLUE)
    drone(d, hx, hy, DRONE_SPAN * k, WHITE)
    return img.resize((size, size), Image.LANCZOS)

out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'icons')
os.makedirs(out, exist_ok=True)
for name, size, scale, white in (('icon-192.png', 192, 96 / BOX_HALF, False), ('icon-512.png', 512, 256 / BOX_HALF, False),
                                 # Android: 0.44 - the owner's phone shows a circle of ~90 % of the icon (measured on
                                 # his screenshots: 0.40 looked small, 0.49 cut the pin's top); only 0.40 is
                                 # guaranteed on every launcher shape. iPhone: its rounded square shows almost all
                                 ('icon-maskable-512.png', 512, 0.44 * 512 / REACH, True),
                                 ('apple-touch-icon.png', 180, 0.49 * 180 / REACH, True)):
    path = os.path.join(out, name)
    icon(size, scale, white).save(path, optimize=True)
    print('%s: %dx%d %s, %d bytes' % (name, size, size, 'white' if white else 'transparent', os.path.getsize(path)))
