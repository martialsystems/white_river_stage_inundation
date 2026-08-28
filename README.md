# White River stage inundation (Nora)

One reach. One gage. USGS **03351000** White River near Nora, IN, at NWS flood stage **11 ft**. Cells that drain to that White River window are wet when sibling HAND is below `Δ = WSE − h_channel`. The interview figure has three layers on that reach only: FEMA SFHA, calibrated `P(sfha | hydro)` at t = 0.75 (a map-completion layer), and the stage-driven wet mask.

Sibling `indiana_flood_completion` stays frozen. This tree does not recompute HAND, does not train on FEMA, and does not paint the whole HUC.

| Layer | Meaning |
|-------|---------|
| FEMA SFHA | mapped floodway ∪ SFHA on the reach |
| Calibrated P | `P(sfha \| hydro)` ≥ 0.75, map-completion |
| Stage wet | HAND < Δ at 03351000, drain-to-reach only |

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src:. python3 scripts/run_fixture.py logs/stage0_fixture
.venv/bin/python -m pytest tests -q
```

Live sibling sha check (needs `~/indiana_flood_completion` rasters on disk, gitignored there):

```bash
PYTHONPATH=src:. python3 -c "from stageflood.pipeline import check_live_sibling; print(check_live_sibling())"
```

## GraphForge

Pin: `stageforge/`. Three refuse laws: sibling template sha before paint, `h_channel` before the wet mask, `P(sfha | hydro)` is a map layer, and the HAND wet mask is not a FIRM. Verify-before-done is the finish gate.

## Legal

Copyright (c) 2026 Martial Systems LLC. MIT. See [LICENSE](LICENSE).
