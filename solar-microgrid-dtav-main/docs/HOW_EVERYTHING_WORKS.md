# How every part of the solar microgrid works

This guide follows the energy from sunlight to the loads, then follows the information from sensors to the digital twin and back. Revision2 keeps all four panels together. It does not reserve half the panels for charging.

## 1. The complete power path

Four panels feed two protected parallel clusters. Both clusters join the protected PV bus. One branch goes to the MPPT charger; another passes through KPV to the solar12V converter. The battery has a separate12V converter. KSEL chooses one regulated12V source, KEN connects or disconnects the bus, and three load relays distribute power.

The solar converter receives first claim on available PV power while solar loads are active. The charger reduces its demand through its existing input-regulation function. STM32 can also inhibit charging with a small MOSFET while testing a source, transferring relays or recovering from a voltage dip. Both functions can operate together when enough power exists.

## 2. Solar panels and the two clusters

PV1 and PV2 form Cluster A; PV3 and PV4 form Cluster B. Parallel wiring adds delivered current at approximately the same voltage. Four6V panels in parallel do not create24V. A panel's advertised voltage is not a fixed output: light, temperature, load and shading change its operating point.

Each panel has its own monitored, protected isolation branch before the cluster join. Each cluster is also measured and reverse-protected before joining PV_COMB. This lets a suspected branch be disconnected while other branches remain available. Low output alone cannot reliably distinguish shade, an open wire and every electrical fault.

## 3. What each MOSFET does

A MOSFET is an electrically controlled switch. Gate-to-source voltage controls conduction. A threshold-voltage specification is not a guarantee of low resistance at3.3V; select a device with suitable guaranteed on-resistance and thermal capability at the actual drive voltage.

A single MOSFET contains a body diode, so gate OFF may still permit current in one direction. Back-to-back MOSFETs can block both directions when off with appropriate gate drive. When both are on, current can flow in either direction: the pair is not automatically an ideal diode or a short-circuit limiter. Independent protection remains necessary. The existing protected MOSFET-switch candidate implements that protection; an unprotected discrete substitute is not equivalent.

Small low-side MOSFETs drive relay coils. GPIO drives the gate; the transistor sinks coil current. Gate resistors/pulldowns define switching and reset behaviour. Flyback clamps handle stored coil energy. The new MPPSET MOSFET carries only signal-divider current: it tells the existing charger to pause; it never regulates battery charging current itself.

## 4. MPPT, battery charging and the new inhibit

MPPT chooses a useful PV operating point. CC/CV charging limits battery current and then final voltage. These are related but different functions. The selected BQ24650 uses programmable input-voltage regulation as its MPPT approximation; this existing function reduces charge demand under input droop.

The provisional pack target is1S LiPo,4.20V charging and0.5A maximum, only if the actual pack permits those settings. Configure the real charger module and its thermistor correctly. A generic cutoff board is not a charger, and a3S-configured module cannot be used unchanged for1S.

STM32 PB10 drives a small N-MOSFET whose drain pulls MPPSET pin2 below the manufacturer's disable threshold. Releasing it restores the original divider. The CC/CV feedback remains untouched. Charging is inhibited for a source test, source transition or PV dip, and released after sustained recovery. Hardware DPM supplies continuous regulation; this slower software supervisor is not a replacement MPPT algorithm.

## 5. Battery protection and the battery boost

A protected battery includes specified pack-level protections. It does not automatically contain a proper solar charger. Conversely, a charger does not replace pack protection, wiring fuses or a manual disconnect. Connect to protected PACK terminals; never bypass protection through bare cell terminals.

The battery boost converts roughly3.7V to regulated12V.6W output at3.35V and85% efficiency requires about2.11A input. Startup can require more. Battery capacity, continuous/pulse current, converter input limits, connectors and wire must all support the measured demand.

Signed battery current measures the net result. A charger may be active while the battery is still discharging if loads draw more than the charger supplies. SOC is estimated by integrating that signed current and calibrating capacity/initial state; voltage alone is not an exact fuel gauge.

## 6. Why all six relays are still needed

KPV enables the solar converter input; the MPPT now has its own continuously connected protected branch. KPV NC is unused and insulated. KSEL selects regulated solar12 or battery12. KEN is the normally-open master bus disconnect. KL1,KL2 andKL3 switch the individual loads.

During transfer, open KEN, change the break-before-make selector, wait the validated release/bounce interval, recheck the source and close KEN. Then restore loads in stages. There is no claim of uninterrupted bus voltage. DC contact and motor/inrush ratings matter; an AC resistive rating is insufficient evidence.

## 7. What happens throughout a day

At startup the load bus and panel enables begin off while sensors are checked. The independently configured charger can operate without the laptop. To qualify direct solar, inhibit charging, close KPV, settle the converter and apply a protected resistor test load. The measured proof establishes a conservative capacity bound.

