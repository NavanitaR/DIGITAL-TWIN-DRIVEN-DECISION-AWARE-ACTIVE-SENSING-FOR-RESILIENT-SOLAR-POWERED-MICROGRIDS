#pragma once
#include <stdint.h>
// GPIO numbers, not connector positions. ESP32-S3 DevKitC-1 only.
constexpr int SDA_PIN = 8, SCL_PIN = 9, SCK_PIN = 12, MISO_PIN = 13,
              MOSI_PIN = 11, CS_PIN = 10, RST_PIN = 14;
constexpr int DHT_PINS[2] = {4, 5}, LDR_PINS[2] = {1, 2},
              ISOLATE_PINS[4] = {15, 16, 17, 18};
constexpr int FAULT_PINS[4] = {6, 7, 21, 47};
constexpr uint8_t INA_ADDR[6] = {0x40, 0x41, 0x44, 0x45, 0x48, 0x49};
constexpr float SHUNT[6] = {.01, .01, .02, .02, .02, .02};
constexpr float GAIN[6] = {1, 1, 1, 1, 1, 1}, OFFSET[6] = {0, 0, 0, 0, 0, 0};
constexpr uint32_t SAMPLE_MS = 1000, MIN_REPORT_MS = 60000;
