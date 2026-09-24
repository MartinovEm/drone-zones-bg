"""Shared weather widget (Open-Meteo forecast) injected into both map pages.

The widget is a small chip in the top-left corner (under the search box) showing
current conditions for the MAP CENTER; tapping it expands a card with a 7-day
hourly forecast: temperature, wind at 10/80/120 m, gusts, direction arrows and
precipitation probability. Hours with strong wind/gusts are highlighted so
no-fly hours are obvious. Data: Open-Meteo (keyless, CORS-open, verified);
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
"""

WX_HTML = r"""<div id="wx">
 <button id="wxchip" aria-label="weather">…</button>
 <div id="wxpanel" hidden>
  <div class="wxhead"><span class="wxplace" id="wxplace"></span><button class="wxclose" id="wxclose" aria-label="close">✕</button></div>
  <div class="wxlayers">
   <button class="wxlbtn" id="wxcld" aria-label="clouds">☁</button>
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
  <div id="wxbody"></div>
  <div class="wxfoot"><span id="wxfootlbl"></span> <a href="https://open-meteo.com/" target="_blank" rel="noopener">Open-Meteo</a></div>
 </div>
</div>"""

WX_JS = r"""
// ---- weather widget (Open-Meteo, map-center based) ----
(function(){
var WXT = {
 bg:{now:'Сега',hum:'влажност',gust:'порив',rain:'дъжд %',rmm:'валеж мм',cld:'облаци',sunrise:'изгрев',sunset:'залез',today:'Днес',
     hh:'час',t:'°C',w10:'вятър 10 м',w80:'вятър 80 м',w120:'вятър 120 м',ms:'м/с',foot:'Прогноза:',nodata:'Няма данни за тук',wxLimitDay:'Изчерпан дневен лимит на метео заявките — нулира се в {t}',wxLimit:'Изчерпан лимит на метео заявките (временно)',wxDown:'Метео услугата временно е недостъпна',
     days:['нд','пн','вт','ср','чт','пт','сб'],title:'Метео прогноза (центъра на картата)',
     bCld:'Облаци — сателит сега, модел напред (плъзгач)',bRad:'Дъжд — радар сега, модел напред (плъзгач)',bPln:'Самолети на живо (adsb.fi / adsb.lol)',
     bWind:'Вятър — частиците текат по вятъра (модел Open-Meteo)',height:'Височина',bSnow:'Прогноза за сняг +72 ч (модел Open-Meteo, в см)',
     bOgn:'Нисък трафик — планери/парапланери/лека авиация (OGN/FLARM; само където има приемник)',
     fcNote:'моделът може да пропуска локални валежи',
     drz:'ръмеж',lgt:'слаб',mod:'умерен',hvy:'силен',str:'буря',hail:'град',snTrace:'следа',snLgt:'слаб',snMod:'умерен',snStr:'силен',snHvy:'обилен',snowRow:'сняг см',
     bGj:'GPS смущения (наши данни от самолетите, последни 12 ч) — дял самолети с влошен GPS на височина; празно = няма прелетели самолети; не значи смущение при земята',gjX:'малко данни',gjG:'чисто',gjY:'2–10% смутени',gjR:'>10% смутени',gjNote:'На самолетна височина',gjLive:'На живо',gjW12:'12ч',gjW24:'24ч',gjHr:'ч',gjStamp:'данни към',
     rvNote:'нощем слабото ехо може да е шум'},
 en:{now:'Now',hum:'humidity',gust:'gust',rain:'rain %',rmm:'rain mm',cld:'clouds',sunrise:'sunrise',sunset:'sunset',today:'Today',
     hh:'hour',t:'°C',w10:'wind 10 m',w80:'wind 80 m',w120:'wind 120 m',ms:'m/s',foot:'Forecast:',nodata:'No data for this spot',wxLimitDay:'Weather request limit reached — resets at {t}',wxLimit:'Weather request limit reached (temporary)',wxDown:'Weather service temporarily unavailable',
     days:['Su','Mo','Tu','We','Th','Fr','Sa'],title:'Weather forecast (map center)',
     bCld:'Clouds — satellite now, model ahead (slider)',bRad:'Rain — radar now, model ahead (slider)',bPln:'Live aircraft (adsb.fi / adsb.lol)',
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
function wxChipHTML(){
  var t = WXT[wxLang()];
  if (!wxData || !wxData.current || wxErr){ // no usable current weather -> show just the place name
    var nm0 = (wxNames[wxCellOf(map.getCenter()) + '|' + wxLang()] || '').split(',')[0];
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
  nm = nm.split(',')[0]; // short form in the chip; the panel shows the full name
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
  for (i = start; i < end; i++){
    hr += '<td>' + times[i].slice(11, 16) + '</td>';
    ic += '<td>' + wxIco(H.weather_code[i], H.is_day[i]) + '</td>';
    te += '<td>' + Math.round(H.temperature_2m[i]) + '°</td>';
    var cc = H.cloud_cover ? H.cloud_cover[i] : null;
    cl += '<td>' + (cc == null ? '—' : cc + '%') + '</td>';
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
  }
  return '<div class="wxscrollwrap"><div class="wxscroll" id="wxscroll"><table class="wxtab">' +
    wxRow(t.hh, hr, 'wxhr') + wxRow('', ic) + wxRow(t.t, te) + wxRow(t.cld, cl) +
    wxRow(t.w10, w1) + wxRow(t.w80, w8) + wxRow(t.w120, w12) +
    wxRow(t.gust, gu) + wxRow(t.rain, ra) + wxRow(t.rmm, rm) + wxRow(t.snowRow, sn) +
    '</table></div></div>';
}
function wxRender(){
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
  var sun = '<div class="wxsun"><span>🌅 ' + t.sunrise + ' ' + sr.slice(11, 16) + ' · 🌇 ' + t.sunset + ' ' + ss.slice(11, 16) + '</span>' +
    '<span class="wxnav"><button class="wxnavbtn" id="wxleft">◀</button><button class="wxnavbtn" id="wxright">▶</button></span></div>';
  wxBody.innerHTML = now + wxDayTabs() + sun + wxTable();
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
    try{ var cw = JSON.parse(localStorage.getItem('wxwx'));
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
    'wind_speed_10m,wind_speed_80m,wind_speed_120m,wind_gusts_10m,wind_direction_10m,wind_direction_80m,wind_direction_120m' +
    '&daily=sunrise,sunset&wind_speed_unit=ms&timezone=auto&forecast_days=8'; // today + 7 full days ahead
  fetch(u).then(function(r){ var st = r.status; return r.json().then(function(d){ return [st, d]; }, function(){ return [st, null]; }); })
    .then(function(sd){ var st = sd[0], d = sd[1];
      if (d && d.hourly && d.current){ wxErr = null; wxData = d; wxRetryMs = 7000; if (wxDay >= d.daily.time.length) wxDay = 0;
        try{ localStorage.setItem('wxwx', JSON.stringify({cell: cell, at: Date.now(), data: d})); }catch(e){}
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
window.closeWxPanel = function(){ wxOpen = false; wxPanel.hidden = true; };
wxChip.onclick = function(e){ e.stopPropagation(); wxOpen = !wxOpen; wxPanel.hidden = !wxOpen;
  if (wxOpen){ if (window.closePanel) window.closePanel(); if (window.collapseLoupe) window.collapseLoupe(); if (window.closeBmPanel) window.closeBmPanel(); wxRender(); } };
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
['cbAirC:airc:wxSetAirC', 'cbAirS:airs:wxSetAirS', 'cbNotam:notam:wxSetNotam'].forEach(function(s){
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
window.wxFcFetch = function(cb){
  var S = window.wxFcState;
  if (S.data && Date.now() - S.at < 1800000){ cb(); return; } // model refresh: 30 min is plenty
  if (!S.data){
    // the grid request is HEAVY in Open-Meteo's rate accounting (294 points x 3
    // models count as hundreds of calls), so a fresh page — e.g. right after a
    // 2D<->3D switch with 🌦 restored on — reuses the previous page's grid from
    // localStorage instead of refetching; a burst of switches stays within limits
    try{ var c = JSON.parse(localStorage.getItem('wxfcdata4'));
      if (c && c.data && c.data.s && c.data.c && Date.now() - c.at < 1800000){ S.data = c.data; S.at = c.at; cb(); return; }
    }catch(e){} // wxfcdata4: cache holds rain (v) + snow (s) + clouds (c); only reuse if all present
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
        '&hourly=precipitation,snowfall,cloud_cover&forecast_hours=72&timezone=UTC&models=icon_eu,gfs_seamless,ecmwf_ifs025')
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
      S.data = {t: d[0].hourly.time,
        v: d.map(function(x){ return fcMax(x.hourly, 'precipitation'); }),
        s: d.map(function(x){ return fcMax(x.hourly, 'snowfall'); }),
        c: d.map(function(x){ return fcMax(x.hourly, 'cloud_cover'); })};
      S.at = Date.now(); S.rms = 12000;
      try{ localStorage.setItem('wxfcdata4', JSON.stringify({at: S.at, data: S.data})); }catch(e){}
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
  S.lastSnow = mxv; // wxFcLabel uses this to say "no snow (model)" on a dry hour
  var cv = document.createElement('canvas'); cv.width = W; cv.height = H;
  var ctx = cv.getContext('2d'), out = ctx.createImageData(W, H), od = out.data;
  // snowfall cm/h -> VIOLET ramp (light -> heavy); deliberately distinct from the rain palette
  var TH = [0.1, 0.5, 1, 2, 4], CO = [[217,199,240],[183,154,230],[144,96,216],[106,47,184],[74,26,138]];
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
      if (v < TH[0]) continue; // no snow stays transparent
      var k = 0; while (k < TH.length - 1 && v >= TH[k + 1]) k++;
      var i4 = (py * W + px) * 4;
      od[i4] = CO[k][0]; od[i4 + 1] = CO[k][1]; od[i4 + 2] = CO[k][2]; od[i4 + 3] = 180;
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
  if (S.data && Date.now() - S.at < 1800000){ cb(); return; }
  if (!S.data){
    try{ var c = JSON.parse(localStorage.getItem('wxwinddata4'));
      if (c && Date.now() - c.at < 1800000 && c.data && c.data.u10 && c.data.u10.length === WXW_NLO * WXW_NLA){
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
        '&forecast_hours=72&wind_speed_unit=ms&timezone=UTC')
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
    var D = dims(), w = D.w, h = D.h, b = cfg.bounds(), segs = [], i, p, s, pt, ptE, ptN, dx, dy, mm, P = pal();
    if (moving){
      // panning/zooming: keep the flow going AND reproject every frame so the dashes
      // ride with the map (no smear, no freeze). Centre px/deg is enough during a drag.
      ctx.clearRect(0, 0, w, h);
      var mcx = (b.w + b.e) / 2, mcy = (b.s + b.n) / 2, mc = cfg.project(mcx, mcy),
          meE = cfg.project(mcx + 0.1, mcy), meN = cfg.project(mcx, mcy + 0.1);
      var mppdLon = (mc && meE ? Math.abs(meE.x - mc.x) / 0.1 : 0) || 1,
          mppdLat = (mc && meN ? Math.abs(meN.y - mc.y) / 0.1 : 0) || 1;
      for (i = 0; i < parts.length; i++){ p = parts[i];
        if (p.lon < b.w || p.lon > b.e || p.lat < b.s || p.lat > b.n){ reseed(p); }
        pt = cfg.project(p.lon, p.lat);
        if (!pt || pt.x < -20 || pt.y < -20 || pt.x > w + 20 || pt.y > h + 20) continue;
        s = window.wxWindSample(p.lon, p.lat); if (!s) continue;
        mm = Math.sqrt(s.u * s.u + s.v * s.v) || 1;
        segs.push([pt.x, pt.y, pt.x + (s.u / mm) * 9, pt.y - (s.v / mm) * 9]);
        p.lon += Math.max(-0.05, Math.min(0.05, s.u * C.SPEED * sc / mppdLon));
        p.lat += Math.max(-0.05, Math.min(0.05, s.v * C.SPEED * sc / mppdLat));
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
        var ax = (ptE.x - pt.x) / 0.02, ay = (ptE.y - pt.y) / 0.02,
            bx = (ptN.x - pt.x) / 0.02, by = (ptN.y - pt.y) / 0.02, det = ax * by - bx * ay;
        if (Math.abs(det) > 1e-4){
          var vx = s.u * C.SPEED * sc, vy = -s.v * C.SPEED * sc; // desired screen velocity (y down)
          // cap the per-frame step so a near-horizon degenerate scale can't make it "fly"
          p.lon += Math.max(-0.05, Math.min(0.05, (by * vx - bx * vy) / det));
          p.lat += Math.max(-0.05, Math.min(0.05, (-ay * vx + ax * vy) / det));
        }
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
window.wxPlnKind = function(a){
  if (a.category === 'A7' || /helicopter/i.test(a.desc || '')) return 'hel';
  // twin turboprops carry wing props, not a nose one: match the common type codes
  // (ATR, Dash 8, Saab, Fokker 50, Do328, Jetstream, Brasilia, Beech 1900, Metro)
  if (/^(AT4|AT7|DH8|SF3|SB2|F50|D32|JS3|JS4|E12|B19|SW[34])/.test((a.t || '').toUpperCase()) ||
      /ATR[- ]?\d/i.test(a.desc || '')) return 'tpr';
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
  window.wxGjWin = (ST.get('gjWin', 12) === 24) ? 24 : 12; var _gjSaved = ST.get('gjDay', null); if (_gjSaved !== null){ window.wxGjDay = _gjSaved || ''; window.wxGjAuto = false; } // an explicit saved choice (incl. '' = live) turns OFF auto; null = never chosen -> auto newest day
  document.querySelectorAll('#wxwindh .wxhseg button').forEach(function(x){ x.classList.toggle('on', +x.getAttribute('data-h') === wh); });
  [['cld','wxcld','wxSetClouds'], ['rad','wxrad','wxSetRain'],
   ['snow','wxsnow','wxSetSnow'], ['gj','wxgj','wxSetGj'],
   ['airc','cbAirC','wxSetAirC'], ['airs','cbAirS','wxSetAirS'], ['notam','cbNotam','wxSetNotam'],
   ['pln','plnbtn','wxSetPlanes'], ['wind','wxwind','wxSetWind'],
   ['ogn','ognbtn','wxSetOgn']].forEach(function(s){
    if (!ST.get(s[0], false)) return;
    var fn = window[s[2]]; if (typeof fn !== 'function') return; // layer not present on this page yet
    var b = document.getElementById(s[1]); if (b) b.classList.add('on');
    try{ fn(true); }catch(e){} // one broken engine must never kill the layers after it (F5 bug, 17.09)
  });
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
// airspace < zones (< aircraft, which have no beforeId). Each layer inserts before the
// lowest layer of a higher slot that currently exists.
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
function wxGjBefore(){ return wxAirFloor() || wxZoneAnchor(); } // GPS + weather below ALL airspace
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
window.wxCloudApply = function(){ // toggle + every slider move: pick satellite (0) or model (ahead)
  if (!cldOn) return;
  if (cldMode() === 'sat'){ cldSatShow(); }
  else if (window.wxFcState && window.wxFcState.data){ cldModelShow(); }
  else { window.wxFcFetch(function(){ if (cldOn && cldMode() === 'model') cldModelShow(); }); } // grid loads once; rain/snow reuse it
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

window.wxSetClouds = function(on){ cldOn = on;
  if (on){ wxBtnBusy('wxcld', ['wxcld','wxcldfc']); window.wxCloudApply();
    cldTimer = setInterval(function(){ if (cldOn && cldMode() === 'sat') cldSatShow(); }, 600000); // refresh the satellite every 10 min while it is the one shown
  } else { clearInterval(cldTimer); wxBtnIdle('wxcld');
    if (map.getLayer(CLD)) map.removeLayer(CLD);
    if (map.getSource('wxcld')) map.removeSource('wxcld');
    if (map.getLayer(CLDFC)) map.removeLayer(CLDFC);
    if (map.getSource('wxcldfc')) map.removeSource('wxcldfc'); }
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
    map.setLayoutProperty(id, 'visibility', i === rvIdx ? 'visible' : 'none'); }); rvLabel(); }
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
  rvIdx = rvFrames.length - 1; rvShow(); }
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
function rvStop(){ rvOn = false; clearInterval(rvTick); clearInterval(rvRefresh); rvClear(); rvFrames = []; rvLabel(); }
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
      fcTimer = setInterval(function(){ if (rainOn && rainMode() === 'model') window.wxFcFetch(function(){ window.wxFcApply(); }); }, 1800000);
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
// ---- forecast SNOW (Open-Meteo model; shares the rain grid -> no extra request) ----
var SNL = 'wxsnow-layer', snowTimer = null;
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
    var go = function(){ window.wxFcFetch(function(){ window.wxSnowApply(); }); };
    go(); snowTimer = setInterval(go, 1800000); // fresh model data every 30 min
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
// while on (the collector writes a new picture every 5 min).
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
      // re-request without a day. Auto keeps tracking (no ST write, so the live
      // response then snaps to the newest ready day); an explicit gone day is
      // remembered as live.
      if (wasDay){ window.wxGjDay = ''; if (!window.wxGjAuto) ST.set('gjDay', ''); window.wxGjSyncLabel(); gjFetch(); gjResetTimer(); }
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
  ST.set('gjDay', window.wxGjDay); ST.set('gjWin', window.wxGjWin);
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
window.wxAirUrl = 'https://full-narwhal-4777.martinovem.deno.net/airspace';
var AIR_CTRL_T = [4,5,6,7,13,14,25,26,36]; // controlled types (rest = special-use)
var AIR_TL = {1:{bg:'Ограничена',en:'Restricted'},2:{bg:'Опасна',en:'Danger'},3:{bg:'Забранена',en:'Prohibited'},
  4:{bg:'CTR — контролна зона',en:'CTR'},5:{bg:'TMZ',en:'TMZ'},6:{bg:'RMZ',en:'RMZ'},7:{bg:'TMA',en:'TMA'},
  8:{bg:'Военна (TRA)',en:'Military (TRA)'},9:{bg:'Военна (TSA)',en:'Military (TSA)'},13:{bg:'ATZ',en:'ATZ'},
  14:{bg:'MATZ',en:'MATZ'},25:{bg:'MTA',en:'MTA'},26:{bg:'CTA',en:'CTA'},36:{bg:'MCTR',en:'MCTR'}};
function airEnsure(cb){
  if (map.getSource('wxair')){ cb(); return; }
  fetch(window.wxAirUrl).then(function(r){ if (!r.ok) throw 0; return r.json(); }).then(function(gj){
    if (!map.getSource('wxair')) map.addSource('wxair', {type:'geojson', data:gj, generateId:true,
      attribution:'Airspace &copy; <a href="https://www.openaip.net/" target="_blank" rel="noopener">openAIP</a> (CC BY-NC 4.0)'});
    cb();
  }).catch(function(){ wxBtnIdle('cbAirC'); wxBtnIdle('cbAirS'); // relay/source down: draw nothing rather than something stale...
    clearTimeout(window._airRt); window._airRt = setTimeout(function(){ // ...then re-attempt the FETCH (never draws stale); stops once toggled off
      if (window.wxAirCOn) window.wxSetAirC(true); if (window.wxAirSOn) window.wxSetAirS(true); }, 15000); });
}
function airDropSourceMaybe(){ if (!map.getLayer('air-ctrl') && !map.getLayer('air-spec') && map.getSource('wxair')) map.removeSource('wxair'); } // each group's labels are removed with its outline
// Each airspace group carries its OWN name labels, added/removed WITH its outline (no
// separate "labels" toggle). MapLibre's collision detection thins overlapping labels out
// by zoom on its own, so it never becomes a wall of text. Text coloured like the outline.
var AIR_LBL_LAYOUT = {'text-field':['get','n'], 'text-size':11, 'text-font':['Noto Sans Regular'], 'text-max-width':9};
var AIR_LW = ['case', ['boolean', ['feature-state', 'sel'], false], 3.8, 1.3]; // clicked airspace outline thickens ~3x (feature-state 'sel')
window.wxSetAirC = function(on){ window.wxAirCOn = on;
  if (on){ wxBtnBusy('cbAirC', 'wxair'); airEnsure(function(){ if (!window.wxAirCOn) return;
    if (!map.getLayer('air-ctrl')) map.addLayer({id:'air-ctrl', type:'line', source:'wxair',
      filter:['in',['get','t'],['literal',AIR_CTRL_T]],
      paint:{'line-color':'#2b6cb0','line-width':AIR_LW,'line-opacity':0.9}}, wxZoneAnchor()); // faint: context, not a dominant border
    if (!map.getLayer('air-ctrl-labels')) map.addLayer({id:'air-ctrl-labels', type:'symbol', source:'wxair',
      filter:['in',['get','t'],['literal',AIR_CTRL_T]], layout:AIR_LBL_LAYOUT,
      paint:{'text-color':'#2b6cb0','text-halo-color':'rgba(255,255,255,0.9)','text-halo-width':1.4}}, wxZoneAnchor()); }); }
  else { wxBtnIdle('cbAirC'); ['air-ctrl','air-ctrl-labels'].forEach(function(id){ if (map.getLayer(id)) map.removeLayer(id); }); airDropSourceMaybe();
    if (window.wxPopupPrune) window.wxPopupPrune(); } // its airspace leaves an open popup too
};
window.wxSetAirS = function(on){ window.wxAirSOn = on;
  if (on){ wxBtnBusy('cbAirS', 'wxair'); airEnsure(function(){ if (!window.wxAirSOn) return;
    if (!map.getLayer('air-spec')) map.addLayer({id:'air-spec', type:'line', source:'wxair',
      filter:['!',['in',['get','t'],['literal',AIR_CTRL_T]]],
      // red for Prohibited(3)/Restricted(1)/Danger(2); magenta for military TRA/TSA(8/9)
      paint:{'line-color':['case',['in',['get','t'],['literal',[8,9]]],'#d81fbf','#d0202a'],'line-width':AIR_LW,'line-opacity':0.9}}, wxZoneAnchor());
    if (!map.getLayer('air-spec-labels')) map.addLayer({id:'air-spec-labels', type:'symbol', source:'wxair',
      filter:['!',['in',['get','t'],['literal',AIR_CTRL_T]]], layout:AIR_LBL_LAYOUT,
      paint:{'text-color':['case',['in',['get','t'],['literal',[8,9]]],'#d81fbf','#d0202a'],'text-halo-color':'rgba(255,255,255,0.9)','text-halo-width':1.4}}, wxZoneAnchor()); }); }
  else { wxBtnIdle('cbAirS'); ['air-spec','air-spec-labels'].forEach(function(id){ if (map.getLayer(id)) map.removeLayer(id); }); airDropSourceMaybe();
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
      (p.nx ? ('<br><small>' + (L === 'en' ? 'by NOTAM' : 'по NOTAM') + '</small>') : ''); };
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
// ---- NOTAM layer (/notam relay over the FAA NMS-API): temporary drone-relevant
// restrictions drawn ABOVE the zones. A lettered pin (P/R/D/M/!) at the centre + a
// dashed, lightly-filled (20%) circle/polygon coloured by category. Click shows the
// NOTAM; a click on one of OUR zones still wins. FAA carries the international series,
// so the popup + menu say "check B-FLIP". Single menu toggle; OFF by default.
window.wxNotamUrl = 'https://full-narwhal-4777.martinovem.deno.net/notam';
// letter -> colour, aligned with B-FLIP (R red, W/warnings orange, M magenta) and
// managed so the only orange (! = warnings) is a deeper orange than the amber
// "req-authorisation" zones, which it must not be confused with.
var NT_COL = ['match', ['get','l'], 'P','#d0202a', 'R','#d0202a', 'D','#d0202a', 'M','#d81fbf', 'O','#00897b', '!','#ef6c00', '#d0202a'];
var NT_TL = {prohibited:{bg:'Забранена зона (NOTAM)',en:'Prohibited (NOTAM)'},
  danger:{bg:'Опасна зона (NOTAM)',en:'Danger (NOTAM)'},
  military:{bg:'Военна / сегрегирана (NOTAM)',en:'Military / segregated (NOTAM)'},
  restricted:{bg:'Ограничена зона (NOTAM)',en:'Restricted (NOTAM)'},
  obstacle:{bg:'Препятствие (NOTAM)',en:'Obstacle (NOTAM)'},
  warning:{bg:'Предупреждение (NOTAM)',en:'Warning (NOTAM)'}};
// Classic teardrop pin markers with the letter baked in, coloured by category and
// added once as map images. icon-anchor 'bottom' puts the tip on the NOTAM centre.
var NT_PINCOL = {P:'#d0202a', R:'#d0202a', D:'#d0202a', M:'#d81fbf', O:'#00897b', '!':'#ef6c00'};
function wxNotamPin(color, letter){
  var pr = 2, W = 26, H = 36, r = 10, cx = W/2, cy = r + 2, tip = H - 1.5;
  var cv = document.createElement('canvas'); cv.width = W*pr; cv.height = H*pr;
  var ctx = cv.getContext('2d'); ctx.scale(pr, pr);
  function path(rr, ty){ ctx.beginPath(); ctx.arc(cx, cy, rr, 0, Math.PI*2);
    ctx.moveTo(cx - rr*0.72, cy + rr*0.7); ctx.lineTo(cx, ty); ctx.lineTo(cx + rr*0.72, cy + rr*0.7); ctx.closePath(); }
  path(r + 1.3, tip + 1); ctx.fillStyle = '#fff'; ctx.fill();   // white halo / outline
  path(r, tip); ctx.fillStyle = color; ctx.fill();               // coloured pin body
  ctx.fillStyle = '#fff'; ctx.font = 'bold ' + (r+2) + 'px sans-serif';
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
    if (!map.hasImage(id)) map.addImage(id, wxNotamPin(NT_PINCOL[k], k), {pixelRatio: 2}); });
  if (!map.hasImage('nthatch')) map.addImage('nthatch', wxNotamHatch('#d0202a'), {pixelRatio: 2}); }
// ONE fetch of /notam -> normalised sources data + the picture's true age from
// the relay's X-Notam-Age-Ms header (= time since the newest successful FAA
// poll behind the picture, KV-restored or live). Shared by the first ON and the
// 10-minute auto-refresh, so the freshness stamp below never lies.
function notFetch(ok){
  fetch(window.wxNotamUrl, {cache: 'no-store'}).then(function(r){ if (!r.ok) throw 0;
    var age = parseInt(r.headers.get('X-Notam-Age-Ms') || '0', 10) || 0;
    return r.json().then(function(gj){ return {gj: gj, age: age}; });
  }).then(function(d){
    var gj = d.gj, ntNow = Date.now();
    // flag UPCOMING (not-yet-active) NOTAMs so they draw muted (fainter, same colour) - fut=1
    (gj.features||[]).forEach(function(f){ f.properties.fut = (f.properties.f && Date.parse(f.properties.f) > ntNow) ? 1 : 0; });
    // a second, point source for the centre pins (built from each feature's cx/cy)
    var pts = {type:'FeatureCollection', features:(gj.features||[]).map(function(f){
      return {type:'Feature', properties:f.properties, geometry:{type:'Point', coordinates:[f.properties.cx, f.properties.cy]}}; })};
    window._ntDataAt = Date.now() - d.age; // moment the picture was truly fresh
    ok(gj, pts);
    notFreshPaint();
  }).catch(function(){ wxBtnIdle('cbNotam'); notFreshPaint(); }); // fetch failed: whatever is drawn keeps AGEING honestly on the stamp/banner
}
function notEnsure(cb){
  if (map.getSource('wxnotam')){ cb(); return; }
  notFetch(function(gj, pts){
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
  notFetch(function(gj, pts){
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
    if (!map.getLayer('notam-pin')) map.addLayer({id:'notam-pin', type:'symbol', source:'wxnotam-pts',
      layout:{'icon-image':['match',['get','l'],'P','ntpin-P','D','ntpin-D','M','ntpin-M','R','ntpin-R','O','ntpin-O','ntpin-excl'],
        'icon-anchor':'bottom', 'icon-size':1, 'icon-allow-overlap':true, 'icon-ignore-placement':true},
      paint:{'icon-opacity':['case',['==',['get','fut'],1],0.5,1]}}); }); }
  else { wxBtnIdle('cbNotam'); ['notam-fill','notam-hatch','notam-line','notam-line-r','notam-pin'].forEach(function(id){ if (map.getLayer(id)) map.removeLayer(id); });
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
function ognLoad(){
  if (document.hidden) return;
  fetch(window.wxOgnUrl).then(function(r){ if (!r.ok) throw new Error('ogn ' + r.status); return r.text(); })
  .then(function(txt){
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
