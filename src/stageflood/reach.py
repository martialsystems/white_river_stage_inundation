# Copyright (c) 2026 Martial Systems LLC
"""Drain-to-reach: cells whose D8 path hits the White River window."""

from __future__ import annotations

from collections import deque

import numpy as np

from stageflood.errors import GateError

# D8: N, NE, E, SE, S, SW, W, NW
D8_OFFSETS: tuple[tuple[int, int], ...] = (
    (-1, 0),
    (-1, 1),
    (0, 1),
    (1, 1),
    (1, 0),
    (1, -1),
    (0, -1),
    (-1, -1),
)
_SQRT2 = float(np.sqrt(2.0))
D8_STEP_WEIGHTS: tuple[float, ...] = (1.0, _SQRT2, 1.0, _SQRT2, 1.0, _SQRT2, 1.0, _SQRT2)
FLOWDIR_NODATA = np.int8(-1)


def nearest_cell(mask: np.ndarray, row: int, col: int) -> tuple[int, int, float]:
    ys, xs = np.where(np.asarray(mask, dtype=bool))
    if ys.size == 0:
        raise GateError("mask is empty")
    d2 = (ys.astype(np.float64) - float(row)) ** 2 + (xs.astype(np.float64) - float(col)) ** 2
    k = int(np.argmin(d2))
    return int(ys[k]), int(xs[k]), float(np.sqrt(d2[k]))


def along_stream_mask(
    stream: np.ndarray,
    *,
    start: tuple[int, int],
    max_m: float,
    cellsize: float,
) -> np.ndarray:
    """8-connected BFS along True stream cells, clipped to max_m along-stream."""
    s = np.asarray(stream, dtype=bool)
    if cellsize <= 0:
        raise GateError("cellsize must be > 0")
    h, w = s.shape
    sr, sc = int(start[0]), int(start[1])
    if not (0 <= sr < h and 0 <= sc < w) or not s[sr, sc]:
        raise GateError("along-stream start is not a stream cell")
    dist = np.full((h, w), np.inf, dtype=np.float64)
    dist[sr, sc] = 0.0
    q: deque[tuple[int, int]] = deque([(sr, sc)])
    while q:
        r, c = q.popleft()
        base = dist[r, c]
        for (dr, dc), wt in zip(D8_OFFSETS, D8_STEP_WEIGHTS):
            rr, cc = r + dr, c + dc
            if not (0 <= rr < h and 0 <= cc < w) or not s[rr, cc]:
                continue
            nd = base + wt * float(cellsize)
            if nd <= float(max_m) + 1e-9 and nd + 1e-9 < dist[rr, cc]:
                dist[rr, cc] = nd
                q.append((rr, cc))
    out = np.isfinite(dist)
    if not out.any():
        raise GateError("along-stream mask is empty")
    return out


def drain_to_reach(
    flowdir: np.ndarray,
    reach_stream: np.ndarray,
    valid: np.ndarray,
) -> np.ndarray:
    """True where downhill D8 hits a reach stream cell (including the stream)."""
    fd = np.asarray(flowdir)
    stream = np.asarray(reach_stream, dtype=bool)
    ok = np.asarray(valid, dtype=bool)
    if fd.shape != stream.shape or fd.shape != ok.shape:
        raise GateError("flowdir, reach_stream, and valid shapes differ")
    if not (stream & ok).any():
        raise GateError("reach stream is empty")
    h, w = fd.shape
    n = h * w
    down = np.full(n, -1, dtype=np.int32)
    for k, (di, dj) in enumerate(D8_OFFSETS):
        sel = (fd == k) & ok
        ys, xs = np.where(sel)
        if ys.size == 0:
            continue
        ni = ys + di
        nj = xs + dj
        inside = (ni >= 0) & (nj >= 0) & (ni < h) & (nj < w)
        if not inside.any():
            continue
        yi, xi, nni, nnj = ys[inside], xs[inside], ni[inside], nj[inside]
        dest_ok = ok[nni, nnj]
        down[yi[dest_ok] * w + xi[dest_ok]] = nni[dest_ok] * w + nnj[dest_ok]
    ptr = np.zeros(n + 1, dtype=np.int32)
    valid_down = down >= 0
    np.add.at(ptr, down[valid_down] + 1, 1)
    np.cumsum(ptr, out=ptr)
    adj = np.empty(int(ptr[-1]), dtype=np.int32)
    cursor = ptr[:-1].copy()
    for i in np.flatnonzero(valid_down):
        d = int(down[i])
        adj[cursor[d]] = i
        cursor[d] += 1
    marked = np.zeros(n, dtype=bool)
    seeds = np.flatnonzero(stream.ravel() & ok.ravel())
    q = deque(int(i) for i in seeds)
    marked[seeds] = True
    while q:
        i = q.popleft()
        for up in adj[ptr[i] : ptr[i + 1]]:
            if marked[up]:
                continue
            marked[up] = True
            q.append(int(up))
    return marked.reshape(h, w)
