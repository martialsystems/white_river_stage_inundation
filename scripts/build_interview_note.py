#!/usr/bin/env python3
# Copyright (c) 2026 Martial Systems LLC
"""Interview note PDF: two frozen Nora figures, two Delta values. No third stage."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO), str(REPO / "src")]

from stageflood.claims import require_clean
from stageflood.compare import pair_fill_sentence
from stageflood.config import (
    CREST_DATE,
    CREST_STAGE_FT,
    GAGE_DATUM_FT_NAVD88,
    GAGE_ID,
    GAGE_NWS_ID,
    LOCKED_V1_PNG_SHA256,
    P_DEFINITION,
    PRIMARY_STAGE_FT,
)
from stageflood.errors import GateError, SiblingShaError

NOTE_DATE = "2026-08-28"
DEST_PDF = REPO / "docs" / "interview_note.pdf"
V1_PNG = REPO / "logs" / "nora_live" / "three_wet.png"
CREST_PNG = REPO / "logs" / "nora_live" / f"three_wet_crest_{CREST_DATE}.png"
V1_JSON = REPO / "logs" / "nora_live" / "stage_c_report.json"
V1_A_JSON = REPO / "logs" / "nora_live" / "stage_a_report.json"
CREST_JSON = REPO / "logs" / "nora_live" / f"crest_{CREST_DATE}_report.json"


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short=12", "HEAD"],
            cwd=str(REPO),
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_v1_png_frozen(path: Path = V1_PNG) -> str:
    if not path.is_file():
        raise GateError(f"v1 figure missing: {path}")
    got = _sha256_file(path)
    if got != LOCKED_V1_PNG_SHA256:
        raise SiblingShaError(f"v1 PNG {got} != locked {LOCKED_V1_PNG_SHA256}")
    return got


def _load(path: Path) -> dict:
    if not path.is_file():
        raise GateError(f"missing report {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _p(text: str, style, story: list) -> None:
    require_clean(text, source="interview_note")
    from reportlab.platypus import Paragraph

    story.append(Paragraph(text, style))


def _styles():
    from reportlab.lib.colors import HexColor
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet

    base = getSampleStyleSheet()
    ink = HexColor("#1b1f1a")
    muted = HexColor("#4a524c")
    return {
        "title": ParagraphStyle(
            "NTitle",
            parent=base["Title"],
            fontName="Times-Bold",
            fontSize=14,
            leading=18,
            textColor=ink,
            alignment=TA_LEFT,
            spaceAfter=6,
        ),
        "sub": ParagraphStyle(
            "NSub",
            parent=base["Normal"],
            fontName="Times-Italic",
            fontSize=10,
            leading=13,
            textColor=muted,
            spaceAfter=8,
        ),
        "h1": ParagraphStyle(
            "NH1",
            parent=base["Heading1"],
            fontName="Times-Bold",
            fontSize=11,
            leading=14,
            textColor=ink,
            spaceBefore=11,
            spaceAfter=5,
        ),
        "body": ParagraphStyle(
            "NBody",
            parent=base["Normal"],
            fontName="Times-Roman",
            fontSize=10,
            leading=13,
            textColor=ink,
            alignment=TA_JUSTIFY,
            spaceAfter=7,
        ),
        "cap": ParagraphStyle(
            "NCap",
            parent=base["Normal"],
            fontName="Times-Italic",
            fontSize=8.5,
            leading=11,
            textColor=muted,
            spaceBefore=3,
            spaceAfter=9,
        ),
        "cell": ParagraphStyle(
            "NCell",
            parent=base["Normal"],
            fontName="Times-Roman",
            fontSize=8,
            leading=10,
            textColor=ink,
            alignment=TA_LEFT,
        ),
        "rev": ParagraphStyle(
            "NRev",
            parent=base["Normal"],
            fontName="Times-Roman",
            fontSize=8,
            leading=10,
            textColor=muted,
            spaceAfter=10,
        ),
        "foot": ParagraphStyle(
            "NFoot",
            parent=base["Normal"],
            fontName="Times-Roman",
            fontSize=8,
            leading=10,
            textColor=muted,
            alignment=TA_CENTER,
        ),
    }


def _table(rows: list[list[str]], col_widths: list[float]):
    from reportlab.lib import colors
    from reportlab.platypus import Paragraph, Table, TableStyle

    styles = _styles()
    data = []
    for i, row in enumerate(rows):
        out = []
        for cell in row:
            st = styles["cell"]
            text = f"<b>{cell}</b>" if i == 0 else cell
            require_clean(cell, source="interview_table")
            out.append(Paragraph(text, st))
        data.append(out)
    grid = Table(data, colWidths=col_widths, repeatRows=1)
    grid.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c5d0c8")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e4ebe7")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return grid


def _png_block(path: Path, heading: str, caption: str, styles):
    from PIL import Image as PILImage
    from reportlab.lib.units import inch
    from reportlab.platypus import Image, KeepTogether, Paragraph

    if not path.is_file():
        raise GateError(f"missing figure {path}")
    require_clean(heading, source="interview_fig_heading")
    require_clean(caption, source="interview_fig_caption")
    with PILImage.open(path) as im:
        aspect = im.height / im.width
    width = 6.9 * inch
    img = Image(str(path), width=width, height=width * aspect)
    img.hAlign = "CENTER"
    return KeepTogether(
        [
            Paragraph(heading, styles["h1"]),
            img,
            Paragraph(caption, styles["cap"]),
        ]
    )


def _footer(canvas, doc) -> None:
    from reportlab.lib.pagesizes import letter

    canvas.saveState()
    canvas.setFont("Times-Roman", 8)
    canvas.setFillColorRGB(0.29, 0.33, 0.39)
    canvas.drawString(72, 36, "Copyright (c) 2026 Martial Systems LLC. MIT.")
    canvas.drawRightString(letter[0] - 72, 36, f"page {doc.page}")
    canvas.restoreState()


def build_pdf(*, dest: Path = DEST_PDF) -> Path:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Spacer

    v1_sha = require_v1_png_frozen()
    v1 = _load(V1_JSON)
    v1_a = _load(V1_A_JSON)
    crest = _load(CREST_JSON)
    delta_v1 = float(v1_a["delta_m"])
    if str(crest.get("v1_figure_sha256") or "") != LOCKED_V1_PNG_SHA256:
        raise SiblingShaError("crest report v1 hash does not match the locked PNG")
    if crest.get("hand_recomputed") or crest.get("window_recomputed"):
        raise GateError("crest report recomputed HAND or window")
    pair = pair_fill_sentence(baseline=v1, later=crest)
    require_clean(pair, source="interview_pair")
    styles = _styles()
    sha = _git_sha()
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    story: list = []

    _p("White River stage inundation (Nora): interview note", styles["title"], story)
    _p(
        f"USGS {GAGE_ID} / NWS {GAGE_NWS_ID}. One 5 km drain-to-reach window. "
        "Two water surfaces on one HAND grid.",
        styles["sub"],
        story,
    )
    _p(
        f"Revisions: {NOTE_DATE}: package the frozen pair (flood stage 11.00 ft and "
        f"crest {CREST_STAGE_FT:.2f} ft on {CREST_DATE}, NWS provisional). "
        f"Generated {generated}. Git {sha}. v1 PNG sha256 {v1_sha[:12]}.",
        styles["rev"],
        story,
    )

    _p("Result", styles["h1"], story)
    _p(
        "Flood stage is a tight bathtub (Delta = 1.09 m, 1197 wet of 2604 drain-to-reach). "
        f"At {CREST_STAGE_FT:.2f} ft (provisional), wet cells are 1876. "
        f"{pair} "
        "That is the crest figure's result. Zone X in the Nora window starts to light up "
        "at 21.18 ft, still under a 30 m HAND assumption. Not a new model.",
        styles["body"],
        story,
    )
    _p(
        f"WSE is gage zero plus stage in NAVD88: 710.51 + {PRIMARY_STAGE_FT:.1f} = 721.51 ft, "
        f"and 710.51 + {CREST_STAGE_FT:.2f} = 731.69 ft. "
        "h_channel is the sibling DEM at the White River cell (218.82 m), not gage zero. "
        "Paint uses stage and WSE, not discharge.",
        styles["body"],
        story,
    )
    _p(
        f"{P_DEFINITION} at t = 0.75 is sibling map-completion, not water at 11 ft and "
        "not water at 21.18 ft.",
        styles["body"],
        story,
    )

    _p("Table 1. Same window, two stages (drain-to-reach cells)", styles["h1"], story)
    story.append(
        _table(
            [
                ["Quantity", "Flood stage 11.00 ft", f"Crest {CREST_STAGE_FT:.2f} ft"],
                ["WSE (ft NAVD88)", "721.51", "731.69"],
                ["h_channel (m)", f"{float(crest['h_channel_m']):.2f}", f"{float(crest['h_channel_m']):.2f}"],
                ["Delta (m)", f"{delta_v1:.2f}", f"{float(crest['delta_m']):.2f}"],
                ["Wet cells", str(int(v1["n_stage_wet"])), str(int(crest["n_stage_wet"]))],
                ["Drain-to-reach", str(int(v1["n_reach_comparable"])), str(int(crest["n_reach_comparable"]))],
                ["SFHA dry at stage", str(int(v1["n_sfha_dry_at_stage"])), str(int(crest["n_sfha_dry_at_stage"]))],
                ["Unshaded X wet", str(int(v1["n_wet_unshaded_x"])), str(int(crest["n_wet_unshaded_x"]))],
                ["IoU SFHA vs wet", f"{float(v1['iou_sfha_wet']):.2f}", f"{float(crest['iou_sfha_wet']):.2f}"],
            ],
            [2.3 * inch, 2.3 * inch, 2.3 * inch],
        )
    )
    _p(
        "IoU is on drain-to-reach cells only. Datum is "
        f"{GAGE_DATUM_FT_NAVD88:.2f} ft NAVD88. Crest date {CREST_DATE}, NWS provisional.",
        styles["cap"],
        story,
    )

    story.append(Spacer(1, 6))
    story.append(
        _png_block(
            V1_PNG,
            "Figure 1. NWS flood stage 11.00 ft",
            "Cells below 721.51 ft WSE on the 5 km reach. Delta = 1.09 m "
            "(3.6 ft of water above the 30 m DEM). 3DEP at the channel is 2.26 m above gage zero.",
            styles,
        )
    )
    story.append(
        _png_block(
            CREST_PNG,
            f"Figure 2. August 2026 crest {CREST_STAGE_FT:.2f} ft ({CREST_DATE}, NWS provisional)",
            "Cells below 731.69 ft WSE on the same reach. Delta = 4.19 m "
            f"(13.8 ft above the DEM). {pair}",
            styles,
        )
    )

    _p("Limits", styles["h1"], story)
    _p(
        "A 30 m HAND model cannot place the unresolved 7.4 ft of stage onto the floodplain. "
        "Window D8 is rebuilt from DEM plus HAND=0 paint; it is not byte-identical to sibling "
        "Stage B. HAND values were not recomputed. Sibling indiana_flood_completion was not edited. "
        "No third Delta, no second gage, no HUC-wide paint.",
        styles["body"],
        story,
    )

    dest.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(dest),
        pagesize=letter,
        title="White River stage inundation (Nora): interview note",
        author="Martial Systems LLC",
        leftMargin=72,
        rightMargin=72,
        topMargin=64,
        bottomMargin=56,
    )
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return dest


def main() -> int:
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else DEST_PDF
    pdf = build_pdf(dest=dest)
    print(f"interview note {pdf}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
