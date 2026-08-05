# SPEC — Nile / River Travel (for Fadak)

**Author:** Oxus (Opus), 8/04, Kris-greenlit. **Target:** `index.html`.

**Context:** River legs (`terr:'river'`/`'canal'`) run through `beginVoyage`, NOT `hajjGo`. They are *voyages* (boat), so none of the land-dash machinery (`checkHajjStops`, halts, `nextWellAhead`, hunting, desert events) touches them. The land-leg unification ("ONE LAND MODEL") is done — every 1271 land leg is a `kind:'hajj'` dash — but rivers are a separate travel mode. The Nile currently has: `Fustat|Qus` (river, flow Fustat, wind), `Fustat|Alexandria` (canal, flow Alexandria, wind). Speed already fixed (v3.3.66): downstream 210, upstream-with-wind 175 li/day; Cairo/Fustat food already 40-for-10s (v3.3.66).

All four features hang off ONE new hook: the caravan pulls to the bank at night. Build that first; the rest attach to it.

---

## 0. Shared hook: nightly river moorings (`checkRiverStops`, parallel to `checkHajjStops`)
- Give a river voyage a per-day tick (one mooring per `lk.d` days) that fires a stop check.
- Progress fraction `p = elapsed/lk.d`; track `pv`/`pPrev` like `checkHajjStops`.
- **Reuse `crossedUp(at)=pv<at && p>=at`** (added v3.3.65) so U-turns on the river don't scramble stops either. Persists across day-jumps (no silent-Wasit), doesn't phantom-fire on a frame flip.

