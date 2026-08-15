# Silk Road — Map/Route Backlog Spec (for Fadak, the fable desk)

Handoff from Oxus. Nine open items, all map- or route-generation. Game is at **v3.4.22**.
Everything below is grounded in the current code; file paths and function names are exact.

---

## 0. Working agreements (read first)

**Repo layout**
- Live game: `Claude Enclosure/Silk Road/index.html` (single file; the `<script>` is the game).
- Maps + data: `Claude Enclosure/Silk Road/Maps/`.
- Git mirror / sync target: `GitHub/Silk-Road/` (copy `index.html`, `Maps/setout_charts_1271.json`,
  `Maps/routes_master.json`, and any changed `Maps/*.jpg|png` here when done).

**Editing constraint (important):** `index.html` and `Maps/` are Edit/Write-protected in the agent
harness. Edit them through `mcp__workspace__bash` with Python string replacement, always asserting a
unique match, e.g.:
```python
s=open('index.html',encoding='utf-8').read()
assert s.count(a)==1, s.count(a)
s=s.replace(a,b); open('index.html','w',encoding='utf-8').write(s)
```
Watch the em-dash: some strings store it as the literal `—`, others as the 6-char escape `—`.
Grep/inspect the exact bytes before matching.

**Verify every JS edit:** extract the largest `<script>` block and `node --check` it:
```bash
python3 -c "import re;s=open('index.html',encoding='utf-8').read();open('/tmp/g.js','w').write(max(re.findall(r'<script>(.*?)</script>',s,re.S),key=len))"
node --check /tmp/g.js
```
Then bump `VERSION`/`BUILD` (top of the script) and copy files to `GitHub/Silk-Road/`. Log in `CHANGELOG.md`.

**Headless harness** (for logic checks) — stub `document`/`window`/`localStorage`/`fetch`/timers,
set `global.location.href='?start=Bukhara'`, `eval(js+tail)`, then poke `S`, `city()`, etc. `render=function(){}`.
See any of the `/tmp/*.js` patterns Oxus used.

---

## 1. The map systems (shared reference)

### 1a. Set-out charts (the departure screen)
- Data lives in **two places, keep both in sync**: standalone `Maps/setout_charts_1271.json` AND embedded
  in `index.html` as the `CHARTS` object (search `"so_<slug>":`). Update both.
- Schema per entry `so_<slug>`:
  ```
  { img:"Maps/so1271_<slug>.jpg", era:"1271", vbw, vbh, geo:[W,E,S0,N], title,
    cities:{ Name:{x,y,r,ldx,ldy, faint?, ruin?, nodot?} },   // px coords
    legs:{ "A|B":"x,y x,y ..." },       // drawn as LAND road (dashed brown)
    sealegs:{ "A|B":"x,y x,y ..." },    // drawn as SEA lane (blue)
    stubs:[ {pts:"x,y ...", hint:"..."} ],  // grey stumps toward off-chart destinations
    open:[cityNames], seasonal:bool }
  ```
- **Projection** (lon/lat → chart pixels), used everywhere:
  `x=(lon-W)/(E-W)*vbw ; y=(N-lat)/(N-S0)*vbh`. Leg strings are pixel polylines in this space.
- Base images: `Maps/so1271_<slug>.jpg` plus `_spring/_summer/_autumn/_winter`. `img` points at the summer default.
- The chart shown for a city is chosen by `chartForCity(name)` (matches `open[]` + era).
- **HALT_LL** (index.html ~7623): `{ 'Landmark':[lon,lat] }` — drawn as faint italic dots on ANY chart whose
  `geo` contains them (renderChart builds these each frame). Use for named waypoints (e.g. Qarshi, Uchkuduk).

### 1b. The generator
- `Maps/gen_setout_1271.py`. Run from the Maps dir with `PYTHONPATH="$PWD" python3 gen_setout_1271.py ...`.
- `--rerender so_<name>`: re-renders the 5 base jpgs while keeping the hand-tuned JSON. Forces `gebco_relief`.
- Base relief: `slice_master`+`relief_boost` for the master-covered box (W 8–123°E, S 24–52°N, from
  `Maps/master1271/` strips); `gebco_relief` (arid ramp) elsewhere or when forced. Then `anachronize`
  (ephemeral water / 1271 corrections) and `fields_multi` (seasonal cultivation quilt).
- Per-town bbox = the town + its edge-destinations + route geometries, padded 10%.

### 1c. **Quality reference — use this as the template for any new arid/mountain base**
`Maps/rebake_urgench_aridity.py` (Oxus, the Urgench redo). It supersedes the old polygon washes:
- **Köppen effective aridity** `AI = P / (20·T)` from `bio12` (precip) + `bio1` (temp) — this, not raw
  mm/yr, is what separates hot desert (Karakum AI 0.40) from cool steppe (AI 1.10 at the same rainfall).
  Ramp: sand → takyr → dry steppe → steppe → piedmont → forest by AI.
