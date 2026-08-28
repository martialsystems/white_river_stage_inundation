# White River stage inundation (Nora)

One reach. One gage. USGS **03351000** / NWS **NORI3** White River near Nora, IN, at NWS flood stage **11 ft**. Water-surface elevation is 710.51 + 11.0 = **721.51 ft NAVD88**. Cells that drain along D8 to that White River window are wet when sibling HAND is finite and below `Δ = WSE − h_channel`, with `h_channel` the sibling DEM at the White River cell nearest the gage (not gage zero). The interview figure has three layers on that reach only.

Sibling `indiana_flood_completion` stays frozen. This tree does not recompute HAND, does not train on FEMA, and does not paint the whole HUC.

| Layer | Meaning |
|-------|---------|
| FEMA SFHA | mapped floodway ∪ SFHA on the window |
| Calibrated P | `P(sfha \| hydro)` ≥ 0.75, sibling map-completion, not water at 11 ft |
| Stage wet | HAND inundation at NWS flood stage on drain-to-reach cells |

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src:. python3 scripts/run_fixture.py logs/stage0_fixture
PYTHONPATH=src:. python3 scripts/run_live.py logs/nora_live
.venv/bin/python -m pytest tests -q
```

Live sibling freeze (HAND, DEM, stream paint, P, zone, transform `479ac376…`):

```bash
PYTHONPATH=src:. python3 -c "from stageflood.pipeline import check_live_sibling; print(check_live_sibling())"
```

## GraphForge

Pin: `stageforge/`. Three refuse laws: sibling template sha before paint, `h_channel` before the wet mask, `P(sfha | hydro)` is a map layer, and the HAND wet mask is not a FIRM. Verify-before-done is the finish gate.

## Legal

Copyright (c) 2026 Martial Systems LLC. MIT. See [LICENSE](LICENSE).
