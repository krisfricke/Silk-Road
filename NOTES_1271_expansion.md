# The Silk Road — 1271 Expansion (Marco Polo) — parking notes

## Boat-route tuner values (Venice ↔ Candia / Mediterranean)
APPROVED by Kris for the Western/Mediterranean seas:
- repulsion (krep) = 0.1
- magnetism (katt) = 0.00
- boundary  (d_repel) = 0.22
- outer range (d_att) = 1.3

Tuner file: Maps/boat_route_tuner_venice.html
Builder:    outputs/build_venice_tuner.py
(The Eastern-Seas / 762 map uses 0.4 / 0.55 / 0.52 / 4.1.)

## Route method (use this, not manual drag)
Shortest navigable sea-path (A* "string") + mid-channel waypoints where a
strait must be forced, then perturb with magnetism/repulsion. See
outputs/build_kollam.py (perturb/route) and outputs/build_venice_tuner.py.

## Historical decisions to honor in the 1271 build
- Staging ports Venice -> Ragusa (Dubrovnik) -> Modon (Methoni) -> Candia
  are historically correct calls (Dalmatian-coast convoy route; Modon/Coron
  were Venetian bases "the two eyes of the Republic" from 1207).
- VESSEL: use a wide-bellied LATEEN-RIGGED ROUND SHIP (a "nave"), sail-driven
  — NOT the sleek oared war galley. (Merchant "great galleys" also existed for
  precious cargo, but the round ship reads right for a merchant and the period.)

## Network rulings (Kris + Fadak, planning round 2)
- Antioch: destroyed 1268 -> ruin-dot beside Ayas. Konya: minor, on a Constantinople-Sivas link. Erzurum keeps
  (junction of Trebizond + Sivas roads, Ilkhanid customs). Rey/Balkh/old Nishapur/Merv: RUINS-GET-A-VOICE rule —
  dialogue box, or a mention in the nearby hub's admire/tavern/desc. Nishapur re-flattened by the 1270 quake.
- Southern rim 1271: Khotan -> Charchan -> Lop -> Shazhou(Dunhuang); Miran is empty sand. Kamul=Hami. Karakorum
  kept as flavour spur via Etzina. NO Hajji-Tarkhan node: Sarai runs the Caspian sailing (to Abaskun -> Khorasan
  road), like Aleppo runs its coast.
- TANA-SARAI = up the DON (not Dnieper) to the great bend, VOLGA PORTAGE at the bend (~modern Volgograd), down
  the Volga. First river-portage-river transit; the mechanic prototypes the AMBER ROAD expansion
  (Vanern -> Gota alv -> Baltic -> Rus rivers & portages -> Miklagard). Parked data now in index.html as
  ERA1271_NORTH (Tana, Sarai, portage leg) beside ERA1271_WEST (Venice-Ragusa-[Modon]-Candia).
- Pontic chart routed (pontic_routes.json): Cpl-Trebizond/Cpl-Caffa/Trebizond-Caffa/Caffa-Tana sea legs, Don+PORTAGE+Volga river legs, Sarai-Mangyshlak Caspian sail. WIRING NOTE: Mangyshlak (the historical Urgench landing) supersedes Abaskun as the Caspian east-shore node in ERA1271_NET — swap the Sarai|Abaskun leg to Sarai|Mangyshlak + Mangyshlak|Urgench at wiring time. Cpl legs start at the Bosphorus mouth (the strait is sub-grid; polyline prepends the city dot).

## RATIFIED (Kris): location-aware travel rollout plan
- SR1271 legs launch WITH the location-aware stack: live marker (arc-length position = legKm/legDist along
  the leg polyline, camera or fixed view — see mockup_travel_marker.html), DEM-generated terrain-underfoot
  profiles (Maps/gen_terrain_profile.py) driving pace/water/hunting/event pools, and lon/lat-anchored POIs
  (converted to arc-fractions at wiring; retires hardcoded mid-leg ranges).
- Once proven in 1271, backport to the 762 main game.
- TRAVEL SCREEN LAYOUT: the walking-camels journeyScene STAYS (Oregon Trail heritage, non-negotiable);
  the moving map takes the schematic regionMap strip's slot above it. Both on one screen.
- Known v1 kinks to work out during 1271 rollout: gulf-corner sampling on coastal legs (sample router cells,
  not straight interpolation); minimum-span merge ~15km on terrain profiles; precipitation raster for the
  steppe/desert climate prior (optional download, GEBCO-pattern).
- PAMIR ROUTES, ruled: Badakhshan|Kashgar = the WAKHAN-SARIKOL road (Panj -> Wakhan corridor -> high Pamir ->
  Tashkurgan/Sarikol -> Gez -> Kashgar) — Polo's own crossing; the A*'d polyline already follows it. The ALAY
  VALLEY belongs to Samarkand|Kashgar: pin that leg via Osh + the Alay (Irkeshtam) at wiring, matching the 762
  Akhsikath|Kashgar corridor. Candidate dlg waypoint: Tashkurgan ("the Stone Tower" candidate — ties to the
  existing Kashgar admire text).
