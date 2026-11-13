# Failure response allocation

| Failure | Implemented software response | Independent requirement / limitation |
|---|---|---|
| S3 crashes | Watchdog; reboot gates low; central telemetry stale | eFuse still protects; gate pulldown; lost solar telemetry cannot establish safety |
| STM32 resets | Master/load outputs low at boot; full local sensor qualification | External pulldowns, e-stop, pack PCM, hardware branch limits |
| C3/Wi-Fi/laptop fails | Local control continues; host stale/disabled | No electrical protection depends on network |
| LoRa fails | Local sensing continues, stale optional data expires; max3 command sends | Central uses loaded source qualification/droop; no remote panel reconnection |
| Solar disappears | Droop invalidates capacity; open transfer, battery if eligible | Converter UVLO and source reverse blocking |
| Battery cutoff | Open battery/bus whenV/SOC ineligible; shed priorities | Hardware UVLO and pack PCM required; software SOC is uncertain |
| Panel low output | Report suspected shade/open ambiguity | Need per-panel sensors; no diagnosis from cluster current alone |
| Panel reverse/protection trip | S3 inhibits and latches affected branch | eFuse/diode/fuse must stop available fault current without I2C |
| Load excess current | Latch load inhibit and open its relay | Independent current limiter/fuse; relay may not interrupt fast enough |
| Relay fails | Drive-level state alone cannot prove actuation | No auxiliary feedback wired; bus/source mismatch after2s latches controller fault; source blocking/e-stop |
| eFuse/MOSFET fails short | Unexpected branch current while off latches diagnostic | Fuse/service isolation; cannot guarantee isolation via failed switch |
| eFuse fails open | Branch power missing; ambiguous sensor/open condition | Inspect branch; other protected branches remain possible |
| INA missing/invalid | Central all-source shutdown for critical local monitors; S3 branch isolation | Hardware remains protection authority; buses need brownout tolerance |
| Brownout | MCU reset/watchdog -> startup outputs | Verify GPIO transient levels, coil release and supply supervisor |
| UART corruption | CRC/COBS drop and resync; bounded queue | No repeated unsafe actuation; physical transport trusted |
| RF spoof/replay | Node/type/sequence checks only | Not authenticated; supervised trusted lab, add MAC/session counter for deployment |

Automatic recovery is permitted for sustained source recovery, low-output shading without a hard latch and ordinary communication reconnection. Electrical branch faults, sensor corruption that invalidated isolation, unknown current after isolation and welded relay suspicion require inspection. Reboot does not automatically enable panels or clear hardware faults in a live power path.

## Shared-PV supervisory failures

An inhibit MOSFET stuck ON stops requested charging; diagnose it before any bypass. If it fails open, charger DPM may still operate but the requested pause is unavailable; commissioning must verify the actual response. A plausible but stuck-high PV ADC value is not guaranteed detectable by this supervisor. During MCU reset the gate pulldown releases inhibit, so independent charger CC/CV, NTC and pack protection remain mandatory. None of these conditions authorises driving MPPSET directly from GPIO or bypassing protection.
