"""Generates a clean, print-ready PDF from a filled form template.

Renders official-style output laid out from the DSL (reliable + controllable),
with a confidence-tier legend and a provenance appendix so every value is
traceable on paper too. Uses reportlab (pure-Python, no system deps).
"""
from __future__ import annotations

import io
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

_TIER_COLOR = {
    "green": colors.HexColor("#1B873F"),
    "amber": colors.HexColor("#B26A00"),
    "red": colors.HexColor("#C62828"),
}


def render_form_pdf(
    title: str,
    subtitle: str,
    filled_fields: list[dict[str, Any]],
    checklist: list[dict[str, Any]],
    output_meta: dict[str, Any],
    lang: str = "en",
) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, topMargin=18 * mm, bottomMargin=16 * mm,
        leftMargin=18 * mm, rightMargin=18 * mm, title=title,
    )
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Heading1"], fontSize=16, spaceAfter=2)
    sub = ParagraphStyle("sub", parent=styles["Normal"], fontSize=9, textColor=colors.grey)
    label_st = ParagraphStyle("lbl", parent=styles["Normal"], fontSize=9, textColor=colors.HexColor("#444"))
    value_st = ParagraphStyle("val", parent=styles["Normal"], fontSize=11, leading=14)
    small = ParagraphStyle("small", parent=styles["Normal"], fontSize=8, textColor=colors.grey)
    section = ParagraphStyle("sec", parent=styles["Heading2"], fontSize=12, spaceBefore=10, spaceAfter=4)

    story: list[Any] = []
    story.append(Paragraph(title, h1))
    story.append(Paragraph(subtitle, sub))
    story.append(Paragraph("Prepared with Sahayak · This is a draft for your confirmation — not auto-submitted.", small))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#DDD")))
    story.append(Spacer(1, 8))

    # Filled fields table with tier dot.
    rows = [[Paragraph("<b>Field</b>", label_st), Paragraph("<b>Value</b>", label_st), Paragraph("<b>Source</b>", small)]]
    for f in filled_fields:
        tier = f.get("tier", "amber")
        dot = f'<font color="{_TIER_COLOR.get(tier, colors.black).hexval()}">●</font> '
        rows.append([
            Paragraph(f.get("label", f.get("key", "")), label_st),
            Paragraph(dot + str(f.get("value", "") if f.get("value") not in (None, "") else "—"), value_st),
            Paragraph(f.get("source", ""), small),
        ])
    table = Table(rows, colWidths=[55 * mm, 75 * mm, 44 * mm])
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.HexColor("#CCC")),
        ("LINEBELOW", (0, 1), (-1, -1), 0.3, colors.HexColor("#EEE")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(table)

    # Legend.
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        '<font color="#1B873F">●</font> verified &nbsp;&nbsp; '
        '<font color="#B26A00">●</font> please check &nbsp;&nbsp; '
        '<font color="#C62828">●</font> you told us this', small))

    # Checklist.
    if checklist:
        story.append(Paragraph("Documents to attach", section))
        for c in checklist:
            line = f"☐ {c['instruction']} — {c['label']}"
            if c.get("note"):
                line += f" <font color='#888'>({c['note']})</font>"
            story.append(Paragraph(line, value_st))

    # Where to submit + fair price.
    story.append(Paragraph("Where to submit", section))
    story.append(Paragraph(output_meta.get("submit_to", ""), value_st))
    if output_meta.get("online_wall"):
        story.append(Spacer(1, 3))
        story.append(Paragraph("⚠ " + output_meta.get("online_wall_note", ""), small))
    fp = output_meta.get("fair_price", {})
    if fp:
        story.append(Spacer(1, 6))
        story.append(Paragraph(
            f"Official fee: ₹{fp.get('official_fee', 0)} &nbsp;·&nbsp; "
            f"Typical tout charge: ₹{fp.get('tout_price', 0)} &nbsp;·&nbsp; "
            f"<b>You save ₹{fp.get('you_save', 0)}</b>", small))

    doc.build(story)
    return buf.getvalue()
