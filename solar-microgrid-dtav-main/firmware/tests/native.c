#include "charge_control.h"
#include "control.h"
#include "protocol.h"
#include "sensor_math.h"
#include <assert.h>
#include <stdio.h>
int main(void) {
  ChargeControl charge;
  charge_init(&charge);
  charge_step(&charge, 100, 6.0f, 1, 0);
  assert(charge.inhibit);
  charge_step(&charge, 16000, 6.0f, 1, 0);
  assert(!charge.inhibit);
  charge_step(&charge, 16001, 5.3f, 1, 0);
  assert(charge.inhibit);
  charge_step(&charge, 20000, 6.1f, 1, 0);
  assert(charge.inhibit);
  charge_step(&charge, 32000, 6.1f, 1, 0);
  assert(!charge.inhibit);
  charge_step(&charge, 33000, 6.1f, 1, 1);
  assert(charge.inhibit);
  charge_step(&charge, 50000, NAN, 1, 0);
  assert(charge.inhibit);
  uint8_t p[256], q[256], w[256];
  uint8_t data[180];
  for (int i = 0; i < 180; i++)
    data[i] = i;
  size_t n = packet(p, SENSOR_REPORT, 1, 42, 100, data, 180);
  assert(valid_packet(p, n));
  size_t z = cobs_encode(p, n, w);
  assert(w[z - 1] == 0);
  assert(cobs_decode(w, z - 1, q) == n);
  assert(memcmp(p, q, n) == 0);
  p[20] ^= 1;
  assert(!valid_packet(p, n));
  assert(fabsf(ina_voltage(9600) - 12) < .001f);
  assert(fabsf(ina_current((uint16_t)-400, .01f, 1, 0) + .1f) < .00001f);
  assert(isnan(ina_current(1, 0, 1, 0)));
  Control c;
  control_init(&c);
  control_step(&c, 15000, 10, 3.8, .6, 1);
  assert(c.source == 0 && c.pending);
  control_step(&c, 15200, 10, 3.8, .6, 1);
  assert(c.source == 0);
  control_step(&c, 15300, 10, 3.8, .6, 1);
  assert(c.source == 2);
  control_step(&c, 16000, 0, 3.2, .01, 1);
  assert(!c.source && !c.mask);
  control_step(&c, 20000, 10, NAN, .5, 1);
  assert(c.state == FAULT);
  uint8_t command[4] = {2, 0, 2, 1};
  assert(control_command(&c, command, 0, 3.2, .01) != 0);
  puts("native sensor conversion, protocol, framing, transfer, low-battery and "
       "invalid-command checks passed");
  return 0;
}