- **keep-master weight**: preserves the master slice's mountains (forest + rock) where elevation is high
  or the master pixel is snow-white / forest-green; only the arid lowland/steppe is recoloured.
- **GEBCO hillshade** (true DEM, not master luminance — that resurrected old polygon edges as haloes)
  for crisp relief; **synthesised snowcaps** above ~3000–3900 m; rivers from Natural Earth with an
  oasis-green valley ribbon. DEM sampled anti-aliased (INTER_AREA), blurs minimal so terrain stays crisp
  while only the desert↔steppe COLOUR is soft.

### 1d. Data locations (all under `Maps/`)
- DEM: `gebco_local/*.tif` (filenames encode bounds `..._n<N>_s<S>_w<W>_e<E>_...`), also `dem_west/`,
  `dem_tarim/`, `dem_tian/`. **Note:** local GEBCO tops out at 45.56°N in the Turan area — north of that
  fills flat; plan bboxes accordingly (or patch north sea/coast from the master).
- Climate: `Climate Information/wc2.1_10m_bio_12.tif` (annual precip), `wc2.1_10m_bio_1.tif` (mean temp).
  (Case-sensitive: the folder is `Climate Information`, not the lowercase in some old code comments.)
- Rivers: `ne_10m_rivers_lake_centerlines.geojson` (filter `scalerank<=8`).
- Master relief: `master1271/` strips, bounds [8,123,24,52], plus `master_amber/` for ≥52°N.

### 1e. Travel / voyage maps (the moving map DURING a leg) — different from set-out charts
- `VOYMAPS` (index.html ~8882): keyed `[from,to].sort().join('|')` →
  `{ img, w, h, from, pts:"x,y ...", cities?:[{n,x,y}] }`. `pts` is the traced route in that image's px.
- `voyMapEntry()` (index.html ~8887): if no explicit `VOYMAPS[key]`, it FALLS BACK to a set-out `CHART`
  that shares the same `img` (borrowing its cities), else derives one. So a sea leg with neither an explicit
  voymap nor a chart on a framing image shows **no** moving map.
- `IMG_GEO` (gen_setout_1271.py): base sea images → geo bbox, used to back-project traced sealegs to lon/lat.
- **Land** legs use the set-out chart (chartForCity) as their moving map — so a land leg with no chart
  covering both endpoints has no moving map.
- `routes_master.json`: canonical leg geometries in lon/lat, keys `'A|B'` sorted. `route_1271.py` is the
  DEM least-cost path generator (endpoints, optional waypoints, resolution) — the tool for terrain routing.

---

## 2. The nine items

Each: **Symptom · Goal · Approach · Files · Acceptance.**

### #55 — Herat-road fork set-out map (NEW)
- **Symptom:** the Herat-road fork (a halt on the `Balkh|Samarkand` leg at `haltAt 0.26`, event
  `oxusFork('herat')` / `evDesertHalt('the Herat-road fork')`) shows no map.
- **Goal:** at the fork, show a set-out-style map with the fork point, Herat, Balkh, the main routes
  (Balkh↔Samarkand, Balkh↔Herat), and the **proposed shortcut drawn with shorter dashes**.
- **Approach:** either add a dedicated small chart (e.g. `so_heratfork`) or reuse `so_balkh`'s frame
  (Balkh 66.9,36.76; Herat 62.2,34.35; Samarkand 66.97,39.65). Add the fork point via HALT_LL or a chart
  city. Wire the fork event to open the chart (pattern: `chartForCity` / `openChart`). The "shorter dashes"
  need a per-leg dash style — add a `dash:'short'` flag on the shortcut leg and honour it in the chart SVG
  leg renderer (grep the renderChart leg-drawing that emits `stroke-dasharray`).
- **Files:** index.html (`oxusFork`, evDesertHalt, renderChart leg dash style, chart registry),
  `setout_charts_1271.json`, a base jpg (gen_setout or crop of `so_balkh`).
- **Acceptance:** standing at the fork opens a map showing Balkh/Herat/Samarkand + the fork, both roads
  drawn, and the shortcut in visibly shorter dashes.

### #56 — Balkh↔Kabul terrain reroute (ghost stub already removed)
- **Symptom:** `Balkh|Kabul` looks too straight on `so_balkh` (not routed around the Hindu Kush). (The ghost
  Balkh→Kabul stub on `so_kabul` is already gone.)
- **Goal:** reroute to follow the passes with finer waypoints, matching the actual travel geometry (which
  the user says already looks right).
