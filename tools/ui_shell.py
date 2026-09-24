"""Shared UI shell injected into both map pages: the floating hamburger (☰)
menu, the glass side panel (drawer), the collapsible search loupe (🔍), the
top-right control cluster (2D/3D + later tools) and the ✈ aircraft button.

Layout (both maps), left column top→bottom: ☰ menu button → panel (opens
below it) → 🔍 loupe → weather chip (#wx, from weather_widget) → ✈ button.
Top-right: the 2D/3D switch (+ measure/fullscreen added later).

Only ONE of {panel, weather card} is open at a time (opening one collapses the
other); the loupe collapses on selection or an outside click. On phones the
panel is a near-full-width overlay and the other left controls hide while it
is open. Mobile browser-chrome overlap at the bottom is handled with
`visualViewport` (the --vp-bottom CSS variable).

Colors go through CSS custom properties (tokens) defined on :root here, so the
dark theme (a later step) only needs to override the tokens — no per-rule
edits. Current values reproduce today's light look.

make_3d.py inserts SHELL_CSS at the style marker and SHELL_JS at
the script marker, and build the panel/right-cluster HTML from the helpers.
"""

SHELL_CSS = r"""
:root{
 --glass-bg:rgba(255,255,255,.92); --glass-strong:rgba(255,255,255,.97); --glass-weak:rgba(255,255,255,.6);
 --fg:#1c1c1e; --muted:#777; --border:rgba(0,0,0,.12);
 --accent:#2b6cb0; --accent-fg:#fff; --shadow:0 2px 12px rgba(0,0,0,.18);
 --hover:#f2f2f2; --sug-hover:#eef3f9;
}
/* floating left column: menu button, panel, loupe, weather chip, planes */
#leftui{position:absolute;top:10px;left:10px;z-index:1100;display:flex;flex-direction:column;
 align-items:flex-start;gap:8px;max-height:calc(100vh - 20px);
 font:14px/1.2 system-ui,'Segoe UI',Roboto,sans-serif;color:var(--fg)}
#rightui{position:absolute;top:10px;right:10px;z-index:1100;display:flex;flex-direction:column;
 align-items:flex-end;gap:8px;font:14px/1.2 system-ui,'Segoe UI',Roboto,sans-serif;color:var(--fg)}
/* both columns are invisible boxes as wide as their widest control (the weather chip /
   the 2D-3D switch): their EMPTY area lets taps through to the map (zones, aircraft,
   panning) - only the controls themselves take a tap */
#leftui,#rightui{pointer-events:none}
#leftui>*,#rightui>*{pointer-events:auto}
.pill{display:inline-flex;align-items:center;gap:8px;background:var(--glass-bg);
 -webkit-backdrop-filter:blur(8px);backdrop-filter:blur(8px);border:1px solid var(--border);
 border-radius:999px;box-shadow:var(--shadow);padding:0 12px;height:38px;box-sizing:border-box;
 font:inherit;color:inherit;cursor:pointer;white-space:nowrap}
.pill:hover{background:var(--glass-strong)}
.pill.icon{padding:0;width:38px;justify-content:center;font-size:17px}
.pill.on{background:var(--accent);color:var(--accent-fg);border-color:var(--accent)}
/* "working…" cue: a data layer's button pulses while its first fetch is in flight
   (visible without opening anything, unlike the calendar's inline text) */
@keyframes wxpulse{0%,100%{opacity:1}50%{opacity:.4}}
.loading{animation:wxpulse 1s ease-in-out infinite}
@media (prefers-reduced-motion:reduce){.loading{animation:none;opacity:.6}}
#fsbtn svg[hidden]{display:none}
#menubtn .brandico{display:block}
#menubtn .mlbl{font-weight:700}
/* the glass drawer */
#panel{width:min(300px,calc(100vw - 20px));background:var(--glass-strong);
 -webkit-backdrop-filter:blur(10px);backdrop-filter:blur(10px);border:1px solid var(--border);
 border-radius:14px;box-shadow:0 4px 18px rgba(0,0,0,.25);padding:10px 12px;
 max-height:calc(100vh - 70px);overflow:auto}
#panel[hidden]{display:none}
.phead{display:flex;justify-content:flex-end;margin:-2px -4px 0 0}
.pclose{border:0;background:transparent;font-size:17px;line-height:1;color:var(--muted);cursor:pointer;padding:2px 6px}
.psec{padding:6px 0}
.psec:first-of-type{padding-top:0}
.psec+.psec{border-top:1px solid var(--border)}
.pfoot{border-top:1px solid var(--border);padding-top:8px;margin-top:6px}
.pfoot a{color:var(--accent);text-decoration:none;font-size:12px}
.pfoot a:hover{text-decoration:underline}
.psh{font-size:11px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;color:var(--fg);margin:0 0 6px}
.prow{display:flex;flex-wrap:wrap;gap:6px}
/* dual-range height (FL) slider: two range inputs overlaid on one track */
.flrow{padding:2px 2px 0}
.fltrack{position:relative;height:22px}
.fltrack::before{content:'';position:absolute;left:0;right:0;top:9px;height:4px;border-radius:2px;background:var(--border)}
.flfill{position:absolute;top:9px;height:4px;border-radius:2px;background:var(--accent)}
.fltrack input[type=range]{position:absolute;top:0;left:0;width:100%;height:22px;margin:0;background:transparent;-webkit-appearance:none;appearance:none;pointer-events:none}
.fltrack input[type=range]:focus{outline:none}
.fltrack input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;appearance:none;pointer-events:auto;width:15px;height:15px;border-radius:50%;background:var(--accent);border:2px solid #fff;box-shadow:0 1px 3px rgba(0,0,0,.35);cursor:pointer;margin-top:-5px}
.fltrack input[type=range]::-moz-range-thumb{pointer-events:auto;width:15px;height:15px;border-radius:50%;background:var(--accent);border:2px solid #fff;box-shadow:0 1px 3px rgba(0,0,0,.35);cursor:pointer}
.fltrack input[type=range]::-webkit-slider-runnable-track{height:4px;background:transparent}
.fltrack input[type=range]::-moz-range-track{height:4px;background:transparent}
.fllbl{display:flex;justify-content:space-between;font-size:11px;color:var(--muted);margin-top:1px;font-variant-numeric:tabular-nums}
.flnote{font-size:10px;color:var(--muted);margin-top:3px;font-style:italic}
/* disabled state (✈ off): grey out the slider + labels, block dragging; the note stays readable */
#flsec.fldis .fltrack,#flsec.fldis .fllbl{opacity:.4}
#flsec.fldis .fltrack{pointer-events:none}
#flsec.fldis .psh{opacity:.55}
/* chips reused inside the panel (zone filters, buildings, layers) */
.chip{display:inline-flex;align-items:center;gap:6px;cursor:pointer;user-select:none;
 border:1px solid var(--border);border-radius:999px;padding:5px 10px;background:var(--glass-bg);
 font-size:13px;color:var(--fg);transition:opacity .15s}
.chip .dot{width:11px;height:11px;border-radius:50%}
.chip .cnt{color:var(--muted);font-variant-numeric:tabular-nums}
.chip.off{opacity:.4}
/* layer toggles (zone filters, buildings, airspace): highlighted (accent) when ON,
   plain when OFF - a faded chip reads as "not available", which a toggled-off layer isn't */
.chip.on{background:var(--sug-hover);border-color:var(--accent);font-weight:600}
.airnote{font-size:11px;color:var(--muted);margin-top:6px;display:flex;align-items:center;gap:4px;flex-wrap:wrap}
.airsw{width:11px;height:11px;border-radius:3px;display:inline-block;border:1px solid rgba(0,0,0,.15);flex:none}
/* NOTAM letter badges in the menu key: small coloured square with a white letter */
.ntk{display:inline-flex;align-items:center;justify-content:center;width:15px;height:15px;border-radius:4px;color:#fff;font-size:10px;font-weight:700;line-height:1;flex:none}
.pbtn{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--border);border-radius:999px;
 padding:6px 11px;background:var(--glass-bg);color:var(--fg);text-decoration:none;font-size:13px;
 cursor:pointer;font-family:inherit}
.pbtn:hover{background:var(--hover)}
.lang{display:inline-flex;border:1px solid var(--border);border-radius:999px;overflow:hidden;
 background:var(--glass-bg);-webkit-backdrop-filter:blur(8px);backdrop-filter:blur(8px);box-shadow:var(--shadow)}
.lang button{display:inline-flex;align-items:center;gap:5px;border:0;background:transparent;cursor:pointer;
 padding:9px 11px;font-size:13px;color:var(--fg);font-family:inherit}
.lang button.on{background:var(--accent);color:var(--accent-fg)}
.lang svg{display:block;border-radius:2px;box-shadow:0 0 0 1px rgba(0,0,0,.15)}
#langbtn .l-en,#langbtn .l-bg{display:inline-flex;align-items:center;gap:5px}
#langbtn .l-en[hidden],#langbtn .l-bg[hidden]{display:none}
#langbtn svg{display:block;border-radius:2px;box-shadow:0 0 0 1px rgba(0,0,0,.15)}
/* 2D/3D segmented switch (top-right) */
.seg{display:inline-flex;align-items:stretch;height:38px;box-sizing:border-box;border:1px solid var(--border);border-radius:999px;overflow:hidden;
 background:var(--glass-bg);-webkit-backdrop-filter:blur(8px);backdrop-filter:blur(8px);box-shadow:var(--shadow)}
.seg a{display:inline-flex;align-items:center;padding:0 14px;text-decoration:none;color:var(--fg);font-weight:600;font-size:13px;cursor:pointer}
.seg a.on{background:var(--accent);color:var(--accent-fg)}
/* base-map (⧉) popover — flies out to the LEFT of the button in the top-right cluster,
   so it never covers the other cluster buttons */
#bmwrap{position:relative;display:flex}
#bmpanel{position:absolute;top:0;right:46px;z-index:20;min-width:152px;background:var(--glass-strong);
 -webkit-backdrop-filter:blur(10px);backdrop-filter:blur(10px);border:1px solid var(--border);
 border-radius:12px;box-shadow:0 4px 18px rgba(0,0,0,.25);padding:6px;max-height:calc(100vh - 20px);overflow:auto}
#bmpanel[hidden]{display:none}
.bmph{font-size:11px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;color:var(--fg);margin:2px 6px 6px}
.bmopt{display:flex;align-items:center;gap:8px;width:100%;box-sizing:border-box;border:0;background:transparent;
 cursor:pointer;font:inherit;font-size:13px;color:var(--fg);text-align:left;padding:7px 9px;border-radius:8px;white-space:nowrap}
.bmopt:hover{background:var(--sug-hover)}
.bmopt .bmdot{width:9px;height:9px;border-radius:50%;border:2px solid var(--muted);flex:none;box-sizing:border-box}
.bmopt.on{background:var(--sug-hover);font-weight:600}
.bmopt.on .bmdot{border-color:var(--accent);background:var(--accent)}
/* the search loupe: a 🔍 pill that expands to the search box */
#loupe .sbox{display:none;align-items:center;gap:7px;background:var(--glass-strong);
 -webkit-backdrop-filter:blur(8px);backdrop-filter:blur(8px);border:1px solid var(--border);
 border-radius:999px;box-shadow:var(--shadow);padding:0 11px;height:38px;box-sizing:border-box;
 width:min(300px,calc(100vw - 20px))}
#loupe.open .sbox{display:flex}
#loupe.open #loupebtn{display:none}
#loupe .sbox input{flex:1;border:0;outline:0;background:transparent;font:inherit;font-size:16px;
 line-height:1.1;padding:0;color:var(--fg);min-width:0}
.locbtn{border:0;background:transparent;cursor:pointer;padding:0;display:flex;color:var(--accent)}
#sug{list-style:none;margin:6px 0 0;padding:4px;background:var(--glass-strong);border-radius:10px;
 box-shadow:0 2px 12px rgba(0,0,0,.2);max-height:50vh;overflow:auto;width:min(300px,calc(100vw - 20px))}
#sug li{padding:7px 9px;border-radius:7px;cursor:pointer}
#sug li:hover,#sug li.active{background:var(--sug-hover)}
#sug .nm{font-weight:600}
#sug .ctx{color:var(--muted);font-size:12px}
#sug[hidden]{display:none}
.pln-hint{font-size:11px;color:var(--muted)}
/* GPS-interference legend: a compact box centred at the BOTTOM, shown only while the
   layer is on; same swatches + font size as the rain legend. On phones an opened
   disclaimer / attribution may lie over it (accepted by design); desktop has room. */
#wxgjlegend{position:absolute;left:50%;bottom:12px;transform:translateX(-50%);z-index:5;
 background:rgba(255,255,255,.92);border-radius:10px;box-shadow:0 1px 6px rgba(0,0,0,.18);
 padding:5px 10px;font-size:11px;color:#333;text-align:center;pointer-events:none;max-width:calc(100vw - 20px)}
#wxgjlegend[hidden]{display:none}
#wxgjlegend .wxgjrow{display:flex;gap:10px;flex-wrap:wrap;justify-content:center}
#wxgjlegend .gjnote{display:block;margin-top:2px;font-size:10px;color:#888}
/* calendar: a clickable date label in the legend + a popup that opens UPWARD.
   The legend itself is pointer-events:none; the label + popup re-enable it. */
#wxgjday{pointer-events:auto;cursor:pointer;display:inline-flex;align-items:center;gap:3px;border:0;background:transparent;font:inherit;font-weight:600;color:inherit;padding:1px 5px 3px;border-radius:6px}
#wxgjday:hover{background:rgba(0,0,0,.06)}
#wxgjday .car{opacity:.55;font-size:9px}
#wxgjcal{position:absolute;bottom:100%;left:50%;transform:translateX(-50%);margin-bottom:6px;pointer-events:auto;text-align:left;background:rgba(255,255,255,.98);border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,.28);padding:8px;width:min(220px,86vw);color:#333}
#wxgjcal[hidden]{display:none}
#wxgjwin{display:flex;border:1px solid #c7c7c7;border-radius:7px;overflow:hidden;margin-bottom:6px}
#wxgjwin button{flex:1;border:0;background:transparent;padding:4px 0;font:inherit;font-size:11px;cursor:pointer;color:inherit}
#wxgjwin button.on{background:#2b6cb0;color:#fff}
#wxgjlive{display:block;width:100%;border:1px solid #c7c7c7;border-radius:7px;background:transparent;padding:4px 0;font:inherit;font-size:11px;cursor:pointer;margin-bottom:6px;color:inherit}
#wxgjlive.on{background:#2b6cb0;color:#fff;border-color:#2b6cb0}
#wxgjcalhd{display:flex;align-items:center;justify-content:space-between;margin-bottom:4px;font-size:11px;font-weight:600}
#wxgjcalhd button{border:0;background:transparent;cursor:pointer;font:inherit;font-size:14px;line-height:1;padding:0 6px;color:inherit}
#wxgjcalhd button:disabled{opacity:.3;cursor:default}
#wxgjgrid table{border-collapse:collapse;width:100%}
#wxgjgrid th{font-size:9px;font-weight:500;color:#999;padding:2px 0}
#wxgjgrid td{text-align:center;padding:0}
#wxgjgrid button{width:24px;height:22px;border:0;background:transparent;font:inherit;font-size:11px;border-radius:5px;color:inherit;opacity:.35;cursor:default}
#wxgjgrid button.av{color:#2b6cb0;opacity:1;font-weight:600;cursor:pointer}
#wxgjgrid button.av:hover{background:rgba(43,108,176,.12)}
#wxgjgrid button.sel{background:#2b6cb0;color:#fff;opacity:1}
#wxgjgrid .gjstat{text-align:center;font-size:10px;color:#888;padding:4px 0 1px}
/* phones only (narrow OR short, so LANDSCAPE phones count too): shrink the GPS
   legend (smaller text + colour squares; rain/snow legends untouched), shrink the
   zoom/compass control, and move the scale bar to the bottom-LEFT so it stops
   overlapping the zoom control in the tight bottom-right corner. */
@media (max-width:640px), (max-height:500px){
 #wxgjlegend{font-size:9px;padding:4px 8px;bottom:10px}
 #wxgjlegend .wxgjrow{gap:7px}
 #wxgjlegend .wxlg i{width:8px;height:8px;border-radius:2px}
 #wxgjlegend .gjnote{font-size:8px}
 #wxgjday{font-size:10px}
 #wxgjcal{width:min(210px,90vw);padding:6px}
 #wxgjgrid button{width:22px;height:20px;font-size:10px}
 .maplibregl-ctrl-bottom-right .maplibregl-ctrl-group{transform:scale(.82);transform-origin:bottom right}
}
/* while the panel is open on phones, hide the rest of the left column */
@media (max-width:640px){
 /* while the panel is open on a phone it fills the screen — hide every other
    floating control (left icons AND the top-right 2D/3D + language) so nothing
    overlaps or dangles; closing the panel brings them all back */
 #leftui.panelopen>#loupe,#leftui.panelopen>#wx,#leftui.panelopen>#wxgj,#leftui.panelopen>#plnbtn,#leftui.panelopen>#ognbtn{display:none}
 #leftui.panelopen ~ #rightui{display:none}
 #panel{width:min(320px,calc(100vw - 20px))}
 .pill{height:34px}
 #loupe .sbox{height:34px}
 .seg{height:34px}
 .seg a{padding:0 12px;font-size:12px}
}
/* --- collapsible disclaimer (#info) ------------------------------------
   Desktop: unchanged — the toggle is hidden and the full warning stays open.
   Phone: the text collapses behind a round red "!" that toggles it open/shut,
   the same idea as the 3D map's ⓘ attribution. The warning is never removed,
   only one tap away — the safety disclaimer must always stay reachable. */
#infotoggle{display:none;flex:none;width:24px;height:24px;border-radius:50%;
 border:1px solid var(--border);background:var(--glass-bg);color:#d03030;
 font-weight:800;font-size:15px;line-height:1;cursor:pointer;padding:0;
 align-self:flex-start;align-items:center;justify-content:center}
/* collapse the disclaimer on small screens — a phone in EITHER orientation:
   portrait (narrow width) OR landscape (short height), so rotating the phone to
   landscape (where width > 640px) doesn't make it reopen itself */
@media (max-width:640px), (max-height:500px){
 /* expanded on a phone: a solid (opaque) box for easy reading over the map —
    desktop keeps the semi-transparent look (owner's choice) */
 #info{display:flex;gap:7px;align-items:flex-start;background:var(--glass-strong)}
 #infotoggle{display:inline-flex}
 /* collapsed = just the "!" toggle: no padding, so it sits at the same 10px inset
    from the edge and the same bottom level as the attribution "i" (which MapLibre
    places 10px from the bottom-right corner) — the two corner buttons stay symmetric */
 #info.collapsed{padding:0;background:transparent;box-shadow:none;max-width:none;overflow:visible}
 #info.collapsed .infobody{display:none}
}
/* --- center crosshair (+) -----------------------------------------------
   Marks the map centre — the exact point the weather chip names / geocodes.
   A thin light "+" glyph (like the owner's HRMG map). Each page sets colour +
   text-shadow (dark on the light 2D map, white on the 3D satellite) and the
   z-index (Leaflet/MapLibre stack differently). pointer-events:none so it never
   blocks a map click. */
#ctrhair{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);
 font:300 32px/1 system-ui,'Segoe UI',Roboto,sans-serif;pointer-events:none}
@media (max-width:640px){#ctrhair{font-size:26px}}
/* --- theme switch (3-way segmented, in the menu drawer) --- */
.thmseg{display:inline-flex;border:1px solid var(--border);border-radius:999px;overflow:hidden;background:var(--glass-bg)}
.thmseg button{border:0;background:transparent;cursor:pointer;font:inherit;font-size:13px;padding:5px 12px;color:var(--fg);display:inline-flex;align-items:center;gap:5px}
.thmseg button.on{background:var(--accent);color:var(--accent-fg)}
.thmseg button+button{border-left:1px solid var(--border)}
/* ===== DARK THEME — UI ONLY (the map basemap is never changed by the theme) =====
   The dark map is a SEPARATE choice that will live in the basemap selector.
   Tokens flip here; the few UI bits that hard-code light colours are overridden
   below. Crosshair + scale bar follow the BASEMAP (.wx2d), not the theme. */
:root[data-theme="dark"]{
 --glass-bg:rgba(32,36,42,.92); --glass-strong:rgba(32,36,42,.97); --glass-weak:rgba(32,36,42,.72);
 --fg:#e8e8ea; --muted:#9aa1ab; --border:rgba(255,255,255,.15);
 --accent:#4a90d9; --accent-fg:#fff; --shadow:0 2px 14px rgba(0,0,0,.55);
 --hover:rgba(255,255,255,.08); --sug-hover:rgba(74,144,217,.22);
}
:root[data-theme="dark"] #wxframe,
:root[data-theme="dark"] #wxlegend,
:root[data-theme="dark"] #wxgjlegend,
:root[data-theme="dark"] #wxgjcal,
:root[data-theme="dark"] #wxfcbar,
:root[data-theme="dark"] #wxpanel{background:var(--glass-strong);color:var(--fg)}
:root[data-theme="dark"] .wxtab th{background:var(--glass-strong);color:var(--muted)}
:root[data-theme="dark"] .wxlbtn:not(.on),
:root[data-theme="dark"] .wxhseg button:not(.on),
:root[data-theme="dark"] .wxday:not(.on),
:root[data-theme="dark"] .wxnavbtn{background:rgba(255,255,255,.06);color:var(--fg);border-color:var(--border)}
:root[data-theme="dark"] .wxnavbtn:hover{background:rgba(255,255,255,.14)}
:root[data-theme="dark"] .wxhseg,
:root[data-theme="dark"] .wxlg i{border-color:var(--border)}
:root[data-theme="dark"] .wxtab tr.wxhr td,
:root[data-theme="dark"] #wxwindh{color:var(--fg)}
:root[data-theme="dark"] .wxhlbl,
:root[data-theme="dark"] .wxclose,
:root[data-theme="dark"] .wxnow .wxsub,
:root[data-theme="dark"] .wxsun,
:root[data-theme="dark"] .wxarr,
:root[data-theme="dark"] #wxfcnote,
:root[data-theme="dark"] #wxrvnote,
:root[data-theme="dark"] .wxfoot,
:root[data-theme="dark"] .wxmsg{color:var(--muted)}
/* popups (MapLibre + Leaflet) default to white -> dark surface + light text */
:root[data-theme="dark"] .maplibregl-popup-content,
:root[data-theme="dark"] .leaflet-popup-content-wrapper,
:root[data-theme="dark"] .leaflet-popup-tip{background:#20242a;color:var(--fg)}
:root[data-theme="dark"] .maplibregl-popup-close-button{color:var(--muted)}
:root[data-theme="dark"] .maplibregl-popup-anchor-top .maplibregl-popup-tip,
:root[data-theme="dark"] .maplibregl-popup-anchor-top-left .maplibregl-popup-tip,
:root[data-theme="dark"] .maplibregl-popup-anchor-top-right .maplibregl-popup-tip{border-bottom-color:#20242a}
:root[data-theme="dark"] .maplibregl-popup-anchor-bottom .maplibregl-popup-tip,
:root[data-theme="dark"] .maplibregl-popup-anchor-bottom-left .maplibregl-popup-tip,
:root[data-theme="dark"] .maplibregl-popup-anchor-bottom-right .maplibregl-popup-tip{border-top-color:#20242a}
:root[data-theme="dark"] .maplibregl-popup-anchor-left .maplibregl-popup-tip{border-right-color:#20242a}
:root[data-theme="dark"] .maplibregl-popup-anchor-right .maplibregl-popup-tip{border-left-color:#20242a}
/* a thin frame + a clearer shadow on every info popup, so two popups that overlap (an
   aircraft over a NOTAM or a zone) keep visible edges: grey line in light theme, a light
   one in dark theme. Always on - aircraft popups move, so an overlap-only frame would flicker. */
.maplibregl-popup-content{border:1px solid rgba(0,0,0,.22);box-shadow:0 2px 10px rgba(0,0,0,.3)}
:root[data-theme="dark"] .maplibregl-popup-content{border-color:rgba(255,255,255,.35);box-shadow:0 2px 14px rgba(0,0,0,.65)}
/* attribution control (bottom-right): default is a light box with black text,
   which is unreadable in dark theme -> dark box, light text, light ⓘ icon */
:root[data-theme="dark"] .maplibregl-ctrl-attrib,
:root[data-theme="dark"] .maplibregl-ctrl-attrib.maplibregl-compact{background-color:rgba(32,36,42,.9);color:var(--fg)}
:root[data-theme="dark"] .maplibregl-ctrl-attrib a{color:#cbd3dd}
:root[data-theme="dark"] .maplibregl-ctrl-attrib-button{filter:invert(.9)}
:root[data-theme="dark"] .leaflet-control-attribution{background:rgba(32,36,42,.9)!important;color:var(--fg)}
:root[data-theme="dark"] .leaflet-control-attribution a{color:#cbd3dd}
/* forecast table wind/gust warning cells: the light-theme shading is a faint
   translucent orange/red, which turns MUDDY BROWN over a dark background. Use a
   more opaque, clearly orange/red fill (with matching text) in dark theme. */
:root[data-theme="dark"] .wxtab td.wxw{background:rgba(255,150,50,.82);color:#1c1c1e}
:root[data-theme="dark"] .wxtab td.wxd{background:rgba(224,64,64,.85);color:#fff}
"""

