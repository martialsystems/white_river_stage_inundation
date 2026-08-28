# Copyright (c) 2026 Martial Systems LLC
"""Injectable GET for NWIS and NHD."""

from __future__ import annotations

import json
import time
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from stageflood.config import USER_AGENT
from stageflood.errors import FetchError

GetBytes = Callable[[str], bytes]
GetJson = Callable[[str], dict[str, Any]]


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, HTTPError):
        return int(getattr(exc, "code", 0) or 0) >= 500
    return isinstance(exc, (URLError, TimeoutError, ConnectionResetError, ConnectionError))


def get_bytes(url: str, *, timeout: int = 90, attempts: int = 6) -> bytes:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    last: BaseException | None = None
    for i in range(attempts):
        try:
            with urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except (HTTPError, URLError, TimeoutError, ConnectionResetError, ConnectionError) as exc:
            last = exc
            if not _is_retryable(exc) or i == attempts - 1:
                raise FetchError(f"GET failed: {url}: {exc}") from exc
            time.sleep(min(2 ** i, 16))
    raise FetchError(f"GET failed: {url}: {last}") from last


def get_text(url: str, *, timeout: int = 90) -> str:
    raw = get_bytes(url, timeout=timeout)
    return raw.decode("utf-8", errors="replace")


def get_json(url: str, *, timeout: int = 90) -> dict[str, Any]:
    raw = get_bytes(url, timeout=timeout)
    try:
        doc = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FetchError(f"not JSON: {url}") from exc
    if not isinstance(doc, dict):
        raise FetchError(f"JSON object required: {url}")
    return doc
