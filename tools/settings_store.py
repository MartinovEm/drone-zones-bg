"""Shared settings store injected into every map page.

One localStorage record (key 'settings', a small JSON object) holds every
user-adjustable switch, so a choice survives page reloads AND carries over
when the user switches between map pages (2D <-> 3D today; any future page
that injects this store joins automatically). Each feature reads its key at
startup and writes it on change:

    ST.get('cld', false)   -> saved value, or the given default
    ST.set('cld', true)    -> saves immediately
    ST.clear()             -> wipes the whole record (the reset button)

Current keys: fP/fA/fC (colour filter chips), cld/rad/fc/pln (clouds, radar,
rain forecast, aircraft), fch (forecast slider hour), obs (the obstacles + the 3D
buildings, default ON; the old bld key is no longer read), aero (airfields,
helipads and hospitals, default OFF),
pitch/bearing (3D camera angle). The language stays under its pre-existing
separate 'lang' key. A future setting (theme, basemap, ...) just picks a new
key - no other wiring needed.

A shared-view link (ROADMAP 8b, `?v=<base64url JSON>`) carries the sender's whole
record. While it is open the page reads the LINK's record instead of the visitor's,
and nothing is written back: the visitor's own settings stay as he left them
(owner 20.10). Only the theme, which the link never carries, stays his own and is
saved as usual. ST.shared = the decoded link (null on a normal visit); ST.all() =
the record to put into a new link.

make_3d.py inserts ST_JS at the top of the page script.
"""

ST_JS = r"""
// ---- shared settings store: one localStorage JSON record for every switch ----
var ST = (function(){
  var KEY = 'settings', data = {}, saved = {}, shared = null;
  try{ saved = JSON.parse(localStorage.getItem(KEY)) || {}; }catch(e){ saved = {}; }
  // a shared-view link: the sender's view for THIS visit only, never written to this visitor's record
  try{ var m = location.search.match(/[?&]v=([^&#]+)/);
    if (m){ var s = m[1].replace(/-/g, '+').replace(/_/g, '/'); while (s.length % 4) s += '=';
      var bin = atob(s), u8 = new Uint8Array(bin.length); for (var i = 0; i < bin.length; i++) u8[i] = bin.charCodeAt(i);
      shared = JSON.parse(new TextDecoder().decode(u8));
      if (!shared || shared.v !== 1 || !shared.st || typeof shared.st !== 'object') shared = null; } }catch(e){ shared = null; }
  if (shared){
    for (var k in shared.st) if (k !== 'theme') data[k] = shared.st[k];
    if (Object.prototype.hasOwnProperty.call(saved, 'theme')) data.theme = saved.theme;
    // the forecast hour travels as an absolute time; one that has passed (or is beyond the 72 h
    // slider) opens at "now" (owner 20.10)
    var h0 = Math.floor(Date.now() / 3600000) * 3600000, fh = shared.t ? Math.round((shared.t - h0) / 3600000) : 0;
    data.fch = (fh >= 1 && fh <= 72) ? fh : 0;
  } else data = saved;
  return {
    get: function(k, dflt){ return Object.prototype.hasOwnProperty.call(data, k) ? data[k] : dflt; },
    set: function(k, v){ data[k] = v;
      if (shared){ if (k !== 'theme') return; saved.theme = v; try{ localStorage.setItem(KEY, JSON.stringify(saved)); }catch(e){} return; }
      try{ localStorage.setItem(KEY, JSON.stringify(data)); }catch(e){} },
    clear: function(){ data = {}; saved = {}; try{ localStorage.removeItem(KEY); }catch(e){} },
    all: function(){ var o = {}; for (var k in data) if (k !== 'theme') o[k] = data[k]; return o; },
    shared: shared
  };
})();
"""