# --- HTML builders ---------------------------------------------------------
# The loupe (search) markup, identical on both pages.
LOUPE_HTML = r"""<div id="loupe">
  <button id="loupebtn" class="pill icon" aria-label="search"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg></button>
  <div class="sbox"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#888" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg><input id="q" type="text" autocomplete="off" spellcheck="false"><button id="loc" class="locbtn" aria-label="locate"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="7"/><line x1="12" y1="1" x2="12" y2="4"/><line x1="12" y1="20" x2="12" y2="23"/><line x1="1" y1="12" x2="4" y2="12"/><line x1="20" y1="12" x2="23" y2="12"/><circle cx="12" cy="12" r="2.5" fill="currentColor" stroke="none"/></svg></button></div>
  <ul id="sug" hidden></ul>
</div>"""

# Center crosshair (+) marking the map centre, injected into both pages.
CTRHAIR_HTML = '<div id="ctrhair" aria-hidden="true">+</div>'

# The drone brand icon reused in the menu button.
BRAND_SVG = ('<svg class="brandico" width="20" height="20" viewBox="0 0 48 48" fill="none" aria-hidden="true">'
 '<g stroke="var(--accent)" stroke-width="3" stroke-linecap="round"><line x1="14" y1="14" x2="34" y2="34"/><line x1="34" y1="14" x2="14" y2="34"/></g>'
 '<g fill="none" stroke="var(--accent)" stroke-width="2.5"><circle cx="12" cy="12" r="7.5"/><circle cx="36" cy="12" r="7.5"/><circle cx="12" cy="36" r="7.5"/><circle cx="36" cy="36" r="7.5"/></g>'
 '<rect x="18" y="18" width="12" height="12" rx="3" fill="var(--accent)"/></svg>')

