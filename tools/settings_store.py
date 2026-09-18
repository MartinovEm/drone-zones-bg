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
rain forecast, aircraft), fch (forecast slider hour), bld (3D buildings),
pitch/bearing (3D camera angle). The language stays under its pre-existing
separate 'lang' key. A future setting (theme, basemap, ...) just picks a new
key - no other wiring needed.

make_3d.py inserts ST_JS at the top of the page script.
"""

ST_JS = r"""
// ---- shared settings store: one localStorage JSON record for every switch ----
var ST = (function(){
  var KEY = 'settings', data = {};
  try{ data = JSON.parse(localStorage.getItem(KEY)) || {}; }catch(e){ data = {}; }
  return {
    get: function(k, dflt){ return Object.prototype.hasOwnProperty.call(data, k) ? data[k] : dflt; },
    set: function(k, v){ data[k] = v; try{ localStorage.setItem(KEY, JSON.stringify(data)); }catch(e){} },
    clear: function(){ data = {}; try{ localStorage.removeItem(KEY); }catch(e){} }
  };
})();
"""
