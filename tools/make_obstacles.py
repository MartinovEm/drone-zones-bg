"""Build the map's obstacles layer: obstacles/index.json plus one file per 0.5° x 0.5° cell
(obstacles/c<ix>_<iy>.json), so the map loads only the cells on the screen (owner 17.10.2026:
it must load fast).

Usage: python tools/make_obstacles.py [out_dir] [--pbf FILE] [--cache DIR]
  out_dir   defaults to <repo>/obstacles
  --pbf     read a local Bulgaria .osm.pbf instead of downloading Geofabrik's daily extract
  --cache   keep the downloads (the extract and ESO's answer) in DIR and reuse them

Run daily by .github/workflows/obstacles.yml (owner 17.10: checked every day, published only on
a real change): only the files whose content changed are rewritten, and index.json's "changed"
date moves only then. If a source fails, nothing is written and the map keeps the previous files.

Sources
- OpenStreetMap (© OpenStreetMap contributors, ODbL 1.0), Geofabrik's daily extract of Bulgaria:
  power lines and their towers / poles, wind turbines, masts, towers, chimneys, cranes and other
  tall man-made objects, aerial lifts and their pylons, electrified railways, tram and trolleybus
  wires. Bulgaria only (owner 17.10), cut at the country border taken from the same extract.
  The files are a derivative database of OSM, offered under the ODbL 1.0 (a notice in every
  file); this script is the method.
- ESO EAD (Електроенергиен системен оператор): the 110-400 kV routes on its public map
  (https://webapps.eso.bg/joining/public/map/). Only built lines (status 3; 1 and 2 are "not
  finished" in ESO's own map code) and only the pieces farther than ESO_GAP metres from every OSM
  power line and at least ESO_MIN metres long, so no line is drawn twice (owner 17.10); 94 % of
  ESO's routes lie within 25 m of OSM's lines.
- Typical heights and minimum wire heights: obstacle_heights.py (sources there).

A cell file is {"lic": ..., "l": lines, "p": points}. Coordinates are integers in 1e-5 degrees
(~1 m). A line is [kind, kV, [x0, y0, dx1, dy1, ...], name, type] with its coordinates
delta-encoded; the points of a cell are sorted and delta-encoded the same way:
[dx, dy, kind, height_dm, kV, name, type]. height_dm > 0 = OSM's own height, < 0 = a typical
height, 0 = none. Trailing empty fields are left out. The kinds are listed in index.json.
"""
import datetime, gzip, io, json, math, os, re, shutil, sys, tempfile, time, urllib.request
import osmium
from obstacle_heights import (TOWERS, POLES, POLE_UNKNOWN, LIFT_PYLON, WIND, WIND_FARMS,
                              WIRE_MIN, WIRE_SRC, WIRE_URL, RAIL_WIRE)

PBF_URL = "https://download.geofabrik.de/europe/bulgaria-latest.osm.pbf"
ESO_URL = "https://webapps.eso.bg/joining/public/map/api/get-lines.php"
HDRS = {"User-Agent": "bgr-drone-zones obstacles build (https://github.com/MartinovEm/drone-zones-bg)"}
LIC = "ODbL 1.0 (https://opendatacommons.org/licenses/odbl/1-0/) · © OpenStreetMap contributors"
CELL, X0, Y0, SCALE = 0.5, 22.0, 41.0, 100000
# m: an ESO piece must lie farther than ESO_GAP from every OSM power line and be at least ESO_MIN long
# (shorter or closer ones were ESO's drawing differing from OSM's, not missing lines: owner 17.10, after
# seeing them on a map); checked every SAMPLE m
ESO_GAP, ESO_MIN, SAMPLE = 200, 1000, 25
ESO_SAME = 30    # m: two ESO pieces this close are the two circuits of one line (merged)

LINE_KINDS = ["line", "minor", "eso", "rail", "tram", "trolley", "lift"]
POINT_KINDS = ["tower", "pole", "upole", "portal", "catmast", "turbine", "liftpylon", "mast", "mtower", "ctower",
               "chimney", "wtower", "lighthouse", "crane", "flagpole", "antenna", "silo", "windmill", "flare",
               "gasometer"]
