"""Airspace structures that the AIP of the Republic of Bulgaria publishes but OpenAIP does not
(ENR 5.1 + 5.2 compared with the airspace layer on 21.10.2026), limited like the rest of the layer
to the zones whose floor is at or below FL180. Reused with the source named, on the strength of
BULATSA's decision № 94-00-1198/19.10.2026, item 3 („НЕ ВЪЗРАЗЯВАМ“ — owner 21.10).

Every entry is copied from the AIP page named in it; check those pages again at every AIRAC
amendment that changes them. make_3d.py inlines AIP_EXTRA_GJ; the map shows ONE zone per name —
an entry here wins over an OpenAIP zone of the same name (owner 21.10).
"""
import json, re

# (name, OpenAIP type: 1 restricted / 2 danger / 8 TRA, lower, upper, AIP page, amendment,
#  lateral limits exactly as printed in the AIP)
AIP_ZONES = [
    ("LBR102", 1, "FL165", "FL425", "ENR 5.1-2", "AIRAC AMDT 07/26",
     # the AIP prints the closing point without its "E"; it is the first point again
     "415703N 0245345E - 415442N 0252432E - 414821N 0255600E - 414300N 0255652E - 413636N 0255727E - "
     "412508N 0254556E - 412408N 0252253E - 413200N 0244706E - 414724N 0243919E - 415703N 0245345E"),
    ("LBD242", 2, "GND", "12000 ft AMSL", "ENR 5.1-11", "AIRAC AMDT 06/26",
     "431241N 0233213E - 431207N 0233152E - 431219N 0233131E - 431246N 0233203E - 431241N 0233213E"),
    ("LBTRA63", 8, "FL135", "FL165", "ENR 5.2-3", "AIRAC AMDT 04/23",
     "423156N 0240449E - 423000N 0241100E - 422229N 0242813E - 421546N 0244329E - 421200N 0245200E - "
     "421228N 0250210E - 421300N 0251400E - 420830N 0252803E - 420339N 0252708E - 415945N 0252624E - "
     "415338N 0252516E - 414638N 0252358E - 414815N 0250613E - 415700N 0244500E - 420220N 0243156E - "
     "420650N 0242535E - 421403N 0241521E - 421849N 0240441E - 421844N 0240112E - 423156N 0240449E"),
    ("LBTRA65", 8, "10500 ft AMSL", "FL165", "ENR 5.2-3", "AIRAC AMDT 04/23",
     "421844N 0240112E - 421849N 0240441E - 421403N 0241521E - 420220N 0243156E - 420554N 0240907E - "
     "421106N 0240217E - 421652N 0240042E - 421844N 0240112E"),
    ("LBTRA74A", 8, "FL135", "FL245", "ENR 5.2-4", "AMDT 188",
     "432059N 0252515E - 432011N 0260122E - 431700N 0260200E - 431500N 0251900E - 431501N 0251325E - "
     "432059N 0252515E"),
    ("LBTRA21C", 8, "FL135", "FL245", "ENR 5.2-5", "AIRAC AMDT 04/23",
     "420450N 0241604E - 420220N 0243156E - 415700N 0244500E - 415338N 0252516E - 415149N 0254600E - "
     "415100N 0255500E - 412500N 0255000E - 412500N 0251900E - 412747N 0250613E - 414033N 0243300E - "
     "415516N 0241526E - 420450N 0241604E"),
    ("LBTRA21E", 8, "FL135", "FL245", "ENR 5.2-6", "AIRAC AMDT 04/23",
     "420554N 0240907E - 420450N 0241604E - 415516N 0241526E - 414033N 0243300E - 414400N 0242400E - "
     "415100N 0241409E - 420554N 0240907E"),
    ("LBTRA34G", 8, "FL175", "FL245", "ENR 5.2-7", "AIRAC AMDT 03/25",
     "422655N 0255930E - 423339N 0264955E - 421000N 0270000E - 421000N 0263038E - 421000N 0262355E - "
     "421000N 0261600E - 421100N 0255300E - 422655N 0255930E"),
]

def _point(lat, lon):
    """'DDMMSSN', 'DDDMMSSE' -> [lon, lat] in degrees, 6 decimals"""
    a = int(lat[0:2]) + int(lat[2:4]) / 60 + int(lat[4:6]) / 3600
    b = int(lon[0:3]) + int(lon[3:5]) / 60 + int(lon[5:7]) / 3600
    return [round(b if lon[7] == "E" else -b, 6), round(a if lat[6] == "N" else -a, 6)]

def _ring(text):
    pts = [_point(m.group(1), m.group(2)) for m in re.finditer(r"(\d{6}[NS])\s+(\d{7}[EW])", text)]
    if len(pts) < 4 or pts[0] != pts[-1]:
        raise SystemExit("aip_extra: an unclosed or short outline: " + text[:40])
    return pts

def geojson():
    return {"type": "FeatureCollection", "features": [
        {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [_ring(lat)]},
         "properties": {"n": n, "t": t, "lo": lo, "up": up, "aip": page + ", " + amdt}}
        for n, t, lo, up, page, amdt, lat in AIP_ZONES]}

AIP_EXTRA_GJ = json.dumps(geojson(), separators=(",", ":"))

# The anti-hail danger areas of AIP ENR 5.1 section 4.1 („Опасни зони (противоградова защита)“,
# GND – 23700 FT AMSL, 01 APR – 30 OCT; read 22.10.2026 from the owner's download). OpenAIP carries
# all 41 under the same names, so only the names are kept: the map adds the AIP's remark on the
# season and the activation to these zones' popups (owner 22.10). Re-check them at every AIRAC.
AIP_ANTIHAIL = [
    "LBD10A", "LBD10B", "LBD10C1", "LBD10D2", "LBD11A1", "LBD11B", "LBD11C2", "LBD11D1",
    "LBD12A2", "LBD12B1", "LBD12C2", "LBD12D4", "LBD13A2", "LBD13B4", "LBD13C2", "LBD13D2",
    "LBD14A", "LBD14B", "LBD15A1", "LBD15C1", "LBD15D1", "LBD16A1", "LBD16B1", "LBD16C",
    "LBD16D", "LBD17A", "LBD17B1", "LBD17C1", "LBD17D", "LBD18A1", "LBD18B2", "LBD18C2",
    "LBD18D1", "LBD19A1", "LBD19B1", "LBD19C1", "LBD19D1", "LBD20A1", "LBD20B1", "LBD20C1",
    "LBD20D2",
]
AIP_ANTIHAIL_JS = json.dumps(AIP_ANTIHAIL, separators=(",", ":"))
