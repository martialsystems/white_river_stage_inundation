# Copyright (c) 2026 Martial Systems LLC
"""USGS rating: place a stage on the curve. Paint uses stage, not Q."""

from __future__ import annotations

from typing import Sequence

from stageflood.errors import RatingError

RatingPoint = tuple[float, float]  # (stage_ft, q_cfs)


def require_stage_on_rating(
    stage_ft: float,
    rating: Sequence[RatingPoint],
    *,
    tol_ft: float = 0.05,
) -> RatingPoint:
    """Return the nearest rating point. Refuse if stage is off the published range."""
    if not rating:
        raise RatingError("rating is empty")
    stages = [float(p[0]) for p in rating]
    lo, hi = min(stages), max(stages)
    h = float(stage_ft)
    if h < lo - tol_ft or h > hi + tol_ft:
        raise RatingError(f"stage {h} ft is off the rating [{lo}, {hi}] ft")
    nearest = min(rating, key=lambda p: abs(float(p[0]) - h))
    return (float(nearest[0]), float(nearest[1]))


def fixture_rating() -> tuple[RatingPoint, ...]:
    """Two-point-plus curve that includes NWS flood stage 11 ft."""
    return (
        (2.0, 200.0),
        (6.0, 2500.0),
        (11.0, 12000.0),
        (16.0, 35000.0),
    )
