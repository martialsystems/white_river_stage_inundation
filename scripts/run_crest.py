#!/usr/bin/env python3
# Copyright (c) 2026 Martial Systems LLC
"""August 2026 crest PNG. Same window as v1. Does not rewrite three_wet.png."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO), str(REPO / "src")]

from stageflood.live import run_crest_figure


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "logs" / "nora_live"
    report = run_crest_figure(out)
    print(
        f"crest n_stage_wet={report['n_wet']} (v1 {report['n_v1_wet']}) "
        f"Δ={report['delta_m']:.2f} m figure={report['figure']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
