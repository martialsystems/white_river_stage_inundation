# White River stage inundation (Nora)

One reach. One gage. USGS **03351000** / NWS **NORI3** White River near Nora, IN, at NWS flood stage **11 ft**. Water-surface elevation is 710.51 + 11.0 = **721.51 ft NAVD88**. Cells that drain along D8 to that White River window are wet when sibling HAND is finite and below `Δ = WSE − h_channel`, with `h_channel` the sibling DEM at the White River cell nearest the gage (not gage zero).

Live Δ is **1.09 m**: 3DEP at the channel sits 2.26 m above gage zero, so flood stage on this 30 m grid is 3.6 ft of water above the DEM. The wet mask is cells below a 721.51 ft water surface among drain-to-reach cells (1197 / 2604), not 11 ft of inundation. IoU vs SFHA is 0.73 on drain-to-reach cells only. v1 figure: `logs/nora_live/three_wet.png`.

A second PNG uses the same window, hashes, and `h_channel` at the NWS NORI3 **21.18 ft** crest of **2026-08-15** (provisional). WSE = 731.69 ft NAVD88. New Δ, new file `logs/nora_live/three_wet_crest_2026-08-15.png`. Extra 679 wet cells filled leftover SFHA (dry 369 to 50); unshaded X wet 38 to 338; IoU 0.73 to 0.76 on drain-to-reach. Same model. v1 stays frozen. This tree stops at those two figures.

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
PYTHONPATH=src:. python3 scripts/run_crest.py logs/nora_live
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
