#ifndef GRID_RADIO_H
#define GRID_RADIO_H
#include <stddef.h>
#include <stdint.h>
/* SX1278 polling driver. Call tick frequently. No sleep during TX. */
typedef struct {
  void (*select)(int);
  uint8_t (*transfer)(uint8_t);
  uint32_t (*ms)(void);
  uint8_t active;
  uint32_t tx_start, next_tx, tx_count, rx_count, errors;
  int16_t rssi;
  int8_t snr;
} Radio;
static uint8_t rr(Radio *r, uint8_t a) {
  r->select(1);
  r->transfer(a & 127);
  uint8_t b = r->transfer(0);
  r->select(0);
  return b;
}
static void rw(Radio *r, uint8_t a, uint8_t b) {
  r->select(1);
  r->transfer(a | 128);
  r->transfer(b);
  r->select(0);
}
static int radio_init(Radio *r) {
  if (rr(r, 0x42) != 0x12)
    return 0;
  rw(r, 1, 0x88); /* LoRa, LF, sleep */
  uint32_t frf = (uint32_t)((433920000ULL << 19) / 32000000);
  rw(r, 6, frf >> 16);
  rw(r, 7, frf >> 8);
  rw(r, 8, frf);
  rw(r, 9, 0x82); /* PA_BOOST, 4dBm conducted: verify antenna ERP */
  rw(r, 0x4d, 0x84);
  rw(r, 0x0b, 0x2b);
  rw(r, 0x1d, 0x72);
  rw(r, 0x1e, 0x74);
  rw(r, 0x26, 0x04); /* BW125 SF7 CR4/5 CRC */
  rw(r, 0x39, 0x42);
  rw(r, 0x0e, 0);
  rw(r, 0x0f, 0);
  rw(r, 0x20, 0);
  rw(r, 0x21, 8);
  rw(r, 1, 0x8d);
  return 1;
}
static void radio_tick(Radio *r) {
  if (r->active) {
    uint32_t now = r->ms();
    if (rr(r, 0x12) & 8) {
      rw(r, 0x12, 8);
      r->active = 0;
      r->tx_count++;
      rw(r, 1, 0x8d);
    } else if (now - r->tx_start > 1500) {
      r->active = 0;
      r->errors++;
      rw(r, 1, 0x8d);
    }
  }
}
static int radio_send(Radio *r, const uint8_t *p, size_t n) {
  radio_tick(r);
  uint32_t now = r->ms();
  if (r->active || (int32_t)(now - r->next_tx) < 0 || n > 193)
    return 0;
  rw(r, 1, 0x89);
  rw(r, 0x0d, 0);
  for (size_t i = 0; i < n; i++)
    rw(r, 0, p[i]);
  rw(r, 0x22, n);
  rw(r, 0x12, 255);
  rw(r, 1, 0x8b);
  r->active = 1;
  r->tx_start = now;
  /* Conservative SF7/BW125 airtime bound: 100ms + 2ms/octet. <=5% scheduler. */
  r->next_tx = now + (100 + 2 * n) * 20;
  return 1;
}
static size_t radio_receive(Radio *r, uint8_t *p) {
  radio_tick(r);
  if (r->active)
    return 0;
  uint8_t flags = rr(r, 0x12);
  if (!(flags & 0x40))
    return 0;
  rw(r, 0x12, flags);
  if (flags & 0x20) {
    r->errors++;
    return 0;
  }
  size_t n = rr(r, 0x13);
  if (n > 193) {
    r->errors++;
    return 0;
  }
  rw(r, 0x0d, rr(r, 0x10));
  for (size_t i = 0; i < n; i++)
    p[i] = rr(r, 0);
  r->rssi = (int16_t)rr(r, 0x1a) - 164;
  r->snr = (int8_t)rr(r, 0x19) / 4;
  r->rx_count++;
  return n;
}
#endif
