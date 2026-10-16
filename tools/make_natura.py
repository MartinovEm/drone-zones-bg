"""Build the map's two nature layers: natura.json (Natura 2000) and protected.json (the
protected territories under the Закон за защитените територии: national and nature parks,
reserves, maintained reserves, protected sites, natural landmarks).

Usage: python tools/make_natura.py [out_dir] [--cache DIR]
       out_dir defaults to the repo root (next to index.html); --cache keeps the raw
       answers in DIR and reuses them on the next run (no new downloads).

Run by hand about once a year (when the EEA publishes a new Natura 2000 release, or the
protected territories change); the outputs are committed. The zone build (build.py) does not
touch them. Both layers cover Bulgaria only (owner 16.10: a layer of rules covers Bulgaria,
like the CAA zones), at about 50 m detail; the servers do the simplification
(maxAllowableOffset). Every area the sources list is kept: a shape that collapses in the
simplification is fetched again unsimplified, nothing is dropped.

- Natura 2000 boundaries: the European Environment Agency's "Natura 2000 (vector)" dataset,
  CC BY 4.0 (copyright holder DG ENV), REST layer 2 = every site once. Names in Bulgarian: the
  MOEW's open Natura 2000 service (its INSPIRE metadata: "No conditions apply to access and
  use"), joined by site code; the EEA carries Latin names only. The map shows when the EEA last
  published the data (owner 16.10); the map service does not carry that date, so it is set here
  from the release's catalogue record, and the script stops when the service starts serving a
  newer release until both settings below are updated.
- Protected territories: the MOEW's open data service (layers 4-7), boundaries + names in
  Bulgarian and Latin; ИАОС's INSPIRE metadata for "Protected Areas in Bulgaria": "No conditions
  apply to access and use". Each one links to its page in the ИАОС register.
- The explicit drone / flight rules (red outlines, quotes, documents) come from nature_bans.py;
  the script stops when one of its entries no longer matches an area.
"""
import datetime, io, json, os, re, sys, time, urllib.parse, urllib.request
from nature_bans import BANS, RESERVE_LAW, HANG, NOTE, NATURA_HANG, REGISTER_FIX

EEA = "https://bio.discomap.eea.europa.eu/arcgis/rest/services/ProtectedSites/Natura2000Sites/MapServer"
MOEW = "https://natura2000.egov.bg/arcgis/rest/services/OpenData/ProtectedSitesOpenData_Feature/MapServer"
MOEW_PA = "https://natura2000.egov.bg/arcgis/rest/services/OpenData/ProtectedAreaOpenData_Feature/MapServer"
MOEW_PA_LAYERS = (7, 6, 5, 4)  # parks, reserves, protected sites, natural landmarks (the point layers 2/3 are empty)
HDRS = {"User-Agent": "bgr-drone-zones (natura build)"}
# the release the map service serves ("dataset: 2024" in its description) and its publication
# date in the EEA catalogue ("Natura 2000 (vector) - version end 2024", published 2025-12-01:
# https://sdi.eea.europa.eu/catalogue/srv/api/records/91357f39-7866-41ce-b447-43905c364ec8)
EEA_RELEASE, EEA_PUBLISHED = "2024", "2025-12-01"
BOX = (14.5, 35.5, 37.0, 49.5)    # the map's data-coverage box (W, S, E, N); Bulgaria lies well inside
FINE = (0.0005, 4)                # maxAllowableOffset (deg, ~50 m), geometryPrecision (~10 m)
FULL = (None, 5)                  # no simplification - the fallback for collapsed shapes

CACHE = None


def get(url, params, tag):
    """GET url?params as JSON (cached under --cache by tag); two retries."""
    path = os.path.join(CACHE, tag + ".json") if CACHE else None
    if path and os.path.exists(path):
        with io.open(path, encoding="utf-8") as f:
            return json.load(f)
    full = url + "?" + urllib.parse.urlencode(params)
    for attempt in range(3):
        try:
            raw = urllib.request.urlopen(urllib.request.Request(full, headers=HDRS), timeout=180).read()
            break
        except Exception as e:
            if attempt == 2:
                raise
            print("  retry (%s): %s" % (tag, e))
            time.sleep(10)
    d = json.loads(raw.decode("utf-8"))
    if path:
        with io.open(path, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False)
    time.sleep(1)  # be gentle with the servers
    return d


