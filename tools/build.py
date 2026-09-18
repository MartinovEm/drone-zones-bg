"""Build the site from the newest data/*.json. With --fetch, first pull the newest
zones from the CAA public GeoServer (uas.caa.bg) and adapt them into data/.
Usage: python tools/build.py [--fetch]   (run from the repo root)"""
import glob, io, os, re, subprocess, sys, urllib.request, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WFS_URL = ("https://uas.caa.bg/geoserver/caa-uas/wfs?service=WFS&version=2.0.0"
           "&request=GetFeature&typeNames=caa-uas:VGeoCAAZonesPublic"
           "&outputFormat=application/json&srsName=EPSG:4326")
# The CAA moved the drone-zone data to uas.caa.bg in 2026; the old caa.bg page is gone.
# The site's "Download JSON" button is client-side - the real public source is this
# anonymous GeoServer WFS layer (plain GET, no key/headers). fetch() adapts its flat
# GeoServer GeoJSON back into the ED-269 shape make_3d.py / make_kml.py already parse.
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
HDRS = {"User-Agent": UA, "Accept": "application/json"}

def _adapt(nf):
    """One GeoServer WFS feature -> one ED-269 feature (the shape make_3d/make_kml parse)."""
    p = nf.get("properties") or {}
    if p.get("is_deleted"):
        return None
    rc = p.get("restriction_code")
    if rc not in ("PROHIBITED", "REQ_AUTHORISATION", "CONDITIONAL"):
        return None
    g = nf.get("geometry") or {}
    if g.get("type") != "Polygon":   # the whole live set is Polygon; skip anything unexpected
        return None
    m = re.search(r"Identifier:\s*([^;]+)", p.get("information") or "")
    ident = m.group(1).strip() if m else str(p.get("zone_id", ""))
    cond = p.get("restriction_conditions")
    conds = [cond.strip()] if isinstance(cond, str) and cond.strip() else []
    if p.get("is_permanent", True):
        applic = [{"permanent": "YES"}]
    else:
        applic = [{"permanent": "NO",
                   "startDateTime": p.get("immediate_period_start") or "",
                   "endDateTime": p.get("immediate_period_end") or ""}]
    return {
        "identifier": ident,
        "country": p.get("region") or "BGR",
        "name": p.get("name") or "?",
        "type": "COMMON",
        "restriction": rc,
        "reason": [],
        "otherReasonInfo": "",
        "uSpaceClass": "YES" if p.get("is_uspace") else "NO",
        "message": p.get("message") or "",
        "applicability": applic,
        "regulationExemption": "NO",
        "zoneAuthority": [{"purpose": p.get("purpose") or "",
                           "name": "ГД ГВА",
                           "contactName": p.get("contact_name") or "",
                           "email": p.get("contact_email") or "",
                           "phone": p.get("contact_phone") or ""}],
        "geometry": [{"uomDimensions": "M",
                      "lowerLimit": p.get("vertical_min_agl") or 0,
                      "lowerVerticalReference": "AGL",
                      "upperLimit": p.get("vertical_max_agl") or 0,
                      "upperVerticalReference": "AGL",
                      "horizontalProjection": {"type": "Polygon", "coordinates": g.get("coordinates")}}],
        "restrictionConditions": conds,
    }

