from pathlib import Path
from html import escape
import re
import argparse
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    Table,
    TableStyle,
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

R = Path(__file__).resolve().parents[1]
args = argparse.ArgumentParser()
args.add_argument(
    "--guide",
    action="store_true",
    help="Build the student working guide with the revised shared-PV design",
)
options = args.parse_args()
out = R / ("docs/WORKING_GUIDE.pdf" if options.guide else "docs/TECHNICAL_REPORT.pdf")
styles = getSampleStyleSheet()
styles["Normal"].fontName = "Helvetica"
styles["Normal"].fontSize = 9
styles["Normal"].leading = 13
styles["Heading1"].fontSize = 20
styles["Heading1"].spaceAfter = 15
styles["Heading2"].fontSize = 13
styles["Heading2"].spaceBefore = 16
styles["Code"].fontSize = 7
styles["Code"].leading = 10
story = [
    Paragraph(
        "How the whole solar microgrid works"
        if options.guide
        else "Autonomous Solar Microgrid",
        styles["Title"],
    ),
    Paragraph("Digital Twin and Decision-Aware Active Sensing", styles["Heading1"]),
    Spacer(1, 25),
    Paragraph("Engineering implementation report / 9 November 2026", styles["Normal"]),
    Spacer(1, 20),
    Paragraph(
        "Software prototype with provisional electrical interfaces. Hardware construction, protection validation and commissioning remain separate acceptance activities.",
        styles["Normal"],
    ),
    Spacer(1, 25),
]
files = [
    "START_HERE.md",
    "docs/architecture/SYSTEM.md",
    "docs/architecture/ASSUMPTIONS.md",
    "hardware/schematics/POWER_DESIGN.md",
    "hardware/pinouts/PIN_MAPS.md",
    "hardware/wiring/I2C.md",
    "docs/firmware/BUILD_FLASH.md",
    "docs/firmware/STATE_MACHINES.md",
    "docs/protocols/WIRE_V1.md",
    "docs/protocols/RF_INDIA.md",
    "docs/architecture/DIGITAL_TWIN.md",
    "docs/research/DTAV.md",
    "docs/bom/POWER_BUDGET.md",
    "docs/bom/SHOPPING_LIST.md",
    "docs/safety/FAILURE_MODES.md",
    "docs/safety/COMMISSIONING.md",
    "docs/testing/TEST_PLAN.md",
    "docs/testing/VALIDATION.md",
    "docs/LIMITATIONS.md",
    "docs/INTEGRATION_CHECKLIST.md",
    "docs/VIVA.md",
    "docs/TROUBLESHOOTING.md",
    "docs/research/SOURCES.md",
]
if options.guide:
    from shared_power_diagram import drawing

    story.append(Spacer(1, 20))
    story.append(drawing())
    files = ["docs/HOW_EVERYTHING_WORKS.md", "docs/architecture/REVISION_2.md"] + files
else:
    files = ["docs/architecture/REVISION_2.md"] + files


def para(t, style="Normal"):
    t = escape(t)
    t = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"`(.*?)`", r'<font name="Courier">\1</font>', t)
    return Paragraph(t, styles[style])


for file in files:
    story.append(PageBreak())
    lines = (R / file).read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        i += 1
        if not line.strip():
            continue
        if line.startswith("```"):
            while i < len(lines) and not lines[i].startswith("```"):
                story.append(para(lines[i], "Code"))
                i += 1
            i += 1
            continue
        if line.startswith("|"):
            rows = [line]
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(lines[i])
                i += 1
            data = [
                [para(c.strip()) for c in row.strip("|").split("|")]
                for row in rows
                if not re.match(r"^\|[\s:|-]+\|$", row)
            ]
            n = max(map(len, data))
            data = [row + [para("")] * (n - len(row)) for row in data]
            widths = [495 / n] * n
            table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e4eef0")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#78939a")),
                        (
                            "LINEBELOW",
                            (0, 1),
                            (-1, -1),
                            0.2,
                            colors.HexColor("#d8e1e3"),
                        ),
                    ]
                )
            )
            story.append(table)
            story.append(Spacer(1, 9))
            continue
        if line.startswith("# "):
            story.append(para(line[2:], "Heading1"))
        elif line.startswith("## "):
            story.append(para(line[3:], "Heading2"))
        else:
            story.append(para(line))
            story.append(Spacer(1, 7))


def footer(canvas, doc):
    canvas.setStrokeColor(colors.HexColor("#d8e1e3"))
    canvas.line(50, 42, 545, 42)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#526c74"))
    canvas.drawString(50, 30, "SOLAR MICROGRID / PROVISIONAL ENGINEERING / 2026-11-09")
    canvas.drawRightString(545, 30, str(doc.page))


SimpleDocTemplate(
    str(out),
    pagesize=(595.28, 841.89),
    rightMargin=50,
    leftMargin=50,
    topMargin=50,
    bottomMargin=55,
    title="Solar Microgrid Working Guide - Shared PV Revision 2"
    if options.guide
    else "Solar Microgrid Engineering Report - Shared PV Revision 2",
    author="Solar microgrid project",
).build(story, onFirstPage=footer, onLaterPages=footer)
print(out)
