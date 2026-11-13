"""Expand connection tables with module-labelled terminals and power nets."""

from pathlib import Path
import csv

R = Path(__file__).resolve().parents[1]
rows = []


def wire(
    sm,
    sp,
    dm,
    dp,
    voltage,
    kind,
    purpose,
    protection,
    notes="Terminal label, not an invented connector position; confirm purchased board",
):
    rows.append(
        dict(
            source_module=sm,
            source_pin=sp,
            destination_module=dm,
            destination_pin=dp,
            voltage=voltage,
            signal_type=kind,
            purpose=purpose,
            required_protection=protection,
            notes=notes,
        )
    )


for board, names, sda, scl in [
    ("S3", ["Cluster A", "Cluster B", "PV1", "PV2", "PV3", "PV4"], "GPIO8", "GPIO9"),
    (
        "STM32",
        ["Battery", "Bus", "Solar12", "Battery12", "Load1", "Load2", "Load3"],
        "PB7",
        "PB6",
    ),
]:
    for name in names:
        for p, d in [(sda, "SDA"), (scl, "SCL")]:
            wire(
                board,
                p,
                "INA226 " + name,
                d,
                "3.3V",
                "I2C",
                f"{board} shared bus",
                "One effective4.7k pullup pair; remove duplicate module pullups",
            )
        wire(
            "REG3V3",
            "3V3",
            "INA226 " + name,
            "VS",
            "3.3V",
            "power",
            "Monitor supply",
            "100nF at device; VS is not measured high-side rail",
        )
        wire(
            "STAR_RETURN",
            "GND",
            "INA226 " + name,
            "GND",
            "0V",
            "ground",
            "Logic reference",
            "Kelvin shunt sense separate from power return",
        )
for board, signals in [
    (
        "S3",
        [
            ("GPIO12", "SCK"),
            ("GPIO13", "MISO"),
            ("GPIO11", "MOSI"),
            ("GPIO10", "NSS"),
            ("GPIO14", "RESET"),
        ],
    ),
    (
        "STM32",
        [
            ("PA5", "SCK"),
            ("PA6", "MISO"),
            ("PA7", "MOSI"),
            ("PA4", "NSS"),
            ("PB0", "RESET"),
        ],
    ),
]:
    for gpio, terminal in signals:
        wire(
            board,
            gpio,
            "Ra02 " + board,
            terminal,
            "3.3V",
            "SPI/GPIO",
            "Radio interface",
            "No5V logic; NSS pullup; RESET defined at boot",
        )
    wire(
        "REG3V3",
        "3V3",
        "Ra02 " + board,
        "3.3V",
        "3.3V",
        "power",
        "Radio supply",
        "100nF+10uF local; validate burst-current supply",
    )
    wire(
        "STAR_RETURN",
        "GND",
        "Ra02 " + board,
        "GND",
        "0V",
        "ground",
        "Radio reference",
        "Short return and antenna keepout",
    )
    wire(
        "Antenna " + board,
        "50ohm feed",
        "Ra02 " + board,
        "IPEX",
        "RF",
        "RF",
        "433MHz antenna",
        "Verify connector,gain/ERP; attach before TX",
    )
for gpio, t in [
    ("PA5", "SCK"),
    ("PA7", "SDA/MOSI"),
    ("PB12", "CS"),
    ("PB13", "DC"),
    ("PB14", "RESET"),
]:
    wire(
        "STM32",
        gpio,
        "TFT ST7735",
        t,
        "3.3V",
        "SPI/GPIO",
        "Display interface",
        "SCK/MOSI shared intentionally; TFT SDO unconnected",
    )
for name, gpio in [
    ("UP", "PA0"),
    ("DOWN", "PA1"),
    ("LEFT", "PB3"),
    ("RIGHT", "PB4"),
    ("SELECT", "PB5"),
]:
    wire(
        "STM32",
        gpio,
        "Button " + name,
        "contact1",
        "3.3V",
        "digital",
        "Active-low navigation",
        "Internal pullup;30ms debounce; optional100nF+1k",
    )
    wire(
        "Button " + name,
        "contact2",
        "STAR_RETURN",
        "GND",
        "0V",
        "ground",
        "Button return",
        "Exactly5 menu buttons; emergency cutoff separate",
    )
for gpio, name in [
    ("PA8", "KEN"),
    ("PA9", "KSEL"),
    ("PA10", "KL1"),
    ("PA11", "KL2"),
    ("PA12", "KL3"),
    ("PB8", "KPV"),
]:
    wire(
        "STM32",
        gpio,
        "Driver " + name,
        "GATE_IN",
        "3.3V",
        "digital",
        "Fail-low coil drive",
        "100ohm gate+100k pulldown+3.3V-ratedMOSFET",
    )
    wire(
        "Driver " + name,
        "DRAIN",
        name,
        "COIL-",
        "12V switched",
        "power",
        "Coil switching",
        "Flyback diode anode drain/cathodeCOIL12",
    )
    wire(
        "COIL12",
        "+12V",
        name,
        "COIL+",
        "12V",
        "power",
        "Relay supply",
        "External isolated12V1A target; verify actual coil current",
    )
