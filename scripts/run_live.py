#!/usr/bin/env python3
# Copyright (c) 2026 Martial Systems LLC
"""Live Nora Stage 0-C against sibling rasters. Does not edit indiana_flood_completion."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO), str(REPO / "src")]

from stageflood.live import run_live


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "logs" / "nora_live"
    report = run_live(out)
    print(
        f"stage C n_stage_wet={report['n_stage_wet']} "
        f"n_drain={report['n_reach_comparable']} figure={report['figure']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
