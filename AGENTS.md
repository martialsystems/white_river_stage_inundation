# Agent notes: white_river_stage_inundation

Private GitHub. MIT on this snapshot. Geography is USGS 03351000 Nora on HUC-8 05120201. Sibling `~/indiana_flood_completion` is frozen. Do not edit it. Do not recompute HAND. Do not add a second HUC, gSSURGO C2, citywide roads, or a model trained on FEMA.

## Formula

WSE_ft = 710.51 + stage (NAVD88). `h_channel` is sibling DEM at the White River cell nearest the gage, not gage zero. Wet iff D8 drain-to-reach and finite HAND and `HAND < Δ`, `Δ = WSE − h_channel`. Live Δ = 1.09 m is the 3DEP offset result; caption it, do not treat it as a bug. Paint uses stage/WSE, not Q. `P(sfha | hydro)` is map-completion, not water at 11 ft. IoU is drain-to-reach only. v1 is 11 ft (`three_wet.png`). Crest 21.18 ft is a second PNG on the same window. Stop after those two files. Package: `docs/interview_note.pdf` (hash-locks v1 PNG).

## Stages

0, A, B, C. `stageforge.gate.require_stage` refuses skips. B refuses unlocked `h_channel`. C refuses a HUC-wide mask.

## Claims

Run `stageflood.claims.scan_text` on reports, README, and figure titles. Fail closed on 100-year exceedance, P as a forecast, HAND as a FIRM, site-level flood risk.

## Verify

`python3 ~/agent_laws_verify_before_done/vbd_gate.py check --app-root . --claim-done`

`vbd.runtime.json` runs `.venv/bin/python -m pytest`, `scripts/run_fixture.py`, and `stageforge/scripts/sanity_stageforge.py`. Do not use stock `/usr/bin/python3 -m pytest`: it has no rasterio and dies in collection.

## GraphForge

Pin is `stageforge/`. Engine checkout `~/graphforge`. No catalog/`surfaces.json` unless the operator asks.
