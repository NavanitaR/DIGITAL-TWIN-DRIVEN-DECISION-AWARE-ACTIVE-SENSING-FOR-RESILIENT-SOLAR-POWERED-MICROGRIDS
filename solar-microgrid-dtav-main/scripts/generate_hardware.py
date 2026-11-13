"""Reproducible engineering tables. Values marked provisional are not approvals."""

from pathlib import Path
import csv, json

ROOT = Path(__file__).resolve().parents[1]


def write(path, text):
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text.strip() + "\n", encoding="utf-8")


def csvfile(path, rows):
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, rows[0])
        w.writeheader()
        w.writerows(rows)


pins = {
    "esp32-s3": {
        "GPIO8": "I2C SDA",
        "GPIO9": "I2C SCL",
        "GPIO12": "Ra02 SCK",
        "GPIO13": "Ra02 MISO",
        "GPIO11": "Ra02 MOSI",
        "GPIO10": "Ra02 NSS",
        "GPIO14": "Ra02 RESET",
        "GPIO4": "DHT22 A DATA",
        "GPIO5": "DHT22 B DATA",
        "GPIO1": "LDR A AO",
        "GPIO2": "LDR B AO",
        "GPIO15": "PV1 eFuse EN",
        "GPIO16": "PV2 eFuse EN",
        "GPIO17": "PV3 eFuse EN",
        "GPIO18": "PV4 eFuse EN",
        "GPIO6": "PV1 eFuse FLT",
        "GPIO7": "PV2 eFuse FLT",
        "GPIO21": "PV3 eFuse FLT",
        "GPIO47": "PV4 eFuse FLT",
    },
    "stm32-f411": {
        "PA5": "SPI1 SCK shared radio TFT",
        "PA6": "SPI1 MISO radio",
        "PA7": "SPI1 MOSI shared radio TFT",
        "PA4": "Ra02 NSS",
        "PB0": "Ra02 RESET",
        "PB12": "TFT CS",
        "PB13": "TFT DC",
        "PB14": "TFT RESET",
        "PB6": "I2C1 SCL",
        "PB7": "I2C1 SDA",
        "PA2": "UART2 TX to C3 GPIO4",
        "PA3": "UART2 RX from C3 GPIO5",
        "PA0": "UP button",
        "PA1": "DOWN button",
        "PB3": "LEFT button",
        "PB4": "RIGHT button",
        "PB5": "SELECT button",
        "PA8": "KEN master relay driver",
        "PA9": "KSEL transfer relay driver",
        "PA10": "KL1 relay driver",
        "PA11": "KL2 relay driver",
        "PA12": "KL3 relay driver",
        "PB8": "KPV solar converter enable relay driver",
        "PB9": "Solar qualification sink gate",
        "PB10": "MPPT MPPSET inhibit MOSFET gate",
        "PB1": "PV bus ADC divider 47k/10k",
    },
    "esp32-c3": {
        "GPIO4": "UART1 RX from STM32 PA2",
        "GPIO5": "UART1 TX to STM32 PA3",
        "GPIO18": "USB D- reserved",
        "GPIO19": "USB D+ reserved",
    },
}
rows = []
for board, mapping in pins.items():
    for gpio, signal in mapping.items():
        protection = "3.3V only; common signal ground"
        if "button" in signal:
            protection = "Button to GND; internal pull-up; optional 100nF + 1k series"
        if "relay driver" in signal:
            protection = (
                "100R gate; 100k pulldown; logic MOSFET; flyback; external coil supply"
            )
        if "eFuse EN" in signal:
            protection = "Fail-low EN; datasheet UVLO divider + open-drain inhibit; see power design"
        if "eFuse FLT" in signal:
            protection = "10k pullup to 3.3V; open-drain input"
        if "DHT22" in signal:
            protection = "4.7k to 3.3V; 100nF local bypass"
        if "LDR" in signal:
            protection = "Power module at 3.3V; ensure AO <=3.3V; 1k/100nF filter"
        if "I2C" in signal:
            protection = (
                "One effective 4.7k pullup pair to 3.3V; remove excess module pullups"
            )
        if gpio == "PB10" and board == "stm32-f411":
            protection = "100ohm gate resistor +100kohm pulldown; NMOS drain to MPPSET2, source charger signal GND"
        if gpio == "PB1" and board == "stm32-f411":
            protection = "47kohm/10kohm divider +100nF; calibrate actual VDDA and ratio"
        rows.append(
            dict(
                source_module=board,
                source_pin=gpio,
                destination_module=signal,
                destination_pin=signal.split()[-1],
                voltage="3.3V logic",
                signal_type="analog"
                if "LDR" in signal or "ADC" in signal
                else "digital",
                purpose=signal,
                required_protection=protection,
                notes="GPIO identity; verify actual connector silk and board revision",
            )
        )