In strong sun the array powers loads and charges the battery together. As a cloud arrives, DPM reduces charging demand. If necessary STM32 inhibits charging; if solar still cannot serve the permitted load, it transfers to battery or sheds loads. At night the battery supports priority loads until voltage/reserve limits require shutdown.

A full battery must not be overcharged just to consume surplus solar. Its charger tapers/terminates independently. Faulted branches stay inhibited according to their recovery policy. No relay/MOSFET arrangement can sustain both loads and charging when the energy balance is negative.

## 8. The three loads

The demonstration assumptions are1W critical lighting,3W fan and2W auxiliary lighting. Each branch has its own monitor, relay and independent protection. The controller sheds auxiliary first, then fan, then critical only if necessary. It restores priority loads one at a time to reduce startup surges.

A motor is not a resistor. Its startup/stall current and inductive energy must be measured, with suitable suppression and DC contact ratings. Manual ON commands still pass availability, reserve and fault checks. Buttons and dashboard cannot bypass hardware protection.

## 9. Every sensor

The S3 has six INA226 devices: two cluster monitors and four panel monitors. STM32 has seven: battery, main bus, two regulated sources and three loads. Each bus needs unique addresses; separate buses may reuse addresses. Some inexpensive breakout boards do not expose all address straps.

An INA226 measures a shunt voltage; current is that voltage divided by shunt resistance. Power is bus voltage times signed current. Kelvin wiring, polarity, zero and gain calibration are essential. Two DHT22 sensors measure temperature/humidity. Two LDR modules give relative light, not calibrated lux. Missing data must remain invalid, not zero.

PB1 adds direct PV-bus voltage sensing through a47kohm/10kohm divider and100nF filter. The nominal scale is5.7, using calibrated MCU reference voltage. This signal lets the central controller supervise charging locally; LoRa is not needed for that response.

## 10. The three brains

ESP32-S3 handles distributed PV/environment sensing, branch inhibition, health and LoRa. STM32F411 owns local source/load control, charge inhibition, central measurements, TFT and five buttons. ESP32-C3 bridges UART to Wi-Fi/MQTT; it is not the sole power controller.

All interfaces are3.3V logic. Exact purchased-board revisions determine connector positions, flash configuration and display details. STM32 is programmed over SWD because this pin map uses its USB pins for load drivers. External isolated supplies power controllers/coils; the prototype is autonomous in control, not proven fully self-powered.

## 11. Communication and the operator interface

Ra02 LoRa connects S3 and STM32 with bounded binary packets, sequence numbers, uptime and CRC. Half-duplex scheduling and bounded retries prevent unlimited transmission. CRC detects corruption; it does not authenticate an attacker. Actual RF power, antenna ERP and current Indian rules must be checked.

UART packets use COBS plus a delimiter. C3 forwards them to MQTT with bounded buffering and expiry. Python accepts real packets in hardware mode, logs them in SQLite and streams state over WebSocket. A published command is not proof of actuation: ACK and subsequent measured response are separate evidence.

The TFT has overview, solar, battery, loads, communication, faults and settings pages. Five buttons navigate/select/confirm/cancel; hold SELECT returns to automatic mode. Fault acknowledgement does not reconnect a latched fault. A separate physical emergency cutoff is still required.

## 12. Digital twin and DTAV

The twin predicts generation, converter losses, battery state, loads and unserved energy with explicit simplified equations. Simulation uses synthetic devices; hardware uses real packets; replay is read-only. Estimates such as SOC and runtime must stay distinguishable from measurements.

DTAV asks whether a fresh measurement could change a permitted decision. It estimates uncertainty, compares candidate service bundles, evaluates expected information value against communication cost, requests useful data, updates the estimate and reevaluates the action. Local deterministic checks remain final authority.

Continuous, periodic and event-triggered reporting are baselines. Compare packets, estimation error, detection/restoration delay and unserved energy under the same scenarios. No universal improvement or novelty is claimed. Essential local safety monitoring never turns off just to save radio messages.

## 13. Practical numbers and next steps

With20W PV potential,6W load needs6/0.88=6.82W input at the assumed solar efficiency. Charging4.2V0.5A needs2.33W input at90% efficiency. Their combined9.15W demand can fit within the available input. With only8W PV, charge current must fall to roughly0.25A at4.2V before additional losses. With5W PV, the full6W load cannot remain solar-powered even with charging stopped.

Start software in simulation, inspect the dashboard, run tests and compare actual experiment outputs. For hardware, begin with current-limited bench supplies and resistor loads. Verify CC/CV,NTC, input regulation, reverse feed, current limits, relay timing, dropout/recovery and thermals before adding a real battery. Scope load steps and weak-source behaviour: software tests cannot prove analog stability.

The following technical chapters give exact provisional wiring, pin assignments, address straps, state machines, protocol, equations, purchasing assumptions and commissioning gates. Revision2 is authoritative for the new shared-PV topology; both current PDFs and generated wiring reflect this shared-PV design.