## 1. River stops (Asyut, Akhmim, Minya, Qena)
- Significant town Qus->Cairo = **Asyut** (chief city of Upper Egypt). Add `rstop/rstopFrom/rstopAt` to river legs (mirror halt fields). `Fustat|Qus`: `rstop:'Asyut', rstopFrom:'Fustat', rstopAt:0.5`. Optional `rstop2` = Akhmim/Minya.
- On crossing, fire a new `evRiverStop(name)` (parallel to `evDesertHalt`) with river-town buttons: buy provisions (Egypt = cheap grain, 40/10s), rest N days, move on. NO fodder/fill-skins framing (you're on a boat).
- ALWAYS log reaching it ("The boat ties up at Asyut."), same policy as land halts (v3.3.63).
- Asyut T-dict: grain barges; the desert road west to Kharga/Dakhla oases and the Darb al-Arba'in slave road up from Darfur; the eastern hills behind. (Kris blesses final wording.)

## 2. River-camp bandit confrontation (amber-beach dynamic on the Nile)
Port the amber-road beach confrontation to a river mooring, gated to Egypt. Raiders (Bedouin / river brigands) approach as the party camps ashore. Three options:
1. **Pay them off** — silver by convoy wealth (reuse warband/toll formula).
2. **Stand and fight** — full combat (reuse resolver).
3. **Shove off hastily** (NEW) — lose the same cargo fraction you'd lose fleeing (reuse flee-loss), AND fight exactly ONE combat round as a rearguard back to the boat (cheaper than a full fight, injuries possible), then back on the water, mooring skipped.
Historically defensible: Ayyubid/early-Mamluk Upper Egypt had real Bedouin raiding and riverbank brigandage.

## 3. Hunting the Nile — bifurcated
Enable food actions on the Nile corridor (Alexandria<->Qus), split by intent:
- **Out of food** -> cultivated country: find a **village**, buy/beg grain (food-shortage -> village event). The valley is the granary; you don't starve here.
- **Go hunting** -> the **marshes**: reed-marsh waterfowl (ducks, geese, ibis), fish, maybe hippo/croc peril. A wetland hunt (`evNileMarshHunt`), distinct from desert/steppe hunts.
Flavour: "you put in where the reeds thicken" (hunt) vs "you put in at a fellahin village" (provisions).

## 4. Cairo food — DONE (v3.3.66)
Fustat gives 40 food for 10s. Give the §1 river-stop provisions button the same Egypt rate at Fustat/Asyut.

## 5. Cairo -> Giza pyramids (Admire destination)
Like Chang'an/Constantinople sub-destinations in "Admire," add a **"Cross the Nile to Giza"** button in Fustat's admire path. Describe the pyramids AS THEY STOOD IN 1271:
- Still largely sheathed in white Tura-limestone **casing** (the quarrying that stripped them for Cairo came mostly LATER; in 1271 the casing was substantially intact though robbing had begun) — smooth and blinding.
- The **Sphinx buried to the shoulders/neck** in sand, only the head clear.
- Arab wonder-lore framing (granaries of Joseph / tombs of antediluvian kings; Abd al-Latif al-Baghdadi had described them a generation or two before).
One-way flavour view, return to Cairo. Mirror the existing admire-sub-destination structure.

## 6. (Optional refactor) turnBack: reframe to the reverse leg
Current `turnBack` flips `dir` and complements `legKm` (legDist-x), keeping the A->B frame — forcing direction-conditional logic everywhere (`_hstart`, `1-haltAt`). The v3.3.65 `crossedUp` patched the well-stop symptom. Kris's note: swapping `from`/`to` was tried and "the marker teleported to its doorstep" (legKm read as covered-toward-the-OLD-destination). The clean version done right: on reverse, swap `dash.from`/`dash.to`, set `legKm` to the complement, `dir=+1`, AND rebase the marker/onward rendering to the new frame. Then every direction-conditional collapses to "measure from current `from`, dir always +1," and U-turns can never scramble a waypoint. Real refactor; do only if worth the tokens.

---

### Build order: 0 hook -> 1 stops -> 3 hunting -> 2 bandit camp -> 5 Giza -> 6 refactor (optional).

---

## ADDENDUM (Kris, 8/04) — hubs, river events, Nile beasts, pyramid sightings

### 1b. Which Nile cities warrant node/hub status? (Oxus recommendation)
- **No Nile city warrants a full HUB** (the Cairo/Alexandria/Aden tier that stocks ~everything) — Cairo (Fustat) and Alexandria already anchor Egypt.
- **Asyut = yes, a minor NODE** (its own small market, not a mere stop). It was the northern terminus of the **Darb al-Arba'in** ("Road of Forty Days"), the great caravan route up from Darfur/Sennar — so it's the place African goods surface: **slaves, ivory, ostrich feathers, gum arabic, tamarind**. Give it a node with a distinctive FORCE_CARRY of those (esp. slaves + ivory + a feathers/gum specialty). This makes it a real reason to stop, not just a well.
- **Akhmim = optional secondary node** — famous for **textiles** (Akhmim linen and figured tapestry-weave); a minor cloth/linen market.
- **Qena, Minya = river stops only** (Qena: the pottery town, the *qulal* porous water-jars; Minya: pass-through). Flavour, not markets.

### 7. General river events (any river/canal leg), seamanship-gated
Parallel to the terrain-keyed land event pools, add a river event pool fired on the §0 mooring/day tick. Gate odds by crew **seamanship** — party members with high `ss` and/or `salty:true` reduce the bad outcomes (mirror how a cartographer halves getting-lost odds).
- **Sandbar** — the boat grounds on a shoal; lose a day working her off. P(strand) and days lost both scale DOWN with total crew seamanship (e.g. `base * 0.6^(numSaltyOrHighSS)`, floored). A good boatman reads the channel.
- **Contrary wind / dead calm** — a day's delay (upstream especially; less likely with wind:true legs).
- **River toll / customs post** — a Nile tax station (the state taxed river traffic heavily); a small fee, or a bribe, or a search. Reuse the tollPost pattern.
- **Grain-fleet passing** — a state grain convoy or a Karimi flotilla overtakes you; a news/price tip (hook to the rumour/tavern-tip system). Pure flavour + info.

### 8. Nile "great beasts" — first-sighting events (once per game each)
Two events, each fires exactly ONCE per game, on a Nile leg, denoting the FIRST time the player sees the beast. Each calls `recordSeen('<id>')` and is added to `beastUniverse()`/`metaBeast()` so it counts toward "the great beasts of the world you have seen" (achievement at ~line 4838).
- **Crocodile** — `recordSeen('crocodile')`. "A log on the mudbank opens a yellow eye..." The Nile crocodile, sacred to old Egypt, still thick on the Upper Nile in 1271.
- **Hippopotamus** — `recordSeen('hippopotamus')`. "A vast grey back rolls up out of the shallows and yawns a cavern of teeth..." Hippos still ranged the Egyptian Nile then (extirpated only by the 19th c.).
- Guard each with a once-flag so it never repeats. Fire opportunistically on any Nile mooring/passage after the flag is unset. (Optional: a tiny peril chance from a provoked hippo — they killed more boatmen than crocodiles.)

### 9. Pyramids visible from the river — ledger log-lines (positional, log-only)
Beyond the city stops, the Nile between Cairo and Minya passes several pyramid fields **visible from the water**. Fire a one-time ledger log line (no stop) as the boat passes each, keyed to fraction on `Fustat|Qus` (use the `sight`-style once-per-crossing log, or per-position log-fires on the §0 tick). Suggested, north→south (fractions from Fustat/Cairo, approximate — Fadak to tune):
- **Giza** (~0.02): the three great pyramids of Giza on the west bank, still white with casing, blazing above the palm-line. (If §5 Giza admire is built, this is the from-the-river glimpse.)
- **Saqqara / Memphis** (~0.05): the Step Pyramid of Djoser and the ruin-fields of old Memphis behind the palms.
- **Dahshur** (~0.07): the **Bent Pyramid** and the Red Pyramid standing clear of the desert edge — the odd broken-angled one catches every traveller's eye (this is the one Kris kept spotting).
- **Meidum** (~0.14): the strange tower-stump of the "false pyramid" (Meidum), already collapsed to its three-stage core, alone at the desert's rim near the Faiyum mouth.
- (Optional) **Lahun / Hawara** (Faiyum, ~0.16): the mud-brick pyramids of the Middle Kingdom, melted to dark mounds.
Each a single evocative log line; they should feel like the surprise Kris had of "pyramids everywhere" on the drive Cairo→Minya.


---
## IMPLEMENTED (Fadak, v3.3.67, 8/05) - deltas from spec
- SS0/1: built as riverMoorTick in stepVoy; Asyut is a REAL minor-hub city splitting the leg (not
  rstop fields) - reuses all existing halt/econ/chart machinery. THRESHOLD crossings, not crossedUp
  (windowed = the silent-Wasit class of bug; Done-flags handle refires).
- SS9: pyramid sights PER-VOYAGE (Kris's ruling), not once.
- SS8: hippo attack built (Kris: yes). SS2: shove-off = rearguard flavor + loss, not a full combat round.
- SS3: out-of-food -> existing evLandFood; marsh-hunt as a distinct action NOT built (river stops
  offer grain; add if Kris asks). SS6: skipped per its own clause.
- Goods: feathers/gum/tamarind baked for all cities; Zanzibar feathers, tamarind across the Indias (Kris).
- Darb al-Arba'in: context road to Kharga + off-map (Kris: not travelable).
