# Autonomous Solar Microgrid with Digital Twin and DTAV

Three-controller educational microgrid: ESP32-S3 distributed sensing/branch isolation, STM32F411 HAL local power control/TFT, ESP32-C3 UART/MQTT bridge, Python twin and React dashboard. Start with [START_HERE.md](START_HERE.md).

**Current electrical revision:** [shared-PV design](docs/architecture/REVISION_2.md). Read the [working guide](docs/WORKING_GUIDE.pdf) for the complete explanation. Both the working guide and technical report use this same design. All four panels remain available; the MPPT and solar converter can operate together under the specified coordination and energy limits.

**Status:** buildable software prototype and provisional hardware design. No physical commissioning or electrical safety validation is claimed. Read [assumptions](docs/architecture/ASSUMPTIONS.md), [power design](hardware/schematics/POWER_DESIGN.md), [commissioning](docs/safety/COMMISSIONING.md) and [validation evidence](docs/testing/VALIDATION.md) before assembly.

The [documentation index](docs/INDEX.md) lists the current reference chapters. Both PDFs, the BOM and all generated wiring diagrams use the shared-PV design.

## Run locally

Requires Python3.12+, Node22+ and npm. Simulation needs no devices or MQTT broker.

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -r backend/requirements.txt
.venv/Scripts/python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

In a second terminal:

```powershell
cd frontend
npm.cmd ci
npm.cmd run dev
```

Open http://127.0.0.1:5173. `npm.cmd` avoids PowerShell's script-wrapper policy. Linux/macOS use `.venv/bin/python` and `npm`. API documentation: http://127.0.0.1:8000/docs. WebSocket `/ws`, CSV `/api/export.csv`. Backend starts in simulation. Hardware mode never substitutes synthetic measurements; replay is read-only.

`scripts/setup.ps1`, `scripts/run-backend.ps1`, `scripts/run-dashboard.ps1` provide Windows shortcuts. MQTT hardware integration requires Mosquitto and [gateway provisioning/flashing](docs/firmware/BUILD_FLASH.md). Do not expose the local API or unauthenticated broker to untrusted networks.

## Test and evaluate

```powershell
.venv/Scripts/python -m pip install -r scripts/requirements-docs.txt
.venv/Scripts/python -m pytest -q
.venv/Scripts/python scripts/experiment.py --seeds 5 --seconds 300
cd frontend
npm.cmd test
npm.cmd run build
```

Firmware, from repository root:

```powershell
.venv/Scripts/python -m pip install platformio==6.2.0
.venv/Scripts/python -m platformio run -d firmware/esp32-s3-sensor-node
.venv/Scripts/python -m platformio run -d firmware/stm32-central-controller
.venv/Scripts/python -m platformio run -d firmware/esp32-c3-wifi-gateway
```

Append `-t upload` to flash; ESP upload may need `--upload-port COMx`; STM32 uses ST-Link. Never flash or reconnect an uncommissioned power stage with a real battery attached. The S3 boots with all panels inhibited. Five-button controls and all manual commands retain local safety checks.

## Deliverables

- [Electrical connection diagrams](hardware/schematics) and [editable KiCad integration map](hardware/kicad/integration.sch). These are review-level interfaces, not a PCB manufacturing release.
- [Complete controller signal table](hardware/wiring/controller_wiring.csv), [pin maps](hardware/pinouts/PIN_MAPS.md), [13-monitor address/shunt allocation](hardware/wiring/ina226_addresses.csv).
- [BOM.xlsx](docs/bom/BOM.xlsx), [BOM.csv](docs/bom/BOM.csv), [purchasing plan](docs/bom/SHOPPING_LIST.md), [power calculations](docs/bom/POWER_BUDGET.md). INR32,376 planning allowance including20% contingency; prices are unverified allowances, not supplier quotes.
- [Engineering report](docs/TECHNICAL_REPORT.pdf), [firmware state machines](docs/firmware/STATE_MACHINES.md), [wire protocol](docs/protocols/WIRE_V1.md), [DTAV equations and limits](docs/research/DTAV.md), [viva guide](docs/VIVA.md).
- [Seeded experiment outputs](simulation/results), software tests and CI.

## Engineering boundaries

All four panels feed one protected PV bus. The MPPT input stays connected through its own protected branch; KPV NO enables the solar converter independently and KPV NC is insulated. BQ24650 input regulation reduces charge demand as loads consume PV power; PB10 drives a signal MOSFET to inhibit charging during probe/transfer/droop. PB1 senses PV voltage. No fixed panel split or exclusive input transfer remains. See [Revision 2](docs/architecture/REVISION_2.md) for coordination, wiring and commissioning requirements.

Actual panel coldVoc, protected pack ratings, charger configuration/NTC, converter thermals/current limits, relay DC timing/endurance and purchased-board pinouts remain commissioning gates. The model uses transparent simplified physics. DTAV uses approximate Bayesian EVSI; comparative improvements and novelty are research hypotheses, not asserted results. See [known limitations](docs/LIMITATIONS.md) for precise scope.

Original source code and authored documentation use MIT licence. Manufacturer datasheets, frameworks, libraries and fonts retain their own licences; no ownership over those is claimed.

## Regenerate the documentation

Markdown chapters are the editable source of truth; the indexer does not overwrite them. Hardware inputs live in `scripts/generate_hardware.py` and `scripts/wiring_details.py`.

```powershell
.venv/Scripts/python -m pip install -r scripts/requirements-docs.txt
.venv/Scripts/python scripts/regenerate_design.py
```

The workbook builder uses the provided `@oai/artifact-tool` Node runtime. The pipeline detects the local Codex runtime or accepts `ARTIFACT_TOOL_NODE_MODULES` pointing to its `node_modules` directory. Outside that runtime, `--skip-workbook` explicitly rebuilds only the other artifacts; use it only when BOM inputs are unchanged. CI checks the committed workbook against CSV and tests regenerated routes so old KPV wiring cannot silently return.
