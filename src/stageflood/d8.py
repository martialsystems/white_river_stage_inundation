# Copyright (c) 2026 Martial Systems LLC
"""Windowed D8 on a sibling DEM crop. Does not recompute HAND."""

from __future__ import annotations

from heapq import heappop, heappush

import numpy as np

from stageflood.config import HYDRO_FILL_EPSILON_M, TEMPLATE_RES_M
from stageflood.errors import GateError
from stageflood.reach import D8_OFFSETS, FLOWDIR_NODATA

_SQRT2 = float(np.sqrt(2.0))
D8_WEIGHTS: tuple[float, ...] = (1.0, _SQRT2, 1.0, _SQRT2, 1.0, _SQRT2, 1.0, _SQRT2)
FLOWDIR_OUTLET = np.int8(-2)


def burn_dem(
    dem: np.ndarray,
    burn_mask: np.ndarray,
    *,
    depth_m: float,
    valid: np.ndarray,
) -> np.ndarray:
    out = dem.astype(np.float64, copy=True)
    out[burn_mask & valid] = out[burn_mask & valid] - float(depth_m)
    return out


def _flood_seeds(valid: np.ndarray, extra: np.ndarray | None) -> np.ndarray:
    """Valid cells on the array rim or adjacent to nodata, plus extra (streams)."""
    h, w = valid.shape
    inv = ~valid
    seeds = np.zeros((h, w), dtype=bool)
    seeds[0, :] |= valid[0, :]
    seeds[-1, :] |= valid[-1, :]
    seeds[:, 0] |= valid[:, 0]
    seeds[:, -1] |= valid[:, -1]
    for di, dj in D8_OFFSETS:
        ti = slice(max(0, -di), h - max(0, di))
        tj = slice(max(0, -dj), w - max(0, dj))
        si = slice(max(0, di), h + min(0, di))
        sj = slice(max(0, dj), w + min(0, dj))
        seeds[ti, tj] |= valid[ti, tj] & inv[si, sj]
    if extra is not None:
        seeds |= extra & valid
    return seeds


def priority_flood_fill(
    dem: np.ndarray,
    valid: np.ndarray,
    *,
    seed_mask: np.ndarray | None = None,
    epsilon: float = HYDRO_FILL_EPSILON_M,
) -> np.ndarray:
    """Fill depressions. Stream seeds stay at burned elevation."""
    h, w = dem.shape
    filled = dem.astype(np.float64, copy=True)
    visited = np.zeros((h, w), dtype=bool)
    visited[~valid] = True
    seeds = _flood_seeds(valid, seed_mask)
    heap: list[tuple[float, int, int]] = []
    ctr = 0
    ys, xs = np.where(seeds)
    for i, j in zip(ys.tolist(), xs.tolist()):
        heappush(heap, (float(filled[i, j]), ctr, i * w + j))
        ctr += 1
        visited[i, j] = True
    while heap:
        z, _, idx = heappop(heap)
        i, j = divmod(idx, w)
        for di, dj in D8_OFFSETS:
            ni = i + di
            nj = j + dj
            if ni < 0 or nj < 0 or ni >= h or nj >= w or visited[ni, nj]:
                continue
            visited[ni, nj] = True
            nz = float(filled[ni, nj])
            if nz < z + epsilon:
                filled[ni, nj] = z + epsilon
            heappush(heap, (float(filled[ni, nj]), ctr, ni * w + nj))
            ctr += 1
    return filled


def d8_flowdir(
    filled: np.ndarray,
    valid: np.ndarray,
    cellsize: float = TEMPLATE_RES_M,
) -> np.ndarray:
    """Steepest-descent D8. Outlets (no downhill neighbor) are FLOWDIR_OUTLET."""
    if cellsize <= 0:
        raise GateError("cellsize must be > 0")
    h, w = filled.shape
    best_drop = np.full((h, w), -np.inf, dtype=np.float64)
    best_dir = np.full((h, w), int(FLOWDIR_OUTLET), dtype=np.int8)
    for k, ((di, dj), weight) in enumerate(zip(D8_OFFSETS, D8_WEIGHTS)):
        dist = weight * cellsize
        ti = slice(max(0, -di), h - max(0, di))
        tj = slice(max(0, -dj), w - max(0, dj))
        si = slice(max(0, di), h + min(0, di))
        sj = slice(max(0, dj), w + min(0, dj))
        drop = (filled[ti, tj] - filled[si, sj]) / dist
        ok = valid[ti, tj] & valid[si, sj] & (drop > best_drop[ti, tj])
        best_drop[ti, tj] = np.where(ok, drop, best_drop[ti, tj])
        best_dir[ti, tj] = np.where(ok, np.int8(k), best_dir[ti, tj])
    best_dir = np.where(best_drop > 0, best_dir, FLOWDIR_OUTLET)
    best_dir = np.where(valid, best_dir, FLOWDIR_NODATA)
    return best_dir.astype(np.int8, copy=False)


def flowdir_from_dem(
    dem: np.ndarray,
    stream: np.ndarray,
    valid: np.ndarray,
    *,
    burn_m: float,
    cellsize: float = TEMPLATE_RES_M,
) -> np.ndarray:
    burned = burn_dem(dem, stream, depth_m=burn_m, valid=valid)
    filled = priority_flood_fill(burned, valid, seed_mask=stream)
    return d8_flowdir(filled, valid, cellsize)