def query(url, where, fields, level, tag, box=None):
    """One ArcGIS REST query as GeoJSON in WGS84, simplified by the server at `level`."""
    off, prec = level
    p = {"where": where, "outSR": 4326, "outFields": fields, "returnGeometry": "true", "geometryPrecision": prec, "f": "geojson"}
    if box:
        p.update({"geometry": "%s,%s,%s,%s" % box, "geometryType": "esriGeometryEnvelope", "inSR": 4326,
                  "spatialRel": "esriSpatialRelIntersects"})
    if off:
        p["maxAllowableOffset"] = off
    d = get(url + "/query", p, tag)
    if d.get("error") or (d.get("properties") or {}).get("exceededTransferLimit"):
        raise SystemExit("query %s failed or was cut: %s" % (tag, str(d)[:300]))
    return d.get("features") or []


def area2(r):  # twice the signed area (lon/lat plane): > 0 = counter-clockwise
    return sum(r[i][0] * r[i + 1][1] - r[i + 1][0] * r[i][1] for i in range(len(r) - 1))


def clean_ring(r):
    out = []
    for pt in r:
        pt = [pt[0], pt[1]]
        if not out or pt != out[-1]:
            out.append(pt)
    if out and out[0] != out[-1]:
        out.append(out[0])
    return out if len(out) >= 4 and area2(out) != 0 else None


def clean_geom(g):
    """Polygon/MultiPolygon with closed, de-duplicated rings, outer CCW + holes CW (RFC 7946);
    None when the outer ring collapsed."""
    if not g or g.get("type") not in ("Polygon", "MultiPolygon"):
        return None
    polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
    keep = []
    for poly in polys:
        rings = [clean_ring(r) for r in poly]
        if not rings or rings[0] is None:
            continue
        fixed = []
        for i, r in enumerate(rings):
            if r is None:
                continue
            if (area2(r) > 0) != (i == 0):
                r = r[::-1]
            fixed.append(r)
        keep.append(fixed)
    if not keep:
        return None
    return {"type": "Polygon", "coordinates": keep[0]} if len(keep) == 1 else {"type": "MultiPolygon", "coordinates": keep}


def shapes(feats, key, refetch):
    """Clean every shape; the collapsed ones come again unsimplified (refetch(keys) -> features)."""
    for f in feats:
        f["geometry"] = clean_geom(f.get("geometry"))
    bad = [key(f) for f in feats if f["geometry"] is None]
    if bad:
        print("  %d collapsed shapes -> fetched again unsimplified" % len(bad))
        again = {key(f): clean_geom(f.get("geometry")) for f in refetch(bad)}
        for f in feats:
            if f["geometry"] is None:
                f["geometry"] = again.get(key(f))
    lost = [str(key(f)) for f in feats if f["geometry"] is None]
    if lost:
        raise SystemExit("no usable shape for: " + ", ".join(lost))


def area_ha(v):
    v = float(v or 0)
    return round(v, 1) if v < 100 else int(round(v))


def write(out_dir, name, fc):
    path = os.path.join(out_dir, name)
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(fc, ensure_ascii=False, separators=(",", ":")))
    return os.path.getsize(path)


def moew_names():
    """site code -> Bulgarian name, from the MOEW's SPA + SCI layers."""
    out = {}
    for layer in (11, 12):  # 11 = SPA (birds), 12 = SCI (habitats)
        d = get(MOEW + "/%d/query" % layer, {"where": "1=1", "outFields": "SiteCode,SiteNameBG",
                                             "returnGeometry": "false", "f": "json"}, "moew_%d" % layer)
        for f in d.get("features") or []:
            a = f.get("attributes") or {}
            code, name = (a.get("SiteCode") or "").strip(), (a.get("SiteNameBG") or "").strip()
            if code and name and code not in out:
                out[code] = name
    return out


