#!/usr/bin/env python3
"""Convert Korean markdown to PDF using reportlab with AppleGothic font."""

import re
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Preformatted, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER

# Register Korean font
FONT_PATH = "/System/Library/Fonts/Supplemental/AppleGothic.ttf"
pdfmetrics.registerFont(TTFont("AppleGothic", FONT_PATH))

INPUT_MD = "/Users/surplus96/projects/bio-simulagent/PM-MCP/adoring-swartz/docs/기획서_투자대시보드.md"
OUTPUT_PDF = "/Users/surplus96/projects/bio-simulagent/PM-MCP/adoring-swartz/docs/기획서_투자대시보드.pdf"


def build_styles():
    styles = getSampleStyleSheet()
    base = {"fontName": "AppleGothic"}

    styles.add(ParagraphStyle("KTitle", parent=styles["Title"], **base, fontSize=22, spaceAfter=12))
    styles.add(ParagraphStyle("KH1", parent=styles["Heading1"], **base, fontSize=18, spaceBefore=16, spaceAfter=8, textColor=HexColor("#1a1a2e")))
    styles.add(ParagraphStyle("KH2", parent=styles["Heading2"], **base, fontSize=15, spaceBefore=14, spaceAfter=6, textColor=HexColor("#16213e")))
    styles.add(ParagraphStyle("KH3", parent=styles["Heading3"], **base, fontSize=13, spaceBefore=10, spaceAfter=4, textColor=HexColor("#0f3460")))
    styles.add(ParagraphStyle("KH4", parent=styles["Heading4"], **base, fontSize=11, spaceBefore=8, spaceAfter=4))
    styles.add(ParagraphStyle("KBody", parent=styles["Normal"], **base, fontSize=9.5, leading=14, spaceAfter=4))
    styles.add(ParagraphStyle("KCode", fontName="AppleGothic", fontSize=7.5, leading=10, leftIndent=12,
                               backColor=HexColor("#f8f9fa"), borderColor=HexColor("#e0e0e0"),
                               borderWidth=0.5, borderPadding=6, spaceAfter=6, spaceBefore=4))
    styles.add(ParagraphStyle("KBullet", parent=styles["Normal"], **base, fontSize=9.5, leading=14,
                               leftIndent=20, bulletIndent=10, spaceAfter=2))
    styles.add(ParagraphStyle("KBlockquote", parent=styles["Normal"], **base, fontSize=9.5, leading=14,
                               leftIndent=20, textColor=HexColor("#555555"), spaceAfter=6))
    return styles


def escape_xml(text):
    """Escape XML special chars for reportlab Paragraph."""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text


def inline_format(text):
    """Convert inline markdown (bold, code) to reportlab XML tags."""
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # Inline code
    text = re.sub(r'`(.+?)`', r'<font face="Courier" size="8" color="#c7254e">\1</font>', text)
    return text


def parse_table(lines):
    """Parse markdown table lines into list of rows."""
    rows = []
    for line in lines:
        line = line.strip()
        if line.startswith("|") and not re.match(r'^\|[\s\-:|]+\|$', line):
            cells = [c.strip() for c in line.split("|")[1:-1]]
            rows.append(cells)
    return rows


def md_to_flowables(md_text, styles):
    """Convert markdown text to reportlab flowables."""
    flowables = []
    lines = md_text.split("\n")
    i = 0
    in_code = False
    code_lines = []

    while i < len(lines):
        line = lines[i]

        # Code block
        if line.strip().startswith("```"):
            if in_code:
                code_text = escape_xml("\n".join(code_lines))
                flowables.append(Preformatted(code_text, styles["KCode"]))
                code_lines = []
                in_code = False
            else:
                in_code = True
            i += 1
            continue

        if in_code:
            code_lines.append(line)
            i += 1
            continue

        stripped = line.strip()

        # Empty line
        if not stripped:
            flowables.append(Spacer(1, 4))
            i += 1
            continue

        # Horizontal rule
        if stripped == "---":
            flowables.append(HRFlowable(width="100%", thickness=1, color=HexColor("#cccccc"),
                                         spaceBefore=8, spaceAfter=8))
            i += 1
            continue

        # Headers
        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            text = stripped.lstrip("#").strip()
            text = escape_xml(text)
            text = inline_format(text)
            style_map = {1: "KTitle", 2: "KH1", 3: "KH2", 4: "KH3"}
            style_name = style_map.get(level, "KH4")
            flowables.append(Paragraph(text, styles[style_name]))
            i += 1
            continue

        # Table
        if stripped.startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            rows = parse_table(table_lines)
            if rows:
                # Escape and format cells
                formatted_rows = []
                for row in rows:
                    formatted_rows.append([
                        Paragraph(inline_format(escape_xml(cell)), styles["KBody"])
                        for cell in row
                    ])

                ncols = max(len(r) for r in formatted_rows)
                col_width = (A4[0] - 40 * mm) / ncols

                t = Table(formatted_rows, colWidths=[col_width] * ncols)
                t_style = [
                    ("BACKGROUND", (0, 0), (-1, 0), HexColor("#e8eaf6")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#1a1a2e")),
                    ("FONTNAME", (0, 0), (-1, -1), "AppleGothic"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cccccc")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ]
                t.setStyle(TableStyle(t_style))
                flowables.append(t)
                flowables.append(Spacer(1, 6))
            continue

        # Blockquote
        if stripped.startswith(">"):
            text = stripped.lstrip(">").strip()
            text = escape_xml(text)
            text = inline_format(text)
            flowables.append(Paragraph(text, styles["KBlockquote"]))
            i += 1
            continue

        # Bullet / numbered list
        if re.match(r'^[\-\*]\s', stripped) or re.match(r'^\d+\.\s', stripped):
            text = re.sub(r'^[\-\*]\s+', '', stripped)
            text = re.sub(r'^\d+\.\s+', '', text)
            text = escape_xml(text)
            text = inline_format(text)
            flowables.append(Paragraph("- " + text, styles["KBullet"]))
            i += 1
            continue

        # Regular paragraph
        text = escape_xml(stripped)
        text = inline_format(text)
        flowables.append(Paragraph(text, styles["KBody"]))
        i += 1

    return flowables


def main():
    with open(INPUT_MD, "r", encoding="utf-8") as f:
        md_text = f.read()

    styles = build_styles()

    doc = SimpleDocTemplate(
        OUTPUT_PDF,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    flowables = md_to_flowables(md_text, styles)
    doc.build(flowables)
    print(f"PDF created: {OUTPUT_PDF}")


if __name__ == "__main__":
    main()
