# Methodology (locked 2026-08-27)

This file is the working contract. If README and this file disagree, this file wins.

Sibling `indiana_flood_completion` is frozen. Do not edit it from this tree. Do not recompute HAND. Do not start a second HUC, gSSURGO C2, citywide roads, or a model trained on FEMA.

## Object

Stage-driven wet area on **one White River reach** at **USGS 03351000** (Nora). Unit: 30 m cell. Formula: wet iff `HAND < Δ` and the cell drains to the reach, with `Δ = WSE − h_channel`.

`P(sfha | hydro)` is a comparison map layer. It is not a flood forecast and not the training target.

## Gage

| Field | Value |
|-------|-------|
| Site | 03351000 White River near Nora, IN |
| NWS | NORI3 |
| HUC-8 | 05120201 |
| Lon, lat | −86.1056, 39.9106 (82nd Street / Nora) |
| Datum | 710.51 ft NAVD88 |
| Primary stage | 11.0 ft (NWS flood stage) |
| NWS minor WSE | 721.51 ft NAVD88 (= 710.51 + 11.0) |
| Why Nora | NWIS publishes gage height and NAVD88 water-surface elevation |

Muncie 03347000 and Centerton 03354000 stay out of v1. Observed crest near 21 ft is a later figure, not a replacement for 11 ft.

## Reach

NHD White River flowline through the gage (gnis_name White River, including ftype 558 Artificial Path), ± 5 km along-stream, clipped to 05120201. A cell is on the reach if its D8 path hits a White River cell in that window. Euclidean distance to the gage is not a wet criterion. Tributaries are included only if they drain to that window, not if they are merely nearby. Log river-km (10 km pin: ± 5 km) and reach cell count.

## HAND and Δ

Sibling `data/interim/hand.tif` (metres, EPSG:5070, template sha256 `479ac37628bfd7e5d409f6108ae6ba1805acfd37ecdc7093785db06ac9ebec22`) is `z_cell − z_drained_stream` along D8. Stream cells have HAND = 0. HAND-nodata stays nodata.

Δ lives in NAVD88. At stage `h` (ft):

1. `WSE_ft = 710.51 + h` (NWS identity: 11.0 ft → 721.51 ft NAVD88), then metres.
2. `h_channel` is the sibling DEM elevation of the White River cell nearest the gage (metres, same grid that made HAND). It is not 710.51. Subtracting gage datum from WSE double-counts stage as inundation depth.
3. `Δ = WSE − h_channel`.
4. A cell is wet only if all of these hold: it drains along D8 to a White River cell inside the reach window; sibling HAND is finite; `HAND < Δ`.

The USGS EXSA rating places `h` on a published Q-stage curve and refuses a stage off the curve. Painting uses stage/WSE, not Q. Sibling flowdir was never written; D8 on the window is rebuilt from the sibling DEM plus HAND=0 stream paint and the White River raster. Those paths are not byte-identical to sibling Stage B. HAND values are not recomputed.

Live at 03351000: Δ = 1.09 m because 3DEP at the channel is 2.26 m above gage zero. On this 30 m DEM, NWS flood stage is 3.6 ft of water above the DEM surface. The other 7.4 ft of the 11 ft stage sits in the unresolved channel. The wet mask is cells below 721.51 ft WSE among drain-to-reach cells.

## Stages

| Stage | Job | Success |
|-------|-----|---------|
| 0 | Claims, sibling pointers, gage pin, fixture reach | Fixture green; live sha match when live rasters are present |
| A | Rating + 11 ft + `h_channel` | Stage on rating; `h_channel` locked; `Δ` finite |
| B | Paint `wet.tif` | HAND-nodata remains nodata; off-reach cells not wet |
| C | Three-layer table + figure | Claim scan clean; reach mask not HUC-wide |

Do not skip. B refuses missing `Δ`. C refuses a HUC-wide wet mask.

## Three layers

Captions (P cannot be read as stage):

- SFHA: mapped floodway ∪ SFHA on the window
- P ≥ 0.75: sibling map-completion, not water at 11 ft
- stage wet: HAND inundation at NWS flood stage

Overlap: counts and IoU on drain-to-reach cells only, plus SFHA-dry-at-stage and wet-on-unshaded-X. Live IoU SFHA vs stage wet is 0.73 on that strip. No PR-AUC. No retraining.

The three-panel figure prints Δ and the 3DEP-minus-datum offset so the 1.09 m water depth is read as the grid result.

## Claims

Banned in reports, README, and figure titles: 100-year exceedance, `P(sfha | hydro)` as a forecast, training a flood model on FEMA, HAND bathtub as a FIRM, site-level flood risk, casualty/climate/population-at-risk.

Allowed: stage-driven wet area at 03351000, HAND < Δ, mapped SFHA on this reach, calibrated P as a map layer.

## Imports

Read-only from `~/indiana_flood_completion/data/interim/`. `check_live_sibling()` hashes HAND, DEM, dist_stream, dist_flowline (stream paint; sibling has no flowdir.tif), `p_sfha_calibrated.tif`, `zone_class.tif`, and transform `479ac376…`. If any of those hashes move, this tree stops. Rasters stay gitignored in the sibling and are not copied into this git tree.

## Revisions

- 2026-08-28: Caption live Δ = 1.09 m and 3DEP +2.26 m on `three_wet.png`. Wet mask is cells below 721.51 ft WSE on drain-to-reach. IoU reported on drain-to-reach only. Window D8 not byte-identical to sibling Stage B.
- 2026-08-28: Lock NAVD88 identity WSE = 710.51 + 11.0 = 721.51 ft. `h_channel` is sibling DEM at the White River cell, not gage datum. 5 km mainstem window. Three captions so P is not water at 11 ft. Band hashes on HAND/DEM/stream paint/P/zone. Live run: White River ftype 558 only, rating 11.00 ft at 10245.31 cfs, Δ = 1.09 m, 1197 wet cells on 2604 drain-to-reach cells.
- 2026-08-27: Lock Nora reach, HAND < Δ, three-layer compare, GraphForge pin for sha / h_channel / claims.
