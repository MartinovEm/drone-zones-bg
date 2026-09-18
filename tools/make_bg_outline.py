"""Regenerate data/bg_outline.geojson - Bulgaria's border, split for the map.

One-time helper (NOT part of build.py). Two roles the map draws differently:
  - "danube" : the northern Danube border, drawn as a blue river line. Taken from the
               ACTUAL Danube river centreline (OpenStreetMap via Overpass), clipped to
               run exactly from the NW tripoint to Silistra - so it follows the real
               river (incl. the big bend at Vidin) and never touches the Serbian border.
  - "land"   : the LAND borders, drawn in a per-basemap colour. Built from the national
               boundary (OSM via Nominatim) as TWO clean arcs between four corners:
                 D (Rezovo, SE) -> A (tripoint, NW)  = the west + south land border
                 B (Silistra)   -> C (Durankulak)    = the NE Dobruja land border
               The Danube arc A->B (blue river instead) and the Black Sea coast C->D
               (a natural sea edge - no line) are left out. So red meets blue exactly at
               the tripoint and at Silistra, and red reaches the coast at Durankulak.

Both sources are OpenStreetMap (ODbL) - credited on the map as "OpenStreetMap
contributors". Deterministic + re-runnable.

Run:  python tools/make_bg_outline.py   ->  writes data/bg_outline.geojson
"""
import json
import math
import os
import urllib.request

OUT = os.path.join(os.path.dirname(__file__), "..", "data", "bg_outline.geojson")
NOMINATIM = "https://nominatim.openstreetmap.org/search.php?country=Bulgaria&polygon_geojson=1&format=jsonv2&limit=1"
OVERPASS = "https://overpass-api.de/api/interpreter"
DANUBE_Q = '[out:json][timeout:90];way["waterway"="river"]["name:en"="Danube"](43.4,22.2,44.4,28.9);out geom;'
UA = {"User-Agent": "bgr-drone-zones-build/1.0"}

SIMPLIFY = 0.0005  # boundary Douglas-Peucker tolerance (deg) - smooth, ~3k points
# The four corners that split the ring (lng, lat), snapped to the nearest boundary point:
CORNERS = {"A": (22.680, 44.216),  # NW tripoint (Serbia / Danube)
           "B": (27.276, 44.119),  # Silistra, where the border leaves the Danube (near the river)
           "C": (28.585, 43.740),  # Durankulak (Dobruja -> coast)
           "D": (28.020, 42.010)}  # Rezovo (coast -> south)
# Arc roles by the pair of corners it lies between:
ROLE = {frozenset("AB"): "danube",  # blue river (from the river data, not the ring)
        frozenset("BC"): "land",    # Dobruja
        frozenset("CD"): "coast",   # Black Sea - no line
        frozenset("DA"): "land"}    # west + south


def _get(url, data=None):
    return urllib.request.urlopen(urllib.request.Request(url, data=data, headers=UA), timeout=90).read().decode("utf-8")


def simplify(pts, tol):
    n = len(pts); keep = [False] * n; keep[0] = keep[-1] = True; stack = [(0, n - 1)]
    def pld(p, a, b):
        ax, ay = a; bx, by = b; px, py = p; dx, dy = bx - ax, by - ay
        if dx == 0 and dy == 0:
            return math.hypot(px - ax, py - ay)
        t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
        return math.hypot(px - (ax + t * dx), py - (ay + t * dy))
    while stack:
        i, j = stack.pop()
        if j <= i + 1:
            continue
        dmax, idx = 0, -1
        for k in range(i + 1, j):
            d = pld(pts[k], pts[i], pts[j])
            if d > dmax:
                dmax, idx = d, k
        if dmax > tol:
            keep[idx] = True; stack.append((i, idx)); stack.append((idx, j))
    return [pts[i] for i in range(n) if keep[i]]


def land_arcs():
    """Red: the two clean land arcs (west+south, Dobruja) between the four corners."""
    nom = json.loads(_get(NOMINATIM))
    g = nom[0]["geojson"]
    rings = g["coordinates"] if g["type"] == "Polygon" else [r for poly in g["coordinates"] for r in poly]
    ring = max(rings, key=len)
    if ring[0] == ring[-1]:
        ring = ring[:-1]
    ring = simplify(ring, SIMPLIFY)
    n = len(ring)
    idx = {k: min(range(n), key=lambda i: (ring[i][0] - v[0]) ** 2 + (ring[i][1] - v[1]) ** 2)
           for k, v in CORNERS.items()}
    order = sorted(idx.items(), key=lambda kv: kv[1])  # corners in ring order
    red = []
    for k in range(4):
        (a_lbl, a_i), (b_lbl, b_i) = order[k], order[(k + 1) % 4]
        seg = ring[a_i:b_i + 1] if k < 3 else ring[a_i:] + ring[:b_i + 1]
        if ROLE[frozenset(a_lbl + b_lbl)] == "land" and len(seg) >= 2:
            red.append(seg)
    return red, ring[idx["A"]], ring[idx["B"]]


def danube_river(a_pt, b_pt):
    """Blue: the Danube centreline, clipped to run from the tripoint (A) to Silistra (B)."""
    dv = json.loads(_get(OVERPASS, data=("data=" + DANUBE_Q).encode()))
    x0, x1 = a_pt[0], b_pt[0]
    segs = []
    for el in dv.get("elements", []):
        run = []
        for nd in el.get("geometry", []) or []:
            x, y = nd["lon"], nd["lat"]
            if x0 <= x <= x1 and 43.5 <= y <= 44.25:
                run.append([x, y])
            else:
                if len(run) >= 2:
                    segs.append(run)
                run = []
        if len(run) >= 2:
            segs.append(run)
    # snap the river's two extreme ends to the land corners A and B so the blue line
    # joins the red land border exactly at the tripoint and at Silistra (no small gap)
    if segs:
        pts = [(si, pi) for si, s in enumerate(segs) for pi in range(len(s))]
        e = max(pts, key=lambda t: segs[t[0]][t[1]][0]); segs[e[0]][e[1]] = list(b_pt)
        w = min(pts, key=lambda t: segs[t[0]][t[1]][0]); segs[w[0]][w[1]] = list(a_pt)
    return segs


def main():
    red, a_pt, b_pt = land_arcs()
    blue = danube_river(a_pt, b_pt)
    fc = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"role": "land"},
         "geometry": {"type": "MultiLineString", "coordinates": red}},
        {"type": "Feature", "properties": {"role": "danube"},
         "geometry": {"type": "MultiLineString", "coordinates": blue}},
    ]}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(fc, f, separators=(",", ":"))
    print("wrote %s - %d bytes; land arcs: %d, danube (river) segments: %d"
          % (os.path.relpath(OUT), os.path.getsize(OUT), len(red), len(blue)))


if __name__ == "__main__":
    main()