def build_natura(out_dir):
    ms = get(EEA, {"f": "json"}, "eea_service")
    m = re.search(r"dataset:\s*(\d{4})", ms.get("description") or "")
    version = m.group(1) if m else ""
    if version != EEA_RELEASE:
        raise SystemExit("The EEA map service now serves the Natura 2000 release '%s' (expected '%s'): set "
                         "EEA_RELEASE and EEA_PUBLISHED from that release's catalogue record first." % (version, EEA_RELEASE))
    fields = "SITECODE,SITENAME,SITETYPE,MS,Area_ha"
    feats = query(EEA + "/2", "MS='BG'", fields, FINE, "eea_BG", BOX)
    total = len(feats)
    code = lambda f: f["properties"]["SITECODE"]
    shapes(feats, code, lambda bad: query(EEA + "/2", "SITECODE IN (%s)" % ",".join("'%s'" % c for c in bad),
                                          fields, FULL, "eea_full_%d_%s" % (len(bad), bad[0]), BOX))
    names = moew_names()
    out = []
    for f in sorted(feats, key=code):
        p, c = f["properties"], code(f)
        q = {"c": c, "n": (p.get("SITENAME") or "").strip(), "t": p.get("SITETYPE") or "",
             "m": p.get("MS") or "", "a": area_ha(p.get("Area_ha"))}
        if c in names:
            q["b"] = names[c]
        if c in NATURA_HANG:  # a hang/para-gliding ban in the order: one popup line (drones are not named)
            h = NATURA_HANG[c]; q.update({"h": h["q"], "hd": h["d"], "hu": h["u"]})
        out.append({"type": "Feature", "geometry": f["geometry"], "properties": q})
    missing = sorted(set(NATURA_HANG) - {f["properties"]["c"] for f in out})
    if missing:
        raise SystemExit("nature_bans.NATURA_HANG lists sites the EEA data no longer has: " + ", ".join(missing))
    nobg = [f["properties"]["c"] for f in out if "b" not in f["properties"]]
    if nobg:
        print("  WARNING: no MOEW name for %d sites: %s" % (len(nobg), ", ".join(nobg)))
    size = write(out_dir, "natura.json", {"type": "FeatureCollection", "v": version, "pub": EEA_PUBLISHED,
                                          "built": datetime.date.today().isoformat(), "features": out})
    print("natura.json: %d sites (of %d listed), EEA release %s published %s, %d bytes"
          % (len(out), total, version, EEA_PUBLISHED, size))


def build_protected(out_dir):
    fields = "OBJECTID,NameBg,NameEn,SiteCode,DesigAbbr,DocumentArea"
    out, used = [], set()
    for layer in MOEW_PA_LAYERS:
        url = MOEW_PA + "/%d" % layer
        feats = query(url, "1=1", fields, FINE, "moew_pa_%d" % layer)
        oid = lambda f: f["properties"]["OBJECTID"]
        shapes(feats, oid, lambda bad: query(url, "OBJECTID IN (%s)" % ",".join(str(b) for b in bad), fields, FULL,
                                             "moew_pa_full_%d_%d" % (layer, len(bad))))
        for f in feats:
            p = f["properties"]
            cat, name = (p.get("DesigAbbr") or "").strip(), (p.get("NameBg") or "").strip()
            key = (cat, name)
            if not re.match(r"^BG0[1-6]$", cat):
                raise SystemExit("unexpected category %r for %r" % (cat, name))
            reg = REGISTER_FIX[key] if key in REGISTER_FIX else "%d/%d" % (int(cat[2:]), int(p.get("SiteCode") or 0))
            q = {"i": "L%d-%d" % (layer, p["OBJECTID"]), "n": name, "m": (p.get("NameEn") or "").strip(),
                 "t": cat[2:], "a": area_ha(p.get("DocumentArea")), "r": reg, "k": ""}
            if cat in RESERVE_LAW["cats"]:  # every activity outside the law's closed list is banned
                q.update({"k": "f", "l": 1})
            if key in BANS:
                b = BANS[key]
                q.update({"k": "f" if b["kind"] == "full" else "p", "q": b["q"], "qe": b["e"], "d": b["d"], "u": b["u"]})
                if b.get("w"):
                    q["w"] = b["w"]
            if key in HANG:
                q["h"] = HANG[key]
            if key in NOTE:
                x = NOTE[key]; q.update({"x": x["q"], "xe": x["e"], "xd": x["d"], "xu": x["u"]})
            used.add(key)
            out.append({"type": "Feature", "geometry": f["geometry"], "properties": q})
    missing = sorted(k for k in set(BANS) | set(HANG) | set(NOTE) | set(REGISTER_FIX) if k not in used)
    if missing:
        raise SystemExit("nature_bans entries that match no area any more: %s" % missing)
    size = write(out_dir, "protected.json", {"type": "FeatureCollection", "built": datetime.date.today().isoformat(), "features": out})
    count = lambda pred: sum(1 for f in out if pred(f["properties"]))
    print("protected.json: %d areas (parks %d, reserves %d, protected sites %d, natural landmarks %d); red %d, dashed %d; %d bytes"
          % (len(out), count(lambda p: p["t"] in ("02", "05")), count(lambda p: p["t"] in ("01", "04")),
             count(lambda p: p["t"] == "06"), count(lambda p: p["t"] == "03"),
             count(lambda p: p["k"] == "f"), count(lambda p: p["k"] == "p"), size))


def main():
    global CACHE
    args = sys.argv[1:]
    if "--cache" in args:
        i = args.index("--cache"); CACHE = args[i + 1]; del args[i:i + 2]
        os.makedirs(CACHE, exist_ok=True)
    out_dir = args[0] if args else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    build_natura(out_dir)
    build_protected(out_dir)


if __name__ == "__main__":
    main()