- **Approach:** `route_1271.py` DEM least-cost Balkh (66.9,36.76)→Kabul (69.18,34.53) through the known
  pass sequence (Bamiyan corridor). Update `routes_master['Balkh|Kabul']`, then reproject into the px space
  of every chart that draws it: `so_balkh`, `so_kabul`, `so_lahore`.
- **Files:** route_1271.py, routes_master.json, the three charts (both JSON copies).
- **Acceptance:** the Balkh–Kabul line curves through the mountains, no straight chord; consistent across
  the three charts.

### #57 — Lahore↔Yarkand route smoothing / crossing
- **Symptom:** from Lahore, `Lahore|Yarkand` overlaps the old Yarkand stub and CROSSES the `Lop|Yarkand`
  (or `Aksu|Yarkand`) route on divergent trajectories — i.e. two routes cross yet keep diverging, which
  can't be right; it reads as routing decided in ~50-mile lumps.
- **Goal:** re-route `Lahore|Yarkand` at fine resolution through the real valleys (Karakoram/Kunlun pass
  chain), and make it not diverge-cross other Yarkand approaches — from any shared point there should be one
  best path onward.
- **Approach:** raise `route_1271.py` cost-grid resolution and/or feed explicit Karakoram waypoints; increase
  the chart leg resample count (the generator caps legs at ~44 pts — too coarse here). Remove the redundant
  Yarkand→Lahore stub if the full leg exists. Sanity-check that `Lahore|Yarkand` and `*|Yarkand` share tail
  geometry into Yarkand rather than crossing.
- **Files:** route_1271.py, routes_master.json, `so_lahore` (+ `so_kabul`) legs/stubs.
- **Acceptance:** on the Lahore chart the two routes converge cleanly into Yarkand with no divergent crossing;
  the Lahore–Yarkand line hugs valleys, making sharp turns where terrain dictates (not 50-mi straights).

### #58 — Gridded forests on the Lahore map
- **Symptom:** on `so_lahore`, the forests at the foot of the mountains are visibly laid out on a grid.
- **Goal:** organic forest, no grid.
- **Approach:** identify the source — likely `fields_multi`'s voronoi cultivation quilt landing where forest
  should be, or the forest classing in `gebco_relief` (`FOREST_SHARP`, the climate cell grid). If it's the
  quilt: increase seed jitter / break the cell grid / mask cultivation out of forest zones. If it's the
  forest layer: smooth the classing edge. Rebake `so_lahore` and verify at zoom.
- **Files:** `rebake_1271_fields.py` (fields_multi), `gen_setout_1271.py` (gebco_relief forest block), rebake.
- **Acceptance:** forest patches read naturally at 1:1; no repeating grid.

### #59 — Populate India + Delhi↔Chittagong travel map (NEW map)
- **Symptom:** India charts look empty (few settlements → reads like empty steppe); no moving map exists for
  the `Chittagong|Delhi` leg (terr `marsh`, a land route).
- **Goal:** (a) add more settlements — on-route ones as real nodes/halts, off-route ones as faint decorative
  dots — so India reads as densely settled; (b) bake a travel map for Delhi→Chittagong down the Gangetic plain.
- **Approach:** (a) add HALT_LL landmarks / faint chart-city markers for 1271 Indian towns (candidates:
  Multan, Ajmer, Kannauj, Kara, Awadh, Varanasi/Banaras, Pataliputra/Patna, Gaur–Lakhnauti, Ujjain,
  Devagiri, Anhilwara/Patan — several already exist in HALT_LL). Add faint dots to `so_lahore`, a `so_delhi`
  if present, and `so_chittagong`. (b) Delhi→Chittagong is LAND → its moving map is a set-out chart covering
  both endpoints; bake a base framing Delhi (77.2,28.6)→Ganges→Bengal→Chittagong (91.8,22.3) with the route,
  and make a chart `open` for that leg (so chartForCity returns it during travel).
- **Files:** index.html (city/HALT_LL/chart-city defs), gen_setout (new base), routes_master, chart JSON.
- **Acceptance:** the India charts show many towns; travelling Delhi→Chittagong shows a moving map with the
  route and named towns along the Ganges.

### #60 — Puttalam↔Kollam transit map must include Puttalam
- **Symptom:** the moving map for the Kollam↔Puttalam sea leg doesn't frame Puttalam.
- **Goal:** frame both Kollam (76.6,8.9) and Puttalam (79.83,8.03) with the traced route.
- **Approach:** add an explicit `VOYMAPS['Kollam|Puttalam']` on a base image that frames S. India + Ceylon
  (crop/adapt an existing eastern-seas tile, or bake a small one), with the traced route (routes_master has
  `Kollam|Puttalam`, 8 pts → back-project to the image px via its geo). This overrides the current fallback
  that's cutting Puttalam off.