MENUBTN_HTML = ('<button id="menubtn" class="pill icon" aria-label="menu">'
 '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">'
 '<line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg></button>')

# ✈ aircraft floating button (below the weather chip).
PLNBTN_HTML = '<button id="plnbtn" class="pill icon" aria-label="live aircraft" title="">✈</button>'

# Low-level traffic (OGN/FLARM) floating button, below the ✈ aircraft button.
# Its icon is a GLIDER (sailplane) — FLARM/OGN's emblematic aircraft; currentColor
# so it inherits the pill colour (dark normally, white when the button is on/blue).
# Low-level traffic (OGN/FLARM) floating button, below the ✈ aircraft button.
# Icon: a hang-glider silhouette — an OWN embedded SVG (not a system emoji), so it
# looks identical on every device (Windows/Mac/iPhone/Android). currentColor ->
# dark normally, white when the button is on/blue.
# Credit: "Hang glider" icon by Delapouite, game-icons.net, CC BY 3.0 (see README).
OGNBTN_HTML = ('<button id="ognbtn" class="pill icon" aria-label="low-level traffic" title="">'
 '<svg width="25" height="25" viewBox="0 0 512 512" fill="currentColor" aria-hidden="true">'
 '<path d="M309.502 104.55c-109.47-.142-219.337 2.602-297.22 12.323 5.24 1.868 10.542 3.734 15.54 5.607 7.285 2.73 14.018 5.47 19.633 8.549 5.615 3.08 10.706 6.093 13.184 12.6 1.34 3.519 2.197 8.42 1.24 14.834 21.817-10.755 48.718-17.695 78.264-22.641 42.214-7.067 89.968-9.817 136.015-11.832l.7 15.984c-45.89 2.008-93.138 4.776-134.075 11.63-36.907 6.178-68.554 15.89-89.26 30.278 6.164 1.115 12.602 2.704 18.649 4.987 7.156 2.702 13.914 6.28 18.703 12.275.7.877 1.325 1.826 1.887 2.822 35.472-20.786 73.93-38.089 104.636-39.255a85.642 85.642 0 0 1 3.456-.063c1.14.003 2.268.029 3.384.08l-.732 15.983c-22.005-1.008-57.709 12.635-91.908 31.14 6.384.898 11.594 2.975 15.765 5.828 6.665 4.56 10.287 9.381 13.123 12.926 111.416-48.998 242.264-86.962 359.233-121.433-52.784-1.146-108.633-2.277-168.338-2.555-7.285-.034-14.581-.057-21.879-.067zm37.168 65.541a3579.804 3579.804 0 0 0-15.443 4.938c1.405 2.49 3.068 6.648 4.636 11.861 3.151 10.472 6.074 25.21 8.756 41.407 3.752 22.655 7.068 48.08 10.51 70.056l15.543-4.281c-3.275-21.198-6.56-45.998-10.268-68.389-2.73-16.485-5.673-31.617-9.218-43.402-1.375-4.567-2.82-8.622-4.516-12.19zm-88.678 29.602a2118.277 2118.277 0 0 0-16.207 5.8c-.284 8.254-.597 17.608-.916 27.577-.612 19.148-.838 35.63-1.01 41.307l15.73-3.59c1.77 16.026 9.72 34.995 19.776 48.37l13.43-3.921c7.915 9.17 15.773 20.882 30.004 26.443 24.52-1.285 44.975-11.4 66.838-18l-8.975-14.853c-18.92 5.373-33.43 10.087-55.03 10.103-5.979-12.37-12.47-26.794-20.534-38.285a26.66 34.884 38.724 0 0 23.746-14.787 26.66 34.884 38.724 0 0 1.023-43.894 26.66 34.884 38.724 0 0-42.62 10.539 26.66 34.884 38.724 0 0-8.442 32.035l-19.1 6.207c.204-6.703.56-18.514 1.156-37.164.373-11.672.758-23.388 1.07-32.26.024-.668.039-.992.061-1.627zm-18.129 74.703c-.01.327-16.247 6.008-31.246 11.194 9.075 3.258 15.571 9.066 19.508 15.869 5.771 9.973 7.394 20.985 9.148 28.824l21.834-6.377c-10.26-15.359-18.074-40.863-19.244-49.51zm-47.236 24.28c-1.89.027-3.955.15-6.217.376-51.093 5.117-83.628 32.6-111.281 68.819-5.717 7.488-10.686 19.262-11.815 27.984-.564 4.361-.08 7.833.606 9.356.685 1.522.531 1.607 2.719 1.851l.888.1.844.293c-.971-.337 5.64-.052 13.66-2.526 8.02-2.473 18.276-6.683 29.168-12.166 21.785-10.965 46.228-27.147 62.248-44.277l1.832-1.957 2.64-.461c14.456-2.515 23.545-4.16 30.169-6.281 5.056-1.62 9.005-3.815 13.4-6.86-2.085-8.623-3.7-17.39-7.21-23.455-3.758-6.492-8.42-10.988-21.651-10.797z"/>'
 '</svg></button>')


