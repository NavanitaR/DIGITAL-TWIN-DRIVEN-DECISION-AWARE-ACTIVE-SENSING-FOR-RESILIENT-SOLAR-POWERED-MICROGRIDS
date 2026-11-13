# Source register — checked 2026-11-09

Manufacturer specifications below support candidate selection, not the rating of an anonymous module. Retail pages checked did not provide reliable live INR prices; BOM prices are allowances.

| Source | Used for | URL |
|---|---|---|
| TI INA226 |36V common-mode, signed shunt LSB, address straps|https://www.ti.com/lit/ds/symlink/ina226.pdf|
| Espressif S3 DevKitC-1 |GPIO/board reference|https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/user_guide.html|
| Espressif board schematic |S3 revision details|https://dl.espressif.com/dl/schematics/SCH_ESP32-S3-DevKitC-1_V1.1_20220413.pdf|
| ST STM32F411CE |Peripheral alternate functions/memory|https://www.st.com/resource/en/datasheet/stm32f411ce.pdf|
| STM32duino variant |Secondary BlackPill profile reference only; firmware usesHAL|https://github.com/stm32duino/Arduino_Core_STM32/blob/main/variants/STM32F4xx/F411C%28C-E%29%28U-Y%29/variant_BLACKPILL_F411CE.h|
| Waveshare16158 |6V5W reference panel,Voc,Isc|https://www.waveshare.com/catalog/product/view/id/3666/s/solar-panel-6v-5w/category/37/|
| TI BQ24650 |1S CC/CV buck, voltage-regulation MPPT,input range|https://www.ti.com/lit/ds/symlink/bq24650.pdf|
| TI BQ25798 |Alternative power-path buck-boost MPPT|https://www.ti.com/lit/ds/symlink/bq25798.pdf|
| TI TPS61088 |Boost IC operating envelope, not output module rating|https://www.ti.com/product/TPS61088|
| TI TPS25940 |eFuse integrated reverse blocking|https://www.ti.com/lit/ds/symlink/tps25940.pdf|
| ADI LTC4368 |Alternative back-to-back externalMOSFET controller|https://www.analog.com/en/products/ltc4368.html|
| Omron G2RL |Candidate DC relay contact/coil information|https://omronfs.omron.com/en_US/ecb/products/pdf/en-g2rl.pdf|
| DoT GSR347(E),9May2022 |433.05-434.79MHz exemption table|https://eservices.dot.gov.in/sites/default/files/circular-notifications/the-use-of-low-power-radio-frequency-devices-in-the-frequency-band-433.05-to-434.79-mhz-exemption-from-license-rules-2022.pdf|
| Robu Ra02 |Product listing only, no retrieved live price/stock|https://robu.in/product/sx1278-lora-module-ra-02-433mhz-wireless-spread-spectrum-transmission/|

No exact C3 SuperMini or LiPo pack has been verified. Adafruit1578 is a protected500mAh example (https://www.adafruit.com/product/1578), not a compatible substitute for the required load current. Built-in protection must be evidenced on the actual selected pack. Original local11-page project synopsis supplied conceptual research context; the latest user specification supersedes its earlier simpler hardware/budget.
