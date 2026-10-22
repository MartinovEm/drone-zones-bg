"""Regenerate data/bg_oblasts.json - Bulgaria's 28 oblasts for the weather-warnings layer.

One-time helper (NOT part of build.py; re-run only if the oblast borders change). The
official weather warnings (NIMH, published by Meteoalarm, served by the relay route
/warnings) are issued per oblast and name it by its NUTS3 code; the map colours these
polygons. Meteoalarm's own warning areas are rough outlines (15-58 points per oblast,
borders up to 8.5 km off - compared 22.10.2026), so the borders come from OpenStreetMap
(ODbL - credited on the map as "OpenStreetMap contributors"): ONE Nominatim lookup of the
28 oblast relations, simplified together as a coverage, so neighbours keep one shared
border (no gaps, no overlaps). Each feature carries its NUTS3 code and the BG / EN name
as the Meteoalarm feed spells it.

The table: the OSM relation of each oblast from Wikidata (P402, by ISO 3166-2 BG-01 ...
BG-28) and its NUTS3 code from the Meteoalarm Bulgaria feed of 22.10.2026 (matched by
name; Sofia oblast = the one code left, BG412). Deterministic + re-runnable.

Run:  python tools/make_oblasts.py   ->  writes data/bg_oblasts.json
"""
import json
import os
import urllib.parse
import urllib.request

import shapely
from shapely.geometry import mapping, shape

OUT = os.path.join(os.path.dirname(__file__), "..", "data", "bg_oblasts.json")
NOMINATIM = "https://nominatim.openstreetmap.org/lookup"
UA = {"User-Agent": "bgr-drone-zones-build/1.0"}
SIMPLIFY = 0.004  # coverage simplification (shapely: ~ the square root of the smallest kept triangle's area, deg); 22.10: ~9.4k points, ~164 KB, borders at most ~1 km from the full OSM ones
DIGITS = 4        # ~11 m

# ISO 3166-2, OSM relation, NUTS3, BG + EN name as in the Meteoalarm feed
OBLASTS = [
    ("BG-01", 1739521, "BG413", "Благоевград", "Blagoevgrad"),
    ("BG-02", 1739523, "BG341", "Бургас", "Burgas"),
    ("BG-03", 1437135, "BG331", "Варна", "Varna"),
    ("BG-04", 1739524, "BG321", "Велико Търново", "Veliko Tarnovo"),
    ("BG-05", 1739525, "BG311", "Видин", "Vidin"),
    ("BG-06", 1739526, "BG313", "Враца", "Vratsa"),
    ("BG-07", 1739527, "BG322", "Габрово", "Gabrovo"),
    ("BG-08", 1739528, "BG332", "Добрич", "Dobrich"),
    ("BG-09", 1739529, "BG425", "Кърджали", "Kardzhali"),
    ("BG-10", 1739530, "BG415", "Кюстендил", "Kyustendil"),
    ("BG-11", 1739531, "BG315", "Ловеч", "Lovech"),
    ("BG-12", 1739532, "BG312", "Монтана", "Montana"),
    ("BG-13", 1739533, "BG423", "Пазарджик", "Pazardzhik"),
    ("BG-14", 1739534, "BG414", "Перник", "Pernik"),
    ("BG-15", 1739535, "BG314", "Плевен", "Pleven"),
    ("BG-16", 1739536, "BG421", "Пловдив", "Plovdiv"),
    ("BG-17", 1739537, "BG324", "Разград", "Razgrad"),
    ("BG-18", 1739538, "BG323", "Русе", "Ruse"),
    ("BG-19", 1739539, "BG325", "Силистра", "Silistra"),
    ("BG-20", 1739540, "BG342", "Сливен", "Sliven"),
    ("BG-21", 1739541, "BG424", "Смолян", "Smolyan"),
    ("BG-22", 1739543, "BG411", "София град", "Sofia-city"),
    ("BG-23", 1739542, "BG412", "Софийска област", "Sofia-region"),
    ("BG-24", 1300657, "BG344", "Стара Загора", "Stara Zagora"),
    ("BG-25", 1739544, "BG334", "Търговище", "Targovishte"),
    ("BG-26", 1739545, "BG422", "Хасково", "Haskovo"),
    ("BG-27", 1739546, "BG333", "Шумен", "Shumen"),
    ("BG-28", 1739547, "BG343", "Ямбол", "Yambol"),
]


def fetch():
    q = urllib.parse.urlencode({"osm_ids": ",".join("R%d" % o[1] for o in OBLASTS),
                                "format": "geojson", "polygon_geojson": 1})
    req = urllib.request.Request(NOMINATIM + "?" + q, headers=UA)
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.load(r)["features"]


def rounded(g):
    def rnd(c):
        return [round(c[0], DIGITS), round(c[1], DIGITS)] if isinstance(c[0], float) else [rnd(x) for x in c]
    m = mapping(g)
    return {"type": m["type"], "coordinates": rnd(m["coordinates"])}


def main():
    got = {int(f["properties"]["osm_id"]): shape(f["geometry"]) for f in fetch()}
    missing = [o for o in OBLASTS if o[1] not in got]
    if missing:
        raise SystemExit("Nominatim gave no polygon for: " + ", ".join(o[0] for o in missing))
    geoms = [shapely.make_valid(got[o[1]]) for o in OBLASTS]
    simple = shapely.coverage_simplify(geoms, SIMPLIFY)
    feats = [{"type": "Feature", "properties": {"nuts": o[2], "bg": o[3], "en": o[4]}, "geometry": rounded(g)}
             for o, g in zip(OBLASTS, simple)]
    out = {"type": "FeatureCollection",
           "source": "OpenStreetMap contributors (ODbL), via Nominatim; NUTS3 codes as in the Meteoalarm Bulgaria feed",
           "features": feats}
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")
    pts = sum(int(shapely.get_num_coordinates(g)) for g in simple)
    print("data/bg_oblasts.json: %d oblasts, %d points, %d KB" % (len(feats), pts, os.path.getsize(OUT) // 1024))


if __name__ == "__main__":
    main()