# GPS-interference (🛰) floating button — sits ABOVE the ✈ aircraft button. GPS
# jamming is aircraft-derived airspace info, NOT weather, so it lives with the
# traffic buttons, not in the weather card. Its small colour legend (green/yellow/
# red + the "aircraft altitude" caveat + the data date) appears under it while on.
GJBTN_HTML = '<button id="wxgj" class="pill icon" aria-label="gps interference" title="">\U0001F6F0</button>'


# Fullscreen toggle button (top-right cluster, under the 2D/3D switch). Two icons
# swapped on fullscreenchange (enter/exit). Hidden by JS where the Fullscreen API
# is unsupported (e.g. iOS Safari).
FSBTN_HTML = ('<button id="fsbtn" class="pill icon" aria-label="fullscreen">'
 '<svg class="fs-in" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="15 3 21 3 21 9"/><polyline points="9 21 3 21 3 15"/><line x1="21" y1="3" x2="14" y2="10"/><line x1="3" y1="21" x2="10" y2="14"/></svg>'
 '<svg class="fs-out" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" hidden><polyline points="4 14 10 14 10 20"/><polyline points="20 10 14 10 14 4"/><line x1="14" y1="10" x2="21" y2="3"/><line x1="3" y1="21" x2="10" y2="14"/></svg>'
 '</button>')