csvfile("hardware/wiring/controller_wiring.csv", rows)
write(
    "hardware/pinouts/PIN_MAPS.md",
    "# Controller assignments\n\n"
    + "\n\n".join(
        "## "
        + b
        + "\n\n| MCU pin | Function |\n|---|---|\n"
        + "\n".join("|" + p + "|" + s + "|" for p, s in m.items())
        for b, m in pins.items()
    )
    + """\n
Pin maps target ESP32-S3 DevKitC-1 N8, STM32F411CEU6 Black Pill and an unstandardised C3 SuperMini. C3 compiles against DevKitM-1 chip profile (4MB flash), NOT a claim of connector compatibility. Check flash capacity and USB wiring before upload. S3 GPIO35-37 (PSRAM), GPIO0/3/45/46 straps and GPIO19/20 USB are avoided. C3 GPIO2/8/9 straps and GPIO20/21 programming UART are avoided. F411 PA13/14 SWD are reserved; PB3/4 cannot simultaneously use full JTAG. STM32 USB PA11/12 is unavailable because they drive load relays; program with ST-Link. Ra02 DIO0 is unconnected: both drivers poll IRQ registers. TFT MISO is unconnected. Do not wire TFT SDO onto radio MISO unless its tri-state behaviour is verified.

MCU substitution requires a new pin, flash, clock and alternate-function audit; do not use an F401 image on an F411 or assume F401 pin-profile equivalence. All data lines are 3.3V. External isolated controller supplies power the boards and coils; none is powered directly from the 1S cell or PV.
""",
)
addr = []
for bus, names, addresses, shunts in [
    (
        "S3",
        ["Cluster A", "Cluster B", "PV1", "PV2", "PV3", "PV4"],
        [0x40, 0x41, 0x44, 0x45, 0x48, 0x49],
        [0.01, 0.01, 0.02, 0.02, 0.02, 0.02],
    ),
    (
        "STM32",
        [
            "Battery signed",
            "Main bus",
            "Solar 12V",
            "Battery boost",
            "Load 1",
            "Load 2",
            "Load 3",
        ],
        [0x40, 0x41, 0x44, 0x45, 0x48, 0x49, 0x4C],
        [0.01] * 7,
    ),
]:
    straps = {
        0x40: ("GND", "GND"),
        0x41: ("GND", "VS"),
        0x44: ("VS", "GND"),
        0x45: ("VS", "VS"),
        0x48: ("SDA", "GND"),
        0x49: ("SDA", "VS"),
        0x4C: ("SCL", "GND"),
    }
    for name, a, r in zip(names, addresses, shunts):
        a1, a0 = straps[a]
        addr.append(
            dict(
                bus=bus,
                name=name,
                address=hex(a),
                A1=a1,
                A0=a0,
                shunt_ohms=r,
                shunt_power_W=1,
                fullscale_A=0.08192 / r,
                monitor_supply="3.3V",
                placement="high-side Kelvin; positive panel->combiner / battery->system",
            )
        )
