# Troubleshooting

No dashboard: run backend on127.0.0.1:8000 and Vite on127.0.0.1:5173. Vite proxies /api and /ws. PowerShell may require npm.cmd instead of npm.ps1; do not weaken system policy. Empty hardware mode is correct without real valid packets. If central packets contain NaN, host rejects them and marks stale rather than inventing measurements.

No MQTT: install/start Mosquitto; set gateway host to laptop LAN address, notlocalhost. Open only a trusted LAN interface with authentication/firewall, provision user/pass on C3, and set matching environment variables on backend. Verify UART crossover, common ground and1152008N1. Gateway must not be wired to5V serial logic.

No LoRa: verify Ra02 power3.3V decoupling, antenna, SPI CS/reset pins, matching433.92/SF7/BW125/syncword and legal RF setup. Polling driver needs no DIO wiring. Airtime limiter intentionally delays transmissions; repeated commands can receive busy/timeout. CRC is not encryption/authentication.

Panels remain isolated: this is the reset default. Confirm hardware protection/monitor health, then explicit reconnect under commissioning conditions. A latched reverse/sensor/protection fault rejects reconnect. Do not repeatedly reboot to evade a fault.

Central stays off: all seven INA channels must be healthy/fresh. Check address straps, common ground, shunt polarity, I2C pullups and pack voltage. Solar auto-selection requires a loaded qualification probe; open-circuit voltage alone is insufficient. TFT garbled: confirm controller/revision, RGB/BGR order and pixel offsets. UART interference: STM32 USB pinsPA11/12 are repurposed; flash overSWD.

Research graphs identical energy: expected when local deterministic controller uses continuous local safety measurements for every strategy. The optional-telemetry comparison isolates communication and estimator performance; it is not proof of identical hardware outcomes under all delays.