- **Files:** VOYMAPS (index.html), a framing base image, routes_master.
- **Acceptance:** sailing Kollam→Puttalam shows both ports on the moving map with the route between.

### #62 — Aydhab↔Aylah transit map (NEW)
- **Symptom:** the `Aydhab|Aylah` Red Sea leg shows no moving map (no `VOYMAPS` entry, no framing chart).
- **Goal:** a Red Sea travel map — Aylah (35.0,29.53) at the head of the gulf down to Aydhab (36.49,22.33),
  route down the sea.
- **Approach:** add `VOYMAPS['Aydhab|Aylah']`. Needs a Red Sea base image framing the whole gulf+N Red Sea
  (check the Arabian/Egypt bakes for a reusable tile; else bake one via gen_setout/aridity for that bbox).
  Trace the coastal route down the Red Sea (there's `routes_master` geometry for the Red Sea legs to reuse).
  Note the leg is fast southbound / a 21-day beat northbound (windEasy Aydhab) — the map is direction-agnostic.
- **Files:** VOYMAPS (index.html), a Red Sea base image, routes_master.
- **Acceptance:** the leg shows a moving Red Sea map with Aylah, Aydhab, and the route.

### #63 — Aylah set-out rebake (Dead Sea level + Damascus/Aydhab in frame + routes)
- **Symptom:** the Aylah set-out map fills the Dead Sea "to the brim" (wrong level), and the Aylah→Damascus
  overland route isn't drawn.
- **Goal:** rebake with a correct (low) Dead Sea, an expanded frame that includes Damascus (36.31,33.51) and
  Aydhab (36.49,22.33), and all routes drawn (Aylah↔Damascus land, Aylah↔Qulzum land, Aylah↔Aydhab sea).
- **Approach:** the brim-full Dead Sea is the `lakeclip`/`anachronize` path in `gebco_relief` (there is a
  "Dead-Sea/rift declamp" hook — make sure it's applied here). Expand the Aylah bbox, rebake the arid base
  (use the §1c aridity template for the desert), draw the three routes. Full set-out rebake.
- **Files:** gen_setout_1271.py (Aylah config / bbox), rebake, chart JSON, routes_master.
- **Acceptance:** Dead Sea at plausible level; Damascus + Aydhab on-frame; the three routes drawn.

### #71 — Kaesong↔Khanbaliq travel map (NEW)
- **Symptom:** no moving map for the Kaesong→Khanbaliq land leg.
- **Goal:** a travel map: Kaesong (126.55,37.97) → Liaodong/Liaoyang (123.17,41.27) → Khanbaliq (~116.4,39.9).
- **Approach:** LAND leg → moving map = a set-out chart covering both endpoints. Bake a base over NE China +
  Korea (there is a `yuaneast1271` tile — check its bbox for reuse) framing Kaesong→Liaoyang→Khanbaliq with
  the route and named towns; make a chart `open` for the leg so chartForCity serves it during travel.
- **Files:** gen_setout (NE-China config), routes_master, chart JSON, index.html chart registry.
- **Acceptance:** travelling Kaesong→Khanbaliq shows a moving map with the route and Liaoyang/Khanbaliq marked.

---

## 3. Definition of done (every item)
1. Overlay the leg polylines on the baked jpg to eyeball geometry (Oxus's pattern: parse the chart block,
   `PIL` draw each `legs`/`sealegs` polyline + city dots, save a `_check.png`, view it).
2. `node --check` after any index.html edit; keep both JSON copies (standalone + embedded) in sync.
3. Bump `VERSION`/`BUILD`; copy changed files to `GitHub/Silk-Road/`; append a `CHANGELOG.md` entry.

## 4. Gotchas Oxus hit
- Embedded chart JSON uses `"key": "value"` with a space after the colon in some entries — match on the
  unique **value** string, not the key, when replacing a leg poly.
- Multiple charts contain a `Balkh|Kabul` / `Otrar|Urgench` etc. — the same leg key recurs across charts;
  scope replacements by the unique poly value.
- `so_urgench` geo is [49.27,70.04,38.36,48.46]; `so_kollam` [50.95,114.87,-1.32,29.68]; `so_zaiton`
  [106.99,122.44,10.45,32.05] — sanity-check any new projection against a known city's existing px.
- Reference bakes already done this cycle: `so_urgench` (aridity redo), `so_kollam` (added Dhofar/Puttalam
  routes + Cambay), `so_zaiton` (Kinsay→sea, Guangzhou route), `so_kabul` (stub removed). Mirror their style.
