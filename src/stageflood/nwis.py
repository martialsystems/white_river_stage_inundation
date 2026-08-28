# Copyright (c) 2026 Martial Systems LLC
"""USGS EXSA stage-discharge rating. Paint uses stage, not Q."""

from __future__ import annotations

from stageflood.config import GAGE_ID, NWIS_RATING_URL
from stageflood.errors import FetchError, RatingError
from stageflood.http import GetBytes, get_bytes as default_get_bytes
from stageflood.rating import RatingPoint


def _token_float(token: str) -> float:
    return float(token.strip().rstrip("*"))


def parse_exsa_rdb(text: str, *, site_no: str = GAGE_ID) -> tuple[RatingPoint, ...]:
    """Parse an NWIS EXSA RDB (tab-separated INDEP/SHIFT/DEP)."""
    if site_no and site_no not in text:
        raise RatingError(f"EXSA text does not name site {site_no}")
    header_seen = False
    skip_types = True
    points: list[RatingPoint] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if not header_seen:
            cols = [c.strip().upper() for c in line.split("\t")]
            if len(cols) == 1:
                cols = line.upper().split()
            if cols and cols[0] == "INDEP":
                header_seen = True
            continue
        if skip_types:
            skip_types = False
            packed = line.replace("\t", "").replace(" ", "")
            if any(ch.isalpha() for ch in packed):
                continue
        parts = line.split()
        if len(parts) < 3:
            continue
        try:
            stage = _token_float(parts[0])
            q = _token_float(parts[2])
        except ValueError:
            continue
        points.append((stage, q))
    if not header_seen:
        raise RatingError("EXSA rating is missing the INDEP header")
    if not points:
        raise RatingError("EXSA rating has no stage-discharge points")
    return tuple(points)


def rating_url(site_no: str = GAGE_ID) -> str:
    return NWIS_RATING_URL.format(site_no=site_no)


def fetch_exsa_rating(
    *,
    site_no: str = GAGE_ID,
    get_bytes: GetBytes | None = None,
) -> tuple[RatingPoint, ...]:
    getter = get_bytes or default_get_bytes
    url = rating_url(site_no)
    try:
        raw = getter(url)
    except FetchError:
        raise
    except Exception as exc:
        raise FetchError(f"EXSA fetch failed: {url}: {exc}") from exc
    if not raw:
        raise RatingError("EXSA rating download was empty")
    text = raw.decode("utf-8", errors="replace") if isinstance(raw, (bytes, bytearray)) else str(raw)
    return parse_exsa_rdb(text, site_no=site_no)
