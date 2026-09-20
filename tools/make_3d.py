"""Build the 3D drone-zones page (MapLibre GL: ESRI imagery + AWS terrarium terrain,
zones as flat fills draped on the terrain, plus OpenFreeMap 3D buildings at close zoom).
Usage: python make_3d.py <bgr_zones.json> <out_dir>"""
import json, math, sys, os, urllib.parse
from zone_i18n import AUTH_EN, en_text, FREEMAIL
from weather_widget import WX_CSS, WX_HTML, WX_JS, WX_LAYERS_JS_3D
from settings_store import ST_JS
from ui_shell import (SHELL_CSS, SHELL_JS, LOUPE_HTML, MENUBTN_HTML, PLNBTN_HTML,
                      OGNBTN_HTML, GJBTN_HTML, LANG_HTML, CTRHAIR_HTML, FSBTN_HTML, panel_html, ZONE_CHIPS, BUILDINGS_CHIP,
                      AIRSPACE_SECTION, NOTAM_SECTION)

src, outdir = sys.argv[1], sys.argv[2]
d = json.load(open(src, encoding="utf-8"))
changed = d.get("changed", "")   # date the zone data last really changed (freshness signal)
datespan = ' · <span data-i18n="ddate">синхронизация от __CHANGED__</span>' if changed else ''

def circle_ring(cx, cy, r):
    pts = []
    for i in range(65):
        a = 2 * math.pi * i / 64
        dy = r * math.cos(a) / 111320.0
        dx = r * math.sin(a) / (111320.0 * math.cos(math.radians(cy)))
        pts.append([round(cx + dx, 6), round(cy + dy, 6)])
    return pts

def extras(f):
    za = (f.get("zoneAuthority") or [{}])[0] or {}
    season = ""
    for a in (f.get("applicability") or []):
        if isinstance(a, dict) and a.get("permanent") == "NO" and a.get("startDateTime"):
            season = a.get("startDateTime", "")[:10] + " → " + a.get("endDateTime", "")[:10]
    conds = f.get("restrictionConditions") or []
    oi = f.get("otherReasonInfo", "") or ""
    name = za.get("name", "")
    cn = za.get("contactName", "") or ""       # the contact PERSON (owner: keep it, it's in the official data)
    em = za.get("email", "") or ""
    ph = za.get("phone", "") or ""
    return {
        "rs": f.get("reason") or [],
        "oi": oi, "oie": en_text(oi),
        "pu": za.get("purpose", ""),
        "au": name, "aue": AUTH_EN.get(name, name), "cn": cn,
        "em": em, "ph": ph,
        "co": " ".join(conds) if conds else "",
        "coe": " ".join(filter(None, (en_text(c) for c in conds))),
        "se": season,
        "me": en_text(f.get("message") or ""),
    }

def _lim(lo, up, ref):
    lo = lo or 0; up = up or 0
    one = lambda v: "GND" if v == 0 else ("%s m" % v)   # CAA labels ground level as GND
    return one(lo) + " – " + one(up) + (" " + ref if (lo or up) and ref else "")

feats = []
for f in d["features"]:
    r = f.get("restriction")
    if r not in ("PROHIBITED", "REQ_AUTHORISATION", "CONDITIONAL"):
        continue
    geo = f["geometry"][0] if isinstance(f["geometry"], list) else f["geometry"]
    hp = geo["horizontalProjection"]
    if hp["type"] == "Circle":
        rings = [circle_ring(hp["center"][0], hp["center"][1], hp["radius"])]
    else:
        rings = [[[round(p[0], 6), round(p[1], 6)] for p in rng] for rng in hp["coordinates"]]
    up = geo.get("upperLimit"); up = 120 if up is None else up   # faithful: a real 0 ceiling stays 0 (do not invent 120)
    props = {"n": f.get("name", "?"), "r": r, "m": f.get("message", ""),
             "lim": _lim(geo.get('lowerLimit'), up, geo.get('upperVerticalReference', '') or ''),
             "id": f.get("identifier", "")}
    props.update(extras(f))
    props["fi"] = len(feats)
    feats.append({"type": "Feature", "properties": props,
                  "geometry": {"type": "Polygon", "coordinates": rings}})

gj = json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False, separators=(",", ":"))
# Bulgaria border outline (data/bg_outline.geojson, built by tools/make_bg_outline.py):
# the "land" borders are drawn in a per-basemap colour, the Danube as a blue river line,
# the Black Sea coast is left unlined. Not zone data - a public OSM boundary, credited.
try:
    bgout = open(os.path.join(os.path.dirname(src), "bg_outline.geojson"), encoding="utf-8").read().strip()
except OSError:
    bgout = '{"type":"FeatureCollection","features":[]}'

FAV = "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'><g stroke='royalblue' stroke-width='3' fill='none' stroke-linecap='round'><path d='M14 14 34 34M34 14 14 34'/><circle cx='12' cy='12' r='7'/><circle cx='36' cy='12' r='7'/><circle cx='12' cy='36' r='7'/><circle cx='36' cy='36' r='7'/></g><rect x='18' y='18' width='12' height='12' rx='3' fill='royalblue'/></svg>"
favicon = "data:image/svg+xml," + urllib.parse.quote(FAV)

