# Copyright (c) 2026 Martial Systems LLC

import hashlib
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("reportlab", reason="pip install -r requirements.txt")

from stageflood.claims import scan_text
from stageflood.config import LOCKED_V1_PNG_SHA256
from stageflood.errors import SiblingShaError

ROOT = Path(__file__).resolve().parents[1]
V1_PNG = ROOT / "logs" / "nora_live" / "three_wet.png"
BUILDER = ROOT / "scripts" / "build_interview_note.py"


def _builder():
    spec = importlib.util.spec_from_file_location("build_interview_note", BUILDER)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_v1_png_hash_locked() -> None:
    got = hashlib.sha256(V1_PNG.read_bytes()).hexdigest()
    assert got == LOCKED_V1_PNG_SHA256
    assert _builder().require_v1_png_frozen() == LOCKED_V1_PNG_SHA256


def test_interview_note_pdf(tmp_path: Path) -> None:
    pytest.importorskip("pypdf")
    from pypdf import PdfReader

    dest = tmp_path / "interview_note.pdf"
    before = V1_PNG.read_bytes()
    subprocess.run(
        [sys.executable, str(BUILDER), str(dest)],
        cwd=str(ROOT),
        check=True,
    )
    assert dest.is_file()
    assert V1_PNG.read_bytes() == before
    text = "\n".join(page.extract_text() or "" for page in PdfReader(str(dest)).pages)
    assert "21.18" in text
    assert "provisional" in text.lower()
    assert "leftover SFHA" in text
    assert "1.09" in text
    assert "4.19" in text
    assert "721.51" in text
    assert "731.69" in text
    assert "All rights reserved" not in text
    assert "MIT" in text
    assert scan_text(text) == []


def test_interview_note_refuses_v1_drift(tmp_path: Path) -> None:
    other = tmp_path / "three_wet.png"
    other.write_bytes(b"not-the-v1-figure")
    with pytest.raises(SiblingShaError):
        _builder().require_v1_png_frozen(other)
