# Provisional electrical design — NOT RELEASED FOR ASSEMBLY

This is a connection-level design for review, not a fabricated PCB or a verified converter reference layout. Exported SVGs use electrical nets and component functions; module internals remain governed by manufacturer reference circuits. No KiCad PCB/ERC signoff or physical tests are claimed. The editable legacy KiCad overview is a net-level integration drawing, not a transistor-level manufacturing schematic.

## Panel protection and measurement, repeated four times

PV+ -> service fuse FPn -> INA shunt (20mohm Kelvin) -> TPS25940L IN; eFuse OUT -> cluster positive. PV- -> PV_RETURN. eFuse GND ->PV_RETURN; local input/output bypass capacitors and transient suppressor must follow TI layout/stability requirements. EN uses hardware UVLO network plus fail-low MCU inhibit; logic must never drive EN above IC rating. FLT open drain ->10k to3.3V ->S3 fault input. Output enable low at reset. The eFuse integrates opposing MOSFET protection and reverse-current blocking; it is not a lone discrete MOSFET with an unanalysed body diode. Current limiting, ramp/thermal cutoff and reverse blocking operate without software. Design1.2A target above panel Isc tolerance; TI nominal I_LIMIT=89/R_ILIM(kohm), so75kohm gives1.19A. Check guaranteed tolerance, dV/dt capacitor, UVLO/OVP divider, input cap and thermal pad against selected suffix. These unresolved values are deliberately not invented.

At panel short the panel's own Isc can be below hardware limiter threshold. Therefore a trip cannot prove a panel short, and lack of trip cannot prove health. Blocking prevents other panels/battery feeding the branch; fuses protect wiring against other available sources only if enough fault current exists. A fuse may never open on PV-only Isc. FLT indicates a protection event without uniquely identifying its cause. Hardware protection does not guarantee interruption if the eFuse fails short; add branch fuse and service disconnect, test reverse blocking at the real operating voltage, and keep stored-energy fault sources isolated.

Each pair connects in parallel after branch protection. ClusterA/B have their own10mohm monitor, fuse/disconnect and blocking device before PV_COMB. Blocking devices are sized for cluster current, drop and reverse voltage. They prevent inter-cluster backfeed and charger/converter leakage. Firmware compares per-panel outputs at comparable irradiance; low current can mean shading/open circuit, not a uniquely diagnosed fault. A detached sensor must not be called a detached panel. Unexpected current after EN low indicates switch/wiring/sensor ambiguity; latch and stop automated recovery.

## PV sharing and charger - Revision 2

All four protected panels combine at PV_COMB. MPPT input remains connected through its own fused/reverse-protected branch. KPV COM=PV_COMB; NO=solar converter input; NC unused and insulated. The two inputs may operate together only with charger input-voltage regulation and verified converter limits. This is coordinated sharing, not an unanalysed parallel connection. No fixed panel split is used.

BQ24650 input-voltage regulation reduces charging demand under input droop. A small logic N-MOSFET from MPPSET pin2 to charger signal GND, gated by PB10 through100ohm with100kohm gate pulldown, requests charge disable. Existing MPPSET divider resumes when released; battery feedback and NTC remain untouched. PB1 ADC1_IN9 senses PV through47kohm/10kohm plus100nF filtering. This is a provisional interface, not a manufacturing release.

Current provisional thresholds assume a physically configured5.5V charger input-regulation target: inhibit below5.4V; allow after>=5.8V for5s and15s dropout hold. Inhibit for source probing/transfer. Solar qualification is7.5W measured at>=11.7V using a nominal8W test load; capacity is recorded as7.5W, not8W. Match thresholds to actual PV/converter behaviour and validate weak-source stability, current limits, UVLO, reverse current and thermals. See docs/architecture/REVISION_2.md (repository docs folder) for the complete rationale.

Charger target4.20V/0.5A is provisional until pack approval. Verify actual1S assembly, TS/NTC, CC/CV, termination and reverse paths. Protected PACK+ -> fuse -> signed battery shunt -> BAT_SYS; charger BAT and battery boost connect at BAT_SYS. All returns use protected PACK-, never bare cell terminals. BMS does not replace charger.

## Conversion and source transfer

TPS61088-based solar and battery boost assemblies produce nominal12V sources. Each needs independent UVLO, input current limit, output current limit/short protection, thermal design and reverse-output path evaluation. Some synchronous converters conduct through body paths when disabled; do not use EN as galvanic isolation. Battery boost target minimum3.35V operational cutoff with hysteresis from hardware. Specify measured6W continuous/9W startup at actual pack voltage; switch-current marketing is insufficient.

Solar source -> reverse-feed protection ->KSEL NC. Battery source ->reverse-feed protection ->KSEL NO. KSEL COM ->KEN NO ->bus INA ->BUS12. KEN COM is selector common, NO is bus; unused NC insulated. KSEL second pole can provide auxiliary feedback but it is not wired in this firmware. BBM must be confirmed by relay data and bench timing. Do not parallel poles without manufacturer approval.

| KEN coil PA8 | KSEL coil PA9 | Bus connection | Meaning |
|---|---|---|---|
|0|0|Disconnected; selector rests solar|Power-off / standby|
|0|1|Disconnected; selector rests battery|Transfer deadtime|
|1|0|Solar only|Solar active|
|1|1|Battery only|Battery active|

No normal binary state directly parallels sources. Invalid physical states include welded contacts, make-before-break replacement, wiring error or failed master: reverse-feed devices and fuses mitigate but do not establish safety. With no contact feedback firmware cannot certify relay actuation; compare bus/source voltage and load current for gross mismatch and require inspection. Controller opens master/load relays, changes selector with master open, waits>=250ms (verify actual relay release/bounce), revalidates source, closes master, restores one load every2s. Source dwell15s; solar recovery10s; emergency dropout bypasses dwell. Gate/coil driver outputs require100k pulldowns; do not rely on floating MCU reset pins.

## Load branches and drive

BUS12 -> independent current limiter + fuse -> INA10mohm -> KL NO contact ->load+. Load- returns to star power ground. Place appropriately rated diode across motor for one-direction motor (cathode+), and TVS/snubber appropriate to motor/relay release requirements. Verify stall current, inrush and contact DC inductive rating. Do not assume resistive8A30VDC rating equals motor rating. Firmware limits0.18/0.6/0.3A are additional diagnostic thresholds, not hardware limiter settings. Hardware branch limits must allow validated startup yet interrupt unsafe wiring faults.

Six coils use low-side3.3V logic MOSFET drivers: GPIO ->100ohm gate;100k gate-ground; source ground; drain coil-; coil+ external12V. Flyback diode cathode12V/anode drain, rated for coil current and clamp energy. Verify Rds_on at2.5/3.3V, Vds margin and relay release delay with clamp. No MCU GPIO directly drives a coil. Qualification sink PB9 uses a separately protected gate driver/18ohm25W resistor upstream of source transfer. Hot resistor guarded and derated in enclosure.

Use an independent DC emergency disconnect and separate maintenance isolation for battery and PV charging. It must remove energy from load bus even if STM32 output sticks. Star power returns, short high-current loops, separate analog Kelvin pairs, decoupled radio3.3V supply, RF antenna clearance, insulated terminals and strain relief are mandatory design considerations. A common DC ground is intentional; never join multiple mains-referenced supplies without assessing earth paths. This design uses certified isolated adapters, no bare AC construction.
