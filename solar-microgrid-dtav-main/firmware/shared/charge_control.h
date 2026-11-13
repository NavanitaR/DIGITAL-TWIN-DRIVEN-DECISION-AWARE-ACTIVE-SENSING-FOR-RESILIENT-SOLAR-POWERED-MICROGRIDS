#ifndef GRID_CHARGE_CONTROL_H
#define GRID_CHARGE_CONTROL_H
#include <math.h>
#include <stdint.h>
/* Provisional PV thresholds must match the physically configured charger DPM.
 * Charger DPM provides continuous hardware regulation; this is a slower inhibit
 * supervisor, not an MPPT algorithm or independent electrical protection. */
typedef struct {
  uint8_t inhibit;
  uint32_t dropped, recovered;
} ChargeControl;
static inline void charge_init(ChargeControl *c) {
  c->inhibit = 1;
  c->dropped = 0;
  c->recovered = 0;
}
static inline void charge_step(ChargeControl *c, uint32_t now, float pv,
                               int valid, int transition) {
  if (!valid || !isfinite(pv) || pv < 5.4f || transition) {
    c->inhibit = 1;
    c->dropped = now;
    c->recovered = 0;
    return;
  }
  if (c->inhibit) {
    if (pv >= 5.8f) {
      if (!c->recovered)
        c->recovered = now ? now : 1;
    } else
      c->recovered = 0;
    if (c->recovered && now - c->recovered >= 5000 && now - c->dropped >= 15000)
      c->inhibit = 0;
  }
}
#endif
