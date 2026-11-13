#ifndef GRID_CONTROL_H
#define GRID_CONTROL_H
#include <math.h>
#include <stdint.h>
enum {
  INIT,
  STANDBY,
  SOLAR_ACTIVE,
  BATTERY_ACTIVE,
  LOAD_SHEDDING,
  FAULT,
  RECOVERY,
  SAFE_SHUTDOWN
};
typedef struct {
  uint8_t source, pending, mask, state;
  uint32_t changed, transfer, restored, solar_since;
  int8_t manual_source;
  uint8_t inhibited;
  float service_budget;
  uint8_t battery_ready;
} Control;
static void control_init(Control *c) {
  *c = (Control){0};
  c->manual_source = -1;
  c->state = INIT;
  c->service_budget = 6;
  c->battery_ready = 1;
}
static float load_power(uint8_t m) {
  return (m & 1 ? 1 : 0) + (m & 2 ? 3 : 0) + (m & 4 ? 2 : 0);
}
static void control_step(Control *c, uint32_t now, float solar, float bv,
                         float soc, int valid) {
  if (!valid || !isfinite(solar) || !isfinite(bv) || !isfinite(soc) ||
      bv < 2.5f || bv > 4.30f || soc < 0 || soc > 1) {
    c->mask = c->source = c->pending = 0;
    c->state = FAULT;
    return;
  }
  int bat = c->battery_ready && bv >= 3.35f && soc > .08f;
  int sun = solar >= 2;
  if (solar >= 7.5f) {
    if (!c->solar_since)
      c->solar_since = now ? now : 1;
  } else
    c->solar_since = 0;
  uint8_t desired = bat ? 2 : 0;
  if (c->solar_since && now - c->solar_since >= 10000)
    desired = 1;
  if (c->source == 1 && solar >= load_power(c->mask) + .5f)
    desired = 1;
  if (c->manual_source == 0)
    desired = 0;
  if (c->manual_source == 1 && sun)
    desired = 1;
  if (c->manual_source == 2 && bat)
    desired = 2;
  int emergency = (c->source == 1 && !sun) || (c->source == 2 && !bat);
  if (c->pending) {
    if ((c->pending == 1 && !sun) || (c->pending == 2 && !bat))
      c->pending = 0;
    else if (now - c->transfer >= 250) {
      c->source = c->pending;
      c->pending = 0;
      c->changed = now;
    }
  } else if (desired != c->source &&
             (emergency || !desired || now - c->changed >= 15000)) {
    c->source = 0;
    c->mask = 0;
    c->pending = desired;
    c->transfer = now;
  }
  float budget = c->source == 1   ? solar - .5f
                 : c->source == 2 ? (soc > .25f   ? 6
                                     : soc > .12f ? 4
                                                  : 1.2f)
                                  : 0;
  budget = fminf(budget, fmaxf(1, c->service_budget));
  for (int i = 2; i >= 0; i--)
    if (load_power(c->mask) > budget || (c->inhibited & (1 << i)))
      c->mask &= ~(1 << i);
  if (now - c->restored >= 2000) {
    const float p[3] = {1, 3, 2};
    for (int i = 0; i < 3; i++)
      if (!(c->mask & (1 << i)) && !(c->inhibited & (1 << i)) &&
          load_power(c->mask) + p[i] <= budget) {
        c->mask |= 1 << i;
        c->restored = now;
        break;
      }
  }
  c->state = c->pending       ? RECOVERY
             : !c->source     ? SAFE_SHUTDOWN
             : c->mask != 7   ? LOAD_SHEDDING
             : c->source == 1 ? SOLAR_ACTIVE
                              : BATTERY_ACTIVE;
}
static int control_command(Control *c, const uint8_t *p, float solar, float bv,
                           float soc) {
  if (p[0] == 5) {
    c->manual_source = -1;
    c->inhibited = 0;
    return 0;
  }
  if (p[0] == 4)
    return 0;
  if (!p[3])
    return 1;
  if (p[0] == 6) {
    if (p[1] != 0 && p[1] != 1 && p[1] != 4 && p[1] != 6)
      return 2;
    c->service_budget = p[1];
    return 0;
  }
  if (p[0] == 2) {
    if (p[2] > 2)
      return 2;
    if (p[2] == 1 && solar < 7.5f)
      return 3;
    if (p[2] == 2 && (!c->battery_ready || bv < 3.35 || soc <= .08))
      return 3;
    c->manual_source = p[2];
    return 0;
  }
  if (p[0] == 1) {
    if (p[1] > 2 || p[2] > 1)
      return 2;
    if (p[2] && (!c->source || soc <= .12))
      return 3;
    if (p[2])
      c->inhibited &= ~(1 << p[1]);
    else {
      c->inhibited |= 1 << p[1];
      c->mask &= ~(1 << p[1]);
    }
    return 0;
  }
  return 2;
}
#endif
