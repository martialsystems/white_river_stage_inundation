# Copyright (c) 2026 Martial Systems LLC

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8")
LICENSE = (ROOT / "LICENSE").read_text(encoding="utf-8")


def test_license_mit_and_readme_lead() -> None:
    assert LICENSE.lstrip().startswith("MIT License")
    assert "All rights reserved" not in README
    assert "03351000" in README
    assert "HAND" in README
    assert "P(sfha | hydro)" in README
    assert "not water at 11 ft" in README
    assert "indiana_flood_completion" in README
    assert ".venv/bin/python -m pytest tests -q" in README
