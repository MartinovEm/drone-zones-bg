"""Shared weather widget (Open-Meteo forecast) injected into both map pages.

The widget is a small chip in the top-left corner (under the search box) showing
current conditions for the MAP CENTER; tapping it expands a card with a 7-day
hourly forecast: temperature, dew point, cloud cover (all + low), visibility, wind
at 10/80/120 m, gusts, direction arrows, precipitation, snow, CAPE and the
freezing level. Hours with strong wind/gusts (and CAPE bands) are highlighted so
no-fly hours are obvious; hours in the night of the EU drone rules (after
evening civil twilight) are marked, computed in the browser. Data: Open-Meteo (keyless, CORS-open, verified);
place name: Photon reverse geocoding (same keyless service the search uses).

make_3d.py inserts the three strings below at marker comments in
their templates. The JS only relies on `map.getCenter()` + `map.on('moveend')`,
which Leaflet and MapLibre share, and on the pages' globals `LANG` and `ST`
(the shared settings store, settings_store.py).
"""

WX_CSS = r"""
#wx{font:13px/1.3 system-ui,'Segoe UI',Roboto,sans-serif;color:var(--fg)}
#wxchip{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--border);border-radius:999px;
 padding:0 12px;height:38px;box-sizing:border-box;background:var(--glass-bg);-webkit-backdrop-filter:blur(8px);backdrop-filter:blur(8px);
 box-shadow:var(--shadow);cursor:pointer;font:inherit;font-size:13px;color:inherit;white-space:nowrap;
 max-width:calc(100vw - 20px);overflow:hidden;text-overflow:ellipsis}
#wxchip .wxnm{font-weight:700;overflow:hidden;text-overflow:ellipsis;max-width:34vw}
.wxlayers{display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-bottom:8px}
.wxlbtn{border:1px solid rgba(0,0,0,.12);border-radius:999px;padding:0 9px;height:29px;box-sizing:border-box;
 display:inline-flex;align-items:center;background:rgba(255,255,255,.95);
 -webkit-backdrop-filter:blur(8px);backdrop-filter:blur(8px);box-shadow:0 2px 10px rgba(0,0,0,.18);cursor:pointer;
 font:inherit;font-size:13px;color:inherit;flex:none}
.wxlbtn.on{background:#2b6cb0;color:#fff;border-color:#2b6cb0}
#wxframe{font-size:11px;background:rgba(255,255,255,.9);border-radius:8px;padding:3px 7px;color:#333;
 box-shadow:0 1px 6px rgba(0,0,0,.18);font-variant-numeric:tabular-nums;flex:none}
#wxlegend,#wxsnowlegend{display:flex;gap:8px;flex-wrap:wrap;margin-top:6px;background:rgba(255,255,255,.92);border-radius:10px;
 padding:5px 9px;box-shadow:0 1px 6px rgba(0,0,0,.18);font-size:11px;color:#333;width:fit-content;max-width:calc(100vw - 20px)}
#wxlegend[hidden],#wxsnowlegend[hidden]{display:none}
#wxfcbar{display:flex;flex-wrap:wrap;align-items:center;gap:3px 8px;margin-top:6px;background:rgba(255,255,255,.92);border-radius:10px;
 padding:6px 9px;box-shadow:0 1px 6px rgba(0,0,0,.18);font-size:11px;color:#333;width:auto}
#wxfcbar[hidden]{display:none}
#wxfcsl{width:100%;accent-color:#2b6cb0;margin:0}
#wxfclbl{font-variant-numeric:tabular-nums;white-space:nowrap;font-weight:600}
#wxfcnote{width:0;min-width:100%;color:#888;font-size:10px}
#wxrvnote{width:0;min-width:100%;color:#888;font-size:10px}
#wxrvnote[hidden]{display:none}
/* lightning (☁ at "now") / model thunderstorms (☁ ahead) note under the slider */
#wxltg{display:block;margin-top:6px;background:rgba(255,255,255,.92);border-radius:10px;padding:5px 9px;
 box-shadow:0 1px 6px rgba(0,0,0,.18);font-size:11px;color:#333;line-height:1.4;width:fit-content;max-width:calc(100vw - 20px)}
#wxltg[hidden]{display:none}
#wxltg .wxltgbad{color:#c62828;font-weight:600}
.wxpale{opacity:.45} /* the pale ⚡ in the thunderstorm key = the one-model bolts on the map */
:root[data-theme="dark"] #wxltg{background:var(--glass-strong);color:var(--fg)}
#wxwindh{display:flex;align-items:center;gap:8px;margin-top:6px;font-size:11px;color:#333}
#wxwindh[hidden]{display:none}
.wxhlbl{color:#555}
.wxhseg{display:inline-flex;border:1px solid rgba(0,0,0,.15);border-radius:999px;overflow:hidden}
.wxhseg button{border:0;background:#fff;cursor:pointer;font:inherit;font-size:11px;padding:3px 10px;color:#333}
.wxhseg button.on{background:#2b6cb0;color:#fff}
.wxlg{display:inline-flex;align-items:center;gap:4px}
.wxlg i{width:11px;height:11px;border-radius:3px;display:inline-block;border:1px solid rgba(0,0,0,.15)}
#wxchip:hover{background:var(--glass-strong)}
#wxpanel{margin-top:6px;width:min(460px,calc(100vw - 20px));background:rgba(255,255,255,.97);
 -webkit-backdrop-filter:blur(8px);backdrop-filter:blur(8px);border-radius:12px;box-shadow:0 4px 18px rgba(0,0,0,.25);
 padding:10px 12px;max-height:min(calc(100vh - 240px),560px);overflow:auto}
/* the panel sits in flow BELOW the chip/☁/🌧 row and the radar legend, so they never overlap */
.wxhead{display:flex;align-items:center;gap:8px;margin-bottom:6px}
.wxplace{font-weight:700;font-size:14px;flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.wxclose{border:0;background:transparent;font-size:16px;line-height:1;color:#555;cursor:pointer;padding:2px 5px;flex:none}
.wxnow{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:8px}
.wxnow .wxbig{font-size:26px;font-weight:700}
.wxnow .wxico{font-size:26px;line-height:1}
.wxnow .wxsub{font-size:12px;color:#555;line-height:1.45}
.wxdays{display:flex;gap:4px;flex-wrap:wrap;margin-bottom:6px}
.wxday{border:1px solid rgba(0,0,0,.12);border-radius:8px;padding:3px 8px;background:#fff;cursor:pointer;
 font:inherit;font-size:12px;color:inherit}
.wxday.on{background:#2b6cb0;color:#fff;border-color:#2b6cb0}
.wxsun{font-size:12px;color:#555;margin-bottom:6px;display:flex;align-items:center;justify-content:space-between;gap:8px}
.wxnav{display:flex;gap:4px;flex:none}
.wxscrollwrap{position:relative}
.wxscroll{overflow-x:auto;overscroll-behavior-x:contain;cursor:grab;-webkit-overflow-scrolling:touch}
.wxscroll.drag{cursor:grabbing;user-select:none}
.wxtab{border-collapse:collapse;font-size:12px;white-space:nowrap}
.wxtab th{position:sticky;left:0;background:rgba(255,255,255,.97);text-align:left;font-weight:600;color:#555;
 padding:2px 8px 2px 2px;font-size:11px}
.wxtab td{text-align:center;padding:2px 4px;min-width:44px;font-variant-numeric:tabular-nums}
.wxtab tr.wxhr td{font-weight:700;color:#333}
/* hours that start in the night (after evening civil twilight, before morning civil twilight) */
.wxtab tr.wxhr td.wxnight{background:#33415c;color:#fff;border-radius:4px}
:root[data-theme="dark"] .wxtab tr.wxhr td.wxnight{background:#1b2440;color:#e8e8ea;box-shadow:inset 0 0 0 1px #6b7fa6}
.wxnote{line-height:1.35}
.wxnote + .wxnote{margin-top:2px}
.wxtab td.wxw{background:rgba(255,140,48,.28);border-radius:4px}
.wxtab td.wxd{background:rgba(208,48,48,.30);border-radius:4px;font-weight:700}
.wxtab td.wxrain{color:#2b6cb0;font-weight:700}
.wxtab td.wxsnowcell{color:#7c3aed;font-weight:700}
.wxarr{display:inline-block;font-size:10px;color:#777;margin-left:1px}
.wxnavbtn{border:1px solid rgba(0,0,0,.12);border-radius:50%;width:24px;height:24px;background:#fff;cursor:pointer;
 font-size:10px;color:#555;display:flex;align-items:center;justify-content:center;padding:0}
.wxnavbtn:hover{background:#f2f2f2}
.wxfoot{font-size:10px;color:#888;margin-top:7px}
.wxfoot a{color:#2b6cb0}
.wxmsg{color:#777;padding:8px 0}
/* phone: the whole widget shrinks and the button row wraps instead of running
   off-screen when the place name is long; popups get the compact treatment */
@media (max-width:640px){
 .wxlayers{flex-wrap:wrap;max-width:calc(100vw - 20px)}
 #wxchip{font-size:12px;padding:0 10px;height:34px}
 #wxchip .wxnm{max-width:40vw}
 .wxlbtn{font-size:12px;padding:0 8px;height:28px}
 #wxframe{font-size:10px;padding:2px 5px}
 #wxlegend{font-size:10px;gap:6px;padding:4px 7px}
 #wxfcbar{font-size:10px;padding:4px 7px}
 #wxltg{font-size:10px;padding:4px 7px}
 #wxpanel{position:fixed;left:0;right:0;bottom:0;top:auto;width:auto;max-height:58vh;
  font-size:11px;padding:8px 10px calc(8px + env(safe-area-inset-bottom,0px));
  border-radius:14px 14px 0 0;box-shadow:0 -4px 20px rgba(0,0,0,.3)}
 .wxplace{font-size:12px}
 .wxnow{gap:9px;margin-bottom:6px}
 .wxnow .wxbig{font-size:20px}
 .wxnow .wxico{font-size:20px}
 .wxnow .wxsub{font-size:11px;line-height:1.35}
 .wxday{font-size:11px;padding:2px 6px}
 .wxsun{font-size:11px}
 .wxtab{font-size:10.5px}
 .wxtab th{font-size:10px}
 .wxtab td{min-width:38px;padding:2px 3px}
 .wxfoot{font-size:9px}
 .wxnavbtn{display:none}
 .wxplnpop .leaflet-popup-content{max-width:58vw;font-size:11px;line-height:1.4;margin:8px 10px}
 .wxplnpop .maplibregl-popup-content{max-width:58vw;font-size:11px;line-height:1.4;padding:6px 9px}
}
/* a phone in LANDSCAPE (wide, but short): the card stays under the chip, so while it is open the
   left buttons below it hide and it may take the screen's height - the desktop cap (100vh - 240px)
   left it ~170 px on a phone, squeezed further by those buttons (owner 21.10). The portrait
   bottom sheet above and the computer are unchanged. #leftui.wxopen is set while the card is open. */
@media (min-width:641px) and (max-height:500px){
 #leftui.wxopen>#menubtn,#leftui.wxopen>#loupe,#leftui.wxopen>#wxgj,#leftui.wxopen>#plnbtn,#leftui.wxopen>#ognbtn{display:none}
 #wxpanel{max-height:calc(100vh - 68px)}
}
"""

WX_HTML = r"""<div id="wx">
 <button id="wxchip" aria-label="weather">…</button>
 <div id="wxpanel" hidden>
  <div class="wxhead"><span class="wxplace" id="wxplace"></span><button class="wxclose" id="wxclose" aria-label="close">✕</button></div>
  <div class="wxlayers">
   <button class="wxlbtn" id="wxcld" aria-label="clouds and lightning"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 16.5h-.5a4 4 0 0 1-.4-7.98A6 6 0 0 1 17.6 8.1 4.2 4.2 0 0 1 18 16.5h-1"/><path d="M12.6 12.5 10.4 16.6h3.4l-2.2 4.4"/></svg></button>
   <button class="wxlbtn" id="wxrad" aria-label="rain">🌧</button>
   <button class="wxlbtn" id="wxwind" aria-label="wind"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M17.7 7.7a2.5 2.5 0 1 1 1.8 4.3H2"/><path d="M9.6 4.6A2 2 0 1 1 11 8H2"/><path d="M12.6 19.4A2 2 0 1 0 14 16H2"/></svg></button>
   <button class="wxlbtn" id="wxsnow" aria-label="snow">❄️</button>
   <span id="wxframe" hidden></span>
  </div>
  <div id="wxwindh" hidden><span class="wxhlbl" data-wxl="height"></span><span class="wxhseg"><button data-h="10" class="on">10 m</button><button data-h="120">120 m</button></span></div>
  <div id="wxfcbar" hidden><input id="wxfcsl" type="range" min="0" max="72" step="1" value="0"><span id="wxfclbl"></span><span id="wxfcnote"></span></div>
  <div id="wxlegend" hidden>
   <span class="wxlg"><i style="background:#9e9375"></i><span data-wxl="drz"></span></span>
   <span class="wxlg"><i style="background:#88ddee"></i><span data-wxl="lgt"></span></span>
   <span class="wxlg"><i style="background:#0077aa"></i><span data-wxl="mod"></span></span>
   <span class="wxlg"><i style="background:#ffee00"></i><span data-wxl="hvy"></span></span>
   <span class="wxlg"><i style="background:#ff4400"></i><span data-wxl="str"></span></span>
   <span class="wxlg"><i style="background:#ff77ff"></i><span data-wxl="hail"></span></span>
   <span id="wxrvnote" hidden></span>
  </div>
  <div id="wxsnowlegend" hidden>
   <span class="wxlg"><i style="background:#d9c7f0"></i><span data-wxl="snTrace"></span></span>
   <span class="wxlg"><i style="background:#b79ae6"></i><span data-wxl="snLgt"></span></span>
   <span class="wxlg"><i style="background:#9060d8"></i><span data-wxl="snMod"></span></span>
   <span class="wxlg"><i style="background:#6a2fb8"></i><span data-wxl="snStr"></span></span>
   <span class="wxlg"><i style="background:#4a1a8a"></i><span data-wxl="snHvy"></span></span>
  </div>
  <div id="wxltg" hidden></div>
  <div id="wxbody"></div>
  <div class="wxfoot"><span id="wxfootlbl"></span> <a href="https://open-meteo.com/" target="_blank" rel="noopener">Open-Meteo</a></div>
 </div>
</div>"""

WX_JS = r"""
// ---- weather widget (Open-Meteo, map-center based) ----
(function(){
var WXT = {
 bg:{now:'Сега',hum:'влажност',gust:'порив',rain:'дъжд %',rmm:'валеж мм',cld:'облаци',sunrise:'изгрев',sunset:'залез',today:'Днес',
     night:'нощ',nightNote:'Тъмните часове = нощ (след гражданския здрач): по правилата за дронове е нужна зелена мигаща светлина.',
     dew:'оросяване',low:'ниски обл.',vis:'видимост км',cape:'⛈ CAPE',frz:'0°C на (м)',
     dewNote:'Оросяване: колкото по-близо е до температурата, толкова по-вероятни са мъгла и конденз.',
     capeNote:'⛈ CAPE (енергия за гръмотевични бури, J/kg): под 1000 слаба · 1000–2500 умерена · 2500–4000 силна · над 4000 екстремна.',
     frzNote:'0°C на (м): височината над морското равнище, на която въздухът е 0°C',frzHere:'теренът тук е ≈ {h} м',
     hh:'час',t:'°C',w10:'вятър 10 м',w80:'вятър 80 м',w120:'вятър 120 м',ms:'м/с',foot:'Прогноза:',nodata:'Няма данни за тук',wxLimitDay:'Изчерпан дневен лимит на метео заявките — нулира се в {t}',wxLimit:'Изчерпан лимит на метео заявките (временно)',wxDown:'Метео услугата временно е недостъпна',
     days:['нд','пн','вт','ср','чт','пт','сб'],title:'Метео прогноза (центъра на картата)',
     bCld:'Облаци и мълнии — сателит сега (мълнии: последните 30 мин), модел напред (облаци и бури)',
     ltgNow:'⚡ Мълнии (сателит EUMETSAT): последните 30 мин, до {t}; по-бледите ⚡ са по-стари.',
     ltgOld:'⚡ Мълнии: няма нови данни след {t}.',ltgErr:'⚡ Мълнии: данните временно не се зареждат.',
     cldAt:'Облаци: сателитна снимка от {t}.',
     stormKey:'⛈ Възможни бури: жълта ⚡ — по-вероятно (показват я поне 2 от 3 различни прогнозни модела), бледа <span class="wxpale">⚡</span> — по-малко вероятно (показва я само един модел).',
     stormNone:'⛈ Без бури по прогнозата за този час',bRad:'Дъжд — радар сега, модел напред (плъзгач)',bPln:'Самолети на живо (adsb.fi / adsb.lol)',
     bWind:'Вятър — частиците текат по вятъра (модел Open-Meteo)',height:'Височина',bSnow:'Прогноза за сняг +72 ч (модел Open-Meteo, в см)',
     bOgn:'Нисък трафик — планери/парапланери/лека авиация (OGN/FLARM; само където има приемник)',
     fcNote:'моделът може да пропуска локални валежи',
     drz:'ръмеж',lgt:'слаб',mod:'умерен',hvy:'силен',str:'буря',hail:'град',snTrace:'следа',snLgt:'слаб',snMod:'умерен',snStr:'силен',snHvy:'обилен',snowRow:'сняг см',
     bGj:'GPS смущения (наши данни от самолетите, последни 12 ч) — дял самолети с влошен GPS на височина; празно = няма прелетели самолети; не значи смущение при земята',gjX:'малко данни',gjG:'чисто',gjY:'2–10% смутени',gjR:'>10% смутени',gjNote:'На самолетна височина',gjLive:'На живо',gjW12:'12ч',gjW24:'24ч',gjHr:'ч',gjStamp:'данни към',
     rvNote:'нощем слабото ехо може да е шум'},
 en:{now:'Now',hum:'humidity',gust:'gust',rain:'rain %',rmm:'rain mm',cld:'clouds',sunrise:'sunrise',sunset:'sunset',today:'Today',
     night:'night',nightNote:'Dark hours = night (after civil twilight): drone rules require a green flashing light.',
     dew:'dew point',low:'low clouds',vis:'visibility km',cape:'⛈ CAPE',frz:'0°C at (m)',
     dewNote:'Dew point: the closer it is to the temperature, the likelier fog and condensation.',
     capeNote:'⛈ CAPE (energy for thunderstorms, J/kg): below 1000 weak · 1000–2500 moderate · 2500–4000 strong · above 4000 extreme.',
     frzNote:'0°C at (m): the height above sea level where the air is 0°C',frzHere:'the ground here is ≈ {h} m',
     hh:'hour',t:'°C',w10:'wind 10 m',w80:'wind 80 m',w120:'wind 120 m',ms:'m/s',foot:'Forecast:',nodata:'No data for this spot',wxLimitDay:'Weather request limit reached — resets at {t}',wxLimit:'Weather request limit reached (temporary)',wxDown:'Weather service temporarily unavailable',
     days:['Su','Mo','Tu','We','Th','Fr','Sa'],title:'Weather forecast (map center)',
     bCld:'Clouds and lightning — satellite now (lightning: last 30 min), model ahead (clouds and thunderstorms)',
     ltgNow:'⚡ Lightning (EUMETSAT satellite): last 30 min, up to {t}; fainter ⚡ = older.',
     ltgOld:'⚡ Lightning: no new data after {t}.',ltgErr:'⚡ Lightning: data temporarily unavailable.',
     cldAt:'Clouds: satellite image of {t}.',
     stormKey:'⛈ Possible thunderstorms: yellow ⚡ — more likely (at least 2 of 3 different forecast models show it), pale <span class="wxpale">⚡</span> — less likely (only one model shows it).',
     stormNone:'⛈ No thunderstorms in the forecast for this hour',bRad:'Rain — radar now, model ahead (slider)',bPln:'Live aircraft (adsb.fi / adsb.lol)',
     bWind:'Wind — particles flow with the wind (Open-Meteo model)',height:'Height',bSnow:'Snow forecast +72 h (Open-Meteo model, in cm)',
     bOgn:'Low-level traffic — gliders/paragliders/light aircraft (OGN/FLARM; only where a receiver hears them)',
     fcNote:'the model can miss local showers',
     drz:'drizzle',lgt:'light',mod:'moderate',hvy:'heavy',str:'storm',hail:'hail',snTrace:'trace',snLgt:'light',snMod:'moderate',snStr:'heavy',snHvy:'very heavy',snowRow:'snow cm',
     bGj:'GPS interference (our own data from aircraft, last 12 h) — share of aircraft with degraded GPS at altitude; blank = no aircraft flew there; may not reach ground level',gjX:'few data',gjG:'clean',gjY:'2–10% affected',gjR:'>10% affected',gjNote:'At aircraft altitude',gjLive:'Live',gjW12:'12h',gjW24:'24h',gjHr:'h',gjStamp:'data as of',
     rvNote:'faint night echoes can be noise'}
};
// caution / danger thresholds for wind + gusts, m/s (visual aid for small drones)
var WX_WARN = 8, WX_DANGER = 12;
var WX_BBOX = {w:22.3, s:41.2, e:28.7, n:44.2}; // fetch only inside Bulgaria (search bbox)
var wxData = null, wxDay = 0, wxCell = '', wxAt = 0, wxNames = {}, wxTimer = null, wxOpen = false, wxRetry = null, wxRetryMs = 7000, wxErr = null;
// place names persist across page loads (they never change), so the chip fills
// instantly on a 2D<->3D switch instead of waiting on Photon again
try{ wxNames = JSON.parse(localStorage.getItem('wxnm')) || {}; }catch(e){}
var wxEl = document.getElementById('wx'), wxChip = document.getElementById('wxchip'),
    wxPanel = document.getElementById('wxpanel'), wxBody = document.getElementById('wxbody'),
    wxPlaceEl = document.getElementById('wxplace');
function wxLang(){ return (typeof LANG !== 'undefined' && LANG === 'en') ? 'en' : 'bg'; }
function wxCellOf(c){ return (Math.round(c.lat / 0.05) * 0.05).toFixed(2) + ',' + (Math.round(c.lng / 0.05) * 0.05).toFixed(2); } // ~5 km cell key from a center; the place name uses THIS, not the weather-fetch wxCell (which the retry resets to '')
function wxEsc(s){ return (s + '').replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
function wxIco(code, day){
  if (code === 0) return day ? '☀️' : '🌙';
  if (code === 1) return day ? '🌤️' : '🌙';
  if (code === 2) return '⛅';
  if (code === 3) return '☁️';
  if (code === 45 || code === 48) return '🌫️';
  if (code >= 51 && code <= 57) return '🌦️';
  if (code >= 61 && code <= 67) return '🌧️';
  if (code >= 71 && code <= 77) return '🌨️';
  if (code >= 80 && code <= 82) return '🌧️';
  if (code === 85 || code === 86) return '🌨️';
  if (code >= 95) return '⛈️';
  return '☁️';
}
function wxArrow(dir){ // met. direction = FROM; arrow shows where the wind blows TO
  return '<span class="wxarr" style="transform:rotate(' + Math.round(dir + 180) + 'deg)">↑</span>';
}
function wxCls(v){ return v >= WX_DANGER ? ' class="wxd"' : (v >= WX_WARN ? ' class="wxw"' : ''); }
function wxV(v){ return (v == null) ? '—' : (Math.round(v * 10) / 10).toFixed(1); }
function wxPos(){ /* no-op: #wx now sits in the #leftui flex column, positioned by layout */ }
function wxNowHourIdx(){ // hourly index for the current hour (hourly + current share the tz)
  if (!wxData || !wxData.current || !wxData.hourly) return -1;
  var nowH = wxData.current.time.slice(0, 13), ts = wxData.hourly.time;
  for (var i = 0; i < ts.length; i++){ if (ts[i].slice(0, 13) >= nowH) return i; }
  return 0;
}
// Civil twilight = the sun's centre 6° below the horizon. The EU drone rules call the time from
// the end of evening civil twilight to the start of morning civil twilight "night" (Reg.
// 2019/947 Art. 2(34)); a green flashing light is required then (UAS.OPEN.060(2)(g)). Computed
// for the forecast point with no extra request; matches the USNO calculator (Sofia 15.10.2026:
// 07:11 / 19:13). Returns [dawn, dusk] as UTC ms for the local date 'YYYY-MM-DD', or null.
function wxCivil(lat, lng, ds){
  var y = +ds.slice(0, 4), mo = +ds.slice(5, 7) - 1, d = +ds.slice(8, 10), rad = Math.PI / 180, out = [];
  for (var k = 0; k < 2; k++){
    var t = Date.UTC(y, mo, d, 12) - lng / 15 * 3600000; // first guess: local solar noon
    for (var it = 0; it < 4; it++){ // refine the sun's position at the event itself
      var n = t / 86400000 + 2440587.5 - 2451545.0; // days since J2000
      var L = (280.460 + 0.9856474 * n) % 360, g = ((357.528 + 0.9856003 * n) % 360) * rad;
      var lam = (L + 1.915 * Math.sin(g) + 0.020 * Math.sin(2 * g)) * rad, eps = (23.439 - 0.0000004 * n) * rad;
      var dec = Math.asin(Math.sin(eps) * Math.sin(lam));
      var ra = (Math.atan2(Math.cos(eps) * Math.sin(lam), Math.cos(lam)) / rad + 360) % 360;
      var eqt = (L - ra + 540) % 360 - 180; // equation of time, degrees
      var cosH = (Math.sin(-6 * rad) - Math.sin(lat * rad) * Math.sin(dec)) / (Math.cos(lat * rad) * Math.cos(dec));
      if (cosH < -1 || cosH > 1) return null; // no civil twilight that day (polar; never in Bulgaria)
      t = Date.UTC(y, mo, d) + (720 - 4 * lng - 4 * eqt + (k ? 4 : -4) * Math.acos(cosH) / rad) * 60000;
    }
    out.push(t);
  }
  return out;
}
var wxTzF = {}, wxCivCache = {};
function wxLocalHM(ms){ // UTC ms -> 'HH:MM' in the forecast's own time zone, to the nearest minute
  ms = Math.round(ms / 60000) * 60000;
  var tz = (wxData && wxData.timezone) || 'Europe/Sofia';
  try{
    var f = wxTzF[tz] || (wxTzF[tz] = new Intl.DateTimeFormat('en-GB', {timeZone: tz, hour: '2-digit', minute: '2-digit', hour12: false}));
    var p = {}; f.formatToParts(new Date(ms)).forEach(function(x){ p[x.type] = x.value; });
    return (p.hour === '24' ? '00' : p.hour) + ':' + p.minute;
  }catch(e){ // no Intl time zones: use the forecast's own UTC offset
    var dt = new Date(ms + ((wxData && wxData.utc_offset_seconds) || 0) * 1000);
    return ('0' + dt.getUTCHours()).slice(-2) + ':' + ('0' + dt.getUTCMinutes()).slice(-2);
  }
}
function wxCivilHM(ds){ // {dawn, dusk} as local 'HH:MM' for a local date at the forecast point (cached)
  if (!wxData || wxData.latitude == null) return null;
  var key = wxData.latitude + ',' + wxData.longitude + ',' + ds;
  if (!(key in wxCivCache)){ var r = wxCivil(wxData.latitude, wxData.longitude, ds);
    wxCivCache[key] = r ? {dawn: wxLocalHM(r[0]), dusk: wxLocalHM(r[1])} : null; }
  return wxCivCache[key];
}
function wxNextDay(ds){ return new Date(Date.UTC(+ds.slice(0, 4), +ds.slice(5, 7) - 1, +ds.slice(8, 10) + 1)).toISOString().slice(0, 10); }
function wxIsNight(ts){ // local 'YYYY-MM-DDTHH:MM' -> true when that hour starts in the night
  var c = wxCivilHM(ts.slice(0, 10)), hm = ts.slice(11, 16);
  return !!c && (hm < c.dawn || hm >= c.dusk);
}
// the chip's short form: the name up to its first comma ("София, София-град" -> "София"); the
// coordinates shown where there is no place name stay whole ("42.82, 20.35": both numbers)
function wxShortName(nm){ return /^-?\d+(\.\d+)?, -?\d+(\.\d+)?$/.test(nm) ? nm : nm.split(',')[0]; }
function wxChipHTML(){
  var t = WXT[wxLang()];
  if (!wxData || !wxData.current || wxErr){ // no usable current weather -> show just the place name
    var nm0 = wxShortName(wxNames[wxCellOf(map.getCenter()) + '|' + wxLang()] || '');
    wxChip.innerHTML = nm0 ? '<span class="wxnm">' + wxEsc(nm0) + '</span>' : '…';
    wxChip.title = t.title; return; }
  var c = wxData.current;
  // when the wind layer is on, the chip shows what the particles depict: the wind at
  // the selected HEIGHT and the selected forecast HOUR (0 = now), so the number matches
  var ws = c.wind_speed_10m, wd = c.wind_direction_10m, hsfx = '';
  if (window.wxWindState && window.wxWindState.on && wxData.hourly){
    var wh = window.wxWindState.h, whr = (window.wxFcState ? window.wxFcState.hour : 0);
    var sk = wxData.hourly['wind_speed_' + wh + 'm'], dk = wxData.hourly['wind_direction_' + wh + 'm'];
    var widx = wxNowHourIdx() + whr;
    if (widx >= 0 && sk && widx < sk.length){ ws = sk[widx]; wd = dk[widx];
      hsfx = (wh === 120 ? ' (120m)' : '') + (whr > 0 ? ' +' + whr + (wxLang() === 'en' ? 'h' : 'ч') : ''); }
  }
  var nm = wxNames[wxCellOf(map.getCenter()) + '|' + wxLang()] || '';
  nm = wxShortName(nm); // short form in the chip; the panel shows the full name
  wxChip.innerHTML = (nm ? '<span class="wxnm">' + wxEsc(nm) + '</span> ' : '') +
    wxIco(c.weather_code, c.is_day) + ' ' + Math.round(c.temperature_2m) + '° · ' +
    wxV(ws) + ' ' + t.ms + hsfx + wxArrow(wd);
  wxChip.title = t.title;
}
function wxDayTabs(){
  var t = WXT[wxLang()], h = '', times = wxData.daily.time;
  for (var i = 0; i < times.length; i++){
    var d = new Date(times[i] + 'T12:00');
    var lbl = (i === 0) ? t.today : (t.days[d.getDay()] + ' ' + d.getDate());
    h += '<button class="wxday' + (i === wxDay ? ' on' : '') + '" data-d="' + i + '">' + lbl + '</button>';
  }
  return '<div class="wxdays">' + h + '</div>';
}
function wxRow(lbl, cells, cls){
  return '<tr' + (cls ? ' class="' + cls + '"' : '') + '><th>' + lbl + '</th>' + cells + '</tr>';
}
function wxTable(){
  var t = WXT[wxLang()], H = wxData.hourly, times = H.time;
  var d0 = wxData.daily.time[wxDay], start = 0, end = 0, i;
  for (i = 0; i < times.length; i++){
    if (times[i].slice(0, 10) === d0){ if (!end) start = i; end = i + 1; }
  }
  if (wxDay === 0 && wxData.current && wxData.current.time){ // today: start at the current hour
    var nowH = wxData.current.time.slice(0, 13);
    for (i = start; i < end; i++){ if (times[i].slice(0, 13) >= nowH){ start = i; break; } }
  }
  var hr = '', ic = '', te = '', cl = '', w1 = '', w8 = '', w12 = '', gu = '', ra = '', rm = '', sn = '';
  var dw = '', lo = '', vi = '', ca = '', fz = '';
  function hv(k){ return (H[k] && H[k][i] != null) ? H[k][i] : null; } // one hourly value, null when absent
  for (i = start; i < end; i++){
    hr += '<td' + (wxIsNight(times[i]) ? ' class="wxnight"' : '') + '>' + times[i].slice(11, 16) + '</td>';
    ic += '<td>' + wxIco(H.weather_code[i], H.is_day[i]) + '</td>';
    te += '<td>' + Math.round(H.temperature_2m[i]) + '°</td>';
    var dp = hv('dew_point_2m');
    dw += '<td>' + (dp == null ? '—' : Math.round(dp) + '°') + '</td>';
    var cc = H.cloud_cover ? H.cloud_cover[i] : null;
    cl += '<td>' + (cc == null ? '—' : cc + '%') + '</td>';
    var cw = hv('cloud_cover_low');
    lo += '<td>' + (cw == null ? '—' : cw + '%') + '</td>';
    vi += '<td>' + wxVis(hv('visibility')) + '</td>';
    w1 += '<td' + wxCls(H.wind_speed_10m[i]) + '>' + wxV(H.wind_speed_10m[i]) + wxArrow(H.wind_direction_10m[i]) + '</td>';
    w8 += '<td' + wxCls(H.wind_speed_80m[i]) + '>' + wxV(H.wind_speed_80m[i]) + wxArrow(H.wind_direction_80m[i]) + '</td>';
    w12 += '<td' + wxCls(H.wind_speed_120m[i]) + '>' + wxV(H.wind_speed_120m[i]) + wxArrow(H.wind_direction_120m[i]) + '</td>';
    gu += '<td' + wxCls(H.wind_gusts_10m[i]) + '>' + wxV(H.wind_gusts_10m[i]) + '</td>';
    var p = H.precipitation_probability[i];
    ra += '<td' + ((p != null && p >= 50) ? ' class="wxrain"' : '') + '>' + (p == null ? '—' : p + '%') + '</td>';
    var mm = H.precipitation ? H.precipitation[i] : null;
    rm += '<td' + ((mm != null && mm >= 0.5) ? ' class="wxrain"' : '') + '>' + (mm == null ? '—' : (mm === 0 ? '0' : (Math.round(mm * 10) / 10).toFixed(1))) + '</td>';
    var sm = H.snowfall ? H.snowfall[i] : null;
    sn += '<td' + ((sm != null && sm >= 0.1) ? ' class="wxsnowcell"' : '') + '>' + (sm == null ? '—' : (sm === 0 ? '0' : (Math.round(sm * 10) / 10).toFixed(1))) + '</td>';
    var cp = hv('cape');
    ca += '<td' + (cp == null ? '' : wxCapeCls(cp)) + '>' + (cp == null ? '—' : Math.round(cp)) + '</td>';
    var fl = hv('freezing_level_height');
    fz += '<td>' + (fl == null ? '—' : Math.round(fl)) + '</td>';
  }
  return '<div class="wxscrollwrap"><div class="wxscroll" id="wxscroll"><table class="wxtab">' +
    wxRow(t.hh, hr, 'wxhr') + wxRow('', ic) + wxRow(t.t, te) + wxRow(t.dew, dw) + wxRow(t.cld, cl) +
    wxRow(t.low, lo) + wxRow(t.vis, vi) +
    wxRow(t.w10, w1) + wxRow(t.w80, w8) + wxRow(t.w120, w12) +
    wxRow(t.gust, gu) + wxRow(t.rain, ra) + wxRow(t.rmm, rm) + wxRow(t.snowRow, sn) +
    wxRow(t.cape, ca) + wxRow(t.frz, fz) +
    '</table></div></div>';
}
// visibility in km: one decimal under 10 km, whole km above
function wxVis(m){ if (m == null) return '—'; var k = Math.round(m / 100) / 10; return k < 10 ? k.toFixed(1) : String(Math.round(m / 1000)); }
// CAPE bands of the US National Weather Service / SPC (owner, 15.10): moderate 1000-2500 J/kg
// orange, strong (2500-4000) and extreme (>4000) red - the same cell shading as wind
function wxCapeCls(v){ return v >= 2500 ? ' class="wxd"' : (v >= 1000 ? ' class="wxw"' : ''); }
// the explanations under the table, in the table's row order
function wxNotes(){
  var t = WXT[wxLang()], el = wxData ? wxData.elevation : null;
  var frz = t.frzNote + (el != null ? '; ' + t.frzHere.replace('{h}', Math.round(el)) : '') + '.';
  return [t.nightNote, t.dewNote, t.capeNote, frz].map(function(s){ return '<div class="wxfoot wxnote">' + s + '</div>'; }).join('');
}
function wxRender(){
  if (wxWantDate && wxData && wxData.daily && wxData.daily.time){ var wi = wxData.daily.time.indexOf(wxWantDate); wxDay = wi > 0 ? wi : 0; wxWantDate = null; } // a shared view's day
  var t = WXT[wxLang()];
  document.getElementById('wxfootlbl').textContent = t.foot;
  var bC = document.getElementById('wxcld'), bR = document.getElementById('wxrad');
  var bP = document.getElementById('plnbtn'); // aircraft button lives outside the weather card now
  if (bC) bC.title = t.bCld;
  if (bR) bR.title = t.bRad;
  if (bP) bP.title = t.bPln;
  var bW = document.getElementById('wxwind'); if (bW) bW.title = t.bWind;
  var bS = document.getElementById('wxsnow'); if (bS) bS.title = t.bSnow;
  var bO = document.getElementById('ognbtn'); if (bO) bO.title = t.bOgn;
  var bG = document.getElementById('wxgj'); if (bG) bG.title = t.bGj;
  var fN = document.getElementById('wxfcnote');
  if (fN) fN.textContent = t.fcNote;
  if (window.wxFcLabel) window.wxFcLabel();
  document.querySelectorAll('[data-wxl]').forEach(function(el){ el.textContent = t[el.getAttribute('data-wxl')]; });
  if (window.wxGjSyncLabel) window.wxGjSyncLabel();
  var rvN = document.getElementById('wxrvnote');
  if (rvN) rvN.textContent = t.rvNote;
  wxChipHTML();
  if (!wxOpen) return;
  if (wxErr){ wxBody.innerHTML = '<div class="wxmsg">' + wxErrMsg() + '</div>'; return; }
  if (!wxData){ wxBody.innerHTML = '<div class="wxmsg">' + t.nodata + '</div>'; return; }
  var c = wxData.current;
  var now = '<div class="wxnow"><span class="wxico">' + wxIco(c.weather_code, c.is_day) + '</span>' +
    '<span class="wxbig">' + Math.round(c.temperature_2m) + '°C</span>' +
    '<span class="wxsub">' + t.hum + ' ' + c.relative_humidity_2m + '%<br>' +
    wxV(c.wind_speed_10m) + ' ' + t.ms + wxArrow(c.wind_direction_10m) + ' · ' + t.gust + ' ' + wxV(c.wind_gusts_10m) + '</span></div>';
  var sr = wxData.daily.sunrise[wxDay], ss = wxData.daily.sunset[wxDay];
  // the night that follows this day: end of its evening civil twilight -> start of the next morning's
  var ds = wxData.daily.time[wxDay], cv = wxCivilHM(ds), cn = wxCivilHM(wxNextDay(ds));
  var sun = '<div class="wxsun"><span>🌅 ' + t.sunrise + ' ' + sr.slice(11, 16) + ' · 🌇 ' + t.sunset + ' ' + ss.slice(11, 16) +
    ((cv && cn) ? ' · 🌙 ' + t.night + ' ' + cv.dusk + '–' + cn.dawn : '') + '</span>' +
    '<span class="wxnav"><button class="wxnavbtn" id="wxleft">◀</button><button class="wxnavbtn" id="wxright">▶</button></span></div>';
  wxBody.innerHTML = now + wxDayTabs() + sun + wxTable() + wxNotes();
  wxBody.querySelectorAll('.wxday').forEach(function(b){
    b.onclick = function(e){ e.stopPropagation(); wxDay = +b.getAttribute('data-d'); wxRender(); };
  });
  var sc = document.getElementById('wxscroll');
  // mouse wheel scrolls the hour strip horizontally
  sc.addEventListener('wheel', function(e){
    if (Math.abs(e.deltaY) > Math.abs(e.deltaX)){ e.preventDefault(); sc.scrollLeft += e.deltaY; }
  }, {passive:false});
  // click-drag scrolling for desktop (touch scrolls natively)
  var dragX = null, dragL = 0;
  sc.addEventListener('pointerdown', function(e){ if (e.pointerType === 'mouse'){ dragX = e.clientX; dragL = sc.scrollLeft; sc.classList.add('drag'); } });
  window.addEventListener('pointermove', function(e){ if (dragX != null){ sc.scrollLeft = dragL - (e.clientX - dragX); } });
  window.addEventListener('pointerup', function(){ dragX = null; sc.classList.remove('drag'); });
  document.getElementById('wxleft').onclick = function(){ sc.scrollBy({left:-220, behavior:'smooth'}); };
  document.getElementById('wxright').onclick = function(){ sc.scrollBy({left:220, behavior:'smooth'}); };
  wxPlaceName();
}
function wxPlaceName(){
  var l = wxLang(), c = map.getCenter(), key = wxCellOf(c) + '|' + l;
  if (wxNames[key]){ wxPlaceEl.textContent = wxNames[key]; wxChipHTML(); return; }
  wxPlaceEl.textContent = '…';
  fetch('https://photon.komoot.io/reverse?lat=' + c.lat.toFixed(4) + '&lon=' + c.lng.toFixed(4) + '&lang=' + (l === 'en' ? 'en' : 'default'))
    .then(function(r){ return r.json(); })
    .then(function(d){
      var p = (d.features && d.features[0] && d.features[0].properties) || {};
      var nm = (p.osm_value === 'city' || p.osm_value === 'town' || p.osm_value === 'village' || p.osm_value === 'hamlet') ? p.name : '';
      var out = nm || p.city || p.county || p.state || p.name || (c.lat.toFixed(2) + ', ' + c.lng.toFixed(2));
      if (p.state && out !== p.state) out += ', ' + p.state;
      wxNames[key] = out; try{ localStorage.setItem('wxnm', JSON.stringify(wxNames)); }catch(e){}
      wxPlaceEl.textContent = out; wxChipHTML();
    }).catch(function(){ wxPlaceEl.textContent = c.lat.toFixed(2) + ', ' + c.lng.toFixed(2); });
}
// Open-Meteo unavailable: tell a rate-LIMIT (429 / "...limit exceeded") apart from a
// service outage, and for the DAILY limit show when it resets (00:00 UTC) in local time.
function wxResetStr(){ var n = new Date();
  var r = new Date(Date.UTC(n.getUTCFullYear(), n.getUTCMonth(), n.getUTCDate() + 1, 0, 0, 0));
  return ('0' + r.getHours()).slice(-2) + ':' + ('0' + r.getMinutes()).slice(-2); }
function wxErrMsg(){ var t = WXT[wxLang()];
  if (!wxErr) return t.nodata;
  if (wxErr.type === 'limit'){ var rs = (wxErr.reason || '').toLowerCase();
    return (rs.indexOf('daily') >= 0 || rs.indexOf('tomorrow') >= 0) ? t.wxLimitDay.replace('{t}', wxResetStr()) : t.wxLimit; }
  return t.wxDown; }
function wxFetch(){
  var c = map.getCenter();
  if (c.lng < WX_BBOX.w || c.lng > WX_BBOX.e || c.lat < WX_BBOX.s || c.lat > WX_BBOX.n) return; // keep last data outside BG
  var cell = (Math.round(c.lat / 0.05) * 0.05).toFixed(2) + ',' + (Math.round(c.lng / 0.05) * 0.05).toFixed(2);
  if (cell === wxCell && wxData && (Date.now() - wxAt) < 900000) return; // same ~5 km cell, fresh (<15 min)
  // instant paint from a persisted cache for this cell: the 2D<->3D switch carries
  // the map center, so the new page's cell matches and the chip fills with no network
  if (!wxData || wxCell !== cell){
    try{ var cw = JSON.parse(localStorage.getItem('wxwx2')); // '2': the answer carries visibility/low cloud/dew point/0°C/CAPE since 15.10
      if (cw && cw.cell === cell && (Date.now() - cw.at) < 900000){
        wxData = cw.data; wxCell = cell; wxAt = cw.at;
        if (wxDay >= wxData.daily.time.length) wxDay = 0;
        wxErr = null; wxRender(); wxPlaceName(); return; // fresh enough — skip the network entirely
      }
    }catch(e){}
  }
  wxCell = cell; wxAt = Date.now();
  var u = 'https://api.open-meteo.com/v1/forecast?latitude=' + c.lat.toFixed(4) + '&longitude=' + c.lng.toFixed(4) +
    '&current=temperature_2m,relative_humidity_2m,weather_code,is_day,wind_speed_10m,wind_direction_10m,wind_gusts_10m' +
    '&hourly=temperature_2m,weather_code,is_day,precipitation_probability,precipitation,snowfall,cloud_cover,' +
    'wind_speed_10m,wind_speed_80m,wind_speed_120m,wind_gusts_10m,wind_direction_10m,wind_direction_80m,wind_direction_120m,' +
    'visibility,cloud_cover_low,dew_point_2m,freezing_level_height,cape' +
    '&daily=sunrise,sunset&wind_speed_unit=ms&timezone=auto&forecast_days=8'; // today + 7 full days ahead
  fetch(u).then(function(r){ var st = r.status; return r.json().then(function(d){ return [st, d]; }, function(){ return [st, null]; }); })
    .then(function(sd){ var st = sd[0], d = sd[1];
      if (d && d.hourly && d.current){ wxErr = null; wxData = d; wxRetryMs = 7000; if (wxDay >= d.daily.time.length) wxDay = 0;
        try{ localStorage.setItem('wxwx2', JSON.stringify({cell: cell, at: Date.now(), data: d})); }catch(e){}
        wxRender(); wxPlaceName(); }
      else { // a rate-limited answer (HTTP 429) is an error JSON, not data; tell it apart from an outage
        var reason = (d && d.reason) || '';
        wxErr = { type: (st === 429 || /limit/i.test(reason)) ? 'limit' : 'down', reason: reason };
        wxPlaceName(); wxRender(); wxRetryLater(); }
    }).catch(function(){ wxErr = { type: 'down', reason: '' }; wxPlaceName(); wxRender(); wxRetryLater(); });
}
function wxRetryLater(){ // failed fetch: forget the cell so the retry truly refetches,
  // and try again by itself instead of waiting for the user to pan the map;
  // the delay doubles up to 1 min so a longer block is not hammered
  wxCell = ''; clearTimeout(wxRetry); wxRetry = setTimeout(wxFetch, wxRetryMs);
  wxRetryMs = Math.min(wxRetryMs * 2, 60000);
}
// the line under the slider while ☁ is on: at "now" the lightning window (last 30 min, up to the
// newest EUMETSAT step, local time) or a stale/failed notice; ahead the model-thunderstorm key
window.wxLtgNote = function(){
  var el = document.getElementById('wxltg'); if (!el) return;
  var cb = document.getElementById('wxcld');
  if (!cb || !cb.classList.contains('on')){ el.hidden = true; return; }
  var t = WXT[wxLang()], S = window.wxFcState, L = window.wxLiState || {}, h = '';
  function hm(ms){ var d = new Date(ms); return ('0' + d.getHours()).slice(-2) + ':' + ('0' + d.getMinutes()).slice(-2); }
  if (!(S && S.hour > 0)){
    // "до HH:MM" = the newest step, or - while the lightning follows the radar loop - that frame's window
    if (L.end) h = (Date.now() - L.end > 2700000) ? '<span class="wxltgbad">' + t.ltgOld.replace('{t}', hm(L.end)) + '</span>' : t.ltgNow.replace('{t}', hm(window.wxLiRef || L.end));
    else if (L.err) h = '<span class="wxltgbad">' + t.ltgErr + '</span>';
    // the satellite clouds are ONE picture (not 30 min): its own time, ~15-40 min behind (owner 15.10)
    if (window.wxCldTime) h += (h ? ' ' : '') + t.cldAt.replace('{t}', hm(window.wxCldTime));
  } else if (S.lastStorm != null){
    h = S.lastStorm < 0.5 ? t.stormNone : t.stormKey;
  }
  el.innerHTML = h; el.hidden = !h;
};
(window.wxLangRefresh = window.wxLangRefresh || []).push(function(){ window.wxLtgNote(); });
window.closeWxPanel = function(){ wxOpen = false; wxPanel.hidden = true; };
// #leftui.wxopen while the card is open (the landscape CSS hides the left buttons below it); watched on
// the card's own hidden attribute, so every way of opening / closing it is covered
(function(){ var lu = document.getElementById('leftui'); if (!lu || !window.MutationObserver) return;
  function sync(){ lu.classList.toggle('wxopen', !wxPanel.hidden); }
  new MutationObserver(sync).observe(wxPanel, {attributes: true, attributeFilter: ['hidden']}); sync(); })();
wxChip.onclick = function(e){ e.stopPropagation(); wxOpen = !wxOpen; wxPanel.hidden = !wxOpen;
  if (wxOpen){ if (window.closePanel) window.closePanel(); if (window.collapseLoupe) window.collapseLoupe(); if (window.closeBmPanel) window.closeBmPanel(); wxRender(); } };
// a shared-view link (ROADMAP 8b) reopens the card: the same place (the map centre comes with the
// link) and the same day while it is still in the forecast (a day already gone -> today)
var wxWantDate = null;
window.wxPanelOpen = function(date){ wxWantDate = date || null; wxOpen = true; wxPanel.hidden = false; wxRender(); };
window.wxPanelDate = function(){ if (!wxOpen) return null; // the open card's day as a date ('' = not loaded yet)
  return (wxData && wxData.daily && wxData.daily.time && wxData.daily.time[wxDay]) || ''; };
// weather map layers: the buttons only flip state; each map page provides
// wxSetClouds/wxSetRain (see the per-map layer script)
// every switch is saved in the shared settings store (ST) so it survives a
// reload and the 2D<->3D switch; the restore block after the layer scripts
// reads the same keys back on page load
document.getElementById('wxcld').onclick = function(e){ e.stopPropagation();
  var on = this.classList.toggle('on'); ST.set('cld', on);
  wxSyncFcBar(); // clouds share the +hours slider: satellite at 0, model ahead
  if (window.wxSetClouds) window.wxSetClouds(on); };
// one "Дъжд" button: RainViewer radar at hour 0 ("now") + Open-Meteo model rain
// ahead on the slider — time-aware like the clouds; it shares the +hours slider
document.getElementById('wxrad').onclick = function(e){ e.stopPropagation();
  var on = this.classList.toggle('on'); ST.set('rad', on);
  wxSyncFcBar();
  if (window.wxSetRain) window.wxSetRain(on); };
// snow is independent of the rain layers (a place is either raining or snowing);
// its own violet legend, and it shares the same +hours slider
document.getElementById('wxsnow').onclick = function(e){ e.stopPropagation();
  var on = this.classList.toggle('on'); ST.set('snow', on);
  wxSyncFcBar();
  if (window.wxSetSnow) window.wxSetSnow(on); };
// GPS interference is a live-window layer (our /gpsown cells, last 12 h);
// independent of the +hours forecast slider
document.getElementById('wxgj').onclick = function(e){ e.stopPropagation();
  var on = this.classList.toggle('on'); ST.set('gj', on);
  if (window.wxSetGj) window.wxSetGj(on); };
// airspace + NOTAM toggles are CHIPS in the drawer (not on-map buttons)
['cbAirC:airc:wxSetAirC', 'cbAirS:airs:wxSetAirS', 'cbAct:act:wxSetAct', 'cbAero:aero:wxSetAero', 'cbNotam:notam:wxSetNotam', 'cbNat:nat:wxSetNat', 'cbZzt:zzt:wxSetZzt', 'cbObs:obs:wxSetObs'].forEach(function(s){
  var a = s.split(':'), el = document.getElementById(a[0]); if (!el) return;
  el.onclick = function(e){ e.stopPropagation(); var on = el.classList.toggle('on');
    try{ ST.set(a[1], on); }catch(_){} if (window[a[2]]) window[a[2]](on); };
});
// the +hours slider is SHARED by the rain forecast and the wind layer, so it
// shows whenever either is on and both read the same hour
function wxSyncFcBar(){ var bar = document.getElementById('wxfcbar');
  var sn = document.getElementById('wxsnow'), cl = document.getElementById('wxcld'), rn = document.getElementById('wxrad');
  var show = (rn && rn.classList.contains('on')) || document.getElementById('wxwind').classList.contains('on') || (sn && sn.classList.contains('on')) || (cl && cl.classList.contains('on'));
  bar.hidden = !show; if (show && window.wxFcLabel) window.wxFcLabel(); }
window.wxSyncFcBar = wxSyncFcBar;
// wind particle layer: independent of the rain layers; the height sub-toggle and
// the shared hour slider appear with it
document.getElementById('wxwind').onclick = function(e){ e.stopPropagation();
  var on = this.classList.toggle('on'); ST.set('wind', on);
  document.getElementById('wxwindh').hidden = !on;
  if (window.wxSetWind) window.wxSetWind(on); // sets wxWindState.on FIRST so the chip below reads the right height/hour
  wxSyncFcBar(); wxChipHTML(); };
Array.prototype.forEach.call(document.querySelectorAll('#wxwindh .wxhseg button'), function(b){
  b.onclick = function(e){ e.stopPropagation();
    var h = +b.getAttribute('data-h'); window.wxWindState.h = h; ST.set('windh', h);
    document.querySelectorAll('#wxwindh .wxhseg button').forEach(function(x){ x.classList.toggle('on', x === b); });
    wxChipHTML(); }; // the engine samples the new height on the next frame
});
document.getElementById('wxfcsl').oninput = function(){
  if (window.wxFcState) window.wxFcState.hour = +this.value;
  ST.set('fch', +this.value);
  if (document.getElementById('wxrad').classList.contains('on') && window.wxRainApply) window.wxRainApply();
  var _sn = document.getElementById('wxsnow'); if (_sn && _sn.classList.contains('on') && window.wxSnowApply) window.wxSnowApply();
  var _cl = document.getElementById('wxcld'); if (_cl && _cl.classList.contains('on') && window.wxCloudApply) window.wxCloudApply(); // clouds: satellite at 0, model ahead
  if (window.wxFcLabel) window.wxFcLabel();
  wxChipHTML(); }; // wind chip follows the slider too (wind reads the hour live each frame)
// desktop: mouse wheel over the slider steps the hour by 1 (touch drags natively)
document.getElementById('wxfcsl').addEventListener('wheel', function(e){
  e.preventDefault();
  var mx = +this.max, v = Math.max(0, Math.min(mx, +this.value + (e.deltaY < 0 ? 1 : -1)));
  if (v === +this.value) return;
  this.value = v; this.dispatchEvent(new Event('input')); // reuse the oninput logic above
}, {passive:false});
document.getElementById('plnbtn').onclick = function(e){ e.stopPropagation();
  var on = this.classList.toggle('on'); ST.set('pln', on);
  if (window.wxFlEnable) window.wxFlEnable(on); // FL slider is active only with ✈ on (greyed otherwise)
  if (window.wxSetPlanes) window.wxSetPlanes(on); };
var ognBtn = document.getElementById('ognbtn'); // low-level traffic (OGN/FLARM); absent on pages without the layer yet
if (ognBtn) ognBtn.onclick = function(e){ e.stopPropagation();
  var on = this.classList.toggle('on'); ST.set('ogn', on);
  if (window.wxSetOgn) window.wxSetOgn(on); };
document.getElementById('wxclose').onclick = function(){ wxOpen = false; wxPanel.hidden = true; };
document.addEventListener('click', function(e){
  // a click on a re-rendered element (e.g. a day tab) leaves e.target detached — that's inside, not outside
  if (wxOpen && e.target.isConnected && !wxEl.contains(e.target)){ wxOpen = false; wxPanel.hidden = true; }
});
['langbtn'].forEach(function(id){ var b = document.getElementById(id);
  if (b) b.addEventListener('click', function(){ wxRender(); if (wxCell) wxPlaceName(); }); });
map.on('moveend', function(){ clearTimeout(wxTimer); wxTimer = setTimeout(wxFetch, 1200); });
window.addEventListener('resize', wxPos);
wxPos(); setTimeout(wxPos, 600); wxChipHTML(); wxFetch();
})();

// ---- shared builder for the cloud overlay (used by both maps' layer code) ----
// The geocolour satellite photo is a real PHOTO: at night it turns into city
// lights on black, which grays the whole map. Instead the overlay is composed
// in the browser from two EUMETSAT WMS images that work day and night alike:
// the MSG cloud mask (white = cloud, 15-min updates) says WHERE clouds are, and
// the MTG IR 10.5 um channel (brightness = cold tops, 10-min updates) says how
// THICK they look; clear sky stays fully transparent. Both endpoints answer
// with CORS *, so the canvas may read the pixels (verified).
window.wxCloudBuild = function(cb){
  var LW = 16, LE = 34, LS = 36.5, LN = 48.5, W = 1400; // lon/lat box: BG + wide margin
  function mx(lon){ return lon * 20037508.343 / 180; }
  function my(lat){ return 6378137 * Math.log(Math.tan(Math.PI / 4 + lat * Math.PI / 360)); }
  var x1 = mx(LW), x2 = mx(LE), y1 = my(LS), y2 = my(LN);
  var H = Math.round(W * (y2 - y1) / (x2 - x1));
  var base = 'https://view.eumetsat.int/geoserver/ows?service=WMS&version=1.1.1&request=GetMap' +
    '&srs=EPSG:3857&bbox=' + x1 + ',' + y1 + ',' + x2 + ',' + y2 + '&width=' + W + '&height=' + H +
    '&format=image/png&transparent=true&_=' + Math.floor(Date.now() / 600000) + '&layers=';
  var imgs = [], done = 0;
  // the picture's time for the note under the slider: the newest step of each layer (from their own
  // small capabilities, ~7 KB each, CORS *), the older of the two
  var cts = [], cn = 0;
  ['msg_fes/clm', 'mtg_fd/ir105_hrfi'].forEach(function(l){
    fetch('https://view.eumetsat.int/geoserver/' + l + '/ows?service=WMS&version=1.3.0&request=GetCapabilities&_=' + Math.floor(Date.now() / 600000))
      .then(function(r){ return r.text(); })
      .then(function(x){ var m = x.match(/<Dimension[^>]*name="time"[^>]*default="([^"]+)"/), t = m ? Date.parse(m[1]) : NaN; if (t > 0) cts.push(t); })
      .catch(function(){})
      .then(function(){ if (++cn === 2){ window.wxCldTime = cts.length ? Math.min.apply(0, cts) : 0; if (window.wxLtgNote) window.wxLtgNote(); } });
  });
  ['msg_fes:clm', 'mtg_fd:ir105_hrfi&styles=mtg_fd_ir105_hrfi_grayscale'].forEach(function(q, i){
    var im = new Image(); im.crossOrigin = 'anonymous';
    im.onload = function(){ if (++done === 2) build(); };
    im.onerror = function(){ clearTimeout(window._cldRt); window._cldRt = setTimeout(function(){ if (cldOn && cldMode() === 'sat') cldSatShow(); }, 15000); }; // failed tile: retry in 15 s instead of waiting for the 10-min timer
    im.src = base + q; imgs[i] = im; });
  function build(){
    var cv = document.createElement('canvas'); cv.width = W; cv.height = H;
    var ctx = cv.getContext('2d');
    ctx.drawImage(imgs[0], 0, 0, W, H); var mk = ctx.getImageData(0, 0, W, H).data;
    ctx.clearRect(0, 0, W, H);
    ctx.drawImage(imgs[1], 0, 0, W, H); var ir = ctx.getImageData(0, 0, W, H).data;
    var n = W * H, a = new Float32Array(n), i, i4, t, lum;
    for (i = 0; i < n; i++){ i4 = i * 4;
      lum = 0.2126 * ir[i4] + 0.7152 * ir[i4 + 1] + 0.0722 * ir[i4 + 2];
      if (mk[i4] > 200 && mk[i4 + 1] > 200 && mk[i4 + 2] > 200){ // white = cloud in the mask
        // IR grayscale sits in ~40..140 for clouds (measured day + night samples);
        // thin/low clouds stay faint, cold thick tops go solid white — the depth
        // gradation that makes the layer read like a real cloud picture
        t = (lum - 40) / 100;
        a[i] = 0.62 + 0.38 * (t < 0 ? 0 : (t > 1 ? 1 : t));
      } else {
        // mask says clear: keep a whisper of grey veil so the layer reads as
        // "on", plus a FAINT cloud wherever the IR is clearly brighter than the
        // ground (~<=55 at night, measured) — thin/low cloud the strict mask
        // misses; capped low, since cold night-time ridges can look the same
        t = (lum - 70) / 60;
        a[i] = 0.1 + 0.35 * (t < 0 ? 0 : (t > 1 ? 1 : t));
      }
    }
    // 2-pass box blur of the alpha plane: soft cloud edges instead of the mask's hard ~5 km squares
    var r = 3, tmp = new Float32Array(n), p = new Float32Array(Math.max(W, H) + 1), x, y, row, lo, hi, k;
    for (k = 0; k < 2; k++){
      for (y = 0; y < H; y++){ row = y * W;
        for (x = 0; x < W; x++) p[x + 1] = p[x] + a[row + x];
        for (x = 0; x < W; x++){ lo = x - r < 0 ? 0 : x - r; hi = x + r >= W ? W - 1 : x + r;
          tmp[row + x] = (p[hi + 1] - p[lo]) / (hi - lo + 1); } }
      for (x = 0; x < W; x++){
        for (y = 0; y < H; y++) p[y + 1] = p[y] + tmp[y * W + x];
        for (y = 0; y < H; y++){ lo = y - r < 0 ? 0 : y - r; hi = y + r >= H ? H - 1 : y + r;
          a[y * W + x] = (p[hi + 1] - p[lo]) / (hi - lo + 1); } }
    }
    // colour follows the (blurred) alpha: grey fringes, white cold cores — pure
    // white would vanish over the light basemap (checked on a real screenshot)
    var out = ctx.createImageData(W, H), od = out.data, v;
    for (i = 0; i < n; i++){ i4 = i * 4;
      t = (a[i] - 0.62) / 0.38; v = Math.round(125 + 130 * (t < 0 ? 0 : (t > 1 ? 1 : t)));
      od[i4] = od[i4 + 1] = od[i4 + 2] = v; od[i4 + 3] = Math.round(a[i] * 255); }
    ctx.putImageData(out, 0, 0);
    // the finished canvas + its mercator frame go into the shared registry the
    // 3D tile cutter reads (key 'cld'; the forecast layer registers as 'fc')
    window._wxCvReg = window._wxCvReg || {};
    window._wxCvReg.cld = {cv: cv, m: {x1: x1, x2: x2, y1: y1, y2: y2}};
    cb(cv, {w: LW, e: LE, s: LS, n: LN});
  }
};

// ---- lightning: EUMETSAT MTG Lightning Imager (LI Accumulated Flash Area), shown with the ☁ at "now" ----
// Drawn as ⚡ SYMBOLS, not colour fields (owner 15.10: coloured spots looked like the rain radar's
// yellow/red/pink). The WMS gives one image per 5-minute step (a TIME range returns only its FIRST
// step - tested 15.10); each step is read ONCE into the 8x8-px cells of a grid where the satellite
// saw flashes (cell centroid + strength from EUMETSAT's pale-yellow (few) -> red (many) ramp), and a
// 30-minute window becomes a point list: per cell the newest age (0-25 min) + the strongest step.
// The newest step comes from the layer's own small capabilities document (~7 KB, CORS *, `default` =
// latest; ~10-15 min behind real time). Without the rain radar there is ONE window (the last 30 min);
// while the radar loops, one window per radar frame (the 30 min up to that frame, no later than the
// newest step) so the bolts move with the rain (owner 15.10). EUMETSAT Data Policy: LI derived
// products are "Core" data, free under CC BY 4.0 (Art. 4 + 5.1). Covers the wide data box like the
// other live layers. frames = the radar frame times (ms) or null -> S.fc[] (one FeatureCollection
// per window) + S.refs[] (each window's end).
window.wxLiState = {end: 0, cells: {}, err: false, any: false, refs: [], fc: []};
window.wxLiBuild = function(frames, cb){
  var S = window.wxLiState, LW = 14.5, LE = 37, LS = 35.5, LN = 49.5, W = 880, C = 8, STEP = 300000, N = 6, MAXW = 7;
  function mx(lon){ return lon * 20037508.343 / 180; }
  function my(lat){ return 6378137 * Math.log(Math.tan(Math.PI / 4 + lat * Math.PI / 360)); }
  var x1 = mx(LW), x2 = mx(LE), y1 = my(LS), y2 = my(LN), H = Math.round(W * (y2 - y1) / (x2 - x1)), NX = Math.ceil(W / C);
  var EUM = 'https://view.eumetsat.int/geoserver/', cv = null;
  function lonOf(px){ return LW + px / W * (LE - LW); }
  function latOf(py){ var ym = y2 - py / H * (y2 - y1); return (2 * Math.atan(Math.exp(ym / 6378137)) - Math.PI / 2) * 180 / Math.PI; }
  function analyse(im){ // one step -> {cell: [centroid x, centroid y, strength 0..1]}
    if (!cv){ cv = document.createElement('canvas'); cv.width = W; cv.height = H; }
    var ctx = cv.getContext('2d'); ctx.clearRect(0, 0, W, H); ctx.drawImage(im, 0, 0, W, H);
    var p = ctx.getImageData(0, 0, W, H).data, acc = {}, out = {}, x, y, i, k, f, a;
    for (y = 0; y < H; y++) for (x = 0; x < W; x++){ i = (y * W + x) * 4; if (!p[i + 3]) continue;
      f = (249 - p[i + 1]) / 221; f = f < 0 ? 0 : (f > 1 ? 1 : f); // EUMETSAT ramp: green 249 (few) .. 28 (many)
      k = ((y / C) | 0) * NX + ((x / C) | 0); a = acc[k] || (acc[k] = [0, 0, 0, 0]);
      a[0] += x; a[1] += y; a[2]++; if (f > a[3]) a[3] = f; }
    for (k in acc){ a = acc[k]; out[k] = [a[0] / a[2], a[1] / a[2], a[3]]; }
    return out;
  }
  function windowFc(ref){ // the bolts of the 30 min up to ref
    var best = {}, k, j, c, b;
    for (j = 0; j < N; j++){ c = S.cells[ref - j * STEP]; if (!c) continue; // newest step first: it sets the cell's age + place
      for (k in c){ b = best[k]; if (!b) best[k] = [c[k][0], c[k][1], c[k][2], j * 5]; else if (c[k][2] > b[2]) b[2] = c[k][2]; } }
    var feats = [];
    for (k in best){ b = best[k];
      feats.push({type: 'Feature', geometry: {type: 'Point', coordinates: [Math.round(lonOf(b[0] + 0.5) * 1000) / 1000, Math.round(latOf(b[1] + 0.5) * 1000) / 1000]},
        properties: {a: b[3], f: Math.round(b[2] * 100) / 100}}); }
    if (feats.length) S.any = true;
    return {type: 'FeatureCollection', features: feats};
  }
  function finish(refs){ S.any = false; S.fc = refs.map(windowFc); S.refs = refs; cb(true); }
  fetch(EUM + 'mtg_fd/li_afa/ows?service=WMS&version=1.3.0&request=GetCapabilities&_=' + Math.floor(Date.now() / STEP))
    .then(function(r){ return r.text(); })
    .then(function(x){
      var m = x.match(/<Dimension[^>]*name="time"[^>]*default="([^"]+)"/) || x.match(/<Dimension[^>]*name="time"[^>]*>[^<]*\/([^\/<]+)\/PT5M<\/Dimension>/);
      var end = m ? Date.parse(m[1]) : NaN;
      if (!(end > 0)) throw new Error('no time dimension');
      S.end = end; S.err = false;
      var refs = frames ? frames.slice(0, MAXW).map(function(t){ return Math.min(Math.floor(t / STEP) * STEP, end); }) : [end];
      var want = {}, k, t;
      refs.forEach(function(r){ for (k = 0; k < N; k++) want[r - k * STEP] = 1; });
      for (t in S.cells){ if (!want[t]) delete S.cells[t]; } // steps no window needs any more
      var todo = Object.keys(want).map(Number).filter(function(t){ return !S.cells[t]; }), left = todo.length;
      if (!left){ finish(refs); return; }
      todo.forEach(function(t){
        var im = new Image(); im.crossOrigin = 'anonymous';
        im.onload = function(){ try{ S.cells[t] = analyse(im); }catch(e){} if (--left === 0) finish(refs); };
        im.onerror = function(){ if (--left === 0) finish(refs); }; // a missing step only leaves a gap
        im.src = EUM + 'ows?service=WMS&version=1.1.1&request=GetMap&layers=mtg_fd:li_afa&styles=&srs=EPSG:3857&bbox=' +
          x1 + ',' + y1 + ',' + x2 + ',' + y2 + '&width=' + W + '&height=' + H +
          '&format=image/png&transparent=true&time=' + new Date(t).toISOString();
      });
    }).catch(function(){ S.err = true; cb(false); });
};

// ---- shared forecast-rain engine (Open-Meteo models over a 294-point grid) ----
// The radar shows only the PAST hour (free RainViewer), so the 🌦 button draws
// MODEL precipitation +1..+12 h ahead instead: one Open-Meteo request for a
// 0.35°x0.25° grid over Bulgaria + margin (verified live: all points in one
// call), asking THREE models at once (ICON-EU, GFS, ECMWF) and keeping the
// per-hour MAXIMUM — if any model expects rain, the pilot sees it. Values are
// bilinearly interpolated into smooth colour bands on a canvas. Numerical
// models still miss small local showers (seen live 2026-09-08: real radar rain
// over Thrace, all three models at 0.0) — hence the "model" caveat in the UI.
window.wxFcState = {data: null, at: 0, hour: 0, on: false}; // hour 0 = now; slider goes forward
// true while ANY forecast-grid consumer is on (rain-model, snow, or clouds in
// model mode). The grid fetch's self-retry uses this so a failed fetch keeps
// retrying for snow/clouds too - not only rain-model - and stops once every
// grid layer is off. Each layer's own draw callback still guards on its state,
// so a retry never draws a layer that was turned off meanwhile.
function wxGridWanted(){
  var S = window.wxFcState;
  if (S && S.on) return true;              // rain (model mode)
  if (window.wxSnowOn) return true;        // snow
  var cb = document.getElementById('wxcld');
  if (cb && cb.classList.contains('on') && S && S.hour > 0) return true; // clouds, slider ahead
  return false;
}
// Open-Meteo forecast data changes only per model run - ICON-EU every 3 h, GFS and
// ECMWF IFS 0.25 every 6 h (their docs, checked 04.10) - so model data is re-fetched
// every 3 h, not every 30 min: Open-Meteo counts EVERY location of a request against
// the visitor's own limits (10,000/day), and the grids are 483 + 546 points. Both
// grids still load together at once (owner: the wind must never wait); if Open-Meteo
// refuses one (600/min), its own retry fetches it again.
window.WX_MODEL_TTL = 10800000;
window.wxFcFetch = function(cb){
  var S = window.wxFcState;
  if (S.data && Date.now() - S.at < window.WX_MODEL_TTL){ cb(); return; } // model refresh: every 3 h (see above)
  if (!S.data){
    // the grid request is HEAVY in Open-Meteo's rate accounting (294 points x 3
    // models count as hundreds of calls), so a fresh page — e.g. right after a
    // 2D<->3D switch with 🌦 restored on — reuses the previous page's grid from
    // localStorage instead of refetching; a burst of switches stays within limits
    try{ var c = JSON.parse(localStorage.getItem('wxfcdata5'));
      if (c && c.data && c.data.s && c.data.c && c.data.w && Date.now() - c.at < window.WX_MODEL_TTL){ S.data = c.data; S.at = c.at; cb(); return; }
    }catch(e){} // wxfcdata5: cache holds rain (v) + snow (s) + clouds (c) + thunderstorms (w); only reuse if all present
  }
  function retry(){ // self-retry with doubling delay (12 s .. 5 min) — the grid is heavy, be polite
    clearTimeout(S.rt); S.rt = setTimeout(function(){ if (wxGridWanted()) window.wxFcFetch(cb); }, S.rms || 12000);
    S.rms = Math.min((S.rms || 12000) * 2, 300000); }
  // covers the WHOLE widest zoom-out (17-33.5 E / 35.5-49.5 N) so rain never cuts
  // inside the frame. Coarser step than wind (0.75°/0.7°) because this asks THREE
  // models at once — keeps the ~483-point x 3 load close to the old grid's.
  var lats = [], lons = [], la, lo;
  for (la = 35.5; la <= 49.501; la += 0.7)
    for (lo = 17.0; lo <= 33.501; lo += 0.75){ lats.push(la.toFixed(2)); lons.push(lo.toFixed(2)); }
  fetch('https://api.open-meteo.com/v1/forecast?latitude=' + lats.join(',') + '&longitude=' + lons.join(',') +
        '&hourly=precipitation,snowfall,cloud_cover,weather_code&forecast_hours=76&timezone=UTC&models=icon_eu,gfs_seamless,ecmwf_ifs025')
    .then(function(r){ return r.json(); })
    .then(function(d){
      if (!Array.isArray(d) || !d.length){ retry(); return; } // rate-limited (429): error JSON, not the array
      // one value per hour = the MAX across every returned <prefix>_* field (if any
      // model expects it, the pilot sees it). Rain (precipitation) AND snow (snowfall)
      // arrive in the SAME request, so the snow layer costs no extra API call.
      function fcMax(h, prefix){
        var ks = Object.keys(h).filter(function(k){ return k.indexOf(prefix) === 0; });
        var n = h.time.length, out = new Array(n), i, k, vv, m;
        for (i = 0; i < n; i++){ m = 0;
          for (k = 0; k < ks.length; k++){ vv = h[ks[k]][i]; if (vv && vv > m) m = vv; }
          out[i] = m; }
        return out;
      }
      // thunderstorms: per hour, HOW MANY of the models give a thunderstorm weather code (95-99);
      // the ☁ layer ahead hatches where at least one does (worst case, owner 15.10) - same request
      function fcCount(h, prefix, min){
        var ks = Object.keys(h).filter(function(k){ return k.indexOf(prefix) === 0; });
        var n = h.time.length, out = new Array(n), i, k, vv, m;
        for (i = 0; i < n; i++){ m = 0;
          for (k = 0; k < ks.length; k++){ vv = h[ks[k]][i]; if (vv != null && vv >= min) m++; }
          out[i] = m; }
        return out;
      }
      S.data = {t: d[0].hourly.time,
        v: d.map(function(x){ return fcMax(x.hourly, 'precipitation'); }),
        s: d.map(function(x){ return fcMax(x.hourly, 'snowfall'); }),
        c: d.map(function(x){ return fcMax(x.hourly, 'cloud_cover'); }),
        w: d.map(function(x){ return fcCount(x.hourly, 'weather_code', 95); })};
      S.at = Date.now(); S.rms = 12000;
      try{ localStorage.setItem('wxfcdata5', JSON.stringify({at: S.at, data: S.data})); }catch(e){}
      cb();
    }).catch(retry);
};
window.wxBaseIdx = function(t){ // index of the hour bucket containing "now" (t[0] is the current hour)
  var now = Date.now(), i, b = 0;
  for (i = 0; i < t.length; i++){ if (Date.parse(t[i] + ':00Z') <= now) b = i; else break; }
  return b;
};
window.wxFcIdx = function(){ // time-axis index for "now + selected hours" (hour 0 = now)
  var S = window.wxFcState; return Math.min(window.wxBaseIdx(S.data.t) + S.hour, S.data.t.length - 1);
};
window.wxFcLabel = function(){
  var el = document.getElementById('wxfclbl'); if (!el) return;
  var S = window.wxFcState, bg = !(typeof LANG !== 'undefined' && LANG === 'en');
  // hour 0 = now; otherwise current whole hour + the selected offset
  var d = new Date(Math.floor(Date.now() / 3600000) * 3600000 + S.hour * 3600000);
  var hhmm = ('0' + d.getHours()).slice(-2) + ':' + ('0' + d.getMinutes()).slice(-2);
  var rainOn = document.getElementById('wxrad') && document.getElementById('wxrad').classList.contains('on') && S.hour > 0; // "no rain (model)" note only for the model ahead, not the radar
  el.textContent = (S.hour === 0 ? (bg ? 'сега' : 'now') : '+' + S.hour + (bg ? ' ч · ' : ' h · ') + hhmm) +
    // the "no rain (model)" note is rain-only (0.15: a lone 0.1 mm point vanishes
    // in interpolation, so it still counts as dry)
    (rainOn && S.lastMax != null && S.lastMax < 0.15 ? (bg ? ' · без дъжд по модела' : ' · no rain (model)') : '');
};
window.wxFcDraw = function(){ // renders the selected hour; returns {cv, b} and registers for the 3D tile cutter
  var S = window.wxFcState;
  if (!S.data) return null;
  var LW = 17.0, LE = 33.5, LS = 35.5, LN = 49.5, NLO = 23, NLA = 21, W = 560;
  function mx(lon){ return lon * 20037508.343 / 180; }
  function my(lat){ return 6378137 * Math.log(Math.tan(Math.PI / 4 + lat * Math.PI / 360)); }
  var x1 = mx(LW), x2 = mx(LE), y1 = my(LS), y2 = my(LN), H = Math.round(W * (y2 - y1) / (x2 - x1));
  var hi = window.wxFcIdx();
  var mxv = 0, p, pv;
  for (p = 0; p < S.data.v.length; p++){ pv = S.data.v[p][hi]; if (pv && pv > mxv) mxv = pv; }
  S.lastMax = mxv; // wxFcLabel uses this to say "no rain (model)" on a dry hour
  var cv = document.createElement('canvas'); cv.width = W; cv.height = H;
  var ctx = cv.getContext('2d'), out = ctx.createImageData(W, H), od = out.data;
  // legend colours (same as the radar legend): light -> heavy
  var TH = [0.1, 0.5, 2, 6, 12], CO = [[136,221,238],[0,119,170],[255,238,0],[255,68,0],[255,119,255]];
  function val(r, c){ r = r < 0 ? 0 : (r > NLA - 1 ? NLA - 1 : r); c = c < 0 ? 0 : (c > NLO - 1 ? NLO - 1 : c);
    var v = S.data.v[r * NLO + c][hi]; return v == null ? 0 : v; }
  for (var py = 0; py < H; py++){
    var ym = y2 - (py + 0.5) / H * (y2 - y1);
    var lat = (2 * Math.atan(Math.exp(ym / 6378137)) - Math.PI / 2) * 180 / Math.PI;
    var fr = (lat - LS) / 0.7, r0 = Math.floor(fr), tr = fr - r0;
    for (var px = 0; px < W; px++){
      var lon = LW + (px + 0.5) / W * (LE - LW);
      var fc = (lon - LW) / 0.75, c0 = Math.floor(fc), tc = fc - c0;
      var v = (val(r0, c0) * (1 - tr) + val(r0 + 1, c0) * tr) * (1 - tc) +
              (val(r0, c0 + 1) * (1 - tr) + val(r0 + 1, c0 + 1) * tr) * tc;
      if (v < TH[0]) continue; // dry stays fully transparent
      var k = 0; while (k < TH.length - 1 && v >= TH[k + 1]) k++;
      var i4 = (py * W + px) * 4;
      od[i4] = CO[k][0]; od[i4 + 1] = CO[k][1]; od[i4 + 2] = CO[k][2]; od[i4 + 3] = 168;
    }
  }
  ctx.putImageData(out, 0, 0);
  window._wxCvReg = window._wxCvReg || {};
  window._wxCvReg.fc = {cv: cv, m: {x1: x1, x2: x2, y1: y1, y2: y2}};
  return {cv: cv, b: {w: LW, e: LE, s: LS, n: LN}};
};
// ---- thunderstorms ahead (☁ with the slider ahead) ----
// Where the three models (ICON-EU, GFS, ECMWF, the same grid request as rain/snow/clouds) give a
// thunderstorm weather code (95-99) at the selected hour, as ⚡ like the lightning "now" (owner
// 17.10): YELLOW where at least 2 of the 3 models give it, PALE where only one does - every storm
// any model gives is shown (the worst case, like rain and clouds). Model thunderstorms are
// diagnosed from instability: an area and an hour of risk, not lightning positions. The bolts sit
// on a 0.2° lattice over the model grid, each nudged by a fixed pseudo-random offset (up to 40 %
// of a step, the same on every draw) so they never line up in rows and columns (owner 17.10);
// bilinear at that point: a storm where >= 0.5 models, yellow where >= 1.5. MapLibre thins them
// when zoomed out (they never overlap).
window.wxStormPoints = function(){
  var S = window.wxFcState;
  if (!S.data || !S.data.w) return null;
  var LW = 17.0, LE = 33.5, LS = 35.5, LN = 49.5, NLO = 23, NLA = 21, D = 0.2;
  var NI = Math.floor((LN - LS) / D + 1e-6), NJ = Math.floor((LE - LW) / D + 1e-6);
  var hi = window.wxFcIdx(), mxv = 0, p, pv, feats = [];
  for (p = 0; p < S.data.w.length; p++){ pv = S.data.w[p][hi]; if (pv > mxv) mxv = pv; }
  S.lastStorm = mxv; // the note under the slider says "no thunderstorms" on a quiet hour
  function val(r, c){ r = r < 0 ? 0 : (r > NLA - 1 ? NLA - 1 : r); c = c < 0 ? 0 : (c > NLO - 1 ? NLO - 1 : c);
    return S.data.w[r * NLO + c][hi] || 0; }
  function jit(i, j, k){ // 0..1 from the lattice cell: the same for the same cell, every time
    var h = Math.imul(i + 1, 374761393) ^ Math.imul(j + 1, 668265263) ^ Math.imul(k, 1274126177);
    h = Math.imul(h ^ (h >>> 13), 1274126177); return ((h ^ (h >>> 16)) >>> 0) / 4294967296; }
  if (mxv > 0){
    for (var i = 0; i < NI; i++){
      for (var j = 0; j < NJ; j++){
        var lat = LS + (i + 0.5 + (jit(i, j, 1) - 0.5) * 0.8) * D, lon = LW + (j + 0.5 + (jit(i, j, 2) - 0.5) * 0.8) * D;
        var fr = (lat - LS) / 0.7, r0 = Math.floor(fr), tr = fr - r0;
        var fc = (lon - LW) / 0.75, c0 = Math.floor(fc), tc = fc - c0;
        var v = (val(r0, c0) * (1 - tr) + val(r0 + 1, c0) * tr) * (1 - tc) +
                (val(r0, c0 + 1) * (1 - tr) + val(r0 + 1, c0 + 1) * tr) * tc;
        if (v < 0.5) continue; // no model gives a thunderstorm here
        feats.push({type: 'Feature', geometry: {type: 'Point', coordinates: [Math.round(lon * 1000) / 1000, Math.round(lat * 1000) / 1000]},
          properties: {s: v >= 1.5 ? 2 : 1}}); // 2 = yellow (2-3 models), 1 = pale (one model)
      }
    }
  }
  return {type: 'FeatureCollection', features: feats};
};
window.wxSnowDraw = function(){ // selected hour's SNOW as a VIOLET ramp; registers 'snow' for the 3D tile cutter
  var S = window.wxFcState;
  if (!S.data || !S.data.s) return null;
  var LW = 17.0, LE = 33.5, LS = 35.5, LN = 49.5, NLO = 23, NLA = 21, W = 560;
  function mx(lon){ return lon * 20037508.343 / 180; }
  function my(lat){ return 6378137 * Math.log(Math.tan(Math.PI / 4 + lat * Math.PI / 360)); }
  var x1 = mx(LW), x2 = mx(LE), y1 = my(LS), y2 = my(LN), H = Math.round(W * (y2 - y1) / (x2 - x1));
  var hi = window.wxFcIdx();
  var mxv = 0, p, pv;
  for (p = 0; p < S.data.s.length; p++){ pv = S.data.s[p][hi]; if (pv && pv > mxv) mxv = pv; }
  // the mountain points' snowfall at the same hour (matched by time; none if not fetched)
  var MT = window.WX_MTN || [], mk = S.mtn ? S.mtn.t.indexOf(S.data.t[hi]) : -1, mv = [];
  for (p = 0; p < MT.length; p++){ pv = mk < 0 ? 0 : (S.mtn.s[p] ? S.mtn.s[p][mk] || 0 : 0); mv.push(pv); if (pv > mxv) mxv = pv; }
  S.lastSnow = mxv; // wxFcLabel uses this to say "no snow (model)" on a dry hour
  var cv = document.createElement('canvas'); cv.width = W; cv.height = H;
  var ctx = cv.getContext('2d'), out = ctx.createImageData(W, H), od = out.data, vals = new Float32Array(W * H);
  // snowfall cm/h -> VIOLET ramp (light -> heavy); deliberately distinct from the rain palette
  var TH = [0.1, 0.5, 1, 2, 4], CO = [[217,199,240],[183,154,230],[144,96,216],[106,47,184],[74,26,138]];
  function paint(ix, v){
    var k = 0; while (k < TH.length - 1 && v >= TH[k + 1]) k++;
    var i4 = ix * 4; od[i4] = CO[k][0]; od[i4 + 1] = CO[k][1]; od[i4 + 2] = CO[k][2]; od[i4 + 3] = 180; }
  function val(r, c){ r = r < 0 ? 0 : (r > NLA - 1 ? NLA - 1 : r); c = c < 0 ? 0 : (c > NLO - 1 ? NLO - 1 : c);
    var v = S.data.s[r * NLO + c][hi]; return v == null ? 0 : v; }
  for (var py = 0; py < H; py++){
    var ym = y2 - (py + 0.5) / H * (y2 - y1);
    var lat = (2 * Math.atan(Math.exp(ym / 6378137)) - Math.PI / 2) * 180 / Math.PI;
    var fr = (lat - LS) / 0.7, r0 = Math.floor(fr), tr = fr - r0;
    for (var px = 0; px < W; px++){
      var lon = LW + (px + 0.5) / W * (LE - LW);
      var fc = (lon - LW) / 0.75, c0 = Math.floor(fc), tc = fc - c0;
      var v = (val(r0, c0) * (1 - tr) + val(r0 + 1, c0) * tr) * (1 - tc) +
              (val(r0, c0 + 1) * (1 - tr) + val(r0 + 1, c0 + 1) * tr) * tc;
      vals[py * W + px] = v;
      if (v < TH[0]) continue; // no snow stays transparent
      paint(py * W + px, v);
    }
  }
  // each mountain point = a soft patch of MTN_KM radius: full value out to half the radius,
  // fading to 0 at the edge; it only ever RAISES what the grid shows there
  var MTN_KM = 12, ppm = W / (x2 - x1);
  for (p = 0; p < MT.length; p++){
    if (!(mv[p] >= TH[0])) continue;
    var cx = (mx(MT[p][1]) - x1) * ppm, cy = (y2 - my(MT[p][0])) * ppm;
    var rp = MTN_KM * 1000 / Math.cos(MT[p][0] * Math.PI / 180) * ppm;
    for (var yy = Math.max(0, Math.floor(cy - rp)); yy <= Math.min(H - 1, Math.ceil(cy + rp)); yy++)
      for (var xx = Math.max(0, Math.floor(cx - rp)); xx <= Math.min(W - 1, Math.ceil(cx + rp)); xx++){
        var d = Math.hypot(xx + 0.5 - cx, yy + 0.5 - cy) / rp; if (d >= 1) continue;
        var vb = mv[p] * (d <= 0.5 ? 1 : (1 - d) * 2), ix = yy * W + xx;
        if (vb >= TH[0] && vb > vals[ix]){ vals[ix] = vb; paint(ix, vb); }
      }
  }
  ctx.putImageData(out, 0, 0);
  window._wxCvReg = window._wxCvReg || {};
  window._wxCvReg.snow = {cv: cv, m: {x1: x1, x2: x2, y1: y1, y2: y2}};
  return {cv: cv, b: {w: LW, e: LE, s: LS, n: LN}};
};
// ---- forecast CLOUDS (Open-Meteo model %, drawn like the satellite clouds) ----
// The ☁ button shows the EUMETSAT satellite at hour 0 and these MODEL clouds when
// the slider moves ahead. Source = cloud_cover % (0-100) on the shared grid; it is
// coloured with the SAME grey-fringe / white-core mapping the satellite uses
// (wxCloudBuild), so a future hour whose model % matches now looks like now.
// Calibration (owner will tune live vs the satellite): below CLD_CUT% draw nothing
// (clear sky = transparent); from CLD_CUT% to 100% the opacity ramps and the colour
// goes grey -> white. CLD_GAMMA bends that ramp (>1 = less mid veil, thinner area).
window.wxCloudFcDraw = function(){
  var S = window.wxFcState;
  if (!S.data || !S.data.c) return null;
  var LW = 17.0, LE = 33.5, LS = 35.5, LN = 49.5, NLO = 23, NLA = 21, W = 560;
  var CLD_CUT = 38, CLD_GAMMA = 1.4, CLD_BLUR = 6; // <-- calibration knobs (BLUR px = soft edges, like the satellite)
  function mx(lon){ return lon * 20037508.343 / 180; }
  function my(lat){ return 6378137 * Math.log(Math.tan(Math.PI / 4 + lat * Math.PI / 360)); }
  var x1 = mx(LW), x2 = mx(LE), y1 = my(LS), y2 = my(LN), H = Math.round(W * (y2 - y1) / (x2 - x1));
  var hi = window.wxFcIdx(), n = W * H, A = new Float32Array(n);
  var cv = document.createElement('canvas'); cv.width = W; cv.height = H;
  var ctx = cv.getContext('2d'), out = ctx.createImageData(W, H), od = out.data;
  function val(r, c){ r = r < 0 ? 0 : (r > NLA - 1 ? NLA - 1 : r); c = c < 0 ? 0 : (c > NLO - 1 ? NLO - 1 : c);
    var v = S.data.c[r * NLO + c][hi]; return v == null ? 0 : v; }
  // pass 1: bilinear cloud-cover % onto the pixel plane (raw 0..100, no cutoff yet)
  for (var py = 0; py < H; py++){
    var ym = y2 - (py + 0.5) / H * (y2 - y1);
    var lat = (2 * Math.atan(Math.exp(ym / 6378137)) - Math.PI / 2) * 180 / Math.PI;
    var fr = (lat - LS) / 0.7, r0 = Math.floor(fr), tr = fr - r0;
    for (var px = 0; px < W; px++){
      var lon = LW + (px + 0.5) / W * (LE - LW);
      var fc = (lon - LW) / 0.75, c0 = Math.floor(fc), tc = fc - c0;
      A[py * W + px] = (val(r0, c0) * (1 - tr) + val(r0 + 1, c0) * tr) * (1 - tc) +
                       (val(r0, c0 + 1) * (1 - tr) + val(r0 + 1, c0 + 1) * tr) * tc;
    }
  }
  // pass 2: 2-pass box blur of the % field BEFORE the cutoff -> soft internal transitions and
  // isolated blobs averaged away, WITHOUT widening the footprint (the 35% edge stays put)
  if (CLD_BLUR > 0){
    var rb = CLD_BLUR, tmp = new Float32Array(n), pp = new Float32Array((W > H ? W : H) + 1), bx, by, brow, blo, bhi, bk;
    for (bk = 0; bk < 2; bk++){
      for (by = 0; by < H; by++){ brow = by * W;
        for (bx = 0; bx < W; bx++) pp[bx + 1] = pp[bx] + A[brow + bx];
        for (bx = 0; bx < W; bx++){ blo = bx - rb < 0 ? 0 : bx - rb; bhi = bx + rb >= W ? W - 1 : bx + rb;
          tmp[brow + bx] = (pp[bhi + 1] - pp[blo]) / (bhi - blo + 1); } }
      for (bx = 0; bx < W; bx++){
        for (by = 0; by < H; by++) pp[by + 1] = pp[by] + tmp[by * W + bx];
        for (by = 0; by < H; by++){ blo = by - rb < 0 ? 0 : by - rb; bhi = by + rb >= H ? H - 1 : by + rb;
          A[by * W + bx] = (pp[bhi + 1] - pp[blo]) / (bhi - blo + 1); } }
    }
  }
  // pass 3: cutoff + gamma on the (blurred) %, then grey fringes (125) -> white cores (255) + alpha
  for (var i = 0; i < n; i++){
    var a = (A[i] - CLD_CUT) / (100 - CLD_CUT);
    if (a <= 0) continue; // below the cutoff stays fully transparent (clear sky)
    if (a > 1) a = 1; if (CLD_GAMMA !== 1) a = Math.pow(a, CLD_GAMMA);
    var tt = (a - 0.62) / 0.38, gg = Math.round(125 + 130 * (tt < 0 ? 0 : (tt > 1 ? 1 : tt))), i4 = i * 4;
    od[i4] = od[i4 + 1] = od[i4 + 2] = gg; od[i4 + 3] = Math.round(a * 255);
  }
  ctx.putImageData(out, 0, 0);
  window._wxCvReg = window._wxCvReg || {};
  window._wxCvReg.cldfc = {cv: cv, m: {x1: x1, x2: x2, y1: y1, y2: y2}};
  return {cv: cv, b: {w: LW, e: LE, s: LS, n: LN}};
};

// ---- shared wind engine (Open-Meteo grid u/v + animated particles) ----
// Same 294-point grid as the rain forecast, but asking for wind at 10 m AND
// 120 m. Speed+direction become u/v components; the VECTOR is bilinearly
// interpolated (u and v separately). The particle layer advects light streaks
// along the field, Windy-style: stronger wind = faster, longer streaks. The
// grid is cached 30 min in localStorage and self-retries on a rate-limited
// answer (same discipline as the rain grid). Wind is drawn as neutral (white
// with a faint dark under-stroke) so it reads on both the light map and the
// dark satellite — no colour coding (owner's choice).
window.wxWindState = {data: null, at: 0, h: 10, on: false, rt: null};
window.wxWindFetch = function(cb){
  var S = window.wxWindState;
  if (S.data && Date.now() - S.at < window.WX_MODEL_TTL){ cb(); return; }
  if (!S.data){
    try{ var c = JSON.parse(localStorage.getItem('wxwinddata4'));
      if (c && Date.now() - c.at < window.WX_MODEL_TTL && c.data && c.data.u10 && c.data.u10.length === WXW_NLO * WXW_NLA){
        S.data = c.data; S.at = c.at; cb(); return; } // only reuse a cache that matches the current grid shape
    }catch(e){}
  }
  function retry(){ clearTimeout(S.rt); S.rt = setTimeout(function(){ if (S.on) window.wxWindFetch(cb); }, 12000); }
  // covers the WHOLE widest zoom-out (17-33.5 E / 35.5-49.5 N: Bulgaria out to the
  // screen edge on desktop AND phone) so the flow never cuts inside the frame. The
  // step is coarser than before (0.66°x0.7°) so it stays ONE request (~546 points;
  // Open-Meteo rejects a too-long URL past ~800 points) and the load stays modest.
  var lats = [], lons = [], la, lo;
  for (la = 35.5; la <= 49.501; la += 0.7)
    for (lo = 17.0; lo <= 33.501; lo += 0.66){ lats.push(la.toFixed(2)); lons.push(lo.toFixed(2)); }
  fetch('https://api.open-meteo.com/v1/forecast?latitude=' + lats.join(',') + '&longitude=' + lons.join(',') +
        '&hourly=wind_speed_10m,wind_direction_10m,wind_speed_120m,wind_direction_120m' +
        '&forecast_hours=76&wind_speed_unit=ms&timezone=UTC')
    .then(function(r){ return r.json(); })
    .then(function(d){
      if (!Array.isArray(d) || !d.length){ retry(); return; }
      function uv(pt, spdKey, dirKey){
        var h = pt.hourly, sp = h[spdKey], dr = h[dirKey], n = sp.length, u = new Array(n), v = new Array(n), i, rad;
        for (i = 0; i < n; i++){ rad = (dr[i] || 0) * Math.PI / 180; // met dir = FROM; vector points opposite
          u[i] = -(sp[i] || 0) * Math.sin(rad); v[i] = -(sp[i] || 0) * Math.cos(rad); }
        return {u: u, v: v};
      }
      S.data = {t: d[0].hourly.time,
        u10: d.map(function(p){ return uv(p, 'wind_speed_10m', 'wind_direction_10m'); }),
        u120: d.map(function(p){ return uv(p, 'wind_speed_120m', 'wind_direction_120m'); })};
      S.at = Date.now();
      try{ localStorage.setItem('wxwinddata4', JSON.stringify({at: S.at, data: S.data})); }catch(e){}
      cb();
    }).catch(retry);
};
window.wxWindIdx = function(){ var S = window.wxWindState; // hour 0 = now, same base as the rain layer
  return Math.min(window.wxBaseIdx(S.data.t) + (window.wxFcState ? window.wxFcState.hour : 0), S.data.t.length - 1);
};
var WXW_LW = 17.0, WXW_LS = 35.5, WXW_DLO = 0.66, WXW_DLA = 0.7, WXW_NLO = 26, WXW_NLA = 21;
window.wxWindSample = function(lon, lat){
  var S = window.wxWindState; if (!S.data) return null;
  var set = (S.h === 120) ? S.data.u120 : S.data.u10, hi = window.wxWindIdx();
  if (!set || set.length !== WXW_NLO * WXW_NLA) return null; // guard: stale/mismatched grid never crashes
  var fr = (lat - WXW_LS) / WXW_DLA, r0 = Math.floor(fr), tr = fr - r0;
  var fc = (lon - WXW_LW) / WXW_DLO, c0 = Math.floor(fc), tc = fc - c0;
  if (r0 < 0 || r0 > WXW_NLA - 1 || c0 < 0 || c0 > WXW_NLO - 1) return null;
  function g(r, c, comp){ r = r < 0 ? 0 : (r > WXW_NLA - 1 ? WXW_NLA - 1 : r); c = c < 0 ? 0 : (c > WXW_NLO - 1 ? WXW_NLO - 1 : c);
    return set[r * WXW_NLO + c][comp][hi]; }
  function bil(comp){ return (g(r0, c0, comp) * (1 - tr) + g(r0 + 1, c0, comp) * tr) * (1 - tc) +
                             (g(r0, c0 + 1, comp) * (1 - tr) + g(r0 + 1, c0 + 1, comp) * tr) * tc; }
  var u = bil('u'), v = bil('v');
  return {u: u, v: v, spd: Math.sqrt(u * u + v * v)};
};
// generic particle engine: cfg = {canvas, project(lon,lat)->{x,y}, unproject(x,y)->{lon,lat}, bounds()->{w,s,e,n}}.
// One implementation drives both Leaflet and MapLibre. Windy-style flowing particles:
// thin points that drift with the wind leaving short FADING trails (the trail IS the
// animation). Crucially the drift is computed in SCREEN space (px per m/s per frame),
// so speed and density stay constant at every zoom (an earlier degree-based advance
// sped up and thickened when zoomed in). Cadence is capped at ~25 fps like the
// open-source "earth" project Windy forked. The streak is a dark under-line + a white
// over-line so it reads on both the light 2D map and the dark 3D satellite.
// --- tunables --- N=density, SPEED=px per m/s per frame, FADE=trail length (higher=longer),
// FRAME_MS=cadence, *A=opacity (lower=lighter), *W=width.
// DENS = CSS px² per particle (higher = sparser); the count scales with the screen
// so density is the same on a phone and a laptop. SPEED = px per m/s per frame.
window.wxWindCfg = {DENS: 1700, SPEED: 0.42, FADE: 0.90, MAXAGE: 100, FRAME_MS: 40};
window.wxWindEngine = function(cfg){
  var cv = cfg.canvas, ctx = cv.getContext('2d'), raf = null, parts = [], running = true;
  var C = window.wxWindCfg;
  function reseed(p){
    // seed uniformly in SCREEN space (unproject runs only at reseed ~ N/MAXAGE per
    // frame, so it's cheap) → even density across the screen even under 3D tilt, where
    // geo-uniform seeding piled up at the far horizon and left the foreground empty
    var D = dims(), ll = cfg.unproject ? cfg.unproject(Math.random() * D.w, Math.random() * D.h) : null;
    if (ll){ p.lon = ll.lon; p.lat = ll.lat; }
    else { var b = cfg.bounds(); p.lon = b.w + Math.random() * (b.e - b.w); p.lat = b.s + Math.random() * (b.n - b.s); }
    p.age = Math.floor(Math.random() * C.MAXAGE); p.px = null; }
  var N0 = Math.max(200, Math.round(dims().w * dims().h / C.DENS)); // particle count scales with the screen area
  for (var i0 = 0; i0 < N0; i0++){ var p0 = {}; reseed(p0); parts.push(p0); }
  var lastT = 0, moving = false;
  // palette follows the BASEMAP brightness, not the map type: dark streaks on a light
  // basemap, white streaks + a dark halo on a dark basemap/satellite. cfg.darkBg (bool
  // or function) chooses; a future dark theme/basemap just flips it and wind stays visible.
  var LIGHTBG = {uW: 1.8, uA: 0.55, oA: 0}, DARKBG = {uW: 2.4, uA: 0.35, oW: 1.1, oA: 0.85};
  function pal(){ return (typeof cfg.darkBg === 'function' ? cfg.darkBg() : cfg.darkBg) ? DARKBG : LIGHTBG; }
  function dims(){ var d = cv._dpr || 1; return {w: cv.width / d, h: cv.height / d}; } // CSS px (ctx is DPR-scaled)
  // One wind step on the map. (ax,ay)/(bx,by) = screen px per degree east/north at the
  // point (the local Jacobian). The flow direction is the wind's OWN geographic direction
  // as the map shows it there (u east, v north, projected), so it turns with a rotated
  // map and follows a 3D tilt (owner 11.10: it used to stay fixed to the screen);
  // the speed stays constant on screen per m/s. Returns the geographic step + the
  // screen unit direction (the short dashes drawn while the map moves), or null.
  function windStep(s, lat, ax, ay, bx, by, k){
    var gx = s.u / Math.max(0.2, Math.cos(lat * Math.PI / 180)), gy = s.v; // m/s -> degrees east : north
    var sx = ax * gx + bx * gy, sy = ay * gx + by * gy, sl = Math.sqrt(sx * sx + sy * sy), det = ax * by - bx * ay;
    if (!sl || Math.abs(det) < 1e-4) return null;
    var spd = Math.sqrt(s.u * s.u + s.v * s.v) * C.SPEED * k, vx = sx / sl * spd, vy = sy / sl * spd;
    return {dlon: (by * vx - bx * vy) / det, dlat: (-ay * vx + ax * vy) / det, ux: sx / sl, uy: sy / sl};
  }
  function strokeSegs(segs, P){ var k; ctx.lineCap = 'round';
    ctx.beginPath(); for (k = 0; k < segs.length; k++){ ctx.moveTo(segs[k][0], segs[k][1]); ctx.lineTo(segs[k][2], segs[k][3]); }
    ctx.lineWidth = P.uW; ctx.strokeStyle = 'rgba(45,55,75,' + P.uA + ')'; ctx.stroke();
    if (P.oA > 0){ ctx.beginPath(); for (k = 0; k < segs.length; k++){ ctx.moveTo(segs[k][0], segs[k][1]); ctx.lineTo(segs[k][2], segs[k][3]); }
      ctx.lineWidth = P.oW; ctx.strokeStyle = 'rgba(255,255,255,' + P.oA + ')'; ctx.stroke(); } }
  function frame(now){
    if (!running) return;
    raf = requestAnimationFrame(frame);
    if (!moving && now && now - lastT < C.FRAME_MS) return; // throttle to ~25 fps only when idle; full rate while moving so it tracks the map
    // advance by ELAPSED time, not per frame, so flow speed is the same at 25/60/120 fps
    // (that is why it raced while dragging and on high-refresh phones)
    var sc = (now && lastT) ? Math.min(3, (now - lastT) / C.FRAME_MS) : 1;
    lastT = now || 0;
    var D = dims(), w = D.w, h = D.h, b = cfg.bounds(), segs = [], i, p, s, st, pt, ptE, ptN, dx, dy, P = pal();
    if (moving){
      // panning/zooming: keep the flow going AND reproject every frame so the dashes
      // ride with the map (no smear, no freeze). The centre's east/north vectors are
      // enough during a drag.
      ctx.clearRect(0, 0, w, h);
      var mcx = (b.w + b.e) / 2, mcy = (b.s + b.n) / 2, mc = cfg.project(mcx, mcy),
          meE = cfg.project(mcx + 0.1, mcy), meN = cfg.project(mcx, mcy + 0.1);
      var jE = (mc && meE) ? [(meE.x - mc.x) / 0.1, (meE.y - mc.y) / 0.1] : [1, 0],
          jN = (mc && meN) ? [(meN.x - mc.x) / 0.1, (meN.y - mc.y) / 0.1] : [0, -1];
      for (i = 0; i < parts.length; i++){ p = parts[i];
        if (p.lon < b.w || p.lon > b.e || p.lat < b.s || p.lat > b.n){ reseed(p); }
        pt = cfg.project(p.lon, p.lat);
        if (!pt || pt.x < -20 || pt.y < -20 || pt.x > w + 20 || pt.y > h + 20) continue;
        s = window.wxWindSample(p.lon, p.lat); if (!s) continue;
        st = windStep(s, p.lat, jE[0], jE[1], jN[0], jN[1], sc); if (!st) continue;
        segs.push([pt.x, pt.y, pt.x + st.ux * 9, pt.y + st.uy * 9]);
        p.lon += Math.max(-0.05, Math.min(0.05, st.dlon));
        p.lat += Math.max(-0.05, Math.min(0.05, st.dlat));
      }
      strokeSegs(segs, P); if (cfg.afterDraw) cfg.afterDraw(ctx); return;
    }
    ctx.globalCompositeOperation = 'destination-in'; // idle: fade existing trails, keep the canvas transparent
    ctx.fillStyle = 'rgba(0,0,0,' + C.FADE + ')'; ctx.fillRect(0, 0, w, h);
    ctx.globalCompositeOperation = 'source-over';
    for (i = 0; i < parts.length; i++){ p = parts[i];
      if (p.age++ > C.MAXAGE || p.lon < b.w || p.lon > b.e || p.lat < b.s || p.lat > b.n){ reseed(p); }
      pt = cfg.project(p.lon, p.lat);
      if (!pt || pt.x < -40 || pt.y < -40 || pt.x > w + 40 || pt.y > h + 40){ reseed(p); continue; }
      s = window.wxWindSample(p.lon, p.lat);
      if (!s){ p.px = null; continue; }
      if (p.px != null){ dx = pt.x - p.px; dy = pt.y - p.py;
        if (dx * dx + dy * dy < 3600) segs.push([p.px, p.py, pt.x, pt.y]); }
      p.px = pt.x; p.py = pt.y;
      // per-particle local px/deg → constant SCREEN speed everywhere, even under 3D tilt
      // (a single centre scale made far-side/horizon particles "fly")
      // full local Jacobian (east + north screen vectors) → invert it to step the
      // particle by the wind's true SCREEN velocity; separate x/y scaling bent the
      // streamlines under 3D tilt/rotation (they plunged on one side of the screen)
      ptE = cfg.project(p.lon + 0.02, p.lat); ptN = cfg.project(p.lon, p.lat + 0.02);
      if (ptE && ptN){
        st = windStep(s, p.lat, (ptE.x - pt.x) / 0.02, (ptE.y - pt.y) / 0.02, (ptN.x - pt.x) / 0.02, (ptN.y - pt.y) / 0.02, sc);
        // cap the per-frame step so a near-horizon degenerate scale can't make it "fly"
        if (st){ p.lon += Math.max(-0.05, Math.min(0.05, st.dlon)); p.lat += Math.max(-0.05, Math.min(0.05, st.dlat)); }
      }
    }
    strokeSegs(segs, P);
    if (cfg.afterDraw) cfg.afterDraw(ctx); // e.g. 2D: punch a clear hole so open popups show above the wind
  }
  raf = requestAnimationFrame(frame);
  return {
    stop: function(){ running = false; if (raf) cancelAnimationFrame(raf); var D = dims(); ctx.clearRect(0, 0, D.w, D.h); },
    setMoving: function(m){ moving = m; if (!m){ for (var j = 0; j < parts.length; j++) parts[j].px = null; } }
  };
};

// ---- shared helpers for the live-aircraft layer ----
// The data comes through the project's own tiny caching relay (Deno Deploy,
// tools/adsb_relay_deno.ts) which reads the community aggregators adsb.fi and
// adsb.lol — both fed by the owner's receiver. The relay serves everyone the
// same 10-s answer, so the aggregators see ONE polite client regardless of
// visitor count. We poll it every 7 s (just above the relay's 6-s cache, so nearly
// every poll brings a fresh frame), only while the layer is on and the tab
// is visible.
window.wxPlnUrl = 'https://full-narwhal-4777.martinovem.deno.net/';
window.wxGjUrl = 'https://full-narwhal-4777.martinovem.deno.net/gpsown'; // OUR OWN GPS-interference cells (from the relayed ADS-B aircraft)
// calendar state: win 12|24, day ''=live else YYYY-MM-DD, days=available.
// First-ever view defaults to YESTERDAY (a full finished day looks complete at
// once; a stale/missing day falls back to live in gjFetch). A saved choice
// (incl. '' = live) overrides this in WX_RESTORE_JS.
window.wxGjWin = 12; window.wxGjDay = new Date(Date.now() - 86400000).toISOString().slice(0, 10); window.wxGjDays = []; window.wxGjAuto = true;
// Six silhouettes (all drawn pointing up in a -16..16 viewBox), Flightradar-style:
// amber fill, dark outline, engines drawn as nacelles, soft drop shadow. Picked by
// type code + ADS-B emitter category: airliner with 2 wing jets (default), heavy
// with 4 (A5), business/regional jet with 2 REAR pods (A2), twin turboprop with
// wing props (ATR/Dash-8 &c by type code), small single prop with a nose propeller
// (A1), helicopter (A7 or "helicopter" in the name).
var WXPLN_SH = '<filter id="wxsh" x="-30%" y="-30%" width="160%" height="160%">' +
  '<feDropShadow dx="0.5" dy="1.3" stdDeviation="0.8" flood-opacity="0.45"/></filter><g filter="url(#wxsh)">';
window.wxPlnKinds = {
  jet: {w: 30, svg: WXPLN_SH + '<g fill="#fcc02e" stroke="#33425b" stroke-width="1.1" stroke-linejoin="round">' +
    '<rect x="4.7" y="-3.4" width="2.4" height="5" rx="1.2"/><rect x="-7.1" y="-3.4" width="2.4" height="5" rx="1.2"/>' +
    '<path d="M0,-14 C1.4,-14 2.1,-12.3 2.1,-10.2 L2.1,-4.4 L14.2,2.4 L14.2,5 L2.1,1.6 L1.9,7 L6.2,9.8 L6.2,11.7 L0.6,10.4 C0.5,11.2 0.3,11.6 0,11.6 C-0.3,11.6 -0.5,11.2 -0.6,10.4 L-6.2,11.7 L-6.2,9.8 L-1.9,7 L-2.1,1.6 L-14.2,5 L-14.2,2.4 L-2.1,-4.4 L-2.1,-10.2 C-2.1,-12.3 -1.4,-14 0,-14 Z"/></g></g>'},
  hvy: {w: 38, svg: WXPLN_SH + '<g fill="#fcc02e" stroke="#33425b" stroke-width="1.1" stroke-linejoin="round">' +
    '<rect x="4.4" y="-4" width="2.4" height="4.8" rx="1.2"/><rect x="-6.8" y="-4" width="2.4" height="4.8" rx="1.2"/>' +
    '<rect x="8.6" y="-2" width="2.4" height="4.6" rx="1.2"/><rect x="-11" y="-2" width="2.4" height="4.6" rx="1.2"/>' +
    '<path d="M0,-14.6 C1.6,-14.6 2.5,-12.8 2.5,-10.4 L2.5,-4.8 L15,3.2 L15,6 L2.5,2.4 L2.2,7.6 L7,10.6 L7,12.6 L0.7,11.2 C0.6,12 0.3,12.4 0,12.4 C-0.3,12.4 -0.6,12 -0.7,11.2 L-7,12.6 L-7,10.6 L-2.2,7.6 L-2.5,2.4 L-15,6 L-15,3.2 L-2.5,-4.8 L-2.5,-10.4 C-2.5,-12.8 -1.6,-14.6 0,-14.6 Z"/></g></g>'},
  bjt: {w: 27, svg: WXPLN_SH + '<g fill="#fcc02e" stroke="#33425b" stroke-width="1.1" stroke-linejoin="round">' +
    '<rect x="1.9" y="3.4" width="2.2" height="4.4" rx="1.1"/><rect x="-4.1" y="3.4" width="2.2" height="4.4" rx="1.1"/>' +
    '<path d="M0,-13 C1.1,-13 1.7,-11.7 1.7,-9.9 L1.7,-3.8 L12.5,2.8 L12.5,5.2 L1.7,2 L1.7,7.2 L5.6,9.4 L5.6,11.2 L0.5,10.1 C0.4,10.8 0.2,11.1 0,11.1 C-0.2,11.1 -0.4,10.8 -0.5,10.1 L-5.6,11.2 L-5.6,9.4 L-1.7,7.2 L-1.7,2 L-12.5,5.2 L-12.5,2.8 L-1.7,-3.8 L-1.7,-9.9 C-1.7,-11.7 -1.1,-13 0,-13 Z"/></g></g>'},
  tpr: {w: 28, svg: WXPLN_SH + '<g fill="#fcc02e" stroke="#33425b" stroke-width="1.1" stroke-linejoin="round">' +
    '<path d="M4.4,-5.4 L7.8,-5.4 M-4.4,-5.4 L-7.8,-5.4" stroke-width="1.4" stroke-linecap="round"/>' +
    '<rect x="4.8" y="-5" width="2.6" height="5" rx="1.2"/><rect x="-7.4" y="-5" width="2.6" height="5" rx="1.2"/>' +
    '<path d="M0,-13 C1.2,-13 1.9,-11.5 1.9,-9.6 L1.9,-3.4 L13.8,-2.6 L13.8,0.2 L1.9,0.2 L1.7,6.6 L5.6,8.8 L5.6,10.6 L0.5,9.6 C0.4,10.4 0.2,10.8 0,10.8 C-0.2,10.8 -0.4,10.4 -0.5,9.6 L-5.6,10.6 L-5.6,8.8 L-1.7,6.6 L-1.9,0.2 L-13.8,0.2 L-13.8,-2.6 L-1.9,-3.4 L-1.9,-9.6 C-1.9,-11.5 -1.2,-13 0,-13 Z"/></g></g>'},
  prp: {w: 25, svg: WXPLN_SH + '<g fill="#fcc02e" stroke="#33425b" stroke-width="1.1" stroke-linejoin="round">' +
    '<path d="M-2.9,-11.4 L2.9,-11.4" stroke-width="1.6" stroke-linecap="round"/>' +
    '<path d="M0,-10.8 C1,-10.8 1.6,-9.8 1.6,-8.4 L1.6,-5 L13,-4 L13,-0.9 L1.6,-1 L1.4,5.4 L5,7.2 L5,9.2 L0,8.4 L-5,9.2 L-5,7.2 L-1.4,5.4 L-1.6,-1 L-13,-0.9 L-13,-4 L-1.6,-5 L-1.6,-8.4 C-1.6,-9.8 -1,-10.8 0,-10.8 Z"/></g></g>'},
  hel: {w: 28, svg: WXPLN_SH + '<path d="M0,-7.2 C3,-7.2 4.6,-4.6 4.6,-1.9 C4.6,0.9 3,3 0.9,3.3 L0.7,8.6 L3.4,9.4 L3.4,11 L-3.4,11 L-3.4,9.4 L-0.7,8.6 L-0.9,3.3 C-3,3 -4.6,0.9 -4.6,-1.9 C-4.6,-4.6 -3,-7.2 0,-7.2 Z" fill="#fcc02e" stroke="#33425b" stroke-width="1.1" stroke-linejoin="round"/>' +
    '<path d="M-7.5,-9.5 L7.5,5.5 M7.5,-9.5 L-7.5,5.5" stroke="#33425b" stroke-width="1.6" fill="none" stroke-linecap="round"/>' +
    '<circle cx="0" cy="-2" r="1.4" fill="#33425b"/></g>'}
};
// Business jets by ICAO type designator. Some broadcast a wrong emitter category (a
// Citation 650 seen saying A1 "light" -> drawn as a small prop), so the TYPE decides
// before the category. A hand-written list of biz-jet designators, like the turboprop
// one below - no aircraft-type database is copied. Each code was checked (2026-09-24)
// against at least two independent designator lists; airliner-based corporate jets
// (ACJ, BBJ, Lineage, Challenger 850 = CRJ2...) share airliner codes and stay out.
var WX_BJT = {};
('C500 C501 C510 C525 C25A C25B C25C C25M C550 C551 C55B C560 C56X C650 C680 C68A C700 C750 ' +  // Cessna Citation
 'LJ23 LJ24 LJ25 LJ28 LJ31 LJ35 LJ40 LJ45 LJ55 LJ60 LJ70 LJ75 ' +                                 // Learjet
 'CL30 CL35 CL60 GLEX GL5T GL7T ' +                                                               // Bombardier Challenger / Global
 'FA10 FA20 FA50 FA6X FA7X FA8X F900 F2TH ' +                                                     // Dassault Falcon
 'ASTR G150 GALX G250 G280 GLF2 GLF3 GLF4 GLF5 GLF6 GA3C GA4C GA5C GA6C GA7C GA8C WW23 WW24 JCOM ' + // Gulfstream / IAI
 'H25A H25B H25C HA4T BE40 BE4W PRM1 ' +                                                          // Hawker / Beechjet / Nextant / Premier
 'E50P E55P E545 E550 E35L HDJT PC24 SF50 EA50 SJ30 MU30 SBR1 SBR2 L29A L29B HF20 S601')          // Embraer, HondaJet, PC-24, Vision Jet, Eclipse, others
  .split(' ').forEach(function(c){ WX_BJT[c] = 1; });
window.wxPlnKind = function(a){
  if (a.category === 'A7' || /helicopter/i.test(a.desc || '')) return 'hel';
  // twin turboprops carry wing props, not a nose one: match the common type codes
  // (ATR, Dash 8, Saab, Fokker 50, Do328, Jetstream, Brasilia, Beech 1900, Metro)
  if (/^(AT4|AT7|DH8|SF3|SB2|F50|D32|JS3|JS4|E12|B19|SW[34])/.test((a.t || '').toUpperCase()) ||
      /ATR[- ]?\d/i.test(a.desc || '')) return 'tpr';
  if (WX_BJT[(a.t || '').toUpperCase()]) return 'bjt'; // known biz-jet type beats a wrong category
  if (a.category === 'A2') return 'bjt'; // mid-weight jets (biz jets, ERJ/CRJ) carry rear pods
  if (a.category === 'A1') return 'prp'; // light singles
  if (a.category === 'A5') return 'hvy';
  return 'jet';
};
window.wxPlaneInfo = function(a){
  var bg = !(typeof LANG !== 'undefined' && LANG === 'en');
  function esc(s){ return (s + '').replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
  var name = (a.flight || '').trim() || a.r || a.hex || '';
  var h = '<b>' + esc(name) + '</b>';
  if (a.r && name !== a.r) h += ' · ' + esc(a.r); // registration next to the callsign
  if (a.desc || a.t) h += '<br>' + esc(a.desc || '') + (a.t ? (a.desc ? ' (' + esc(a.t) + ')' : esc(a.t)) : '');
  if (typeof a.alt_baro === 'number'){
    h += '<br>' + (bg ? 'височина: ' : 'altitude: ') + Math.round(a.alt_baro * 0.3048) + ' m (' + a.alt_baro + ' ft)';
    var vs = (typeof a.baro_rate === 'number') ? a.baro_rate * 0.00508 : 0; // ft/min -> m/s
    if (Math.abs(vs) >= 0.5) h += ' · ' + (vs > 0 ? '↑' : '↓') + Math.abs(vs).toFixed(1) + (bg ? ' м/с' : ' m/s');
  }
  if (typeof a.gs === 'number') h += '<br>' + (bg ? 'скорост: ' : 'speed: ') + Math.round(a.gs * 1.852) + ' km/h' +
    (a.track != null ? ' · ' + (bg ? 'курс: ' : 'track: ') + Math.round(a.track) + '°' : '');
  if (typeof a.nic === 'number'){ // GPS integrity straight from ADS-B (what gpsjam maps are built from)
    var q = a.nic >= 7 ? (bg ? 'добър' : 'good') : (a.nic === 0 ? (bg ? 'слаб' : 'poor') : (bg ? 'среден' : 'fair'));
    h += '<br>GPS: NIC ' + a.nic + (typeof a.nac_p === 'number' ? ' · NACp ' + a.nac_p : '') + ' (' + q + ')';
  }
  return h;
};

// ---- OGN / FLARM low-level traffic: shared defs used by both maps ----
// Live gliders, paragliders, light aircraft & helicopters from the Open Glider
// Network (FLARM/OGN/FANET/SafeSky/ADS-L). Fetched straight in the browser from
// live.glidernet.org — HTTPS + CORS-open, one fixed all-Bulgaria box. Pilots who
// opted out (no-track/stealth) are already dropped AT SOURCE, so what arrives is
// safe to show. Marker column order + type enum verified from their own ogn.js.
// Licence ODbL (attributed on the map).
// box covers the whole widest zoom-out (lat 36-49 N, lon 17-33.5 E: Bulgaria +
// neighbours out to the edge of the map's max zoom-out on desktop AND phone), so
// low-level traffic never cuts dead inside the frame. One request; OGN traffic is
// light, so a bigger box is still a small response.
window.wxOgnUrl = 'https://live.glidernet.org/lxml.php?a=0&b=49&c=36&d=33.5&e=17';
// backup while live.glidernet.org is down: our relay reads the same OGN network itself
// (same box, the DDB privacy choices kept) and answers in the same lxml format
window.wxOgnRelay = 'https://full-narwhal-4777.martinovem.deno.net/ogn';
// aircraft type code (marker column 10, 0-15) -> icon kind + name (FLARM/OGN enum)
window.wxOgnTypes = {
  1:{k:'gld',bg:'планер',en:'glider'}, 2:{k:'pwr',bg:'влекач',en:'tow plane'},
  3:{k:'hel',bg:'хеликоптер',en:'helicopter'}, 4:{k:'cht',bg:'парашутист',en:'skydiver'},
  5:{k:'pwr',bg:'десантен самолет',en:'drop plane'}, 6:{k:'par',bg:'делтапланер',en:'hang glider'},
  7:{k:'par',bg:'парапланер',en:'paraglider'}, 8:{k:'pwr',bg:'моторен самолет',en:'aircraft'},
  9:{k:'jet',bg:'реактивен',en:'jet'}, 11:{k:'bal',bg:'балон',en:'balloon'},
  12:{k:'bal',bg:'дирижабъл',en:'airship'}, 13:{k:'drn',bg:'дрон',en:'drone'}
};
window.wxOgnNoRot = {bal:1, cht:1, drn:1, gen:1}; // kinds with no meaningful heading -> don't rotate
window.wxOgnKind = function(t){ var e = window.wxOgnTypes[t]; return e ? e.k : 'gen'; };
window.wxOgnName = function(t){ var e = window.wxOgnTypes[t], bg = !(typeof LANG !== 'undefined' && LANG === 'en');
  return e ? (bg ? e.bg : e.en) : (bg ? 'летящ обект' : 'aircraft'); };
var OGN_F = '#16c8a8', OGN_S = '#0a423d'; // teal-green fill + dark outline: reads on the light 2D map AND the dark 3D satellite
function ognG(inner){ return WXPLN_SH + '<g fill="' + OGN_F + '" stroke="' + OGN_S + '" stroke-width="1.1" stroke-linejoin="round">' + inner + '</g></g>'; }
window.wxOgnKinds = {
  gld: {w:26, svg: ognG('<path d="M0,-12 C0.8,-12 1.2,-11 1.2,-9.6 L1.2,-2 L15,1 L15,3 L1.2,2 L1,9 L4,10.6 L4,12 L0,11 L-4,12 L-4,10.6 L-1,9 L-1.2,2 L-15,3 L-15,1 L-1.2,-2 L-1.2,-9.6 C-1.2,-11 -0.8,-12 0,-12 Z"/>')},
  pwr: {w:24, svg: ognG('<path d="M-2.9,-11.4 L2.9,-11.4" stroke-width="1.6" stroke-linecap="round"/><path d="M0,-10.8 C1,-10.8 1.6,-9.8 1.6,-8.4 L1.6,-5 L13,-4 L13,-0.9 L1.6,-1 L1.4,5.4 L5,7.2 L5,9.2 L0,8.4 L-5,9.2 L-5,7.2 L-1.4,5.4 L-1.6,-1 L-13,-0.9 L-13,-4 L-1.6,-5 L-1.6,-8.4 C-1.6,-9.8 -1,-10.8 0,-10.8 Z"/>')},
  hel: {w:26, svg: WXPLN_SH + '<path d="M0,-7.2 C3,-7.2 4.6,-4.6 4.6,-1.9 C4.6,0.9 3,3 0.9,3.3 L0.7,8.6 L3.4,9.4 L3.4,11 L-3.4,11 L-3.4,9.4 L-0.7,8.6 L-0.9,3.3 C-3,3 -4.6,0.9 -4.6,-1.9 C-4.6,-4.6 -3,-7.2 0,-7.2 Z" fill="' + OGN_F + '" stroke="' + OGN_S + '" stroke-width="1.1" stroke-linejoin="round"/><path d="M-7.5,-9.5 L7.5,5.5 M7.5,-9.5 L-7.5,5.5" stroke="' + OGN_S + '" stroke-width="1.6" fill="none" stroke-linecap="round"/><circle cx="0" cy="-2" r="1.4" fill="' + OGN_S + '"/></g>'},
  par: {w:24, svg: ognG('<path d="M-11,-5 A11,8.5 0 0 1 11,-5 L8.4,-3.4 A8,6.5 0 0 0 -8.4,-3.4 Z"/><path d="M-8,-3.6 L-0.6,6 M8,-3.6 L0.6,6" stroke-width="0.9" fill="none"/><circle cx="0" cy="8" r="1.8"/>')},
  cht: {w:22, svg: ognG('<path d="M-10,-3 A10,8.5 0 0 1 10,-3 L6,-2 A6,5.5 0 0 0 -6,-2 Z"/><path d="M-6,-2.2 L0,6.5 M6,-2.2 L0,6.5" stroke-width="0.9" fill="none"/><circle cx="0" cy="8.2" r="1.6"/>')},
  jet: {w:24, svg: ognG('<path d="M0,-13 C1.1,-13 1.7,-11.7 1.7,-9.9 L1.7,-3.8 L12.5,2.8 L12.5,5.2 L1.7,2 L1.7,7.2 L5.6,9.4 L5.6,11.2 L0.5,10.1 C0.4,10.8 0.2,11.1 0,11.1 C-0.2,11.1 -0.4,10.8 -0.5,10.1 L-5.6,11.2 L-5.6,9.4 L-1.7,7.2 L-1.7,2 L-12.5,5.2 L-12.5,2.8 L-1.7,-3.8 L-1.7,-9.9 C-1.7,-11.7 -1.1,-13 0,-13 Z"/>')},
  bal: {w:24, svg: ognG('<path d="M0,-12 C5.5,-12 9,-8 9,-3.5 C9,1.2 5,5.2 1.7,7 L-1.7,7 C-5,5.2 -9,1.2 -9,-3.5 C-9,-8 -5.5,-12 0,-12 Z"/><rect x="-2.4" y="7" width="4.8" height="3.4" rx="0.8"/>')},
  drn: {w:26, svg: ognG('<path d="M-8,-8 L8,8 M8,-8 L-8,8" stroke-width="1.6"/><circle cx="-8" cy="-8" r="3.2"/><circle cx="8" cy="-8" r="3.2"/><circle cx="-8" cy="8" r="3.2"/><circle cx="8" cy="8" r="3.2"/><rect x="-2.6" y="-2.6" width="5.2" height="5.2" rx="1.2"/>')},
  gen: {w:20, svg: ognG('<circle cx="0" cy="0" r="6"/>')}
};
// parse the lxml <m a="lat,lon,cn,ps,alt,time,ddf,track,speed,vz,type,recv,fid,crc"/> markers
window.wxOgnParse = function(txt){
  var out = [];
  try{
    var doc = new DOMParser().parseFromString(txt, 'text/xml');
    var ms = doc.getElementsByTagName('m');
    for (var i = 0; i < ms.length; i++){
      var t = (ms[i].getAttribute('a') || '').split(',');
      if (t.length < 14) continue;
      var typ = parseInt(t[10], 10); if (isNaN(typ) || typ < 0 || typ > 15) typ = 0;
      if (typ === 15) continue; // static ground objects (receivers etc.) are not traffic
      var lat = parseFloat(t[0]), lon = parseFloat(t[1]);
      if (!isFinite(lat) || !isFinite(lon)) continue;
      out.push({lat: lat, lon: lon, cn: t[2], ps: t[3], alt: parseFloat(t[4]),
        track: parseFloat(t[7]), speed: parseFloat(t[8]), vz: parseFloat(t[9]),
        typ: typ, fid: t[12], crc: t[13] || (t[0] + '_' + t[1])});
    }
  }catch(e){}
  return out;
};
window.wxOgnInfo = function(a){
  var bg = !(typeof LANG !== 'undefined' && LANG === 'en');
  function esc(s){ return (s + '').replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
  var anon = (!a.fid || a.fid === '0'); // opted-out pilots arrive anonymised (no FLARM id)
  var name = anon ? (bg ? 'анонимен' : 'anonymous')
                  : ((a.cn && a.cn !== '_') ? a.cn : (a.ps || (bg ? 'обект' : 'object')));
  var h = '<b>' + esc(name) + '</b> · ' + esc(window.wxOgnName(a.typ));
  if (isFinite(a.alt)){ h += '<br>' + (bg ? 'височина: ' : 'altitude: ') + Math.round(a.alt) + ' m';
    if (isFinite(a.vz) && Math.abs(a.vz) >= 0.3) h += ' · ' + (a.vz > 0 ? '↑' : '↓') + Math.abs(a.vz).toFixed(1) + (bg ? ' м/с' : ' m/s'); }
  if (isFinite(a.speed)) h += '<br>' + (bg ? 'скорост: ' : 'speed: ') + Math.round(a.speed) + ' km/h' +
    (isFinite(a.track) ? ' · ' + (bg ? 'курс: ' : 'track: ') + Math.round(a.track) + '°' : '');
  h += '<br><small>Open Glider Network</small>';
  return h;
};

// ---- Flight-level filter: applies to the ADS-B ✈ layer ONLY ----
// FL = pressure altitude in hundreds of feet; ADS-B alt_baro is already feet
// (barometric) -> FL = alt_baro/100, exact. Aircraft with unknown altitude are
// always shown. The ✈ layer registers a redraw in wxReapply so moving the slider
// re-filters instantly, without waiting a poll (the menu note also scopes the
// slider to ✈). The OGN 🛩 low-traffic layer is DELIBERATELY not height-filtered:
// it is low aviation (gliders/paragliders/GA) - exactly the altitudes where drones
// fly - so it always shows in full regardless of the slider.
window.wxFL = {min: 0, max: 660};
window.wxFlOk = function(altFt){ if (altFt == null || !isFinite(altFt)) return true;
  var fl = altFt / 100; return fl >= window.wxFL.min && fl <= window.wxFL.max; };
window.wxReapply = [];
window.wxFlApply = function(){ window.wxReapply.forEach(function(f){ try{ f(); }catch(e){} }); };
// each open-popup owner (zones, aircraft, OGN) registers a re-render here so a
// BG/EN switch retranslates the OPEN popup immediately, not only on reopen
window.wxLangRefresh = window.wxLangRefresh || [];
window.wxRefreshOpenPopups = function(){ (window.wxLangRefresh || []).forEach(function(f){ try{ f(); }catch(e){} }); };
// wire the dual-range FL slider in the panel: restore saved bounds, filter live
(function(){
  var lo = document.getElementById('flmin'), hi = document.getElementById('flmax');
  if (!lo || !hi) return;
  window.wxFL.min = ST.get('flmin', 0); window.wxFL.max = ST.get('flmax', 660);
  function paint(){
    lo.value = window.wxFL.min; hi.value = window.wxFL.max;
    var a = document.getElementById('fllblmin'), b = document.getElementById('fllblmax'), fill = document.getElementById('flfill');
    if (a) a.textContent = 'FL' + window.wxFL.min; if (b) b.textContent = 'FL' + window.wxFL.max;
    if (fill){ fill.style.left = (window.wxFL.min / 660 * 100) + '%'; fill.style.right = (100 - window.wxFL.max / 660 * 100) + '%'; }
  }
  function onInput(e){
    var mn = +lo.value, mx = +hi.value;
    if (mn > mx){ if (e.target === lo) mx = mn; else mn = mx; } // keep min <= max
    window.wxFL.min = mn; window.wxFL.max = mx;
    ST.set('flmin', mn); ST.set('flmax', mx);
    paint(); window.wxFlApply();
  }
  lo.addEventListener('input', onInput); hi.addEventListener('input', onInput);
  window.wxFlEnable = function(on){
    var sec = document.getElementById('flsec'); if (sec) sec.classList.toggle('fldis', !on);
    lo.disabled = !on; hi.disabled = !on;
  };
  window.wxFlEnable(false); // ✈ is off by default; the restore block re-enables it if it was saved on
  paint();
})();
"""

# Shared restore snippet appended to BOTH per-map layer scripts below: it flips
# the saved switches back on at page load. It must run AFTER the wxSet* layer
# functions exist, i.e. after the per-map layer script — hence the appending.
WX_RESTORE_JS = r"""
// ---- restore the saved layer switches (shared settings store) on page load ----
(function(){
  window.wxFcState.hour = ST.get('fch', 0);
  var sl = document.getElementById('wxfcsl'); if (sl) sl.value = window.wxFcState.hour;
  // wind height (set before the layer turns on so the chip + engine use it)
  var wh = ST.get('windh', 10); if (window.wxWindState) window.wxWindState.h = wh;
  window.wxGjWin = (ST.get('gjWin', 12) === 24) ? 24 : 12; var _gjSaved = ST.get('gjDay', null); if (_gjSaved === ''){ window.wxGjDay = ''; window.wxGjAuto = false; } // only an explicit LIVE choice survives a reload; a picked past day is for this visit only (owner 04.10: a reload opens the newest ready day) - an old saved date is ignored -> auto
  if (ST.shared && typeof ST.shared.gd === 'string'){ window.wxGjDay = ST.shared.gd; window.wxGjAuto = false; } // a shared view: the sender's GPS day ('' = live)
  document.querySelectorAll('#wxwindh .wxhseg button').forEach(function(x){ x.classList.toggle('on', +x.getAttribute('data-h') === wh); });
  [['cld','wxcld','wxSetClouds'], ['rad','wxrad','wxSetRain'],
   ['snow','wxsnow','wxSetSnow'], ['gj','wxgj','wxSetGj'],
   ['airc','cbAirC','wxSetAirC'], ['airs','cbAirS','wxSetAirS'], ['act','cbAct','wxSetAct'], ['aero','cbAero','wxSetAero'], ['notam','cbNotam','wxSetNotam'],
   ['nat','cbNat','wxSetNat'], ['zzt','cbZzt','wxSetZzt'], ['pln','plnbtn','wxSetPlanes'], ['wind','wxwind','wxSetWind'],
   ['ogn','ognbtn','wxSetOgn']].forEach(function(s){
    if (!ST.get(s[0], false)) return;
    var fn = window[s[2]]; if (typeof fn !== 'function') return; // layer not present on this page yet
    var b = document.getElementById(s[1]); if (b) b.classList.add('on');
    try{ fn(true); }catch(e){} // one broken engine must never kill the layers after it (F5 bug, 17.09)
  });
  // obstacles + the 3D buildings: ON by default (owner 17.10), so restored from their own default
  var ob = document.getElementById('cbObs');
  if (ob){ var obOn = ST.get('obs', true); ob.classList.toggle('on', obOn); if (window.wxSetObs) try{ window.wxSetObs(obOn); }catch(e){} }
  if (window.wxFlEnable) window.wxFlEnable(ST.get('pln', false)); // FL slider active only if ✈ restored on
  if (ST.get('wind', false)){ var whd = document.getElementById('wxwindh'); if (whd) whd.hidden = false;
    if (window.wxSyncFcBar) window.wxSyncFcBar(); }
})();
"""

# Per-map weather layer scripts. Both define window.wxSetClouds / window.wxSetRain,
# which the widget's cloud/rain buttons call. Clouds: one country-wide image
# built by wxCloudBuild (in WX_JS) — EUMETSAT cloud mask + IR channel merged in
# the browser into white-on-transparent clouds, usable day AND night (the
# earlier geocolour photo showed city lights on black at night). Rain:
# RainViewer public tiles (keyless) — the last ~1 h of radar frames animated in
# a loop; the small label next to the buttons shows the frame time. Both layers
# render BELOW the zone overlays so restrictions stay readable. Both scripts
# also define window.wxSetPlanes: live aircraft via the project's Deno relay
# over adsb.fi/adsb.lol (fixed all-Bulgaria query, 8 s poll, airborne only)
# drawn ABOVE the zones.


WX_LAYERS_JS_3D = r"""
// ---- weather map layers (MapLibre): EUMETSAT clouds + RainViewer radar ----
(function(){
// weather rasters go below the zone fills (and below buildings) so zones stay readable
// Fixed stack below the zones (whatever order the user toggles): weather < GPS <
// Natura 2000 < airspace < zones (< aircraft, which have no beforeId). Each layer inserts
// before the lowest layer of a higher slot that currently exists.
function wxStyleLayers(){ try{ var st = map.getStyle(); return (st && st.layers) || []; }catch(e){ return []; } } // [] before the style is ready - callers then anchor lazily
function wxZoneAnchor(){ var zs = {'f-PROHIBITED':1, 'f-REQ_AUTHORISATION':1, 'f-CONDITIONAL':1}, ls = wxStyleLayers(), i;
  for (i = 0; i < ls.length; i++){ if (zs[ls[i].id]) return ls[i].id; } // LOWEST zone layer = "below ALL zones"
  return map.getLayer('buildings') ? 'buildings' : undefined; }
// the LOWEST airspace layer currently on the map: the air layers all sit just under the
// zones, but their order AMONG themselves depends on the toggle sequence, so GPS + weather
// must anchor below ALL of them - not below whichever one we happen to name first (that bug
// let the clouds slip above the red/pink 'special airspace' outline). Scan bottom -> top.
function wxAirFloor(){ var ls = wxStyleLayers(), i;
  for (i = 0; i < ls.length; i++){ if (ls[i].id === 'air-ctrl' || ls[i].id === 'air-spec' || ls[i].id === 'air-ctrl-labels' || ls[i].id === 'air-spec-labels') return ls[i].id; }
  return undefined; }
// the LOWEST layer of the nature slot (Natura 2000 + protected territories, information layers:
// above GPS + weather, below airspace + zones); within the slot the territories sit above Natura
function natFloor(pre){ var ls = wxStyleLayers(), i; pre = pre || 'wxnat-';
  for (i = 0; i < ls.length; i++){ if (ls[i].id.indexOf(pre) === 0) return ls[i].id; }
  return undefined; }
function zztFloor(){ return natFloor('wxnat-t-'); }
function wxGjBefore(){ return natFloor() || wxAirFloor() || wxZoneAnchor(); } // GPS + weather below Natura 2000 + ALL airspace
function wxBefore(){ return map.getLayer('wxgj-layer') ? 'wxgj-layer' : wxGjBefore(); } // weather below GPS
// adding sources/layers before the style finishes loading throws in MapLibre.
// Wait for 'idle', not 'load': 'load' fires only ONCE ever, so waiting on it
// while tiles are merely refreshing would hang forever; 'idle' fires again
// after every loading spell.
function whenReady(fn){ if (map.isStyleLoaded()) fn(); else map.once('idle', fn); }
// refresh a wxcv raster layer IN PLACE when it already exists (setTiles keeps its
// z-order); otherwise add it fresh at `beforeId`. This stops the forecast layers
// from jumping to the top each time they re-render on a slider move (owner's report).
function wxRaster(layerId, srcId, key, attr, opacity, beforeId){
  var src = map.getSource(srcId), stamp = 'wxcv://' + key + '/' + Date.now() + '/{z}/{x}/{y}';
  if (src && map.getLayer(layerId)){ src.setTiles([stamp]); return; } // in place -> draw order preserved
  if (map.getLayer(layerId)) map.removeLayer(layerId);
  if (src) map.removeSource(srcId);
  map.addSource(srcId, {type: 'raster', tiles: [stamp], tileSize: 256, maxzoom: 8, attribution: attr});
  map.addLayer({id: layerId, type: 'raster', source: srcId,
    paint: {'raster-opacity': opacity, 'raster-fade-duration': 0}}, beforeId);
}
// id of the layer drawn just above `layerId` (its slot), so a swapped-in layer keeps the same position
function wxAboveOf(layerId){ var ls = wxStyleLayers(), i;
  for (i = 0; i < ls.length; i++){ if (ls[i].id === layerId) return (i + 1 < ls.length) ? ls[i + 1].id : undefined; }
  return undefined; }
var CLD = 'wxcld-layer', CLDFC = 'wxcldfc-layer', cldTimer = null, cldOn = false, cldProtoDone = false, cldEmptyTile = null;
var LI = 'wxli-layer', STM = 'wxstorm-layer', liTimer = null; // lightning (now) + model thunderstorms (ahead), both with ☁
// An 'image' source gets clipped to a single web-mercator tile when 3D terrain
// is on (seen live: hard edges at 22.5°E / 40.98°N — z4 tile borders). So the
// cloud canvas is served as proper raster TILES instead, cut on the fly.
function cldProto(){
  if (cldProtoDone || !maplibregl.addProtocol) return; cldProtoDone = true;
  // generic cutter: wxcv://KEY/stamp/z/x/y serves 256px tiles cut from whichever
  // canvas is registered under KEY in window._wxCvReg (clouds 'cld', forecast 'fc')
  // decode a canvas to a PNG ArrayBuffer SYNCHRONOUSLY — toBlob is async and
  // does not fire reliably under headless virtual-time, which broke testing
  function pngBuf(canvas){
    var b64 = canvas.toDataURL('image/png').split(',')[1], bin = atob(b64), n = bin.length;
    var u = new Uint8Array(n); for (var i = 0; i < n; i++) u[i] = bin.charCodeAt(i);
    return u.buffer;
  }
  maplibregl.addProtocol('wxcv', function(params){
    return new Promise(function(resolve){
      var m = params.url.match(/wxcv:\/\/([a-z]+)\/\d+\/(\d+)\/(\d+)\/(\d+)/);
      var reg = (m && window._wxCvReg) ? window._wxCvReg[m[1]] : null;
      function empty(){ // fully transparent 1x1 for tiles outside the canvas box
        if (!cldEmptyTile){ var e = document.createElement('canvas'); e.width = 1; e.height = 1; cldEmptyTile = pngBuf(e); }
        resolve({data: cldEmptyTile});
      }
      if (!reg){ empty(); return; }
      var cv = reg.cv, g = reg.m;
      var M = 20037508.343, world = 2 * M, z = +m[2], xx = +m[3], yy = +m[4], n = Math.pow(2, z);
      var tx1 = xx / n * world - M, tx2 = (xx + 1) / n * world - M;
      var ty2 = M - yy / n * world, ty1 = M - (yy + 1) / n * world;
      var ix1 = Math.max(tx1, g.x1), ix2 = Math.min(tx2, g.x2), iy1 = Math.max(ty1, g.y1), iy2 = Math.min(ty2, g.y2);
      if (ix1 >= ix2 || iy1 >= iy2){ empty(); return; }
      var t = document.createElement('canvas'); t.width = 256; t.height = 256;
      t.getContext('2d').drawImage(cv,
        (ix1 - g.x1) / (g.x2 - g.x1) * cv.width, (g.y2 - iy2) / (g.y2 - g.y1) * cv.height,
        (ix2 - ix1) / (g.x2 - g.x1) * cv.width, (iy2 - iy1) / (g.y2 - g.y1) * cv.height,
        (ix1 - tx1) / (tx2 - tx1) * 256, (ty2 - iy2) / (ty2 - ty1) * 256,
        (ix2 - ix1) / (tx2 - tx1) * 256, (iy2 - iy1) / (ty2 - ty1) * 256);
      resolve({data: pngBuf(t)});
    });
  });
}
// Clouds are TIME-AWARE (owner's design): the ☁ button shows the EUMETSAT
// satellite at hour 0 ("now") and the Open-Meteo MODEL clouds when the shared
// slider moves ahead. Both render through the same tile cutter, styled the same
// (grey fringes / white cores). Satellite -> registry 'cld'; model -> 'cldfc'.
function cldMode(){ return (window.wxFcState && window.wxFcState.hour > 0) ? 'model' : 'sat'; }
function cldSatShow(){ // show the satellite image (hour 0); refresh in place, or take the model layer's slot when swapping
  window.wxCloudBuild(function(){
    if (!cldOn || cldMode() !== 'sat') return;
    whenReady(function(){
      if (!cldOn || cldMode() !== 'sat') return;
      cldProto();
      var pos = map.getLayer(CLDFC) ? wxAboveOf(CLDFC) : wxBefore(); // keep clouds' z-order (vs rain) across the swap
      if (map.getLayer(CLDFC)) map.removeLayer(CLDFC);
      if (map.getSource('wxcldfc')) map.removeSource('wxcldfc');
      wxRaster(CLD, 'wxcld', 'cld', 'Clouds &copy; <a href="https://www.eumetsat.int/" target="_blank" rel="noopener">EUMETSAT</a>', 0.9, pos);
    });
  });
}
function cldModelShow(){ // draw the model clouds for the selected hour (hour > 0); refresh in place, or take the satellite layer's slot when swapping
  var r = window.wxCloudFcDraw(); if (!r) return; // also registers 'cldfc' for the tile cutter
  whenReady(function(){
    if (!cldOn || cldMode() !== 'model') return;
    cldProto();
    var pos = map.getLayer(CLD) ? wxAboveOf(CLD) : wxBefore(); // keep clouds' z-order (vs rain) across the swap
    if (map.getLayer(CLD)) map.removeLayer(CLD);
    if (map.getSource('wxcld')) map.removeSource('wxcld');
    wxRaster(CLDFC, 'wxcldfc', 'cldfc', 'Clouds &copy; <a href="https://open-meteo.com/" target="_blank" rel="noopener">Open-Meteo</a> (model)', 0.85, pos);
  });
}
// lightning = one GeoJSON symbol layer of ⚡ bolts (owner 15.10): the last 30 min without the rain
// radar; while the radar loops, its data switches with every radar frame (the 30 min up to it)
var liSync = false, LIATTR = 'Lightning &copy; <a href="https://www.eumetsat.int/" target="_blank" rel="noopener">EUMETSAT</a>';
function liRemove(){ if (map.getLayer(LI)) map.removeLayer(LI); if (map.getSource('wxli')) map.removeSource('wxli'); liSync = false; window.wxLiRef = 0; }
function stormRemove(){ if (map.getLayer(STM)) map.removeLayer(STM); if (map.getSource('wxstorm')) map.removeSource('wxstorm'); }
// lightning is drawn just above the zones (owner 15.10: over the clouds AND the zones) but below
// the layers added later without a slot (NOTAM pins, aircraft, activated zones)
function liSlot(){ var top = map.getLayer('obs-sym2') ? 'obs-sym2' : map.getLayer('aero-label') ? 'aero-label' : map.getLayer('o-CONDITIONAL') ? 'o-CONDITIONAL' : null; // above the zones, the airfields AND the obstacles
  return top ? wxAboveOf(top) : undefined; }
function liFrames(){ return (rvOn && rvFrames.length) ? rvFrames.map(function(f){ return f.time * 1000; }) : null; }
function liIcon(){ // a yellow bolt with a dark outline, drawn once at pixel ratio 2
  if (map.hasImage('ltg-bolt')) return;
  var R = 2, w = 22 * R, h = 26 * R, c = document.createElement('canvas'); c.width = w; c.height = h;
  var x = c.getContext('2d'); x.translate(w / 2, h / 2); x.scale(R * 1.2, R * 1.2);
  x.beginPath(); x.moveTo(1, -9); x.lineTo(-5, 1); x.lineTo(-1, 1); x.lineTo(-3, 9); x.lineTo(5, -2); x.lineTo(1, -2); x.lineTo(3, -9); x.closePath();
  x.lineJoin = 'round'; x.lineWidth = 2.2; x.strokeStyle = '#141414'; x.stroke(); x.fillStyle = '#ffd400'; x.fill();
  map.addImage('ltg-bolt', x.getImageData(0, 0, w, h), {pixelRatio: R});
}
function liLayer(){ // the bolts layer (once): bolts never overlap - MapLibre thins them when zoomed out, the
  // newest + strongest win where they would collide; older = fainter
  liIcon();
  if (!map.getSource('wxli')) map.addSource('wxli', {type: 'geojson', data: {type: 'FeatureCollection', features: []}, attribution: LIATTR});
  if (!map.getLayer(LI)) map.addLayer({id: LI, type: 'symbol', source: 'wxli',
    layout: {'icon-image': 'ltg-bolt', 'icon-size': 0.8, 'icon-allow-overlap': false, 'icon-ignore-placement': false, 'icon-padding': 2,
      'symbol-sort-key': ['-', ['get', 'a'], ['*', 10, ['get', 'f']]]},
    paint: {'icon-opacity': ['interpolate', ['linear'], ['get', 'a'], 0, 1, 25, 0.4]}}, liSlot());
}
function liShow(){ // hour 0: the last 30 min, or one window per radar frame while the radar loops
  var fr = liFrames();
  window.wxLiBuild(fr, function(ok){
    if (window.wxLtgNote) window.wxLtgNote();
    if (!ok || !cldOn || cldMode() !== 'sat') return; // a failed refresh keeps the last bolts; the note tells
    whenReady(function(){
      if (!cldOn || cldMode() !== 'sat') return;
      liLayer(); liSync = !!fr;
      if (liSync) liSyncShow();
      else { window.wxLiRef = 0; map.getSource('wxli').setData(window.wxLiState.fc[0]); if (window.wxLtgNote) window.wxLtgNote(); }
    });
  });
}
function liSyncShow(){ // the radar ticked: the bolts of that frame's 30 min, and the note's time with it
  if (!liSync || !map.getSource('wxli')) return;
  var L = window.wxLiState, i = Math.min(rvIdx, L.fc.length - 1); if (i < 0) return;
  map.getSource('wxli').setData(L.fc[i]); window.wxLiRef = L.refs[i] || 0;
  if (window.wxLtgNote) window.wxLtgNote();
}
function stormShow(){ // the model thunderstorms for the selected hour (ahead): ⚡ yellow (2-3 models) / pale (1 model), just above the zones like the lightning "now"
  var fc = window.wxStormPoints(); if (window.wxLtgNote) window.wxLtgNote(); if (!fc) return;
  whenReady(function(){
    if (!cldOn || cldMode() !== 'model') return;
    liIcon();
    if (map.getSource('wxstorm')) map.getSource('wxstorm').setData(fc);
    else map.addSource('wxstorm', {type: 'geojson', data: fc, attribution: 'Thunderstorms &copy; <a href="https://open-meteo.com/" target="_blank" rel="noopener">Open-Meteo</a> (model)'});
    if (!map.getLayer(STM)) map.addLayer({id: STM, type: 'symbol', source: 'wxstorm',
      layout: {'icon-image': 'ltg-bolt', 'icon-size': 0.8, 'icon-allow-overlap': false, 'icon-ignore-placement': false, 'icon-padding': 2,
        'symbol-sort-key': ['-', ['get', 's']]}, // the yellow ones win where two would collide
      paint: {'icon-opacity': ['case', ['==', ['get', 's'], 2], 1, 0.45]}}, liSlot());
  });
}
window.wxCloudApply = function(){ // toggle + every slider move: satellite + lightning (0) or model clouds + thunderstorms (ahead)
  if (!cldOn) return;
  if (cldMode() === 'sat'){ stormRemove(); cldSatShow(); liShow(); }
  else { liRemove();
    if (window.wxFcState && window.wxFcState.data){ cldModelShow(); stormShow(); }
    else { window.wxFcFetch(function(){ if (cldOn && cldMode() === 'model'){ cldModelShow(); stormShow(); } }); } } // grid loads once; rain/snow reuse it
  if (window.wxLtgNote) window.wxLtgNote();
};
// generic "working…" cue: pulse a layer's button/chip from toggle-on until its
// MapLibre source appears (or ~12 s timeout). Turning the layer off removes the
// class, which also stops the watcher.
function wxBtnBusy(btnId, srcIds){
  var b = document.getElementById(btnId); if (!b) return;
  b.classList.add('loading');
  var ids = (typeof srcIds === 'string') ? [srcIds] : srcIds, n = 0;
  var t = setInterval(function(){
    if (!b.classList.contains('loading')){ clearInterval(t); return; }
    var have = false; for (var i = 0; i < ids.length; i++){ if (map.getSource(ids[i])){ have = true; break; } }
    if (have || ++n > 80){ clearInterval(t); b.classList.remove('loading'); }
  }, 150);
}
function wxBtnIdle(btnId){ var b = document.getElementById(btnId); if (b) b.classList.remove('loading'); }

window.wxSetClouds = function(on){ cldOn = on; clearInterval(cldTimer); clearInterval(liTimer);
  if (on){ wxBtnBusy('wxcld', ['wxcld','wxcldfc']); window.wxCloudApply();
    cldTimer = setInterval(function(){ if (cldOn && cldMode() === 'sat') cldSatShow(); }, 600000); // refresh the satellite every 10 min while it is the one shown
    liTimer = setInterval(function(){ if (cldOn && cldMode() === 'sat') liShow(); }, 300000); // a new lightning step every 5 min
  } else { wxBtnIdle('wxcld');
    if (map.getLayer(CLD)) map.removeLayer(CLD);
    if (map.getSource('wxcld')) map.removeSource('wxcld');
    if (map.getLayer(CLDFC)) map.removeLayer(CLDFC);
    if (map.getSource('wxcldfc')) map.removeSource('wxcldfc');
    liRemove(); stormRemove(); }
  if (window.wxLtgNote) window.wxLtgNote();
  if (window.wxSyncFcBar) window.wxSyncFcBar();
};
var rvFrames = [], rvIds = [], rvIdx = 0, rvTick = null, rvRefresh = null, rvOn = false;
var FCL = 'wxfc-layer', fcTimer = null, rainOn = false, rainBefore; // rainBefore = z-slot for the rain block (radar frames or FCL)
function rainMode(){ return (window.wxFcState && window.wxFcState.hour > 0) ? 'model' : 'radar'; }
function rvLabel(){ var el = document.getElementById('wxframe');
  var rvN = document.getElementById('wxrvnote');
  if (rvN) rvN.hidden = !(rvOn && rvFrames.length); // the night-noise caveat is about the radar, not the model
  if (!el) return;
  if (!rvOn || !rvFrames.length){ el.hidden = true; return; }
  var d = new Date(rvFrames[rvIdx].time * 1000);
  el.hidden = false; el.textContent = ('0' + d.getHours()).slice(-2) + ':' + ('0' + d.getMinutes()).slice(-2); }
function rvClear(){ rvIds.forEach(function(id){
    if (map.getLayer(id)) map.removeLayer(id);
    if (map.getSource(id)) map.removeSource(id); }); rvIds = []; }
function rvShow(){ rvIds.forEach(function(id, i){
    map.setLayoutProperty(id, 'visibility', i === rvIdx ? 'visible' : 'none'); }); rvLabel(); liSyncShow(); } // the lightning follows the radar frame
function rvBuild(host){
  // keep the radar block's current z-slot on a reload; else use the rain block's slot
  var pos = (rvIds.length && map.getLayer(rvIds[rvIds.length - 1])) ? wxAboveOf(rvIds[rvIds.length - 1]) : (rainBefore || wxBefore()); // capture may predate the style - re-anchor now
  rvClear();
  rvFrames.forEach(function(f, i){ var id = 'wxrad' + i;
    // free RainViewer: max zoom 7, 512px tiles (their personal-use docs); MapLibre overzooms beyond
    map.addSource(id, {type: 'raster', tiles: [host + f.path + '/512/{z}/{x}/{y}/2/1_1.png'], tileSize: 256, maxzoom: 7,
      attribution: i === 0 ? 'Rain <a href="https://www.rainviewer.com/" target="_blank" rel="noopener">RainViewer</a>' : ''});
    map.addLayer({id: id, type: 'raster', source: id, layout: {visibility: 'none'},
      paint: {'raster-opacity': 0.7}}, pos);
    rvIds.push(id); });
  rvIdx = rvFrames.length - 1; rvShow();
  if (cldOn && cldMode() === 'sat') liShow(); } // new radar frames: rebuild the lightning windows for them
function rvLoad(){
  fetch('https://api.rainviewer.com/public/weather-maps.json')
    .then(function(r){ return r.json(); })
    .then(function(d){ if (!rvOn) return;
      rvFrames = ((d.radar && d.radar.past) || []).slice(-7);
      if (rvFrames.length) whenReady(function(){ rvBuild(d.host); }); })
    .catch(function(){ if (rvOn){ clearTimeout(window._rvRt); window._rvRt = setTimeout(function(){ if (rvOn) rvLoad(); }, 15000); } }); } // failed list fetch: retry in 15 s (the 5-min refresh also covers it)
function rvStart(){ if (rvOn) return; rvOn = true; rvLoad();
  rvTick = setInterval(function(){ if (rvIds.length){ rvIdx = (rvIdx + 1) % rvIds.length; rvShow(); } }, 800);
  rvRefresh = setInterval(rvLoad, 300000); }
function rvStop(){ rvOn = false; clearInterval(rvTick); clearInterval(rvRefresh); rvClear(); rvFrames = []; rvLabel();
  if (liSync && cldOn && cldMode() === 'sat') liShow(); } // radar gone: back to one lightning picture (the last 30 min)
// ---- forecast rain (Open-Meteo model, shared engine in WX_JS) ----
window.wxFcApply = function(){
  if (!window.wxFcState.on) return;
  var r = window.wxFcDraw(); if (!r) return; // also registers 'fc' for the tile cutter
  whenReady(function(){
    if (!window.wxFcState.on) return;
    cldProto();
    wxRaster(FCL, 'wxfc', 'fc', 'Forecast <a href="https://open-meteo.com/" target="_blank" rel="noopener">Open-Meteo</a>', 0.75, rainBefore || wxBefore());
    window.wxFcLabel();
  });
};
function fcStop(){ clearInterval(fcTimer); fcTimer = null; window.wxFcState.on = false;
  if (map.getLayer(FCL)) map.removeLayer(FCL); if (map.getSource('wxfc')) map.removeSource('wxfc'); }
// ---- one "Дъжд" layer: RainViewer radar at hour 0, Open-Meteo model ahead (time-aware) ----
window.wxRainApply = function(){ // toggle + every slider move: pick radar (0) or model (ahead), keeping the z-order
  if (!rainOn) return;
  if (rainMode() === 'radar'){
    if (map.getLayer(FCL) || fcTimer){ rainBefore = map.getLayer(FCL) ? wxAboveOf(FCL) : rainBefore; fcStop(); } // leaving model: keep the slot
    rvStart(); // no-op if already animating
  } else {
    if (rvOn){ rainBefore = (rvIds.length && map.getLayer(rvIds[rvIds.length - 1])) ? wxAboveOf(rvIds[rvIds.length - 1]) : rainBefore; rvStop(); } // leaving radar: keep the slot
    window.wxFcState.on = true;
    if (!fcTimer){ // entering model: one fetch now + a 30-min refresh
      fcTimer = setInterval(function(){ if (rainOn && rainMode() === 'model') window.wxFcFetch(function(){ window.wxFcApply(); }); }, window.WX_MODEL_TTL);
      window.wxFcFetch(function(){ window.wxFcApply(); });
    } else { window.wxFcApply(); } // already model, slider moved: just redraw the selected hour
  }
};
window.wxSetRain = function(on){ rainOn = on;
  var lg = document.getElementById('wxlegend'); // one rain legend, shown whenever Дъжд is on (radar or model)
  if (on){ wxBtnBusy('wxrad', ['wxfc','wxrad0']); rainBefore = wxBefore(); if (lg) lg.hidden = false; window.wxRainApply(); }
  else { wxBtnIdle('wxrad'); if (lg) lg.hidden = true; rvStop(); fcStop(); }
  if (window.wxSyncFcBar) window.wxSyncFcBar(); // the slider bar is shared with wind + snow
};
// ---- forecast SNOW (Open-Meteo model; shares the rain grid + a small mountain request) ----
var SNL = 'wxsnow-layer', snowTimer = null;
// Mountain points: the grid samples every ~55-80 km and lands in valleys, so snow on the
// ridges fell BETWEEN its points (28.09: Musala 3 cm in 3 days vs 0 cm and rain at the
// nearest grid point, 784 m). 30 ridge / ski-area points, their heights checked on
// Open-Meteo's 90 m terrain model (owner 29.09); snowfall only, fetched only while the
// snow layer is on - Open-Meteo counts EVERY location, so this adds 30 per refresh.
var WX_MTN = window.WX_MTN = [
  [42.1797,23.5853],[42.1789,23.4064],[42.2360,23.5840],[42.2034,23.3219],[42.1806,23.7462], // Rila: Musala, Malyovitsa, Borovets, Seven Lakes, Belmeken
  [41.7672,23.3994],[41.7883,23.4383],[41.7714,23.4929],[41.6708,23.4892],[41.5105,23.6497], // Pirin: Vihren, Bansko (below Todorka), above Dobrinishte, Kamenitsa, Orelyak
  [42.5636,23.2786],[42.5840,23.2930],                                                        // Vitosha: Cherni vrah, Aleko
  [43.3967,22.6739],[43.1739,23.0536],[42.8328,23.6710],[42.7547,24.3953],[42.7833,24.6167],
  [42.7169,24.9175],[42.7063,25.1527],[42.7358,25.3936],[42.7847,25.9674],                   // Stara planina: Midzhur, Kom, Murgash, Vezhen, Beklemeto, Botev, above Uzana, Buzludzha, Chumerna
  [41.6394,24.6775],[41.6031,24.5733],[41.8167,24.5498],[41.7250,24.6850],[41.8597,24.0209], // Rhodopes: Pamporovo, Golyam Perelik, Golyam Persenk, Chepelare, Syutkya
  [42.1600,22.5150],[41.3350,22.9925],[41.3801,23.6209],[42.6140,24.5155]                    // Osogovo (Ruen), Belasitsa, Slavyanka, Sredna gora (Bogdan)
];
window.wxMtnFetch = function(cb){ // S.mtn = {at, t, s: [point][hour] cm/h}; cached like the grid, never blocks the grid
  var S = window.wxFcState;
  if (S.mtn && Date.now() - S.mtn.at < window.WX_MODEL_TTL){ cb(); return; }
  try{ var c = JSON.parse(localStorage.getItem('wxmtn1'));
    if (c && c.t && c.s && Date.now() - c.at < window.WX_MODEL_TTL){ S.mtn = c; cb(); return; }
  }catch(e){}
  fetch('https://api.open-meteo.com/v1/forecast?latitude=' + WX_MTN.map(function(q){ return q[0]; }).join(',') +
        '&longitude=' + WX_MTN.map(function(q){ return q[1]; }).join(',') +
        '&hourly=snowfall&forecast_hours=76&timezone=UTC&models=icon_eu,gfs_seamless,ecmwf_ifs025')
    .then(function(r){ return r.json(); })
    .then(function(d){
      if (!Array.isArray(d) || d.length !== WX_MTN.length){ cb(); return; } // rate-limited: the grid alone
      S.mtn = {at: Date.now(), t: d[0].hourly.time, s: d.map(function(x){ // MAX across the models, like fcMax
        var h = x.hourly, ks = Object.keys(h).filter(function(k){ return k.indexOf('snowfall') === 0; });
        return h.time.map(function(_, i){ var m = 0; ks.forEach(function(k){ if (h[k][i] > m) m = h[k][i]; }); return m; }); })};
      try{ localStorage.setItem('wxmtn1', JSON.stringify(S.mtn)); }catch(e){}
      cb();
    }).catch(function(){ cb(); });
};
window.wxSnowApply = function(){
  if (!window.wxSnowOn) return;
  var r = window.wxSnowDraw(); if (!r) return; // also registers 'snow' for the tile cutter
  whenReady(function(){
    if (!window.wxSnowOn) return;
    cldProto();
    wxRaster(SNL, 'wxsnow', 'snow', 'Forecast <a href="https://open-meteo.com/" target="_blank" rel="noopener">Open-Meteo</a>', 0.8, wxBefore());
    window.wxFcLabel();
  });
};
window.wxSetSnow = function(on){ window.wxSnowOn = on;
  var lg = document.getElementById('wxsnowlegend');
  if (on){
    wxBtnBusy('wxsnow', 'wxsnow');
    if (lg) lg.hidden = false;
    var go = function(){ window.wxFcFetch(function(){ window.wxMtnFetch(function(){ window.wxSnowApply(); }); }); };
    go(); snowTimer = setInterval(go, window.WX_MODEL_TTL); // fresh model data every 3 h (model runs, see wxFcFetch)
  } else {
    clearInterval(snowTimer); wxBtnIdle('wxsnow');
    if (lg) lg.hidden = true;
    if (map.getLayer(SNL)) map.removeLayer(SNL);
    if (map.getSource('wxsnow')) map.removeSource('wxsnow');
  }
  if (window.wxSyncFcBar) window.wxSyncFcBar(); // the slider bar is shared with rain-forecast + wind
};
// ---- GPS interference (/gpsown - OUR OWN cells from the relayed ADS-B data) -----
// Live 12 h window, independent of the forecast slider. Banded by the relay
// (Wilson lower bound): grey = too few aircraft to judge, green < 2%, yellow
// 2-10%, red > 10% of aircraft in the cell reporting degraded GPS accuracy -
// measured at AIRCRAFT altitudes - jamming seen at 10 km often does not reach
// 120 m, which the legend says. Drawn below the zones; refreshed every 5 min
// while on (the relay snapshots the aircraft every 2 min and serves a new
// picture at most every 5 min).
var GJL = 'wxgj-layer', GJO = 'wxgj-line', gjTimer = null;

// The GPS layer shows either the LIVE rolling window (window.wxGjWin = 12|24 h)
// or one finished calendar day (window.wxGjDay = 'YYYY-MM-DD'). The picker (a
// day-calendar + the 12/24 switch) lives in a popup that opens from the date
// label in the legend; the map front stays clean. window.wxGjDays = the days
// the relay actually has (from the /gpsown response), so only those are clickable.
function gjBuildUrl(){
  if (window.wxGjDay) return window.wxGjUrl + '?day=' + window.wxGjDay;
  return window.wxGjUrl + (window.wxGjWin === 24 ? '?window=24' : '');
}
// i18n for the dynamic bits (this layer block is a separate scope from WXT/wxLang;
// like the NOTAM code it reads window.LANG + a small local dict). The static popup
// buttons (12ч/24ч/На живо) are localised via data-wxl by the main i18n pass.
var GJTX = { bg:{live:'На живо', hr:'ч', stamp:'данни към', load:'зареждане…', none:'няма архив'}, en:{live:'Live', hr:'h', stamp:'data as of', load:'loading…', none:'no history'} };
function gjL(){ return (window.LANG === 'en') ? 'en' : 'bg'; }
function gjLocale(){ return (window.LANG === 'en') ? 'en-GB' : 'bg-BG'; }

// the date label in the legend + the on-states of the popup controls
window.wxGjSyncLabel = function(){
  var x = GJTX[gjL()];
  var el = document.getElementById('wxgjdaylbl');
  if (el){
    if (window.wxGjDay){ var p = window.wxGjDay.split('-'); el.textContent = p[2] + '.' + p[1] + '.' + p[0]; }
    else { el.textContent = x.live + ' \u00b7 ' + window.wxGjWin + x.hr; }
  }
  var lv = document.getElementById('wxgjlive'); if (lv) lv.classList.toggle('on', !window.wxGjDay);
  document.querySelectorAll('#wxgjwin button').forEach(function(b){
    b.classList.toggle('on', !window.wxGjDay && +b.getAttribute('data-w') === window.wxGjWin);
  });
  var c = document.getElementById('wxgjcal'); if (c && !c.hidden) gjBuildCal();
};

function gjDraw(gj){
  var x = GJTX[gjL()];
  window.wxGjLoading = false;
  var _gb = document.getElementById('wxgj'); if (_gb) _gb.classList.remove('loading'); // data in -> stop the pulse
  window.wxGjDays = (gj && gj.days) || window.wxGjDays || [];
  // Auto-default = the newest READY finished day the relay reports. Not persisted,
  // so it advances by itself at the daily rollover; while the new day is still
  // being computed it simply keeps showing the last ready day (days[0] unchanged).
  if (window.wxGjAuto){
    var _d0 = window.wxGjDays[0];
    if (_d0 && window.wxGjDay !== _d0){ window.wxGjDay = _d0; gjFetch(); return; } // snap to the newest ready day, then draw that
    if (!_d0 && window.wxGjDay){ window.wxGjDay = ''; } // no finished day yet -> live
  }
  var src = map.getSource('wxgj');
  if (src){ src.setData(gj); }
  else {
    map.addSource('wxgj', {type: 'geojson', data: gj,
      attribution: 'GPS: own calculation \u00b7 data <a href="https://adsb.fi/" target="_blank" rel="noopener">adsb.fi</a> / <a href="https://www.adsb.lol/" target="_blank" rel="noopener">adsb.lol</a>'});
    // colour by the relay's band: grey (too few aircraft) and green (checked clean)
    // are FAINT washes so they never bury the zones; yellow and red stand out.
    var GJC = ['match', ['get', 'band'], 'green', '#5bb56a', 'yellow', '#e8c528', 'red', '#e03434', '#8a9098'];
    map.addLayer({id: GJL, type: 'fill', source: 'wxgj',
      paint: {'fill-color': GJC, 'fill-opacity': ['match', ['get', 'band'], 'yellow', 0.3, 'red', 0.4, 'grey', 0.16, 0.3]}}, wxGjBefore());
    map.addLayer({id: GJO, type: 'line', source: 'wxgj',
      paint: {'line-color': GJC, 'line-width': 1, 'line-opacity': ['match', ['get', 'band'], 'grey', 0.3, 0.55]}}, wxGjBefore());
  }
  // freshness stamp: only for the live window; a finished day is static, so blank
  var d = document.getElementById('wxgjdate');
  if (d){
    if (window.wxGjDay){ d.textContent = ''; }
    else { var g = gj && gj.generated ? new Date(gj.generated) : null;
      d.textContent = g ? (x.stamp + ' ' + ('0'+g.getHours()).slice(-2) + ':' + ('0'+g.getMinutes()).slice(-2)) : ''; }
  }
  window.wxGjSyncLabel();
}

// robust "run when the map can take a source/layer": whenReady's single once('idle')
// can be missed when the draw is gated behind a network fetch (the idle may have
// already fired), which left the restored layer + calendar empty until a manual
// toggle. Poll isStyleLoaded as a backstop; run exactly once.
function gjReady(fn){
  if (map.isStyleLoaded()){ fn(); return; }
  var done = false, run = function(){ if (done) return; done = true; fn(); };
  map.once('idle', run);
  var n = 0, t = setInterval(function(){ if (done || ++n > 60){ clearInterval(t); return; } if (map.isStyleLoaded()){ clearInterval(t); run(); } }, 100);
}
function gjFetch(){
  var wasDay = window.wxGjDay;
  window.wxGjLoading = true;
  var _gb = document.getElementById('wxgj'); if (_gb) _gb.classList.add('loading'); // pulse the 🛰 button while fetching
  var c = document.getElementById('wxgjcal'); if (c && !c.hidden) gjBuildCal(); // show "loading…" at once
  fetch(gjBuildUrl()).then(function(r){ if (!r.ok) throw new Error('gj ' + r.status); return r.json(); })
    .then(function(gj){ gjReady(function(){ if (window.wxGjOn) gjDraw(gj); }); })
    .catch(function(){
      window.wxGjLoading = false;
      if (!wasDay){ var _gb2 = document.getElementById('wxgj'); if (_gb2) _gb2.classList.remove('loading'); } // hard failure (not a day-fallback retry) -> stop the pulse
      // a day the relay can't give (e.g. the auto default right after midnight,
      // before the new day is computed) must not leave the layer/calendar empty:
      // re-request without a day. No ST write: auto keeps tracking (the live
      // response then snaps to the newest ready day), and a picked day was for
      // this visit only anyway.
      if (wasDay){ window.wxGjDay = ''; window.wxGjSyncLabel(); gjFetch(); gjResetTimer(); }
      else { var cc = document.getElementById('wxgjcal'); if (cc && !cc.hidden) gjBuildCal(); }
    });
}
function gjResetTimer(){
  clearInterval(gjTimer); gjTimer = null;
  if (!window.wxGjDay) gjTimer = setInterval(gjFetch, 300000); // live refreshes every 5 min; a finished day never changes
}
// apply a selection (day '' = live), persist, refetch, refresh the popup + label
function gjApply(day, win){
  window.wxGjDay = day || '';
  window.wxGjAuto = false; // any explicit choice (a day, or Live via win) stops auto-tracking
  if (win) window.wxGjWin = win;
  ST.set('gjDay', window.wxGjDay ? null : ''); ST.set('gjWin', window.wxGjWin); // Live is remembered; a past day is not (null = auto newest day next visit)
  window.wxGjSyncLabel();
  gjBuildCal();
  gjFetch(); gjResetTimer();
}

// ---- month calendar inside the popup ----
var gjCalM = null; // Date at the 1st (UTC) of the displayed month
function gjMonKey(dt){ return dt.getUTCFullYear() + '-' + ('0'+(dt.getUTCMonth()+1)).slice(-2); }
function gjBuildCal(){
  var grid = document.getElementById('wxgjgrid'); if (!grid) return;
  var days = window.wxGjDays || [];
  if (!gjCalM){
    var base = window.wxGjDay || days[0] || new Date().toISOString().slice(0,10);
    var bp = base.split('-'); gjCalM = new Date(Date.UTC(+bp[0], +bp[1]-1, 1));
  }
  var loc = gjLocale(), y = gjCalM.getUTCFullYear(), mo = gjCalM.getUTCMonth();
  var first = new Date(Date.UTC(y, mo, 1));
  var title = first.toLocaleDateString(loc, {month:'long', year:'numeric', timeZone:'UTC'});
  var startDow = (first.getUTCDay() + 6) % 7;              // Monday-first
  var ndays = new Date(Date.UTC(y, mo+1, 0)).getUTCDate();
  var minM = days.length ? days[days.length-1].slice(0,7) : gjMonKey(gjCalM);
  var maxM = days.length ? days[0].slice(0,7) : gjMonKey(gjCalM);
  var curM = gjMonKey(gjCalM);
  var wd = (window.LANG === 'en') ? ['Mo','Tu','We','Th','Fr','Sa','Su'] : ['\u043f\u043d','\u0432\u0442','\u0441\u0440','\u0447\u0442','\u043f\u0442','\u0441\u0431','\u043d\u0434'];
  var h = '<div id="wxgjcalhd"><button type="button" id="wxgjprev">\u2039</button><span>' + title + '</span><button type="button" id="wxgjnext">\u203a</button></div><table><thead><tr>';
  for (var i=0; i<7; i++) h += '<th>' + wd[i] + '</th>';
  h += '</tr></thead><tbody><tr>';
  var col = 0, k;
  for (k=0; k<startDow; k++){ h += '<td></td>'; col++; }
  for (var dn=1; dn<=ndays; dn++){
    var ds = y + '-' + ('0'+(mo+1)).slice(-2) + '-' + ('0'+dn).slice(-2);
    var av = days.indexOf(ds) >= 0, sel = ds === window.wxGjDay;
    var cls = (av ? 'av' : '') + (sel ? ' sel' : '');
    h += '<td><button type="button" class="' + cls + '"' + (av ? ' data-d="'+ds+'"' : ' disabled') + '>' + dn + '</button></td>';
    if (++col === 7){ h += '</tr><tr>'; col = 0; }
  }
  while (col && col < 7){ h += '<td></td>'; col++; }
  h += '</tr></tbody></table>';
  if (!days.length){ var xx = GJTX[gjL()]; h += '<div class="gjstat">' + (window.wxGjLoading ? xx.load : xx.none) + '</div>'; } // no clickable days yet: loading vs genuinely empty
  grid.innerHTML = h;
  var pv = document.getElementById('wxgjprev'), nx = document.getElementById('wxgjnext');
  if (pv){ pv.disabled = curM <= minM; pv.onclick = function(){ gjCalM = new Date(Date.UTC(y, mo-1, 1)); gjBuildCal(); }; }
  if (nx){ nx.disabled = curM >= maxM; nx.onclick = function(){ gjCalM = new Date(Date.UTC(y, mo+1, 1)); gjBuildCal(); }; }
  grid.querySelectorAll('button.av').forEach(function(b){
    b.onclick = function(){ gjApply(this.getAttribute('data-d')); }; // stay open; closes only on click outside
  });
}
function gjOpenCal(){ var c = document.getElementById('wxgjcal'); if (!c) return; gjCalM = null; gjBuildCal(); c.hidden = false; }
function gjCloseCal(){ var c = document.getElementById('wxgjcal'); if (c) c.hidden = true; }
function gjToggleCal(){ var c = document.getElementById('wxgjcal'); if (!c) return; if (c.hidden) gjOpenCal(); else gjCloseCal(); }

window.wxSetGj = function(on){ window.wxGjOn = on;
  var lg = document.getElementById('wxgjlegend');
  if (on){
    if (lg) lg.hidden = false;
    window.wxGjSyncLabel();
    gjFetch(); gjResetTimer();
  } else {
    clearInterval(gjTimer); gjTimer = null;
    gjCloseCal();
    var _gb = document.getElementById('wxgj'); if (_gb) _gb.classList.remove('loading');
    if (lg) lg.hidden = true;
    if (map.getLayer(GJL)) map.removeLayer(GJL);
    if (map.getLayer(GJO)) map.removeLayer(GJO);
    if (map.getSource('wxgj')) map.removeSource('wxgj');
  }
};

// wire the popup controls once (the legend HTML is already in the DOM here)
(function(){
  var hdr = document.getElementById('wxgjday');
  if (hdr) hdr.onclick = function(e){ e.stopPropagation(); gjToggleCal(); };
  var lv = document.getElementById('wxgjlive');
  if (lv) lv.onclick = function(){ gjApply('', window.wxGjWin); };   // back to live, keep the window
  document.querySelectorAll('#wxgjwin button').forEach(function(b){
    b.onclick = function(){ gjApply('', +this.getAttribute('data-w')); }; // choosing a window means "live, that window"
  });
  // close only on a click truly OUTSIDE. Use pointerdown (fires BEFORE the click
  // that rebuilds the grid) so picking a day - which replaces the button node -
  // isn't misread as an outside click once the old node is detached.
  document.addEventListener('pointerdown', function(e){
    var c = document.getElementById('wxgjcal'); if (!c || c.hidden) return;
    var hd = document.getElementById('wxgjday');
    if (!c.contains(e.target) && !(hd && hd.contains(e.target))) gjCloseCal();
  });
})();
// ---- Airspace (OpenAIP via the relay): controlled (blue) + special (red/pink) ----
// Outlines ONLY (no fill), same weight as our zone outlines, BELOW the zones. Two
// independent menu toggles (controlled / special-use). Click shows name/type/limits,
// but a click on one of OUR zones wins (this pops only when no zone is under it).
// A zone the CAA ALSO publishes, under the same name, in its public layer of BULATSA zones
// (/actzones, see the activated-zones block) takes the CAA's contour + heights while the
// CAA lists it as active (owner 11.10: same name -> the official, current source; e.g. LBR1
// cut at the border, LBR7 2.5 km). Not published, not started yet, or CAA data older than
// 3 h / unavailable -> the OpenAIP shape stays (airGvaData).
window.wxAirUrl = 'https://full-narwhal-4777.martinovem.deno.net/airspace';
var AIR_CTRL_T = [4,5,6,7,13,14,25,26,36]; // controlled types (rest = special-use)
var AIR_CTRL_F = ['in',['get','t'],['literal',AIR_CTRL_T]], AIR_SPEC_F = ['!', AIR_CTRL_F];
var AIR_TL = {1:{bg:'Ограничена',en:'Restricted'},2:{bg:'Опасна',en:'Danger'},3:{bg:'Забранена',en:'Prohibited'},
  4:{bg:'CTR — контролна зона',en:'CTR'},5:{bg:'TMZ',en:'TMZ'},6:{bg:'RMZ',en:'RMZ'},7:{bg:'TMA',en:'TMA'},
  8:{bg:'Военна (TRA)',en:'Military (TRA)'},9:{bg:'Военна (TSA)',en:'Military (TSA)'},13:{bg:'ATZ',en:'ATZ'},
  14:{bg:'MATZ',en:'MATZ'},25:{bg:'MTA',en:'MTA'},26:{bg:'CTA',en:'CTA'},36:{bg:'MCTR',en:'MCTR'}};
function airEnsure(cb){
  if (map.getSource('wxair')){ cb(); return; }
  fetch(window.wxAirUrl).then(function(r){ if (!r.ok) throw 0; return r.json(); }).then(function(gj){
    window._airRaw = airMergeAip(gj);
    if (!map.getSource('wxair')){ var d = airGvaData(); window._airGvaSig = d.sig;
      map.addSource('wxair', {type:'geojson', data:d.fc, generateId:true,
        attribution:'Airspace &copy; <a href="https://www.openaip.net/" target="_blank" rel="noopener">openAIP</a> (CC BY-NC 4.0); BULATSA zone contours: <a href="https://uas.caa.bg/" target="_blank" rel="noopener">CAA uas.caa.bg</a>; zones missing in openAIP: AIP of the Republic of Bulgaria'}); }
    cb();
  }).catch(function(){ wxBtnIdle('cbAirC'); wxBtnIdle('cbAirS'); // relay/source down: draw nothing rather than something stale...
    clearTimeout(window._airRt); window._airRt = setTimeout(function(){ // ...then re-attempt the FETCH (never draws stale); stops once toggled off
      if (window.wxAirCOn) window.wxSetAirC(true); if (window.wxAirSOn) window.wxSetAirS(true); }, 15000); });
}
// The AIP structures OpenAIP does not have (tools/aip_extra.py, inlined as AIP_EXTRA) join the
// OpenAIP picture; ONE zone per name - an AIP entry wins over an OpenAIP zone of the same name
// (owner 21.10: the official source). The CAA swap (airGvaData) then applies to both alike.
function airMergeAip(gj){
  var ours = (typeof AIP_EXTRA !== 'undefined' && AIP_EXTRA.features) || [], seen = {}, key = function(f){
    return String(((f && f.properties) || {}).n || '').replace(/\s+/g, '').toUpperCase(); };
  ours.forEach(function(f){ seen[key(f)] = 1; });
  return {type:'FeatureCollection', features:((gj && gj.features) || []).filter(function(f){ return !seen[key(f)]; }).concat(ours)};
}
function airDropSourceMaybe(){ if (!map.getLayer('air-ctrl') && !map.getLayer('air-spec') && map.getSource('wxair')){ map.removeSource('wxair'); window._airGvaSig = null; } } // each group's labels are removed with its outline
// The OpenAIP picture with the CAA's contour + heights in place of the same-name zones the
// CAA lists as ACTIVE right now (the activated layer's own test: window started, not ended);
// names compared case-insensitively ("CHAIKA MATZ" = "Chaika MATZ"). sig = the swapped part.
function airGvaData(){
  var raw = window._airRaw || {type:'FeatureCollection', features:[]}, by = {}, now = Date.now(), sw = [];
  if (window._actDataAt && now - window._actDataAt <= ACT_DROP_MIN * 60000) (window._actRaw || []).forEach(function(f){
    var p = (f && f.properties) || {}, s = Date.parse(p.s), e = Date.parse(p.e);
    if (f && f.geometry && p.n && !(e <= now) && !(s > now)) by[String(p.n).toUpperCase()] = f; });
  var fc = {type:'FeatureCollection', features:(raw.features || []).map(function(f){
    var g = by[String((f.properties || {}).n || '').toUpperCase()]; if (!g) return f;
    var q = g.properties || {}, p = {}, k; for (k in f.properties) p[k] = f.properties[k];
    p.lo = q.lo || p.lo; p.up = q.up || p.up; p.gva = 1;
    var o = {type:'Feature', geometry:g.geometry, properties:p}; sw.push(o); return o; })};
  return {fc:fc, sig:JSON.stringify(sw)};
}
// re-apply on the live source when the CAA data or a window edge changes the swap
function airGvaApply(){
  var src = map.getSource('wxair'); if (!src || !window._airRaw) return;
  var d = airGvaData(); if (d.sig === window._airGvaSig) return;
  window._airGvaSig = d.sig; src.setData(d.fc);
}
// the CAA data the swap needs - shared with the activated layer, fetched at most every 10 min
function airGvaNeed(){
  if (window._actRaw && Date.now() - (window._actFetchAt || 0) < 600000){ airGvaApply(); return; }
  actFetch(airGvaApply);
}
// while an airspace group is on: window edges every minute (+ the 10-min refetch, done by the
// activated layer's own timer when that layer is on)
function airGvaTick(on){
  if (on && !window._airGvaT) window._airGvaT = setInterval(function(){ if (window.wxActOn) airGvaApply(); else airGvaNeed(); }, 60000);
  if (!on && window._airGvaT){ clearInterval(window._airGvaT); window._airGvaT = null; }
}
// Each airspace group carries its OWN name labels, added/removed WITH its outline (no
// separate "labels" toggle). MapLibre's collision detection thins overlapping labels out
// by zoom on its own, so it never becomes a wall of text. Text coloured like the outline.
var AIR_LBL_LAYOUT = {'text-field':['get','n'], 'text-size':11, 'text-font':['Noto Sans Regular'], 'text-max-width':9};
var AIR_LW = ['case', ['boolean', ['feature-state', 'sel'], false], 3.8, 1.3]; // clicked airspace outline thickens ~3x (feature-state 'sel')
// filter of a group (outlines AND labels), minus the zones the activated-zones layer draws as
// ACTIVE right now (window._actSup, filled while that layer is on): each such zone is drawn
// once, by that layer, and its label - so its popup entry, reachable only via the label -
// gives way to the activated zone's own label + heights; back when it ends / the layer is off
window.wxAirLblFilter = function(ctrl){
  var base = ctrl ? AIR_CTRL_F : AIR_SPEC_F, sup = (window._actSup || []).map(function(n){ return String(n).toUpperCase(); });
  return sup.length ? ['all', base, ['!', ['in', ['upcase', ['to-string', ['get','n']]], ['literal', sup]]]] : base; };
window.wxSetAirC = function(on){ window.wxAirCOn = on;
  if (on){ wxBtnBusy('cbAirC', 'wxair'); airEnsure(function(){ if (!window.wxAirCOn) return;
    if (!map.getLayer('air-ctrl')) map.addLayer({id:'air-ctrl', type:'line', source:'wxair',
      filter:window.wxAirLblFilter(true),
      paint:{'line-color':'#2b6cb0','line-width':AIR_LW,'line-opacity':0.9}}, wxZoneAnchor()); // faint: context, not a dominant border
    if (!map.getLayer('air-ctrl-labels')) map.addLayer({id:'air-ctrl-labels', type:'symbol', source:'wxair',
      filter:window.wxAirLblFilter(true), layout:AIR_LBL_LAYOUT,
      paint:{'text-color':'#2b6cb0','text-halo-color':'rgba(255,255,255,0.9)','text-halo-width':1.4}}, wxZoneAnchor());
    airGvaNeed(); airGvaTick(true); }); }
  else { wxBtnIdle('cbAirC'); ['air-ctrl','air-ctrl-labels'].forEach(function(id){ if (map.getLayer(id)) map.removeLayer(id); }); airDropSourceMaybe();
    airGvaTick(!!window.wxAirSOn);
    if (window.wxPopupPrune) window.wxPopupPrune(); } // its airspace leaves an open popup too
};
window.wxSetAirS = function(on){ window.wxAirSOn = on;
  if (on){ wxBtnBusy('cbAirS', 'wxair'); airEnsure(function(){ if (!window.wxAirSOn) return;
    if (!map.getLayer('air-spec')) map.addLayer({id:'air-spec', type:'line', source:'wxair',
      filter:window.wxAirLblFilter(false),
      // red for Prohibited(3)/Restricted(1)/Danger(2); magenta for military TRA/TSA(8/9)
      paint:{'line-color':['case',['in',['get','t'],['literal',[8,9]]],'#d81fbf','#d0202a'],'line-width':AIR_LW,'line-opacity':0.9}}, wxZoneAnchor());
    if (!map.getLayer('air-spec-labels')) map.addLayer({id:'air-spec-labels', type:'symbol', source:'wxair',
      filter:window.wxAirLblFilter(false), layout:AIR_LBL_LAYOUT,
      paint:{'text-color':['case',['in',['get','t'],['literal',[8,9]]],'#d81fbf','#d0202a'],'text-halo-color':'rgba(255,255,255,0.9)','text-halo-width':1.4}}, wxZoneAnchor());
    airGvaNeed(); airGvaTick(true); }); }
  else { wxBtnIdle('cbAirS'); ['air-spec','air-spec-labels'].forEach(function(id){ if (map.getLayer(id)) map.removeLayer(id); }); airDropSourceMaybe();
    airGvaTick(!!window.wxAirCOn);
    if (window.wxPopupPrune) window.wxPopupPrune(); } // its airspace leaves an open popup too
};
(function(){
  // The airspace NAME feeds the SHARED overlapping-feature chooser (make_3d.py:
  // openZones/listHTML/detailHTML) alongside drone-zones + NOTAMs. Here we expose the
  // list/detail renderers + the 'thicken the shown outline' highlight it calls.
  window.wxAirColor = function(p){ return (AIR_CTRL_T.indexOf(p.t) >= 0) ? '#2b6cb0' : ((p.t === 8 || p.t === 9) ? '#d81fbf' : '#d0202a'); };
  window.wxAirName = function(p){ return p.n || ''; };
  window.wxAirSub = function(p){ var L = (window.LANG || 'bg'); return (AIR_TL[p.t] && AIR_TL[p.t][L]) || ('#' + p.t); };
  window.wxAirDetail = function(p){ var L = (window.LANG || 'bg');
    return '<b>' + esc(p.n) + '</b><br>' + window.wxAirSub(p) + '<br>' + esc(p.lo) + ' – ' + esc(p.up) +
      (p.nx ? ('<br><small>' + (L === 'en' ? 'by NOTAM' : 'по NOTAM') + '</small>') : '') +
      // the AIP's anti-hail danger areas: its remark on the season and the activation (owner-approved text, 22.10)
      ((typeof AIP_HAIL !== 'undefined' && AIP_HAIL.indexOf(String(p.n || '').replace(/\s+/g, '').toUpperCase()) >= 0) ? '<br><small>' + (L === 'en'
        ? 'Per the AIP of the Republic of Bulgaria (ENR 5.1): anti-hail activity, season 1 Apr – 30 Oct. The time of activity is not announced in advance. The season dates are announced by NOTAM. When active, overflying is permitted at or above FL 240.'
        : 'По AIP на Република България (ENR 5.1): противоградова защита, сезон 01.04 – 30.10. Кога се активира, не се обявява предварително. Датите на сезона се обявяват с NOTAM. При активиране прелитането е разрешено на или над FL 240.') + '</small>' : '') +
      // where the shape comes from: the CAA's contour + heights swapped in (airGvaData), else the
      // AIP (an entry of tools/aip_extra.py, with its page + amendment), else OpenAIP (owner 21.10)
      '<br><small>' + (+p.gva === 1 ? (L === 'en' ? 'Contour and heights: CAA (uas.caa.bg)' : 'Контур и височини: ГД ГВА (uas.caa.bg)')
        : p.aip ? (L === 'en' ? 'Source: AIP of the Republic of Bulgaria (' : 'Източник: AIP на Република България (') + esc(p.aip) + ')'
        : (L === 'en' ? 'Source: OpenAIP' : 'Източник: OpenAIP')) + '</small>'; };
  // thicken the CLICKED airspace outline (feature-state 'sel' -> AIR_LW); one at a time
  window._airSel = null;
  window.wxAirSelect = function(aid){
    if (window._airSel != null && map.getSource('wxair')) map.setFeatureState({source:'wxair', id:window._airSel}, {sel:false});
    window._airSel = null;
    if (aid != null && map.getSource('wxair')){ window._airSel = aid; map.setFeatureState({source:'wxair', id:aid}, {sel:true}); } };
  // hover cue: the NAME is the click target (the thin outline is NOT clickable)
  ['air-ctrl-labels','air-spec-labels'].forEach(function(id){
    map.on('mouseenter', id, function(){ map.getCanvas().style.cursor = 'pointer'; });
    map.on('mouseleave', id, function(){ map.getCanvas().style.cursor = ''; });
  });
})();
// ---- Activated zones (/actzones relay over the CAA's public layer of BULATSA zones):
// EVERY zone the CAA publishes there is drawn - if the CAA (a copy of B-FLIP's
// "Activated SUA") lists it, it IS active; no thresholds of our own (owner 11.10). Only
// the data changes the picture: deleted ones never arrive (the relay drops them), a zone
// vanishes at its own end time, and one whose window has not started yet is "upcoming".
// Each has its time window (the permanent ones run to 2036) and the heights of THIS
// activation. Drawn ABOVE the zones in the special-use colours (red P/R/D, magenta
// TRA/TSA): a normal-weight solid edge (dashed = upcoming), a band along the inside of
// the edge, a ~20% fill and a label "<name> / АКТИВНА до <end>" (no end given: just
// "АКТИВНА"). Thickness stays the CLICK highlight, as for the airspace outlines. While a
// zone is active, its OpenAIP outline + label (and so its popup entry) are hidden: one
// zone, drawn once, one set of heights; they return when the activation ends. The same
// data also gives the airspace layer its CAA contours (airGvaData, above).
// Honest freshness: data older than 60 min raises a banner; older than 3 h draws nothing
// and says so - an empty map must never read as "nothing is active".
window.wxActUrl = 'https://full-narwhal-4777.martinovem.deno.net/actzones';
var ACT_STALE_MIN = 60, ACT_DROP_MIN = 180;
var ACT_COL = ['case', ['==', ['get','mil'], 1], '#d81fbf', '#d0202a'];
var ACT_SEL = ['boolean', ['feature-state', 'sel'], false];
window._actRaw = null; window._actDataAt = 0; window._actFail = false; window._actSup = []; window._actSupKey = ''; window._actSig = '';
// kind from the ICAO designator (the CAA layer types them all "Зона от РВД"); codes = AIR_TL's
function actEn(){ return (window.LANG || 'bg') === 'en'; } // page language (as the NOTAM layer reads it)
function actKind(n){ n = String(n || '').toUpperCase();
  return /TRA/.test(n) ? 8 : /TSA/.test(n) ? 9 : /^LBD/.test(n) ? 2 : /^LBR/.test(n) ? 1 : /^LBP/.test(n) ? 3 : /MATZ/.test(n) ? 14 : 0; }
function actKindName(p, en){ var k = +p.k; return (AIR_TL[k] && AIR_TL[k][en ? 'en' : 'bg']) || p.zt || (en ? 'BULATSA zone' : 'Зона от РВД'); }
// times in BULGARIAN time (the airspace's own), whatever the visitor's device zone
var ACT_TZ = (function(){ try { return new Intl.DateTimeFormat('en-GB', {timeZone:'Europe/Sofia', year:'numeric', month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit', hour12:false}); } catch(e){ return null; } })();
function actParts(t){ var d = new Date(t), o = {}, p = function(n){ return (n < 10 ? '0' : '') + n; };
  if (ACT_TZ) ACT_TZ.formatToParts(d).forEach(function(x){ o[x.type] = x.value; });
  else o = {day:p(d.getDate()), month:p(d.getMonth()+1), year:String(d.getFullYear()), hour:p(d.getHours()), minute:p(d.getMinutes())};
  return {d: o.day + '.' + o.month, y: o.year, hm: (o.hour === '24' ? '00' : o.hour) + ':' + o.minute, k: o.year + o.month + o.day}; }
// today: time only; another day: + the date; another year (the permanent zones' 2036): + the year
function actWhen(t){ var a = actParts(t), n = actParts(Date.now());
  return a.k === n.k ? a.hm : (actDay(a, n) + ' ' + a.hm); }
function actWhenFull(t){ var a = actParts(t); return actDay(a, actParts(Date.now())) + ' ' + a.hm; }
function actDay(a, n){ return a.y === n.y ? a.d : (a.d + '.' + a.y); }
function actHm(t){ var d = new Date(t), p = function(n){ return (n < 10 ? '0' : '') + n; }; return p(d.getHours()) + ':' + p(d.getMinutes()); }
function actLabel(n, fut, s, e){ var en = actEn();
  return n + '\n' + (fut ? (en ? 'UPCOMING from ' : 'ПРЕДСТОИ от ') + actWhen(s) : actUntil(e, en)); }
// "АКТИВНА до <end>", or just "АКТИВНА" when the CAA gave no end
function actUntil(e, en){ return isNaN(e) ? (en ? 'ACTIVE' : 'АКТИВНА') : (en ? 'ACTIVE until ' : 'АКТИВНА до ') + actWhen(e); }
// the drawable picture NOW: every zone whose window has not ended, while the data is < 3 h old
function actBuild(){
  var now = Date.now(), out = [], sup = [], next = Infinity;
  var fresh = !!(window._actDataAt && now - window._actDataAt <= ACT_DROP_MIN * 60000);
  if (fresh) (window._actRaw || []).forEach(function(f){
    var p = (f && f.properties) || {}, s = Date.parse(p.s), e = Date.parse(p.e);
    if (!f || !f.geometry || e <= now) return; // nothing to draw / its window has ended (no end given = NaN: stays)
    var n = p.n || p.idf || '?', fut = s > now ? 1 : 0, k = actKind(n), edge = fut ? s : e;
    if (edge < next) next = edge;
    out.push({type:'Feature', geometry:f.geometry, properties:{key:n + '|' + (p.s || ''), n:n, zt:p.zt, lo:p.lo, up:p.up, s:p.s, e:p.e, rm:p.rm, src:p.src,
      k:k, mil:(k === 8 || k === 9) ? 1 : 0, fut:fut, lbl:actLabel(n, fut, s, e)}});
    if (!fut) sup.push(n);
  });
  return {gj:{type:'FeatureCollection', features:out}, sup:sup, next:next};
}
// hide/restore the OpenAIP outlines + labels of the zones active right now (see wxAirLblFilter)
function actSup(list){ var key = list.slice().sort().join('|'); if (key === window._actSupKey) return;
  window._actSupKey = key; window._actSup = list.slice();
  ['air-ctrl','air-ctrl-labels','air-spec','air-spec-labels'].forEach(function(id){ if (map.getLayer(id)) map.setFilter(id, window.wxAirLblFilter(id.indexOf('air-ctrl') === 0)); }); }
// redraw the picture (data, suppression, stamp/banner); called on every fetch, every
// minute, and exactly when the next window starts or ends
function actPaint(){
  var b = actBuild(), src = map.getSource('wxact');
  if (src){ var sig = window._actDataAt + '|' + (window.LANG || 'bg') + '|' + JSON.stringify(b.gj.features.map(function(f){ return f.properties; }));
    if (sig !== window._actSig){ window._actSig = sig; src.setData(b.gj); } }
  actSup(window.wxActOn && src ? b.sup : []);
  clearTimeout(window._actEdge);
  if (window.wxActOn && b.next - Date.now() < 61000) window._actEdge = setTimeout(actPaint, Math.max(500, b.next - Date.now() + 500));
  actFreshPaint();
  airGvaApply(); // the airspace layer's CAA contours follow the same data + window edges
}
function actFreshPaint(){
  var el = document.getElementById('wxactfresh'), bn = document.getElementById('wxactstale');
  var en = actEn(), at = window._actDataAt, on = !!window.wxActOn, age = at ? Date.now() - at : 0, msg = '';
  if (el){ if (on && at){ el.style.display = ''; el.textContent = (en ? 'Activated zones: data as of ' : 'Активирани зони: данни към ') + actHm(at); } else el.style.display = 'none'; }
  if (on && at && age > ACT_DROP_MIN * 60000) msg = en ? '⚠ No current data on activated zones (last: ' + actHm(at) + ') – none are shown'
                                                       : '⚠ Няма актуални данни за активираните зони (последни: ' + actHm(at) + ') – не се показват';
  else if (on && at && age > ACT_STALE_MIN * 60000) msg = en ? '⚠ Activated-zone data is ' + Math.round(age / 60000) + ' min old – may be incomplete'
                                                            : '⚠ Данните за активираните зони са от преди ' + Math.round(age / 60000) + ' мин – може да не са пълни';
  else if (on && !at && window._actFail) msg = en ? '⚠ No data on activated zones right now' : '⚠ В момента няма данни за активираните зони';
  if (msg && !bn){ bn = document.createElement('div'); bn.id = 'wxactstale';
    bn.style.cssText = 'position:absolute;left:50%;transform:translateX(-50%);bottom:84px;z-index:7;' +
      'background:#b71c1c;color:#fff;font:12px/1.4 sans-serif;padding:6px 12px;border-radius:8px;' +
      'box-shadow:0 1px 6px rgba(0,0,0,.35);pointer-events:none;max-width:86vw;text-align:center';
    map.getContainer().appendChild(bn); }
  if (bn){ if (msg){ bn.textContent = msg; bn.style.display = ''; } else bn.style.display = 'none'; }
}
// ONE fetch of /actzones; the picture's true age comes from the relay's X-Act-Age-Ms
function actFetch(ok){
  window._actFetchAt = Date.now(); // when WE last asked (the airspace swap refetches by this, not by the data's age)
  fetch(window.wxActUrl, {cache: 'no-store'}).then(function(r){ if (!r.ok) throw 0;
    var age = parseInt(r.headers.get('X-Act-Age-Ms') || '0', 10) || 0;
    return r.json().then(function(gj){ return {gj: gj, age: age}; });
  }).then(function(d){
    window._actRaw = (d.gj && d.gj.features) || []; window._actDataAt = Date.now() - d.age; window._actFail = false;
    ok();
  }).catch(function(){ window._actFail = true; wxBtnIdle('cbAct'); actPaint(); }); // whatever is drawn keeps AGEING honestly
}
function actEnsure(cb){
  if (map.getSource('wxact')){ cb(); return; }
  actFetch(function(){
    if (!map.getSource('wxact')) map.addSource('wxact', {type:'geojson', data:{type:'FeatureCollection', features:[]}, promoteId:'key',
      attribution:'Activated zones: BULATSA via <a href="https://uas.caa.bg/" target="_blank" rel="noopener">CAA uas.caa.bg</a>'});
    cb();
  });
}
function actRefresh(){
  if (!window.wxActOn) return;
  if (!map.getSource('wxact')){ window.wxSetAct(true); return; } // a failed first load left no source: re-attempt on this tick
  actFetch(actPaint);
}
window.wxSetAct = function(on){ window.wxActOn = on;
  // minute timer: expiry/upcoming + stamp/banner every minute, a refetch every 10th
  if (on && !window._actTick){ window._actTickN = 0;
    window._actTick = setInterval(function(){ window._actTickN++; if (window._actTickN % 10 === 0) actRefresh(); else actPaint(); }, 60000); }
  if (!on && window._actTick){ clearInterval(window._actTick); window._actTick = null; }
  if (on){ wxBtnBusy('cbAct', 'wxact'); actEnsure(function(){ if (!window.wxActOn) return;
    // no beforeId = top of the stack = ABOVE the zones, like the NOTAM layer
    if (!map.getLayer('act-fill')) map.addLayer({id:'act-fill', type:'fill', source:'wxact',
      paint:{'fill-color':ACT_COL, 'fill-opacity':['case',['==',['get','fut'],1],0.06,0.2]}});
    // the band along the INSIDE of the edge (positive offset = inset on polygons)
    if (!map.getLayer('act-band')) map.addLayer({id:'act-band', type:'line', source:'wxact', layout:{'line-join':'round'},
      paint:{'line-color':ACT_COL, 'line-width':7, 'line-offset':3.5, 'line-blur':0.5, 'line-opacity':['case',['==',['get','fut'],1],0.15,0.4]}});
    if (!map.getLayer('act-line')) map.addLayer({id:'act-line', type:'line', source:'wxact', filter:['==',['get','fut'],0],
      paint:{'line-color':ACT_COL, 'line-width':['case',ACT_SEL,4.4,2], 'line-opacity':1}});
    if (!map.getLayer('act-line-fut')) map.addLayer({id:'act-line-fut', type:'line', source:'wxact', filter:['==',['get','fut'],1],
      paint:{'line-color':ACT_COL, 'line-width':['case',ACT_SEL,3.6,1.6], 'line-opacity':0.75, 'line-dasharray':[3,2]}});
    if (!map.getLayer('act-label')) map.addLayer({id:'act-label', type:'symbol', source:'wxact',
      layout:{'text-field':['get','lbl'], 'text-size':11.5, 'text-font':['Noto Sans Regular'], 'text-max-width':20},
      paint:{'text-color':ACT_COL, 'text-halo-color':'rgba(255,255,255,0.92)', 'text-halo-width':1.6}});
    window._actSig = ''; actPaint(); }); }
  else { wxBtnIdle('cbAct'); clearTimeout(window._actEdge);
    ['act-fill','act-band','act-line','act-line-fut','act-label'].forEach(function(id){ if (map.getLayer(id)) map.removeLayer(id); });
    if (map.getSource('wxact')) map.removeSource('wxact');
    window._actSel = null; actSup([]); // OpenAIP labels back
    if (window.wxPopupPrune) window.wxPopupPrune(); // its zones leave an open popup too
    actFreshPaint(); } // hides the stamp + banner
};
// helpers for the SHARED click chooser in make_3d (same list as zones / NOTAM / airspace)
window.wxActColor = function(p){ return +p.mil === 1 ? '#d81fbf' : '#d0202a'; };
window.wxActName = function(p){ return p.n || ''; };
window.wxActSub = function(p){ var en = actEn();
  return actKindName(p, en) + ' · ' + (+p.fut === 1 ? (en ? 'upcoming from ' : 'предстои от ') + actWhen(Date.parse(p.s))
                                                   : actUntil(Date.parse(p.e), en)); };
window.wxActDetail = function(p){ var en = actEn(), s = Date.parse(p.s), e = Date.parse(p.e);
  // UTC, with the year when it is not this year (the permanent zones run to 2036)
  var z = function(t){ var d = new Date(t), q = function(n){ return (n < 10 ? '0' : '') + n; };
    return q(d.getUTCDate()) + '.' + q(d.getUTCMonth() + 1) + (d.getUTCFullYear() !== new Date().getUTCFullYear() ? '.' + d.getUTCFullYear() : '') +
      ' ' + q(d.getUTCHours()) + ':' + q(d.getUTCMinutes()) + 'Z'; };
  var none = en ? 'not given' : 'не е посочен';
  var per = (isNaN(s) && isNaN(e)) ? (en ? 'not given by the CAA' : 'не е посочен от ГВА')
    : '<b>' + (isNaN(s) ? none : actWhenFull(s)) + ' – ' + (isNaN(e) ? none : actWhenFull(e)) + '</b> ' +
      '<small>(' + (en ? 'Bulgarian time; ' : 'българско време; ') + (isNaN(s) ? '…' : z(s)) + ' – ' + (isNaN(e) ? '…' : z(e)) + ')</small>';
  var hts = (p.lo && p.up) ? (esc(p.lo) + ' – ' + esc(p.up)) : (en ? 'no data' : 'няма данни');
  return '<b>' + esc(p.n) + '</b> <span class="ptype">' + esc(actKindName(p, en)) + '</span><br>' +
    (+p.fut === 1 ? (en ? 'Upcoming activation' : 'Предстоящо активиране') : '<b>' + (en ? 'ACTIVATED now' : 'АКТИВИРАНА сега') + '</b>') +
    '<br>' + (en ? 'Window: ' : 'Период: ') + per +
    '<br>' + (en ? 'Heights of this activation: ' : 'Височини при това активиране: ') + '<b>' + hts + '</b>' +
    // the CAA's own texts, verbatim (only when present)
    (p.rm ? ('<br>' + (en ? 'CAA remark: ' : 'Бележка (ГВА): ') + esc(p.rm)) : '') +
    (p.src ? ('<br><small>' + (en ? 'CAA source field: ' : 'Източник (ГВА): ') + esc(p.src) + '</small>') : '') +
    (p.zt ? ('<br><small>' + (en ? 'CAA type: ' : 'Тип по ГВА: ') + esc(p.zt) + '</small>') : '') +
    '<br><small>' + (en ? 'Data: BULATSA via the ' : 'Данни: БУЛАТСА чрез ') +
    '<a href="https://uas.caa.bg/" target="_blank" rel="noopener">' + (en ? 'CAA (uas.caa.bg)' : 'ГД ГВА (uas.caa.bg)') + '</a>' +
    (window._actDataAt ? (' · ' + (en ? 'as of ' : 'към ') + actHm(window._actDataAt)) : '') + '</small>'; };
// thicken the CLICKED activated zone's edge (feature-state 'sel'); one at a time
window._actSel = null;
window.wxActSelect = function(key){
  if (window._actSel != null && map.getSource('wxact')) map.setFeatureState({source:'wxact', id:window._actSel}, {sel:false});
  window._actSel = null;
  if (key != null && map.getSource('wxact')){ window._actSel = key; map.setFeatureState({source:'wxact', id:key}, {sel:true}); } };
// a BG/EN switch re-labels the zones on the map
(window.wxLangRefresh = window.wxLangRefresh || []).push(function(){ window._actSig = ''; if (window.wxActOn) actPaint(); });
['act-fill','act-label'].forEach(function(id){
  map.on('mouseenter', id, function(){ map.getCanvas().style.cursor = 'pointer'; });
  map.on('mouseleave', id, function(){ map.getCanvas().style.cursor = ''; });
});
// ---- Natura 2000 (owner 16.10): an INFORMATION layer, not a drone zone, Bulgaria only. The EEA's
// boundaries (CC BY 4.0, simplified) + the MOEW's Bulgarian names from the static natura.json (built
// by tools/make_natura.py, refreshed about once a year). MapLibre loads the file itself on the
// first switch-on (parsed in its worker, not on the page's thread). Green - never the zones'
// red / orange / yellow: a faint fill + a fine hatch + a dark outline, under the airspace and
// the zones, above GPS + weather (natFloor in the stack helpers). Its sites join the shared
// click chooser (items tagged _nat) after the zones, NOTAMs and activated zones.
window.wxNatUrl = 'natura.json';
var NAT_PUB = '__NATPUB__', NAT_COL = '#2e7d32', NAT_EDGE = '#1b5e20', NAT_SEL = ['boolean', ['feature-state', 'sel'], false];
var NAT_TYPE = {bg: {A: 'за птиците', B: 'за местообитанията', C: 'за птиците и местообитанията'},
                en: {A: 'birds (SPA)', B: 'habitats (SCI)', C: 'birds + habitats (SPA + SCI)'}};
function natEn(){ return (window.LANG || 'bg') === 'en'; }
function natHatch(){ // a fine 45° green hatch, drawn once at pixel ratio 2 (seamless: the step divides the tile)
  if (map.hasImage('nathatch')) return;
  var pr = 2, S = 16, cv = document.createElement('canvas'); cv.width = S * pr; cv.height = S * pr;
  var x = cv.getContext('2d'); x.scale(pr, pr); x.strokeStyle = 'rgba(27,94,32,0.5)'; x.lineWidth = 1.2;
  for (var o = -S; o <= S; o += 8){ x.beginPath(); x.moveTo(o, S); x.lineTo(o + S, 0); x.stroke(); }
  map.addImage('nathatch', {width: S * pr, height: S * pr, data: x.getImageData(0, 0, S * pr, S * pr).data}, {pixelRatio: pr});
}
// a load failure is told under the chip, in the page language
function natMsg(){ var el = document.getElementById('wxnatmsg'); if (!el) return;
  var on = !!(window._natFail && window.wxNatOn);
  el.textContent = on ? (natEn() ? 'Natura 2000: the data could not be loaded.' : 'Натура 2000: данните не се заредиха.') : '';
  el.style.display = on ? '' : 'none'; }
window.wxSetNat = function(on){ window.wxNatOn = on; window._natFail = false; natMsg();
  var chip = document.getElementById('cbNat');
  if (on){
    if (chip && !map.getSource('wxnat')) chip.classList.add('loading'); // until MapLibre has the file
    whenReady(function(){ if (!window.wxNatOn) return;
      natHatch();
      if (!map.getSource('wxnat')) map.addSource('wxnat', {type: 'geojson', data: window.wxNatUrl, promoteId: 'c', maxzoom: 14,
        attribution: 'Natura 2000 &copy; <a href="https://www.eea.europa.eu/en/datahub/datahubitem-view/6fc8ad2d-195d-40f4-bdec-576e7d1268e4" target="_blank" rel="noopener">EEA / European Commission</a> (CC BY 4.0, simplified) · names <a href="https://natura2000.egov.bg/" target="_blank" rel="noopener">MOEW</a>'});
      var b = zztFloor() || wxAirFloor() || wxZoneAnchor(); // under the territories, ALL airspace + zones; GPS + weather anchor below natFloor()
      if (!map.getLayer('wxnat-fill')) map.addLayer({id: 'wxnat-fill', type: 'fill', source: 'wxnat',
        paint: {'fill-color': NAT_COL, 'fill-opacity': 0.1}}, b);
      if (!map.getLayer('wxnat-hatch')) map.addLayer({id: 'wxnat-hatch', type: 'fill', source: 'wxnat',
        paint: {'fill-pattern': 'nathatch'}}, b);
      if (!map.getLayer('wxnat-line')) map.addLayer({id: 'wxnat-line', type: 'line', source: 'wxnat', layout: {'line-join': 'round'},
        paint: {'line-color': NAT_EDGE, 'line-opacity': 0.85,
          'line-width': ['interpolate', ['linear'], ['zoom'], 6, ['case', NAT_SEL, 2.6, 0.6], 11, ['case', NAT_SEL, 3.6, 1.4]]}}, b);
    }); }
  else { if (chip) chip.classList.remove('loading');
    ['wxnat-line', 'wxnat-hatch', 'wxnat-fill'].forEach(function(id){ if (map.getLayer(id)) map.removeLayer(id); });
    if (map.getSource('wxnat')) map.removeSource('wxnat'); // a failed load is retried at the next switch-on
    window._natSel = null;
    if (window.wxPopupPrune) window.wxPopupPrune(); }
};
// the file has landed (the chip stops pulsing) / could not be loaded (the drawer says so)
map.on('sourcedata', function(e){ if (e.sourceId === 'wxnat' && e.isSourceLoaded){ var c = document.getElementById('cbNat'); if (c) c.classList.remove('loading'); } });
map.on('error', function(e){ if (!e || e.sourceId !== 'wxnat') return;
  var c = document.getElementById('cbNat'); if (c) c.classList.remove('loading');
  window._natFail = true; natMsg(); });
(window.wxLangRefresh = window.wxLangRefresh || []).push(natMsg);
// helpers for the SHARED click chooser in make_3d (same list as zones / NOTAM / airspace)
function natNum(v, en){ // 27102 -> "27 102" / "27,102"; 0.5 -> "0,5" / "0.5"
  var s = String(v).split('.'), i = s[0].replace(/\B(?=(\d{3})+(?!\d))/g, en ? ',' : ' ');
  return s.length > 1 ? i + (en ? '.' : ',') + s[1] : i; }
window.wxNatColor = function(){ return NAT_COL; };
window.wxNatName = function(p){ return (!natEn() && p.b) ? p.b : (p.n || p.c); };
window.wxNatSub = function(p){ var en = natEn(), t = NAT_TYPE[en ? 'en' : 'bg'][p.t];
  return (en ? 'Natura 2000' : 'Натура 2000') + (t ? ' · ' + t : ''); };
window.wxNatDetail = function(p){ var en = natEn(), t = NAT_TYPE[en ? 'en' : 'bg'][p.t];
  var ha = +p.a, km = ha >= 100 ? Math.round(ha / 100) : 0;
  // the MOEW page of the site: its designation order (the bans, if any), the SDF, the boundaries
  var a = '<a href="https://natura2000.egov.bg/EsriBg.Natura.Public.Web.App/Home/ProtectedSite?code=' + encodeURIComponent(p.c) +
          '&siteType=' + (p.t === 'B' ? 'HabitatDirective' : 'BirdsDirective') + '" target="_blank" rel="noopener">';
  return '<b>' + esc(window.wxNatName(p)) + '</b> <span class="ptype">' + (en ? 'Natura 2000' : 'Натура 2000') + '</span><br>' +
    (t ? (en ? 'Protected area for ' : 'Защитена зона ') + t + ' · ' : '') + esc(p.c) +
    '<br>' + (en ? 'Area: ' : 'Площ: ') + natNum(ha, en) + (en ? ' ha' : ' ха') + (km ? ' (' + natNum(km, en) + (en ? ' km²)' : ' км²)') : '') +
    // the owner's wording (16.10)
    '<br>' + (en ? 'Natura 2000 by itself does not ban drone flights. Any bans for this site are in its designation order: ' + a + 'MOEW ↗</a>'
                 : 'Натура 2000 сама по себе си не забранява полети с дрон. Ако за тази зона има забрани, те са в заповедта ѝ: ' + a + 'МОСВ ↗</a>') +
    // the ЗБР bans disturbing ALL wild birds (чл. 46) but only the PROTECTED animals (чл. 38, Annex 3)
    // a hang/para-gliding ban in the site's order: one line, not red (owner 16.10: drones are not named)
    (p.h ? '<br>' + (en ? 'Its order bans hang-gliding / paragliding; drones are not mentioned'
                        : 'Заповедта забранява: „' + esc(p.h) + '“ — дроновете не са споменати') +
           ' <small>(<a href="' + esc(p.hu) + '" target="_blank" rel="noopener">' + esc(p.hd) + ' ↗</a>)</small>' : '') +
    '<br>' + (en ? 'Disturbing wild birds and protected animals is banned everywhere, especially during nesting.'
                 : 'Навсякъде е забранено безпокоенето на диви птици и защитени животни, особено при гнездене.') +
    // whose date it is: the EEA's last publication of the data, not our update (owner 16.10)
    '<br><small>' + (en ? 'Boundaries: EEA / European Commission' : 'Граници: ЕАОС / ЕК') +
      (NAT_PUB ? (en ? ' — last published: ' + NAT_PUB + ';' : ' — последна публикация: ' + NAT_PUB.split('-').reverse().join('.') + ';') : ',') +
      (en ? ' simplified' : ' опростени') + (p.b && !en ? ' · име: МОСВ' : '') + '</small>'; };
// thicken the CLICKED site's outline (feature-state 'sel'); one at a time
window._natSel = null;
window.wxNatSelect = function(code){
  if (window._natSel != null && map.getSource('wxnat')) map.setFeatureState({source: 'wxnat', id: window._natSel}, {sel: false});
  window._natSel = null;
  if (code != null && map.getSource('wxnat')){ window._natSel = code; map.setFeatureState({source: 'wxnat', id: code}, {sel: true}); } };
map.on('mouseenter', 'wxnat-fill', function(){ map.getCanvas().style.cursor = 'pointer'; });
map.on('mouseleave', 'wxnat-fill', function(){ map.getCanvas().style.cursor = ''; });
// ---- protected territories (owner 16.10): parks, reserves, protected sites, natural landmarks
// (Закон за защитените територии), Bulgaria only, from the static protected.json (built by
// tools/make_natura.py: the MOEW's open data, ИАОС register links, the rules of nature_bans.py).
// Owner rule: RED only where an official document explicitly bans drones or flying, every one
// with its quote + document link - a thick red outline over the green (k 'f': the whole area,
// reserves by the law itself), a red DASHED outline where it holds only in a part of the area or
// of the year (k 'p'); green = no explicit ban found. Above Natura 2000 in the nature slot, the
// opposite hatch, so both layers together read as a crosshatch.
window.wxZztUrl = 'protected.json';
var ZZT_RED = '#d32f2f', ZZT_REG = 'https://eea.government.bg/zpo/bg/', ZZT_SEL = ['boolean', ['feature-state', 'sel'], false];
var ZZT_CAT = {bg: {'01': 'Резерват', '02': 'Национален парк', '03': 'Природна забележителност', '04': 'Поддържан резерват', '05': 'Природен парк', '06': 'Защитена местност'},
               en: {'01': 'Strict nature reserve', '02': 'National park', '03': 'Natural landmark', '04': 'Managed reserve', '05': 'Nature park', '06': 'Protected site'}};
function zztHatch(){ // the opposite 45° hatch to Natura's, drawn once at pixel ratio 2
  if (map.hasImage('nathatch2')) return;
  var pr = 2, S = 16, cv = document.createElement('canvas'); cv.width = S * pr; cv.height = S * pr;
  var x = cv.getContext('2d'); x.scale(pr, pr); x.strokeStyle = 'rgba(27,94,32,0.5)'; x.lineWidth = 1.2;
  for (var o = -S; o <= S; o += 8){ x.beginPath(); x.moveTo(o, 0); x.lineTo(o + S, S); x.stroke(); }
  map.addImage('nathatch2', {width: S * pr, height: S * pr, data: x.getImageData(0, 0, S * pr, S * pr).data}, {pixelRatio: pr});
}
function zztMsg(){ var el = document.getElementById('wxzztmsg'); if (!el) return;
  var on = !!(window._zztFail && window.wxZztOn);
  el.textContent = on ? (natEn() ? 'Protected areas: the data could not be loaded.' : 'Защитени територии: данните не се заредиха.') : '';
  el.style.display = on ? '' : 'none'; }
window.wxSetZzt = function(on){ window.wxZztOn = on; window._zztFail = false; zztMsg();
  var chip = document.getElementById('cbZzt');
  if (on){
    if (chip && !map.getSource('wxzzt')) chip.classList.add('loading'); // until MapLibre has the file
    whenReady(function(){ if (!window.wxZztOn) return;
      zztHatch();
      if (!map.getSource('wxzzt')) map.addSource('wxzzt', {type: 'geojson', data: window.wxZztUrl, promoteId: 'i', maxzoom: 14,
        attribution: 'Protected areas &copy; <a href="https://eea.government.bg/zpo/bg/" target="_blank" rel="noopener">ИАОС</a> / <a href="https://natura2000.egov.bg/" target="_blank" rel="noopener">MOEW</a> (simplified)'});
      var b = wxAirFloor() || wxZoneAnchor(); // the top of the nature slot: above Natura, under ALL airspace + zones
      var W = function(sel, base, top){ return ['interpolate', ['linear'], ['zoom'], 6, ['case', ZZT_SEL, sel, base], 11, ['case', ZZT_SEL, sel + 1, top]]; };
      if (!map.getLayer('wxnat-t-fill')) map.addLayer({id: 'wxnat-t-fill', type: 'fill', source: 'wxzzt',
        paint: {'fill-color': NAT_COL, 'fill-opacity': 0.08}}, b);
      if (!map.getLayer('wxnat-t-hatch')) map.addLayer({id: 'wxnat-t-hatch', type: 'fill', source: 'wxzzt',
        paint: {'fill-pattern': 'nathatch2'}}, b);
      if (!map.getLayer('wxnat-t-line')) map.addLayer({id: 'wxnat-t-line', type: 'line', source: 'wxzzt', filter: ['==', ['get', 'k'], ''],
        layout: {'line-join': 'round'}, paint: {'line-color': NAT_EDGE, 'line-opacity': 0.85, 'line-width': W(2.6, 0.6, 1.4)}}, b);
      if (!map.getLayer('wxnat-t-part')) map.addLayer({id: 'wxnat-t-part', type: 'line', source: 'wxzzt', filter: ['==', ['get', 'k'], 'p'],
        layout: {'line-join': 'round'}, paint: {'line-color': ZZT_RED, 'line-width': W(3, 1.6, 2.6), 'line-dasharray': [2, 1.5]}}, b);
      if (!map.getLayer('wxnat-t-ban')) map.addLayer({id: 'wxnat-t-ban', type: 'line', source: 'wxzzt', filter: ['==', ['get', 'k'], 'f'],
        layout: {'line-join': 'round'}, paint: {'line-color': ZZT_RED, 'line-width': W(3, 1.6, 2.6)}}, b);
    }); }
  else { if (chip) chip.classList.remove('loading');
    ['wxnat-t-ban', 'wxnat-t-part', 'wxnat-t-line', 'wxnat-t-hatch', 'wxnat-t-fill'].forEach(function(id){ if (map.getLayer(id)) map.removeLayer(id); });
    if (map.getSource('wxzzt')) map.removeSource('wxzzt'); // a failed load is retried at the next switch-on
    window._zztSel = null;
    if (window.wxPopupPrune) window.wxPopupPrune(); }
};
map.on('sourcedata', function(e){ if (e.sourceId === 'wxzzt' && e.isSourceLoaded){ var c = document.getElementById('cbZzt'); if (c) c.classList.remove('loading'); } });
map.on('error', function(e){ if (!e || e.sourceId !== 'wxzzt') return;
  var c = document.getElementById('cbZzt'); if (c) c.classList.remove('loading');
  window._zztFail = true; zztMsg(); });
(window.wxLangRefresh = window.wxLangRefresh || []).push(zztMsg);
window.wxZztColor = function(p){ return p.k ? ZZT_RED : NAT_COL; };
window.wxZztName = function(p){ return (natEn() && p.m) ? p.m : (p.n || p.m); };
window.wxZztSub = function(p){ var en = natEn();
  return ZZT_CAT[en ? 'en' : 'bg'][p.t] + (p.k === 'f' ? (en ? ' · ban' : ' · забрана') : p.k === 'p' ? (en ? ' · partial ban' : ' · частична забрана') : ''); };
window.wxZztDetail = function(p){ var en = natEn(), ha = +p.a, km = ha >= 100 ? Math.round(ha / 100) : 0;
  var A = function(u, t){ return '<a href="' + esc(u) + '" target="_blank" rel="noopener">' + esc(t) + ' ↗</a>'; };
  var red = function(t){ return '<b style="color:' + ZZT_RED + '">' + t + '</b>'; };
  var rp = (p.r || '').split('/'), reg = rp.length === 2 ? ZZT_REG + 'area.jsp?NEM_Partition=1&categoryID=' + rp[0] + '&areaID=' + rp[1] : ZZT_REG;
  var h = '<b>' + esc(window.wxZztName(p)) + '</b> <span class="ptype">' + esc(ZZT_CAT[en ? 'en' : 'bg'][p.t]) + '</span>' +
    (ha ? '<br>' + (en ? 'Area: ' : 'Площ: ') + natNum(ha, en) + (en ? ' ha' : ' ха') + (km ? ' (' + natNum(km, en) + (en ? ' km²)' : ' км²)') : '') : '');
  if (p.l) h += '<br>' + (en ? red('🚫 Reserves:') + ' the Protected Areas Act (Art. 17 and 27) bans every activity outside its closed list (' + A('https://lex.bg/laws/ldoc/2134445060', 'the law') + '): take-off and landing inside are banned; the law does not clearly say whether overflight is.'
                             : red('🚫 По закона (ЗЗТ, чл. 17 и чл. 27)') + ' в резерватите и поддържаните резервати се забраняват всякакви дейности извън изброените (' + A('https://lex.bg/laws/ldoc/2134445060', 'закона') + '): излитане и кацане вътре са забранени; дали е забранено прелитане отгоре, законът не казва ясно.');
  if (p.q) h += '<br>' + (p.k === 'p' ? red(en ? '⚠ Partial ban:' : '⚠ Частична забрана') + (en ? '' : ' (' + esc(p.w || '') + '):')
                                     : red(en ? '🚫 Explicit ban:' : '🚫 Изрична забрана:')) +
                ' ' + (en ? esc(p.qe) : '„' + esc(p.q) + '“') + ' <small>(' + A(p.u, p.d) + ')</small>';
  if (p.h) h += '<br>' + (en ? 'Its order bans hang-gliding / paragliding; drones are not mentioned.'
                             : 'В заповедта ѝ: „' + esc(p.h) + '“ — дроновете не са споменати.');
  if (p.x) h += '<br>' + (en ? esc(p.xe) : 'Планът за управление забранява: „' + esc(p.x) + '“') + ' <small>(' + A(p.xu, p.xd) + ')</small>';
  if (!p.k) h += '<br>' + (en ? 'No explicit ban on drones or flights was found.' : 'Не е открита изрична забрана за дронове или полети.');
  return h + '<br>' + (en ? 'Disturbing wild birds and protected animals is banned everywhere, especially during nesting.'
                          : 'Навсякъде е забранено безпокоенето на диви птици и защитени животни, особено при гнездене.') +
    '<br>' + (en ? 'Documents of the area: ' + A(reg, 'ИАОС register (in Bulgarian)') : 'Документите на територията: ' + A(reg, 'регистър на ИАОС')) +
    '<br><small>' + (en ? 'Boundaries and names: ИАОС / MOEW, simplified' : 'Граници и имена: ИАОС / МОСВ, опростени') + '</small>'; };
window._zztSel = null;
window.wxZztSelect = function(id){
  if (window._zztSel != null && map.getSource('wxzzt')) map.setFeatureState({source: 'wxzzt', id: window._zztSel}, {sel: false});
  window._zztSel = null;
  if (id != null && map.getSource('wxzzt')){ window._zztSel = id; map.setFeatureState({source: 'wxzzt', id: id}, {sel: true}); } };
map.on('mouseenter', 'wxnat-t-fill', function(){ map.getCanvas().style.cursor = 'pointer'; });
map.on('mouseleave', 'wxnat-t-fill', function(){ map.getCanvas().style.cursor = ''; });
// ---- obstacles (owner 17.10): power lines and their towers / poles, ESO's lines that OSM lacks, wind
// turbines, masts, towers, chimneys and other tall objects, lifts, rail / tram / trolleybus wires - from
// obstacles/ (built daily by tools/make_obstacles.py from OpenStreetMap + ESO, ODbL). ONE button together
// with the 3D buildings, ON by default. Only the 0.5° cells on the screen are fetched, and only when
// zoomed in (OBS_MINZ); the cells around the view sit in ONE GeoJSON source (the ones used longest ago
// are forgotten after OBS_KEEP). Dark lines and symbols - never the zones' red / orange / yellow - just
// above the zones, below the layers added without a slot (NOTAM, activated zones, aircraft). Heights:
// OSM's own, or a typical one ("~"; values + sources from index.json / tools/obstacle_heights.py).
window.wxObsUrl = 'obstacles/';
var OBS_MINZ = 11, OBS_KEEP = 16, OBS_INK = '#1f2a30', OBS_LIFT = '#00695c', OBS_RAIL = '#6a1b9a';
var OBS = {idx: null, idxP: null, have: {}, cells: {}, order: [], shown: '', shown3d: '', on: false, busy: 0, fail: false};
var OBS_IDS = ['obs-rail', 'obs-lift', 'obs-minor', 'obs-eso-case', 'obs-eso', 'obs-line-case', 'obs-line', 'obs-sup', 'obs-3d', 'obs-sym', 'obs-sym2'];
// 3D (owner 17-18.10): every object with a height (OSM's own or a typical one) stands as a tapered "needle" of
// that height, from zoom OBS_Z_3D, only in 3D mode and only around the screen; MapLibre cannot lift lines, so the
// power wires are bands of short level pieces (obsWires), the other wires stay on the ground. Transmission towers get arms across their line at the height of the lowest
// wire (ESO): 400 kV two (the upper a little narrower), 220 kV two 6 m apart (ESO type НТ), 110 kV three
// 3.5 m apart, the middle one the widest (ESO's „бъчва“); a tower with its OWN height is the model scaled to
// it. Widths are a sign, not the real footprint. Turbines: a white tower to the hub (0.67 x the tip height:
// 0.64-0.70 in the four farms of obstacle_heights.py) and a thin grey part up to the blade tip.
var OBS_Z_3D = 14, OBS_WHITE = '#eceff1', OBS_BLADE = '#b0bec5';
// owner 17.10, after seeing Sofia: the small objects (flagpoles, antennas, silos, cranes, water towers, bell towers)
// show from zoom 14, the rail / tram / trolleybus wires from 13; the rest as before (lines and tall objects 11, poles 13)
var OBS_SMALL = ['flagpole', 'antenna', 'silo', 'crane', 'wtower'], OBS_Z_SMALL = 14, OBS_Z_RAIL = 13;
var OBS_SUP = ['tower', 'pole', 'upole', 'portal', 'catmast', 'liftpylon'];
var OBS_TALL = ['turbine', 'mast', 'mtower', 'ctower', 'chimney', 'wtower', 'lighthouse', 'crane', 'flagpole', 'antenna', 'silo',
                'windmill', 'flare', 'gasometer'];
function obsEn(){ return (window.LANG || 'bg') === 'en'; }
function obsNum(v){ var s = String(Math.round(v * 10) / 10); return obsEn() ? s : s.replace('.', ','); }
function obsMsg(){ var el = document.getElementById('wxobsmsg'); if (!el) return;
  var on = !!(OBS.fail && OBS.on);
  el.textContent = on ? (obsEn() ? 'Obstacles: the data could not be loaded.' : 'Препятствия: данните не се заредиха.') : '';
  el.style.display = on ? '' : 'none'; }
function obsBusy(d){ OBS.busy = Math.max(0, OBS.busy + d); var c = document.getElementById('cbObs');
  if (c) c.classList.toggle('loading', OBS.busy > 0 && OBS.on); }
function obsIcons(){ var pr = 2;
  function make(id, w, h, draw){ if (map.hasImage(id)) return;
    var c = document.createElement('canvas'); c.width = w * pr; c.height = h * pr;
    var x = c.getContext('2d'); x.scale(pr, pr); x.lineJoin = 'round'; x.lineCap = 'round'; draw(x);
    map.addImage(id, {width: w * pr, height: h * pr, data: x.getImageData(0, 0, w * pr, h * pr).data}, {pixelRatio: pr}); }
  // a tall object: the aviation obstacle sign - a narrow spike over a dot, dark with a white edge
  make('obs-spike', 16, 22, function(x){
    var path = function(){ x.beginPath(); x.moveTo(3, 20); x.lineTo(8, 2); x.lineTo(13, 20); };
    path(); x.lineWidth = 4.4; x.strokeStyle = 'rgba(255,255,255,0.95)'; x.stroke();
    path(); x.lineWidth = 2.1; x.strokeStyle = OBS_INK; x.stroke();
    x.beginPath(); x.arc(8, 17, 2.7, 0, 7); x.fillStyle = '#fff'; x.fill();
    x.beginPath(); x.arc(8, 17, 1.8, 0, 7); x.fillStyle = OBS_INK; x.fill(); });
  // a wind turbine: a mast and three blades
  make('obs-wind', 20, 24, function(x){
    var draw = function(lw, col){ x.lineWidth = lw; x.strokeStyle = col;
      x.beginPath(); x.moveTo(10, 23); x.lineTo(10, 9); x.stroke();
      [-90, 30, 150].forEach(function(a){ var r = a * Math.PI / 180;
        x.beginPath(); x.moveTo(10, 9); x.lineTo(10 + 8 * Math.cos(r), 9 + 8 * Math.sin(r)); x.stroke(); }); };
    draw(4.4, 'rgba(255,255,255,0.95)'); draw(2.1, OBS_INK);
    x.beginPath(); x.arc(10, 9, 1.9, 0, 7); x.fillStyle = OBS_INK; x.fill(); });
}
// the height label next to a tall object: "150 м" (OSM's own) or "~125 м" (typical)
function obsLabel(){ var H = ['abs', ['get', 'h']];
  return ['case', ['==', ['get', 'h'], 0], '',
          ['concat', ['case', ['<', ['get', 'h'], 0], '~', ''], ['number-format', H, {'max-fraction-digits': 0}], obsEn() ? ' m' : ' м']]; }
// in 3D, from the zoom where an object stands as a 3D shape, its 2D sign (icon / dot) goes; the height label
// stays (owner 18.10: „където се появи 3D колона скриваш знака“). Objects without a height keep their sign.
function obsIcon(){ var normal = ['match', ['get', 'k'], 'turbine', 'obs-wind', 'obs-spike'];
  return window.wxMode === '3d' ? ['step', ['zoom'], normal, OBS_Z_3D, ['case', ['!=', ['get', 'h'], 0], '', normal]] : normal; }
function obsDotOp(){ return window.wxMode === '3d' ? ['step', ['zoom'], 1, OBS_Z_3D, ['case', ['!=', ['get', 'h'], 0], 0, 1]] : 1; }
function obsSlot(){ var ls = wxStyleLayers(), i; // just above the zones, below the lightning / thunderstorm bolts (liSlot)
  for (i = 0; i < ls.length; i++){ if (ls[i].id === 'wxli-layer' || ls[i].id === 'wxstorm-layer') return ls[i].id; }
  for (i = 0; i < ls.length; i++){ if (ls[i].id === 'o-CONDITIONAL'){ // above the zones AND the airfields (aero-*), which stay just above the zones
    for (i++; i < ls.length && ls[i].id.indexOf('aero-') === 0; i++){}
    return i < ls.length ? ls[i].id : undefined; } }
  return undefined; }
function obsLayers(){
  if (map.getLayer('obs-line')) return;
  var b = obsSlot(), Z = function(a, c){ return ['interpolate', ['linear'], ['zoom'], 11, a, 16, c]; };
  // a power line's width by its voltage (400 / 220 / the rest), from zoom 11 to 16
  var V = function(add){ var w = function(a, m, c){ return ['case', ['>=', ['get', 'v'], 300], a + add, ['>=', ['get', 'v'], 200], m + add, c + add]; };
    return ['interpolate', ['linear'], ['zoom'], 11, w(2.2, 1.8, 1.4), 16, w(4.5, 3.6, 2.8)]; };
  var K = function(k){ return ['==', ['get', 'k'], k]; }, IN = function(a){ return ['in', ['get', 'k'], ['literal', a]]; };
  var L = function(id, filter, paint, minz){ map.addLayer({id: id, type: 'line', source: 'wxobs', minzoom: minz || OBS_MINZ, filter: filter,
    layout: {'line-join': 'round'}, paint: paint}, b); };
  L('obs-rail', IN(['rail', 'tram', 'trolley']), {'line-color': OBS_RAIL, 'line-width': Z(0.8, 2), 'line-opacity': 0.85, 'line-dasharray': [3, 2]}, OBS_Z_RAIL);
  L('obs-lift', K('lift'), {'line-color': OBS_LIFT, 'line-width': Z(1.2, 2.6), 'line-dasharray': [2, 1.2]});
  L('obs-minor', K('minor'), {'line-color': OBS_INK, 'line-width': Z(0.7, 1.8), 'line-opacity': 0.9});
  L('obs-eso-case', K('eso'), {'line-color': '#fff', 'line-opacity': 0.5, 'line-width': V(1.6)});
  L('obs-eso', K('eso'), {'line-color': OBS_INK, 'line-width': V(0), 'line-dasharray': [2.5, 1.5]});   // ESO: an approximate route
  L('obs-line-case', K('line'), {'line-color': '#fff', 'line-opacity': 0.5, 'line-width': V(1.6)});
  L('obs-line', K('line'), {'line-color': OBS_INK, 'line-width': V(0)});
  map.addLayer({id: 'obs-sup', type: 'circle', source: 'wxobs', minzoom: 13, filter: ['all', ['==', ['geometry-type'], 'Point'], IN(OBS_SUP)],
    paint: {'circle-radius': ['interpolate', ['linear'], ['zoom'], 13, 1.8, 17, 4], 'circle-color': ['match', ['get', 'k'], 'liftpylon', OBS_LIFT, OBS_INK],
            'circle-stroke-color': '#fff', 'circle-stroke-width': 0.8, 'circle-opacity': obsDotOp(), 'circle-stroke-opacity': obsDotOp()}}, b);
  // the 3D needles + arms (their own source of small polygons, built only in 3D - obs3dPush)
  if (!map.getSource('wxobs3d')) map.addSource('wxobs3d', {type: 'geojson', data: {type: 'FeatureCollection', features: []}, maxzoom: 16});
  map.addLayer({id: 'obs-3d', type: 'fill-extrusion', source: 'wxobs3d', minzoom: OBS_Z_3D,
    layout: {visibility: window.wxMode === '3d' ? 'visible' : 'none'},
    paint: {'fill-extrusion-color': ['get', 'zc'], 'fill-extrusion-base': ['get', 'zb'], 'fill-extrusion-height': ['get', 'zt'],
            'fill-extrusion-opacity': 0.95}}, b);
  var small = ['any', IN(OBS_SMALL), ['all', K('mtower'), ['==', ['get', 't'], 'bell_tower']]];
  var S = function(id, filter, minz){ map.addLayer({id: id, type: 'symbol', source: 'wxobs', minzoom: minz,
    filter: ['all', ['==', ['geometry-type'], 'Point'], IN(OBS_TALL), filter],
    layout: {'icon-image': obsIcon(), 'icon-anchor': 'bottom',
             'icon-size': ['interpolate', ['linear'], ['zoom'], 11, 0.75, 15, 1], 'symbol-sort-key': ['-', 0, ['abs', ['get', 'h']]],
             'text-field': obsLabel(), 'text-font': ['Noto Sans Regular'], 'text-size': 10.5, 'text-anchor': 'left', 'text-offset': [0.7, -1],
             'text-optional': true},
    paint: {'text-color': OBS_INK, 'text-halo-color': '#fff', 'text-halo-width': 1.4}}, b); };
  S('obs-sym', ['!', small], OBS_MINZ);
  S('obs-sym2', small, OBS_Z_SMALL);
}
// one cell file -> GeoJSON features (coordinates are delta-encoded integers, see make_obstacles.py)
function obsDecode(key, c){
  var K = OBS.idx.kinds, S = OBS.idx.scale, kk = key.split('_'), base = (+kk[0] * 64 + +kk[1]) * 100000, n = 0, out = [], dir = {};
  (c.l || []).forEach(function(r){ var f = r[2], x = f[0], y = f[1], q = [[x, y]], k = K[r[0]];
    for (var i = 2; i < f.length; i += 2){ x += f[i]; y += f[i + 1]; q.push([x, y]); }
    // the line's direction at each vertex (its towers / poles / lift pylons stand there): the 3D arms go across it
    if (k === 'line' || k === 'minor' || k === 'lift') q.forEach(function(p, i){ var a = q[Math.max(0, i - 1)], e = q[Math.min(q.length - 1, i + 1)];
      dir[p[0] + ',' + p[1]] = Math.atan2((e[1] - a[1]) * 0.993, (e[0] - a[0]) * Math.cos(p[1] / S * Math.PI / 180)); }); // 0.993 = m per deg lat / lon
    out.push({type: 'Feature', id: base + n++, geometry: {type: 'LineString', coordinates: q.map(function(p){ return [p[0] / S, p[1] / S]; })},
              properties: {k: k, v: r[1] || 0, n: r[3] || '', t: r[4] || ''}}); });
  out.dir = dir;
  var x = 0, y = 0, sup = {}, pw = [];
  (c.p || []).forEach(function(r){ x += r[0]; y += r[1];
    var pr = {k: K[r[2]], h: (r[3] || 0) / 10, v: r[4] || 0, n: r[5] || '', t: r[6] || ''};
    if (r[7]){ pr.s = r[7] / 10; pr.a = r[8] || 0; }   // a portal mapped as a way: its span (m) + the beam's direction (°)
    // the supports of the power lines, for the wires in the air: by their spot (a line vertex), a portal way by its middle
    if (pr.k === 'tower' || pr.k === 'pole' || pr.k === 'upole' || pr.k === 'portal'){ if (pr.s) pw.push({x: x, y: y, p: pr}); else sup[x + ',' + y] = pr; }
    out.push({type: 'Feature', id: base + n++, geometry: {type: 'Point', coordinates: [x / S, y / S]}, properties: pr}); });
  out.sup = sup; out.pw = pw;
  return out; }
// the cells on the screen (+ a quarter cell around it); when the view is tilted towards the horizon,
// only the OBS_KEEP - 4 nearest to the centre
function obsView(){ var I = OBS.idx, b = map.getBounds(), C = I.cell, m = C / 4, out = [], c = map.getCenter();
  for (var ix = Math.floor((b.getWest() - m - I.x0) / C); ix <= Math.floor((b.getEast() + m - I.x0) / C); ix++)
    for (var iy = Math.floor((b.getSouth() - m - I.y0) / C); iy <= Math.floor((b.getNorth() + m - I.y0) / C); iy++)
      if (OBS.have[ix + '_' + iy]) out.push(ix + '_' + iy);
  if (out.length > OBS_KEEP - 4){
    var d = function(k){ var a = k.split('_'); return Math.pow(I.x0 + (+a[0] + 0.5) * C - c.lng, 2) + Math.pow(I.y0 + (+a[1] + 0.5) * C - c.lat, 2); };
    out.sort(function(p, q){ return d(p) - d(q); }); out = out.slice(0, OBS_KEEP - 4); }
  return out.sort(); }
function obsPush(){
  var src = map.getSource('wxobs'); if (!OBS.on || !src || !OBS.idx) return;
  var keys = map.getZoom() < OBS_MINZ - 0.5 ? [] : obsView().filter(function(k){ return OBS.cells[k]; });
  Object.keys(OBS.cells).forEach(function(k){ if (OBS.cells[k] && OBS.order.indexOf(k) < 0) OBS.order.unshift(k); }); // loaded after the view moved on
  keys.forEach(function(k){ var i = OBS.order.indexOf(k); if (i >= 0) OBS.order.splice(i, 1); OBS.order.push(k); });
  while (OBS.order.length > OBS_KEEP){ var old = OBS.order.shift(); if (keys.indexOf(old) >= 0){ OBS.order.push(old); break; } delete OBS.cells[old]; }
  var sig = keys.join(',');
  if (sig !== OBS.shown){ OBS.shown = sig;
    var fs = []; keys.forEach(function(k){ fs = fs.concat(OBS.cells[k]); });
    src.setData({type: 'FeatureCollection', features: fs}); }
  obs3dPush(keys); }
// the 3D shapes of one object (polygons with zb / zt = their base / top in metres and zc = colour); every polygon
// carries the object's id + properties, so the click chooser shows it once
function obsShape(f, dir, out){
  var p = f.properties, H = Math.abs(p.h), x = f.geometry.coordinates[0], y = f.geometry.coordinates[1];
  var mx = 111320 * Math.cos(y * Math.PI / 180), my = 110540, S = OBS.idx.scale;
  var th = dir[Math.round(x * S) + ',' + Math.round(y * S)] || 0;
  var P = function(ring, zb, zt, zc){ out.push({type: 'Feature', id: f.id, geometry: {type: 'Polygon', coordinates: [ring]},
    properties: {k: p.k, h: p.h, v: p.v, n: p.n, t: p.t, zb: zb, zt: zt, zc: zc}}); };
  var oct = function(r){ var g = []; for (var i = 0; i <= 8; i++){ var a = (i % 8) * Math.PI / 4 + Math.PI / 8; g.push([x + r * Math.cos(a) / mx, y + r * Math.sin(a) / my]); } return g; };
  var arm = function(len, w){ var ux = Math.cos(th + Math.PI / 2), uy = Math.sin(th + Math.PI / 2), vx = Math.cos(th), vy = Math.sin(th);
    return [[1, 1], [1, -1], [-1, -1], [-1, 1], [1, 1]].map(function(s){ var ex = s[0] * ux * len / 2 + s[1] * vx * w / 2, ey = s[0] * uy * len / 2 + s[1] * vy * w / 2;
      return [x + ex / mx, y + ey / my]; }); };
  var tiers = function(top, rs, zc){ rs.forEach(function(r, i){ P(oct(r), top * i / rs.length, top * (i + 1) / rs.length, zc); }); };
  if (p.k === 'tower'){
    var cls = p.v >= 300 ? 400 : p.v >= 200 ? 220 : p.v >= 60 ? 110 : p.v > 0 ? 20 : (H >= 20 ? 110 : 20);
    if (cls === 20){ tiers(H, [1.2, 0.9, 0.6, 0.4], OBS_INK); P(arm(3, 0.5), H - 0.8, H - 0.4, OBS_INK); return; }
    var T = (OBS.idx.towers || {})[String(cls)] || {low: 16, h: 27.5}, s = H / (T.h || H), sc = Math.max(0.5, Math.min(2.5, s));
    var low = Math.min(T.low * s, H * 0.75);
    var arms = cls === 400 ? [[0, 15], [(H - low) * 0.6 / s, 12]] : cls === 220 ? [[0, 12], [6, 9.6]] : [[0, 7], [3.5, 9], [7, 7]];
    tiers(H, [3, 2.1, 1.35, 0.75].map(function(r){ return r * sc; }), OBS_INK);
    arms.forEach(function(a){ var z = low + a[0] * s; if (z < H) P(arm(a[1] * sc, sc), z - 0.5 * sc, z + 0.5 * sc, OBS_INK); });
  } else if (p.k === 'pole' || p.k === 'upole'){ P(oct(0.55), 0, H, OBS_INK); P(arm(2.6, 0.5), H - 0.8, H - 0.4, OBS_INK); }
  else if (p.k === 'liftpylon'){ P(oct(0.7), 0, H, OBS_LIFT); P(arm(5, 0.6), H - 0.6, H, OBS_LIFT); }
  else if (p.k === 'turbine'){ var hub = H * 0.67; tiers(hub, [2.2, 1.9, 1.6, 1.3], OBS_WHITE); P(oct(0.5), hub, H, OBS_BLADE); }
  else if (p.k === 'portal'){
    // a substation portal (owner 18.10): a „П“ frame - a leg at both ends and one every bay, the beam the wires
    // hang from (ESO), the legs up to the columns' peaks where a figure exists (110 kV). Along the OSM way (leg
    // to leg); a portal mapped as a point stands across its line with one bay. Unknown voltage = 110 kV.
    var pc = p.v >= 300 ? 400 : p.v >= 200 ? 220 : 110, PC = (OBS.idx.portals || {})[String(pc)] || {h: H, beam: H, w: 9};
    var beam = PC.beam * H / (PC.h || H), bay = PC.w || 9, span = p.s || bay, nb = Math.max(1, Math.round(span / bay));
    var lr = pc === 400 ? 0.9 : pc === 220 ? 0.7 : 0.5, bh = pc === 400 ? 1.6 : pc === 220 ? 1.2 : 0.9, bw = pc === 400 ? 1 : 0.7;
    var ang = p.s ? p.a * Math.PI / 180 : th + Math.PI / 2, ux = Math.cos(ang), uy = Math.sin(ang);
    var leg = function(d){ var cx = x + d * ux / mx, cy = y + d * uy / my, g = [];
      for (var i = 0; i <= 8; i++){ var a = (i % 8) * Math.PI / 4 + Math.PI / 8; g.push([cx + lr * Math.cos(a) / mx, cy + lr * Math.sin(a) / my]); }
      return g; };
    for (var i = 0; i <= nb; i++) P(leg(-span / 2 + span * i / nb), 0, H, OBS_INK);
    P([[1, 1], [1, -1], [-1, -1], [-1, 1], [1, 1]].map(function(s){ var ex = s[0] * ux * (span / 2 + lr) - s[1] * uy * bw / 2,
      ey = s[0] * uy * (span / 2 + lr) + s[1] * ux * bw / 2; return [x + ex / mx, y + ey / my]; }), beam - bh, beam, OBS_INK); }
  else if (p.k === 'chimney') tiers(H, [3.5, 3.1, 2.7, 2.4], OBS_INK);
  else if (p.k === 'mtower' || p.k === 'ctower') tiers(H, [4, 3, 2, 1.2], OBS_INK);
  else tiers(H, [1.4, 1, 0.7, 0.4], OBS_INK); }
// wires in the air (owner 18.10, a trial): every power line (line / minor) as a band of short level pieces from support
// to support (every vertex of a line is taken as a support): at a tower the lowest wire (ESO; a tower with its own height
// scaled like its arms), at a portal its beam, at a pole its top; between them the wire sags down to the Наредба № 3
// minimum outside settlements (its lowest point). A span cut at a cell border is joined with its other half from the neighbouring
// cell (mirrored when that cell is not loaded). ESO routes, lifts and contact wires stay on the ground; the ground line
// stays as the wire's shadow. The pieces are cut by equal height steps (short where the wire is steep, by the
// supports): OBS_WSTEP m near the bottom of the screen, coarser farther away; OBS_WTH = a piece's thickness,
// widths by kind (m) (owner 18.10, after the first look: thinner, smooth by the towers).
var OBS_WSTEP = [[1500, 0.4], [5000, 1], [Infinity, 2.5]], OBS_WTH = 0.25, OBS_WW = {line: 0.4, minor: 0.3};
function obsWireZ(k, v, sp){ var I = OBS.idx, c = obsCls(+v), TW = I.towers || {}, PL = I.poles || {};
  if (sp && sp.h){ var H = Math.abs(sp.h);
    if (sp.k === 'portal'){ var P = (I.portals || {})[String(sp.v >= 300 ? 400 : sp.v >= 200 ? 220 : 110)]; return P ? P.beam * H / P.h : H; }
    if (sp.k === 'tower'){ var tc = obsCls(+sp.v || +v), T = TW[String(tc || 110)];
      return (!T || tc === 20 || tc === 0.4) ? H : Math.min(T.low * H / T.h, H * 0.75); }
    return H; }
  if (k === 'line' && c !== 20 && c !== 0.4) return (TW[String(c)] || TW['110'] || {low: 16}).low;
  return PL[String(c)] || I.poleUnknown || 11; }
function obsWires(keys, W, E, Sb, N, out){
  var I = OBS.idx, S = I.scale, B = Math.round(I.cell * S), X0 = Math.round(I.x0 * S), Y0 = Math.round(I.y0 * S), segs = [], ends = {};
  var K = function(p){ return Math.round(p[0] * S) + ',' + Math.round(p[1] * S); };
  var M = function(a, b){ return Math.hypot((b[0] - a[0]) * 111320 * Math.cos(a[1] * Math.PI / 180), (b[1] - a[1]) * 110540); };
  var inBox = function(p){ return p[0] >= W && p[0] <= E && p[1] >= Sb && p[1] <= N; };
  keys.forEach(function(ck){ var cell = OBS.cells[ck]; if (!cell) return;
    cell.forEach(function(f){ var p = f.properties; if (f.geometry.type !== 'LineString' || (p.k !== 'line' && p.k !== 'minor')) return;
      var co = f.geometry.coordinates, n = co.length, z = [], cut = [];
      for (var i = 0; i < n; i++){ var x = Math.round(co[i][0] * S), y = Math.round(co[i][1] * S), sp = (cell.sup || {})[x + ',' + y];
        cut[i] = (i === 0 || i === n - 1) && ((x - X0) % B === 0 || (y - Y0) % B === 0);   // a cell border, not a support
        if (!sp && (i === 0 || i === n - 1)) (cell.pw || []).forEach(function(q){   // a line ending on a node of a portal way
          if (!sp && M(co[i], [q.x / S, q.y / S]) <= q.p.s / 2 + 3) sp = q.p; });
        z[i] = cut[i] ? null : obsWireZ(p.k, p.v, sp); }
      var w = {f: f, co: co, z: z, cut: cut, zmin: ((I.wire || {})[String(obsCls(+p.v))] || (I.wire || {})['0'] || [6])[0]};
      [0, n - 1].forEach(function(i){ if (cut[i]) (ends[K(co[i])] = ends[K(co[i])] || []).push({w: w, i: i}); });
      segs.push(w); }); });
  // the pieces of a span from support a (height za) towards b, over the part [0, tb] of a span to a support of height zo
  // (a parabola through both supports whose lowest point is the minimum - nearer the lower support when they differ)
  var el = map.getContainer(), nb = map.unproject([el.clientWidth / 2, el.clientHeight]), near = [nb.lng, nb.lat];   // the nearest ground on the screen
  var span = function(w, a, b, za, zo, tb){
    var m = w.zmin, ra = Math.sqrt(Math.max(0, za - m)), rb = Math.sqrt(Math.max(0, zo - m)), c = (ra + rb) * (ra + rb), t0 = ra / ((ra + rb) || 1), sag = ra && rb;
    var zf = sag ? function(t){ return m + c * (t - t0) * (t - t0); } : function(t){ return za + (zo - za) * t; };
    var dn = M(near, [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2]), step = (OBS_WSTEP.filter(function(s){ return dn < s[0]; })[0] || OBS_WSTEP[OBS_WSTEP.length - 1])[1];
    var ts = [0], cut = function(z0, z1, toT){ var k = Math.max(1, Math.ceil(Math.abs(z1 - z0) / step)); for (var j = 1; j <= k; j++) ts.push(toT(z0 + (z1 - z0) * j / k)); };
    if (!sag) cut(zf(0), zf(tb), function(z){ return Math.abs(zo - za) > 1e-9 ? (z - za) / (zo - za) : tb; });
    else { var t1 = Math.min(t0, tb);
      cut(za, zf(t1), function(z){ return Math.min(t1, t0 - Math.sqrt(Math.max(0, z - m) / c)); });                 // down to the lowest point
      if (tb > t0) cut(m, zf(tb), function(z){ return Math.min(tb, t0 + Math.sqrt(Math.max(0, z - m) / c)); }); }   // and up again
    var len = M(a, b), mx = 111320 * Math.cos(a[1] * Math.PI / 180), my = 110540, ux = (b[0] - a[0]) * mx / (len || 1), uy = (b[1] - a[1]) * my / (len || 1);
    var hw = (OBS_WW[w.f.properties.k] || 0.3) / 2, p = w.f.properties;
    for (var j = 0; j + 1 < ts.length; j++){ if (ts[j + 1] - ts[j] < 1e-6) continue;
      var z0 = zf(ts[j]), z1 = zf(ts[j + 1]), d0 = len * ts[j] / tb - 0.05, d1 = len * ts[j + 1] / tb + 0.05;
      var ring = [[d0, -hw], [d1, -hw], [d1, hw], [d0, hw], [d0, -hw]].map(function(q){
        return [a[0] + (q[0] * ux - q[1] * uy) / mx, a[1] + (q[0] * uy + q[1] * ux) / my]; });
      out.push({type: 'Feature', id: w.f.id, geometry: {type: 'Polygon', coordinates: [ring]},
                properties: {k: p.k, v: p.v, n: p.n, t: p.t, zb: Math.max(0, Math.min(z0, z1) - OBS_WTH / 2), zt: Math.max(z0, z1) + OBS_WTH / 2, zc: OBS_INK}}); } };
  segs.forEach(function(w){ var co = w.co, n = co.length;
    for (var i = 0; i + 1 < n; i++){ var a = co[i], b = co[i + 1];
      if (!inBox(a) && !inBox(b)) continue;
      if (!w.cut[i] && !w.cut[i + 1]){ span(w, a, b, w.z[i], w.z[i + 1], 1); continue; }
      if (w.cut[i] && w.cut[i + 1]) continue;                        // a sliver between two borders: left on the ground
      var si = w.cut[i] ? i + 1 : i, ci = w.cut[i] ? i : i + 1, dA = M(co[si], co[ci]), zo = w.z[si], dB = dA;
      var o = (ends[K(co[ci])] || []).filter(function(e){ return e.w !== w && e.w.f.properties.k === w.f.properties.k; })[0];
      if (o){ var oi = o.i === 0 ? 1 : o.w.co.length - 2;
        if (o.w.z[oi] != null){ zo = o.w.z[oi]; dB = M(co[ci], o.w.co[oi]); } }   // the other half of the span
      span(w, co[si], co[ci], w.z[si], zo, dA / (dA + dB)); } }); }
// in 3D from zoom OBS_Z_3D - 0.5: the shapes of the objects around the screen (rebuilt when the view moves on)
function obs3dPush(keys){
  var src = map.getSource('wxobs3d'); if (!src) return;
  var on = OBS.on && window.wxMode === '3d' && map.getZoom() >= OBS_Z_3D - 0.5, b = map.getBounds();
  var w = (b.getEast() - b.getWest()) * 0.3, h = (b.getNorth() - b.getSouth()) * 0.3, g = 0.002, R = function(v){ return Math.round(v / g); };
  var W = b.getWest() - w, E = b.getEast() + w, Sb = b.getSouth() - h, N = b.getNorth() + h;
  var want = on ? keys.join(',') + '|' + [R(W), R(E), R(Sb), R(N)].join(',') : '';
  if (want === OBS.shown3d) return;
  OBS.shown3d = want;
  var fs = [];
  if (on) keys.forEach(function(k){ var cell = OBS.cells[k]; (cell || []).forEach(function(f){
    if (f.geometry.type !== 'Point' || !f.properties.h) return;
    var x = f.geometry.coordinates[0], y = f.geometry.coordinates[1];
    if (x >= W && x <= E && y >= Sb && y <= N) obsShape(f, cell.dir || {}, fs); }); });
  if (on) obsWires(keys, W, E, Sb, N, fs);
  src.setData({type: 'FeatureCollection', features: fs}); }
// called by wxSetMode (make_3d) on a 2D <-> 3D switch
window.wxObs3D = function(){
  if (map.getLayer('obs-3d')) map.setLayoutProperty('obs-3d', 'visibility', (OBS.on && window.wxMode === '3d') ? 'visible' : 'none');
  ['obs-sym', 'obs-sym2'].forEach(function(id){ if (map.getLayer(id)) map.setLayoutProperty(id, 'icon-image', obsIcon()); });
  if (map.getLayer('obs-sup')){ map.setPaintProperty('obs-sup', 'circle-opacity', obsDotOp()); map.setPaintProperty('obs-sup', 'circle-stroke-opacity', obsDotOp()); }
  obsPush(); };
function obsRefresh(){
  if (!OBS.on || !OBS.idx || !map.getSource('wxobs')) return;
  if (map.getZoom() >= OBS_MINZ - 0.5) obsView().forEach(function(k){
    if (OBS.cells[k] !== undefined) return;
    OBS.cells[k] = null; obsBusy(1);
    fetch(window.wxObsUrl + 'c' + k + '.json?v=' + encodeURIComponent(OBS.idx.changed || ''))
      .then(function(r){ if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function(c){ OBS.cells[k] = obsDecode(k, c); OBS.fail = false; })
      .catch(function(){ delete OBS.cells[k]; OBS.fail = true; })
      .then(function(){ obsBusy(-1); obsMsg(); obsPush(); }); });
  obsPush(); }
function obsIndex(){ if (OBS.idx || OBS.idxP) return;
  obsBusy(1);
  OBS.idxP = fetch(window.wxObsUrl + 'index.json', {cache: 'no-cache'})
    .then(function(r){ if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(function(d){ OBS.idx = d; OBS.have = {}; (d.cells || []).forEach(function(c){ OBS.have[c[0] + '_' + c[1]] = 1; }); OBS.fail = false; })
    .catch(function(){ OBS.fail = true; })
    .then(function(){ OBS.idxP = null; obsBusy(-1); obsMsg(); obsRefresh(); }); }
window.wxSetObs = function(on){ OBS.on = on; OBS.fail = false; obsMsg(); obsBusy(0);
  whenReady(function(){
    // the 3D buildings ride the same button (owner 17.10); 2D never shows them
    if (map.getLayer('buildings')) map.setLayoutProperty('buildings', 'visibility', (OBS.on && window.wxMode === '3d') ? 'visible' : 'none');
    if (!OBS.on){
      OBS_IDS.slice().reverse().forEach(function(id){ if (map.getLayer(id)) map.removeLayer(id); });
      ['wxobs', 'wxobs3d'].forEach(function(id){ if (map.getSource(id)) map.removeSource(id); });
      OBS.shown = ''; OBS.shown3d = ''; obsBusy(0);
      if (window.wxPopupPrune) window.wxPopupPrune();
      return; }
    obsIcons();
    if (!map.getSource('wxobs')) map.addSource('wxobs', {type: 'geojson', data: {type: 'FeatureCollection', features: []}, maxzoom: 16,
      attribution: '<a href="https://webapps.eso.bg/joining/public/map/" target="_blank" rel="noopener">ESO EAD</a> (power lines)'});
    obsLayers(); OBS.shown = ''; OBS.shown3d = '';
    if (OBS.idx) obsRefresh(); else obsIndex();
  }); };
map.on('moveend', function(){ if (OBS.on) obsRefresh(); });
(window.wxLangRefresh = window.wxLangRefresh || []).push(function(){ obsMsg();
  ['obs-sym', 'obs-sym2'].forEach(function(id){ if (map.getLayer(id)) map.setLayoutProperty(id, 'text-field', obsLabel()); }); });
['obs-sym', 'obs-sym2', 'obs-3d', 'obs-sup', 'obs-line', 'obs-eso', 'obs-minor', 'obs-lift', 'obs-rail'].forEach(function(id){
  map.on('mouseenter', id, function(){ map.getCanvas().style.cursor = 'pointer'; });
  map.on('mouseleave', id, function(){ map.getCanvas().style.cursor = ''; }); });
// helpers for the SHARED click chooser in make_3d (items tagged _obs)
var OBS_N = {
  bg: {line: 'Далекопровод', minor: 'Електропровод', eso: 'Далекопровод', rail: 'Контактна мрежа на жп линия', tram: 'Контактна мрежа на трамвай',
       trolley: 'Контактна мрежа на тролейбус', lift: 'Лифт', tower: 'Стълб на далекопровод', pole: 'Стълб на електропровод', upole: 'Стълб',
       portal: 'Портал (подстанция)', catmast: 'Стълб на контактна мрежа', liftpylon: 'Опора на лифт', turbine: 'Ветрогенератор', mast: 'Мачта',
       mtower: 'Кула', ctower: 'Телекомуникационна кула', chimney: 'Комин', wtower: 'Водна кула', lighthouse: 'Фар', crane: 'Кран',
       flagpole: 'Пилон', antenna: 'Антена', silo: 'Силоз', windmill: 'Вятърна мелница', flare: 'Газов факел', gasometer: 'Газхолдер'},
  en: {line: 'Power line', minor: 'Power line', eso: 'Power line', rail: 'Railway overhead wire', tram: 'Tram overhead wire',
       trolley: 'Trolleybus overhead wire', lift: 'Lift', tower: 'Power line tower', pole: 'Power line pole', upole: 'Pole',
       portal: 'Portal (substation)', catmast: 'Catenary mast', liftpylon: 'Lift pylon', turbine: 'Wind turbine', mast: 'Mast',
       mtower: 'Tower', ctower: 'Communications tower', chimney: 'Chimney', wtower: 'Water tower', lighthouse: 'Lighthouse', crane: 'Crane',
       flagpole: 'Flagpole', antenna: 'Antenna', silo: 'Silo', windmill: 'Windmill', flare: 'Gas flare', gasometer: 'Gas holder'}};
var OBS_LIFTS = {
  bg: {chair_lift: 'Седалков лифт', gondola: 'Кабинков лифт', cable_car: 'Въжена линия', mixed_lift: 'Смесен лифт', drag_lift: 'Ски влек',
       't-bar': 'Ски влек', 'j-bar': 'Ски влек', platter: 'Ски влек', rope_tow: 'Въжен влек', magic_carpet: 'Лента за начинаещи',
       zip_line: 'Зиплайн', goods: 'Товарна въжена линия', abandoned: 'Изоставен лифт'},
  en: {chair_lift: 'Chair lift', gondola: 'Gondola lift', cable_car: 'Cable car', mixed_lift: 'Mixed lift', drag_lift: 'Drag lift',
       't-bar': 'T-bar lift', 'j-bar': 'J-bar lift', platter: 'Platter lift', rope_tow: 'Rope tow', magic_carpet: 'Magic carpet',
       zip_line: 'Zip line', goods: 'Goods ropeway', abandoned: 'Abandoned lift'}};
var OBS_TT = {
  bg: {communication: 'комуникационна', bell_tower: 'камбанария', cooling: 'охладителна', minaret: 'минаре', observation: 'наблюдателна',
       lighting: 'осветителна', defensive: 'крепостна', watchtower: 'наблюдателна', clock: 'часовникова'},
  en: {communication: 'communication', bell_tower: 'bell tower', cooling: 'cooling', minaret: 'minaret', observation: 'observation',
       lighting: 'lighting', defensive: 'defensive', watchtower: 'watchtower', clock: 'clock'}};
function obsCls(v){ return v >= 300 ? 400 : v >= 200 ? 220 : v >= 60 ? 110 : v >= 1 ? 20 : v > 0 ? 0.4 : 0; }
window.wxObsColor = function(p){ return (p.k === 'lift' || p.k === 'liftpylon') ? OBS_LIFT : (p.k === 'rail' || p.k === 'tram' || p.k === 'trolley') ? OBS_RAIL : OBS_INK; };
window.wxObsName = function(p){ var L = obsEn() ? 'en' : 'bg', q = obsEn() ? ['"', '"'] : ['„', '“'];
  var s = p.k === 'lift' ? (OBS_LIFTS[L][p.t] || OBS_N[L].lift) : (OBS_N[L][p.k] || p.k);
  if (p.k === 'mtower' && OBS_TT[L][p.t]) s += ' (' + OBS_TT[L][p.t] + ')';
  if (['line', 'minor', 'eso', 'tower', 'pole', 'portal'].indexOf(p.k) >= 0 && +p.v) s += ' ' + obsNum(+p.v) + ' kV';
  return s + (p.n ? ' ' + q[0] + p.n + q[1] : ''); };
window.wxObsSub = function(p){ var en = obsEn(), h = +p.h || 0;
  if (p.k === 'eso') return en ? 'route by ESO, approximate' : 'трасе по ЕСО, приблизително';
  if ((p.k === 'line' || p.k === 'minor') && !+p.v) return en ? 'voltage unknown' : 'напрежението не е известно';
  if (h > 0) return obsNum(h) + (en ? ' m' : ' м');
  if (h < 0) return '~' + obsNum(-h) + (en ? ' m (typical)' : ' м (типична)');
  return ''; };
function obsHeight(p){ var en = obsEn(), I = OBS.idx || {}, h = +p.h || 0, M = en ? ' m' : ' м', H = en ? 'Height: ' : 'Височина: ';
  if (h > 0) return H + obsNum(h) + M;
  if (!h) return H + (en ? 'no data' : 'няма данни');
  var t = H + '~' + obsNum(-h) + M + ' — ', c = obsCls(+p.v), tw = (I.towers || {})[String(c)];
  if (p.k === 'turbine'){ var f = (I.farms || {})[p.t], r = (I.wind || {}).range;
    return H + '~' + obsNum(-h) + M + (en ? ' to the blade tip — ' : ' до върха на перката — ') +
      (f ? (en ? 'typical for the ' + f.n + ' wind farm (' + f.m + ')' : 'типична за ВЕП „' + f.n + '“ (' + f.m + ')')
         : (en ? 'typical (' + r + ' m)' : 'типична (' + r + ' м)')); }
  if (p.k === 'liftpylon') return t + (en ? 'typical (' + (I.lift || {}).range + ' m)' : 'типична (' + (I.lift || {}).range + ' м)');
  if (p.k === 'portal'){ var PP = (I.portals || {})[String(c)] || {};   // owner 18.10: the texts
    if (!c) return t + (en ? 'the voltage is unknown, so a 110 kV portal is assumed.' : 'напрежението не е известно, приет е портал 110 kV.');
    if (PP.foreign) return t + (en ? 'from a foreign type design; no Bulgarian figure for ' + c + ' kV.' : 'по чужд типов проект; за ' + c + ' kV в български документи няма число.');
    return t + (en ? 'typical for a ' + c + ' kV portal (ESO)' : 'типична за портал ' + c + ' kV (ЕСО)') +
      (PP.beam && PP.beam < -h ? (en ? '; the wires hang at ~' + obsNum(PP.beam) + ' m' : '; проводниците са окачени на ~' + obsNum(PP.beam) + ' м') : '') + '.' +
      (PP.rods ? (en ? ' Some portals carry a lightning rod — up to ~' + obsNum(PP.rods) + ' m.' : ' Някои портали имат мълниеприемник — до ~' + obsNum(PP.rods) + ' м.') : ''); }
  if (tw) return t + (en ? 'typical for a ' + c + ' kV tower (' + tw.range + ' m); the lowest wire hangs at ~' + obsNum(tw.low) + ' m at the tower'
                         : 'типична за стълб ' + c + ' kV (' + tw.range + ' м); долният проводник е на ~' + obsNum(tw.low) + ' м при стълба');
  if (c === 20) return t + (en ? 'typical for a 20 kV pole' : 'типична за стълб 20 kV');
  if (c === 0.4) return t + (en ? 'typical for a low-voltage pole' : 'типична за стълб ниско напрежение');
  if (Math.abs(-h - (I.poleUnknown || 11)) < 0.01)
    return t + (en ? 'typical; the voltage is unknown, so the taller 20 kV pole is assumed' : 'типична; напрежението не е известно, приет е по-високият стълб 20 kV');
  return t + (en ? 'typical for a power line tower; the voltage is unknown' : 'типична за стълб на далекопровод; напрежението не е известно'); }
function obsWire(p){ var en = obsEn(), W = (OBS.idx || {}).wire || {}, w = W[String(obsCls(+p.v))] || W['0'] || [6, 6];
  return en ? 'The wires may hang as low as ' + obsNum(w[0]) + ' m above the ground' + (w[1] !== w[0] ? ' (' + obsNum(w[1]) + ' m in settlements)' : '') + ' — Bulgarian rules (Наредба № 3).'
            : 'Проводниците може да са само на ' + obsNum(w[0]) + ' м над земята' + (w[1] !== w[0] ? ' (' + obsNum(w[1]) + ' м в населено място)' : '') + ' — по Наредба № 3.'; }
window.wxObsDetail = function(p){ var en = obsEn(), I = OBS.idx || {}, sub = window.wxObsSub(p), wire = ['line', 'minor', 'eso'].indexOf(p.k) >= 0;
  var h = '<b>' + esc(window.wxObsName(p)) + '</b>' + (sub ? ' <span class="ptype">' + esc(sub) + '</span>' : '');
  if (OBS_TALL.indexOf(p.k) >= 0 || OBS_SUP.indexOf(p.k) >= 0) h += '<br>' + esc(obsHeight(p));
  if (wire) h += '<br>' + esc(obsWire(p));
  if (p.k === 'eso') h += '<br>' + (en ? 'The route is from ESO\'s map (approximate); OpenStreetMap does not have this line.'
                                     : 'Трасето е по картата на ЕСО (приблизително); в OpenStreetMap тази линия липсва.');
  if (p.k === 'rail' && I.rail) h += '<br>' + (en ? 'The contact wire hangs about ' + obsNum(I.rail.h) + ' m above the rails (' + obsNum(I.rail.lc) + ' m at level crossings).'
                                                  : 'Контактният проводник е на около ' + obsNum(I.rail.h) + ' м над релсите (' + obsNum(I.rail.lc) + ' м на прелезите).');
  if (wire) h += '<br><small>' + (en ? 'A line missing on the map does not mean there is none.' : 'Липсата на линия на картата не значи, че там няма.') + '</small>';
  return h; };
// ---- airfields, helipads and hospitals (ROADMAP 7, owner 19.10): ONE chip «Летища, площадки и болници» in
// «Въздушно пространство», OFF by default (ST aero). Straight from the OpenFreeMap vector tiles the page already
// loads for the 3D buildings (source 'ofm', OpenMapTiles schema, OpenStreetMap data): aerodromes = a dashed outline
// (aeroway, from zoom 10) + a plane sign with the name and ICAO (aerodrome_label, from zoom 8: name, class, icao,
// iata, ele); runways (aeroway, from 10); heliports / helipads (aeroway, an H; the tiles carry them from 14);
// hospitals (poi subclass 'hospital' ONLY - the tiles' class 'hospital' also holds clinics and nursing homes; a red
// cross, the tiles carry them from 14) + their grounds (landuse 'hospital', a red dashed outline from 12). Taxiways,
// aprons and gates are left out. Every aerodrome the tiles carry is shown (private and agricultural strips too -
// their kind is in the popup). Just above the zones, below the obstacles and the lightning (aeroBefore / obsSlot / liSlot).
var AERO_IDS = ['aero-field', 'aero-hosp-area', 'aero-rwy-area', 'aero-rwy', 'aero-heli', 'aero-hosp', 'aero-label'];
var AERO_CLICK = ['aero-label', 'aero-heli', 'aero-hosp', 'aero-rwy', 'aero-rwy-area'];
var AERO_INK = '#283593', AERO_RED = '#c62828', AERO_RWY = '#455a64';
var AERO_KIND = {
  bg: {international: 'Международно летище', 'public': 'Обществено летище', regional: 'Регионално летище', military: 'Военно летище',
       'private': 'Частно летище', other: 'Летище', heliport: 'Хеликоптерно летище', helipad: 'Хеликоптерна площадка', runway: 'Писта', hospital: 'Болница'},
  en: {international: 'International airport', 'public': 'Public airport', regional: 'Regional airport', military: 'Military airfield',
       'private': 'Private airfield', other: 'Airfield', heliport: 'Heliport', helipad: 'Helipad', runway: 'Runway', hospital: 'Hospital'}};
function aeroEn(){ return (window.LANG || 'bg') === 'en'; }
function aeroBefore(){ var ls = wxStyleLayers(), i; // the lowest obstacle / lightning layer, else just above the zones
  for (i = 0; i < ls.length; i++){ var id = ls[i].id; if (id.indexOf('obs-') === 0 || id === 'wxli-layer' || id === 'wxstorm-layer') return id; }
  return map.getLayer('o-CONDITIONAL') ? wxAboveOf('o-CONDITIONAL') : undefined; }
function aeroIcons(){ var pr = 2;
  function make(id, w, h, draw){ if (map.hasImage(id)) return;
    var c = document.createElement('canvas'); c.width = w * pr; c.height = h * pr;
    var x = c.getContext('2d'); x.scale(pr, pr); x.lineJoin = 'round'; x.lineCap = 'round'; draw(x);
    map.addImage(id, {width: w * pr, height: h * pr, data: x.getImageData(0, 0, w * pr, h * pr).data}, {pixelRatio: pr}); }
  // an aerodrome: a small aeroplane, dark blue with a white edge
  make('aero-plane', 20, 20, function(x){
    var p = function(){ x.beginPath(); x.moveTo(10, 2.5); x.lineTo(10, 17.5); x.moveTo(2.5, 10); x.lineTo(17.5, 10); x.moveTo(6.5, 16.5); x.lineTo(13.5, 16.5); };
    p(); x.lineWidth = 4.6; x.strokeStyle = 'rgba(255,255,255,0.95)'; x.stroke();
    p(); x.lineWidth = 2.2; x.strokeStyle = AERO_INK; x.stroke(); });
  // a heliport / helipad: a white disc with a dark blue H
  make('aero-h', 18, 18, function(x){
    x.beginPath(); x.arc(9, 9, 7.6, 0, 7); x.fillStyle = '#fff'; x.fill(); x.lineWidth = 1.6; x.strokeStyle = AERO_INK; x.stroke();
    x.fillStyle = AERO_INK; x.fillRect(5.6, 4.8, 1.8, 8.4); x.fillRect(10.6, 4.8, 1.8, 8.4); x.fillRect(5.6, 8.1, 6.8, 1.8); });
  // a hospital: a red cross on a white square
  make('aero-cross', 18, 18, function(x){
    x.fillStyle = '#fff'; x.strokeStyle = AERO_RED; x.lineWidth = 1.4; x.beginPath(); x.rect(1.5, 1.5, 15, 15); x.fill(); x.stroke();
    x.fillStyle = AERO_RED; x.fillRect(7.3, 4, 3.4, 10); x.fillRect(4, 7.3, 10, 3.4); }); }
function aeroLayers(){
  if (map.getLayer('aero-label') || !map.getSource('ofm')) return;
  aeroIcons();
  var b = aeroBefore(), L = function(o){ o.source = 'ofm'; map.addLayer(o, b); };
  var K = function(c){ return ['==', ['get', 'class'], c]; }, G = function(t){ return ['==', ['geometry-type'], t]; };
  var TXT = {'text-font': ['Noto Sans Regular'], 'text-size': 10.5, 'text-optional': true, 'text-max-width': 9};
  var HALO = function(col){ return {'text-color': col, 'text-halo-color': '#fff', 'text-halo-width': 1.4}; };
  L({id: 'aero-field', type: 'line', 'source-layer': 'aeroway', minzoom: 10, filter: ['all', K('aerodrome'), G('Polygon')], layout: {'line-join': 'round'},
     paint: {'line-color': AERO_INK, 'line-opacity': 0.85, 'line-dasharray': [3, 2], 'line-width': ['interpolate', ['linear'], ['zoom'], 10, 1, 15, 2]}});
  L({id: 'aero-hosp-area', type: 'line', 'source-layer': 'landuse', minzoom: 12, filter: K('hospital'), layout: {'line-join': 'round'},
     paint: {'line-color': AERO_RED, 'line-opacity': 0.7, 'line-dasharray': [2, 1.5], 'line-width': 1.2}});
  L({id: 'aero-rwy-area', type: 'fill', 'source-layer': 'aeroway', minzoom: 10, filter: ['all', K('runway'), G('Polygon')],
     paint: {'fill-color': AERO_RWY, 'fill-opacity': 0.75}});
  L({id: 'aero-rwy', type: 'line', 'source-layer': 'aeroway', minzoom: 10, filter: ['all', K('runway'), G('LineString')],
     paint: {'line-color': AERO_RWY, 'line-width': ['interpolate', ['exponential', 2], ['zoom'], 10, 1.5, 16, 26]}});
  L({id: 'aero-heli', type: 'symbol', 'source-layer': 'aeroway', minzoom: 12, filter: ['in', ['get', 'class'], ['literal', ['heliport', 'helipad']]],
     layout: {'icon-image': 'aero-h', 'icon-size': ['interpolate', ['linear'], ['zoom'], 12, 0.8, 16, 1.1], 'icon-allow-overlap': true}});
  L({id: 'aero-hosp', type: 'symbol', 'source-layer': 'poi', minzoom: 12, filter: ['all', K('hospital'), ['==', ['get', 'subclass'], 'hospital']],
     layout: Object.assign({'icon-image': 'aero-cross', 'icon-size': 0.9, 'icon-allow-overlap': true, 'text-field': ['coalesce', ['get', 'name'], ''],
       'text-anchor': 'left', 'text-offset': [0.9, 0]}, TXT), paint: HALO(AERO_RED)});
  L({id: 'aero-label', type: 'symbol', 'source-layer': 'aerodrome_label', minzoom: 8,
     layout: Object.assign({'icon-image': 'aero-plane', 'icon-size': ['interpolate', ['linear'], ['zoom'], 8, 0.75, 13, 1], 'icon-allow-overlap': true,
       'symbol-sort-key': ['match', ['get', 'class'], 'international', 0, 'public', 1, 'regional', 2, 'military', 3, 4],
       'text-field': ['concat', ['coalesce', ['get', 'name'], ''], ['case', ['has', 'icao'], ['concat', '\n', ['get', 'icao']], '']],
       'text-anchor': 'top', 'text-offset': [0, 0.9]}, TXT), paint: HALO(AERO_INK)}); }
window.wxSetAero = function(on){ window.wxAeroOn = on; var c = document.getElementById('cbAero');
  if (on){ if (c) c.classList.add('loading');
    whenReady(function(){ if (!window.wxAeroOn) return; aeroLayers();
      map.once('idle', function(){ var c2 = document.getElementById('cbAero'); if (c2) c2.classList.remove('loading'); }); }); }
  else { AERO_IDS.forEach(function(id){ if (map.getLayer(id)) map.removeLayer(id); });
    if (c) c.classList.remove('loading');
    if (window.wxPopupPrune) window.wxPopupPrune(); } };
AERO_CLICK.forEach(function(id){
  map.on('mouseenter', id, function(){ map.getCanvas().style.cursor = 'pointer'; });
  map.on('mouseleave', id, function(){ map.getCanvas().style.cursor = ''; }); });
// helpers for the SHARED click chooser in make_3d (items tagged _aero; _al = the layer the item came from)
function aeroKind(p){ var K = AERO_KIND[aeroEn() ? 'en' : 'bg'], c = p['class'];
  return p._al === 'aero-label' ? (K[c] || K.other) : p._al === 'aero-hosp' ? K.hospital : (K[c] || c || ''); }
window.wxAeroColor = function(p){ return p._al === 'aero-hosp' ? AERO_RED : AERO_INK; };
window.wxAeroName = function(p){ var k = aeroKind(p);
  if (p._al === 'aero-label' || p._al === 'aero-hosp') return p.name || k;
  return k + (p.ref ? ' ' + p.ref : ''); };
window.wxAeroSub = function(p){ return ((p._al === 'aero-label' || p._al === 'aero-hosp') && p.name) ? aeroKind(p) : ''; };
window.wxAeroDetail = function(p){ var en = aeroEn(), sub = window.wxAeroSub(p);
  var h = '<b>' + esc(window.wxAeroName(p)) + '</b>' + (sub ? ' <span class="ptype">' + esc(sub) + '</span>' : '');
  if (p._al === 'aero-label'){ var codes = [];
    if (p.icao) codes.push('ICAO: ' + p.icao);
    if (p.iata) codes.push('IATA: ' + p.iata);
    if (codes.length) h += '<br>' + esc(codes.join(' · '));
    if (p.ele != null && p.ele !== '' && isFinite(+p.ele)) h += '<br>' + (en ? 'Elevation: ' : 'Надморска височина: ') + Math.round(+p.ele) + (en ? ' m' : ' м'); }
  return h; };
// ---- NOTAM layer (/notam relay over the FAA NMS-API): temporary drone-relevant
// restrictions drawn ABOVE the zones. A lettered pin (P/R/D/M/!) at the centre + a
// dashed, lightly-filled (20%) circle/polygon coloured by category. Click shows the
// NOTAM; a click on one of OUR zones still wins. FAA carries the international series,
// so the popup + menu say "check B-FLIP". Single menu toggle; OFF by default.
window.wxNotamUrl = 'https://full-narwhal-4777.martinovem.deno.net/notam';
// letter -> colour, aligned with B-FLIP (R red, W/warnings orange, M magenta) and
// managed so the only orange (! = warnings) is a deeper orange than the amber
// "req-authorisation" zones, which it must not be confused with. G = GNSS interference
// (owner 11.10): yellow as B-FLIP draws it, with a DARK letter on its pin (white on yellow
// does not read).
var NT_COL = ['match', ['get','l'], 'P','#d0202a', 'R','#d0202a', 'D','#d0202a', 'M','#d81fbf', 'O','#00897b', '!','#ef6c00', 'G','#f9b800', '#d0202a'];
var NT_TL = {prohibited:{bg:'Забранена зона (NOTAM)',en:'Prohibited (NOTAM)'},
  danger:{bg:'Опасна зона (NOTAM)',en:'Danger (NOTAM)'},
  military:{bg:'Военна / сегрегирана (NOTAM)',en:'Military / segregated (NOTAM)'},
  restricted:{bg:'Ограничена зона (NOTAM)',en:'Restricted (NOTAM)'},
  obstacle:{bg:'Препятствие (NOTAM)',en:'Obstacle (NOTAM)'},
  warning:{bg:'Предупреждение (NOTAM)',en:'Warning (NOTAM)'},
  gnss:{bg:'GNSS смущения (NOTAM)',en:'GNSS interference (NOTAM)'}};
// Classic teardrop pin markers with the letter baked in, coloured by category and
// added once as map images. icon-anchor 'bottom' puts the tip on the NOTAM centre.
var NT_PINCOL = {P:'#d0202a', R:'#d0202a', D:'#d0202a', M:'#d81fbf', O:'#00897b', '!':'#ef6c00', G:'#f9b800'};
var NT_PININK = {G:'#2b2100'}; // letter colour where white would not read (default white)
function wxNotamPin(color, letter, ink){
  var pr = 2, W = 26, H = 36, r = 10, cx = W/2, cy = r + 2, tip = H - 1.5;
  var cv = document.createElement('canvas'); cv.width = W*pr; cv.height = H*pr;
  var ctx = cv.getContext('2d'); ctx.scale(pr, pr);
  function path(rr, ty){ ctx.beginPath(); ctx.arc(cx, cy, rr, 0, Math.PI*2);
    ctx.moveTo(cx - rr*0.72, cy + rr*0.7); ctx.lineTo(cx, ty); ctx.lineTo(cx + rr*0.72, cy + rr*0.7); ctx.closePath(); }
  path(r + 1.3, tip + 1); ctx.fillStyle = '#fff'; ctx.fill();   // white halo / outline
  path(r, tip); ctx.fillStyle = color; ctx.fill();               // coloured pin body
  ctx.fillStyle = ink || '#fff'; ctx.font = 'bold ' + (r+2) + 'px sans-serif';
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(letter, cx, cy + 0.5);
  return {width: W*pr, height: H*pr, data: ctx.getImageData(0, 0, W*pr, H*pr).data};
}
// red diagonal-hatch tile for the 'restricted' (R) NOTAM fill
function wxNotamHatch(color){
  var pr = 2, S = 8; var cv = document.createElement('canvas'); cv.width = S*pr; cv.height = S*pr;
  var ctx = cv.getContext('2d'); ctx.scale(pr, pr); ctx.strokeStyle = color; ctx.lineWidth = 1.3;
  for (var o = -S; o <= S; o += 4){ ctx.beginPath(); ctx.moveTo(o, S); ctx.lineTo(o + S, 0); ctx.stroke(); }
  return {width: S*pr, height: S*pr, data: ctx.getImageData(0, 0, S*pr, S*pr).data};
}
function notPinsReady(){ if (window._ntPinsDone) return; window._ntPinsDone = true;
  Object.keys(NT_PINCOL).forEach(function(k){ var id = 'ntpin-' + (k === '!' ? 'excl' : k);
    if (!map.hasImage(id)) map.addImage(id, wxNotamPin(NT_PINCOL[k], k, NT_PININK[k]), {pixelRatio: 2}); });
  if (!map.hasImage('nthatch')) map.addImage('nthatch', wxNotamHatch('#d0202a'), {pixelRatio: 2}); }
// ONE fetch of /notam -> normalised sources data + the picture's true age from
// the relay's X-Notam-Age-Ms header (= time since the newest successful FAA
// poll behind the picture, KV-restored or live). Shared by the first ON and the
// 10-minute auto-refresh, so the freshness stamp below never lies.
// Sofia FIR boundary for FIR-wide NOTAMs (fir:1, no outline of their own; owner 04.10):
// the land legs follow the state border the map already has (BGOUT: land + Danube),
// the Black Sea leg = the 8 points of the Bulgarian AIP ENR 2.1-1 (AIRAC AMDT 01/26,
// 22 JAN 26: 4344N 02837E ... 4159N 02802E), each end joined to the nearest border
// vertex so the dashed line has no gap at the coast.
var WX_FIR_SEA = [[28.6167,43.7333],[29.0,43.6667],[29.0333,43.7333],[30.5333,43.6833],[30.75,42.8],[29.0,42.1167],[28.3167,41.9833],[28.0333,41.9833]];
function wxFirLines(){
  var B = (typeof BGOUT !== 'undefined' && BGOUT) ? BGOUT : {features: []}, lines = [], all = [];
  (B.features || []).forEach(function(f){ var g = f.geometry; if (!g) return;
    (g.type === 'LineString' ? [g.coordinates] : g.type === 'MultiLineString' ? g.coordinates : []).forEach(function(ln){ lines.push(ln); all = all.concat(ln); }); });
  function near(q){ var best = null, bd = 1e9; all.forEach(function(c){ var d = Math.hypot((c[0] - q[0]) * Math.cos(q[1] * Math.PI / 180), c[1] - q[1]); if (d < bd){ bd = d; best = c; } }); return bd < 0.1 ? best : null; }
  var sea = WX_FIR_SEA.slice(), a = near(sea[0]), z = near(sea[sea.length - 1]);
  if (a) sea.unshift(a); if (z) sea.push(z);
  return lines.concat([sea]);
}
function notFetch(ok){
  fetch(window.wxNotamUrl, {cache: 'no-store'}).then(function(r){ if (!r.ok) throw 0;
    var age = parseInt(r.headers.get('X-Notam-Age-Ms') || '0', 10) || 0;
    return r.json().then(function(gj){ return {gj: gj, age: age}; });
  }).then(function(d){
    var gj = d.gj, ntNow = Date.now();
    // flag UPCOMING (not-yet-active) NOTAMs so they draw muted (fainter, same colour) - fut=1
    (gj.features||[]).forEach(function(f){ f.properties.fut = (f.properties.f && Date.parse(f.properties.f) > ntNow) ? 1 : 0; });
    // a second, point source for the centre pins (built from each feature's cx/cy);
    // FIR-wide pins usually share one Q centre, so each next one steps 0.25° east
    var fk = 0, firs = (gj.features||[]).filter(function(f){ return f.properties.fir === 1; });
    var pts = {type:'FeatureCollection', features:(gj.features||[]).map(function(f){
      var dx = f.properties.fir === 1 ? 0.25 * fk++ : 0;
      return {type:'Feature', properties:f.properties, geometry:{type:'Point', coordinates:[f.properties.cx + dx, f.properties.cy]}}; })};
    // the FIR boundary only while a FIR-wide NOTAM exists; its colour = theirs when they agree
    var fl = firs.length && firs.every(function(f){ return f.properties.l === firs[0].properties.l; }) ? firs[0].properties.l : '';
    var fir = {type:'FeatureCollection', features: firs.length ? [{type:'Feature', properties:{l: fl}, geometry:{type:'MultiLineString', coordinates: wxFirLines()}}] : []};
    window._ntDataAt = Date.now() - d.age; // moment the picture was truly fresh
    ok(gj, pts, fir);
    notFreshPaint();
  }).catch(function(){ wxBtnIdle('cbNotam'); notFreshPaint(); }); // fetch failed: whatever is drawn keeps AGEING honestly on the stamp/banner
}
function notEnsure(cb){
  if (map.getSource('wxnotam')){ cb(); return; }
  notFetch(function(gj, pts, fir){
    if (!map.getSource('wxnotam-fir')) map.addSource('wxnotam-fir', {type:'geojson', data:fir});
    if (!map.getSource('wxnotam')) map.addSource('wxnotam', {type:'geojson', data:gj,
      attribution:'NOTAM &copy; <a href="https://www.faa.gov/" target="_blank" rel="noopener">FAA</a> NMS'});
    if (!map.getSource('wxnotam-pts')) map.addSource('wxnotam-pts', {type:'geojson', data:pts});
    cb();
  }); // first load failing draws nothing rather than something stale (unchanged behaviour)
}
// while ON: refetch every 10 min so the picture (and its stamp) stays current
function notRefresh(){
  if (!window.wxNotamOn) return;
  if (!map.getSource('wxnotam')){ window.wxSetNotam(true); return; } // failed first load left no source: re-attempt the add on this tick
  notFetch(function(gj, pts, fir){
    if (map.getSource('wxnotam-fir')) map.getSource('wxnotam-fir').setData(fir);
    if (map.getSource('wxnotam')) map.getSource('wxnotam').setData(gj);
    if (map.getSource('wxnotam-pts')) map.getSource('wxnotam-pts').setData(pts);
  });
}
// Honest freshness for the pilot: the menu stamp "данни към HH:MM" (local) and,
// once the picture is older than NT_STALE_MIN (relay/FAA down for a while), a
// LOUD on-map banner - old data must never read as live. Painted on every
// fetch + every minute by the layer's timer.
var NT_STALE_MIN = 60;
function notFreshPaint(){
  var el = document.getElementById('wxntfresh'), bn = document.getElementById('wxntstale');
  var L = (window.LANG || 'bg'), at = window._ntDataAt;
  if (el){
    if (window.wxNotamOn && at){
      var d = new Date(at), p = function(n){ return (n < 10 ? '0' : '') + n; };
      el.style.display = '';
      el.textContent = (L === 'en' ? 'data as of ' : 'данни към ') + p(d.getHours()) + ':' + p(d.getMinutes());
    } else el.style.display = 'none';
  }
  var stale = !!(window.wxNotamOn && at && (Date.now() - at > NT_STALE_MIN * 60000));
  if (stale && !bn){
    bn = document.createElement('div'); bn.id = 'wxntstale';
    bn.style.cssText = 'position:absolute;left:50%;transform:translateX(-50%);bottom:46px;z-index:7;' +
      'background:#b71c1c;color:#fff;font:12px/1.4 sans-serif;padding:6px 12px;border-radius:8px;' +
      'box-shadow:0 1px 6px rgba(0,0,0,.35);pointer-events:none;max-width:86vw;text-align:center';
    map.getContainer().appendChild(bn);
  }
  if (bn){
    if (stale){
      var min = Math.round((Date.now() - at) / 60000);
      var tm = min >= 120 ? (Math.round(min / 60) + (L === 'en' ? ' h' : ' ч')) : (min + (L === 'en' ? ' min' : ' мин'));
      bn.textContent = (L === 'en' ? '⚠ NOTAM data is ' + tm + ' old'
                                   : '⚠ NOTAM данните са от преди ' + tm);
      bn.style.display = '';
    } else bn.style.display = 'none';
  }
}
window.wxSetNotam = function(on){ window.wxNotamOn = on;
  // freshness timer: repaint the stamp/banner every minute; refetch every 10th
  if (on && !window._ntTick){ window._ntTickN = 0;
    window._ntTick = setInterval(function(){
      window._ntTickN++;
      if (window._ntTickN % 10 === 0) notRefresh();
      notFreshPaint();
    }, 60000); }
  if (!on && window._ntTick){ clearInterval(window._ntTick); window._ntTick = null; }
  if (on){ wxBtnBusy('cbNotam', 'wxnotam'); notEnsure(function(){ if (!window.wxNotamOn) return;
    notPinsReady(); // register the pin + hatch images first
    // no beforeId = top of the stack = ABOVE the zones (owner's choice)
    // fill: 'restricted' (R) gets a diagonal hatch; the rest a lighter (12%) wash. Dashed edge for all.
    // upcoming (fut=1) NOTAMs: SAME colour, just muted via lower opacity so they don't read as active now
    if (!map.getLayer('notam-fill')) map.addLayer({id:'notam-fill', type:'fill', source:'wxnotam',
      filter:['!=',['get','l'],'R'], paint:{'fill-color':NT_COL, 'fill-opacity':['case',['==',['get','fut'],1],0.05,0.12]}});
    if (!map.getLayer('notam-hatch')) map.addLayer({id:'notam-hatch', type:'fill', source:'wxnotam',
      filter:['==',['get','l'],'R'], paint:{'fill-pattern':'nthatch', 'fill-opacity':['case',['==',['get','fut'],1],0.4,1]}});
    // edge: SOLID for restricted (R), dashed for the rest
    if (!map.getLayer('notam-line')) map.addLayer({id:'notam-line', type:'line', source:'wxnotam',
      filter:['!=',['get','l'],'R'], paint:{'line-color':NT_COL, 'line-width':1.4, 'line-opacity':['case',['==',['get','fut'],1],0.35,0.9], 'line-dasharray':[2,1.5]}});
    if (!map.getLayer('notam-line-r')) map.addLayer({id:'notam-line-r', type:'line', source:'wxnotam',
      filter:['==',['get','l'],'R'], paint:{'line-color':'#d0202a', 'line-width':1.6, 'line-opacity':['case',['==',['get','fut'],1],0.4,0.95]}});
    // FIR-wide NOTAMs: the whole Sofia FIR as a translucent band + a dashed line on top,
    // no fill (their pins carry the detail). The band keeps it apart from the plain state
    // border it runs along on land (owner 04.10: clearly visible there; 11.10: thinner -
    // 11 px read as a highlighter once the GNSS NOTAM drew it yellow).
    if (!map.getLayer('notam-fir-band')) map.addLayer({id:'notam-fir-band', type:'line', source:'wxnotam-fir',
      layout:{'line-join':'round', 'line-cap':'round'}, paint:{'line-color':NT_COL, 'line-width':5, 'line-opacity':0.3, 'line-blur':1}});
    if (!map.getLayer('notam-fir')) map.addLayer({id:'notam-fir', type:'line', source:'wxnotam-fir',
      paint:{'line-color':NT_COL, 'line-width':2.5, 'line-opacity':1, 'line-dasharray':[3,2]}});
    if (!map.getLayer('notam-pin')) map.addLayer({id:'notam-pin', type:'symbol', source:'wxnotam-pts',
      layout:{'icon-image':['match',['get','l'],'P','ntpin-P','D','ntpin-D','M','ntpin-M','R','ntpin-R','O','ntpin-O','G','ntpin-G','ntpin-excl'],
        'icon-anchor':'bottom', 'icon-size':1, 'icon-allow-overlap':true, 'icon-ignore-placement':true},
      paint:{'icon-opacity':['case',['==',['get','fut'],1],0.5,1]}}); }); }
  else { wxBtnIdle('cbNotam'); ['notam-fill','notam-hatch','notam-line','notam-line-r','notam-fir-band','notam-fir','notam-pin'].forEach(function(id){ if (map.getLayer(id)) map.removeLayer(id); });
    if (map.getSource('wxnotam-fir')) map.removeSource('wxnotam-fir');
    if (map.getSource('wxnotam')) map.removeSource('wxnotam');
    if (map.getSource('wxnotam-pts')) map.removeSource('wxnotam-pts');
    if (window.wxPopupPrune) window.wxPopupPrune(); // its NOTAMs leave an open popup too
    notFreshPaint(); } // hides the stamp + banner
};
// NOTAM colour / label / detail helpers, exposed for the UNIFIED click chooser in
// make_3d: a NOTAM over a zone now appears in the SAME "choose which" list as the
// overlapping zones (instead of a separate popup that hid one of them).
window.wxNotamColor = function(l){ return NT_PINCOL[l] || '#d0202a'; };
window.wxNotamName = function(p){ var L = (window.LANG || 'bg'); return (NT_TL[p.cat] && NT_TL[p.cat][L]) || 'NOTAM'; };
// compact UTC formatter for NOTAM validity (NOTAM times are UTC)
window.wxNtFmt = function(iso){ if (!iso) return ''; var d = new Date(iso); if (isNaN(d)) return String(iso);
  var p = function(n){ return (n < 10 ? '0' : '') + n; };
  return p(d.getUTCDate()) + '.' + p(d.getUTCMonth()+1) + ' ' + p(d.getUTCHours()) + ':' + p(d.getUTCMinutes()) + 'Z'; };
window.wxNotamSub = function(p){ var L = (window.LANG || 'bg');
  return (String(p.t).toUpperCase() === 'PERM') ? (L === 'en' ? 'permanent' : 'постоянен') : (wxNtFmt(p.f) + ' – ' + wxNtFmt(p.t)); };
window.wxNotamDetail = function(p){ var L = (window.LANG || 'bg');
  var perm = String(p.t).toUpperCase() === 'PERM';
  var fut = p.f && Date.parse(p.f) > Date.now();
  var when = perm ? (L === 'en' ? 'permanent' : 'постоянен')
    : fut ? ((L === 'en' ? 'Upcoming · active from ' : 'Предстоящ · активен от ') + '<b>' + esc(wxNtFmt(p.f)) + '</b>' + (p.t ? (' ' + (L === 'en' ? 'to ' : 'до ') + esc(wxNtFmt(p.t))) : ''))
    : ((L === 'en' ? 'Active · until ' : 'Активен · до ') + '<b>' + esc(wxNtFmt(p.t)) + '</b>');
  return '<b>' + esc(wxNotamName(p)) + '</b><br><small>' + esc(p.q || '') + ' · ' + when + '</small>' +
    (p.fir === 1 ? ('<br><small><b>' + (L === 'en' ? 'Applies to the whole Sofia FIR (Bulgaria and its Black Sea area)' : 'Важи за целия FIR София (България и морската му част)') + '</b></small>') : '') +
    (p.txt ? ('<br>' + esc(p.txt)) : '') +
    // source line = ONLY what this layer actually uses (FAA); the official
    // B-FLIP pointer lives once, in the page disclaimer (owner, 16.09). The
    // series note stays in the menu key as "Международна серия (FAA)".
    '<br><small>' + (L === 'en' ? 'NOTAM data: ' : 'NOTAM данни: ') +
    '<a href="https://www.faa.gov/" target="_blank" rel="noopener">FAA</a></small>'; };
// hover cursor over NOTAM features
['notam-fill','notam-hatch','notam-pin'].forEach(function(id){
  map.on('mouseenter', id, function(){ map.getCanvas().style.cursor = 'pointer'; });
  map.on('mouseleave', id, function(){ map.getCanvas().style.cursor = ''; });
});
// ---- wind particles (MapLibre): shared engine on a DOM canvas over the map ----
var windCanvas = null, windEngine = null, windOn = false, windResize = null, windMove = null, windMoveEnd = null;
function windProject(lon, lat){ var pt = map.project([lon, lat]); return {x: pt.x, y: pt.y}; }
function windUnproject(x, y){ var ll = map.unproject([x, y]); return {lon: ll.lng, lat: ll.lat}; }
var windDark = function(){ return window.wxDark !== false; }; // dark palette on the satellite (3D mode, default), light on the flat OSM basemap (2D mode)
function windBounds(){ var b = map.getBounds(); return {w: b.getWest(), s: b.getSouth(), e: b.getEast(), n: b.getNorth()}; }
function windSize(){ if (!windCanvas) return; var el = map.getContainer(), dpr = window.devicePixelRatio || 1;
  windCanvas.width = Math.round(el.clientWidth * dpr); windCanvas.height = Math.round(el.clientHeight * dpr);
  windCanvas.style.width = el.clientWidth + 'px'; windCanvas.style.height = el.clientHeight + 'px';
  windCanvas._dpr = dpr; windCanvas.getContext('2d').setTransform(dpr, 0, 0, dpr, 0, 0); } // crisp + same size on Retina/phone
window.wxSetWind = function(on){ windOn = on; window.wxWindState.on = on;
  if (on){ var _wb = document.getElementById('wxwind'); if (_wb) _wb.classList.add('loading'); // honest cue: pulse until the grid lands (the fetch cb below clears it) or a 30 s safety cap
    clearTimeout(window._windCue); window._windCue = setTimeout(function(){ wxBtnIdle('wxwind'); }, 30000);
    if (!windCanvas){ windCanvas = document.createElement('canvas'); windCanvas.className = 'wxwindcv';
      windCanvas.style.cssText = 'position:absolute;inset:0;pointer-events:none;z-index:5'; // over the GL map; thin/soft so zones read through
      map.getContainer().appendChild(windCanvas); }
    windSize(); windResize = function(){ windSize(); };
    map.on('resize', windResize); window.addEventListener('resize', windResize);
    windMove = function(){ if (windEngine) windEngine.setMoving(true); };     // pan/zoom: dashes ride with the map
    windMoveEnd = function(){ if (windEngine) windEngine.setMoving(false); }; // stopped: full flowing trails return
    map.on('movestart', windMove); map.on('zoomstart', windMove);
    map.on('moveend', windMoveEnd); map.on('zoomend', windMoveEnd);
    // Start the particle loop NOW, independent of the network. The engine reads
    // wxWindState live each frame, so it draws nothing until the grid lands and
    // then fills in by itself. Gating creation on the fetch left the loop
    // unstarted whenever the fetch was slow/failed/stale-path (pulse cleared on
    // timeout, no particles) until an F5 read the cached grid synchronously.
    if (windEngine) windEngine.stop();
    windEngine = window.wxWindEngine({canvas: windCanvas, project: windProject, unproject: windUnproject, bounds: windBounds, darkBg: windDark, afterDraw: (typeof windMask !== 'undefined' ? windMask : null)});
    window.wxWindFetch(function(){ if (windOn) wxBtnIdle('wxwind'); }); // grid in -> stop the pulse (engine already running)
  } else { wxBtnIdle('wxwind');
    if (windEngine){ windEngine.stop(); windEngine = null; }
    if (windResize){ map.off('resize', windResize); window.removeEventListener('resize', windResize); windResize = null; }
    if (windMove){ map.off('movestart', windMove); map.off('zoomstart', windMove); windMove = null; }
    if (windMoveEnd){ map.off('moveend', windMoveEnd); map.off('zoomend', windMoveEnd); windMoveEnd = null; }
    if (windCanvas){ windCanvas.remove(); windCanvas = null; }
  }
};
// ---- live aircraft (relay over adsb.fi/adsb.lol), drawn above the zones ----
var plnTimer = null, plnOn = false, plnImagesReady = false, plnClickAdded = false, plnFresh = 0;
function plnAddImages(cb){ // render the shared SVG silhouettes into map images (2x for crisp icons)
  var kinds = Object.keys(window.wxPlnKinds), left = kinds.length;
  kinds.forEach(function(kn){
    if (map.hasImage('wxpln-' + kn)){ if (!--left){ plnImagesReady = true; cb(); } return; }
    var k = window.wxPlnKinds[kn], sz = k.w * 2, img = new Image();
    img.onload = function(){
      var cv = document.createElement('canvas'); cv.width = sz; cv.height = sz;
      var ctx = cv.getContext('2d'); ctx.drawImage(img, 0, 0, sz, sz);
      if (!map.hasImage('wxpln-' + kn)) map.addImage('wxpln-' + kn, ctx.getImageData(0, 0, sz, sz));
      if (!--left){ plnImagesReady = true; cb(); }
    };
    img.onerror = function(){ if (!--left) cb(); };
    img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(
      '<svg xmlns="http://www.w3.org/2000/svg" width="' + sz + '" height="' + sz + '" viewBox="-16 -16 32 32">' + k.svg + '</svg>');
  });
}
var plnData = null;
function plnFC(d){
  var f = [];
  ((d && d.ac) || []).forEach(function(a){
    if (a.lat == null || a.lon == null || a.alt_baro === 'ground' || !window.wxFlOk(a.alt_baro)) return; // airborne + within the height filter
    f.push({type: 'Feature', geometry: {type: 'Point', coordinates: [a.lon, a.lat]},
      properties: {rot: Math.round(a.track != null ? a.track : 0), kind: window.wxPlnKind(a),
        info: window.wxPlaneInfo(a), id: a.hex || ((a.flight || '') + a.lat)}});
  });
  return {type: 'FeatureCollection', features: f};
}
var plnPopup = null, plnPopupId = null;
function plnFollowPopup(fc){ // MapLibre popups don't track a moving feature -> move it with the aircraft
  if (!plnPopup || !plnPopup.isOpen() || plnPopupId == null) return;
  var i, feat = null; for (i = 0; i < fc.features.length; i++){ if (fc.features[i].properties.id === plnPopupId){ feat = fc.features[i]; break; } }
  if (feat){ plnPopup.setLngLat(feat.geometry.coordinates); plnPopup.setHTML(feat.properties.info); }
  else plnPopup.remove(); // aircraft gone / filtered out -> close the popup
}
window.wxReapply.push(function(){ var s = map.getSource('wxpln'); if (s && plnData){ var fc = plnFC(plnData); s.setData(fc); plnFollowPopup(fc); } });
function plnLoad(){
  if (document.hidden) return; // background tab: skip the poll
  fetch(window.wxPlnUrl).then(function(r){
    if (!r.ok) throw new Error('relay ' + r.status);
    return r.json();
  }).then(function(d){
    if (!plnOn) return;
    plnFresh = Date.now(); plnData = d;
    whenReady(function(){
      if (!plnOn) return;
      var src = map.getSource('wxpln');
      if (src){ var fc = plnFC(d); src.setData(fc); plnFollowPopup(fc); return; }
      plnAddImages(function(){
        if (!plnOn || map.getSource('wxpln')) return;
        map.addSource('wxpln', {type: 'geojson', data: plnFC(d),
          attribution: 'Aircraft <a href="https://adsb.fi/" target="_blank" rel="noopener">adsb.fi</a> / <a href="https://adsb.lol/" target="_blank" rel="noopener">adsb.lol</a> (ODbL)'});
        map.addLayer({id: 'wxpln-layer', type: 'symbol', source: 'wxpln', // no beforeId: planes go on top
          layout: {'icon-image': ['concat', 'wxpln-', ['get', 'kind']],
            'icon-size': window.innerWidth <= 640 ? 0.36 : 0.5, // phones get smaller planes
            'icon-rotate': ['get', 'rot'], 'icon-rotation-alignment': 'map',
            'icon-allow-overlap': true, 'icon-ignore-placement': true}});
        if (!plnClickAdded){ plnClickAdded = true;
          map.on('click', 'wxpln-layer', function(e){
            var f = e.features[0]; if (plnPopup) plnPopup.remove();
            plnPopupId = f.properties.id;
            plnPopup = new maplibregl.Popup({offset: 16, maxWidth: '270px', className: 'wxplnpop'})
              .setLngLat(f.geometry.coordinates).setHTML(f.properties.info).addTo(map);
          });
        }
      });
    });
  }).catch(function(){
    // no fresh data: bridge brief hiccups, but after ~90 s wipe the planes —
    // an honest empty sky beats a frozen "live" one
    if (plnOn && plnFresh && Date.now() - plnFresh > 90000){
      var s = map.getSource('wxpln');
      if (s) s.setData({type: 'FeatureCollection', features: []});
      plnFresh = 0;
    }
  });
}
window.wxSetPlanes = function(on){ plnOn = on;
  if (on){ wxBtnBusy('plnbtn', 'wxpln'); plnLoad(); plnTimer = setInterval(plnLoad, 7000); } // solid the moment the planes source appears on the map
  else { clearInterval(plnTimer); wxBtnIdle('plnbtn');
    if (plnPopup){ plnPopup.remove(); plnPopup = null; plnPopupId = null; } // layer off -> its aircraft popup goes too
    if (map.getLayer('wxpln-layer')) map.removeLayer('wxpln-layer');
    if (map.getSource('wxpln')) map.removeSource('wxpln'); }
};
// ---- OGN / FLARM low-level traffic (direct browser fetch), drawn on top ----
var ognTimer = null, ognOn = false, ognClickAdded = false, ognFresh = 0;
function ognAddImages(cb){ // rasterise the shared teal SVG icons into map images (2x for crispness)
  var kinds = Object.keys(window.wxOgnKinds), left = kinds.length;
  kinds.forEach(function(kn){
    if (map.hasImage('wxogn-' + kn)){ if (!--left) cb(); return; }
    var k = window.wxOgnKinds[kn], sz = k.w * 2, img = new Image();
    img.onload = function(){
      var cv = document.createElement('canvas'); cv.width = sz; cv.height = sz;
      cv.getContext('2d').drawImage(img, 0, 0, sz, sz);
      if (!map.hasImage('wxogn-' + kn)) map.addImage('wxogn-' + kn, cv.getContext('2d').getImageData(0, 0, sz, sz));
      if (!--left) cb();
    };
    img.onerror = function(){ if (!--left) cb(); };
    img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(
      '<svg xmlns="http://www.w3.org/2000/svg" width="' + sz + '" height="' + sz + '" viewBox="-16 -16 32 32">' + k.svg + '</svg>');
  });
}
function ognFC(list){
  var f = [];
  list.forEach(function(a){ var kind = window.wxOgnKind(a.typ);
    f.push({type: 'Feature', geometry: {type: 'Point', coordinates: [a.lon, a.lat]},
      properties: {rot: (window.wxOgnNoRot[kind] || !isFinite(a.track)) ? 0 : Math.round(a.track),
        kind: kind, info: window.wxOgnInfo(a), id: a.crc}}); });
  return {type: 'FeatureCollection', features: f};
}
var ognPopup = null, ognPopupId = null, ognLast = null;
function ognFollowPopup(fc){ // move the popup with its OGN object as it flies
  if (!ognPopup || !ognPopup.isOpen() || ognPopupId == null) return;
  var i, feat = null; for (i = 0; i < fc.features.length; i++){ if (fc.features[i].properties.id === ognPopupId){ feat = fc.features[i]; break; } }
  if (feat){ ognPopup.setLngLat(feat.geometry.coordinates); ognPopup.setHTML(feat.properties.info); }
  else ognPopup.remove();
}
// retranslate the open 3D aircraft/OGN popup on a BG/EN switch
(window.wxLangRefresh = window.wxLangRefresh || []).push(function(){ if (plnData) plnFollowPopup(plnFC(plnData)); });
(window.wxLangRefresh = window.wxLangRefresh || []).push(function(){ if (ognLast) ognFollowPopup(ognFC(ognLast)); });
var ognViaRelay = 0, ognBusy = false; // until ognViaRelay ask the relay directly; one poll at a time
function ognGet(u, ms){ // text with a time limit, so a hanging site can't stall the 10 s poll
  var ac = window.AbortController ? new AbortController() : null, t = ac ? setTimeout(function(){ ac.abort(); }, ms) : 0;
  return fetch(u, ac ? {signal: ac.signal} : {}).then(function(r){ clearTimeout(t); if (!r.ok) throw new Error('ogn ' + r.status); return r.text(); },
    function(e){ clearTimeout(t); throw e; });
}
function ognLoad(){
  if (document.hidden || ognBusy) return;
  ognBusy = true;
  // live.glidernet.org first; if it fails, the same markers from the relay at once, and
  // straight from the relay for the next 5 min before live.glidernet.org is tried again
  (Date.now() < ognViaRelay ? ognGet(window.wxOgnRelay, 15000)
    : ognGet(window.wxOgnUrl, 8000).catch(function(){ ognViaRelay = Date.now() + 300000; return ognGet(window.wxOgnRelay, 15000); }))
  .then(function(txt){
    ognBusy = false;
    if (!ognOn) return; ognFresh = Date.now();
    var list = window.wxOgnParse(txt); ognLast = list;
    whenReady(function(){
      if (!ognOn) return;
      var src = map.getSource('wxogn');
      if (src){ var fc = ognFC(list); src.setData(fc); ognFollowPopup(fc); return; }
      ognAddImages(function(){
        if (!ognOn || map.getSource('wxogn')) return;
        map.addSource('wxogn', {type: 'geojson', data: ognFC(list),
          attribution: 'Low traffic <a href="https://www.glidernet.org/" target="_blank" rel="noopener">OGN</a> (ODbL)'});
        map.addLayer({id: 'wxogn-layer', type: 'symbol', source: 'wxogn', // on top, like the aircraft
          layout: {'icon-image': ['concat', 'wxogn-', ['get', 'kind']],
            'icon-size': window.innerWidth <= 640 ? 0.4 : 0.5,
            'icon-rotate': ['get', 'rot'], 'icon-rotation-alignment': 'map',
            'icon-allow-overlap': true, 'icon-ignore-placement': true}});
        if (!ognClickAdded){ ognClickAdded = true;
          map.on('click', 'wxogn-layer', function(e){
            var f = e.features[0]; if (ognPopup) ognPopup.remove();
            ognPopupId = f.properties.id;
            ognPopup = new maplibregl.Popup({offset: 16, maxWidth: '260px', className: 'wxplnpop'})
              .setLngLat(f.geometry.coordinates).setHTML(f.properties.info).addTo(map);
          });
        }
      });
    });
  }).catch(function(){
    ognBusy = false;
    if (ognOn && ognFresh && Date.now() - ognFresh > 90000){ // honest empty sky after ~90 s
      var s = map.getSource('wxogn'); if (s) s.setData({type: 'FeatureCollection', features: []}); ognFresh = 0;
    }
  });
}
window.wxSetOgn = function(on){ ognOn = on;
  if (on){ wxBtnBusy('ognbtn', 'wxogn'); ognLoad(); ognTimer = setInterval(ognLoad, 10000); }
  else { clearInterval(ognTimer); wxBtnIdle('ognbtn');
    if (ognPopup){ ognPopup.remove(); ognPopup = null; ognPopupId = null; } // layer off -> its popup goes too
    if (map.getLayer('wxogn-layer')) map.removeLayer('wxogn-layer');
    if (map.getSource('wxogn')) map.removeSource('wxogn'); }
};
})();
""" + WX_RESTORE_JS
