"""Electrical connection SVGs and editable KiCad legacy integration schematic.
No manufacturing release: unresolved module internals are explicitly labelled.
"""

from pathlib import Path
from html import escape
import json

R = Path(__file__).resolve().parents[1]
D = R / "hardware/schematics"
D.mkdir(parents=True, exist_ok=True)


class Drawing:
    def __init__(self, title, w=1200, h=650):
        self.w = w
        self.h = h
        self.parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><rect width="100%" height="100%" fill="white"/><style>text{{font-family:Arial,sans-serif;fill:#142932}}.net{{stroke:#177052;stroke-width:2;fill:none}}.symbol{{stroke:#182f39;stroke-width:2;fill:#fafcff}}</style>'
        ]
        self.text(30, 35, title, 22)
        self.text(
            30,
            60,
            "PROVISIONAL ENGINEERING REVIEW / Not assembly approval / 2026-11-09",
            12,
            "#a34731",
        )

    def text(self, x, y, t, size=13, color=None):
        self.parts.append(
            f'<text x="{x}" y="{y}" font-size="{size}"'
            + (f' style="fill:{color}"' if color else "")
            + ">"
            + escape(t)
            + "</text>"
        )

    def line(self, *points):
        self.parts.append(
            '<polyline class="net" points="'
            + " ".join(f"{x},{y}" for x, y in points)
            + '"/>'
        )

    def dot(self, x, y):
        self.parts.append(f'<circle cx="{x}" cy="{y}" r="4" fill="#177052"/>')

    def box(self, x, y, w, h, title, subtitle=""):
        self.parts.append(
            f'<rect class="symbol" x="{x}" y="{y}" width="{w}" height="{h}"/>'
        )
        self.text(x + 10, y + 25, title, 14)
        if subtitle:
            self.text(x + 10, y + 46, subtitle, 10)

    def resistor(self, x, y, label):
        self.line((x - 15, y), (x, y))
        self.parts.append(
            f'<rect class="symbol" x="{x}" y="{y - 8}" width="55" height="16"/>'
        )
        self.line((x + 55, y), (x + 70, y))
        self.text(x - 4, y - 20, label, 11)

    def ground(self, x, y):
        self.line((x, y), (x, y + 15))
        self.line((x - 15, y + 15), (x + 15, y + 15))
        self.line((x - 10, y + 21), (x + 10, y + 21))
        self.line((x - 5, y + 27), (x + 5, y + 27))

    def save(self, name):
        self.text(
            30,
            self.h - 25,
            "Module boundaries are functional interfaces. Refer to POWER_DESIGN.md and manufacturer circuits for unresolved passives.",
            11,
        )
        (D / (name + ".svg")).write_text(
            "".join(self.parts) + "</svg>", encoding="utf-8"
        )


d = Drawing("01 / Array, independent branch protection and cluster combiner", 1200, 690)
for i in range(4):
    y = 125 + i * 120
    d.box(35, y - 25, 100, 60, f"PV{i + 1}", "6V / 5W ref.")
    d.line((135, y + 5), (170, y + 5))
    d.resistor(185, y + 5, f"FP{i + 1} + Rsh 20mR")
    d.line((255, y + 5), (300, y + 5))
    d.box(300, y - 25, 180, 60, f"EF{i + 1} TPS25940L", "High-side reverse blocking")
    d.line((480, y + 5), (600, y + 5))
    d.text(
        310, y + 65, f"EN GPIO{[15, 16, 17, 18][i]} / FLT GPIO{[6, 7, 21, 47][i]}", 11
    )
for y in (130, 370):
    d.line((600, y), (600, y + 120))
    d.dot(600, y + 60)
    d.line((600, y + 60), (650, y + 60))
    d.box(650, y + 30, 165, 60, "Cluster INA226", "10mR + service fuse")
    d.line((815, y + 60), (850, y + 60))
    d.box(850, y + 30, 125, 60, "Blocking", ">=20V target")
    d.line((975, y + 60), (1040, y + 60))
d.line((1040, 190), (1040, 430))
d.dot(1040, 310)
d.line((1040, 310), (1160, 310))
d.text(1060, 295, "PV_COMB", 13)
d.text(
    40,
    640,
    "All panel negatives -> PV_RETURN, star DC ground. Do not join pre-protection positives.",
    13,
)
d.save("01-array-combiner")

d = Drawing(
    "02 / Panel electronic isolation channel with independent protection", 1200, 730
)
d.text(40, 125, "PVn+", 15)
d.line((90, 120), (135, 120))
d.resistor(150, 120, "FPn / DC fuse")
d.line((220, 120), (260, 120))
d.resistor(275, 120, "Rsh=20mR / 1W")
d.line((345, 120), (440, 120))
d.box(440, 90, 300, 220, "TPS25940L RVC20", "IN pins9-13 / OUT pins4-8")
d.line((740, 120), (1080, 120))
d.text(900, 105, "CLUSTER_n+", 14)
d.text(465, 175, "Internal opposing MOSFET protection", 12)
d.text(465, 197, "Reverse blocking + current limiter", 12)
d.text(465, 225, "EN14 / FLT20 / ILIM17 / dVdT18", 12)
d.text(465, 249, "GND16 + exposed thermal pad", 12)
d.text(465, 275, "DEVSLP1=GND; OVP15 divider", 12)
d.line((260, 120), (260, 185), (160, 185))
d.line((345, 120), (345, 210), (160, 210))
d.box(35, 170, 125, 65, "INA226", "Kelvin IN+/IN-")
d.line((100, 235), (100, 325))
d.text(40, 350, "I2C +3.3V logic", 12)
d.line((510, 310), (510, 365))
d.resistor(510, 365, "R_ILIM 75k target")
d.line((580, 365), (610, 365))
d.ground(610, 365)
d.text(450, 420, "89/R(kohm) gives nominal 1.19A; audit tolerance/thermal design.", 12)
d.text(
    40,
    475,
    "S3 EN ->1k ->EN14 with100k fail-low pulldown. Input UVLO: implement approved divider/inhibit circuit.",
    13,
)
d.text(
    40,
    505,
    "FLT20 open drain ->10k pullup3.3V ->S3 input. Do not treat FLT as uniquely diagnosing a short.",
    13,
)
d.text(
    40,
    535,
    "Select Cin/Cout/dVdT/UVLO/OVP from actual TI reference circuit and PV cold-voltage envelope.",
    13,
)
d.text(
    40,
    565,
    "The 75k nominal ILIM is provisional; not a guarantee of 1.2A over all tolerances.",
    13,
)
d.text(
    40,
    595,
    "Controller never replaces hardware limit. Fuse may not clear at PV-only Isc.",
    13,
)
d.ground(700, 310)
d.save("02-panel-efuse")

from shared_power_diagram import drawing as shared_pv_drawing
from reportlab.graphics import renderSVG

renderSVG.drawToFile(shared_pv_drawing(), str(D / "03-charge-convert-allocation.svg"))

d = Drawing("04 / Source transfer: master disconnect plus BBM selector", 1200, 680)
d.text(40, 150, "SOLAR12", 14)
d.box(165, 120, 160, 60, "Reverse blocking", "source fuse")
d.line((120, 145), (165, 145))
d.line((325, 145), (440, 145))
d.dot(440, 145)
d.text(450, 135, "NC solar", 12)
d.text(40, 300, "BAT12", 14)
d.box(165, 270, 160, 60, "Reverse blocking", "source fuse")
d.line((105, 295), (165, 295))
d.line((325, 295), (440, 295))
d.dot(440, 295)
d.text(450, 320, "NO battery", 12)
d.line((440, 145), (535, 220), (620, 220))
d.text(480, 85, "KSEL transfer PA9", 14)
d.dot(535, 220)
d.text(550, 200, "COM", 11)
d.line((620, 220), (670, 220))
d.line((680, 220), (730, 190))
d.dot(745, 220)
d.line((745, 220), (825, 220))
d.text(650, 160, "KEN master PA8", 14)
d.box(825, 190, 170, 60, "Main bus monitor", "INA226 0x41 / 10mR")
d.line((995, 220), (1150, 220))
d.text(1050, 200, "BUS12", 15)
d.text(
    40,
    400,
    "PA8=0 PA9=0: bus OFF, selector solar. PA8=0 PA9=1: bus OFF, selector battery.",
    14,
)
d.text(
    40,
    435,
    "PA8=1 PA9=0: solar ONLY. PA8=1 PA9=1: battery ONLY. Neither binary state parallels sources.",
    14,
)
d.text(
    40,
    480,
    "Open KEN -> change KSEL -> wait>=250ms -> revalidate -> close KEN -> stage loads every2s.",
    14,
)
d.text(
    40,
    520,
    "Verify BBM timing, DC motor/contact endurance, flyback release delay and failed-contact mitigation.",
    13,
)
d.text(
    40,
    555,
    "Optional selector second-pole feedback is not wired. No physical actuation guarantee from coil drive alone.",
    13,
)
d.save("04-source-transfer")

d = Drawing("05 / Three protected and monitored load branches", 1200, 650)
d.text(35, 125, "BUS12", 15)
d.line((95, 120), (95, 490))
for i in range(3):
    y = 160 + i * 140
    d.dot(95, y)
    d.line((95, y), (160, y))
    d.box(
        160, y - 28, 200, 65, f"FL{i + 1} + current limiter", "Independent of firmware"
    )
    d.line((360, y), (410, y))
    d.box(410, y - 28, 180, 65, f"INA226 Load{i + 1}", "10mR / Kelvin")
    d.line((590, y), (680, y))
    d.line((680, y), (720, y - 25))
    d.dot(735, y)
    d.line((735, y), (815, y))
    d.text(650, y - 48, f"KL{i + 1} NO / PA{10 + i}", 12)
    d.box(
        815,
        y - 28,
        190,
        65,
        ["Critical1W", "Fan3W", "Auxiliary2W"][i],
        "12V demonstration assumption",
    )
    d.line((1005, y), (1090, y))
    d.ground(1090, y)
d.text(
    40,
    590,
    "Fan: diode cathode load+ / anode return + appropriate TVS/snubber. Measure startup and stall before integration.",
    13,
)
d.save("05-load-branches")

d = Drawing("06 / Relay driver channel, repeat KEN/KSEL/KPV/KL1-3", 1200, 620)
d.text(40, 180, "MCU GPIO", 14)
d.line((130, 175), (190, 175))
d.resistor(205, 175, "100R gate")
d.line((275, 175), (420, 175))
d.box(420, 140, 180, 100, "Logic N-MOSFET", "Rds_on at3.3V verified")
d.text(430, 215, "G / D / S interface", 12)
d.line((500, 140), (500, 95), (820, 95))
d.box(820, 75, 200, 65, "12V relay coil", "flyback diode in parallel")
d.line((1020, 95), (1100, 95))
d.text(1040, 75, "COIL12", 12)
d.line((500, 240), (500, 300))
d.ground(500, 300)
d.line((350, 175), (350, 215))
d.parts.append('<rect class="symbol" x="342" y="215" width="16" height="55"/>')
d.line((350, 270), (350, 290))
d.text(180, 290, "100k gate-source", 12)
d.ground(350, 290)
d.text(
    40,
    400,
    "Flyback cathode to COIL12, anode to MOSFET drain; choose clamp for release timing and energy.",
    14,
)
d.text(
    40,
    435,
    "Never connect a coil directly to MCU. External12V supply must support simultaneous coil current.",
    14,
)
d.text(
    40,
    470,
    "Logic ground common with driver source; gate pulldown holds relays OFF through reset/brownout.",
    14,
)
d.save("06-relay-driver")

# Direct signal wiring sheets from the single authoritative map, not decorative diagrams.
import csv

pins = {}
with (R / "hardware/wiring/controller_wiring.csv").open(encoding="utf-8") as f:
    for row in csv.DictReader(f):
        pins.setdefault(row["source_module"], {})[row["source_pin"]] = row["purpose"]
for index, (board, mapping) in enumerate(pins.items(), 7):
    d = Drawing(
        f"{index:02} / {board} pin-to-interface wiring",
        1200,
        max(650, 130 + len(mapping) * 30),
    )
    for i, (pin, signal) in enumerate(mapping.items()):
        y = 110 + i * 30
        d.text(40, y, pin, 13)
        d.line((145, y - 5), (360, y - 5))
        d.text(385, y, signal, 13)
        d.text(780, y, "3.3V signal / see wiring CSV", 11)
    d.save(f"{index:02}-{board}-signals")

d = Drawing("10 / Control and communications architecture", 1200, 540)
boxes = [
    (30, "S3 sensor node", "6 INA / DHT / LDR"),
    (315, "STM32F411", "7 INA / relays / TFT"),
    (600, "ESP32-C3", "UART to Wi-Fi bridge"),
    (885, "Laptop host", "MQTT / FastAPI / React"),
]
for x, title, sub in boxes:
    d.box(x, 180, 230, 110, title, sub)
for x, label in [(260, "LoRa 433.92"), (545, "UART COBS"), (830, "MQTT binary")]:
    d.line((x, 235), (x + 55, 235))
    d.text(x - 5, 160, label, 11)
d.text(
    40,
    370,
    "Bidirectional commands: host -> MQTT -> C3 -> UART -> STM32 -> LoRa -> S3. ACKs follow reverse path.",
    13,
)
d.text(
    40,
    410,
    "Protection boundaries: branch eFuse, hardware current limits, pack PCM, boost UVLO, DC fuses and emergency cutoff.",
    13,
)
d.save("10-system-architecture")

# Legacy Eeschema integration document with actual connector nets, readable by KiCad import.
K = R / "hardware/kicad"
K.mkdir(parents=True, exist_ok=True)
sch = [
    "EESchema Schematic File Version 4",
    "LIBS:power",
    "EELAYER 29 0",
    "EELAYER END",
    "$Descr A4 11693 8268",
    "encoding utf-8",
    "Sheet 1 1",
    'Title "Solar microgrid integration / provisional"',
    'Date "2026-11-09"',
    'Rev "0.2-shared-pv-review"',
    'Comp "Educational prototype"',
    'Comment1 "Interface net map only. See POWER_DESIGN.md. Not ERC/PCB signoff."',
    "$EndDescr",
]
modules = [
    ("PV_COMB", ["PV_COMB", "GND"]),
    ("MPPT", ["PV_COMB", "BAT_SYS", "GND", "NTC", "MPPSET"]),
    ("SOLAR_BOOST", ["SOLAR_IN", "SOLAR12", "GND"]),
    ("PACK", ["PACK_PLUS", "PACK_MINUS"]),
    ("BAT_BOOST", ["BAT_SYS", "BAT12", "GND"]),
    ("SOURCE_TRANSFER", ["SOLAR12", "BAT12", "BUS12", "GND"]),
    ("LOAD1", ["BUS12", "L1_PLUS", "GND"]),
    ("LOAD2", ["BUS12", "L2_PLUS", "GND"]),
    ("LOAD3", ["BUS12", "L3_PLUS", "GND"]),
]
for i, (name, nets) in enumerate(modules):
    x = 1600 + (i % 3) * 3300
    y = 1700 + (i // 3) * 2000
    n = len(nets)
    ref = f"J{i + 1}"
    sch += [
        "$Comp",
        f"L Connector_Generic:Conn_01x{n:02d} {ref}",
        f"U 1 1 {0x60000000 + i:X}",
        f"P {x} {y}",
        f'F 0 "{ref}" H {x + 80} {y} 50 0000 L CNN',
        f'F 1 "{name}" H {x + 80} {y - 100} 50 0000 L CNN',
        f"\t1 {x} {y}",
        "\t1 0 0 -1",
        "$EndComp",
    ]
    for j, net in enumerate(nets):
        yy = y + (j - (n - 1) // 2) * 100
        sch += [
            "Wire Wire Line",
            f"\t{x - 200} {yy} {x - 850} {yy}",
            f"Text Label {x - 850} {yy} 0 40 ~ 0",
            net,
        ]
sch += [
    "Text Notes 650 750 0 70 ~ 0",
    "Rev2: protected MPPT input=PV_COMB; KPV COM=PV_COMB, NO=SOLAR_IN, NC insulated. PB10 inhibits MPPSET.",
    "Text Notes 650 7800 0 55 ~ 0",
    "Module internals/protection passives unresolved. Actual board terminal order must be verified.",
    "$EndSCHEMATC",
]
(K / "integration.sch").write_text("\n".join(sch) + "\n")
print("Generated10 SVG connection sheets and KiCad integration net map")