KINDS = LINE_KINDS + POINT_KINDS
K = {k: i for i, k in enumerate(KINDS)}
SUPPORTS = {"tower": "tower", "pole": "pole", "portal": "portal", "catenary_mast": "catmast"}
MAN_MADE = {"mast": "mast", "tower": "mtower", "communications_tower": "ctower", "chimney": "chimney",
            "water_tower": "wtower", "lighthouse": "lighthouse", "crane": "crane", "flagpole": "flagpole",
            "antenna": "antenna", "silo": "silo", "windmill": "windmill", "flare": "flare", "gasometer": "gasometer"}
LIFTS = {"cable_car", "gondola", "mixed_lift", "chair_lift", "drag_lift", "t-bar", "j-bar", "platter", "rope_tow",
         "magic_carpet", "zip_line", "goods", "abandoned"}
RAILS = {"rail", "light_rail", "narrow_gauge"}
FARM = {"n%d" % i: f for f in WIND_FARMS for i in f["ids"]}
SAME_SPOT = 30   # m: an outline whose centre is this close to a node of the same kind is the same object
SAME_OUTLINE = 5  # m: two outlines of the same kind with centres this close are one object (silos stand closer than 30 m)
LAT0 = math.radians(42.7)
KX, KY = 111320.0 * math.cos(LAT0), 110540.0   # metres per degree around Bulgaria (local plane)


# ---- small helpers -------------------------------------------------------------------------

def http(url, path):
    """Download url to path; two retries."""
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HDRS), timeout=600) as r, \
                    open(path, "wb") as f:
                shutil.copyfileobj(r, f, 1 << 20)
            return
        except Exception as e:
            if attempt == 2:
                raise SystemExit("download failed (%s): %s" % (url, e))
            print("  retry (%s): %s" % (url, e))
            time.sleep(20)


def num(s):
    """The height in an OSM value ('30', '30 m', '12.5', '100 ft') in metres, or None."""
    m = re.match(r"\s*~?\s*(\d+(?:[.,]\d+)?)\s*(ft|feet|')?", s or "")
    if not m:
        return None
    v = float(m.group(1).replace(",", ".")) * (0.3048 if m.group(2) else 1)
    return v if 0 < v < 700 else None


def kv(s):
    """The highest voltage in an OSM voltage value ('110000', '110000;20000') in kV; 0 = unknown."""
    best = 0.0
    for part in (s or "").split(";"):
        try:
            best = max(best, float(part.strip()) / 1000.0)
        except ValueError:
            pass
    return best


def vclass(v):
    """kV -> the class of obstacle_heights (400, 220, 110, 20, 0.4; 0 = unknown)."""
    return 400 if v >= 300 else 220 if v >= 200 else 110 if v >= 60 else 20 if v >= 1 else 0.4 if v > 0 else 0


def name_of(t):
    return (t.get("name") or "").strip()[:80]


def wind(t):
    return t.get("generator:source") == "wind" or t.get("generator:method") == "wind_turbine"


def tunnel(t):
    return t.get("tunnel") not in (None, "no") or t.get("location") in ("underground", "underwater", "indoor")


def line_kind(t):
    """(kind, kV, type) of a way that is a wire-carrying line, else (None, 0, '')."""
    p = t.get("power")
    if p in ("line", "minor_line") and t.get("location") not in ("underground", "underwater", "indoor"):
        return ("line" if p == "line" else "minor"), kv(t.get("voltage")), ""
    if tunnel(t):
        return None, 0, ""
    r = t.get("railway")
    if r in RAILS and t.get("electrified") == "contact_line":
        return "rail", 0, ""
    if r == "tram":
        return "tram", 0, ""
    if t.get("trolley_wire") == "yes" and "highway" in t:
        return "trolley", 0, ""
    if t.get("aerialway") in LIFTS:
        return "lift", 0, t.get("aerialway")
    return None, 0, ""


def point_kind(t):
    """(kind, type) of an object drawn as a point (a node, or the centre of an outline), else (None, '')."""
    p, mm = t.get("power"), t.get("man_made")
    if p in SUPPORTS:
        return SUPPORTS[p], ""
    if mm == "utility_pole":
        return "upole", ""
    if p == "generator" and wind(t):
        return "turbine", ""
    if t.get("aerialway") == "pylon":
        return "liftpylon", ""
    if mm in MAN_MADE:
        return MAN_MADE[mm], (t.get("tower:type") or "")[:24] if mm == "tower" else ""
    return None, ""


