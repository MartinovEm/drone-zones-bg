#!/usr/bin/env python3
"""
Build the app icons named in manifest.webmanifest (owner 24.10: the map installable on a phone).

One-time tool, like make_oblasts.py: rerun only when the drone sign changes. It draws the page's own
favicon (make_3d.py FAV: a royal-blue drone on a 48-unit grid) on a white, opaque square:
  icons/icon-192.png, icons/icon-512.png - purpose "any", the drone over ~84 % of the square
  icons/icon-maskable-512.png           - purpose "maskable": Android crops it to a circle or a
                                          squircle, so the whole drone stays inside the central
                                          circle of 80 % (the maskable safe zone)
  icons/apple-touch-icon.png (180)      - the iPhone home-screen icon (iOS rounds the corners itself)
Drawn 4x larger and scaled down (smooth edges). Needs Pillow.

Usage: python tools/make_icons.py [out_dir]   (default: icons/ next to tools/)
"""
import math, os, sys
from PIL import Image, ImageDraw

BLUE = (65, 105, 225)  # royalblue, as the favicon
SS = 4                 # supersampling

def drone(size, span):
    """A size x size icon; span = the share of the side the drone's outer edges cover (centred)."""
    S = size * SS
    img = Image.new('RGB', (S, S), (255, 255, 255))
    d = ImageDraw.Draw(img)
    k = span * S / 41.0          # the drone spans 41 grid units (3.5 .. 44.5)
    o = (S - 48 * k) / 2         # centre the 48-unit grid
    P = lambda u: o + u * k
    w = 3 * k                    # the arms' stroke (3 units, round caps)
    for (x1, y1, x2, y2) in ((14, 14, 34, 34), (34, 14, 14, 34)):
        d.line([(P(x1), P(y1)), (P(x2), P(y2))], fill=BLUE, width=round(w))
        for (x, y) in ((x1, y1), (x2, y2)):
            d.ellipse([P(x) - w / 2, P(y) - w / 2, P(x) + w / 2, P(y) + w / 2], fill=BLUE)
    r, sw = 7 * k, 3 * k         # the rotors: r 7, stroke 3 (outer edge at r + 1.5)
    for (cx, cy) in ((12, 12), (36, 12), (12, 36), (36, 36)):
        d.ellipse([P(cx) - r - sw / 2, P(cy) - r - sw / 2, P(cx) + r + sw / 2, P(cy) + r + sw / 2],
                  outline=BLUE, width=round(sw))
    d.rounded_rectangle([P(18), P(18), P(30), P(30)], radius=3 * k, fill=BLUE)
    return img.resize((size, size), Image.LANCZOS)

# the farthest point of the drone from the centre: a rotor's centre (16.97 units away) + r 7 + half stroke
REACH = math.hypot(12, 12) + 7 + 1.5
MASKABLE_SPAN = 0.8 / 2 / REACH * 41   # the outer edges inside the central 80 % circle

out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'icons')
os.makedirs(out, exist_ok=True)
for name, size, span in (('icon-192.png', 192, 0.84), ('icon-512.png', 512, 0.84),
                         ('icon-maskable-512.png', 512, MASKABLE_SPAN), ('apple-touch-icon.png', 180, 0.8)):
    path = os.path.join(out, name)
    drone(size, span).save(path, optimize=True)
    print('%s: %dx%d, %d bytes' % (name, size, size, os.path.getsize(path)))