csvfile("hardware/wiring/ina226_addresses.csv", addr)
write(
    "hardware/wiring/I2C.md",
    """# INA226 allocation and calibration

There are 13 monitors: six on the S3 bus and seven on the independent STM32 bus. Addresses may repeat across buses. Exact A1/A0 straps and 7-bit addresses are in `ina226_addresses.csv`. INA226 supports sixteen addresses, not just the four combinations exposed by some breakout boards. SDA/SCL strap options may require PCB rework; buy modules exposing both pins or fabricate carriers. No I2C mux is needed with all strap options accessible.

Raw shunt register signed LSB = 2.5 uV; bus LSB = 1.25 mV. I = signed_shunt*2.5e-6/R. P = V*I. Firmware intentionally uses raw registers so no incorrect factory current calibration can affect results. Optional INA current register calibration: CAL = floor(0.00512/(current_LSB*R)); for 0.02ohm, current_LSB=0.0001A gives CAL=2560; power_LSB=25*current_LSB. For 0.01ohm use 0.0002A, CAL=2560. Current register is unused in this release.

0.02ohm at 0.916A dissipates 16.8mW; 0.01ohm at cluster 1.832A dissipates 33.6mW. The assumed 3.358A battery startup current produces about113mW in 0.01ohm; specify 1W, 1%, low-temperature-coefficient four-terminal shunts. INA full-scale +/-81.92mV gives 4.096A / 8.192A respectively. Range is not a branch protection rating. Verify burden voltage and Kelvin routing, no load current through signal ground. Battery monitor sits on PACK+ outside integrated protection, between pack and combined charger/boost node; positive current is discharge. Charger return and boost return go to protected PACK-, never bare cell B-.

Calibrate zero with isolated branches, then >=3 current points using a traceable DMM and resistor load; store slope/offset with date, shunt temperature and uncertainty. Check polarity with a current-limited source. LDR calibration is dark/bright normalized relative intensity, not lux. Compare DHTs to a reference, preserve missing values. Analog module AO must remain <=3.3V.
""",
)

