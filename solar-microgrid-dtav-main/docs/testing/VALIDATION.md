# Software validation - 2026-11-09

Executed on Windows with Python3.12.4, Node24.22.1, GCC (MinGW), PlatformIO6.2.0. Machine-readable commands, exit codes and output tails are in `simulation/results/validation.json`; use `python scripts/validate.py` to reproduce. Initial compilation failures were fixed before the final successful run; no failed run is represented as passing.

| Check | Observed outcome |
|---|---|
| Backend pytest |30 passed; one upstream Starlette/httpx deprecation warning |
| Native C |Sensor conversions, CRC/COBS, transfer deadtime, invalid command and low-battery assertions passed |
| ESP32-S3 |PlatformIO Arduino build passed; image generated |
| STM32F411CE |PlatformIO STM32Cube HAL C build passed; image generated |
| ESP32-C3 |PlatformIO Arduino build passed; image generated |
| Frontend |2 component/format tests passed; TypeScript and Vite production build passed |
| npm audit |0 vulnerabilities after upgrading Vitest |
| Application startup |Uvicorn started; /api/state returned simulated state; Vite HTTP200 at127.0.0.1:5173 |
| Browser visual QA |Blocked: browser-access host unavailable; no screenshot/UI navigation pass claimed |
| BOM |Formula results26980+5396=32376INR checked; no cached formula errors; preview visually reviewed |
| Reports |Both PDFs rebuilt from current revision-2 sources and rendered for visual layout review |
| Diagrams/tables |10SVG XML documents;13 unique per-bus monitor assignments;GPIO and BOM consistency checks |
| Research |5 paired seeds x4 strategies x300s; CSV,JSON,PNG,SVG exported; no universal DTAV improvement claimed |

The Vite build reports a nonfatal bundle-size advisory. Backend tests warn about a future test-client transport change; runtime/API tests pass. Neither warning establishes a physical safety issue.

Protocol integration uses encoded binary/COBS logical hops, bidirectional requests and ACKs. It is not a real RF/MQTT hardware-loop measurement. Source/panel/load fault tests are software models. No boards were flashed, no battery charged, no relay timing measured, no antenna ERP verified and no physical short/overload experiment performed. Every commissioning gate in `docs/safety/COMMISSIONING.md` remains open.

Revision2 includes native charge-inhibit recovery/probe/invalid-value checks, shared-surplus/actual-supervisor-packet tests and documentation consistency/regeneration tests. WORKING_GUIDE.pdf and TECHNICAL_REPORT.pdf both describe the current shared-PV design; neither is retained as a historical exclusive-allocation report.
