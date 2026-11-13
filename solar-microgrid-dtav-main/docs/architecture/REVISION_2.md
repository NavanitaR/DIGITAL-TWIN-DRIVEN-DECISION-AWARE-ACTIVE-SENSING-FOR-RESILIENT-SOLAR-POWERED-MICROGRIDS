# Revision 2: one shared PV array, load-priority MPPT charging

This revision replaces the previous exclusive allocation. There is no fixed panel split. Both protected clusters combine onto PV_COMB; the solar converter and MPPT charger can operate simultaneously from that bus when sufficient power exists.

The earlier conclusion that these inputs must always be time-divided was too restrictive. BQ24650 input-voltage regulation reduces charge demand when a system load plus charging exceed the source capability (TI datasheet section8.3.2). This design coordinates that existing function, independent converter limits and a MOSFET inhibit. It is not a claim that arbitrary unidentified converter boards can be paralleled without validation.

## Actual connections

1. Four individually protected MOSFET panel branches form two parallel clusters. Cluster monitors, fuses and reverse-blocking paths feed PV_COMB.
2. PV_COMB feeds the MPPT input through its own fused/reverse-protected branch, continuously.
3. PV_COMB -> KPV COM; KPV NO -> solar boost input. KPV NC is unused and insulated. KPV enables direct solar conversion; it no longer transfers PV away from charging.
4. Solar12 and battery12 remain separate protected sources into KSEL NC/NO. KSEL COM -> KEN NO master -> monitored bus -> three protected load branches.
5. A small logic N-MOSFET pulls BQ24650 MPPSET pin2 low: drain at MPPSET, source at charger signal GND, gate from STM32 PB10 through100ohm,100kohm gate-source pulldown. High PB10 requests charge inhibition. Release restores the original input-regulation divider. Do not drive MPPSET high from a GPIO or alter battery CC/CV feedback.
6. PV_COMB ->47kohm upper/10kohm lower ADC divider -> PB1 ADC1_IN9;100nF across lower resistor. Scale5.7; calibrate actual VDDA and resistor ratio. PB1 was unused; LoRa IRQ remains polled. This divider measures voltage, not independent protection.

There are still six relays: KPV,KSEL,KEN,KL1-3. No additional power-path manager IC is required. MOSFETs provide inhibition, isolation and coil driving. The existing MPPT charger, converters, sensing and independent protection remain required; bare MOSFETs and relays cannot replace a safe charger or regulated converter.

## Coordination and provisional thresholds

Configure charger input regulation to the measured panel operating point after blocking/wiring losses. The current firmware uses a provisional5.5V target: inhibit below5.4V; reallow only after PV>=5.8V for5s and at least15s since a dropout. Configure the solar converter's hardware input current limit/UVLO independently; a5.0V input cutoff is a commissioning target, not a verified module rating. Match these values to actual modules and measured PV I-V behaviour.

Inhibit charging during the solar proof test and source transfer. Close KPV, settle the converter, enable the protected18ohm test load, then measure output. At12V the resistor requests8W. Output>=7.5W at>=11.7V qualifies a7.5W capacity bound, not8W. The controller permits6W loads with reserve, uses10s solar recovery, opens KEN before changing KSEL and waits>=250ms before revalidation. Charging can resume after stable PV recovery; the MPPT hardware loop then reduces charge demand as necessary. If loads exceed solar capability even at zero charging, transfer to battery or shed loads.

| KPV PB8 | Inhibit PB10 | Paths |
|---|---|---|
|0|0|MPPT allowed; solar converter input disconnected|
|0|1|MPPT inhibited; solar converter input disconnected|
|1|0|Both inputs connected; charger DPM regulates its demand|
|1|1|Solar converter connected; charging inhibited for probe/transition/recovery|

PB10's passive pulldown permits the independently configured MPPT during MCU reset; KPV,KEN and loads default open. Charger CC/CV,NTC and pack protection must therefore already be correct without firmware.

## Energy accounting

P_direct_input=P_served/eta_solar when solar selected. P_surplus=max(0,P_PV-P_direct_input). P_charge=min(eta_charge*P_surplus,V_bat*I_charge_limit), subject to charging state, temperature and inhibit. Net pack current is positive for discharge and includes charger and battery-converter demand.

At20W PV and6W solar load, direct input at88% efficiency is6.82W. Charging4.2V0.5A requires about2.33W input at90% efficiency: combined demand~9.15W before extra wiring losses. At8W PV, only1.18W input remains after the same load; charging falls to about0.25A at4.2V. Below6.82W, full6W service plus charging cannot be promised. No switching circuit removes losses or creates missing energy.

## Required physical verification

Sweep source impedance/irradiance and load steps while observing PV voltage, solar12 voltage, charger current and pack current. A constant-power boost can destabilize a weak PV source; DPM alone is not proof of system stability. Verify converter current limiting, startup, UVLO hysteresis, inhibit/recovery, reverse feed, relay timing and charger temperature behaviour. Actual power-module and pack specifications remain construction gates.

Source: TI BQ24650 datasheet, pin2 and input-voltage-regulation section: https://www.ti.com/lit/ds/symlink/bq24650.pdf . This revision is reflected in both current PDFs, the wiring tables and their generators.