items = [
    (
        "Solar panel",
        4,
        "Waveshare 16158 6V 5W",
        "Voc7.2V +/-5%; Isc916mA +/-5%",
        1100,
        "Waveshare reference; Indian quote pending",
        "https://www.waveshare.com/catalog/product/view/id/3666/s/solar-panel-6v-5w/category/37/",
        "Datasheet-backed 6V5W equivalent",
        "proposed",
    ),
    (
        "Sensor controller",
        1,
        "ESP32-S3-DevKitC-1 N8",
        "3.3V GPIO; 8MB flash",
        850,
        "Robu/authorised Espressif distributor",
        "https://www.espressif.com/en/products/devkits/esp32-s3-devkitc-1",
        "N8R8 after pin/flash audit",
        "needs purchase",
    ),
    (
        "Central controller",
        1,
        "Black Pill STM32F411CEU6",
        "512KB flash 128KB SRAM; authentic MCU",
        450,
        "Robu / WeAct distributor",
        "",
        "WeAct F411CE documented revision",
        "needs purchase",
    ),
    (
        "Gateway controller",
        1,
        "ESP32-C3 SuperMini",
        "3.3V GPIO; verify 4MB flash USB",
        250,
        "Robu / documented board supplier",
        "",
        "Official DevKitM-1; pins differ",
        "unresolved",
    ),
    (
        "LoRa radio",
        2,
        "Ai-Thinker Ra-02 SX1278",
        "3.3V only; 433MHz; firmware4dBm",
        480,
        "Robu listing verified, price unavailable",
        "https://robu.in/product/sx1278-lora-module-ra-02-433mhz-wireless-spread-spectrum-transmission/",
        "Genuine Ra02 same frequency",
        "needs purchase",
    ),
    (
        "Antenna",
        2,
        "433MHz 50ohm IPEX assembly",
        "Gain/ERP and connector match to verify",
        150,
        "Robu / RF supplier",
        "",
        "Low-gain matched antenna",
        "needs purchase",
    ),
    (
        "Temperature/humidity",
        2,
        "DHT22 / AM2302",
        "3.3V supply; >=2s per sensor",
        180,
        "Robu / Aosong distributor",
        "",
        "AM2302 wired version",
        "needs purchase",
    ),
    (
        "Light sensor",
        2,
        "Analog LDR module",
        "3.3V AO <=3.3V; no lux claim",
        60,
        "Robu",
        "",
        "LDR+resistor divider",
        "needs purchase",
    ),
    (
        "Current monitors",
        13,
        "INA226 carriers, strap access",
        "36V CM max; A0 A1 SDA/SCL straps",
        230,
        "Robu / TI distributor",
        "https://www.ti.com/product/INA226",
        "Custom INA226 carriers",
        "unresolved",
    ),
    (
        "Panel shunts",
        4,
        "0.020ohm Kelvin 1%",
        "1W; low tempco",
        45,
        "Mouser India / element14",
        "",
        "0.02ohm 4terminal rated part",
        "needs purchase",
    ),
    (
        "Other shunts",
        9,
        "0.010ohm Kelvin 1%",
        "1W; low tempco",
        45,
        "Mouser India / element14",
        "",
        "0.01ohm rated part",
        "needs purchase",
    ),
    (
        "Display",
        1,
        "ST7735 128x160 1.8 inch SPI",
        "3.3V logic; panel offset to confirm",
        380,
        "Robu",
        "",
        "ST7735R documented module",
        "needs purchase",
    ),
    (
        "Navigation buttons",
        5,
        "Momentary normally open",
        "Signal rated; 5 exactly",
        12,
        "Local electronics supplier",
        "",
        "Panel mount tactile",
        "needs purchase",
    ),
    (
        "Battery pack",
        1,
        "Protected 1S LiPo 5000mAh target",
        "4.2V CC/CV; >=5A pulse >=3A continuous REQUIRED",
        1400,
        "Battery OEM with signed datasheet",
        "",
        "Lower-power pack only after derating",
        "unresolved",
    ),
    (
        "Solar MPPT charger",
        1,
        "BQ24650 configured 1S assembly",
        "5-28V input IC; 4.2V/0.5A target; NTC",
        1800,
        "TI distributor / custom carrier",
        "https://www.ti.com/product/BQ24650",
        "BQ25798 power path redesign",
        "unresolved",
    ),
    (
        "12V boost stages",
        2,
        "TPS61088 engineered assemblies",
        "2.7-12V IC input; >=6W out at3.35V; test startup",
        750,
        "TI distributor / evaluated assembly",
        "https://www.ti.com/product/TPS61088",
        "TPS61288 after design review",
        "unresolved",
    ),
    (
        "Panel protection channels",
        4,
        "TPS25940L + carrier/passives",
        "2.7-18V; reverse blocking; 1.2A target",
        650,
        "TI / Mouser India",
        "https://www.ti.com/product/TPS25940",
        "LTC4368 + back-to-back FETs",
        "unresolved",
    ),
    (
        "Load protection channels",
        3,
        "Independent current limiter + fuse",
        "12V branch; 0.18/0.6/0.3A firmware limits not hardware ratings",
        220,
        "TI distributor / designed branch",
        "",
        "TPS25940 after low-current range audit",
        "unresolved",
    ),
    (
        "Source master relay KEN",
        1,
        "Omron G2RL-1A DC12 candidate",
        "NO contact; verify DC load endurance",
        200,
        "element14 / Mouser India",
        "https://omronfs.omron.com/en_US/ecb/products/pdf/en-g2rl.pdf",
        "DC-rated NO relay",
        "proposed",
    ),
    (
        "Source transfer KSEL",
        1,
        "Omron G2RL-2 DC12 candidate",
        "DPDT; verify break-before-make timing; use one pole",
        280,
        "element14 / Mouser India",
        "",
        "Documented DC transfer relay",
        "proposed",
    ),
    (
        "Solar converter enable relay KPV",
        1,
        "Omron G2RL-1 DC12 candidate",
        "DC-rated NO path enables solar converter; NC unused and insulated; MPPT has independent protected input",
        220,
        "element14 / Mouser India",
        "",
        "DPDT with spare feedback pole",
        "proposed",
    ),
    (
        "Load relays KL1-3",
        3,
        "Omron G2RL-1A DC12 candidate",
        "12V coils; DC-rated NO contacts",
        180,
        "element14 / Mouser India",
        "",
        "Low-power DC-rated relay",
        "proposed",
    ),
    (
        "Relay driver channels",
        6,
        "3.3V logic N-MOSFET drivers",
        "100R gate;100k pulldown; diode coil clamp",
        65,
        "Mouser India / local",
        "",
        "ULN2003 if3.3V drive verified",
        "needs purchase",
    ),
    (
        "Solar test load",
        1,
        "18ohm 25W resistor + protected MOSFET",
        "8W at12V; guarded hot surface; PB9 control",
        220,
        "element14 / local",
        "",
        "Electronic load with safe EN",
        "needs purchase",
    ),
    (
        "Demonstration loads",
        1,
        "1W lamp + 3W fan + 2W lamp set",
        "12V; motor peak <=6W assumed",
        400,
        "Robu / local",
        "",
        "All resistive first bring-up",
        "proposed",
    ),
    (
        "Branch/source fuses",
        11,
        "DC-rated fuse holders + coordinated fuses",
        "Panel4 cluster2 battery1 bus1 sources2 charger1; ratings pending",
        45,
        "element14 / local",
        "",
        "Resettable eFuse plus sacrificial fuse",
        "unresolved",
    ),
    (
        "Emergency cutoff",
        1,
        "Latching DC disconnect",
        "Open PV/battery load paths; separate safe charge isolator",
        250,
        "Industrial supplier",
        "",
        "DC-rated multipole disconnect",
        "needs purchase",
    ),
    (
        "Reverse-feed devices",
        4,
        "Schottky or ideal diode circuits",
        "Cluster2 source2; >=20V and4A design envelope",
        90,
        "Mouser India",
        "",
        "Low-drop ideal diode module",
        "proposed",
    ),
    (
        "Controller and coil supplies",
        1,
        "Isolated regulated 5V3A +12V1A set",
        "External mains adapters certified; no bare AC",
        650,
        "Reputable adapter supplier",
        "",
        "Lab isolated bench supplies",
        "needs purchase",
    ),
    (
        "Programming interface",
        1,
        "ST-Link V2/V3 + SWD leads",
        "3.3V signal; avoid counterfeit probe",
        400,
        "ST distributor",
        "",
        "CMSIS-DAP supported probe",
        "needs purchase",
    ),
    (
        "Passives and suppression",
        1,
        "NTC dividers bypass bulk TVS flyback set",
        "Motor TVS selection and input margins pending",
        600,
        "Mouser India / local",
        "",
        "See protection calculations",
        "unresolved",
    ),
    (
        "Connectors and wire",
        1,
        "Terminals ferrules harness set",
        "Battery >=5A path; keyed pack connector",
        650,
        "Local electrical supplier",
        "",
        "Rated XT30 path + signal headers",
        "needs purchase",
    ),
    (
        "PCB and enclosure",
        1,
        "Custom carriers + insulated vented enclosure",
        "No high-current solderless breadboard",
        1600,
        "PCB fabricator / local",
        "",
        "DIN terminals on insulating base",
        "needs purchase",
    ),
]
items.append(
    (
        "Charge-supervisor interface",
        1,
        "Logic NMOS + gate network + PV ADC divider",
        "NMOS sink at3.3V;100R/100k gate;47k/10k/100nF ADC",
        60,
        "Authorised component distributor; quote pending",
        "",
        "Equivalent guaranteed low-gate-voltage MOSFET",
        "unresolved",
    )
)
rows = []
for name, qty, model, rating, price, supplier, url, alt, status in items:
    rows.append(
        dict(
            component=name,
            quantity=qty,
            model=model,
            electrical_ratings=rating,
            why_required=name + " subsystem",
            unit_price_INR=price,
            total_price_INR=qty * price,
            source=supplier,
            purchase_url=url,
            alternative=alt,
            compatibility_notes="Engineering estimate, not live quotation; confirm selected module",
            status=status,
            price_check_date="2026-11-09",
            price_evidence="Unverified planning allowance; no price returned by supplier pages",
        )
    )
