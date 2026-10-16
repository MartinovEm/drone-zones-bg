"""Build natura.json - the Natura 2000 information layer of the map.

Usage: python tools/make_natura.py [out_dir] [--cache DIR]
       out_dir defaults to the repo root (next to index.html); --cache keeps the raw
       answers in DIR and reuses them on the next run (no new downloads).

Run by hand when the EEA publishes a new Natura 2000 release (about once a year); the
output is committed. The zone build (build.py) does not touch it.

- Boundaries: the European Environment Agency's "Natura 2000 (vector)" dataset, CC BY 4.0
  (copyright holder DG ENV), REST layer 2 = every site once. Bulgaria only (owner 16.10: a
  layer of rules covers Bulgaria, like the CAA zones), at about 50 m detail; the EEA server
  does the simplification (maxAllowableOffset).
- Names in Bulgarian: the MOEW's open Natura 2000 service (its INSPIRE metadata: "No
  conditions apply to access and use"), joined by site code; the EEA carries Latin names only.
Every Bulgarian site the EEA lists is kept: a site whose simplified shape collapses is
fetched again unsimplified, nothing is dropped.
"""
import datetime, io, json, os, re, sys, time, urllib.parse, urllib.request

EEA = "https://bio.discomap.eea.europa.eu/arcgis/rest/services/ProtectedSites/Natura2000Sites/MapServer"
MOEW = "https://natura2000.egov.bg/arcgis/rest/services/OpenData/ProtectedSitesOpenData_Feature/MapServer"
HDRS = {"User-Agent": "bgr-drone-zones (natura build)"}
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
    time.sleep(1)  # be gentle with the EEA server
    return d


def eea_sites(where, box, level, tag):
    off, prec = level
    p = {"where": where, "geometry": "%s,%s,%s,%s" % box, "geometryType": "esriGeometryEnvelope",
         "inSR": 4326, "spatialRel": "esriSpatialRelIntersects", "outSR": 4326,
         "outFields": "SITECODE,SITENAME,SITETYPE,MS,Area_ha", "returnGeometry": "true",
         "geometryPrecision": prec, "f": "geojson"}
    if off:
        p["maxAllowableOffset"] = off
    d = get(EEA + "/2/query", p, tag)
    if d.get("error") or (d.get("properties") or {}).get("exceededTransferLimit"):
        raise SystemExit("EEA query %s failed or was cut: %s" % (tag, str(d)[:300]))
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


def area_ha(v):
    v = float(v or 0)
    return round(v, 1) if v < 100 else int(round(v))


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


def main():
    global CACHE
    args = sys.argv[1:]
    if "--cache" in args:
        i = args.index("--cache"); CACHE = args[i + 1]; del args[i:i + 2]
        os.makedirs(CACHE, exist_ok=True)
    out_dir = args[0] if args else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

    ms = get(EEA, {"f": "json"}, "eea_service")
    m = re.search(r"dataset:\s*(\d{4})", ms.get("description") or "")
    version = m.group(1) if m else ""

    sites = {f["properties"]["SITECODE"]: f for f in eea_sites("MS='BG'", BOX, FINE, "eea_BG")}
    total = len(sites)

    for code, f in sites.items():
        f["geometry"] = clean_geom(f.get("geometry"))
    bad = sorted(c for c, f in sites.items() if f["geometry"] is None)
    if bad:  # collapsed by the simplification: the same sites again, unsimplified
        print("  %d collapsed shapes -> fetched again unsimplified" % len(bad))
        where = "SITECODE IN (%s)" % ",".join("'%s'" % c for c in bad)
        for f in eea_sites(where, BOX, FULL, "eea_full_%d_%s" % (len(bad), bad[0])):
            g = clean_geom(f.get("geometry"))
            if g:
                sites[f["properties"]["SITECODE"]]["geometry"] = g
    lost = sorted(c for c, f in sites.items() if f["geometry"] is None)
    if lost:
        raise SystemExit("no usable shape for: " + ", ".join(lost))

    names = moew_names()
    feats = []
    for code in sorted(sites):
        p = sites[code]["properties"]
        q = {"c": code, "n": (p.get("SITENAME") or "").strip(), "t": p.get("SITETYPE") or "",
             "m": p.get("MS") or "", "a": area_ha(p.get("Area_ha"))}
        if code in names:
            q["b"] = names[code]
        feats.append({"type": "Feature", "geometry": sites[code]["geometry"], "properties": q})
    nobg = [f["properties"]["c"] for f in feats if "b" not in f["properties"]]
    if nobg:
        print("  WARNING: no MOEW name for %d sites: %s" % (len(nobg), ", ".join(nobg)))

    fc = {"type": "FeatureCollection", "v": version, "built": datetime.date.today().isoformat(), "features": feats}
    path = os.path.join(out_dir, "natura.json")
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(fc, ensure_ascii=False, separators=(",", ":")))
    print("natura.json: %d sites (of %d listed), EEA version %s, %d bytes"
          % (len(feats), total, version or "?", os.path.getsize(path)))


if __name__ == "__main__":
    main()
