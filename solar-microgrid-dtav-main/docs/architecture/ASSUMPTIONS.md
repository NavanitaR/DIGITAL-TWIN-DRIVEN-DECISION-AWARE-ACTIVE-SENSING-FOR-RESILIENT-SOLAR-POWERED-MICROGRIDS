# Engineering assumptions register — 2026-11-09

| ID | Decision or unknown | Evidence / required action |
|---|---|---|
| A01 | Four nominal6V5W Waveshare16158 panels as reference | Manufacturer lists Voc7.2V +/-5%, Isc916mA +/-5%; obtain cold Voc/I-V curve |
| A02 | 12V design PV ceiling,4.8A combined target | Conservative provisional envelope; NOT measured maximum |
| A03 | Protected1S5Ah pack, >=3A continuous and5A pulse target | No actual pack specified; signed OEM datasheet and PCM evidence required |
| A04 | Charge4.2V0.5A and NTC | BQ24650 supports1S but off-the-shelf board configuration unknown |
| A05 |6W steady9W startup loads | Demonstration assumptions; measure fan locked-rotor/inrush |
| A06 |TPS61088 candidate for both12V converters | IC range supports inputs; module inductors/thermal/current limits unresolved |
| A07 | Shared-PV load priority using charger DPM plus MOSFET inhibit | Both functions may operate; converter limits and analog stability require commissioning |
| A08 |KEN+KSEL source transfer | One BBM selector plus master avoids source paralleling by normal contact geometry; weld still requires independent blocking/fusing |
| A09 |S3 DevKitC-1 N8 /F411CE/C3 SuperMini | Exact purchased revisions unknown; C3 has no universal authoritative board schematic |
| A10 |ST7735 RGB565128x160,zero pixel offset | Confirm display controller, color order, inversion and offsets |
| A11 |External5V control and12V relay supplies | Keeps real-time controller powered during source loss; not energy-self-sufficient |
| A12 |Indian433.92MHz,SF7BW125,4dBm conducted target | Actual antenna gain/cable losses, emissions, current rules and equipment approval must be checked |
| A13 |CRC detects corruption, no radio authentication | Trusted isolated lab only; physical/network access control; add keyed MAC before hostile deployment |
| A14 |50% initialSOC,5Ah firmware model | Estimate explicitly uncalibrated; set knownSOC/capacity after pack characterization |
| A15 |13 INA carriers with full address straps | Common cheap two-jumper modules may not expose SDA/SCL strapping |
| A16 |TPS25940L panel branch at1.2A target | External passives, low-voltage operation, reverse trip, latch/reset and thermal design require review |
| A17 |Nominal8W sink test;7.5W qualified capacity | PB9 guarded resistor and hardware limit; measured>=7.5W at>=11.7V qualifies only7.5W |
| A18 |All prices planning estimates | Supplier pages did not return verifiable INR quotes; no stock/ownership asserted |
| A19 |PB10 charge inhibit;PB1 PV ADC;5.5V provisional charger DPM | NMOS pulls MPPSET2 low;47k/10k divider; firmware inhibit5.4V/recover5.8V must match calibrated hardware |

Unresolved assumptions are construction blockers where electrical safety depends on them. They do not prevent software builds or repeatable simulation. Dates reflect this engineering session; verify manufacturer revisions before procurement.