csvfile("docs/bom/BOM.csv", rows)
write("docs/bom/bom_data.json", json.dumps(rows, indent=2))
total = sum(r["total_price_INR"] for r in rows)
write(
    "docs/bom/SHOPPING_LIST.md",
    f"""# Purchasing plan — 2026-11-09

Base planning allowance INR {total:,.0f}; 20% contingency INR {total * 0.2:,.0f}; total INR {total * 1.2:,.0f}. These are budget estimates, **not verified retailer quotes**, and exclude test instruments. No component is assumed owned. The expanded 13-monitor/protection architecture is substantially more expensive than the original synopsis's approximate INR6,000 target.

Buy development boards, display and sensors first; verify address strap access before purchasing 13 INA modules. Obtain battery OEM discharge/charge/temperature/PCM documentation and charger configuration evidence before buying power components. Reject anonymous BQ24650 modules fixed for 3S batteries. A generic cutoff module is not an MPPT charger. Distributor IC listings are specification references, not ready-to-wire modules. Imported EVMs can greatly exceed the allowance.

Robu Ra02 product listing was reachable but returned no price or stock evidence. Waveshare reference panel specifications are manufacturer-backed; Indian availability remains unconfirmed. Use Robu, Evelta, electronicscomp and authorised TI/ST/Espressif distributors as quotation candidates; purchase URLs are present only where the actual page was verified. Blank URLs deliberately indicate unresolved sourcing. CSV and XLSX retain status and price provenance per line.

Resolve the battery pack, eFuse carrier, converter continuous/peak rating, charger NTC and transfer-contact timing before ordering a production PCB. Do not substitute a 500mAh protected cell for the 5Ah design: it cannot be presumed to deliver the calculated load current.
""",
)
write(
    "docs/bom/POWER_BUDGET.md",
    """# Preliminary power budget

Reference array: four Waveshare16158 nominal6V5W panels. Manufacturer Voc7.2V +/-5%, Isc916mA +/-5%. Provisional design envelope: 12V maximum PV terminal voltage including cold uncertainty, 1.2A/panel operating protection target, 2.4A/cluster,4.8A combiner. Cold-temperature Voc coefficient is not supplied: confirm before construction. 20W STC is not guaranteed field power. Nominal Imp~5/6=0.833A is an estimate because the advertised6V is not independently established Vmp; obtain I-V curve.

Demonstration load assumptions:1W critical,3W fan,2W auxiliary =6W at12V (0.5A). Fan startup assumed6W gives9W simultaneous transient. Battery-side6/(3.35*0.85)=2.107A steady;9/(3.35*0.80)=3.358A startup. A 5A current path margin is a design target, not a proven pack rating. If fan stalls at higher power, reduce loads or choose a rated converter/pack. 1S5Ah nominal energy18.5Wh; usable0.8*18.5*0.85=12.58Wh -> ideal ~2.10h at6W before modelling temperature, aging and voltage drop. Controllers/coils are externally powered and excluded; this is NOT a fully energy-autonomous demonstration.

All four panels feed the shared protected PV_COMB bus. MPPT input remains connected through its own fused/reverse-protected branch. KPV NO enables the solar boost; NC is unused and insulated. Existing BQ24650 input-voltage regulation reduces charging demand under input droop; PB10 MOSFET inhibition pauses charging for probe, transfer or recovery. Charging0.5A at4.2V requires about2.33W PV at90% efficiency; solar loads6W require about6.82W at88%. Combined demand is about9.15W before extra losses, so both functions can operate when available generation and actual hardware limits permit. No fixed panel partition or additional power-path manager is used. Analog loop interaction must be bench-validated.

Solar qualification uses an18ohm/25W guarded resistor on solar boost output, upstream of KSEL:12^2/18=8W,0.667A nominal test demand. PB9 enables a protected MOSFET sink for2s after500ms settling every60s while on battery; charging is inhibited during the test. Measured output>=7.5W and>=11.7V establishes a7.5W capacity bound for90s, not8W. During solar operation,11.4V source droop revokes qualification. The resistor must be guarded and independently protected against unsafe stuck-on heating.

Charging settings are provisional:4.20V/0.5A CC/CV, NTC enabled; pack must explicitly allow these. Firmware3.35V cutoff and8%SOC reserve do not replace pack PCM or independent boost UVLO. 3.55V recovery target must be implemented by qualified hardware UVLO hysteresis. MCU SOC initial50% is an explicitly uncalibrated estimate; calibrate pack capacity and initialSOC before runtime claims.

Each0.02ohm panel shunt dissipates~0.017W at0.916A; cluster0.01ohm~0.034W at1.832A. For eFuse42mohm typical, conduction~0.035W at0.916A; maximum Rds_on and thermal rise must come from actual grade/datasheet. Two0.3V cluster/source diodes at1A total path can lose0.6W; remeasure boost voltage and12V bus after these drops. TPS61088's10A-class SWITCH rating is not10A output capability. Review inductor saturation, current limit, copper and thermals at3.35V input.
""",
)

if __name__ == "__main__":
    print(
        f"Wrote pin maps, {len(addr)} monitor allocations, {len(rows)} BOM lines; budget INR {total * 1.2:,.0f}"
    )
