#include "config.h"
#include "protocol.h"
#include "radio.h"
#include "sensor_math.h"
#include <Arduino.h>
#include <DHT.h>
#include <SPI.h>
#include <Wire.h>
#include <esp_task_wdt.h>
DHT dhtA(DHT_PINS[0], DHT22), dhtB(DHT_PINS[1], DHT22);
SensorReport report;
Radio radio;
uint16_t seq = 0, last_command = 0;
bool have_command = false, radio_ok = false;
uint32_t sampled = 0, reported = 0, dht_at = 0, report_ms = MIN_REPORT_MS;
uint8_t pending[GRID_MAX];
size_t pending_n = 0;
uint8_t faults[4] = {0};
uint32_t low_since[4] = {0};
float currents[4] = {NAN, NAN, NAN, NAN};
void selectRadio(int on) { digitalWrite(CS_PIN, on ? LOW : HIGH); }
uint8_t spiByte(uint8_t b) { return SPI.transfer(b); }
uint32_t nowMs() { return millis(); }
bool reg(uint8_t addr, uint8_t r, uint16_t &v) {
  Wire.beginTransmission(addr);
  Wire.write(r);
  if (Wire.endTransmission(false))
    return false;
  if (Wire.requestFrom((int)addr, 2) != 2)
    return false;
  v = (Wire.read() << 8) | Wire.read();
  return true;
}
void isolate(int i, bool off) {
  digitalWrite(ISOLATE_PINS[i], off ? LOW : HIGH);
  if (off)
    report.isolated |= 1 << i;
  else
    report.isolated &= ~(1 << i);
}
void queuePacket(uint8_t type, const void *data, uint8_t n, uint16_t id = 0) {
  pending_n = packet(pending, type, 1, id ? id : ++seq, millis(), data, n);
}
void ack(uint16_t id, uint8_t status) {
  uint8_t p[3];
  put16(p, id);
  p[2] = status;
  queuePacket(status ? NACK : ACK, p, 3, id);
}
void acquire() {
  report.health = 0;
  for (int i = 0; i < 6; i++) {
    uint16_t raw, bus;
    float v = NAN, a = NAN;
    if (reg(INA_ADDR[i], 2, bus) && reg(INA_ADDR[i], 1, raw)) {
      v = ina_voltage(bus);
      a = ina_current(raw, SHUNT[i], GAIN[i], OFFSET[i]);
      if (v > 12 || fabsf(a) > 8) {
        v = a = NAN;
      } else
        report.health |= 1 << i;
    }
    if (i < 2) {
      report.cluster[i][2] = v;
      report.cluster[i][3] = a;
      report.cluster[i][4] = v * a;
    } else {
      int panel = i - 2;
      currents[panel] = a;
      report.panel_power[panel] = v * a;
      if (!(report.isolated & (1 << panel)) &&
          digitalRead(FAULT_PINS[panel]) == LOW) {
        faults[panel] = 6;
        isolate(panel, true);
      }
      if (isfinite(a) && a < -.03) {
        faults[panel] = 3;
        isolate(panel, true);
      }
      if ((report.isolated & (1 << panel)) && isfinite(a) && fabsf(a) > .03)
        faults[panel] = 5;
      float sibling = report.panel_power[panel ^ 1];
      if (!(report.isolated & (1 << panel)) && isfinite(a) && a < .005 &&
          sibling > .5) {
        if (!low_since[panel])
          low_since[panel] = millis();
        if (millis() - low_since[panel] > 30000)
          faults[panel] = 1;
      } else
        low_since[panel] = 0;
      if (!isfinite(a)) {
        faults[panel] = 4;
        isolate(panel, true);
      }
    }
  }
  for (int i = 0; i < 2; i++)
    report.cluster[i][5] = analogRead(LDR_PINS[i]) / 4095.f;
  report.panel_current[0] = currents[0];
  report.panel_current[1] = currents[1];
  report.faults = 0;
  for (int i = 0; i < 4; i++)
    if (faults[i])
      report.faults |= 1 << i;
  report.sample_seq++;
}
void handle(uint8_t *p, size_t n) {
  if (!valid_packet(p, n) || p[3] != 2)
    return;
  uint16_t id = get16(p + 4);
  if (have_command && id == last_command) {
    ack(id, 0);
    return;
  }
  uint8_t status = 0;
  uint8_t *q = p + 11;
  switch (p[2]) {
  case MEASUREMENT_REQUEST:
    acquire();
    queuePacket(MEASUREMENT_RESPONSE, &report, sizeof(report), id);
    return;
  case PANEL_ISOLATION_REQUEST:
    if (p[10] != 2 || q[0] > 3 || q[1] > 1) {
      status = 2;
      break;
    }
    if (!q[1] && (faults[q[0]] || !(report.health & (1 << (q[0] + 2))))) {
      status = 3;
      break;
    }
    isolate(q[0], q[1]);
    break;
  case CONFIG_GET:
    queuePacket(CONFIG_GET, &report_ms, 4);
    return;
  case CONFIG_SET:
    if (p[10] != 4 || get32(q) < 60000 || get32(q) > 3600000)
      status = 2;
    else
      report_ms = get32(q);
    break;
  default:
    status = 2;
  }
  if (!status) {
    last_command = id;
    have_command = true;
  }
  ack(id, status);
}
void setup() {
  Serial.begin(115200);
  for (int i = 0; i < 4; i++) {
    digitalWrite(ISOLATE_PINS[i], LOW);
    pinMode(ISOLATE_PINS[i], OUTPUT);
    pinMode(FAULT_PINS[i], INPUT_PULLUP);
  }
  report.isolated = 15;
  for (int i = 0; i < 2; i++) {
    for (int j = 0; j < 6; j++)
      report.cluster[i][j] = NAN;
  }
  for (auto &x : report.panel_power)
    x = NAN;
  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setTimeOut(10);
  SPI.begin(SCK_PIN, MISO_PIN, MOSI_PIN, CS_PIN);
  pinMode(CS_PIN, OUTPUT);
  digitalWrite(CS_PIN, HIGH);
  pinMode(RST_PIN, OUTPUT);
  digitalWrite(RST_PIN, LOW);
  delay(2);
  digitalWrite(RST_PIN, HIGH);
  delay(10);
  radio.select = selectRadio;
  radio.transfer = spiByte;
  radio.ms = nowMs;
  radio_ok = radio_init(&radio);
  dhtA.begin();
  dhtB.begin();
  esp_task_wdt_init(5, true);
  esp_task_wdt_add(NULL);
}
void loop() {
  uint32_t now = millis();
  esp_task_wdt_reset();
  // Local service action after inspection: USB line "clear 1" through "clear
  // 4". It clears a latch only with branch already off, monitor healthy and
  // near-zero current.
  static String service;
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      if (service.startsWith("clear ")) {
        int i = service.substring(6).toInt() - 1;
        if (i >= 0 && i < 4 && (report.isolated & (1 << i)) &&
            (report.health & (1 << (i + 2))) && isfinite(currents[i]) &&
            fabsf(currents[i]) < .01) {
          faults[i] = 0;
          Serial.println("Latch cleared; branch remains isolated. Reconnect "
                         "requires confirmation.");
        }
      }
      service = "";
    } else if (c != '\r' && service.length() < 24)
      service += c;
  }
  if (now - sampled >= SAMPLE_MS) {
    sampled = now;
    acquire();
    Serial.printf("health=%02x isolated=%x fault=%x\n", report.health,
                  report.isolated, report.faults);
  }
  // DHT library bounds each transaction; two sensors are staggered, no delay in
  // loop.
  if (now - dht_at >= 1100) {
    static int which = 0;
    dht_at = now;
    DHT &d = which ? dhtB : dhtA;
    float t = d.readTemperature(), h = d.readHumidity();
    report.cluster[which][0] = isfinite(t) && t >= -40 && t <= 80 ? t : NAN;
    report.cluster[which][1] = isfinite(h) && h >= 0 && h <= 100 ? h : NAN;
    which ^= 1;
  }
  uint8_t p[GRID_MAX];
  if (radio_ok) {
    size_t n = radio_receive(&radio, p);
    if (n)
      handle(p, n);
    if (pending_n && radio_send(&radio, pending, pending_n)) {
      pending_n = 0;
      reported = now;
    }
    static uint8_t last_fault = 0;
    if (!pending_n &&
        (now - reported >= report_ms || last_fault != report.faults)) {
      queuePacket(SENSOR_REPORT, &report, sizeof(report));
      last_fault = report.faults;
    }
  } else if (now % 10000 < 5)
    radio_ok = radio_init(&radio);
}
