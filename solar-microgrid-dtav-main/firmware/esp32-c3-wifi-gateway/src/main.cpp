#include "protocol.h"
#include <Arduino.h>
#include <Preferences.h>
#include <PubSubClient.h>
#include <WiFi.h>
#include <esp_task_wdt.h>
// GPIO4 RX <- STM32 PA2; GPIO5 TX -> STM32 PA3. GPIO18/19 reserved for USB.
WiFiClient net;
PubSubClient mqtt(net);
Preferences prefs;
GridStream uartStream = {};
String ssid, password, host, user, pass;
uint16_t port = 1883;
uint32_t lastWifi = 0, lastMqtt = 0, heartbeat = 0;
uint16_t sequence = 0;
struct Frame {
  uint8_t data[GRID_MAX];
  uint16_t n;
  uint32_t at;
};
Frame frames[8];
uint8_t head = 0, count = 0;
uint32_t dropped = 0, forwarded = 0;
void mqttMessage(char *, byte *data, unsigned int n) {
  if (n > GRID_MAX || !valid_packet(data, n) || data[2] != CONTROL)
    return;
  uint8_t framed[256];
  size_t len = cobs_encode(data, n, framed);
  Serial1.write(framed, len);
}
void provision() {
  static String line;
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\r')
      continue;
    if (c == '\n') {
      int at = line.indexOf('=');
      if (at > 0) {
        String key = line.substring(0, at), value = line.substring(at + 1);
        if (key == "ssid" || key == "password" || key == "host" ||
            key == "user" || key == "pass") {
          prefs.putString(key.c_str(), value);
          Serial.println("Saved; reset to apply.");
        }
      }
      line = "";
    } else if (line.length() < 128)
      line += c;
    else
      line = "";
  }
}
void setup() {
  Serial.begin(115200);
  Serial1.begin(115200, SERIAL_8N1, 4, 5);
  prefs.begin("microgrid", false);
  ssid = prefs.getString("ssid", "");
  password = prefs.getString("password", "");
  host = prefs.getString("host", "");
  user = prefs.getString("user", "");
  pass = prefs.getString("pass", "");
  WiFi.mode(WIFI_STA);
  mqtt.setServer(host.c_str(), port);
  mqtt.setCallback(mqttMessage);
  mqtt.setBufferSize(512);
  mqtt.setSocketTimeout(1);
  mqtt.setKeepAlive(20);
  esp_task_wdt_init(5, true);
  esp_task_wdt_add(NULL);
  Serial.println("Provision USB: ssid=..., password=..., host=... (broker LAN "
                 "address), user=..., pass=...");
}
void loop() {
  uint32_t now = millis();
  esp_task_wdt_reset();
  provision();
  if (WiFi.status() != WL_CONNECTED && ssid.length() &&
      now - lastWifi > 10000) {
    lastWifi = now;
    WiFi.begin(ssid.c_str(), password.c_str());
  }
  if (WiFi.status() == WL_CONNECTED && !mqtt.connected() && host.length() &&
      now - lastMqtt > 5000) {
    lastMqtt = now;
    String id = "grid-c3-" + String((uint32_t)ESP.getEfuseMac(), HEX);
    if (mqtt.connect(id.c_str(), user.c_str(), pass.c_str(),
                     "microgrid/v1/gateway", 1, true, "offline")) {
      mqtt.subscribe("microgrid/v1/down", 1);
      mqtt.publish("microgrid/v1/gateway", "online", true);
    }
  }
  mqtt.loop();
  uint8_t raw[256];
  int budget = 512;
  while (Serial1.available() && budget--) {
    size_t n = stream_byte(&uartStream, Serial1.read(), raw);
    if (n) {
      if (count == 8) {
        head = (head + 1) % 8;
        count--;
        dropped++;
      }
      Frame &f = frames[(head + count) % 8];
      memcpy(f.data, raw, n);
      f.n = n;
      f.at = now;
      count++;
    }
  }
  if (count) {
    Frame &f = frames[head];
    if (now - f.at > 5000) {
      head = (head + 1) % 8;
      count--;
      dropped++;
    } else if (mqtt.connected() &&
               mqtt.publish("microgrid/v1/up", f.data, f.n, false)) {
      head = (head + 1) % 8;
      count--;
      forwarded++;
    }
  }
  if (now - heartbeat > 2000) {
    heartbeat = now;
    uint8_t state[4] = {(uint8_t)(WiFi.status() == WL_CONNECTED),
                        (uint8_t)mqtt.connected(), count,
                        (uint8_t)(dropped > 0)};
    uint8_t p[32], wire[40];
    size_t n = packet(p, HEARTBEAT, 3, ++sequence, now, state, 4);
    Serial1.write(wire, cobs_encode(p, n, wire));
  }
}
