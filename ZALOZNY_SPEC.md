# SPEC — The Zalozny Route & Tmutarakan (for Fadak / Fable)

**Author:** Oxus · **For:** Fadak · **Status:** ready to implement · **Era:** 762 (primary); 1271 (optional, declined)

Sign in/out on the COPILOT STATUS BOARD as usual; edit `index.html` via the bash+Python `assert count==1` discipline; `node --check` the largest script; bump VERSION/BUILD; prepend CHANGELOG; sync `index.html` + `CHANGELOG.md` to both repos. Reference map: `Silk Road/Pictures/zalozny_route.jpg`.

## 1. Goal
Add the historically-documented **Zalozny route** as a route variant that branches at **Kiev** and bypasses the Dnieper rapids by going up the Samara, portaging the Vovcha->Kalmius watershed, down to the Sea of Azov, and by sea to **Tmutarakan** on the Kerch strait, then rejoining the Black-Sea coast for the Greek ports. It is **longer and portage-heavy** but avoids the seven rapids and the Pecheneg gauntlet — the sane choice when you have missed the June flood/convoy (see the seasonal rapids effect shipped in 3.4.120, `dnieperFlood()`).

## 2. Geography & waypoints (lon,lat WGS84, from the routed map)
| Point | lon,lat | Role |
|---|---|---|
| Kiev (`Kiev hillfort` 762 / `Kiev` 1271) | 30.52, 50.45 | fork point (existing node) |
| Samara mouth | 35.15, 48.50 | branch off the Dnieper; transition only |
| up the Samara -> Vovcha | 35.9->37.0, ~48.1 | river; transition only |
| **The Portage** (Vovcha->Kalmius watershed) | ~37.6, 48.0 | overland portage; transition only |
| down the Kalmius -> Azov shore | 37.55, 47.10 | river->sea transition only |
| **Tmutarakan** (Tamatarkha) | 36.72, 45.22 | **new node** (Taman side of the strait) |
| out the Kerch strait -> Black Sea | 36.4, 45.0 | rejoin the coast |

Samara is a left-bank tributary of the Dnieper; up the Samara, then up ITS tributary the Vovcha, a short overland portage crosses the Donets-ridge watershed to the Kalmius, which runs south to the Azov. So: Dnieper -> Samara -> Vovcha -> **portage** -> Kalmius -> Azov.

## 3. Settlements along the route — none of note
Open Pecheneg (762) / Cuman (1271) **nomad steppe**, willow-lined banks, no permanent towns. Intermediate points are **transition waypoints only** (river<->portage<->sea handoffs, like the Don->Volga `THE PORTAGE` dialogue and `Berezan camp`). Do **not** make them markets. The only settlements are the endpoints, Kiev and Tmutarakan; the middle is empty grass and nomads (see section 8).

## 4. New node: Tmutarakan
Add node + `CITY_LL['Tmutarakan']=[36.72,45.22]` + region membership (same bucket as Cherson/Soldaia for kit/news).

**762 (primary):** a real Khazar emporium; size like a minor hub comparable to **Cherson** (`hub:'minor', cash:160`):
```
{name:'Tmutarakan', terr:'settled', frac:.88, era:'762', hub:'minor', cash:170,
 desc:"Tamatarkha on the strait ... brick walls, a fine harbour, and every tongue of the inner sea in its lanes: Greeks, Khazars, Jews, Rus, Circassians; naphtha seeps in the hills the Romans pay silver for.",
 adm:"You take the measure of Tamatarkha."}
```
**1271 (optional):** declined **Matracha**, below Soldaia/Tana; `era:'1271', hub:'minor', cash:100`.

## 5. Size vs Soldaia and Tana (era-dependent)
- **762:** Tmutarakan (Tamatarkha) is near its stride — a walled merchant port comparable to Cherson. Soldaia (Sudak) has not yet risen (peak 12th-14th c.); Tana (Azak) barely exists yet. So in 762 Tmutarakan is the BIGGER of the three.
- **1271:** reversed — Soldaia and Tana are the great Golden-Horde/Italian hubs (full hub tier, frac ~.90, no cash cap); Tmutarakan has shrunk to little Matracha, well below both.
- **Implication:** put the Zalozny/Tmutarakan content primarily in the **762 era** (the monoxyla-in-June route is 9th-10th c.). Cherson-class minor hub in 762; a small declined node in 1271 if added at all.

## 6. Legs (branch at Kiev; rejoin at Cherson/Constantinople). era:'762'.
1. `Kiev hillfort` -> `the Samara portage` — `terr:'river'`, `flow:'the Samara portage'`, `d:~14`, `portage:true`. Covers Dnieper-down-to-Samara-mouth, up the Samara/Vovcha, the watershed portage. Model the two-beat portage on the Don->Volga dialogue (one beat leaving the Samara, one reaching the Kalmius).
2. `the Samara portage` -> `Tmutarakan` — `terr:'river'`->`coast`, `d:~7`.
3. `Tmutarakan` -> `Cherson` — `coast:true, terr:'med', d:~4`.
4. `Tmutarakan` -> `Constantinople` — `terr:'med', d:~9` (optional direct sea-road).

