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
| HUC-8 | 05120201 |
| Lon, lat | −86.1055, 39.9106 |
| Datum | 710.51 ft NAVD88 |
| Primary stage | 11.0 ft (NWS flood stage) |
| Why Nora | NWIS publishes gage height and NAVD88 water-surface elevation |

Muncie 03347000 and Centerton 03354000 stay out of v1.

## Reach

NHD White River flowline through the gage, ± 5 km along-stream, clipped to 05120201. A cell is on the reach if its D8 path hits a stream cell in that window. Bounding boxes are drawing aids. Tributaries with a different water surface stay dry at Nora's Δ.

## HAND and Δ

Sibling `data/interim/hand.tif` (metres, EPSG:5070, template sha256 `479ac37628bfd7e5d409f6108ae6ba1805acfd37ecdc7093785db06ac9ebec22`) is `z_cell − z_drained_stream` along D8. Stream cells have HAND = 0. HAND-nodata stays nodata.

At stage `h` (ft):

1. `WSE` is NWIS NAVD88 water-surface elevation, or `datum_ft + h`, converted to metres.
2. `h_channel` is the DEM elevation of the HAND stream cell that drains the gage (metres, same datum).
3. `Δ = WSE − h_channel`.
4. Wet iff `HAND < Δ` on drain-to-reach cells.

The USGS rating places `h` on a published Q-stage curve and refuses a stage off the curve. Painting uses stage/WSE, not Q.

## Stages

| Stage | Job | Success |
|-------|-----|---------|
| 0 | Claims, sibling pointers, gage pin, fixture reach | Fixture green; live sha match when live rasters are present |
| A | Rating + 11 ft + `h_channel` | Stage on rating; `h_channel` locked; `Δ` finite |
| B | Paint `wet.tif` | HAND-nodata remains nodata; off-reach cells not wet |
| C | Three-layer table + figure | Claim scan clean; reach mask not HUC-wide |

Do not skip. B refuses missing `Δ`. C refuses a HUC-wide wet mask.

## Three layers

FEMA SFHA (zone floodway ∪ sfha), calibrated P ≥ 0.75, stage wet. Overlap: counts and IoU, plus SFHA-dry-at-stage and wet-on-unshaded-X. No PR-AUC. No retraining.

## Claims

Banned in reports, README, and figure titles: 100-year exceedance, `P(sfha | hydro)` as a forecast, training a flood model on FEMA, HAND bathtub as a FIRM, site-level flood risk, casualty/climate/population-at-risk.

Allowed: stage-driven wet area at 03351000, HAND < Δ, mapped SFHA on this reach, calibrated P as a map layer.

## Imports

Read-only from `~/indiana_flood_completion/data/interim/`: `hand.tif`, `dem.tif`, `zone_class.tif`, `p_sfha_calibrated.tif`, `stack_manifest.json`. Refuse if `template_transform_sha256` drifts. Rasters stay gitignored in the sibling and are not copied into this git tree.

## Revisions

- 2026-08-27: Lock Nora reach, HAND < Δ, three-layer compare, GraphForge pin for sha / h_channel / claims.
