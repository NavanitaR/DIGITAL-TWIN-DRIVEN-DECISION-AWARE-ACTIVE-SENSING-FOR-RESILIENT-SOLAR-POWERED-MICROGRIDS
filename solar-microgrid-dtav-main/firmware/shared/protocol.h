#ifndef GRID_PROTOCOL_H
#define GRID_PROTOCOL_H
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#define GRID_MAX 193
enum {
  HEARTBEAT = 1,
  SENSOR_REPORT,
  PANEL_REPORT,
  FAULT_EVENT,
  MEASUREMENT_REQUEST,
  MEASUREMENT_RESPONSE,
  PANEL_ISOLATION_REQUEST,
  ACK,
  NACK,
  CONFIG_GET,
  CONFIG_SET,
  CONTROL,
  CENTRAL_REPORT
};
static inline uint16_t crc16(const uint8_t *p, size_t n) {
  uint16_t c = 0xffff;
  while (n--) {
    c ^= (uint16_t)*p++ << 8;
    for (int i = 0; i < 8; i++)
      c = c & 0x8000 ? (c << 1) ^ 0x1021 : c << 1;
  }
  return c;
}
static inline void put16(uint8_t *p, uint16_t x) {
  p[0] = x;
  p[1] = x >> 8;
}
static inline uint16_t get16(const uint8_t *p) {
  return p[0] | (uint16_t)p[1] << 8;
}
static inline void put32(uint8_t *p, uint32_t x) {
  for (int i = 0; i < 4; i++)
    p[i] = x >> (8 * i);
}
static inline uint32_t get32(const uint8_t *p) {
  return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 |
         (uint32_t)p[3] << 24;
}
static inline size_t packet(uint8_t *out, uint8_t type, uint8_t node,
                            uint16_t seq, uint32_t ms, const void *data,
                            uint8_t n) {
  if (n > 180)
    return 0;
  out[0] = 0xa7;
  out[1] = 1;
  out[2] = type;
  out[3] = node;
  put16(out + 4, seq);
  put32(out + 6, ms);
  out[10] = n;
  if (n)
    memcpy(out + 11, data, n);
  put16(out + 11 + n, crc16(out, 11 + n));
  return n + 13;
}
static inline int valid_packet(const uint8_t *p, size_t n) {
  return n >= 13 && n <= GRID_MAX && p[0] == 0xa7 && p[1] == 1 && p[2] >= 1 &&
         p[2] <= 13 && p[10] <= 180 && n == (size_t)p[10] + 13 &&
         crc16(p, n - 2) == get16(p + n - 2);
}
static inline size_t cobs_encode(const uint8_t *in, size_t n, uint8_t *out) {
  size_t start = 0, pos = 1;
  uint8_t code = 1;
  while (n--) {
    if (!*in) {
      out[start] = code;
      start = pos++;
      code = 1;
      in++;
    } else {
      out[pos++] = *in++;
      if (++code == 255) {
        out[start] = code;
        start = pos++;
        code = 1;
      }
    }
  }
  out[start] = code;
  out[pos++] = 0;
  return pos;
}
static inline size_t cobs_decode(const uint8_t *in, size_t n, uint8_t *out) {
  size_t i = 0, k = 0;
  while (i < n) {
    uint8_t c = in[i++];
    if (!c || i + c - 1 > n)
      return 0;
    for (int j = 1; j < c; j++)
      out[k++] = in[i++];
    if (c < 255 && i < n)
      out[k++] = 0;
  }
  return k;
}
typedef struct {
  uint8_t data[256];
  size_t n;
  uint32_t errors;
} GridStream;
static inline size_t stream_byte(GridStream *s, uint8_t b, uint8_t *out) {
  if (b) {
    if (s->n < sizeof(s->data))
      s->data[s->n++] = b;
    else {
      s->n = 0;
      s->errors++;
    }
    return 0;
  }
  size_t n = cobs_decode(s->data, s->n, out);
  s->n = 0;
  if (!valid_packet(out, n)) {
    s->errors++;
    return 0;
  }
  return n;
}
typedef struct {
  float cluster[2][6];
  float panel_power[4];
  float panel_current[2];
  uint8_t isolated, health, faults, sample_seq;
} SensorReport;
typedef struct {
  float battery_v, battery_a, soc, bus_v, solar_w, load_w, load[3];
  float load_v[3], load_a[3];
  uint8_t source, mask, state, health;
} CentralReport;
#ifdef __cplusplus
static_assert(sizeof(SensorReport) == 76, "sensor wire size");
static_assert(sizeof(CentralReport) == 64, "central wire size");
#else
_Static_assert(sizeof(SensorReport) == 76, "sensor wire size");
_Static_assert(sizeof(CentralReport) == 64, "central wire size");
#endif
#endif
