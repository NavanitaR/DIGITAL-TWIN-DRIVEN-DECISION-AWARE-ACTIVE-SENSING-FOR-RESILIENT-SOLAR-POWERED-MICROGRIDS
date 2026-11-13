# Controller and fault state machines

Source FSM has OFF, TRANSFER_PENDING, SOLAR and BATTERY. INIT keeps relays off until seven valid local monitors arrive. Invalid/missing monitor ->FAULT with master and all loads off. Valid data returns to source evaluation; local power restoration still uses deadtime. Battery eligible iffV>=3.35 andSOC>0.08. Solar eligible after measured qualification7.5W and10s recovery; active solar remains eligible while capacity/droop condition permits. Off->pending->target after250ms. Any target invalidation cancels pending.15s dwell avoids chatter; unavailable source and operator shutdown bypass dwell. KPV enables the solar input during target/active/probe; MPPT remains on a separate protected input branch. PB10 inhibits charging during probe/transition/droop; release requires sustained PV recovery.

Load FSM uses priority1,2,3 with power1,3,2W. Solar budget=qualified capacity-0.5W reserve. Battery budget6W above25%SOC,4W above12%,1.2W above8%,0 below cutoff. Iterate shed3,2,1 until sum<=budget; restore1,2,3 at most one every2s. Individual firmware overcurrent latches inhibition; automatic-mode command cannot clear hardware fault latch. Manual enable requests remove only operator inhibit and still pass budget and hardware checks. Bus remains unserved during break-before-make; no hold-up ride-through is promised.

Top-level display states INIT,STANDBY,SOLAR_ACTIVE,BATTERY_ACTIVE,LOAD_SHEDDING,FAULT,RECOVERY,SAFE_SHUTDOWN reflect those FSMs. STANDBY is a named reserved display state; current implementation progresses from INIT to SAFE_SHUTDOWN or RECOVERY rather than lingering in STANDBY. Fault state is an invalid local monitor; source loss normally enters RECOVERY/SAFE_SHUTDOWN. No relay feedback or charger-status GPIO is implemented, so those states cannot be inferred with certainty from drive levels.

Panel policy: boot ISOLATED -> healthy readings + confirmed reconnect ->CONNECTED. Low contribution sustained30s relative to a productive sibling ->SUSPECT_LOW_OUTPUT, report but do not isolate solely for shading. Negative current<-30mA ->REVERSE_SUSPECT and isolate. Missing/invalid branch sensor ->SENSOR_FAULT and isolate. Hardware FLT ->PROTECTION_TRIP and isolate. Current magnitude>30mA with EN low ->ISOLATION_MISMATCH. Electrical/sensor fault latches require inspection and local reset/clear; no automatic retry of suspected short/reverse/failed isolation. Shade can recover without relay reconnection because it is not automatically isolated. An open panel and heavy shade remain ambiguous without additional irradiance/Voc tests; report ambiguity, not fabricated diagnosis.

Reset loses volatile fault history: independent hardware and host SQLite retain their own information but are not an MCU persistent fault log. Keep all branch enables low at every reboot and require recommissioned reconnect. Do not use reboot as an automatic fault-clear-and-reconnect mechanism. Settings are compile-time except report interval in RAM and gateway Wi-Fi NVS; threshold/priority persistence and arbitrary UI edits are deliberately constrained to validated constants in this version.

## Charge-inhibit supervisor

The existing BQ24650 input-voltage-regulation loop continuously reduces charger demand under PV droop. The STM32 supervisor in `firmware/shared/charge_control.h` adds slower inhibition through PB10; it is neither an MPPT algorithm nor independent electrical protection.

| Condition | PB10 / MOSFET action | Recovery rule |
|---|---|---|
| Firmware initial state | Inhibit requested | Wait for valid local sensing and recovery |
| Invalid ADC or critical sensing, actuation fault, PV below5.4V | Inhibit; restart timers | No release while condition persists |
| Solar proof test, pending transfer, or active solar below11.7V | Inhibit; restart timers | Finish transition and regain PV headroom |
| Inhibited, PV at least5.8V | Start sustained-recovery timer | Release only after5s recovery and15s since last dropout |
| Charging permitted | Release MOSFET; original MPPSET divider governs | Hardware DPM still reduces charge current |
| MCU reset or unpowered GPIO | Passive gate pulldown releases inhibit | Charger/NTC/pack protection operate independently |

These thresholds assume a provisional5.5V physical charger input-regulation setting and require calibration/bench validation against actual modules. KPV remains solely a solar-converter input enable. MPPT is never transferred to its NC contact. A nominal8W resistor test qualifies only the measured7.5W bound used by the source controller.