def panel_html(zone_chips, extra_secs, buildings_chip="", foot=""):
    """Assemble the drawer. zone_chips/extra_secs/buildings_chip/foot are HTML
    strings; buildings_chip is put in the ZONES section (3D only); foot is a
    trailing note (e.g. the 3D rotate/tilt hint)."""
    return (
      '<div id="panel" hidden>'
      '<div class="phead"><button class="pclose" id="panelclose" aria-label="close">✕</button></div>'
      '<div class="psec"><div class="psh" data-i18n="secZones">Зони</div><div class="prow">'
      + zone_chips + buildings_chip + '</div></div>'
      + extra_secs +
      # dual-range height (Flight Level) filter — always visible, but greyed/disabled
      # (class "fldis") until the ✈ layer is on, with an italic note explaining it
      '<div class="psec fldis" id="flsec"><div class="psh" data-i18n="secFL">Височина на самолетите</div>'
      '<div class="flrow"><div class="fltrack"><div class="flfill" id="flfill"></div>'
      '<input type="range" id="flmin" min="0" max="660" step="10" value="0" aria-label="FL min">'
      '<input type="range" id="flmax" min="0" max="660" step="10" value="660" aria-label="FL max"></div>'
      '<div class="fllbl"><span id="fllblmin">FL0</span><span id="fllblmax">FL660</span></div>'
      '<div class="flnote" data-i18n="flnote">активно само при включени ✈ самолети</div>'
      '</div></div>'
      '<div class="psec"><div class="psh" data-i18n="secTheme">Тема</div>'
      '<div class="thmseg" id="thmseg">'
      '<button data-thm="light" aria-label="light">☀</button>'
      '<button data-thm="dark" aria-label="dark">\U0001F319</button>'
      '<button data-thm="system" aria-label="system"><span data-i18n="thmAuto">Авто</span></button>'
      '</div></div>'
      '<div class="psec"><div class="psh" data-i18n="secTools">Инструменти</div><div class="prow">'
      '<a class="pbtn" href="bgr_drone_zones.kml" download>⬇ <span data-i18n="kml">KML за Google Earth</span></a>'
      '<button class="pbtn" id="rst" title="">⟳ <span data-i18n="reset">Нулиране</span></button>'
      '</div></div>'
      + foot +
      '<div class="pfoot"><a href="https://github.com/MartinovEm/drone-zones-bg" target="_blank" rel="noopener" data-i18n="moreinfo">Повече информация и източници</a></div>'
      '</div>')


