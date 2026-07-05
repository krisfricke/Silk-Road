# Silk Road — Map Editing Notes (how-to + hard-won lessons)

Purpose: stop re-learning the same map lessons every time. Read this BEFORE touching any baked map PNG.

## The reveal map: Maps/dzungaria762.png (the "country behind you" Dzungaria map)
Files:
- Maps/dzungaria762.png  — the LIVE image the game shows.
- Maps/_dzungaria_base.png — approved baseline: relief + BOTH routes (lower valley road + upper
  Dzungarian-Gate loop) + rivers + original small baked labels. Treat as READ-ONLY truth for routes/relief.
- Maps/_ili_clean_summer.png — LABEL-FREE, CIRCLE-FREE render of the same area, PIXEL-ALIGNED with
  _dzungaria_base (corner diff = 0.0). This is the "clean terrain" source for erasing things.
- outputs/_bake_ili.py + outputs/_cfg_ili_*.json — the DEM baker + configs. Bounds [73,91,41.0,46.6],
  output 1980x616, ~12-18s, needs rasterio + _ili_mosaic.tif.

Coord conversion (bounds 73-91 lon, 41-46.6 lat, image 1980x616):
  x = (lon-73)/(91-73)*1980
  y = (46.6-lat)/(46.6-41)*616

## GOLDEN RULE for removing a baked label
NEVER median-paint / flat-fill over a label — it destroys relief, rivers and routes and looks awful
(this is exactly what went wrong with Almaliq). Instead COPY the same rectangle from a pixel-aligned,
label-free render (_ili_clean_summer.png):
    base[y0:y1, x0:x1] = clean[y0:y1, x0:x1]
Then verify: erased box residual vs clean should be ~0.
If the label sits on a route that's only in the base (e.g. the upper Gate loop is NOT in _ili_clean),
keep the erase box to the part clear of those dashes (labels usually sit below/beside the route).

## To ADD labels/dots/stubs
Draw as an OVERLAY composited on top (PIL ImageDraw -> alpha_composite). Additive never destroys.
Bold serif + 4px cream stroke so text reads over terrain. Town dot = red circle, cream outline.

## Known label locations in _dzungaria_base.png (px)
- Suyab dot ~(242,417); old label ~(130-216,394-426)
- Beshbalik dot ~(1783,277); old label ~(1594-1744,268-291)
- Turfan dot ~(1782,403); old label ~(1686-1800,405-432)
- Almaliq (REMOVED): ~(850-968,278-328), on the lower route
- Bole (REMOVED): ~(963-1026,143-170), upper route runs ABOVE it
- "the Dzungarian Gate" (KEEP, geographic): ~(960-1100,90-118)

## GOTCHAS that burned time
1. Crop-scale misreads: recompute orig = box_origin + display/scale carefully (mislocated Bole ~150px twice).
2. cur-vs-clean diff ALSO flags the upper route (not present in _ili_clean) — a diff blob may be route, not text.
3. Don't recreate routes with A* "stubs" casually — it produced a wrong path (missed the Gate, doubled itself).
   The correct two-route geometry lives in _dzungaria_base; preserve it, don't re-derive it.
4. The TWO routes are the fork (over-the-passes vs north-around / Dzungarian Gate) — never drop one.
5. Browsers cache map PNGs — hard-reload (Ctrl+Shift+R) after changing an image.

## Rebuild recipe (current good state)
1. Start from _dzungaria_base.png.
2. Erase old town labels + Almaliq + Bole by copying those boxes from _ili_clean_summer.png.
3. Overlay: prominent Suyab / Beshbalik(above dot) / Turfan; "to Talas" west of Suyab;
   "to Hami" off BOTH Beshbalik and Turfan. Keep "the Dzungarian Gate".
4. Save to Maps/dzungaria762.png; verify erased boxes ~0 residual vs clean.

## General project notes
- Game is one file: index.html. Edits via shell Python exact-string/regex replace (Edit/Write tools are
  blocked for this folder). Bump const VERSION. Verify with node --check on the extracted <script>.
- Temp crop/preview files may pile up in the workspace (_tmpcrop/, _rebake_preview.png) — safe to delete.

## Round-2 lessons (label removal: Almaty / Bole / the passes / Gate legibility)
- I mislocated "Bole" THREE times by eyeballing coordinates off resized crops. STOP doing that.
  Reliable method: build ONE annotated composite — crop each candidate region and print its exact
  pixel box ON the image — then read identity + box together. (See the z_composite approach.)
- A "residual == 0 vs clean" check only proves your BOX matches clean terrain; it does NOT prove you
  boxed the right label. ALSO view the result to confirm the label is actually gone.
- Confirmed baked-label boxes in _dzungaria_base.png (px):
    Suyab old label      130-216 , 394-426
    Beshbalik old label  1594-1744, 268-291
    Turfan old label     1686-1800, 405-432
    Almaliq              850-968 , 278-328   (on the lower route)
    Bole                 978-1074, 160-199   (upper route runs ABOVE it)
    Almaty               416-518 , 353-386
    "the passes"         686-840 , 370-402   (italic, sits just BELOW the lower route)
    "the Dzungarian Gate"843-1120, 62-110    (slanted italic, illegible -> erase & redraw)
- To fix an illegible baked label: erase its box from clean, then REDRAW it in the overlay with the
  legible font (DejaVuSerif-Bold + cream stroke). The Gate is now redrawn at ~(1005,120), below the route.
- Labels that imply permanent settlements were ALL removed per the user (Almaliq, Bole, Almaty).
  "the Dzungarian Gate" stays (geographic). "the passes" removed (not needed).
- Workflow that finally worked, every time: (1) start from _dzungaria_base, (2) erase each unwanted
  label box by copying from _ili_clean_summer, (3) draw wanted labels/stubs as an overlay,
  (4) print residual-vs-clean for each erase AND eyeball the final image before shipping.

## Round-3 lessons (the BIG ones — light labels & route-overlap)
- TWO KINDS OF LABELS exist on the baked map:
    * DARK town labels (Suyab, Beshbalik, Turfan, Almaliq, Bole, Almaty) — find via dark-pixel detection.
    * LIGHT cream-italic GEOGRAPHIC labels ("the passes", "the Dzungarian Gate") — dark detection MISSES
      these. Detect with: base.min(channel) > ~165 AND differs from clean. This was the root of repeated failure:
      I kept boxing dark pixels (= the ROUTE) instead of the light text, which ERASED route segments.
- ROUTE-OVERLAP RULE: the clean source (_ili_clean_summer) has only route-A (the A* leg), NOT route-B
  (the second/Dzungarian-loop route added by the old script). So clean-copying ANY box that covers route-B
  deletes that route. Before erasing, check whether the box overlaps route-B.
    * If a label sits CLEAR of route-B -> erase by clean-copy (e.g. "the passes": light text sits just ABOVE
      its route, so a tight box on the text only is safe).
    * If a label OVERLAPS route-B (e.g. "the Dzungarian Gate" lies on the loop) -> DO NOT erase. COVER it
      instead: draw the new legible label as an overlay (dark bold + thick cream stroke) right on top. An
      overlay never deletes route pixels.
