"""Convert the CAA ED-269 drone-zones JSON to a colored KML (for Google Earth).
Usage: python make_kml.py <bgr_zones.json> <out_dir>"""
import json, math, sys, os
from xml.sax.saxutils import escape

src, outdir = sys.argv[1], sys.argv[2]
d = json.load(open(src, encoding="utf-8"))
stamp = d.get("title", "").replace("BGRZoneVersion", "").strip()

STYLES = {"PROHIBITED": ("ff2020ff", "332020ff"), "REQ_AUTHORISATION": ("ff0080ff", "330080ff"), "CONDITIONAL": ("ff00ccff", "3300ccff")}
BG = {"PROHIBITED": "ЗАБРАНЕНИ", "REQ_AUTHORISATION": "С РАЗРЕШЕНИЕ", "CONDITIONAL": "УСЛОВНИ"}

def rings_of(geo):
    hp = geo["horizontalProjection"]
    if hp["type"] == "Circle":
        cx, cy = hp["center"]; r = hp["radius"]
        pts = []
        for i in range(65):
            a = 2 * math.pi * i / 64
            dy = r * math.cos(a) / 111320.0
            dx = r * math.sin(a) / (111320.0 * math.cos(math.radians(cy)))
            pts.append((cx + dx, cy + dy))
        return [pts]
    return [[(p[0], p[1]) for p in rng] for rng in hp["coordinates"]]

folders = {k: [] for k in STYLES}
def _lim(geo):
    lo = geo.get("lowerLimit") or 0; up = geo.get("upperLimit") or 0
    one = lambda v: "GND" if v == 0 else ("%s m" % v)   # CAA labels ground level as GND
    ref = geo.get("upperVerticalReference", "") or ""
    return one(lo) + " – " + one(up) + (" " + ref if (lo or up) else "")

for f in d["features"]:
    r = f.get("restriction")
    if r not in STYLES:
        continue
    geo = f["geometry"][0] if isinstance(f["geometry"], list) else f["geometry"]
    rings = rings_of(geo)
    desc = escape(f"{f.get('message','')}\n{_lim(geo)}\nID {f.get('identifier','')} / {f.get('name','')}")
    h = geo.get("upperLimit"); h = 120 if h is None else h  # real upper limit (m AGL) — the whole point of the 3D view
    coord = " ".join(f"{x:.6f},{y:.6f},{h}" for x, y in rings[0])
    inner = "".join(f"<innerBoundaryIs><LinearRing><coordinates>{' '.join(f'{x:.6f},{y:.6f},{h}' for x,y in rg)}</coordinates></LinearRing></innerBoundaryIs>" for rg in rings[1:])
    volume = f"<Polygon><extrude>1</extrude><tessellate>1</tessellate><altitudeMode>relativeToGround</altitudeMode><outerBoundaryIs><LinearRing><coordinates>{coord}</coordinates></LinearRing></outerBoundaryIs>{inner}</Polygon>"
    # crisp footprint outline clamped to the terrain, so the on-ground boundary stays sharp at any angle (never smears)
    ground = "".join(f"<LineString><tessellate>1</tessellate><coordinates>{' '.join(f'{x:.6f},{y:.6f},0' for x,y in rg)}</coordinates></LineString>" for rg in rings)
    folders[r].append(f"<Placemark><name>{escape(str(f.get('name','?')))}</name><styleUrl>#{r}</styleUrl>"
                      f"<description>{desc}</description><MultiGeometry>{volume}{ground}</MultiGeometry></Placemark>")

kml = [f'<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Дрон зони България (ГВА)</name>']
for r, (line, poly) in STYLES.items():
    kml.append(f'<Style id="{r}"><LineStyle><color>{line}</color><width>1.5</width></LineStyle><PolyStyle><color>{poly}</color></PolyStyle></Style>')
for r in STYLES:
    kml.append(f"<Folder><name>{BG[r]} ({len(folders[r])})</name>{''.join(folders[r])}</Folder>")
kml.append("</Document></kml>")
os.makedirs(outdir, exist_ok=True)
out = os.path.join(outdir, "bgr_drone_zones.kml")
open(out, "w", encoding="utf-8").write("".join(kml))
print("bgr_drone_zones.kml:", os.path.getsize(out) // 1024, "KB,", sum(len(v) for v in folders.values()), "zones, version:", stamp)