# Language switch — a single pill in the top-right cluster showing the TARGET language
# (flag + code): on BG it shows EN, on EN it shows БГ. applyLang() flips which span is shown.
LANG_HTML = ('<button id="langbtn" class="pill" aria-label="language">'
 '<span class="l-en"><svg width="20" height="13" viewBox="0 0 60 30" aria-hidden="true"><clipPath id="ukc"><rect width="60" height="30"/></clipPath><g clip-path="url(#ukc)"><rect width="60" height="30" fill="#012169"/><path d="M0,0 L60,30 M60,0 L0,30" stroke="#fff" stroke-width="6"/><path d="M0,0 L60,30 M60,0 L0,30" stroke="#c8102e" stroke-width="3"/><path d="M30,0 V30 M0,15 H60" stroke="#fff" stroke-width="10"/><path d="M30,0 V30 M0,15 H60" stroke="#c8102e" stroke-width="6"/></g></svg><span>EN</span></span>'
 '<span class="l-bg" hidden><svg width="20" height="13" viewBox="0 0 60 39" aria-hidden="true"><rect width="60" height="13" fill="#fff"/><rect y="13" width="60" height="13" fill="#00966e"/><rect y="26" width="60" height="13" fill="#d62612"/></svg><span>БГ</span></span>'
 '</button>')