- Confirmed LIGHT-label boxes: "the passes" x774-866 y351-372 ; "the Dzungarian Gate" x~930-1090 y74-90.
- Diagnostic that finally nailed the gaps: render removed-dark pixels in bright red over the map
  (base_dark & ~current_dark) — route gaps show as line segments, erased labels as blobs.
- Salt-lake route gap was a mislocated "the passes" box (30px too high) landing on the route, not the label.
  Lesson: locate light labels by bright-pixel detection, never by eyeballing a scaled crop.

## Quick checklist before shipping a map edit
1. Start from _dzungaria_base.png. 2. Dark labels: erase via clean-copy. 3. Light labels: detect bright
   pixels; erase only if clear of route-B, else COVER with an overlay. 4. Render the red removed-pixel diff
   and confirm NO route segments are red. 5. Eyeball the final image. 6. Hard-reload to view (PNG cache).

## Round-4 lesson (the Lake Aibi/Ebi route gap)
WHY IT HAPPENED: erasing the **Bole** label box clean-copied terrain there, but **route-B passed
diagonally THROUGH the Bole box** (route-B enters from the top ~(1038,158) and exits toward the lake
~(1082,200); Bole's text sat just left of that line). Because the clean source has NO route-B, copying
clean = deleting the route. Crucially, the "residual == 0 vs clean" check returned 0 here — that is the
trap, not reassurance: matching clean is EXACTLY what a deleted route-B looks like. The residual check
can never detect route-B loss because route-B isn't in clean.

PREVENTION (do this for EVERY erase, dark OR light labels):
1. Compute routeB = (base dark) & (clean NOT dark). BEFORE erasing a box, check `routeB[box].any()`.
   If the box intersects route-B, the erase WILL cut the route.
2. If it intersects: either (a) shrink the box so it clears the route line, or (b) erase, then redraw the
   route across the box: probe routeB just OUTSIDE the box on each side to get the route's entry/exit
   points, and draw a dashed bridge (dark, dash 9 / gap 7, width 3) between them.
3. ALWAYS finish with the red removed-dark diff (base_dark & ~current_dark) and confirm NO red line
   segments remain — red blobs (erased label text) are fine, red LINES are deleted route = must fix.
Note: a DARK label can overlap route-B too (Bole did), so this check is not just for light labels.

## Round-5 lesson (route repair: RESURRECT, never draw)
DO NOT draw a replacement route segment by hand — a straight drawn bridge cannot match the original's
curve and ends up misaligned (this caused the "misaligned course" complaint). The route pixels still exist
intact in the pre-erase base (_dzungaria_base.png), so RESURRECT them:
  routeB = (base dark) & (clean NOT dark)        # the real route-B pixels
  result[region] = clean[region]                 # reset patch to terrain
  mask = routeB in region, MINUS a tight box over only the label glyphs that sit CLEAR of the route line
  result[mask] = base[mask]                       # copy the actual route pixels back (true curve)
Key subtlety at Lake Aibi: the route descended diagonally THROUGH the "Bole" label, so the exclusion box
must cover only the dot + the left letters that are off the route (x<~1048 here). If the box's edge reaches
the route's x at any y, it clips the line and reopens a gap — keep the box strictly left of/away from the
route at every y it spans. A couple of label-pixels that lie right on the route can stay; the dashes hide them.
RULE OF THUMB: to fix any erased/!broken course, always copy the real pixels back from the pre-erase image;
only ever DRAW a route for a brand-new course that never existed.

## STANDARD PROCEDURE for a new section/departure map (use this every time)
At this point every city-to-city course is already plotted in the baked/wired maps; a new map is just a
closer look at one section. Steps:

(1) Identify the cities the map is FOR (e.g. Beshbalik + Turfan).
(2) Identify the surrounding destinations that must be in-frame (e.g. Kucha, Miran, Dunhuang, Hami; Suyab
    too — but if a destination is very far, cut the frame off after the nearest in-scope city, only when
    specified — here we cut the west end just past Kucha and did NOT extend to Suyab). Set the bake bounds
    to include those cities with margin so the FOR-cities aren't on the very edge. Don't remake the whole
    region; leave the existing shared maps (e.g. taklamakan762.png, tarim_region762.png) untouched.
(3) Draw the EXISTING established courses (don't invent new ones), INCLUDING the portions that lead off the
    map. Off-map legs must exit in the CORRECT direction — this is the step that's gone wrong before:
      - Data: city lon/lat = DESERT_LL; desert crossings = SHORTCUTS; rim sequences = NORTH/SOUTH order.
      - For routes the game draws as straight chart-lines (the Tarim rim + shortcuts), draw a straight
        dashed line to the real next-city coordinate (even if off-canvas) and let the image clip it — the
        exit angle is then automatically correct.
      - For routes that are BAKED/curved (e.g. the Dzungarian Beshbalik->Suyab leg goes WEST along ~lat 44
        and loops, it does NOT head straight at Suyab's latitude), follow the real route's direction, not a
        straight line to the city. If unsure, bake a larger frame that contains the whole leg, then crop.
      - Never guess an off-map bearing; always aim at the real coordinate or trace the real route.

Build method: bake RELIEF ONLY (legs=[],stubs=[],landmarks={}) for the bounds, then draw routes + city
dots + labels as a PIL overlay (additive, never destructive). City pixel coords come from the bake's COORDS
printout. Main/rim roads = dark dashes (dash 12 / gap 8 / w4); desert SHORTCUTS = a lighter, finer dotted
line (brown, dash 6 / gap 9 / w3). Per design, the desert shortcuts are meant to appear only on MOUSEOVER
of a proposed destination when wired into the game — so leave them OUT of the baked base image and add them
as a hover overlay at wiring time.

Example just built: turfan_beshbalik762.png — bounds [81.5,95.3,38.3,45.0], FOR Turfan+Beshbalik, dests
Kucha/Miran/Dunhuang/Hami, off-map stubs to Suyab (W, ~lat44), Aksu (W), Khotan (SW), Jiuquan (E).

## CRITICAL: "match the existing routes" — WHY it keeps failing & the rule
WHY IT FAILED (again): I drew straight lines between city coordinates, assuming routes are straight
chart-lines. They are NOT. Many established legs are carefully-baked CURVED POLYLINES, stored in two places:
  - In the game: CHARTS[chartKey].legs["A|B"].pts = [[x,y],...] (px in that chart, with chart .geo bounds).
    (e.g. hexi.legs has Hami|Dunhuang, Miran|Dunhuang, Dunhuang|Jiuquan.)
  - On disk: outputs/<map>_routes.json -> land:[{leg:[A,B], pts:[[x,y],...]}] (px in that bake's bounds).
    (e.g. _north_ili_ext_routes.json = the curved Beshbalik<->Suyab course; steppe762_routes.json = the
     steppe legs.)
NOTE: a match for "A|B" in index.html may be LEG_TERRAIN (terrain strings), NOT geometry — ignore those.

THE RULE (do for EVERY leg on a new section map):
1. Look up the leg's established geometry FIRST:
   - search CHARTS[*].legs for "A|B":{pts:...}  (and remember that chart's geo bounds)
   - else search outputs/*_routes.json land[] for leg [A,B]  (and that bake's bounds)
2. If a polyline exists, REPROJECT it and draw that exact curve:
       src px -> lon/lat   via source bounds:  lon=W+(x/srcW)*(E-W),  lat=N-(y/srcH)*(N-S)
       lon/lat -> new px    via new bounds:     x=(lon-W2)/(E2-W2)*DW, y=(N2-lat)/(N2-S2)*DH
   (Verify: a reprojected endpoint must land on the new map's city dot. Then the off-map portion exits in
    the correct direction automatically because it IS the real route.)
3. ONLY if NO polyline exists anywhere is the leg drawn straight (those are the truly live chart-line legs:
   e.g. Turfan-Kucha, Hami-Turfan, Beshbalik-Hami). A straight dash then matches the game.
Never approximate a baked route with a straight line or a fresh A* path.

## WHERE ESTABLISHED ROUTE GEOMETRY LIVES — check in THIS order (do this first, every time)
A route's plotted curve can be in one of three places. Search them in order; stop at the first hit:
 1. IN THE GAME: CHARTS[chart].legs["A|B"] = "x,y x,y ..." (space-separated px STRING) in index.html.
    Reproject px with that chart's .geo = [W,E,S,N] and its vbw/vbh.   (e.g. hexi.)
 2. ON DISK: outputs/<map>_routes.json -> land:[{leg:[A,B], pts:[[x,y]...]}].  Bounds are NOT in the json;
    get them from that map's chart .geo or its bake config.   (e.g. _north_ili_ext_routes.json = Beshbalik-Suyab,
    bounds [73,91,41,46.6] 1980x616 ; steppe762_routes.json = the steppe legs.)
 3. ONLY IN A BAKE SCRIPT (no saved data): some maps computed routes at bake time via an A* route() and never
    dumped them — the geometry exists ONLY by re-running that script. THIS WAS THE TARIM CASE
    (bake_taklamakan.py). You must regenerate it (recipe below).
 (A bare "A|B" match in index.html may just be LEG_TERRAIN — terrain strings, not geometry. Ignore those.)

### Recipe to regenerate routes from a bake script that never dumped them
   head -n <last line BEFORE the image write> bake_xxx.py > _dump_xxx.py
   # append: dump routesPX (already-smoothed px) + bounds [LO0,LO1,LA0,LA1] + DW,DH to json, then STOP
   #         (exiting before the seasonal image bake = the live map PNG is NOT overwritten).
   # to also get a leg the script's LEGS list doesn't have (e.g. an arbitrary cutoff to a lon/lat point):
   #   add  cut = smooth([ll2px(*c) for c in route(C['Turfan'], (86.9,44.2))])  in the same run
   #   (route()/USED carry shared-corridor state, so compute it inside the same run, not separately).
   python3 _dump_xxx.py    # ~15-240s; writes _xxx_routes_dump.json {DW,DH,bounds,routes:[{leg,px}]}

### Then reproject + draw (same as always)
   src px -> lon/lat (via src bounds) -> new px (via new bounds); draw as dashed polyline; VERIFY an endpoint
   lands on the new city dot (<~2px). Off-map portions then exit correctly because they ARE the real curve.

### REGION INDEX (so next time it's a lookup, not a hunt)
 - Tarim rim  (Dunhuang-Hami, Hami-Turfan, Turfan-Kucha, Kucha-Aksu, Aksu-Kashgar, Kashgar-Yarkand,
   Yarkand-Khotan, Khotan-Miran, Miran-Dunhuang, Beshbalik-Hami, Suyab-Beshbalik, Talas-Suyab, Kashgar-Osh)
     -> SOURCE: bake_taklamakan.py (route() A*); bounds [71,95,35,44.7] DW1980 DH800; NOT saved -> re-run to dump.
 - Hexi / Gansu (Miran-Dunhuang, Hami-Dunhuang, Dunhuang-Jiuquan, Jiuquan-Zhangye, Zhangye-Wuwei,
   Wuwei-Lanzhou, Lanzhou-Chang'an, Chang'an-Luoyang) -> CHARTS.hexi.legs strings; geo [88.5,113,32.5,43.5] 1980x889.
 - Steppe (Bukhara-Samarkand, Samarkand-Chach, Chach-Ispijab, Ispijab-Talas, Talas-Suyab,
   Samarkand-Akhsikath, Akhsikath-Kashgar) -> steppe762_routes.json (bounds from steppe chart/_bake_steppe cfg).
 - Dzungaria (Beshbalik-Suyab curved westward course) -> _north_ili_ext_routes.json, [73,91,41,46.6] 1980x616.
 RULE: rim/oasis/steppe/mountain courses are ALWAYS plotted curves from one of the above. The ONLY straight
 lines are the cross-desert SHORTCUTS that were never plotted (and those are mouseover-only, never baked in).

## STEP: city LABELS — never get an "underlying name" (and how to remove one cleanly)
The recurring failure: a small baked name sits UNDER the big overlay name, and trying to paint it out wrecks
the terrain. PREVENT it structurally + verify:
 1. The relief bake must be LABEL-FREE. _bake_ili.py draws NO city text (cities are used only for COORDS and
    routing) — keep it that way. After baking, VERIFY: zoom the RAW _xxx_summer.png at 2-3 city spots; it must
    show clean terrain, no names. If you ever see a baked name, the base is wrong — re-bake clean, don't paint.
 2. Draw exactly ONE overlay label per city (the town() helper). The overlay is the ONLY source of names, so
    there is no underlying name to remove.
 3. VERIFY before shipping: diff final-vs-label-free-base at each city (mask diff>40) and zoom ~5x; you must see
    a single name + dot + routes. (A stray mark beside a dot is usually a ROUTE DASH, not a second label — check
    the overlay-only diff before "fixing" it.)
 4. Fix label COLLISIONS by REPOSITIONING in the overlay (move the anchor/offset), NEVER by painting. Crowded
    corners (e.g. Dunhuang next to "to Jiuquan" + "the Jade Gate") -> put the city name above its dot ("mm",
    dy=-26) and push the stub label to the edge.
 5. If a label is genuinely baked into an OLD image and must go: re-bake the SAME bounds label-free and copy
    that rectangle of clean terrain over the baked name (the pixel-aligned clean-copy method), then redraw the
    label in the overlay. Never flat-paint.

### CORRECTION to the LABELS step — the real cause of "a label under the city name"
It was NOT a baked underlying name (the relief is verified label-free). It was an OFF-MAP STUB label
("to Suyab", "to Khotan") drawn on top of the city. Cause: I placed each stub at the route polyline's
LAST in-canvas point. For a leg that comes INTO the map (Suyab->Beshbalik, Khotan->Miran) that endpoint
IS the in-map city -> the stub landed exactly on Beshbalik / Miran and read as a second small label.
FIX / RULE: place an off-map stub at the EDGE CROSSING — the in-canvas point of the segment that straddles
the canvas boundary — NEVER at the polyline endpoint. Helper:
    def crossing(pts):
        inb=lambda p:0<=p[0]<=DW and 0<=p[1]<=DH
        for i in range(len(pts)-1):
            a,b=pts[i],pts[i+1]
            if inb(a)!=inb(b): return a if inb(a) else b
        return pts[-1]
Works regardless of polyline direction (inbound or outbound). VERIFY: print each crossing — it must sit on
a map edge (x≈0/DW or y≈0/DH), not on a city dot. (Diagnostic note: an overlay-diff "current minus base"
HIDES anything identical in both, so it can't prove the base is clean and it can't reveal a stub sitting on a
city — zoom the actual final image at each city instead.)

## CANON: the Jade Gate routing takes PRECEDENCE
As of this revision, Dunhuang's western/northern departures route THROUGH the Jade Gate (Yumen Guan,
~93.87E,40.36N): Dunhuang -> Jade Gate is one shared leg, then it forks Jade Gate -> Hami and Jade Gate -> Miran
(computed with the standard least-grade A* route() in bake_taklamakan.py, terrain+sand cost). These supersede
the OLD direct Dunhuang-Hami and Dunhuang-Miran courses.
RULE: wherever any other map (incl. the big whole-basin tarim_region762 / taklamakan762) still shows Dunhuang
going direct to Hami or Miran WITHOUT passing the Jade Gate, the Jade-Gate version is canonical and wins. Those
older maps are to be reconciled to it later (NOT redone now). The canonical Jade-Gate polylines (lon/lat) are
saved in outputs/_jade_routes.json (keys jade, Dunhuang|JadeGate, JadeGate|Hami, JadeGate|Miran).

## NOTE: the odd greenish-grey by Turfan = BELOW-SEA-LEVEL elevation color (not water)
The relief shader colors by elevation. Its lowest ramp stops (<2 m) were a greenish-grey (150,160,150),
which is why the Turfan Depression floor (Aydingkol basin, down to ~-161 m — the only sub-sea-level land on
these maps) looked uniquely bluish-green against the tan. It is NOT a lake.
FIX (chosen: pale salt flat): changed the ramp lowest stops in _bake_ili.py to a pale salt tone
((-50)->(214,208,191), (2)->(196,186,150)); future bakes inherit it. For the already-baked _tb_summer base I
recolored in place by DEM mask (elev<2 full salt, fading out to 80 m), preserving hillshade texture; original
saved as Maps/_tb_summer_greenbak.png. Lop Nor (the SE blue blob) is unaffected — it sits at ~800 m and is drawn
from the lakes layer, not the elevation ramp.

## MAP: turfan_beshbalik_main762.png  (the MAIN Turfan/Beshbalik departure map)
Tight departure map for Turfan AND Beshbalik. Bounds [85.2,94.2,41.5,44.7], 1980x704.
Framing: ~1.7deg W of the Turfan-bypass/Beshbalik-Suyab junction (86.9,44.2); Hami at the E edge; just S of
Bosten Lake's south shore (~41.75); N enough to clear Beshbalik (44.05) + junction.
Built like the others: relief baked label/route-free via _bake_ili.py + _cfg_tbm.json (drawRoutes:false), then
overlay the ESTABLISHED reprojected curves: Suyab-Beshbalik, Beshbalik-Hami, Hami-Turfan, Turfan-Kucha,
Turfan-cutoff(bypass), JadeGate-Hami. Off-map stubs at edge crossings: to Suyab(W), to Kucha(SW), to the Jade Gate(S).
Inherits the salt-flat depression ramp. NOT wired into the game yet.
PLAN (future): clicking the UPPER portion of the wide Tarim-basin map opens this at Turfan; this is the main map
for Beshbalik. The wider turfan_beshbalik762.png is now kept only as the canonical REFERENCE for the
Dunhuang->JadeGate->Hami/Miran routes.

### turfan_beshbalik_main762 — route updates (3 fixes)
1. OVERLAP "solid line" bug: two dashed routes sharing a corridor (e.g. Beshbalik-Hami & Hami-Turfan from Hami
   to their fork) double-draw out of phase -> reads as a solid line. FIX: dash-dedup — keep a coverage set of
   ~6px cells; draw the through-routes first, and skip drawing a dash where a previous route already covered the
   cell. Each corridor draws once, with clean continuous dashes; branches draw only their unique parts.
2. Bypass didn't reach the Suyab road (dead-ended ~23 km short). FIX: put a waypoint ON the Beshbalik-Suyab road
   (WP=86.95,44.43, the nearest road vertex) and re-routed Turfan->WP via the standard A* (usual rules). Saved in
   Maps/_tbm_routes2.json key "Turfan|WP". (General rule: to connect a route to an existing course, snap the new
   endpoint to a vertex ON that course and re-route to it — don't draw a free-floating bridge.)
3. Added the direct Turfan->Beshbalik road THROUGH the Tian Shan (A* least-grade, ratio 1.15, finds the pass);
   key "Turfan|Beshbalik". It shares the pass-climb out of Turfan with the bypass, then forks.

### WIRED into game (v2.02.22): two chart variants from one map
Baked TWO label/dot-free variants (chart overlay supplies clickable dots+labels, so the bake must NOT include
city dots/names — only routes + edge stubs + relief):
- turfan_beshbalik_main762.png  = Mode A (Beshbalik set-out): bold = Beshbalik's departures (to Hami, to Suyab,
  the Turfan mountain road); faded dots = Turfan-only legs except where they overlap a bold route.
- turfan_beshbalik_fromTarim762.png = Mode B: bold = Turfan's routes; faded = Beshbalik-to-Hami / -to-Suyab
  except overlaps.
CHARTS entries added: `tbesh` (open:["Beshbalik"], Mode A) and `tbeshB` (open:[], Mode B, reached via link).
On the `tarim` chart a chartLink rect over Beshbalik (at:"Turfan" only) -> chartSwitch("tbeshB"); tbeshB has a
"back to the Tarim basin" link. City dot px on these maps: Beshbalik 847,143 · Turfan 876,389 · Hami 1828,411.
De-emphasis technique: draw bold routes' coverage cells first, then draw faded routes skipping those cells
(faint dotted), then bold dashes on top -> shared corridors render bold, unique faded parts stay faint.

### LESSON: in-game chart routes must be SVG VECTORS, not baked raster
First attempt baked the bold/faded routes INTO the chart PNG. The game scales a 1980px image down to ~750px in
the browser, which blurs raster dashes into faint near-solid lines (looked terrible). FIX: the chart bg is the
CLEAN relief only (turfan_beshbalik_base762.png = _tbm_summer); routes are drawn as SVG <polyline> at display
res via new chart fields fadeLegs/boldLegs (renderChart draws fade first faint-dotted, then bold dashes on top).
This matches every other chart (which use ch.legs polylines) and stays crisp at any zoom. Generated the polyline
point-strings (chart px, resampled ~8px) in outputs/_tbm_chartlegs.json; fade strings are pre-trimmed where they
overlap a bold route so shared corridors show bold only.
Other chart gotchas fixed: (a) city label is LEFT-anchored (text-anchor=start) so a label near the right edge
needs a big negative ldx to clear its dot (Hami ldx -140); (b) "secret"/shortcut city pairs render grey+faded by
default — to show one as a normal red destination on a specific chart, add it to the `ok` test for that chartKey
(did this for Turfan<->Beshbalik on tbesh/tbeshB); (c) indicate the through-road past a hub as a bold stub
(Hami -> the Jade Gate).

### v2.02.27 — gap road real travel, Suyab clickable, back-link moved, solo-hunt skip
- The Turfan<->Beshbalik gap road no longer teleports: turfanBeshGo now builds an S.dash kind:'gap' synthetic
  leg (screen='travel') like turfanDivert/akChach, so it takes real days with road events; arrival handled in
  dashArrive (sets the steppe/north route + restock).
- Suyab is now a destination you can set out for: added a clickable Suyab dot at the western edge of
  tbesh/tbeshB (replaced the "to Suyab" farLabel). From Turfan -> turfanSuyab() event -> gap road then auto-
  continues west toward Suyab (S.dash.toSuyab -> mapSetOutTo('Suyab') on arrival). From Beshbalik -> sets the
  'k' route and sets out west. Suyab also made clickable (kept faded) on the big tarim chart from Turfan.
- "back to the Tarim basin" chartLink moved from top-left to the lower-left corner on tbeshB.
- Solo party: hmStart skips the hunter-selection screen (livingParty().length===0 -> hmGo([hmYou()])).

### CORRECTION (v2.02.29) — emphasis rule for the from-Turfan inset
Bold = any leg ON THE WAY from the viewpoint city to a destination (incl. onward legs, e.g. Hami->Jade Gate).
Faded = legs not on a journey from the viewpoint. So on tbeshB (from Turfan): bold = HT, BYP, MTN, TK, jJH,
and the Suyab spur SB_west (WP->Suyab, since Turfan->Suyab goes by the bypass); faded = SB_east (WP->Beshbalik,
because Turfan reaches Beshbalik by the mountain road, not via WP) and BH (Beshbalik->Hami). Split SB at WP px(385,59).

## VEGETATION + LAKES + SEASONS on _bake_ili.py maps (steppe/Sogdiana)
- FOREST is now TWO belts (both gated by Blue-Marble greenness so they only appear where forest grows):
  conifer spruce/juniper ~1500-2950 m (dark green 58,94,60) and walnut-fruit BROADLEAF ~900-1700 m
  (warm green 106,130,58). Broadleaf is suppressed inside cfg "dryZones" (rain-shadowed / Tarim-facing slopes)
  so it does NOT green up Kashgar; steppe dryZones=[[74.0,77.4,37.5,40.8]] (juniper belt still shows there).
- LAKES/RESERVOIRS: _bake_ili default is a BLACKLIST (all lakes water except the named reservoir) — fine for
  other regions. Central Asia is full of Soviet reservoirs that look natural in GSHHS, so the steppe cfg uses a
  WHITELIST: cfg "ancientLakes"=[[76.78,42.40],[73.39,39.02],[75.17,41.84],[75.31,40.65]] (Issyk-Kul, Karakul,
  Son-Kul, Chatyr-Kul). With ancientLakes set, ONLY those (within 0.45 deg) are drawn as water; every other lake
  polygon -> marsh. This is what turns Chardara/Kayrakkum/Charvak/Andijan reservoirs back to marsh. (Rivers are a
  separate layer and always drawn — a blue-blob detector will conflate them with lakes; verify visually.)
- SEASONS are cfg-driven: cfg "seasons"=[[tag,snowline]...] (default [["summer",3450]] = summer-only, so section
  maps are unaffected). Steppe seasons = summer 3450 / autumn 2500 / winter 1500 / spring 2700 (lower snowline =
  more snow). Baker produces <base>_<season>.png for each + copies summer to <out>.

## READY-TO-USE recipe for the FUTURE SUYAB-CENTRED MAP (and any Central-Asian map)
Bake with outputs/_bake_ili.py + a cfg JSON. The vegetation/lake/season behaviour is ALL cfg-driven now, so a
new map just needs these keys (baker code needs no edits):
  "bounds":[W,E,S,N], "cities":{...}, "legs":[...], "out":"suyab762.png",
  "ancientLakes": [[76.78,42.40],[75.17,41.84],[75.31,40.65], ...],   # WHITELIST of natural lakes -> water.
        # Suyab/Zhetysu naturals: Issyk-Kul(76.78,42.40), Son-Kul(75.17,41.84), Chatyr-Kul(75.31,40.65),
        # + Balkhash(~74-77,45-46) IF the north edge reaches it. Do NOT list Kapchagay(77.68,43.83) — it's a
        # modern reservoir and MUST fall through to marsh. Everything not whitelisted -> marsh.
  "dryZones": [],   # Suyab's northern Tian Shan slopes ARE moist (apple/walnut homeland) -> usually none needed.
        # only add a [W,E,S,N] box if the frame includes a rain-shadowed flank (as Kashgar/Tarim did).
  "seasons": [["summer",3450],["autumn",2500],["winter",1500],["spring",2700]]   # 4-season snow; lower=snowier.
Veg belts are automatic (no cfg): broadleaf walnut-fruit ~900-1700m (warm green 106,130,58) under conifer
spruce/juniper ~1500-2950m (dark green 58,94,60), both gated by Blue-Marble greenness. Output: <out>_<season>.png
per season + <out> = summer copy. Wire into CHARTS with seasonal:true so chartImg picks the season.
Reference cfgs to copy: outputs/_cfg_steppe.json (full: fields, marshPolys, ancientLakes, dryZones, seasons).

## ANATOLIA (the flagship first map) — final setup
Baked by outputs/_bake_anat_lbl.py + _cfg_anat_setout.json (out=anatolia_relief_setout.png). Uses:
  vegMode:"temperate" (forest sea-level->treeline), lmSize:18 (smaller town labels; DO NOT move placements),
  seasons:[[summer,3450],[autumn,2500],[winter,1500],[spring,2700]], and addRivers:[...] hand-drawn Nile-delta
  distributaries (Rosetta W / Damietta E / central channel) since Natural-Earth has no delta branches.
Temperate forest greens (both bakers, in sync): broadleaf 78,108,50 / conifer 48,82,52 (deep forest green).
Game wiring: ANAT_IMG replaced by anatImg() -> Maps/anatolia_relief_setout_<chartSeason()>.png (seasonal).

## PERSIA CORRIDOR (persiacorridor762*) — Baghdad-corner label surgery (v2.05.x era, by Fable)
THE PROBLEM: bake_corridor.py baked minor names at lmSize 30 — nearly hub-label weight (game hubs are 34px
SVG). "Ctesiphon" stacked directly under the game-drawn "Baghdad" (dots ~18px apart — they ARE twin cities)
and read as a shouting two-line label. The baker + _cfg_corr.json lived in a dead session's outputs/ and are
LOST — no re-bake, no label-free clean render. Fixed by in-place pixel surgery on all 5 PNGs:
 - Ctesiphon + Kufa: erased (color-gated mask: dark glyphs min<110 OR cream-halo match, inside tight boxes
   x142-348/y672-717 and x133-228/y742-782, dilate 7x7, dot discs r14 protected) and REDRAWN at 22px
   DejaVuSerif-Bold, 1px cream halo at ~55% (the tuned 0.055xfont convention). Ctesiphon anchored ls at
   (152,701) — below Baghdad's game label with clear separation; Kufa ls at (137,771).
 - Hulwan/Kermanshah/Hamadan/Qom LEFT AT 30px on purpose: Hulwan's "an" crosses dark mountain relief —
   color-inseparable, inpainting it = the Almaliq failure. Rule applied: quiet the labels only where they
   crowd a hub; a full-size sweep needs a re-bake.
 - NEW LESSON — INPAINT SMEAR: cv2 TELEA/NS inpaint on the noise-grained plain leaves a visibly SMOOTH pale
   ghost where text was. Fix: after inpainting, re-grain the masked px with gaussian noise whose per-channel
   std is measured from the un-masked ring around the box (hf = region - blur9; std from clean px). This made
   the erase invisible at 3x zoom. ALWAYS re-grain after inpainting these maps.
 - Verified: removed-dark diff outside the label boxes = 59 px (dilation fringe only; route >100px away),
   rivers continuous in all seasons, in-game overlay simulated (red hub dot + 34px Baghdad at chart px 117,654).
 - Originals kept as Maps/_persiacorridor762*_lblbak.png. GitHub deploy copies synced.
 - PROPER LONG-TERM FIX: regenerate bake_corridor.py (GEBCO zips still in Maps/) with lmSize ~20-22 for ALL
   minor names; then this surgery is superseded.

## ALEPPO CHART (aleppo_relief762.png) — illegible minor names fixed (same session as the Persia fix)
THE PROBLEM: the ten baked minor towns (Nikomedia, Nicaea, Ankyra, Dorylaion, Sebasteia, Amorion, Caesarea,
Sardis, Tarsus, Attaleia) were CREAM TEXT ON A CREAM HALO — tone-on-tone, unreadable at any zoom; they
rendered as blank pills. (This was the recurring "fonts on the map" complaint.)
FIX: erased the pills (cream-gated masks per label box, dilate 7x7), NS-inpaint + gentle re-grain, and redrew
all ten at 22px DejaVuSerif-BoldItalic, ink (58,44,23), 1px cream halo @55%, anchored 14px right of each dot
ring, vertically centred on it. Bold-italic dark-brown = the "landmark, not clickable" voice, subordinate to
the 34px game-drawn hub labels. Dots untouched.
LESSONS (hard-won, three passes):
 1. RE-GRAIN NOISE must be LUMINANCE-correlated (one gaussian added to all three channels) and clamped
    (sigma ~3-4, measured from a known SMOOTH patch of the same map) — per-channel independent noise with
    std measured from a high-contrast ring (coastline/forest) sprays rainbow confetti. 
 2. DOT-RING protection discs must use MEASURED centres (cv2.HoughCircles on the backup, pick the darkest
    ring among candidates) — guessing from blob edges missed by ~20px, which BOTH deleted a ring (dilated
    cream fill took the thin ring with it) AND preserved chunks of old pill inside the misplaced disc.
 3. After ring-disc protection, sweep the annulus r9.5-16 for surviving cream-pill wisps and inpaint them
    (never touching r<9.5).
 4. Verify rings numerically: dark-px count in a 20x20 window at each measured centre, old vs new.
Original kept as Maps/_aleppo_relief762_lblbak.png.

## ARABIA (arabia762.png) — the overland pilgrim & incense network (v2.06.01, Fable)
Bounds [31.5,57.5,11.0,32.5], 1980x1637, square-degree equirect like all charts. BAKER IS SAVED:
Maps/bake_arabia.py (empirical elevation->colour ramp REGRESSED from egypt_redsea762 over the shared
rect — the trick for matching a lost baker's style). DEM = 3-tile GEBCO mosaic (egypt zip west of 48.9E,
Indian-Ocean zip east below 24.1N, whole-route zip east above 24.1N; recipe in the bake session).
Routes: least-grade A* (slope x45, alt>2400 penalty, mainland-component snap for coastal cities — Aden's
isthmus reads as sea at 0.02deg!) pinned through Hegra and Taif; saved as Maps/arabia_routes.json +
arabia_citypx.json. Routes are SVG chart legs (never baked). 7 new towns are SEA[] minor hubs wired as
gated (hajj:true) land edges — unlock with the maritime network. Relief is label-free per standard.
NOTE: egypt_redsea762 still carries illegible cream-on-cream "Jeddah"/"Mecca" pills — same disease as
the Aleppo chart; fix with the Aleppo recipe when convenient.
== ANATOLIA SETOUT GEOREF: 84 px/deg, x=(lon-23.803)*84, y=(42.295-lat)*84, 1402x999 ==

## 1271 MAPS — status (Fadak, big-build session)
- yuaneast1271.png BAKED: [95.5,122.5,23.5,45.5] 1980x1613, label-free relief. Baker SAVED: Maps/bake_yuaneast.py
  (ramp regressed from hexi762_summer; south-China green is a MOISTURE HEURISTIC — replace with Blue Marble
  greenness when available; Tibetan high ground reads as snow via ramp extrapolation, acceptable).
- Persia/Tarim/Hexi 1271 charts REUSE existing relief PNGs (geography; the 762 in filenames is cosmetic).
- UNBAKEABLE with on-hand DEM — GEBCO SHOPPING LIST for Kris (download at gebco.net, GeoTIFF).
  NOTE existing coverage: the whole-route band is lon 24.246-96.601E with NORTH EDGE 45.562N (all other
  tiles sit south/east of that). So only the true gaps are needed — mosaic with existing tiles at bake time:
    1) WEST GAP (Adriatic/Italy/west Greece):  lon 9E..24.3E,  lat 33N..47N     (Venice-Ragusa-Candia)
    2) NORTH STRIP (steppe above the band):    lon 27E..62E,   lat 45.5N..52N   (Tana/Sarai/portage/N Caspian)
    3) optional NORTH-EAST STRIP (Karakorum):  lon 95E..110E,  lat 45.5N..50N
  Drop the zips in Maps/ like the others; the bake_arabia/bake_yuaneast mosaic pattern stitches gap+band.

## 1271 REGION RELIEFS — batch bake (Fadak; baker SAVED Maps/bake_1271_regions.py)
armenia1271 [28.5,49.5,35,42.5] 1980x714 (Tabriz trunk; ramp from anatolia setout; Caspian SL split >48E);
khwarezm1271 [45,72,37,49.5] 1980x917 (Horde east; taklamakan ramp + grass; ARAL HAND-CARVED — GEBCO shows
its bed as dry land at +30..50m, the Caspian-trap's sibling; NE corner >45.56N,>62E has no DEM -> filled as
steppe, background only); persiasouth1271 [44,60,25.5,34.5] 1980x1114 (persiacorridor ramp);
bactria1271 [58,78,32,41] 1980x891 (persiacorridor ramp). WITH pontic1271 + yuaneast1271 + reused 762 relief
(taklamakan/hexi/steppe/persiacorridor/baghdadhub/aleppo/egypt), the 1271 world is fully mapped EXCEPT the
Venice/Adriatic map: still blocked on the WEST GAP tile (lon 9-24.3E, lat 33-47N) — last item on the list.
- ARAL SOLVED PROPERLY: elevation FLOOD-FILL, not a hand polygon — flood the connected basin component
  below the historical surface (+53m for the 13th-c Aral), then shift elevations so the surface = local sea
  level: exact shoreline AND true depth shading. bake_1271_regions.py carve param is now (seed_lon,seed_lat,
  surface_elev). Reusable for any endorheic lake (Caspian would work this way too with lvl=-28, though the
  SL-split already handles it). The rectangular seam NE of the Aral is the no-DEM corner, cured by the
  pending NE tile.
- FINAL TILES ARRIVED & BAKED: adriatic1271.png [11,27,34,46.5] 1980x1547 (Venice-Ragusa-Modon-Candia; anat
  ramp); khwarezm1271 REBAKED with the Kazakh strip — the fake NE-of-Aral corner is now real terrain, Aral
  flood-filled true. bake_1271_regions.py TILES list now includes both new tiles (ramp_from selects source
  tile by bounds, no longer by index). DEM COVERAGE IS NOW COMPLETE for the whole 762+1271+Amber-Road world:
  lon 8-123E, with the northern band to 52N from 27E east. No outstanding data requests.
- BELOW-SEA-LEVEL LAKE TRAP (cousin of the Caspian/Aral traps): any depression under 0m floods to the 0
  contour in a naive bake — the Dead Sea drowned its rift to Jericho on levant762 v1. Fix: carve now accepts
  a LIST of (seed,surface) tuples; Dead Sea -395 (ancient), Galilee -210. Give the ROUTER the same carves or
  it treats dry rift floor as water. Sweep any future map containing: Dead Sea, Galilee, Turfan depression
  (-154!), Qattara, Lut. NOTE: taklamakan762 contains Turfan — existing map, check someday.
  v2 LESSON (the full cure): carving the lake is NOT enough — dry land between lake level and 0 still paints
  as sea (painter rule d<=0). bake() now takes lift=(lonlo,lonhi,latlo,lathi): dry sub-0 cells in the box are
  remapped to 1..75m tones. Carves take an optional per-lake box, REQUIRED where two lakes share a below-0
  valley (Jordan rift chains Galilee to the Dead Sea at any workable threshold). Router needs the same
  carve+lift or dry rift floor reads as water.
- levant762 BIOME/RIVER PASS (map-only, no version bump): rivers hand-polylined from known geography with
  sine jitter (Euphrates+Tigris 4px, Nile 5px + Rosetta/Damietta 3px branches + delta polygon, Orontes 3,
  Jordan 2), drawn in SEAR shallow tone on land only; fertile green (bake grass color) = blurred river
  corridors + Med coastal strip (<55km, lon<37.3) + Ghouta gaussian at Damascus + weak north-steppe tint.
  TRUE DUNE SEAS paled/yellowed (blend to 238,220,155 @ ~0.5, flat+low cells only) + paired dark/light
  2px dimple stipple: Great Nafud fringe (map's SE), N-Sinai coastal belt, Egyptian Western Desert. All
  masks hand-polygoned from real geography - no landcover raster exists in the pipeline yet.
- LIFT-vs-OCEAN TRAP: the endorheic lift must EXCLUDE cells connected to real sea, or any coastal water
  inside the lift box becomes square land (Haifa Bay east of 35E got lifted on levant762 v3). Rule: flood
  ocean components from known sea seeds first; lift dry=(d<0)&box&~lakes&~ocean. Fixed in the levant render.
## WHY THE SUYAB RIVERS WERE WRONG (v2.07.20-21) - and the rule
FAILURE MODE: I hand-waypointed river courses every ~30-80km from memory and added sine jitter. That
produces "river-shaped decoration", not rivers: too straight between waypoints, wrong valleys entirely
where memory was thin (the Naryn ran outside its own structural valley), and it cannot know braids,
meanders or where a course hugs a range front. Meanwhile the ESTABLISHED steppe762 series already renders
this exact ground with REAL hydrography (Natural-Earth/GSHHS lines + lake polygons; ancientLakes whitelist
turns Soviet reservoirs to marsh; Blue-Marble-gated forest belts; calculated ag fields) via the _bake_ili
pipeline - see the READY-TO-USE SUYAB RECIPE above, which I failed to read before baking. THE RULE:
before baking ANY new region, grep MAP_NOTES for the region name AND for an overlapping existing series;
hydrography must come from data (or be reprojected from an existing correct raster), never from memory.
FIX APPLIED: suyab762 (all 4 seasons + base, now seasonal:true) is a LANCZOS REPROJECTION of steppe762
into [70,77.3,39.5,44.5] 1980x1356 (+light regrain, minor labels re-laid). Source transform calibrated
from steppe chart city dots by least squares: x=146.60*lon-9362.1, y=-147.36*lat+6590.8 (steppe762 true
bounds [63.86,77.37,37.51,44.73] - its stored geo, like aleppo's, is NOT its projection). East edge pulled
in from 79 to 77.3 (steppe762's limit): Issyk-Kul runs off-edge, Barskhan label dropped, Almaty (76.95)
kept. NOTE: _bake_ili.py + _cfg_steppe.json + steppe762_routes.json lived in a PRIOR session's outputs/
and are GONE - if the pipeline is needed again (e.g. a map east of 77.37), ask Kris whether a copy exists,
else rebuild from the recipe above. SCRIPTS THAT MATTER BELONG IN Maps/, NOT outputs/.
- SUYAB v4 (route doubling + circles-in-circles, Kris review): the SHIPPED steppe762*.png have the
  established routes, cream town dots and field mosaics BAKED IN (both steppe762 and steppe762_new).
  So (1) never re-draw rings/labels where the source already has dots - labels only, beside the baked dot;
  (2) vector chart legs must TRACE the baked geometry or you get two roads. TECHNIQUE - RASTER ROUTE
  TRACING: threshold the dash color (r<95,g<80,b<70), dilate 7px, then A* with cost 1 on-mask / 60 off-mask
  between the two city px - the path follows the dashes and bridges the gaps; smooth + reproject. Used for
  Talas-Suyab (the baked course DOES thread Merke+Navekat - wayside fracs .468/.862), the eastbound piedmont
  road (my DEM-A* had cut through the Chong-Kemin because slope-only cost can't price valley NARROWNESS -
  future DEM routing should add a ruggedness/exposure term: local relief range in a ~10km window), and both
  Akhsikath stubs (the Kashgar one properly via Osh).
## MASTER ROUTE REGISTRY (Kris ruling, 07-03): Maps/routes_master.json
One canonical version of every route, stored in LON/LAT (never chart px). Charts REPROJECT their slice from
it (lonlat -> chart px via that chart's true transform); never redraw or re-A* a route that already exists
here. When building/rebuilding any map: (1) pull every on-map leg from the registry; (2) any NEW leg you
route/trace gets written INTO the registry in lonlat before it goes on a chart. Seeded with the Anatolia
trunk, Levant set, and Talas road. Pairs with the coming MASTER RELIEF bake (one contiguous 1271 base,
sliced per chart) - together they end per-map re-derivation.
## THE 1271 MASTER RELIEF (Maps/bake_master.py + Maps/master1271/ + Maps/slice_master.py)
One contiguous base, [8,123]x[24,52] @147px/deg (16,905x4,116), baked as 8 butt-jointed strips (0.5-deg
overlap margins during bake keep hillshade seamless). All accumulated rules baked ONCE: endorheic carves
(Aral +53, Issyk-Kul +1607, Dead Sea -395, Galilee -205), rift/Turfan/Qattara lifts, Caspian regional sea
level -26.5, ocean = border-connected components, and the OXUS TIBET RULE: hypsometric brown plateau
blend >3000m, snow only >5300m - no more all-white Tibet. Ramp: persiacorridor-empirical + plateau/snow
overrides (v1; biome passes - greens, deserts, fields, rivers - accrete per-slice or as master layers when
hydrography data lands). SLICING: python3 slice_master.py W E S N OUTW OUTH out.png. Every future 1271
chart base comes from a slice; pair with routes_master.json for the legs. Amber-Road tile (8-42E,52-61N)
is in /tmp/geb/fc + registered in bake_1271_regions TILES for the future northern extension (master bounds
can grow: re-run bake_master with new MN and more strips).
- MASTER v2 - REAL HYDROGRAPHY + FORESTS (Kris fetched ne_10m_rivers_lake_centerlines + ne_10m_lakes):
  master_detail.py paints, per strip: forest belts (climato boxes x elevation x blotch; broadleaf 78,108,50
  <1400m, conifer 48,82,52 above), NATURAL EARTH lakes (featurecla 'Reservoir' -> MARSH per the ancientLakes
  doctrine, all else water w/ rim), NE river centerlines (width by scalerank), light regrain. Relief-only
  bases kept as strip_XX_relief.png for re-runs. NOTE the DEM-flow-accumulation fallback (master_flow.py,
  priority-flood + D8) is proven (Volga traced at 124k cells) - use it for rivers NE lacks (small oasis
  streams) or any future no-data region. OOM lesson: full-domain grids die (~<2GB); work in lon BLOCKS and
  separate processes per strip.
- MASTER v4 (Kris review round 2): (1) the "doubled north Caspian" was NOT a lake-paint bug - it was the
  CASPIAN DEPRESSION TRAP: dry sub-zero steppe north of 48.2N flooded by the default 0 sea level, with my
  regional -26.5 box's straight edge as the phantom shoreline. Cure: the regional level must cover the WHOLE
  depression - CASP box now (43,60,35.5,50.5). Add to the endorheic sweep list: any regional sea level's box
  must reach the depression's rim, never cut through it. (2) Ukraine forest-steppe: box replaced by a
  MOISTURE-GRADIENT treeline - weight = clip((lat-(43.2+(lon-8)*0.185))/3), the boundary climbing NE exactly
  as the real forest-steppe line does; no more box edges over featureless steppe. (3) dune/lush tint edges
  now levant-grade: noise-warp +-48px, blur 45; Nile delta / al-Thughur / Fergana / Batiha are POLYGONS with
  elevation gates, warped+feathered, not boxes.
- FARMLAND LAYER DESIGN (Kris 07-04): fields are ERA-SPECIFIC (settlements move/resize between 762 and
  1271) so they are NOT master layers - slice_master.py grows a fields pass: input settlements
  [(name,lon,lat,radius_km)], render the steppe762-style polygonal quilt (voronoi-ish patches, 2-3 earth
  tones + green) clipped to lowland/river proximity, feathered. Master stays era-neutral; each chart's
  slice call provides its era's towns. DEM inventory note: Transylvania sliver (24.3-27.2 x 45.3-47.5)
  fetched 07-04 - coverage for master [8,123]x[24,52] + Amber band now COMPLETE, no holes.
- SEA-LANE TRACING RULE (the Palembang straight-line bug): sea charts draw lanes in DASH BLUE (e.g.
  48,108,132 on easternseas), not the land dark/red - NEVER trace with an assumed ink color; histogram-
  detect the lane cluster from the raster at points along the pair first (union dark|red|detected-blue).
  And never crop-box a sea trace: lanes arc far outside endpoint boxes (Malacca) - full-frame, cost 700.
- LANE TINTS ARE PER-ROUTE, not per-chart (Socotra|Zanzibar lesson): sea charts draw secondary lanes in a
  FAINTER tint (indianocean: 128,168,184 vs primary 48,108,132). Detect the lane color per-pair by sampling
  along that pair's own corridor; corridor-mask the A* when bright junction lanes (Aden) offer a cheap wrong
  way round.