# ---- reading OpenStreetMap -----------------------------------------------------------------

def read_osm(pbf):
    sup = {}      # support node id -> [lon, lat, kind, own height]
    pts = []      # other points: [sort key, lon, lat, kind, own height, name, type]
    lines = []    # [sort key, kind, kV, [(lon, lat)], name, type, node ids or None]
    bways, brel, bad = {}, None, 0
    proc = (osmium.FileProcessor(pbf).with_locations()
            .with_filter(osmium.filter.KeyFilter("power", "man_made", "aerialway", "railway", "trolley_wire",
                                                 "boundary")))
    for o in proc:
        t = o.tags
        if o.is_node():
            kind, ty = point_kind(t)
            if not kind:
                continue
            lon, lat = o.location.lon, o.location.lat
            if kind in ("tower", "pole", "upole", "portal", "catmast"):
                sup[o.id] = [lon, lat, kind, num(t.get("height"))]
            else:
                pts.append(["n%d" % o.id, lon, lat, kind, num(t.get("height")), name_of(t), ty])
        elif o.is_way():
            if t.get("boundary") == "administrative" and t.get("admin_level") == "2":
                bways[o.id] = [(n.ref, n.lon, n.lat) for n in o.nodes if n.location.valid()]
            kind, v, ty = line_kind(t)
            nodes = [n for n in o.nodes if n.location.valid()]
            bad += len(o.nodes) - len(nodes)
            if kind:
                coords = [(n.lon, n.lat) for n in nodes]
                if len(coords) >= 2:
                    refs = [n.ref for n in nodes] if kind in ("line", "minor") else None
                    lines.append(["w%d" % o.id, kind, v, coords, name_of(t), ty, refs])
                continue
            kind, ty = point_kind(t)
            if kind and nodes:   # an outline (a tower, a chimney, a portal ...): its centre
                xy = [(n.lon, n.lat) for n in nodes]
                if len(xy) > 1 and xy[0] == xy[-1]:
                    xy = xy[:-1]
                pts.append(["w%d" % o.id, sum(x for x, _ in xy) / len(xy), sum(y for _, y in xy) / len(xy), kind,
                            num(t.get("height")), name_of(t), ty])
        elif o.is_relation():
            if t.get("boundary") == "administrative" and t.get("admin_level") == "2" and t.get("ISO3166-1") == "BG":
                brel = [(m.ref, m.role) for m in o.members if m.type == "w"]
    if bad:
        print("  %d way nodes without a location (outside the extract) skipped" % bad)
    if not brel:
        raise SystemExit("no border relation of Bulgaria (ISO3166-1=BG, admin_level=2) in the extract")
    return sup, pts, lines, bways, brel


def border_rings(brel, bways, pbf):
    """The closed rings of Bulgaria's border relation, chained from its member ways."""
    need = {w for w, role in brel if role in ("outer", "")}
    missing = need - set(bways)
    if missing:   # members without admin_level=2 on the way itself: a second, slower pass
        print("  %d border ways not tagged admin_level=2: second pass" % len(missing))
        for o in osmium.FileProcessor(pbf).with_locations().with_filter(osmium.filter.EntityFilter(osmium.osm.WAY)):
            if o.id in missing:
                bways[o.id] = [(n.ref, n.lon, n.lat) for n in o.nodes if n.location.valid()]
    pool = [list(bways[w]) for w in need if bways.get(w)]
    rings = []
    while pool:
        ring = pool.pop()
        while ring[0][0] != ring[-1][0]:
            end = ring[-1][0]
            for i, s in enumerate(pool):
                if s[0][0] == end:
                    ring += s[1:]
                    break
                if s[-1][0] == end:
                    ring += s[::-1][1:]
                    break
            else:
                raise SystemExit("the border of Bulgaria does not close (ends at node %d)" % end)
            pool.pop(i)
        rings.append([(x, y) for _, x, y in ring])
    return rings