ZONE_CHIPS = (
 '<span class="chip on" id="cbP"><span class="dot" style="background:#ff2020"></span><span data-i18n="fP">Забранени</span> <span class="cnt" id="nP"></span></span>'
 '<span class="chip on" id="cbA"><span class="dot" style="background:#ff8000"></span><span data-i18n="fA">С разрешение</span> <span class="cnt" id="nA"></span></span>'
 '<span class="chip on" id="cbC"><span class="dot" style="background:#ffcc00"></span><span data-i18n="fC">Условни</span> <span class="cnt" id="nC"></span></span>')

BUILDINGS_CHIP = '<span class="chip on" id="cbB"><span class="dot" style="background:#b7ad9c"></span><span data-i18n="bld">Сгради</span></span>'

# Airspace section for the drawer (goes right under "Zones"): two independent toggles —
# controlled (blue) + special-use (red/pink) — from OpenAIP, with a small colour note
# and the FL180 cap note. Off by default; the layers are added on the map on demand.
AIRSPACE_SECTION = (
  '<div class="psec"><div class="psh" data-i18n="secAir">Въздушно пространство</div>'
  '<div class="prow">'
  '<span class="chip" id="cbAirC"><span class="dot" style="background:#2b6cb0"></span><span data-i18n="airCtrl">Контролирано</span></span>'
  '<span class="chip" id="cbAirS"><span class="dot" style="background:#d0202a"></span><span data-i18n="airSpec">Специални зони</span></span>'
  '</div>'
  '<div class="airnote"><span class="airsw" style="background:#d0202a"></span><span data-i18n="airLegRPD">забранени / ограничени / опасни</span>'
  '<span class="airsw" style="background:#d81fbf;margin-left:6px"></span><span data-i18n="airMil">военни</span></div>'
  '<div class="flnote" data-i18n="airFL180">Показва се само до FL180 (18 000 ft)</div>'
  '</div>')


# NOTAM section: one toggle + a colour/letter key (P/R/D/M/!). Own section because
# NOTAM is dynamic ("active now"), unlike the static airspace/zones. Default OFF.
NOTAM_SECTION = (
  '<div class="psec"><div class="psh" data-i18n="secNotam">NOTAM (временни)</div>'
  '<div class="prow">'
  '<span class="chip" id="cbNotam"><span class="dot" style="background:#d0202a"></span><span data-i18n="ntShow">NOTAM</span></span>'
  '</div>'
  '<div class="airnote">'
  '<span class="ntk" style="background:#d0202a">P</span><span data-i18n="ntP">забранена</span>'
  '<span class="ntk" style="background:#d0202a">D</span><span data-i18n="ntD">опасна</span>'
  '<span class="ntk" style="background:#d0202a">R</span><span data-i18n="ntR">ограничена (щрих)</span>'
  '<span class="ntk" style="background:#d81fbf">M</span><span data-i18n="ntM">военна</span>'
  '<span class="ntk" style="background:#00897b">O</span><span data-i18n="ntO">препятствие</span>'
  '<span class="ntk" style="background:#ef6c00">!</span><span data-i18n="ntW">предупреждение</span>'
  '</div>'
  '<div class="flnote" data-i18n="ntUpc">приглушените са предстоящи (все още неактивни)</div>'
  '<div class="flnote" data-i18n="ntSrc">Международна серия (FAA)</div>'
  # freshness stamp, filled by JS in the page language while the layer is ON
  # ("данни към HH:MM" / "data as of HH:MM"); hidden when OFF or before data
  '<div class="flnote" id="wxntfresh" style="display:none"></div>'
  '</div>')


