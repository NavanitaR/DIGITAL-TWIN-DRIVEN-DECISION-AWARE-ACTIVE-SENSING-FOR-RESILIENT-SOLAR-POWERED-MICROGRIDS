# India RF commissioning notes

DoT GSR347(E)2022 lists433.05-434.79MHz with10mW ERP and<=10% duty cycle for one exemption entry. Additional entries have different bandwidth/power/access conditions; do not conflate them. Reference firmware chooses433.92MHz,SF7,125kHzBW,CR4/5,4dBm conducted PA_BOOST and a conservative<=5% airtime scheduler. This is not a compliance certificate.

ERP_dBm=P_conducted_dBm+G_antenna_dBd-L_cable_dB.10mW=10dBm ERP.4dBm with an assumed0dBd antenna is below that limit only if actual gain/emissions/power accuracy comply. Do not assume antenna specifications or use SX1278 maximum20dBm by default. Confirm current law, equipment/type approval/import requirements, spectral occupancy, spurious emissions and actual antenna installation before transmitting. Connect a matched antenna before TX.

At SF7/BW125 explicit header,CRC,preamble8, CR4/5: Tsymbol=2^7/125000=1.024ms. Standard LoRa payload-symbol equation determines actual airtime. Firmware upper bound100ms+2ms*packet_bytes at this fixed configuration is deliberately conservative; nextTX=now+20*bound. Retries/ACKs consume the same transmitter budget. Changing modulation requires a fresh bound/calculation and regulatory check. Software-only continuous reporting baseline is not a legal over-air continuous-TX configuration.

RF link-loss tests use software disconnects or legal attenuated setups, not an assumption that transmitted packets are interference-free. The reference rule is cited in SOURCES.md; verify amendments before a demonstration.