for i, gpio, flt in zip(range(1, 5), [15, 16, 17, 18], [6, 7, 21, 47]):
    for sm, sp, dm, dp, purpose in [
        ("S3", f"GPIO{gpio}", f"EF{i}", "EN14", "Panel inhibit"),
        (f"EF{i}", "FLT20", "S3", f"GPIO{flt}", "Protection status"),
    ]:
        wire(
            sm,
            sp,
            dm,
            dp,
            "3.3V",
            "digital",
            purpose,
            "EN fail-low100k; FLT10k pullup3.3V; verify UVLO network",
        )
    wire(
        f"PV{i}",
        "+",
        f"FP{i}",
        "IN",
        "PV<=12V provisional",
        "power",
        "Panel service fuse",
        "DC-rated fuse; coordination pending actual PV coldVoc/Isc",
    )
    wire(
        f"FP{i}",
        "OUT",
        f"RSH_PV{i}",
        "IN+",
        "PV",
        "power",
        "Panel high-side shunt",
        "20mohm1W Kelvin",
    )
    wire(
        f"RSH_PV{i}",
        "IN-",
        f"EF{i}",
        "IN9-13",
        "PV",
        "power",
        "Protected isolation input",
        "TPS25940L IN pins tied per TI layout",
    )
    wire(
        f"EF{i}",
        "OUT4-8",
        "Cluster " + ("A" if i < 3 else "B"),
        "POSITIVE",
        "PV",
        "power",
        "Parallel after independent branch protection",
        "Never join bare panel positives upstream of protection",
    )
    wire(
        f"PV{i}",
        "-",
        "PV_RETURN",
        "GND",
        "0V",
        "ground",
        "Panel power return",
        "Rated wire and service disconnect",
    )
for cluster in ("A", "B"):
    wire(
        "Cluster " + cluster,
        "POSITIVE",
        "Cluster " + cluster + " shunt/fuse",
        "IN",
        "PV",
        "power",
        "Independent cluster measurement/protection",
        "10mohm1W;2.4A design target not final fuse rating",
    )
    wire(
        "Cluster " + cluster + " shunt/fuse",
        "OUT",
        "Block " + cluster,
        "ANODE/IN",
        "PV",
        "power",
        "Cluster reverse protection",
        "Voltage/drop/current/thermal review required",
    )
    wire(
        "Block " + cluster,
        "CATHODE/OUT",
        "KPV",
        "COM",
        "PV",
        "power",
        "Protected combining",
        "KPV COM is single combined PV node",
    )
for sm, sp, dm, dp, purpose in [
    (
        "PV_COMB",
        "+",
        "Charger branch fuse/reverse protection",
        "IN",
        "Continuously connected MPPT branch",
    ),
    (
        "Charger branch fuse/reverse protection",
        "OUT",
        "BQ24650",
        "VIN",
        "MPPT input independent of KPV",
    ),
    ("KPV", "NO", "Solar boost", "VIN", "Solar converter input enable; NC insulated"),
    ("BQ24650", "BAT", "BAT_SYS", "+", "CC/CV charger output"),
    ("Protected pack", "PACK+", "FBAT", "IN", "Pack fuse near cell"),
    ("FBAT", "OUT", "Battery INA shunt", "PACK_SIDE", "Bidirectional sensing"),
    ("Battery INA shunt", "SYSTEM_SIDE", "BAT_SYS", "+", "Net battery current"),
    ("BAT_SYS", "+", "Battery boost", "VIN", "Boost supply"),
    ("Solar boost", "VOUT", "Source block solar", "IN", "Source protection"),
    ("Battery boost", "VOUT", "Source block battery", "IN", "Source protection"),
    ("Source block solar", "OUT", "KSEL", "NC", "Solar source"),
    ("Source block battery", "OUT", "KSEL", "NO", "Battery source"),
    ("KSEL", "COM", "KEN", "COM", "Single selected source"),
    ("KEN", "NO", "Main bus INA shunt", "IN", "Master disconnect"),
    ("Main bus INA shunt", "OUT", "BUS12", "+", "Load bus"),
]:
    wire(
        sm,
        sp,
        dm,
        dp,
        "PV/1S/12V: see power tree",
        "power",
        purpose,
        "Protection and ratings per POWER_DESIGN.md; no source paralleling",
    )
