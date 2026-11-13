"""Revision-2 functional net diagram: deliberately not a converter PCB schematic."""

from pathlib import Path
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Circle
from reportlab.graphics import renderSVG
from reportlab.lib import colors


def drawing():
    d = Drawing(495, 355)

    def line(x, y, a, b):
        d.add(Line(x, y, a, b, strokeColor=colors.HexColor("#315f4d"), strokeWidth=1.5))

    def text(x, y, t, size=9):
        d.add(String(x, y, t, fontName="Helvetica", fontSize=size))

    def box(x, y, w, h, title, sub):
        d.add(
            Rect(
                x,
                y,
                w,
                h,
                fillColor=colors.HexColor("#eff6f2"),
                strokeColor=colors.HexColor("#315f4d"),
            )
        )
        text(x + 7, y + h - 16, title, 10)
        text(x + 7, y + 10, sub, 8)

    box(5, 300, 105, 45, "PV1-PV4", "Four protected branches")
    box(130, 300, 110, 45, "A+B combiner", "Protected PV_COMB")
    line(110, 322, 130, 322)
    line(240, 322, 415, 322)
    d.add(Circle(260, 322, 3, fillColor=colors.HexColor("#315f4d")))
    line(260, 322, 260, 280)
    line(260, 280, 225, 280)
    line(225, 280, 225, 255)
    line(415, 322, 415, 255)
    box(160, 210, 130, 45, "MPPT charger", "DPM + 1S CC/CV + NTC")
    box(340, 210, 145, 45, "KPV NO -> boost", "Regulated SOLAR12")
    box(5, 205, 120, 50, "PB10 signal MOSFET", "Pull MPPSET low to pause")
    line(125, 230, 160, 230)
    text(7, 185, "PB1 senses PV bus locally", 8)
    line(225, 210, 225, 160)
    box(160, 115, 130, 45, "Protected 1S pack", "Fuse + signed monitor")
    line(290, 137, 340, 137)
    box(340, 115, 145, 45, "Battery boost", "Regulated BAT12")
    line(415, 210, 415, 190)
    text(345, 177, "SOLAR12 -> KSEL NC", 8)
    line(415, 115, 415, 95)
    text(345, 82, "BAT12 -> KSEL NO", 8)
    text(5, 52, "KSEL COM -> KEN NO master -> bus monitor -> KL1/KL2/KL3 -> loads", 10)
    text(
        5,
        30,
        "MPPT and solar boost share PV only with the specified regulation/current limits.",
        8,
    )
    text(
        5,
        13,
        "Signal/protection interface drawing. Common DC return and branch fuses are required.",
        8,
    )
    return d


if __name__ == "__main__":
    path = (
        Path(__file__).resolve().parents[1]
        / "hardware/schematics/03-charge-convert-allocation.svg"
    )
    renderSVG.drawToFile(drawing(), str(path))
    print(path)
