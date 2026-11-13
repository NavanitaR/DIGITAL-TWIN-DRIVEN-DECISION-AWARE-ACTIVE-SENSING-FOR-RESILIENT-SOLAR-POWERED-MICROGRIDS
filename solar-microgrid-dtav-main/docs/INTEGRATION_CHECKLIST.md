# Final integration checklist

- [x] Three firmware projects and shared binary protocol compile in available environment.
- [x] Local backend, database, simulation/replay/hardware mode boundaries and WebSocket API execute.
- [x] Frontend type/build/component checks pass; local HTTP preview serves.
- [x] Sensing strategies, approximate EVSI and safety-limited return commands implemented.
- [x] Seeded scenarios export actual computed results and comparative charts.
- [x] Wiring, shunts/addresses, protection assumptions, budget and commissioning procedures documented.
- [x] Shared-PV descriptions, BOM, GPIO tables, wiring, KiCad integration map and both PDF generators agree on the current topology.
- [x] Regression checks prevent regenerators from restoring the previous KPV routing and compare the committed workbook with CSV.
- [ ] Exact purchased module/pack datasheets and rated assembly schematics confirmed.
- [ ] Charger/boost/branch carrier schematics completed and reviewed; PCB/ERC release approved.
- [ ] Physical protection, UVLO, NTC, reverse current and DC contact tests completed.
- [ ] Hardware firmware flashing, calibration and complete RF/UART/MQTT loop verified.
- [ ] Browser visual QA completed on desktop and mobile viewport.
- [ ] Experimental research novelty and performance hypotheses evaluated with calibrated hardware.

GitHub private visibility and remote commit verification are reported in the final delivery. They do not close physical commissioning items.
