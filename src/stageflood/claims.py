# Copyright (c) 2026 Martial Systems LLC
"""Fail closed if a report calls P a forecast or the HAND mask a FIRM."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from stageflood.errors import ClaimBanError

_BANS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "casualty_count",
        re.compile(r"\b(deaths?|fatalit(?:y|ies)|casualt(?:y|ies)|killed)\b", re.I),
    ),
    (
        "climate_attribution",
        re.compile(r"\b(cmip\d*|downscal(?:e|ed|ing)|gcm)\b", re.I),
    ),
    (
        "population_at_risk",
        re.compile(r"\b(lives|people|population)\s+at\s+risk\b", re.I),
    ),
    (
        "p_as_100yr",
        re.compile(r"\b100-year\s+exceedance\b", re.I),
    ),
    (
        "p_as_forecast",
        re.compile(
            r"\bP\(sfha\s*\|\s*hydro\)\s+is\s+(?:a\s+)?(?:flood\s+)?forecast\b|"
            r"\bcalibrated P predicts\b|"
            r"\btrain(?:ed|ing)? (?:a )?(?:flood )?model on FEMA\b",
            re.I,
        ),
    ),
    (
        "hand_as_firm",
        re.compile(r"\bHAND (?:mask|wet(?: area)?|bathtub) is (?:a |the )?FIRM\b", re.I),
    ),
    (
        "site_level_flood_risk",
        re.compile(r"\bsite-level flood risk\b", re.I),
    ),
)


def scan_text(text: str) -> list[str]:
    hits: list[str] = []
    blob = text or ""
    for name, pat in _BANS:
        if pat.search(blob):
            hits.append(name)
    return hits


def require_clean(text: str, *, source: str) -> None:
    hits = scan_text(text)
    if hits:
        raise ClaimBanError(f"{source}: banned claims {hits}")


def require_paths_clean(paths: Iterable[Path]) -> None:
    for path in paths:
        if path.is_file():
            require_clean(path.read_text(encoding="utf-8"), source=str(path))
