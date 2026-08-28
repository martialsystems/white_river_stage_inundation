# Agent notes: white_river_stage_inundation

Private GitHub. MIT on this snapshot. Geography is USGS 03351000 Nora on HUC-8 05120201. Sibling `~/indiana_flood_completion` is frozen. Do not edit it. Do not recompute HAND. Do not add a second HUC, gSSURGO C2, citywide roads, or a model trained on FEMA.

## Formula

Wet iff `HAND < Δ` and drain-to-reach, `Δ = WSE − h_channel`. Paint uses stage/WSE, not Q. `P(sfha | hydro)` is a map layer.

## Stages

0, A, B, C. `stageforge.gate.require_stage` refuses skips. B refuses unlocked `h_channel`. C refuses a HUC-wide mask.

## Claims

Run `stageflood.claims.scan_text` on reports, README, and figure titles. Fail closed on 100-year exceedance, P as a forecast, HAND as a FIRM, site-level flood risk.

## Verify

`python3 ~/agent_laws_verify_before_done/vbd_gate.py check --app-root . --claim-done`

`vbd.runtime.json` runs pytest, `scripts/run_fixture.py`, and `stageforge/scripts/sanity_stageforge.py`.

## GraphForge

Pin is `stageforge/`. Engine checkout `~/graphforge`. No catalog/`surfaces.json` unless the operator asks.
