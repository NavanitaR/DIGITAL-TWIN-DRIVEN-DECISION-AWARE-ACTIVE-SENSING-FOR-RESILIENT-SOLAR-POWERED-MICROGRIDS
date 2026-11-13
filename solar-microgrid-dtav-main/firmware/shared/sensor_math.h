#ifndef GRID_SENSOR_MATH_H
#define GRID_SENSOR_MATH_H
#include <math.h>
#include <stdint.h>
static inline float ina_voltage(uint16_t bus) { return bus * .00125f; }
static inline float ina_current(uint16_t shunt, float ohms, float gain,
                                float offset) {
  return ohms > 0 ? ((int16_t)shunt) * .0000025f / ohms * gain + offset : NAN;
}
#endif
