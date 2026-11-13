# System architecture and requirements

The hardware boundary is a low-voltage educational DC prototype. No grid interconnection or exposed mains is designed. C/C++ devices retain local monitoring when upstream communications fail. Laptop decisions are supervisory and can only reduce local authority, never bypass hardware protection.

| Layer | Implementation | Failure behaviour |
|---|---|---|
| Branch protection | Four TPS25940L-based eFuse channels, branch fuses | Hardware protection independent of I2C |
| Sensor | S3, six INA226, two DHT22, two relative-light ADCs | Fail-low enables; missing branch monitor inhibits branch |
| Real-time control | F411 HAL C, seven INA226, three load relays, source transfer, PV allocation | Invalid local critical sensors open master and loads |
| Transport | Ra02 SPI polling; C3 UART/COBS and MQTT | Bounded queues/retries; no safety dependency |
| Host | FastAPI, SQLite, NumPy physical model, EVSI | Never required for cutoff or relay operation |
| UI | React19, TypeScript, Vite, Tailwind4, Recharts | Unknown data shown as unknown; stale controls disabled |

Power wiring: four protected panel branches form two monitored clusters. Both protected cluster outputs combine at PV_COMB. MPPT remains on its own protected input branch. KPV COM=PV_COMB; NO=solar boost input; NC insulated. Existing charger DPM and PB10 inhibition coordinate simultaneous load supply and charging; PB1 senses PV locally. KSEL/KEN and three protected load branches retain their source-selection topology.

Functional requirements map to code: protocol.h/protocol.py define wire format; control.h/control.py enforce source deadtime and priorities; sensor-node main.cpp owns acquisition and inhibition; central main.c owns HAL devices, TFT/buttons and local decisions; gateway main.cpp owns bounded forwarding; engine.py routes mode-specific data/commands; twin.py defines synthetic plant; dtav.py defines sensing strategies. Software tests cannot establish contact timing, fault interruption or LiPo safety.

Modes are separate engine instances on each change. Hardware uses only parsed radio/central packets. Replay snapshots are read-only and never publish commands. Simulation commands traverse mock binary/COBS hops and receive explicit simulated acknowledgements. Host switching clears pending commands and model state; already delivered hardware commands cannot be undone by changing host mode. Use physical cutoff for emergency isolation.

Local defaults: branch enables low, KEN open, loads open, KSEL at solar NC and KPV solar-enable NO open with NC insulated. The MPPT input remains on its own protected branch. PB10's passive gate pulldown releases the charge-inhibit MOSFET during MCU reset, so independently configured charging may continue. Firmware initially requests inhibition until valid local sensing and recovery qualify release. Charger CC/CV, NTC and pack protection must be correct without firmware. Load-bus emergency isolation and battery/charging service isolation are separate functions.