class Inside:
    """Point in Bulgaria (even-odd over the border rings), with the edges bucketed by latitude."""

    def __init__(self, rings, band=0.01):
        self.band, self.y0, self.idx = band, min(y for r in rings for _, y in r), {}
        for r in rings:
            for (x1, y1), (x2, y2) in zip(r, r[1:]):
                if y1 != y2:
                    lo, hi = sorted((y1, y2))
                    for b in range(int((lo - self.y0) / band), int((hi - self.y0) / band) + 1):
                        self.idx.setdefault(b, []).append((x1, y1, x2, y2))

    def __call__(self, x, y):
        c = False
        for x1, y1, x2, y2 in self.idx.get(int((y - self.y0) / self.band), ()):
            if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                c = not c
        return c


def clip(coords, inside):
    """The parts of a polyline whose segments have at least one end in Bulgaria."""
    ins = [inside(x, y) for x, y in coords]
    parts, cur = [], []
    for i in range(len(coords) - 1):
        if ins[i] or ins[i + 1]:
            if not cur:
                cur = [coords[i]]
            cur.append(coords[i + 1])
        else:
            if len(cur) >= 2:
                parts.append(cur)
            cur = []
    if len(cur) >= 2:
        parts.append(cur)
    return parts


# ---- heights -------------------------------------------------------------------------------

def support_height(kind, v, on_line, on_hv):
    """A typical height for a tower / pole (metres; 0 = none). v = the highest kV of the lines
    through it; on_hv = it carries a power=line (transmission), on_line = any power line."""
    if kind not in ("tower", "pole", "upole"):
        return 0                          # portals, catenary masts: no typical height
    c = vclass(v)
    if c in TOWERS:
        return TOWERS[c]["h"]
    if c in POLES:
        return POLES[c]["h"]
    if kind == "tower" and (on_hv or not on_line):
        return TOWERS[110]["h"]           # a transmission tower of unknown voltage: the lowest class
    return POLE_UNKNOWN if kind != "upole" or on_line else 0   # owner 17.10: the 20 kV pole