for i in range(1, 4):
    for sm, sp, dm, dp in [
        ("BUS12", "+", f"Limiter/fuse L{i}", "IN"),
        (f"Limiter/fuse L{i}", "OUT", f"Load INA{i} shunt", "IN"),
        (f"Load INA{i} shunt", "OUT", f"KL{i}", "COM"),
        (f"KL{i}", "NO", f"Load{i}", "+"),
        (f"Load{i}", "-", "STAR_RETURN", "GND"),
    ]:
        wire(
            sm,
            sp,
            dm,
            dp,
            "12V",
            "power",
            "Independent load branch",
            "Verify DC inductive ratings and motor diode/TVS; current limiter independent of firmware",
        )
for i, (dh, ld) in enumerate([(4, 1), (5, 2)]):
    wire(
        "S3",
        f"GPIO{dh}",
        f"DHT22 {i + 1}",
        "DATA",
        "3.3V",
        "digital",
        "Temperature/humidity",
        "4.7k pullup3.3V;100nF bypass",
    )
    wire(
        f"LDR{i + 1}",
        "AO",
        "S3",
        f"GPIO{ld}",
        "0..3.3V",
        "ADC",
        "Relative illumination",
        "Power module3.3V;1k/100nF filter; not calibrated lux",
    )
    for module in (f"DHT22 {i + 1}", f"LDR{i + 1}"):
        wire(
            "REG3V3",
            "3V3",
            module,
            "VCC",
            "3.3V",
            "power",
            "Sensor supply",
            "Verify module supply compatibility",
        )
        wire(
            "STAR_RETURN",
            "GND",
            module,
            "GND",
            "0V",
            "ground",
            "Sensor reference",
            "Power return separated from Kelvin sense",
        )
wire(
    "STM32",
    "PA2 TX",
    "C3",
    "GPIO4 RX",
    "3.3V",
    "UART",
    "Upstream binary frames",
    "Cross TX/RX;1152008N1;common ground",
)
wire(
    "C3",
    "GPIO5 TX",
    "STM32",
    "PA3 RX",
    "3.3V",
    "UART",
    "Downstream commands/heartbeat",
    "Cross TX/RX;GPIO18/19 reservedUSB",
)
wire(
    "STM32",
    "PB9",
    "Solar test sink",
    "GATE_IN",
    "3.3V",
    "digital",
    "Loaded source qualification",
    "18ohm25W resistor + protectedMOSFET; hardware current limit",
)
wire(
    "Solar boost",
    "VOUT after INA",
    "Solar test sink",
    "LOAD+",
    "12V",
    "power",
    "8W qualification load",
    "Upstream of KSEL;guard hot resistor;no bus connection",
)
wire(
    "STM32",
    "PB10",
    "Charge inhibit NMOS",
    "GATE",
    "3.3V",
    "digital",
    "Charge inhibit request",
    "100ohm gate resistor;100kohm gate-source pulldown; choose guaranteed3.3V sink capability",
)
wire(
    "Charge inhibit NMOS",
    "DRAIN",
    "BQ24650",
    "MPPSET pin2",
    "Analog signal",
    "control",
    "Pull MPPSET below75mV to disable charging",
    "Do not drive MPPSET high from GPIO; retain original divider",
)
wire(
    "Charge inhibit NMOS",
    "SOURCE",
    "Charger signal GND",
    "GND",
    "0V",
    "ground",
    "Signal return",
    "Tie to reviewed charger ground",
)
wire(
    "PV_COMB",
    "+",
    "PV sense divider",
    "47kohm upper",
    "PV",
    "analog",
    "PV-bus sensing supply",
    "10kohm lower toGND;100nF filter; calibrate ADC reference/ratio",
)
wire(
    "PV sense divider",
    "MID",
    "STM32",
    "PB1 ADC1_IN9",
    "0..3.3V",
    "ADC",
    "Local PV-voltage measurement",
    "Scale5.7 nominal; not independent protection",
)
wire(
    "PV sense divider",
    "10kohm lower end",
    "STAR_RETURN",
    "GND",
    "0V",
    "ground",
    "Divider return",
    "100nF capacitor across lower resistor",
)
for module in (
    "BQ24650",
    "Solar boost",
    "Battery boost",
    "Solar test sink",
    "Driver KEN",
    "Driver KSEL",
    "Driver KPV",
    "Driver KL1",
    "Driver KL2",
    "Driver KL3",
):
    wire(
        "STAR_RETURN",
        "GND",
        module,
        "GND",
        "0V",
        "ground",
        "Common DC reference",
        "Protected PACK- only; independent e-stop/service isolation",
    )
with (R / "hardware/wiring/full_connections.csv").open(
    "w", newline="", encoding="utf-8"
) as f:
    w = csv.DictWriter(f, rows[0])
    w.writeheader()
    w.writerows(rows)
print(f"Generated{len(rows)} detailed module/net connections")