def fetch():
    import json
    raw = urllib.request.urlopen(urllib.request.Request(WFS_URL, headers=HDRS), timeout=120).read()
    src = json.loads(raw.decode("utf-8", "replace"))
    feats = src.get("features") or []
    out = [a for a in (_adapt(nf) for nf in feats) if a]
    out.sort(key=lambda a: a["identifier"])   # stable order run-to-run -> no spurious weekly commit if GeoServer reorders
    if len(out) < 100:   # sanity floor (~879 today): a broken/empty fetch OR a changed feed schema _adapt can't use
        # keep the last good data (exit BEFORE the write) AND fail LOUDLY so the weekly Action goes red -> GitHub emails the owner
        sys.exit("FATAL: WFS returned only %d usable zones (<100) - keeping the last good data, NOT overwriting. The feed is down or its schema changed." % len(out))
    dst = os.path.join(ROOT, "data", "bgr_zones_current.json")
    # "changed" = the date the zone data last really changed (the WFS feed has no version field
    # of its own). Keep the previous date when the new content is identical, so the weekly run
    # neither churns the file nor bumps the shown date on a no-op fetch; advance it only on a
    # real change. This is the page's freshness / staleness signal.
    from datetime import datetime, timezone
    new_sig = json.dumps(out, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    changed = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if os.path.exists(dst):
        try:
            prev = json.load(open(dst, encoding="utf-8"))
            prev_sig = json.dumps(prev.get("features", []), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            if prev_sig == new_sig and prev.get("changed"):
                changed = prev["changed"]
        except Exception:
            pass
    doc = {"changed": changed,
           "description": "Adapted from uas.caa.bg GeoServer WFS (caa-uas:VGeoCAAZonesPublic)",
           "features": out}
    with open(dst, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, separators=(",", ":"))
    print("fetched %d zones from uas.caa.bg (changed %s) -> data/bgr_zones_current.json" % (len(out), changed))

def newest_json():
    cur = os.path.join(ROOT, "data", "bgr_zones_current.json")
    if os.path.exists(cur):
        return cur
    files = sorted(glob.glob(os.path.join(ROOT, "data", "bgr_zones_*.json")),
                   key=lambda p: (re.sub(r".*bgr_zones_(\d{2})(\d{2})(\d{4})\.json", r"\3\2\1", p.replace("\\", "/"))))
    return files[-1]

def _cyr(s):
    return any(0x0400 <= ord(c) <= 0x04FF for c in (s or ""))

def _norm(s):
    return " ".join((s or "").split())

def mymemory_bg_en(text):
    """Translate one Bulgarian string to English via the free MyMemory API (no key).
    Returns '' on any error or quota response, so the caller can retry on a later build."""
    import json, urllib.request, urllib.parse
    try:
        url = "https://api.mymemory.translated.net/get?q=" + urllib.parse.quote(text) + "&langpair=bg|en"
        req = urllib.request.Request(url, headers={"User-Agent": "bgr-drone-zones"})
        d = json.loads(urllib.request.urlopen(req, timeout=30).read().decode("utf-8"))
        if d.get("responseStatus") != 200:
            return ""
        t = ((d.get("responseData") or {}).get("translatedText") or "").strip()
        if not t or t.upper() == text.strip().upper() or "MYMEMORY WARNING" in t.upper() or "QUOTA" in t.upper():
            return ""
        return t
    except Exception as e:
        print("  MT error:", e)
        return ""

def ensure_translations(src):
    """Auto-translate any new Bulgarian zone text (message / conditions / details) to
    English and cache it in tools/zone_i18n_auto.json, so the EN toggle never has to hide
    text. Curated entries in zone_i18n.py always win; anything already cached is skipped.
    Runs on every build, including the weekly GitHub Action, so it is fully automatic."""
    import json, time
    import zone_i18n as z
    auto_path = os.path.join(ROOT, "tools", "zone_i18n_auto.json")
    try:
        auto = json.load(open(auto_path, encoding="utf-8"))
    except Exception:
        auto = {}
    curated = set()
    for m in (z.MSG_EN, z.COND_EN, z.OI_EN):
        for k in m:
            curated.add(_norm(k))
    need, seen = [], set()
    for f in json.load(open(src, encoding="utf-8")).get("features", []):
        vals = [f.get("message"), f.get("otherReasonInfo")] + list(f.get("restrictionConditions") or [])
        for s in vals:
            k = _norm(s)
            if k and _cyr(k) and k not in curated and k not in auto and k not in seen:
                seen.add(k); need.append(k)
    if not need:
        print("auto-translate: nothing new to translate.")
        return
    print("auto-translate: %d new Bulgarian text(s) BG->EN via MyMemory ..." % len(need))
    ok = 0
    for k in need:
        t = mymemory_bg_en(k)
        if t:
            auto[k] = t
            ok += 1
        time.sleep(0.6)
    json.dump(auto, open(auto_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)
    print("auto-translate: cached %d/%d (tools/zone_i18n_auto.json)" % (ok, len(need)))

def check_translations(src):
    """Safety net: report any message/condition still without English (translator was
    unavailable). Such text is hidden in EN and retried on the next build; it is never
    shown in Bulgarian on the EN toggle."""
    import json
    import zone_i18n as z
    try:
        auto = json.load(open(os.path.join(ROOT, "tools", "zone_i18n_auto.json"), encoding="utf-8"))
    except Exception:
        auto = {}
    covered = set(_norm(k) for k in auto)
    for m in (z.MSG_EN, z.COND_EN):
        for k in m:
            covered.add(_norm(k))
    miss = set()
    for f in json.load(open(src, encoding="utf-8")).get("features", []):
        for s in [f.get("message")] + list(f.get("restrictionConditions") or []):
            k = _norm(s)
            if k and _cyr(k) and k not in covered:
                miss.add(k)
    if miss:
        print("\n[!] BG/EN: %d text(s) still without English (translator unavailable);" % len(miss))
        print("    hidden in EN and retried on the next build:")
        for s in sorted(miss):
            print("    " + s)
    else:
        print("\n[ok] BG/EN: every zone message and condition has an English translation.")

if __name__ == "__main__":
    if "--fetch" in sys.argv:
        fetch()
    src = newest_json()
    print("building from:", os.path.basename(src))
    ensure_translations(src)
    tools = os.path.join(ROOT, "tools")
    for script in ("make_3d.py", "make_kml.py"):
        subprocess.check_call([sys.executable, os.path.join(tools, script), src, ROOT])
    check_translations(src)
