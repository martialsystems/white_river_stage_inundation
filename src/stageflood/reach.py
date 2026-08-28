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
FLOWDIR_NODATA = np.int8(-1)


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
    for r in range(h):
        for c in range(w):
            if not ok[r, c]:
                continue
            d = int(fd[r, c])
            if d < 0 or d >= len(D8_OFFSETS):
                continue
            dr, dc = D8_OFFSETS[d]
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w and ok[rr, cc]:
                down[r * w + c] = rr * w + cc
    ptr = np.zeros(n + 1, dtype=np.int32)
    for i in range(n):
        j = int(down[i])
        if j >= 0:
            ptr[j + 1] += 1
    np.cumsum(ptr, out=ptr)
    adj = np.empty(int(ptr[-1]), dtype=np.int32)
    cursor = ptr[:-1].copy()
    for i in range(n):
        j = int(down[i])
        if j >= 0:
            adj[cursor[j]] = i
            cursor[j] += 1
    marked = np.zeros(n, dtype=bool)
    seeds = np.flatnonzero(stream.ravel() & ok.ravel())
    q: deque[int] = deque(int(i) for i in seeds)
    for i in seeds:
        marked[i] = True
    while q:
        i = q.popleft()
        for up in adj[ptr[i] : ptr[i + 1]]:
            if marked[up]:
                continue
            marked[up] = True
            q.append(int(up))
    return marked.reshape(h, w)
