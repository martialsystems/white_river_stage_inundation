#!/usr/bin/env python3
# Copyright (c) 2026 Martial Systems LLC
"""Fixture Stage 0-C. No NWIS. CI join."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO), str(REPO / "src")]

from stageflood.pipeline import run_fixture


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "logs" / "stage0_fixture"
    report = run_fixture(out)
    print(f"stage C n_stage_wet={report['n_stage_wet']} figure={report['figure']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