`the Samara portage` is a **silent camp waypoint** node (like `Berezan camp`), not a market.

**Tradeoff (design intent):** rapids road Kiev->Cherson ~7 days; Zalozny Kiev->Tmutarakan->Cherson ~25 days. Longer + portage drudgery, but no rapids and far less Pecheneg exposure.

## 7. The fork at Kiev
Leaving Kiev toward the Greeks, present a route choice (like the Tarim/Dzungaria forks):
- **"Run the rapids road (the way to the Greeks)"** -> existing Kiev->Berezan/Oleshye rapids leg. Fast; seven gates; Pecheneg ambush; now seasonal via `dnieperFlood()` (cheap/safe in the June flood-convoy, deadly/lonely off-season).
- **"Take the Zalozny — up the Samara, over to the Azov"** -> the new chain. Slow, portage-heavy, skips the rapids.

Lean the fork text on the season: if `dnieperFlood()` is low (missed the June gathering) the Zalozny is explicitly the sensible choice; in full flood the rapids road is the bold, faster play. This is the payoff that gives the seasonal effect teeth.

## 8. Nomad encounters on the steppe legs
On legs 1-2 reuse the warband/steppe machinery with the right people by era: **Pechenegs** (762), **Cumans/Polovtsy** (1271). The portage (boats out of the water, "the shore has eyes") is the natural ambush beat — mirror `evRapid`'s portage ambush and `evWarband`.

## 9. Monoxyla (the "xylophone dugouts") — optional, low priority
The game already models the Rus river craft with the Norse **faering** (light, portageable). The **monoxylon** (Slav single-log dugout, what Constantine's Rus gathered at Kiev) is near-identical mechanically. Recommendation: **skip a full new boat type**; optionally flavour the Dnieper/Zalozny craft as a *monoxylon* (cosmetic label, or a cheap starter dugout). If you do add one:
```
monoxylon: {n:'monoxylon', pl:'monoxyla', base:22, crewMin:2, crewFull:4, cargo:24, waters:1, buildDays:10, note:'a single-log Rus dugout - cheap, cranky, and carried over any portage'}
```
region-gated to the Rus rivers.

## 10. Verify & ship
- `node --check` the largest script after each edit.
- Confirm the fork appears only at Kiev in-era and the Zalozny legs date-gate correctly.
- Tmutarakan set-out chart can be baked later (Oxus, via the Pontic/Azov DEM + NE vectors used for `zalozny_route.jpg`); not required for first ship.
- Bump VERSION/BUILD, prepend CHANGELOG, sign the board, sync both repos.

## Sources
- Route from the Varangians to the Greeks / the monoxyla (Constantine Porphyrogenitus, De Administrando Imperio ch.9): https://en.wikipedia.org/wiki/Route_from_the_Varangians_to_the_Greeks
- Tmutarakan (Tamatarkha): https://en.wikipedia.org/wiki/Tmutarakan
- Vovcha (Samara tributary): https://en.wikipedia.org/wiki/Vovcha

---
## IMPLEMENTED (Fadak, v3.4.121, 8/15) - deltas from spec
- KRIS AMENDMENT (the one design change): Tmutarakan is a minor hub ONLY in 762 (Cherson-class,
  cash 170). In 1271 there is NO Matracha market node at all - instead 'Matracha' is a HALT on the
  Soldaia|Tana sea leg at the Kerch strait (haltAt 0.45 from Soldaia): you may take on provisions
  or recover from an Azov storm, but the trading and the seaworthy hulls are at Soldaia. Served by
  riverMoorTick, which now also runs on 'med' voyages that declare a halt (no-op for all others);
  evRiverStop gained a Matracha blurb pointing the trade back at Soldaia.
- SS6 legs: leg 1 carries no flow (down-Dnieper + up-Samara mixed; flat d:14 both ways, the
  Tana|Sarai precedent). Fork = the ordinary destination choice at Kiev, flavoured by
  dnieperSeasonNote(), whose two low-water branches now recommend the Zalozny by name (SS7's lean).
- SS8: portage beats mirror the Don->Volga two-beat dialogue; ambush ~20% at the boats-out beat via
  evWarband. warbandTribe gained a steppe bucket ('the Samara portage'/Tmutarakan/Berezan/Oleshye):
  Pecheneg horse-band in 762, Cuman in 1271 - this also fixes the rapids-road ambushes, which were
  naming Krivichi in Pecheneg country.
- SS9 monoxylon: skipped per spec's own recommendation (cosmetic only).
- SS10: set-out chart deferred to Oxus as specified. No camels on the Azov run (isAmberPlace).