SHELL_JS = r"""
// ---- UI shell: menu drawer, loupe, mutual exclusivity, mobile viewport ----
(function(){
  var leftui = document.getElementById('leftui'),
      menubtn = document.getElementById('menubtn'),
      panel = document.getElementById('panel'),
      loupe = document.getElementById('loupe'),
      loupebtn = document.getElementById('loupebtn');
  window.closePanel = function(){ panel.hidden = true; menubtn.classList.remove('on');
    leftui.classList.remove('panelopen'); };
  function openPanel(){ panel.hidden = false; menubtn.classList.add('on');
    leftui.classList.add('panelopen');
    if (window.closeWxPanel) window.closeWxPanel(); // only one drawer open at a time
    if (window.closeBmPanel) window.closeBmPanel();
    collapseLoupe(); }
  menubtn.onclick = function(e){ e.stopPropagation();
    if (panel.hidden) openPanel(); else window.closePanel(); };
  var panelclose = document.getElementById('panelclose');
  if (panelclose) panelclose.onclick = function(e){ e.stopPropagation(); window.closePanel(); };
  // a click anywhere outside the open panel closes it (same as the weather card)
  document.addEventListener('click', function(e){
    if (!panel.hidden && e.target.isConnected && !panel.contains(e.target) && !menubtn.contains(e.target)) window.closePanel();
  });
  // loupe: 🔍 expands to the search box; collapses on select / outside click
  window.collapseLoupe = function(){ loupe.classList.remove('open'); };
  loupebtn.onclick = function(e){ e.stopPropagation(); loupe.classList.add('open');
    var q = document.getElementById('q'); if (q) q.focus(); };
  document.addEventListener('click', function(e){
    if (!loupe.contains(e.target)) collapseLoupe();
  });
  // mobile browser chrome at the bottom: expose its height as --vp-bottom
  function vpBottom(){
    var vv = window.visualViewport, off = 0;
    if (vv){ off = Math.max(0, Math.round((window.innerHeight || 0) - (vv.offsetTop + vv.height))); }
    document.documentElement.style.setProperty('--vp-bottom', off + 'px');
  }
  if (window.visualViewport){ window.visualViewport.addEventListener('resize', vpBottom);
    window.visualViewport.addEventListener('scroll', vpBottom); }
  window.addEventListener('resize', vpBottom); vpBottom();
})();
// ---- collapsible disclaimer (#info): phones start collapsed behind the "!" ----
(function(){
  var info = document.getElementById('info'),
      tog = document.getElementById('infotoggle');
  if (!info || !tog) return;
  // small screen = a phone in either orientation (narrow OR short) — matches the
  // disclaimer's collapse CSS, so landscape rotation doesn't reopen it
  var mq = window.matchMedia('(max-width:640px), (max-height:500px)');
  function apply(){ info.classList.toggle('collapsed', mq.matches); }
  apply();
  if (mq.addEventListener) mq.addEventListener('change', apply);
  else if (mq.addListener) mq.addListener(apply);
  tog.onclick = function(e){ e.stopPropagation(); info.classList.toggle('collapsed'); };
  // a click anywhere outside the open disclaimer collapses it (same as the
  // popups/panels); only where it is collapsible (phones). Capture phase so it
  // fires even when the clicked control stops propagation (e.g. the attribution
  // "i" button) — this is what makes the disclaimer and the attribution mutually
  // exclusive: opening one closes the other, on both maps.
  document.addEventListener('click', function(e){
    if (mq.matches && !info.classList.contains('collapsed') &&
        e.target.isConnected && !info.contains(e.target)) info.classList.add('collapsed');
  }, true);
})();
// ---- fullscreen toggle (top-right). Hidden where the Fullscreen API is
// unsupported (e.g. iOS Safari). Each page also resizes its own map on change. ----
(function(){
  var fsbtn = document.getElementById('fsbtn');
  if (!fsbtn) return;
  var root = document.documentElement;
  if (!root.requestFullscreen){ fsbtn.hidden = true; return; }
  fsbtn.onclick = function(e){ e.stopPropagation();
    if (!document.fullscreenElement){ root.requestFullscreen().catch(function(){}); }
    else if (document.exitFullscreen){ document.exitFullscreen(); } };
  function render(){ var on = !!document.fullscreenElement;
    fsbtn.classList.toggle('on', on);
    var i = fsbtn.querySelector('.fs-in'), o = fsbtn.querySelector('.fs-out');
    if (i) i.hidden = on; if (o) o.hidden = !on;
    fsbtn.setAttribute('aria-label', on ? 'exit fullscreen' : 'fullscreen'); }
  document.addEventListener('fullscreenchange', render); render();
})();
// ---- theme: light / dark / system (default system). UI ONLY — the map basemap
// is never touched (a dark MAP is a separate choice in the basemap selector).
// Preference lives in the shared ST store, so it carries across pages and reloads;
// ⟳ reset clears ST -> back to system. "system" follows the OS setting live. ----
(function(){
  var seg = document.getElementById('thmseg');
  var mq = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;
  function pref(){ try{ return ST.get('theme', 'system'); }catch(e){ return 'system'; } }
  function resolved(p){ return (p === 'dark' || (p !== 'light' && mq && mq.matches)) ? 'dark' : 'light'; }
  window.wxApplyTheme = function(){
    var p = pref();
    document.documentElement.setAttribute('data-theme', resolved(p));
    if (seg) Array.prototype.forEach.call(seg.querySelectorAll('button'), function(b){
      b.classList.toggle('on', b.getAttribute('data-thm') === p); });
  };
  if (seg) seg.addEventListener('click', function(e){
    var b = e.target.closest('button[data-thm]'); if (!b) return;
    e.stopPropagation();
    try{ ST.set('theme', b.getAttribute('data-thm')); }catch(e2){}
    window.wxApplyTheme();
  });
  if (mq){ var onOS = function(){ if (pref() === 'system') window.wxApplyTheme(); };
    if (mq.addEventListener) mq.addEventListener('change', onOS); else if (mq.addListener) mq.addListener(onOS); }
  window.wxApplyTheme();
})();
"""