html = r"""<!DOCTYPE html>
<html lang="bg"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Дрон зони в България</title>
<link rel="icon" href="__FAVICON__">
<link rel="stylesheet" href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css">
<script src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js"></script>
<style>
*{box-sizing:border-box}
html,body{height:100%;margin:0}
#map{position:absolute;inset:0}
/* center + : white with a dark glow so it reads on the satellite (HRMG style);
   above the wind canvas (5), below MapLibre popups (10) */
#ctrhair{z-index:6;color:#fff;text-shadow:0 0 3px rgba(0,0,0,.85)}
.wx2d #ctrhair{color:#1c1c1e;text-shadow:0 0 3px #fff,0 0 2px #fff} /* dark "+" on the flat OSM 2D basemap */
#info{position:absolute;left:10px;bottom:10px;z-index:1000;max-width:min(340px,calc(100% - 20px));width:fit-content;
 background:var(--glass-weak);
 border-radius:10px;box-shadow:0 2px 10px rgba(0,0,0,.15);padding:6px 9px;
 font:9.5px/1.35 system-ui,'Segoe UI',Roboto,sans-serif;color:var(--fg)}
#info a{color:var(--accent)}
#info .src{font-weight:600}
#info .ihint{color:var(--accent);font-weight:600;margin-bottom:3px}
.maplibregl-popup{z-index:10}
.maplibregl-popup-content{font:13px/1.4 system-ui,'Segoe UI',Roboto,sans-serif;max-height:70vh;overflow:auto}
.maplibregl-popup-content a{color:var(--accent)} /* readable in light AND dark; overrides the browser's dark-purple "visited" link */
.maplibregl-ctrl-attrib{font-size:9px}
/* The wind particle canvas sits at z-index:5 over the map. MapLibre's bottom-right
   control corner is its OWN z-index:2 stacking context, so a z-index on the
   attribution alone stays trapped below the wind. Lift the whole corner above the
   wind instead, so the open credit (and the zoom) are never covered. */
.maplibregl-ctrl-bottom-right{z-index:6}
/* opaque attribution panel when expanded (it collapses to the ⓘ, like 2D) */
.maplibregl-ctrl-attrib.maplibregl-compact-show{background:var(--glass-strong)}
/* custom scale line by the ⓘ (bottom-right): no box, fixed-width bar, only the
   number changes; colour follows the mode (white on satellite, dark on OSM) */
#wxscale{position:absolute;right:44px;bottom:12px;z-index:6;pointer-events:none;
 font:600 10px/1.3 system-ui,'Segoe UI',Roboto,sans-serif;color:#fff;text-align:center}
#wxscale .lbl{display:block;text-shadow:0 0 2px rgba(0,0,0,.9),0 0 2px rgba(0,0,0,.9);margin-bottom:1px}
#wxscale .bar{display:block;height:5px;border:1.5px solid #fff;border-top:none;
 box-shadow:0 0 2px rgba(0,0,0,.8);margin:0 auto} /* width set by JS to a round distance */
.wx2d #wxscale{color:#1c1c1e}
.wx2d #wxscale .lbl{text-shadow:0 0 2px #fff,0 0 2px #fff}
.wx2d #wxscale .bar{border-color:#1c1c1e;box-shadow:0 0 2px #fff}
/* measure tool ("линийка"): draggable cyan pins + plain distance numbers */
.rpin{cursor:grab;-webkit-touch-callout:none;-webkit-user-select:none;user-select:none}
.rpin:active{cursor:grabbing}
.rpin svg{display:block;filter:drop-shadow(0 1px 2px rgba(0,0,0,.4))}
/* distance numbers: no bubble; colour follows the BASEMAP (white on the 3D
   satellite, dark on the light 2D OSM) with a contrast halo so they stay readable */
.rlbl{font:600 12px/1 system-ui,'Segoe UI',Roboto,sans-serif;color:#fff;white-space:nowrap;
 pointer-events:none;text-shadow:0 0 3px rgba(0,0,0,.95),0 0 2px rgba(0,0,0,.95)}
.wx2d .rlbl{color:#12232b;text-shadow:0 0 3px #fff,0 0 3px #fff,0 0 2px #fff}
.rlbl b{font-weight:800}
.ruler-on .maplibregl-canvas-container,.ruler-on .maplibregl-canvas{cursor:crosshair!important}
.zlh{font-weight:700;margin-bottom:5px}
.zpick{padding:5px 4px;cursor:pointer;border-radius:6px;display:flex;align-items:center;gap:7px}
.zpick:hover{background:var(--sug-hover)}
.pdot{width:11px;height:11px;border-radius:50%;flex:none}
.ptype{color:var(--muted);font-size:12px}
.zback{color:var(--accent);cursor:pointer;font-weight:600;margin-bottom:5px}
@media (max-width:640px){
 #info{font-size:8px;max-width:70vw;max-height:24vh;overflow:auto;padding:4px 7px} /* same size as the map attribution */
 .maplibregl-ctrl-attrib{max-width:38vw;max-height:30vh;overflow:auto;font-size:8px;line-height:1.3}
 .maplibregl-popup-content{max-height:42vh;font-size:11px;line-height:1.4;max-width:66vw;padding:7px 9px}
 .maplibregl-popup{max-width:calc(100vw - 20px)!important}
 .ptype{font-size:10.5px}
}
/*__SHELL_CSS__*/
/*__WX_CSS__*/
</style></head><body>
<div id="leftui">
 <!--__WX_HTML__-->
 <!--__MENUBTN__-->
 <!--__PANEL__-->
 <!--__LOUPE__-->
 <!--__GJBTN__-->
 <!--__PLNBTN__-->
 <!--__OGNBTN__-->
</div>
<div id="rightui">
 <!--__LANG__-->
 <span class="seg"><a id="to2d">2D</a><a id="to3d" class="on">3D</a></span>
 <div id="bmwrap"><button id="bmbtn" class="pill icon" aria-label="base map" title=""><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg></button><div id="bmpanel" hidden></div></div>
 <!--__FSBTN__-->
 <button id="rulerbtn" class="pill icon" aria-label="measure" title=""><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21.3 15.3a2.4 2.4 0 0 1 0 3.4l-2.6 2.6a2.4 2.4 0 0 1-3.4 0L2.7 8.7a2.4 2.4 0 0 1 0-3.4l2.6-2.6a2.4 2.4 0 0 1 3.4 0Z"/><path d="m14.5 12.5 2-2"/><path d="m11.5 9.5 2-2"/><path d="m8.5 6.5 2-2"/><path d="m17.5 15.5 2-2"/></svg></button>
</div>
<div id="map"></div>
<!--__CTRHAIR__-->
<div id="wxscale"><span class="lbl"></span><span class="bar"></span></div>
<div id="wxgjlegend" hidden>
 <button id="wxgjday" type="button"><span>📅</span> <span id="wxgjdaylbl"></span> <span class="car">▾</span></button>
 <div class="wxgjrow">
  <span class="wxlg"><i style="background:#8a9098"></i><span data-wxl="gjX"></span></span>
  <span class="wxlg"><i style="background:#5bb56a"></i><span data-wxl="gjG"></span></span>
  <span class="wxlg"><i style="background:#e8c528"></i><span data-wxl="gjY"></span></span>
  <span class="wxlg"><i style="background:#e03434"></i><span data-wxl="gjR"></span></span>
 </div>
 <span class="gjnote"><span data-wxl="gjNote"></span> <b id="wxgjdate"></b></span>
 <div id="wxgjcal" hidden>
  <div id="wxgjwin"><button type="button" data-w="12" data-wxl="gjW12"></button><button type="button" data-w="24" data-wxl="gjW24"></button></div>
  <button id="wxgjlive" type="button" data-wxl="gjLive"></button>
  <div id="wxgjgrid"></div>
 </div>
</div>
<div id="info"><button id="infotoggle" type="button" aria-label="info" title="">!</button><div class="infobody"><div class="ihint" data-i18n="clickhint">Клик върху зона за повече информация</div><span class="src" data-i18n="src">Източник Зони: ГД ГВА</span> (<a href="https://uas.caa.bg" target="_blank" rel="noopener">uas.caa.bg</a>)__DATESPAN__<br><span data-i18n-html="disc">Неофициална визуализация. Преди полет е задължителна проверка на официалния източник и <a href="https://b-flip.bulatsa.com" target="_blank" rel="noopener">B-FLIP</a> (NOTAM, активни зони).</span></div></div>
<script>
//__ST_JS__
var Z = {type: 'FeatureCollection', features: []}; // zones are fetched from zones.json once the map starts (keeps index.html small -> fast first paint / LCP)
var BGOUT = __BGOUTLINE__; // BG border outline: "land" (per-basemap colour) + "danube" (blue); see tools/make_bg_outline.py
var T = {
 bg:{brand:'Дрон зони в България',menu:'Меню',fP:'Забранени',fA:'С разрешение',fC:'Условни',bld:'Сгради',
     kml:'KML за Google Earth',hint:'десен бутон = въртене/наклон',search:'Търсене на локация…',loc:'Къде съм',
     ddate:'синхронизация от __CHANGED__',src:'Източник Зони: ГД ГВА',here:'Вие сте тук',
     clickhint:'Клик върху зона за повече информация',reason:'Причина',cond:'Условия',active:'Активна',contact:'Контакт',height:'Височина',details:'Детайли',authFrom:'Разрешение от',notify:'Уведоми',info:'Информация',zonesHere:'зони тук',backList:'назад',reset:'Нулиране',ruler:'Линийка',secZones:'Зони',secTheme:'Тема',thmAuto:'Авто',secTools:'Инструменти',secLang:'Език',bmMap:'Основна карта',bmHead:'Основа',bmSat:'Сателит',bmDark:'Тъмна',secFL:'Височина на самолетите (FL)',flnote:'активно само при включени ✈ самолети',moreinfo:'Повече информация и източници',
     secAir:'Въздушно пространство',airCtrl:'Контролирано',airSpec:'Специални зони',airLegRPD:'забранени / ограничени / опасни',airMil:'военни',airFL180:'Показва се само до FL180 (18 000 ft)',
     secNotam:'NOTAM (временни)',ntShow:'NOTAM',ntP:'забранена',ntD:'опасна',ntR:'ограничена (щрих)',ntM:'военна/сегрегирана',ntW:'предупреждение',ntO:'препятствие',ntUpc:'приглушените са предстоящи (все още неактивни)',ntSrc:'Международна серия (FAA)',
     disc:'Неофициална визуализация. Преди полет е задължителна проверка на официалния източник и <a href="https://b-flip.bulatsa.com" target="_blank" rel="noopener">B-FLIP</a> (NOTAM, активни зони).',
     tP:'ЗАБРАНЕНА',tA:'НЕОБХОДИМО РАЗРЕШЕНИЕ',tC:'УСЛОВНА'},
 en:{brand:'Bulgaria Drone Zones',menu:'Menu',fP:'Prohibited',fA:'Authorisation',fC:'Conditional',bld:'Buildings',
     kml:'KML for Google Earth',hint:'right-drag = rotate/tilt',search:'Search for a place…',loc:'Where am I',
     ddate:'synced from __CHANGED__',src:'Zones source: Bulgarian CAA',here:'You are here',
     clickhint:'Click a zone for more info',reason:'Reason',cond:'Conditions',active:'Active',contact:'Contact',height:'Height',details:'Details',authFrom:'Authorisation from',notify:'Notify',info:'Information',zonesHere:'zones here',backList:'back',reset:'Reset',ruler:'Measure',secZones:'Zones',secTheme:'Theme',thmAuto:'Auto',secTools:'Tools',secLang:'Language',bmMap:'Base map',bmHead:'Base map',bmSat:'Satellite',bmDark:'Dark',secFL:'Aircraft height (FL)',flnote:'active only when ✈ aircraft are on',moreinfo:'More info & sources',
     secAir:'Airspace',airCtrl:'Controlled',airSpec:'Special-use',airLegRPD:'prohibited / restricted / danger',airMil:'military',airFL180:'Shown up to FL180 only',
     secNotam:'NOTAM (temporary)',ntShow:'NOTAM',ntP:'prohibited',ntD:'danger',ntR:'restricted (hatch)',ntM:'military/segregated',ntW:'warning',ntO:'obstacle',ntUpc:'muted = upcoming (not yet active)',ntSrc:'International series (FAA)',
     disc:'Unofficial visualization. Before flying, check the official source and <a href="https://b-flip.bulatsa.com" target="_blank" rel="noopener">B-FLIP</a> (NOTAM, active zones).',
     tP:'PROHIBITED',tA:'AUTHORISATION REQUIRED',tC:'CONDITIONAL'}
};
var RSN = {PRIVACY:{bg:'лични данни',en:'privacy'},SENSITIVE:{bg:'чувствителен обект',en:'sensitive site'},AIR_TRAFFIC:{bg:'въздушен трафик',en:'air traffic'},FOREIGN_TERRITORY:{bg:'чужда територия',en:'foreign territory'},NATURE:{bg:'природа',en:'nature'}};
var COL = {PROHIBITED:'#ff2020', REQ_AUTHORISATION:'#ff8000', CONDITIONAL:'#ffcc00'};  // bright, vivid, high-saturation so the zones read strong on OSM
var LANG = 'bg'; try{ LANG = localStorage.getItem('lang') || 'bg'; }catch(e){}
function applyLang(l){
  LANG = l; try{ localStorage.setItem('lang', l); }catch(e){}
  document.documentElement.lang = l;
  document.title = T[l].brand;
  document.querySelectorAll('[data-i18n]').forEach(function(el){ el.textContent = T[l][el.getAttribute('data-i18n')]; });
  document.querySelectorAll('[data-i18n-html]').forEach(function(el){ el.innerHTML = T[l][el.getAttribute('data-i18n-html')]; });
  document.getElementById('q').placeholder = T[l].search;
  document.getElementById('loc').title = T[l].loc;
  document.getElementById('rst').title = T[l].reset;
  var _rb = document.getElementById('rulerbtn'); if (_rb) _rb.title = T[l].ruler;
  var _bm = document.getElementById('bmbtn'); if (_bm) _bm.title = T[l].bmMap;
  var lb = document.getElementById('langbtn');
  lb.querySelector('.l-en').hidden = (l !== 'bg'); // on BG show the EN target; on EN show БГ
  lb.querySelector('.l-bg').hidden = (l !== 'en');
  if (window.wxRefreshOpenPopups) window.wxRefreshOpenPopups(); // retranslate any OPEN popup now
}
document.getElementById('langbtn').onclick = function(){ applyLang(LANG === 'bg' ? 'en' : 'bg'); };
function esc(s){ return (s + '').replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
function ztype(r){ return r === 'PROHIBITED' ? T[LANG].tP : (r === 'REQ_AUTHORISATION' ? T[LANG].tA : T[LANG].tC); }
function popupHTML(p){ var t = T[LANG];
  var h = '<b>' + esc(p.n) + '</b> — ' + ztype(p.r);
  h += '<br>' + t.height + ': ' + esc(p.lim);
  var msg = (LANG === 'en') ? p.me : p.m;
  if (msg) h += '<br>' + esc(msg);
  if (p.rs && p.rs.length) h += '<br><small>' + t.reason + ': ' + p.rs.map(function(c){ return (RSN[c] && RSN[c][LANG]) || c; }).join(', ') + '</small>';
  var det = (LANG === 'en') ? p.oie : p.oi; if (det) h += '<br><small>' + t.details + ': ' + esc(det) + '</small>';
  var cnd = (LANG === 'en') ? p.coe : p.co;
  if (cnd) h += '<br><small>' + t.cond + ': ' + esc(cnd) + '</small>';
  if (p.se) h += '<br><small>' + t.active + ': ' + esc(p.se) + '</small>';
  if (p.au || p.cn || p.em || p.ph){ var cl = (p.pu === 'AUTHORIZATION' ? t.authFrom : (p.pu === 'NOTIFICATION' ? t.notify : (p.pu === 'INFORMATION' ? t.info : t.contact)));
    h += '<br><small>' + cl + ': ' + esc((LANG === 'en' ? (p.aue || p.au) : p.au) || '');
    if (p.cn) h += ' — ' + esc(p.cn);
    if (p.em) h += ' · <a href="mailto:' + esc(p.em) + '">' + esc(p.em) + '</a>';
    if (p.ph) h += ' · <a href="tel:' + esc((p.ph + '').replace(/[^0-9+]/g, '')) + '">' + esc(p.ph) + '</a>';
    h += '</small>'; }
  h += '<br><small>ID ' + esc(p.id) + '</small>';
  return h; }

// --- overlapping-zone chooser ---
var curPopup = null, curList = [], curRender = null;
// signature of a feature list (zones by index, NOTAMs by id) - to tell "same set" apart
function listSig(list){ return list.map(function(p){ return p._nt ? ('n' + p.id) : p._air ? ('a' + p._aid) : ('z' + p.fi); }).sort().join('|'); }
function listHTML(list){ var h = '<div class="zlh">' + list.length + ' ' + T[LANG].zonesHere + '</div>';
  list.forEach(function(p, i){ var dot, inner;
    if (p._nt){ dot = window.wxNotamColor(p.l);
      inner = '<b>' + esc(window.wxNotamName(p)) + '</b> <span class="ptype">NOTAM · ' + esc(window.wxNotamSub(p)) + '</span>'; }
    else if (p._air){ dot = window.wxAirColor(p);
      inner = '<b>' + esc(window.wxAirName(p)) + '</b> <span class="ptype">' + esc(window.wxAirSub(p)) + '</span>'; }
    else { dot = COL[p.r];
      inner = '<b>' + esc(p.n) + '</b> <span class="ptype">' + esc(p.lim) + ' · ' + ztype(p.r) + '</span>'; }
    h += '<div class="zpick" data-i="' + i + '"><span class="pdot" style="background:' + dot + '"></span><span>' + inner + '</span></div>'; });
  return h; }
function detailHTML(p, withBack){ return (withBack ? '<div class="zback">‹ ' + T[LANG].backList + ' (' + curList.length + ')</div>' : '') + (p._nt ? window.wxNotamDetail(p) : p._air ? window.wxAirDetail(p) : popupHTML(p)); }
function wirePopup(){ var el = curPopup && curPopup.getElement && curPopup.getElement(); if (!el || el._zwired) return;
  // ONE delegated handler on the popup root (a STATIC ancestor, survives setHTML) instead of
  // re-wiring onclick on each row / the "back" button after every content swap - the re-wiring
  // was unreliable on touch, so "Назад" read as inactive on the phone (confirmed fixed).
  el._zwired = true;
  el.addEventListener('click', function(ev){
    var t = ev.target, back = t.closest ? t.closest('.zback') : null;
    if (back){ ev.stopPropagation(); curRender = function(){ return listHTML(curList); }; setPopupContent(curRender()); if (window.wxAirSelect) window.wxAirSelect(null); return; }
    var pick = t.closest ? t.closest('.zpick') : null;
    if (pick){ ev.stopPropagation(); var i = +pick.getAttribute('data-i'); curRender = function(){ return detailHTML(curList[i], true); }; setPopupContent(curRender()); if (window.wxAirSelect) window.wxAirSelect(curList[i]._air ? curList[i]._aid : null); }
  });
}
function showPopup(html, lngLat){ if (curPopup) curPopup.remove(); curPopup = new maplibregl.Popup({maxWidth:'340px'}).setLngLat(lngLat).setHTML(html).addTo(map); wirePopup(); curPopup.on('close', function(){ if (window.wxAirSelect) window.wxAirSelect(null); }); }
function setPopupContent(html){ if (curPopup){ curPopup.setHTML(html); wirePopup(); } }
function openZones(list, lngLat){ if (!list.length) return; curList = list;
  curRender = (list.length === 1) ? function(){ return detailHTML(curList[0], false); } : function(){ return listHTML(curList); };
  showPopup(curRender(), lngLat);
  if (window.wxAirSelect) window.wxAirSelect((list.length === 1 && list[0]._air) ? list[0]._aid : null); }
// retranslate an open zone popup on a BG/EN switch
(window.wxLangRefresh = window.wxLangRefresh || []).push(function(){ if (curPopup && curPopup.isOpen && curPopup.isOpen() && curRender) setPopupContent(curRender()); });

var ic = [25.3, 42.75], iz = 7; // original 2D default view (whole of Bulgaria), restored
var hm = location.hash.match(/^#(-?\d+(?:\.\d+)?)\/(-?\d+(?:\.\d+)?)\/(\d+(?:\.\d+)?)/);
if (hm){ ic = [+hm[2], +hm[1]]; iz = +hm[3]; } // one engine now: the hash stores the native MapLibre zoom (no ±1 juggling)
// MapTiler basemaps (Topo/Winter/Landscape) use RASTER tiles (flat images, so no clash
// with our own 3D buildings). The key is PUBLIC but ORIGIN-RESTRICTED in the MapTiler
// dashboard to martinovem.github.io + localhost, so it is safe in this public page.
var MTKEY = '0DfYAoUH19VVOKmkoZUk';
var MT_ATTR = '&copy; <a href="https://www.maptiler.com/copyright/" target="_blank" rel="noopener">MapTiler</a> &copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors';
var map = new maplibregl.Map({
  container: 'map',
  center: ic, zoom: iz,
  pitch: 0, bearing: 0, // default = flat 2D mode; 3D mode restores tilt/terrain on load
  minZoom: 5, // floor; wxFitRegion sets the real limit per screen (see below)
  maxBounds: [[16.5, 34.0], [34.0, 49.5]], // Bulgaria + surrounding region (tall enough that a portrait phone can fit the whole country); can't wander to the rest of the world
  maxPitch: 80, attributionControl: false,
  style: {
    version: 8,
    glyphs: 'https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf', // fonts for airspace name labels (keyless, same host as our buildings)
    sources: {
      sat: {type: 'raster', tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'], tileSize: 256, attribution: 'Imagery &copy; Esri, Vantor, Earthstar Geographics'},
      lbl: {type: 'raster', tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}'], tileSize: 256, attribution: 'Labels &copy; Esri'},
      dem: {type: 'raster-dem', tiles: ['https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png'], tileSize: 256, encoding: 'terrarium', maxzoom: 13, attribution: 'Terrain: USGS, NOAA &middot; Mapzen/AWS'},
      ofm: {type: 'vector', url: 'https://tiles.openfreemap.org/planet', attribution: 'Buildings &copy; OpenMapTiles &copy; OpenStreetMap contributors'},
      osm: {type: 'raster', tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'], tileSize: 256, maxzoom: 19, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors'},
      dg: {type: 'raster', tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}'], tileSize: 256, maxzoom: 16, attribution: 'Dark Gray Canvas &copy; Esri, HERE, Garmin &middot; &copy; OpenStreetMap contributors'},
      mt_topo: {type: 'raster', tiles: ['https://api.maptiler.com/maps/topo-v2/256/{z}/{x}/{y}.png?key=' + MTKEY], tileSize: 256, maxzoom: 22, attribution: MT_ATTR},
      mt_winter: {type: 'raster', tiles: ['https://api.maptiler.com/maps/winter-v2/256/{z}/{x}/{y}.png?key=' + MTKEY], tileSize: 256, maxzoom: 22, attribution: MT_ATTR},
      mt_landscape: {type: 'raster', tiles: ['https://api.maptiler.com/maps/landscape/256/{z}/{x}/{y}.png?key=' + MTKEY], tileSize: 256, maxzoom: 22, attribution: MT_ATTR},
      bgline: {type: 'geojson', data: BGOUT, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors'},
      zones: {type: 'geojson', data: Z}
    },
    layers: [{id: 'osm', type: 'raster', source: 'osm'}, // default basemap: OSM shown (the ⧉ selector swaps these)
      {id: 'sat', type: 'raster', source: 'sat', layout: {visibility: 'none'}},
      {id: 'lbl', type: 'raster', source: 'lbl', layout: {visibility: 'none'}},
      {id: 'dg', type: 'raster', source: 'dg', layout: {visibility: 'none'}},
      {id: 'mt_topo', type: 'raster', source: 'mt_topo', layout: {visibility: 'none'}},
      {id: 'mt_winter', type: 'raster', source: 'mt_winter', layout: {visibility: 'none'}},
      {id: 'mt_landscape', type: 'raster', source: 'mt_landscape', layout: {visibility: 'none'}},
      {id: 'bg-danube', type: 'line', source: 'bgline', filter: ['==', ['get', 'role'], 'danube'],
       layout: {'line-join': 'round', 'line-cap': 'round'},
       paint: {'line-color': '#2f8fd0', 'line-width': ['interpolate', ['linear'], ['zoom'], 5, 2, 9, 3, 13, 4.5], 'line-opacity': 0.95}},
      {id: 'bg-land', type: 'line', source: 'bgline', filter: ['==', ['get', 'role'], 'land'],
       layout: {'line-join': 'round', 'line-cap': 'round'},
       paint: {'line-color': '#1a1a1a', 'line-color-transition': {duration: 0}, 'line-width': ['interpolate', ['linear'], ['zoom'], 5, 2.4, 9, 3.4, 13, 5], 'line-opacity': 0.95}},
      {id: 'buildings', type: 'fill-extrusion', source: 'ofm', 'source-layer': 'building', minzoom: 14,
       layout: {visibility: 'none'},
       paint: {'fill-extrusion-color': ['interpolate', ['linear'], ['get', 'render_height'],
                 0, '#b0a48f', 12, '#c2b8a4', 40, '#d0c8b9', 120, '#ddd6c8'],
               'fill-extrusion-height': ['get', 'render_height'],
               'fill-extrusion-base': ['get', 'render_min_height'], 'fill-extrusion-opacity': 0.95,
               'fill-extrusion-vertical-gradient': true}}]
    // no terrain in the initial (2D) style — 3D mode adds it via setTerrain
  }
});
map.addControl(new maplibregl.AttributionControl({compact: true}), 'bottom-right');
// Start the attribution COLLAPSED (just the ⓘ) instead of open on first load.
// OSM's official attribution guidelines allow a collapsed credit as long as the
// user can still reach it via an "(i)" button — which is exactly this control;
// the Esri/terrain/OSM credits stay one tap away. MapLibre opens it by default
// (adds 'maplibregl-compact-show'); removing that class collapses it, and the
// ⓘ button still toggles it back open.
function wxCollapseAttrib(){ var a = document.querySelector('.maplibregl-ctrl-attrib.maplibregl-compact');
  if (!a) return; if ('open' in a) a.open = false; a.classList.remove('maplibregl-compact-show'); }
map.on('load', wxCollapseAttrib); wxCollapseAttrib();
// a click anywhere outside the open credit collapses it (like the 2D map and the
// popups). Capture phase so it still fires when the clicked control stops
// propagation (e.g. the "!" disclaimer toggle bottom-left, the menu buttons).
document.addEventListener('click', function(e){
  var a = document.querySelector('.maplibregl-ctrl-attrib.maplibregl-compact');
  if (!a) return;
  var shown = ('open' in a ? a.open : false) || a.classList.contains('maplibregl-compact-show');
  if (shown && !a.contains(e.target)) wxCollapseAttrib();
}, true);
map.addControl(new maplibregl.NavigationControl({visualizePitch: true}), 'bottom-right');
// custom scale bar: a fixed-width line (no box) whose NUMBER changes — like a
// normal map scale, unlike MapLibre's own control which stretches the bar. Sits
// by the ⓘ; colour follows the mode (dark on OSM, white on the satellite).
(function(){
  var el = document.getElementById('wxscale'), lbl = el.querySelector('.lbl'), bar = el.querySelector('.bar');
  var MAXW = 88; // max bar width (px); a ROUND 1/2/5·10ⁿ distance that fits is chosen (like every map)
  function hav(a, b){ var R = 6371000, k = Math.PI / 180,
    dLat = (b.lat - a.lat) * k, dLng = (b.lng - a.lng) * k,
    s = Math.sin(dLat/2)*Math.sin(dLat/2) + Math.cos(a.lat*k)*Math.cos(b.lat*k)*Math.sin(dLng/2)*Math.sin(dLng/2);
    return 2 * R * Math.asin(Math.sqrt(s)); }
  function nice(d){ var p = Math.pow(10, Math.floor(Math.log10(d))), f = d / p; return (f >= 5 ? 5 : f >= 2 ? 2 : 1) * p; }
  function fmt(d){ return d >= 1000 ? (d/1000) + ' km' : d + ' m'; } // d is round -> whole numbers
  var attribEl = null;
  function place(){ if (!attribEl) attribEl = document.querySelector('.maplibregl-ctrl-attrib');
    var open = attribEl && (attribEl.open || attribEl.classList.contains('maplibregl-compact-show'));
    // when the credit is open, slide the scale left of it so they never overlap
    el.style.right = open ? (Math.round(attribEl.getBoundingClientRect().width) + 16) + 'px' : '44px'; }
  function upd(){ var c = map.getContainer(), y = c.clientHeight/2, x = c.clientWidth/2;
    var mMax = hav(map.unproject([x, y]), map.unproject([x + MAXW, y])); // metres across MAXW px
    var d = nice(mMax); bar.style.width = Math.round(MAXW * d / mMax) + 'px'; lbl.textContent = fmt(d); place(); }
  map.on('load', function(){ upd(); var a = document.querySelector('.maplibregl-ctrl-attrib');
    if (a) a.addEventListener('toggle', function(){ requestAnimationFrame(place); }); });
  map.on('move', upd);
})();
// keep the GL map crisp on entering/leaving fullscreen (belt-and-braces; MapLibre also tracks resize)
document.addEventListener('fullscreenchange', function(){ setTimeout(function(){ map.resize(); }, 60); });
// The widest zoom-out fits Bulgaria (+ a small margin) on THIS screen, recomputed
// per viewport / rotation, so the WHOLE country is always visible and the map
// locks in both directions at max zoom-out (a wide screen shows more side context,
// a tall phone more top/bottom context). maxBounds keeps it on the region.
function wxFitRegion(){
  var el = map.getContainer(), vw = el.clientWidth, vh = el.clientHeight; if (!vw || !vh) return;
  var yN = function(lat){ var r = lat * Math.PI / 180; return (1 - Math.log(Math.tan(r) + 1/Math.cos(r)) / Math.PI) / 2; };
  var invY = function(y){ return Math.atan(Math.sinh(Math.PI * (1 - 2*y))) * 180 / Math.PI; };
  // min zoom that fits a whole lng/lat box in this viewport (smaller of width- and height-fit)
  function fit(wl, sb, el2, nb){ var lngSpan = (el2 - wl) / 360, latSpan = Math.abs(yN(nb) - yN(sb));
    return Math.min(Math.log2(vw / (512 * lngSpan)), Math.log2(vh / (512 * latSpan))); }
  // The right max zoom-out depends on the SCREEN SHAPE (Bulgaria is wider than tall):
  //  - tall phone  -> fit ~Bulgaria itself, so the WHOLE country shows, not a central strip;
  //  - wide screen -> lock to the country's N-S extent + a small margin (approx 39.5-46 N);
  //    height limits on a wide screen, so the country fills the view and only the neighbours
  //    spill in on the sides (not the whole surrounding region, which zoomed out too far).
  var z = (vh > vw) ? fit(21.6, 40.7, 29.4, 44.7) : fit(22.0, 39.5, 28.9, 46.0);
  if (!isFinite(z)) return;
  map.setMinZoom(z);
  // Lock panning to EXACTLY what is visible at max zoom-out, centered on Bulgaria, so the
  // map is pinned in both directions there (and can pan only within that on the way in).
  var cLng = 25.3, cy = yN(42.75), slack = 1.015; // tiny slack so the edge isn't razor-tight
  var lngHalf = (vw * 360 / (512 * Math.pow(2, z))) / 2 * slack;
  var yHalf = (vh / (512 * Math.pow(2, z))) / 2 * slack;
  map.setMaxBounds([[cLng - lngHalf, invY(cy + yHalf)], [cLng + lngHalf, invY(cy - yHalf)]]);
}
map.on('load', wxFitRegion);
window.addEventListener('resize', function(){ clearTimeout(window._wxfit); window._wxfit = setTimeout(wxFitRegion, 150); });
// ---- in-page 2D (flat OSM) / 3D (satellite + terrain + tilt) mode toggle ----
// The single MapLibre page shows a flat OSM "2D mode" and a satellite "3D mode".
// This template now generates BOTH index.html (the main page, 2D by default) and
// 3d.html (kept for old links); the old Leaflet index.html is being retired.
var wxMode = ''; // applied on load from the saved 'mode' (default 2D)
var wxLoaded = false; // set once the FIRST style load fires; gate switches on THIS,
map.on('load', function(){ wxLoaded = true; }); // not isStyleLoaded (which flaps false while tiles stream -> a switch could wait for 'idle' that never comes on a slow link)
window.wxSetMode = function(m){
  if (m === wxMode) return;
  if (!wxLoaded){ map.once('load', function(){ window.wxSetMode(m); }); return; } // defer ONLY until the first load, never on later tile streaming
  wxMode = m; var d2 = (m === '2d');
  try{ ST.set('mode', m); }catch(e){} // remember the mode so a refresh restores it
  // Instant feedback FIRST (button + tilt cap are cheap), so the click paints right
  // away and feels responsive even while 3D tiles are still streaming on a slow link.
  var s2 = document.getElementById('to2d'), s3 = document.getElementById('to3d');
  s2.classList.toggle('on', d2); s3.classList.toggle('on', !d2);
  map.setMaxPitch(d2 ? 0 : 80);
  if (d2 && map.getPitch() > 0) map.easeTo({pitch: 0, bearing: 0, duration: 300});
  // The heavy part (terrain DEM + our 3D buildings) OFF the click's critical path.
  // Going to 2D removes terrain -> that also STOPS the 3D tile loading. The stale-check
  // makes rapid taps apply only the last mode. The basemap (which tiles show) is owned
  // by the selector (wxApplyBasemap), NOT the mode - so it stays across 2D<->3D.
  var apply = function(){
    if (wxMode !== m) return;
    var bOn = !document.getElementById('cbB').classList.contains('off');
    map.setLayoutProperty('buildings', 'visibility', (!d2 && bOn) ? 'visible' : 'none');
    map.setTerrain(d2 ? null : {source: 'dem', exaggeration: 1.15});
  };
  (window.requestAnimationFrame || function(f){ setTimeout(f, 0); })(apply);
};
document.getElementById('to2d').onclick = function(e){ e.preventDefault(); window.wxSetMode('2d'); };
document.getElementById('to3d').onclick = function(e){ e.preventDefault(); window.wxSetMode('3d'); };
// ---- base-map selector (⧉ in the top-right cluster) ----------------------------
// ONE basemap choice, applied to BOTH 2D and 3D (the mode only adds terrain/tilt/
// buildings). All basemaps are RASTER (flat images) so none clash with our own 3D
// buildings. The choice persists in ST ('basemap'); ⟳ reset -> OSM.
var BM = {
  osm:       {layers: ['osm'],          dark: false, name: 'OSM',       border: '#1a1a1a'}, // черна
  sat:       {layers: ['sat', 'lbl'],   dark: true,  i18n: 'bmSat',     border: '#ee2b2b'}, // червена
  dark:      {layers: ['dg'],           dark: true,  i18n: 'bmDark',    border: '#ee2b2b'}, // червена
  topo:      {layers: ['mt_topo'],      dark: false, name: 'Topo',      border: '#2f6b3c'}, // тъмнозелена (мат)
  winter:    {layers: ['mt_winter'],    dark: false, name: 'Winter',    border: '#2b6cb0'}, // синя (accent)
  landscape: {layers: ['mt_landscape'], dark: false, name: 'Landscape', border: '#666a70'}  // сива
};
var BM_ORDER = ['osm', 'sat', 'dark', 'topo', 'winter', 'landscape'];
var BM_ALL = ['osm', 'sat', 'lbl', 'dg', 'mt_topo', 'mt_winter', 'mt_landscape'];
var wxBasemap = '';
window.wxApplyBasemap = function(id){
  if (!BM[id]) id = 'osm';
  wxBasemap = id; try{ ST.set('basemap', id); }catch(e){}
  window.wxDark = !!BM[id].dark; // basemap brightness -> wind palette contrast (read live by windDark)
  document.documentElement.classList.toggle('wx2d', !BM[id].dark); // .wx2d = LIGHT basemap: dark crosshair/scale/ruler
  var p = document.getElementById('bmpanel');
  if (p) Array.prototype.forEach.call(p.querySelectorAll('.bmopt'), function(b){ b.classList.toggle('on', b.getAttribute('data-bm') === id); });
  // the layer ops need the style loaded; if it is mid-load (e.g. just after a 3D terrain
  // swap) defer to the next idle and re-apply, like wxSetMode does
  if (!map.isStyleLoaded()){ map.once('idle', function(){ window.wxApplyBasemap(id); }); map.triggerRepaint(); return; }
  BM_ALL.forEach(function(l){ if (map.getLayer(l)) map.setLayoutProperty(l, 'visibility', 'none'); });
  BM[id].layers.forEach(function(l){ if (map.getLayer(l)) map.setLayoutProperty(l, 'visibility', 'visible'); });
  if (map.getLayer('bg-land') && BM[id].border){
    map.setPaintProperty('bg-land', 'line-color', BM[id].border); // border colour per basemap (Danube stays blue)
    map.triggerRepaint(); // force an immediate repaint so the new colour shows without needing a zoom
  }
};
(function(){
  var btn = document.getElementById('bmbtn'), panel = document.getElementById('bmpanel');
  if (!btn || !panel) return;
  window.wxBuildBasemapMenu = function(){
    var t = T[LANG];
    var html = '<div class="bmph">' + (t.bmHead || 'Основа') + '</div>';
    BM_ORDER.forEach(function(id){
      var nm = BM[id].name || t[BM[id].i18n] || id;
      html += '<button class="bmopt" data-bm="' + id + '"><span class="bmdot"></span><span>' + nm + '</span></button>';
    });
    panel.innerHTML = html;
    Array.prototype.forEach.call(panel.querySelectorAll('.bmopt'), function(b){
      b.onclick = function(e){ e.stopPropagation(); window.wxApplyBasemap(b.getAttribute('data-bm')); closeBm(); };
    });
    if (wxBasemap) window.wxApplyBasemap(wxBasemap); // keep the active highlight after a rebuild
  };
  window.closeBmPanel = function(){ panel.hidden = true; btn.classList.remove('on'); };
  function closeBm(){ window.closeBmPanel(); }
  function openBm(){ panel.hidden = false; btn.classList.add('on');
    if (window.closePanel) window.closePanel();
    if (window.closeWxPanel) window.closeWxPanel();
    if (window.collapseLoupe) window.collapseLoupe(); }
  btn.onclick = function(e){ e.stopPropagation(); if (panel.hidden) openBm(); else closeBm(); };
  document.addEventListener('click', function(e){
    if (!panel.hidden && !panel.contains(e.target) && !btn.contains(e.target)) closeBm(); });
  window.wxBuildBasemapMenu();
  (window.wxLangRefresh = window.wxLangRefresh || []).push(window.wxBuildBasemapMenu); // rebuild names on BG/EN switch
})();
// on load apply the saved basemap + mode (default OSM/2D so a refresh restores the last
// choice, and ⟳ reset — which clears the store — returns to OSM/2D); restore the 3D camera
map.on('load', function(){ window.wxApplyBasemap(ST.get('basemap', 'osm'));
  var sm = ST.get('mode', '2d'); window.wxSetMode(sm);
  if (sm === '3d') map.jumpTo({pitch: ST.get('pitch', 0), bearing: ST.get('bearing', 0)}); });
map.on('moveend', function(){ var c = map.getCenter();
  history.replaceState(null, '', '#' + c.lat.toFixed(5) + '/' + c.lng.toFixed(5) + '/' + map.getZoom().toFixed(2)); });
// remember the camera angle so 3D reopens (incl. after a trip to 2D) as it was left
function stCam(){ if (wxMode === '3d'){ ST.set('pitch', Math.round(map.getPitch())); ST.set('bearing', Math.round(map.getBearing())); } } // don't let flat 2D overwrite the saved 3D camera
map.on('moveend', stCam); map.on('pitchend', stCam); map.on('rotateend', stCam);
// Legend counts — recomputed when zones.json lands (see wxLoadZones below).
function wxZoneCounts(){ var n = {P:0,A:0,C:0};
  Z.features.forEach(function(f){ var r = f.properties.r; n[r === 'PROHIBITED' ? 'P' : (r === 'REQ_AUTHORISATION' ? 'A' : 'C')]++; });
  var eP = document.getElementById('nP'), eA = document.getElementById('nA'), eC = document.getElementById('nC');
  if (eP) eP.textContent = n.P; if (eA) eA.textContent = n.A; if (eC) eC.textContent = n.C; }
// The ~1.4 MB zone GeoJSON is fetched from a SEPARATE zones.json (not inlined) so this
// page stays small and paints fast on mobile; the map + UI appear first and the zones
// fill in a moment later via setData. If the fetch fails the map/weather/UI still work
// (the disclaimer already tells pilots to check the official source + B-FLIP).
function wxLoadZones(){
  fetch('zones.json').then(function(r){ if (!r.ok) throw 0; return r.json(); }).then(function(gj){
    Z = gj;
    // Fill the map as soon as the 'zones' source exists (it is in the initial style).
    // Gate on the source itself, NOT map.isStyleLoaded()/'load': isStyleLoaded flaps to
    // false while tiles stream, and 'load' fires only once, so a late fetch could miss it
    // and the zones would never appear. 'styledata' fires repeatedly during style load.
    (function apply(){ var s = map.getSource('zones');
      if (!s){ map.once('styledata', apply); return; }
      s.setData(Z); wxZoneCounts(); })();
  }).catch(function(){ setTimeout(wxLoadZones, 20000); }); // core content: keep retrying (own-origin file) so a transient blip doesn't leave the map zone-less until F5
}
wxLoadZones();
applyLang(LANG);

// --- place search (Photon / OpenStreetMap, free autocomplete) + locate ---
var QI = document.getElementById('q'), SUG = document.getElementById('sug'), stmr = null, sres = [], sidx = -1;
function sctx(p){ var a = []; if (p.city && p.city !== p.name) a.push(p.city); if (p.state) a.push(p.state); if (p.country) a.push(p.country); return a.join(', '); }
function hideSug(){ SUG.hidden = true; SUG.innerHTML = ''; sres = []; sidx = -1; }
function renderSug(){ if (!sres.length){ hideSug(); return; } sidx = -1;
  SUG.innerHTML = sres.map(function(f, i){ var p = f.properties; return '<li data-i="' + i + '"><span class="nm">' + esc(p.name || '') + '</span> <span class="ctx">' + esc(sctx(p)) + '</span></li>'; }).join('');
  SUG.hidden = false;
  Array.prototype.forEach.call(SUG.children, function(li){ li.onclick = function(){ pick(+li.getAttribute('data-i')); }; }); }
function doSearch(v){ var lg = (LANG === 'en' ? '&lang=en' : '');
  fetch('https://photon.komoot.io/api/?q=' + encodeURIComponent(v) + '&limit=6' + lg + '&bbox=22.3,41.2,28.7,44.2')
    .then(function(r){ return r.json(); }).then(function(d){ sres = (d && d.features) || []; renderSug(); }).catch(function(){ hideSug(); }); }
QI.addEventListener('input', function(){ clearTimeout(stmr); var v = QI.value.trim(); if (v.length < 2){ hideSug(); return; } stmr = setTimeout(function(){ doSearch(v); }, 250); });
QI.addEventListener('keydown', function(e){ if (SUG.hidden) return;
  if (e.key === 'ArrowDown'){ sidx = Math.min(sidx + 1, sres.length - 1); shi(); e.preventDefault(); }
  else if (e.key === 'ArrowUp'){ sidx = Math.max(sidx - 1, 0); shi(); e.preventDefault(); }
  else if (e.key === 'Enter'){ pick(sidx >= 0 ? sidx : 0); e.preventDefault(); }
  else if (e.key === 'Escape'){ hideSug(); } });
function shi(){ Array.prototype.forEach.call(SUG.children, function(li, i){ li.classList.toggle('active', i === sidx); }); }
function pick(i){ var f = sres[i]; if (!f) return; var c = f.geometry.coordinates; QI.value = f.properties.name || QI.value; hideSug(); if (window.collapseLoupe) window.collapseLoupe(); goTo(c[0], c[1], f.properties.name); }
document.addEventListener('click', function(e){ if (!document.getElementById('loupe').contains(e.target)) hideSug(); });
var sMark = null;
function goTo(lon, lat, name){ map.flyTo({center:[lon, lat], zoom:14}); if (sMark) sMark.remove();
  sMark = new maplibregl.Marker({color:'#2b6cb0'}).setLngLat([lon, lat]).addTo(map);
  if (name){ sMark.setPopup(new maplibregl.Popup({offset:25}).setText(name)); sMark.togglePopup(); } }
document.getElementById('loc').onclick = function(){ if (!navigator.geolocation) return;
  navigator.geolocation.getCurrentPosition(function(p){ var lo = p.coords.longitude, la = p.coords.latitude;
    map.flyTo({center:[lo, la], zoom:14}); if (sMark) sMark.remove();
    var dEl = document.createElement('div'); // "you are here" = our drone emblem, not a plain dot
    dEl.style.cssText = 'width:34px;height:34px;filter:drop-shadow(0 1px 2px rgba(0,0,0,.6))';
    dEl.innerHTML = '<svg width="34" height="34" viewBox="0 0 48 48"><g fill="none" stroke="#2b6cb0" stroke-width="3.5" stroke-linecap="round"><path d="M14 14 34 34M34 14 14 34"/><circle cx="12" cy="12" r="7.5"/><circle cx="36" cy="12" r="7.5"/><circle cx="12" cy="36" r="7.5"/><circle cx="36" cy="36" r="7.5"/></g><rect x="18" y="18" width="12" height="12" rx="3" fill="#2b6cb0"/></svg>';
    sMark = new maplibregl.Marker({element: dEl}).setLngLat([lo, la]).addTo(map);
    sMark.setPopup(new maplibregl.Popup({offset:22}).setText(T[LANG].here)); sMark.togglePopup(); },
    function(){ // denied, or blocked because the page is plain http (geolocation needs https/localhost)
      new maplibregl.Popup().setLngLat(map.getCenter())
        .setText(LANG === 'en' ? 'Location unavailable — allow location access (needs https).'
                               : 'Локацията не е достъпна — разрешете достъп (нужен е https).').addTo(map); }); };
document.getElementById('rst').onclick = function(){
  // Reset = back to the site's default state: flat 2D mode, country-wide view, all
  // filters on, no weather/aircraft layers, Bulgarian. Clear the saved language +
  // settings and reload THIS (single MapLibre) page with no hash -> defaults to 2D.
  // (Reload THIS page rather than navigating away; index.html and 3d.html are now
  // the same merged page, so a plain reload returns to the 2D country-wide default.)
  try{ localStorage.removeItem('lang'); }catch(e){}
  ST.clear();
  var base = location.href.replace(/#.*$/, '');
  if (location.href === base) location.reload(); else location.href = base;
};

map.on('load', function(){
  // higher fill opacity + a crisp outline so zones read on BOTH the light OSM map
  // and the darker satellite (the old faint fills .35/.28/.22 washed out over both).
  var ZOP = {PROHIBITED: 0.55, REQ_AUTHORISATION: 0.55, CONDITIONAL: 0.5};
  // Draw order = severity: CONDITIONAL bottom -> REQ_AUTHORISATION -> PROHIBITED on TOP,
  // so a red (prohibited) zone stays vivid where it overlaps an orange one instead of
  // being dimmed under it. ("below the zones" anchors scan for the LOWEST f- layer.)
  ['CONDITIONAL','REQ_AUTHORISATION','PROHIBITED'].forEach(function(r){
    // Draped flat fill at all zooms: it follows the terrain surface cleanly. Extruded
    // volumes are avoided because MapLibre gives a whole polygon a single base elevation,
    // so peaks/ground pierce large zone boxes on uneven terrain ("moth-eaten" look).
    map.addLayer({id: 'f-' + r, type: 'fill', source: 'zones',
      filter: ['==', ['get','r'], r],
      paint: {'fill-color': COL[r], 'fill-opacity': ZOP[r]}});
    map.on('mouseenter', 'f-' + r, function(){ map.getCanvas().style.cursor = 'pointer'; });
    map.on('mouseleave', 'f-' + r, function(){ map.getCanvas().style.cursor = ''; });
  });
  // crisp category-coloured outlines, added AFTER all fills so the borders stay on top
  ['PROHIBITED','REQ_AUTHORISATION','CONDITIONAL'].forEach(function(r){
    map.addLayer({id: 'o-' + r, type: 'line', source: 'zones',
      filter: ['==', ['get','r'], r],
      paint: {'line-color': COL[r], 'line-width': 2.0, 'line-opacity': 1.0}});
  });
  map.on('click', function(e){
    if (window.wxRulerOn) return; // measure tool active: a click places a pin, not a zone popup
    var tol = 4, pt = e.point, box = [[pt.x - tol, pt.y - tol], [pt.x + tol, pt.y + tol]];
    var layers = ['f-PROHIBITED','f-REQ_AUTHORISATION','f-CONDITIONAL'].filter(function(id){ return map.getLayer(id); });
    var fs = layers.length ? map.queryRenderedFeatures(box, {layers: layers}) : [];
    var seen = {}, list = [];
    fs.forEach(function(f){ var fi = f.properties.fi; if (!seen[fi]){ seen[fi] = 1; list.push(Z.features[fi].properties); } });
    // NOTAMs (when the layer is on) join the SAME chooser list, so a pin over a zone isn't hidden
    var nl = ['notam-fill','notam-hatch','notam-pin'].filter(function(id){ return map.getLayer(id); });
    if (nl.length){ var ns = {};
      map.queryRenderedFeatures(box, {layers: nl}).forEach(function(f){ var id = f.properties.id;
        if (!ns[id]){ ns[id] = 1; var p = {}; for (var k in f.properties) p[k] = f.properties[k]; p._nt = true; list.push(p); } }); }
    // airspace joins LAST (order: drone-zones > NOTAM > airspace); reachable ONLY via its NAME label (owner's choice)
    var al = ['air-ctrl-labels','air-spec-labels'].filter(function(id){ return map.getLayer(id); });
    if (al.length){ var as = {};
      map.queryRenderedFeatures(box, {layers: al}).forEach(function(f){ var aid = f.id;
        if (aid != null && !as[aid]){ as[aid] = 1; var p = {}; for (var k in f.properties) p[k] = f.properties[k]; p._air = true; p._aid = aid; list.push(p); } }); }
    if (!list.length) return;
    // tapping the SAME feature(s) the open popup already shows dismisses it (so a tap on the
    // same big zone just above the popup clears it instead of reopening a popup)
    if (curPopup && curList.length && listSig(list) === listSig(curList)){ curPopup.remove(); curPopup = null; return; }
    openZones(list, e.lngLat);
  });
  function zvis(r, on){ var v = on ? 'visible' : 'none';
    map.setLayoutProperty('f-' + r, 'visibility', v);
    if (map.getLayer('o-' + r)) map.setLayoutProperty('o-' + r, 'visibility', v); }
  function chip(id, r, k){ var el = document.getElementById(id);
    if (!ST.get(k, true)){ el.classList.remove('on'); zvis(r, false); }
    el.onclick = function(){
    var on = el.classList.toggle('on'); ST.set(k, on);
    zvis(r, on); }; }
  chip('cbP','PROHIBITED','fP'); chip('cbA','REQ_AUTHORISATION','fA'); chip('cbC','CONDITIONAL','fC');
  var eb = document.getElementById('cbB');
  if (!ST.get('bld', true)) eb.classList.remove('on'); // visibility is gated by the mode (2D hides buildings)
  eb.onclick = function(){ var on = eb.classList.toggle('on'); ST.set('bld', on);
    map.setLayoutProperty('buildings', 'visibility', (wxMode === '3d' && on) ? 'visible' : 'none'); };
});
// ---- measure tool ("линийка") -------------------------------------------------
// Cyan draggable pins; a pin dropped inside a zone turns RED (still valid). Left
// click adds a pin, left-drag moves it; right-click (desktop) / long-press (touch)
// removes one pin (on a pin) or all (on empty map). Numbers between pins show each
// segment's length; from the 2nd segment the last one also shows the total
// ("seg / total"). One billboarded pin for 2D & 3D (upright when the map is tilted).
// iOS Safari fires no `contextmenu` on long-press (verified), so long-press is manual.
(function(){
  var btn = document.getElementById('rulerbtn'); if (!btn) return;
  var CYAN = '#06b6d4', RED = '#e23b3b';
  var ZL = ['f-PROHIBITED','f-REQ_AUTHORISATION','f-CONDITIONAL'];
  var pins = [], labels = [], on = false, suppressClick = false;
  // tell a right CLICK (delete) apart from a right DRAG (rotate/tilt): remember where
  // the right button went down; if the pointer moved, the contextmenu was a rotate.
  var rDownX = 0, rDownY = 0;
  document.addEventListener('mousedown', function(e){ if (e.button === 2){ rDownX = e.clientX; rDownY = e.clientY; } }, true);
  function rDrag(e){ return Math.abs((e.clientX || 0) - rDownX) > 6 || Math.abs((e.clientY || 0) - rDownY) > 6; }
  function onPin(e){ return !!(e.target && e.target.closest && e.target.closest('.rpin')); }
  function hav(a, b){ var R = 6371000, k = Math.PI / 180,
    dLat = (b[1]-a[1])*k, dLng = (b[0]-a[0])*k,
    s = Math.sin(dLat/2)*Math.sin(dLat/2) + Math.cos(a[1]*k)*Math.cos(b[1]*k)*Math.sin(dLng/2)*Math.sin(dLng/2);
    return 2 * R * Math.asin(Math.sqrt(s)); }
  function fmt(m){ return m >= 1000 ? (Math.round(m/100)/10) + ' км' : Math.round(m) + ' м'; }
  function pinEl(){ var d = document.createElement('div'); d.className = 'rpin';
    d.innerHTML = '<svg width="26" height="34" viewBox="0 0 26 34"><path d="M13 1C6.4 1 1 6.4 1 13c0 8.7 12 20 12 20s12-11.3 12-20C25 6.4 19.6 1 13 1Z" fill="' + CYAN + '" stroke="#08323b" stroke-width="1.6"/><circle cx="13" cy="13" r="4" fill="#fff"/></svg>';
    return d; }
  function paint(p){ var pa = p.el.querySelector('path'); if (pa) pa.setAttribute('fill', p.inZone ? RED : CYAN); }
  function zoneCheck(p){
    var av = ZL.filter(function(id){ return map.getLayer(id); });
    if (!av.length){ p.inZone = false; paint(p); return; }
    var pt = map.project(p.marker.getLngLat());
    var f = map.queryRenderedFeatures([[pt.x-2, pt.y-2], [pt.x+2, pt.y+2]], {layers: av});
    p.inZone = f.length > 0; paint(p); }
  function coords(){ return pins.map(function(p){ var l = p.marker.getLngLat(); return [l.lng, l.lat]; }); }
  function ensureLine(){ if (map.getSource('ruler-line')) return;
    map.addSource('ruler-line', {type:'geojson', data:{type:'Feature',geometry:{type:'LineString',coordinates:[]}}});
    map.addLayer({id:'ruler-line', type:'line', source:'ruler-line',
      layout:{'line-cap':'round','line-join':'round'},
      paint:{'line-color':CYAN, 'line-width':2.5, 'line-dasharray':[2,1.6]}}); }
  function lblEl(){ var d = document.createElement('div'); d.className = 'rlbl'; return d; }
  function sync(){
    ensureLine();
    var c = coords();
    map.getSource('ruler-line').setData({type:'Feature',geometry:{type:'LineString',coordinates:c}});
    var nseg = Math.max(0, c.length - 1), seg = [], total = 0, i;
    for (i = 1; i < c.length; i++){ var d = hav(c[i-1], c[i]); seg.push(d); total += d; }
    while (labels.length < nseg){ labels.push(new maplibregl.Marker({element:lblEl(), anchor:'bottom', offset:[0,-4]}).setLngLat([0,0]).addTo(map)); }
    while (labels.length > nseg){ labels.pop().remove(); }
    for (i = 0; i < nseg; i++){
      var mid = [(c[i][0]+c[i+1][0])/2, (c[i][1]+c[i+1][1])/2];
      var html = fmt(seg[i]);
      if (i === nseg-1 && nseg >= 2) html = fmt(seg[i]) + ' / <b>' + fmt(total) + '</b>'; // total only from the 2nd segment; a single segment shows just itself
      labels[i].setLngLat(mid); labels[i].getElement().innerHTML = html;
    }
  }
  function addPin(lngLat){
    var el = pinEl();
    var m = new maplibregl.Marker({element:el, draggable:true, anchor:'bottom'}).setLngLat(lngLat).addTo(map);
    var p = {marker:m, el:el, inZone:false};
    m.on('drag', function(){ zoneCheck(p); sync(); });
    m.on('dragend', function(){ zoneCheck(p); sync(); });
    el.addEventListener('contextmenu', function(e){ if (!on) return; e.preventDefault(); if (rDrag(e)) return; e.stopPropagation(); delPin(p); });
    longPress(el, function(){ if (on) delPin(p); });
    pins.push(p); zoneCheck(p); sync();
  }
  function delPin(p){ p.marker.remove(); var i = pins.indexOf(p); if (i >= 0) pins.splice(i, 1); sync(); }
  function delAll(){ pins.forEach(function(p){ p.marker.remove(); }); pins = []; sync(); }
  // manual long-press for touch (iOS Safari has no contextmenu event)
  function longPress(el, cb){ var t = null, sx = 0, sy = 0;
    el.addEventListener('touchstart', function(e){ var c = e.touches[0]; sx = c.clientX; sy = c.clientY;
      t = setTimeout(function(){ t = null; cb(); }, 500); }, {passive:true});
    el.addEventListener('touchmove', function(e){ var c = e.touches[0];
      if (t && (Math.abs(c.clientX-sx) > 10 || Math.abs(c.clientY-sy) > 10)){ clearTimeout(t); t = null; } }, {passive:true});
    el.addEventListener('touchend', function(){ if (t){ clearTimeout(t); t = null; } }); }
  function setActive(a){
    if (a === on) return;
    on = a; window.wxRulerOn = a; btn.classList.toggle('on', a);
    document.documentElement.classList.toggle('ruler-on', a); // CSS gives the map a crosshair cursor
    // variant B: turning the tool OFF keeps the measurement on the map (frozen); the
    // pins just stop being draggable. Re-enter to edit; clear via right-click/long-press.
    // Rotation stays available while measuring: right-DRAG rotates/tilts (3D), a right
    // CLICK without moving deletes (see rDrag below) — so both work at once.
    pins.forEach(function(p){ p.marker.setDraggable(a); });
  }
  btn.onclick = function(e){ e.stopPropagation(); setActive(!on); };
  document.addEventListener('keydown', function(e){ if (e.key === 'Escape' && on) setActive(false); });
  // left click on empty map adds a pin (a click on a pin never reaches the map)
  map.on('click', function(e){ if (!on) return;
    if (suppressClick){ suppressClick = false; return; } addPin(e.lngLat); });
  // right-click / long-press on EMPTY map clears all
  var cc = map.getCanvasContainer();
  // right CLICK on empty map -> clear all; but not a right DRAG (that rotates) and not
  // on a pin (the pin's own handler removes just that one).
  cc.addEventListener('contextmenu', function(e){ if (!on) return; e.preventDefault(); if (onPin(e) || rDrag(e)) return; delAll(); });
  (function(){ var t = null, sx = 0, sy = 0;
    cc.addEventListener('touchstart', function(e){ if (!on || e.touches.length !== 1) return; if (onPin(e)) return; var c = e.touches[0]; sx = c.clientX; sy = c.clientY;
      t = setTimeout(function(){ t = null; delAll(); suppressClick = true; setTimeout(function(){ suppressClick = false; }, 600); }, 500); }, {passive:true});
    cc.addEventListener('touchmove', function(e){ if (t){ var c = e.touches[0]; if (Math.abs(c.clientX-sx) > 10 || Math.abs(c.clientY-sy) > 10){ clearTimeout(t); t = null; } } }, {passive:true});
    cc.addEventListener('touchend', function(){ if (t){ clearTimeout(t); t = null; } });
  })();
})();
//__SHELL_JS__
//__WX_JS__
//__WX_LAYERS_JS__
</script>
<!-- Cloudflare Web Analytics --><script type='module' src='https://static.cloudflareinsights.com/beacon.min.js' data-cf-beacon='{"token": "f8ed2b78300348ea854f1b425ee36c57", "spa": false}'></script><!-- End Cloudflare Web Analytics -->
</body></html>
"""
html = (html.replace("__BGOUTLINE__", bgout).replace("__FAVICON__", favicon).replace("__DATESPAN__", datespan).replace("__CHANGED__", changed)
        .replace("//__ST_JS__", ST_JS)
        .replace("/*__SHELL_CSS__*/", SHELL_CSS).replace("//__SHELL_JS__", SHELL_JS)
        .replace("<!--__MENUBTN__-->", MENUBTN_HTML)
        .replace("<!--__PANEL__-->", panel_html(ZONE_CHIPS, AIRSPACE_SECTION + NOTAM_SECTION, BUILDINGS_CHIP,
                 foot='<div class="psec"><div class="pln-hint" data-i18n="hint">десен бутон = въртене/наклон</div></div>'))
        .replace("<!--__LOUPE__-->", LOUPE_HTML).replace("<!--__PLNBTN__-->", PLNBTN_HTML)
        .replace("<!--__OGNBTN__-->", OGNBTN_HTML).replace("<!--__GJBTN__-->", GJBTN_HTML)
        .replace("<!--__CTRHAIR__-->", CTRHAIR_HTML)
        .replace("<!--__FSBTN__-->", FSBTN_HTML)
        .replace("<!--__LANG__-->", LANG_HTML)
        .replace("/*__WX_CSS__*/", WX_CSS).replace("<!--__WX_HTML__-->", WX_HTML)
        .replace("//__WX_JS__", WX_JS).replace("//__WX_LAYERS_JS__", WX_LAYERS_JS_3D))
os.makedirs(outdir, exist_ok=True)
# The whole app is ONE page, written as index.html (2D and 3D both live here; opens
# in flat 2D mode by default). The old Leaflet index.html and the separate 3d.html
# page are retired — there is no 3d.html any more.
open(os.path.join(outdir, "index.html"), "w", encoding="utf-8").write(html)
# Zone GeoJSON in its OWN file (fetched by the page) so index.html stays small -> faster
# first paint on mobile (LCP). Same minified FeatureCollection that used to be inlined.
open(os.path.join(outdir, "zones.json"), "w", encoding="utf-8").write(gj)
print("index.html:", os.path.getsize(os.path.join(outdir, "index.html")) // 1024, "KB,",
      "zones.json:", os.path.getsize(os.path.join(outdir, "zones.json")) // 1024, "KB,", len(feats), "zones")
