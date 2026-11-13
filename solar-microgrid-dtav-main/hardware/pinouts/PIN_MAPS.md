# Controller assignments

## esp32-s3

| MCU pin | Function |
|---|---|
|GPIO8|I2C SDA|
|GPIO9|I2C SCL|
|GPIO12|Ra02 SCK|
|GPIO13|Ra02 MISO|
|GPIO11|Ra02 MOSI|
|GPIO10|Ra02 NSS|
|GPIO14|Ra02 RESET|
|GPIO4|DHT22 A DATA|
|GPIO5|DHT22 B DATA|
|GPIO1|LDR A AO|
|GPIO2|LDR B AO|
|GPIO15|PV1 eFuse EN|
|GPIO16|PV2 eFuse EN|
|GPIO17|PV3 eFuse EN|
|GPIO18|PV4 eFuse EN|
|GPIO6|PV1 eFuse FLT|
|GPIO7|PV2 eFuse FLT|
|GPIO21|PV3 eFuse FLT|
|GPIO47|PV4 eFuse FLT|

## stm32-f411

| MCU pin | Function |
|---|---|
|PA5|SPI1 SCK shared radio TFT|
|PA6|SPI1 MISO radio|
|PA7|SPI1 MOSI shared radio TFT|
|PA4|Ra02 NSS|
|PB0|Ra02 RESET|
|PB12|TFT CS|
|PB13|TFT DC|
|PB14|TFT RESET|
|PB6|I2C1 SCL|
|PB7|I2C1 SDA|
|PA2|UART2 TX to C3 GPIO4|
|PA3|UART2 RX from C3 GPIO5|
|PA0|UP button|
|PA1|DOWN button|
|PB3|LEFT button|
|PB4|RIGHT button|
|PB5|SELECT button|
|PA8|KEN master relay driver|
|PA9|KSEL transfer relay driver|
|PA10|KL1 relay driver|
|PA11|KL2 relay driver|
|PA12|KL3 relay driver|
|PB8|KPV solar converter enable relay driver|
|PB9|Solar qualification sink gate|
|PB10|MPPT MPPSET inhibit MOSFET gate|
|PB1|PV bus ADC divider 47k/10k|

## esp32-c3

| MCU pin | Function |
|---|---|
|GPIO4|UART1 RX from STM32 PA2|
|GPIO5|UART1 TX to STM32 PA3|
|GPIO18|USB D- reserved|
|GPIO19|USB D+ reserved|

Pin maps target ESP32-S3 DevKitC-1 N8, STM32F411CEU6 Black Pill and an unstandardised C3 SuperMini. C3 compiles against DevKitM-1 chip profile (4MB flash), NOT a claim of connector compatibility. Check flash capacity and USB wiring before upload. S3 GPIO35-37 (PSRAM), GPIO0/3/45/46 straps and GPIO19/20 USB are avoided. C3 GPIO2/8/9 straps and GPIO20/21 programming UART are avoided. F411 PA13/14 SWD are reserved; PB3/4 cannot simultaneously use full JTAG. STM32 USB PA11/12 is unavailable because they drive load relays; program with ST-Link. Ra02 DIO0 is unconnected: both drivers poll IRQ registers. TFT MISO is unconnected. Do not wire TFT SDO onto radio MISO unless its tri-state behaviour is verified.

MCU substitution requires a new pin, flash, clock and alternate-function audit; do not use an F401 image on an F411 or assume F401 pin-profile equivalence. All data lines are 3.3V. External isolated controller supplies power the boards and coils; none is powered directly from the 1S cell or PV.
