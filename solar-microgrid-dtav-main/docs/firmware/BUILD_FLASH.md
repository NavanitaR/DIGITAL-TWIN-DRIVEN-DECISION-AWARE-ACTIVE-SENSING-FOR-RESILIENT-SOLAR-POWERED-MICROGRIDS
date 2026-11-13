# Reproducible firmware builds and flashing

All three targets use PlatformIO as one build front end; STM32 uses STM32Cube HAL C, not Arduino. Each platform is version-pinned. Device libraries retain their upstream licences. STM32 uses default HSI16MHz, avoiding an undocumented Black Pill external crystal; HAL tick and peripheral baud rates derive from this clock.

From repository root:

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install platformio==6.2.0
.venv/Scripts/python -m platformio run -d firmware/esp32-s3-sensor-node
.venv/Scripts/python -m platformio run -d firmware/stm32-central-controller
.venv/Scripts/python -m platformio run -d firmware/esp32-c3-wifi-gateway
```

Flash with the same commands plus `-t upload`; use `--upload-port COMx` for ESP boards if detection is ambiguous. Linux use `.venv/bin/python` and `/dev/ttyACMx` or `/dev/ttyUSBx`. STM32 upload uses ST-Link and SWD PA13/PA14, GND and3.3V reference; avoid powering from two sources. STM32 project is a reproducible HAL equivalent to CubeIDE; no fabricated .ioc project is supplied. Import sources/HAL/startup/linker profile manually if CubeIDE is mandatory and preserve pin mapping/HSI16MHz.

S3 defaults to all panels isolated. Inspect branch health and provide confirmed panel reconnect commands after protected bench bring-up; it never enables panels automatically at boot. C3 uses native USB GPIO18/19; selected board profile is a chip/flash build profile, not a verified SuperMini schematic. Provision through USB serial at115200 with separate lines `ssid=YOUR_SSID`, `password=YOUR_PASSWORD`, `host=LAPTOP_LAN_IP`, optionally `user=MQTT_USER`, `pass=MQTT_PASSWORD`. Values are stored in NVS and never printed; reset to apply. NVS is not encrypted in this prototype. No secrets belong in Git. STM32 UART is3.3V1152008N1 crossed TX/RX with common ground.

Calibration constants live in S3 include/config.h; current signs and shunts are explicit. STM32 capacity/initialSOC and thresholds are in source and must match actual pack. User menu confirmation is required for manual source/load requests; hold SELECT for automatic policy. TFT navigation LEFT/RIGHT changes seven pages, UP/DOWN selects row, SELECT opens confirmation, LEFT cancels, SELECT confirms. Fault acknowledgement does not reconnect a latched electrical fault.

Boot loops contain no deliberate delay; startup reset/TFT delays are bounded. DHT library transactions temporarily mask interrupts and can block for a few ms; they are staggered, not truly asynchronous edge capture. HAL SPI/I2C calls have bounded timeouts, TFT draws one text row per slice. Gateway MQTT reconnect may block up to its1s socket timeout and must not be used for safety control. Watchdogs reset after a stalled loop, but external pulldowns/protection are still required.