def drop_doubles(pts, sup):
    """Drop an outline (way) whose centre lies within SAME_SPOT m of a node, or within SAME_OUTLINE m
    of an earlier outline, of the same kind: the same object mapped twice (e.g. the Ruse TV tower as
    a node and as two outlines). Outlines with a name or a height go first, so those are kept."""
    G, grid = 100.0, {}

    def put(kind, x, y, is_node):
        grid.setdefault((kind, int(x * KX // G), int(y * KY // G)), []).append((x * KX, y * KY, is_node))

    for p in pts:
        if p[0][0] == "n":
            put(p[3], p[1], p[2], True)
    for x, y, kind, _ in sup.values():
        put(kind, x, y, True)
    keep, dropped = [p for p in pts if p[0][0] == "n"], 0
    for p in sorted((p for p in pts if p[0][0] == "w"), key=lambda p: (not p[5], not p[4], p[0])):
        px, py = p[1] * KX, p[2] * KY
        gx, gy = int(px // G), int(py // G)
        if any(math.hypot(px - qx, py - qy) <= (SAME_SPOT if q_node else SAME_OUTLINE)
               for i in (gx - 1, gx, gx + 1) for j in (gy - 1, gy, gy + 1)
               for qx, qy, q_node in grid.get((p[3], i, j), ())):
            dropped += 1
            continue
        put(p[3], p[1], p[2], False)
        keep.append(p)
    return keep, dropped


# ---- ESO -----------------------------------------------------------------------------------

def read_eso(cache):
    path = os.path.join(cache, "eso_lines.json") if cache else os.path.join(tempfile.gettempdir(), "eso_lines.json")
    if not (cache and os.path.exists(path)):
        http(ESO_URL, path)
    try:
        with io.open(path, encoding="utf-8") as f:
            feats = json.load(f).get("features") or []
    except ValueError as e:
        raise SystemExit("ESO's answer is not GeoJSON: %s" % e)
    if len(feats) < 500:
        raise SystemExit("ESO's answer has only %d lines - not used" % len(feats))
    return feats


def eso_pieces(feats, osm_lines, inside):
    """[(kV, name, coords)] = the parts of ESO's built lines farther than ESO_GAP m from every OSM power
    line - minor lines too: ~21 km of ESO's pieces lay on OSM minor lines (the same wires tagged lower)."""
    G = 250.0
    segs, grid = [], {}
    for ln in osm_lines:
        if ln[1] not in ("line", "minor"):
            continue
        pts = [(x * KX, y * KY) for x, y in ln[3]]
        for a, b in zip(pts, pts[1:]):
            i = len(segs)
            segs.append((a, b))
            for gx in range(int(min(a[0], b[0]) // G), int(max(a[0], b[0]) // G) + 1):
                for gy in range(int(min(a[1], b[1]) // G), int(max(a[1], b[1]) // G) + 1):
                    grid.setdefault((gx, gy), []).append(i)

    def near(px, py):
        gx, gy = int(px // G), int(py // G)
        for i in range(gx - 1, gx + 2):
            for j in range(gy - 1, gy + 2):
                for s in grid.get((i, j), ()):
                    (ax, ay), (bx, by) = segs[s]
                    dx, dy = bx - ax, by - ay
                    l2 = dx * dx + dy * dy
                    t = 0.0 if l2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / l2))
                    if math.hypot(px - ax - t * dx, py - ay - t * dy) <= ESO_GAP:
                        return True
        return False

    out, newest = [], ""
    for f in feats:
        p = f.get("properties") or {}
        try:
            built = int(p.get("status")) == 3
        except (TypeError, ValueError):
            built = False
        if not built:
            continue
        newest = max(newest, str(p.get("updated_at") or "")[:10])
        g = f.get("geometry") or {}
        parts = [g.get("coordinates")] if g.get("type") == "LineString" else g.get("coordinates") or []
        for part in parts:
            dense = []   # (lon, lat, is an original vertex)
            for (x1, y1), (x2, y2) in zip(part, part[1:]):
                n = max(1, int(math.ceil(math.hypot((x2 - x1) * KX, (y2 - y1) * KY) / SAMPLE)))
                dense.append((x1, y1, True))
                dense += [(x1 + (x2 - x1) * k / n, y1 + (y2 - y1) * k / n, False) for k in range(1, n)]
            if part:
                dense.append((part[-1][0], part[-1][1], True))
            run = []
            for x, y, orig in dense + [(None, None, None)]:
                if x is not None and not near(x * KX, y * KY):
                    run.append((x, y, orig))
                    continue
                run_m = sum(math.hypot((b[0] - a[0]) * KX, (b[1] - a[1]) * KY) for a, b in zip(run, run[1:]))
                if len(run) >= 2 and run_m >= ESO_MIN:   # keep the run's ends and the original vertices inside it
                    keep = [(rx, ry) for k, (rx, ry, ro) in enumerate(run) if ro or k in (0, len(run) - 1)]
                    for piece in clip(keep, inside):
                        try:
                            volt = float(p.get("volt") or 0)   # ESO gives kV
                        except (TypeError, ValueError):
                            volt = 0.0
                        out.append((volt, (p.get("name") or "").strip()[:80], piece))
                run = []
    merged = merge_eso(out)
    km = sum(math.hypot((b[0] - a[0]) * KX, (b[1] - a[1]) * KY) for _, _, c in merged for a, b in zip(c, c[1:])) / 1000
    return merged, newest, km


def merge_eso(pieces):
    """ESO lists each circuit of a double-circuit line as its own line, so two of its pieces can lie
    on the same towers (e.g. Емона and Иракли). Longest first: the parts of a piece within ESO_SAME m
    of a kept piece are dropped and its name joins that piece's name; the rest is kept when it is
    still ESO_MIN long."""
    G, grid, kept = 100.0, {}, []   # kept: [kV, set of names, coords]

    def length(c):
        return sum(math.hypot((b[0] - a[0]) * KX, (b[1] - a[1]) * KY) for a, b in zip(c, c[1:]))

    def near(px, py):
        gx, gy = int(px // G), int(py // G)
        for i in (gx - 1, gx, gx + 1):
            for j in (gy - 1, gy, gy + 1):
                for k, (ax, ay), (bx, by) in grid.get((i, j), ()):
                    dx, dy = bx - ax, by - ay
                    l2 = dx * dx + dy * dy
                    t = 0.0 if l2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / l2))
                    if math.hypot(px - ax - t * dx, py - ay - t * dy) <= ESO_SAME:
                        return k
        return None

    def add(v, names, coords):
        k = len(kept)
        kept.append([v, set(names), coords])
        pts = [(x * KX, y * KY) for x, y in coords]
        for a, b in zip(pts, pts[1:]):
            for gx in range(int(min(a[0], b[0]) // G), int(max(a[0], b[0]) // G) + 1):
                for gy in range(int(min(a[1], b[1]) // G), int(max(a[1], b[1]) // G) + 1):
                    grid.setdefault((gx, gy), []).append((k, a, b))

    for v, name, coords in sorted(pieces, key=lambda p: -length(p[2])):
        dense = []   # (lon, lat, is an original vertex, the kept piece it lies on or None)
        for (x1, y1), (x2, y2) in zip(coords, coords[1:]):
            n = max(1, int(math.ceil(math.hypot((x2 - x1) * KX, (y2 - y1) * KY) / SAMPLE)))
            dense += [(x1 + (x2 - x1) * k / n, y1 + (y2 - y1) * k / n, k == 0) for k in range(n)]
        dense.append((coords[-1][0], coords[-1][1], True))
        run = []
        for x, y, orig in dense + [(None, None, None)]:
            on = near(x * KX, y * KY) if x is not None else None
            if on is not None:
                kept[on][1].add(name)
                kept[on][0] = max(kept[on][0], v)
            if x is not None and on is None:
                run.append((x, y, orig))
                continue
            part = [(rx, ry) for k, (rx, ry, ro) in enumerate(run) if ro or k in (0, len(run) - 1)]
            if len(part) >= 2 and length(part) >= ESO_MIN:
                add(v, [name], part)
            run = []
    return [(v, " / ".join(sorted(n for n in names if n)), coords) for v, names, coords in kept]


# ---- cells and output ----------------------------------------------------------------------

def cell_of(x, y):
    return int(math.floor((x - X0) / CELL)), int(math.floor((y - Y0) / CELL))


def cut_cells(coords):
    """Split a polyline at the cell borders -> {cell: [polyline, ...]}."""
    out, cur, cc = {}, [], None
    for (x1, y1), (x2, y2) in zip(coords, coords[1:]):
        ts = {0.0, 1.0}
        for a1, a2, a0 in ((x1, x2, X0), (y1, y2, Y0)):
            if a1 != a2:
                for i in range(int(math.floor((min(a1, a2) - a0) / CELL)) + 1, int(math.floor((max(a1, a2) - a0) / CELL)) + 1):
                    t = (a0 + i * CELL - a1) / (a2 - a1)
                    if 0 < t < 1:
                        ts.add(t)
        ts = sorted(ts)
        pt = lambda t: (x1 + (x2 - x1) * t, y1 + (y2 - y1) * t)
        for ta, tb in zip(ts, ts[1:]):
            c = cell_of(*pt((ta + tb) / 2))
            if c != cc:
                if len(cur) >= 2:
                    out.setdefault(cc, []).append(cur)
                cur, cc = [pt(ta)], c
            cur.append(pt(tb))
    if len(cur) >= 2:
        out.setdefault(cc, []).append(cur)
    return out


def ints(coords):
    out = []
    for x, y in coords:
        q = (int(round(x * SCALE)), int(round(y * SCALE)))
        if not out or q != out[-1]:
            out.append(q)
    return out


def trim(rec, defaults):
    """Drop trailing fields that hold their default value (None = a field that always stays)."""
    while rec and defaults[len(rec) - 1] is not None and rec[-1] == defaults[len(rec) - 1]:
        rec.pop()
    return rec


def kv_out(v):
    return int(v) if v == int(v) else round(v, 1)


def dump(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def write_if_changed(path, text):
    if os.path.exists(path):
        with io.open(path, encoding="utf-8") as f:
            if f.read() == text:
                return False
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return True


def main():
    args = sys.argv[1:]

    def opt(name):
        if name in args:
            i = args.index(name)
            v = args[i + 1]
            del args[i:i + 2]
            return v
        return None

    pbf, cache = opt("--pbf"), opt("--cache")
    out_dir = os.path.abspath(args[0] if args else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "obstacles"))
    tmp = None
    if cache:
        os.makedirs(cache, exist_ok=True)
    if not pbf:
        if cache:
            pbf = os.path.join(cache, "bulgaria-latest.osm.pbf")
            if not os.path.exists(pbf):
                http(PBF_URL, pbf)
        else:
            tmp = tempfile.mkdtemp()
            pbf = os.path.join(tmp, "bulgaria-latest.osm.pbf")
            http(PBF_URL, pbf)
    try:
        build(pbf, cache, out_dir)
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)


def build(pbf, cache, out_dir):
    reader = osmium.io.Reader(pbf, osmium.osm.osm_entity_bits.NOTHING)
    osm_ts = reader.header().get("osmosis_replication_timestamp") or ""
    reader.close()
    eso = read_eso(cache)   # before the long part: a source failure writes nothing
    sup, pts, lines, bways, brel = read_osm(pbf)
    inside = Inside(border_rings(brel, bways, pbf))
    pts, doubles = drop_doubles(pts, sup)

    # the voltage of a support = the highest of the power lines through it
    vol, on_line, on_hv = {}, set(), set()
    for ln in lines:
        if ln[6]:
            for r in ln[6]:
                on_line.add(r)
                if ln[1] == "line":
                    on_hv.add(r)
                vol[r] = max(vol.get(r, 0.0), ln[2])

    cells, stats = {}, {}

    def count(key, n=1):
        stats[key] = stats.get(key, 0) + n

    def add_point(key, x, y, kind, own, typical, v, name, ty):
        if not inside(x, y):
            return
        h = int(round(own * 10)) if own else -int(round(typical * 10)) if typical else 0
        count(kind)
        count("height: own" if own else "height: typical" if typical else "height: none")
        cells.setdefault(cell_of(x, y), {"l": [], "p": []})["p"].append(
            (int(round(x * SCALE)), int(round(y * SCALE)), key, kind, h, kv_out(v), name, ty))

    def add_line(key, kind, v, coords, name, ty):
        n = 0
        for part in clip(coords, inside):
            for c, polys in cut_cells(part).items():
                for poly in polys:
                    q = ints(poly)
                    if len(q) >= 2:
                        cells.setdefault(c, {"l": [], "p": []})["l"].append((key, kind, kv_out(v), q, name, ty))
                        n += 1
        if n:
            count(kind)

    orphans, farms_found, wind_own = 0, 0, []
    for r, (x, y, kind, own) in sup.items():
        v = vol.get(r, 0.0)
        if kind == "tower" and r not in on_line and inside(x, y):
            orphans += 1
        add_point("n%d" % r, x, y, kind, own, support_height(kind, v, r in on_line, r in on_hv), v, "", "")
    for key, x, y, kind, own, name, ty in pts:
        typical = 0
        if kind == "turbine":
            farm = FARM.get(key)
            farms_found += bool(farm)
            typical = farm["h"] if farm else WIND["h"]
            ty = farm["key"] if farm else ""
            if own:
                wind_own.append((key, own, typical))
                if own < typical:   # owner 17.10: the higher of the two (OSM heights of 80-105 m are hub heights)
                    own = None
        elif kind == "liftpylon":
            typical = LIFT_PYLON["h"]
        add_point(key, x, y, kind, own, typical, 0, name, ty)
    for key, kind, v, coords, name, ty, _ in lines:
        add_line(key, kind, v, coords, name, ty)
    pieces, eso_date, eso_km = eso_pieces(eso, lines, inside)
    for i, (v, name, coords) in enumerate(sorted(pieces, key=lambda p: (p[1], p[2][0]))):
        add_line("e%05d" % i, "eso", v, coords, name, "")

    files = {}
    for (ix, iy), c in sorted(cells.items()):
        ls = []
        for key, kind, v, q, name, ty in sorted(c["l"], key=lambda r: (r[0], r[3][0])):
            flat = [q[0][0], q[0][1]]
            for (ax, ay), (bx, by) in zip(q, q[1:]):
                flat += [bx - ax, by - ay]
            ls.append(trim([K[kind], v, flat, name, ty], [None, None, None, "", ""]))
        ps, px, py = [], 0, 0
        for x, y, key, kind, h, v, name, ty in sorted(c["p"], key=lambda r: (r[0], r[1], r[2])):
            ps.append(trim([x - px, y - py, K[kind], h, v, name, ty], [None, None, None, 0, 0, "", ""]))
            px, py = x, y
        files["c%d_%d.json" % (ix, iy)] = dump({"lic": LIC, "l": ls, "p": ps})

    meta = {
        "lic": LIC, "attr": "© OpenStreetMap contributors · ЕСО ЕАД (далекопроводи, които липсват в OSM)",
        "src": {"osm": PBF_URL, "eso": ESO_URL}, "eso": eso_date,
        "cell": CELL, "x0": X0, "y0": Y0, "scale": SCALE, "kinds": KINDS,
        "towers": {str(k): {"h": t["h"], "range": t["range"], "low": t["low"]} for k, t in TOWERS.items()},
        "poles": {str(k): p["h"] for k, p in POLES.items()}, "poleUnknown": POLE_UNKNOWN,
        "lift": {"h": LIFT_PYLON["h"], "range": LIFT_PYLON["range"]},
        "wind": {"h": WIND["h"], "range": WIND["range"]},
        "farms": {f["key"]: {"n": f["n"], "m": f["m"], "h": f["h"]} for f in WIND_FARMS},
        "wire": {str(k): w for k, w in WIRE_MIN.items()}, "wireSrc": WIRE_SRC, "wireUrl": WIRE_URL,
        "rail": {"h": RAIL_WIRE["h"], "lc": RAIL_WIRE["lc"], "src": RAIL_WIRE["src"]},
        "cells": [[int(n[1:].split("_")[0]), int(n.split("_")[1][:-5])] for n in sorted(files)],
    }
    meta = json.loads(dump(meta))   # the same types as a file read back

    os.makedirs(out_dir, exist_ok=True)
    changed = [n for n, text in files.items() if write_if_changed(os.path.join(out_dir, n), text)]
    gone = [n for n in os.listdir(out_dir) if re.match(r"^c-?\d+_-?\d+\.json$", n) and n not in files]
    for n in gone:
        os.remove(os.path.join(out_dir, n))
    ipath = os.path.join(out_dir, "index.json")
    old = None
    if os.path.exists(ipath):
        with io.open(ipath, encoding="utf-8") as f:
            old = json.load(f)
    same = old is not None and {k: v for k, v in old.items() if k not in ("changed", "osm")} == meta
    if changed or gone or not same:
        meta.update({"changed": datetime.date.today().isoformat(), "osm": osm_ts})
        write_if_changed(ipath, dump(meta))

    raw = sum(len(t.encode("utf-8")) for t in files.values())
    gz = sum(len(gzip.compress(t.encode("utf-8"), 9)) for t in files.values())
    big = max(files.items(), key=lambda kv_: len(kv_[1]))
    print("OSM data %s, ESO data to %s; %d cells, %.2f MB (%.2f MB gzip); the biggest %s %.0f KB (%.0f KB gzip)"
          % (osm_ts, eso_date, len(files), raw / 1e6, gz / 1e6, big[0], len(big[1].encode("utf-8")) / 1e3,
             len(gzip.compress(big[1].encode("utf-8"), 9)) / 1e3))
    print("ESO pieces not in OSM: %d, %.0f km" % (len(pieces), eso_km))
    print("outlines dropped as doubles of a node: %d; towers on no mapped line: %d; wind-farm turbines found by id: %d of %d"
          % (doubles, orphans, farms_found, len(FARM)))
    if wind_own:
        print("turbines with their own OSM height (own m / typical m): " +
              ", ".join("%s %g/%g" % (k, o, t) for k, o, t in wind_own))
    print("  " + ", ".join("%s %d" % (k, v) for k, v in sorted(stats.items())))
    print("written: %d cells changed, %d removed%s" % (len(changed), len(gone),
                                                       ", index.json updated" if (changed or gone or not same) else ""))


if __name__ == "__main__":
    main()
