#include "charge_control.h"
#include "control.h"
#include "protocol.h"
#include "radio.h"
#include "sensor_math.h"
#include "stm32f4xx_hal.h"
#include <math.h>
#include <stdio.h>
SPI_HandleTypeDef spi;
I2C_HandleTypeDef i2c;
UART_HandleTypeDef uart;
IWDG_HandleTypeDef watchdog;
ADC_HandleTypeDef pv_adc;
ChargeControl charge_control;
float pv_voltage = NAN;
Control control;
Radio radio;
GridStream stream;
SensorReport solar_report;
CentralReport telemetry;
uint32_t last_radio = 0, last_gateway = 0, sensor_at[7] = {0}, sense_at = 0,
         report_at = 0, display_at = 0;
uint16_t sequence = 0, last_command = 0;
uint8_t command_seen = 0, radio_ok = 0;
float volts[7], amps[7], soc = .5f;
uint8_t health = 0, load_fault = 0;
uint8_t pending[GRID_MAX];
size_t pending_n = 0;
uint8_t probe = 0;
uint32_t probe_at = 0, qualified_at = 0;
float solar_capacity = 0;
uint8_t waiting = 0, attempts = 0;
uint32_t sent_at = 0;
uint16_t waiting_id = 0;
uint8_t actuation_fault = 0;
uint32_t source_active_at = 0;
uint32_t service_at = 0;
uint8_t page = 0, row = 0, confirm = 0;
uint8_t requested[4];
uint32_t fault_at = 0;
uint8_t last_fault = 0;
void SysTick_Handler(void) { HAL_IncTick(); }
void Error_Handler(void) {
  __disable_irq();
  for (;;) {
  }
}
void pin(GPIO_TypeDef *p, uint16_t pins, uint32_t mode, uint32_t pull,
         uint8_t af) {
  GPIO_InitTypeDef g = {0};
  g.Pin = pins;
  g.Mode = mode;
  g.Pull = pull;
  g.Speed = GPIO_SPEED_FREQ_HIGH;
  g.Alternate = af;
  HAL_GPIO_Init(p, &g);
}
void init_hw(void) {
  HAL_Init();
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();
  __HAL_RCC_GPIOC_CLK_ENABLE();
  // HSI 16MHz default clock avoids assumptions about Black Pill crystal
  // revision.
  HAL_GPIO_WritePin(
      GPIOA, GPIO_PIN_8 | GPIO_PIN_9 | GPIO_PIN_10 | GPIO_PIN_11 | GPIO_PIN_12,
      GPIO_PIN_RESET);
  HAL_GPIO_WritePin(GPIOB, GPIO_PIN_8, GPIO_PIN_RESET);
  HAL_GPIO_WritePin(GPIOB, GPIO_PIN_12 | GPIO_PIN_14, GPIO_PIN_SET);
  HAL_GPIO_WritePin(GPIOA, GPIO_PIN_4, GPIO_PIN_SET);
  pin(GPIOA, GPIO_PIN_8 | GPIO_PIN_9 | GPIO_PIN_10 | GPIO_PIN_11 | GPIO_PIN_12,
      GPIO_MODE_OUTPUT_PP, GPIO_NOPULL, 0);
  pin(GPIOB,
      GPIO_PIN_0 | GPIO_PIN_8 | GPIO_PIN_9 | GPIO_PIN_10 | GPIO_PIN_12 |
          GPIO_PIN_13 | GPIO_PIN_14,
      GPIO_MODE_OUTPUT_PP, GPIO_NOPULL, 0);
  pin(GPIOA, GPIO_PIN_4, GPIO_MODE_OUTPUT_PP, GPIO_NOPULL, 0);
  // PB1=ADC1_IN9, previously unused (Ra02 IRQs are polled).
  pin(GPIOB, GPIO_PIN_1, GPIO_MODE_ANALOG, GPIO_NOPULL, 0);
  __HAL_RCC_ADC1_CLK_ENABLE();
  pv_adc.Instance = ADC1;
  pv_adc.Init.ClockPrescaler = ADC_CLOCK_SYNC_PCLK_DIV4;
  pv_adc.Init.Resolution = ADC_RESOLUTION_12B;
  pv_adc.Init.ScanConvMode = DISABLE;
  pv_adc.Init.ContinuousConvMode = DISABLE;
  pv_adc.Init.DiscontinuousConvMode = DISABLE;
  pv_adc.Init.ExternalTrigConvEdge = ADC_EXTERNALTRIGCONVEDGE_NONE;
  pv_adc.Init.ExternalTrigConv = ADC_SOFTWARE_START;
  pv_adc.Init.DataAlign = ADC_DATAALIGN_RIGHT;
  pv_adc.Init.NbrOfConversion = 1;
  pv_adc.Init.EOCSelection = ADC_EOC_SINGLE_CONV;
  if (HAL_ADC_Init(&pv_adc) != HAL_OK)
    Error_Handler();
  ADC_ChannelConfTypeDef channel = {0};
  channel.Channel = ADC_CHANNEL_9;
  channel.Rank = 1;
  channel.SamplingTime = ADC_SAMPLETIME_144CYCLES;
  if (HAL_ADC_ConfigChannel(&pv_adc, &channel) != HAL_OK)
    Error_Handler();
  pin(GPIOA, GPIO_PIN_0 | GPIO_PIN_1, GPIO_MODE_INPUT, GPIO_PULLUP, 0);
  pin(GPIOB, GPIO_PIN_3 | GPIO_PIN_4 | GPIO_PIN_5, GPIO_MODE_INPUT, GPIO_PULLUP,
      0);
  pin(GPIOA, GPIO_PIN_5 | GPIO_PIN_6 | GPIO_PIN_7, GPIO_MODE_AF_PP, GPIO_NOPULL,
      GPIO_AF5_SPI1);
  __HAL_RCC_SPI1_CLK_ENABLE();
  spi.Instance = SPI1;
  spi.Init.Mode = SPI_MODE_MASTER;
  spi.Init.Direction = SPI_DIRECTION_2LINES;
  spi.Init.DataSize = SPI_DATASIZE_8BIT;
  spi.Init.CLKPolarity = SPI_POLARITY_LOW;
  spi.Init.CLKPhase = SPI_PHASE_1EDGE;
  spi.Init.NSS = SPI_NSS_SOFT;
  spi.Init.BaudRatePrescaler = SPI_BAUDRATEPRESCALER_4;
  spi.Init.FirstBit = SPI_FIRSTBIT_MSB;
  if (HAL_SPI_Init(&spi) != HAL_OK)
    Error_Handler();
  pin(GPIOB, GPIO_PIN_6 | GPIO_PIN_7, GPIO_MODE_AF_OD, GPIO_PULLUP,
      GPIO_AF4_I2C1);
  __HAL_RCC_I2C1_CLK_ENABLE();
  i2c.Instance = I2C1;
  i2c.Init.ClockSpeed = 100000;
  i2c.Init.DutyCycle = I2C_DUTYCYCLE_2;
  i2c.Init.AddressingMode = I2C_ADDRESSINGMODE_7BIT;
  if (HAL_I2C_Init(&i2c) != HAL_OK)
    Error_Handler();
  pin(GPIOA, GPIO_PIN_2 | GPIO_PIN_3, GPIO_MODE_AF_PP, GPIO_PULLUP,
      GPIO_AF7_USART2);
  __HAL_RCC_USART2_CLK_ENABLE();
  uart.Instance = USART2;
  uart.Init.BaudRate = 115200;
  uart.Init.WordLength = UART_WORDLENGTH_8B;
  uart.Init.StopBits = UART_STOPBITS_1;
  uart.Init.Parity = UART_PARITY_NONE;
  uart.Init.Mode = UART_MODE_TX_RX;
  uart.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  uart.Init.OverSampling = UART_OVERSAMPLING_16;
  if (HAL_UART_Init(&uart) != HAL_OK)
    Error_Handler();
  watchdog.Instance = IWDG;
  watchdog.Init.Prescaler = IWDG_PRESCALER_64;
  watchdog.Init.Reload = 1000;
  HAL_IWDG_Init(&watchdog);
}
void rselect(int on) {
  HAL_GPIO_WritePin(GPIOA, GPIO_PIN_4, on ? GPIO_PIN_RESET : GPIO_PIN_SET);
}
uint8_t transfer(uint8_t b) {
  uint8_t x = 0;
  HAL_SPI_TransmitReceive(&spi, &b, &x, 1, 2);
  return x;
}
void serial_send(const uint8_t *p, size_t n) {
  uint8_t wire[256];
  size_t z = cobs_encode(p, n, wire);
  HAL_UART_Transmit(&uart, wire, z, 25);
}
int ina(uint8_t address, uint8_t r, uint16_t *v) {
  uint8_t b[2];
  if (HAL_I2C_Mem_Read(&i2c, address << 1, r, 1, b, 2, 4) != HAL_OK)
    return 0;
  *v = (b[0] << 8) | b[1];
  return 1;
}
void acquire(uint32_t now) {
  static int channel = 0;
  uint16_t raw, bus;
  int i = channel;
  uint8_t addr[7] = {0x40, 0x41, 0x44, 0x45, 0x48, 0x49, 0x4c};
  if (ina(addr[i], 2, &bus) && ina(addr[i], 1, &raw)) {
    volts[i] = ina_voltage(bus);
    amps[i] = ina_current(raw, .01f, 1, 0);
    if (volts[i] < 16 && fabsf(amps[i]) < 10) {
      health |= 1 << i;
      sensor_at[i] = now;
    } else
      health &= ~(1 << i);
  } else
    health &= ~(1 << i);
  if (i == 0 && health & 1) {
    static uint32_t at = 0;
    if (at)
      soc = fmaxf(0, fminf(1, soc - amps[0] * (now - at) / 18000000.f));
    at = now;
  }
  for (int j = 4; j < 7; j++) {
    float limits[3] = {.18f, .6f, .3f};
    if ((health & (1 << j)) && amps[j] > limits[j - 4]) {
      load_fault |= 1 << (j - 4);
      control.inhibited |= 1 << (j - 4);
      control.mask &= ~(1 << (j - 4));
    }
  }
  channel = (channel + 1) % 7;
}
void outputs(void) { /* KEN master NO + KSEL break-before-make transfer. Never
                        two source outputs in parallel. */
  uint8_t target = control.pending ? control.pending : control.source;
  if (!control.source)
    HAL_GPIO_WritePin(GPIOA, GPIO_PIN_8, GPIO_PIN_RESET);
  HAL_GPIO_WritePin(GPIOA, GPIO_PIN_9,
                    target == 2 ? GPIO_PIN_SET : GPIO_PIN_RESET);
  if (control.source)
    HAL_GPIO_WritePin(GPIOA, GPIO_PIN_8, GPIO_PIN_SET);
  for (int i = 0; i < 3; i++)
    HAL_GPIO_WritePin(GPIOA, GPIO_PIN_10 << i,
                      (control.mask & (1 << i)) ? GPIO_PIN_SET
                                                : GPIO_PIN_RESET);
  // Rev2 KPV NO enables solar boost only. MPPT has its own always-connected
  // protected PV input. KPV NC is insulated, not a charger connection.
  HAL_GPIO_WritePin(GPIOB, GPIO_PIN_8,
                    (control.source == 1 || control.pending == 1 || probe)
                        ? GPIO_PIN_SET
                        : GPIO_PIN_RESET);
  HAL_GPIO_WritePin(GPIOB, GPIO_PIN_9,
                    probe == 2 ? GPIO_PIN_SET : GPIO_PIN_RESET);
  HAL_GPIO_WritePin(GPIOB, GPIO_PIN_10,
                    charge_control.inhibit ? GPIO_PIN_SET : GPIO_PIN_RESET);
}
void solar_probe(uint32_t now) {
  // Independent 18ohm/25W test resistor + protected MOSFET on solar 12V output.
  // It is downstream of source INA, upstream of transfer relay; never on the
  // bus.
  if (control.source == 1) {
    probe = 0;
    if (volts[2] < 11.4f) {
      solar_capacity = 0;
      qualified_at = 0;
    }
    return;
  }
  if (!probe && now - probe_at >= 60000 && control.source == 2) {
    probe = 1;
    probe_at = now;
  }
  if (probe == 1 && now - probe_at >= 500)
    probe = 2;
  if (probe == 2 && now - probe_at >= 2500) {
    if ((health & 4) && volts[2] >= 11.7f && volts[2] * amps[2] >= 7.5f) {
      solar_capacity =
          7.5f; // Capacity bound no greater than the proof threshold.
      qualified_at = now;
    } else {
      solar_capacity = 0;
      qualified_at = 0;
    }
    probe = 0;
  }
  if (qualified_at && now - qualified_at > 90000) {
    solar_capacity = 0;
    qualified_at = 0;
  }
}
void acknowledge(uint16_t id, uint8_t status) {
  uint8_t p[32], b[3];
  put16(b, id);
  b[2] = status;
  size_t n = packet(p, status ? NACK : ACK, 2, id, HAL_GetTick(), b, 3);
  serial_send(p, n);
}
void command(uint8_t *p, size_t n) {
  if (!valid_packet(p, n))
    return;
  uint16_t id = get16(p + 4);
  if (p[2] == HEARTBEAT && p[3] == 3) {
    last_gateway = HAL_GetTick();
    return;
  }
  if (p[2] != CONTROL || p[3] != 9 || p[10] != 4)
    return;
  if (command_seen && id == last_command) {
    acknowledge(id, 0);
    return;
  }
  uint8_t *q = p + 11;
  uint8_t status = 0;
  if (q[0] == 3 || q[0] == 4) {
    if (q[0] == 3 && (q[1] > 3 || q[2] > 1 || !q[3]))
      status = 2;
    else if (pending_n || waiting)
      status = 4;
    else {
      uint8_t b[2] = {q[1], q[2]};
      pending_n = packet(
          pending, q[0] == 3 ? PANEL_ISOLATION_REQUEST : MEASUREMENT_REQUEST, 2,
          id, HAL_GetTick(), b, q[0] == 3 ? 2 : 1);
      waiting_id = id;
      attempts = 0;
    }
  } else if (health != 127)
    status = 3;
  else
    status = control_command(&control, q, telemetry.solar_w, volts[0], soc);
  if (!status) {
    last_command = id;
    command_seen = 1;
    if (q[0] == 6)
      service_at = HAL_GetTick();
  }
  if ((q[0] != 3 && q[0] != 4) || status)
    acknowledge(id, status);
}
// Minimal ST7735 RGB565 driver and compact 5x7 text, no framebuffer.
void tcmd(uint8_t c, const uint8_t *d, int n) {
  HAL_GPIO_WritePin(GPIOB, GPIO_PIN_12, GPIO_PIN_RESET);
  HAL_GPIO_WritePin(GPIOB, GPIO_PIN_13, GPIO_PIN_RESET);
  HAL_SPI_Transmit(&spi, &c, 1, 2);
  HAL_GPIO_WritePin(GPIOB, GPIO_PIN_13, GPIO_PIN_SET);
  if (n)
    HAL_SPI_Transmit(&spi, (uint8_t *)d, n, 8);
  HAL_GPIO_WritePin(GPIOB, GPIO_PIN_12, GPIO_PIN_SET);
}
void area(int x, int y, int w, int h, uint16_t color) {
  uint8_t a[4] = {0, x, 0, x + w - 1}, b[4] = {0, y, 0, y + h - 1};
  tcmd(0x2a, a, 4);
  tcmd(0x2b, b, 4);
  tcmd(0x2c, 0, 0);
  uint8_t pixels[256];
  for (int i = 0; i < 256; i += 2) {
    pixels[i] = color >> 8;
    pixels[i + 1] = color;
  }
  HAL_GPIO_WritePin(GPIOB, GPIO_PIN_12, GPIO_PIN_RESET);
  for (int left = w * h; left > 0; left -= 128)
    HAL_SPI_Transmit(&spi, pixels, (left > 128 ? 128 : left) * 2, 4);
  HAL_GPIO_WritePin(GPIOB, GPIO_PIN_12, GPIO_PIN_SET);
}
// Glyphs for ASCII 32..95, stored as five vertical columns.
#include "font.h"
void text(int x, int y, const char *s, uint16_t color) {
  for (; *s && x < 122; s++, x += 6) {
    unsigned c = (unsigned char)*s;
    if (c >= 'a' && c <= 'z')
      c -= 32;
    if (c < 32 || c > 95)
      c = '?';
    for (int col = 0; col < 5; col++)
      for (int bit = 0; bit < 7; bit++)
        if (font[c - 32][col] & (1 << bit))
          area(x + col, y + bit, 1, 1, color);
  }
}
void display_init(void) {
  HAL_GPIO_WritePin(GPIOB, GPIO_PIN_14, GPIO_PIN_RESET);
  HAL_Delay(5);
  HAL_GPIO_WritePin(GPIOB, GPIO_PIN_14, GPIO_PIN_SET);
  HAL_Delay(10);
  tcmd(1, 0, 0);
  HAL_Delay(130);
  tcmd(0x11, 0, 0);
  HAL_Delay(130);
  uint8_t b = 5;
  tcmd(0x3a, &b, 1);
  b = 0;
  tcmd(0x36, &b, 1);
  tcmd(0x29, 0, 0);
  area(0, 0, 128, 160, 0x0841);
}
void display(uint32_t now) {
  char lines[9][24];
  memset(lines, 0, sizeof(lines));
  const char *titles[] = {"OVERVIEW",    "SOLAR ARRAY", "BATTERY", "LOADS",
                          "LINK STATUS", "FAULTS",      "SETTINGS"};
  snprintf(lines[0], 24, "%s %d/7", titles[page], page + 1);
  if (page == 0) {
    snprintf(lines[1], 24, "SOURCE %s",
             control.source == 1   ? "SOLAR"
             : control.source == 2 ? "BATTERY"
                                   : "OFF");
    snprintf(lines[2], 24, "SOC ~%d%%", (int)(soc * 100));
    snprintf(lines[3], 24, "PV %.1fW", telemetry.solar_w);
    snprintf(lines[4], 24, "LOAD %.1fW", telemetry.load_w);
    snprintf(lines[5], 24, "STATE %u", control.state);
    snprintf(lines[6], 24, "LORA %s",
             now - last_radio < 180000 ? "OK" : "STALE");
  }
  if (page == 1) {
    for (int i = 0; i < 4; i++)
      snprintf(lines[1 + i], 24, "PV%d %.1fW %s", i + 1,
               solar_report.panel_power[i],
               solar_report.isolated & (1 << i) ? "OFF" : "ON");
    snprintf(lines[5], 24, "A %.1fV %.2fA", solar_report.cluster[0][2],
             solar_report.cluster[0][3]);
    snprintf(lines[6], 24, "B %.1fV %.2fA", solar_report.cluster[1][2],
             solar_report.cluster[1][3]);
  }
  if (page == 2) {
    snprintf(lines[1], 24, "PACK %.3fV", volts[0]);
    snprintf(lines[2], 24, "I %.3fA +DISCH", amps[0]);
    snprintf(lines[3], 24, "SOC EST %d%%", (int)(soc * 100));
    snprintf(lines[4], 24, "CALIBRATE INITIAL SOC");
    snprintf(lines[5], 24, "UV %.2fV", 3.35);
  }
  if (page == 3) {
    for (int i = 0; i < 3; i++)
      snprintf(lines[1 + i], 24, "%cL%d P%d %s %.1fW", row == i ? '>' : ' ',
               i + 1, i + 1, control.mask & (1 << i) ? "ON" : "OFF",
               telemetry.load[i]);
    snprintf(lines[5], 24, "SELECT TO TOGGLE");
  }
  if (page == 4) {
    snprintf(lines[1], 24, "RADIO %s", radio_ok ? "READY" : "FAULT");
    snprintf(lines[2], 24, "RX%lu TX%lu", (unsigned long)radio.rx_count,
             (unsigned long)radio.tx_count);
    snprintf(lines[3], 24, "RSSI%d SNR%d", radio.rssi, radio.snr);
    snprintf(lines[4], 24, "UART %s",
             now - last_gateway < 6000 ? "OK" : "STALE");
    snprintf(lines[5], 24, "ERROR %lu", (unsigned long)stream.errors);
  }
  if (page == 5) {
    snprintf(lines[1], 24, "LOAD FAULTS %X", load_fault);
    snprintf(lines[2], 24, "PV FAULTS %X", solar_report.faults);
    snprintf(lines[3], 24, "ISOLATED %X", solar_report.isolated);
    snprintf(lines[4], 24, "AGE %lus",
             (unsigned long)((now - fault_at) / 1000));
    snprintf(lines[5], 24, "SELECT ACK ONLY");
  }
  if (page == 6) {
    snprintf(lines[1], 24, "%cAUTO", row == 0 ? '>' : ' ');
    snprintf(lines[2], 24, "%cFORCE SOLAR", row == 1 ? '>' : ' ');
    snprintf(lines[3], 24, "%cFORCE BATTERY", row == 2 ? '>' : ' ');
    snprintf(lines[4], 24, "%cALL OFF", row == 3 ? '>' : ' ');
    snprintf(lines[6], 24, "HOLD SELECT: AUTO");
  }
  if (confirm) {
    snprintf(lines[6], 24, "SELECT CONFIRM");
    snprintf(lines[7], 24, "LEFT CANCEL");
  }
  // Redraw one row per call, bounding SPI occupancy and fault latency.
  static uint8_t line = 0;
  area(0, line * 17, 128, 15, line == 0 ? 0x1249 : 0x0841);
  text(2, line * 17 + 3, lines[line], line == 0 ? 0x5ff7 : 0xffff);
  line = (line + 1) % 9;
}
void button_action(int b, int held) {
  if (held && b == 4) {
    control.manual_source = -1;
    control.inhibited = load_fault;
    confirm = 0;
    return;
  }
  if (b == 2) {
    if (confirm)
      confirm = 0;
    else
      page = (page + 6) % 7;
    return;
  }
  if (b == 3) {
    page = (page + 1) % 7;
    row = 0;
    confirm = 0;
    return;
  }
  if (b == 0) {
    row = (row + 3) % 4;
    return;
  }
  if (b == 1) {
    row = (row + 1) % 4;
    return;
  }
  if (b != 4)
    return;
  if (confirm) {
    int result =
        control_command(&control, requested, telemetry.solar_w, volts[0], soc);
    (void)result;
    control.inhibited |= load_fault;
    confirm = 0;
    return;
  }
  if (page == 3 && row < 3) {
    requested[0] = 1;
    requested[1] = row;
    requested[2] = !(control.mask & (1 << row));
    requested[3] = 1;
    confirm = 1;
  }
  if (page == 6) {
    requested[0] = row == 0 ? 5 : 2;
    requested[1] = 0;
    requested[2] = row == 3 ? 0 : row;
    requested[3] = 1;
    confirm = 1;
  }
  if (page == 5)
    last_fault = load_fault;
}
void buttons(uint32_t now) {
  GPIO_TypeDef *ports[5] = {GPIOA, GPIOA, GPIOB, GPIOB, GPIOB};
  uint16_t pins[5] = {GPIO_PIN_0, GPIO_PIN_1, GPIO_PIN_3, GPIO_PIN_4,
                      GPIO_PIN_5};
  static uint8_t raw[5] = {0}, stable[5] = {0}, long_sent[5] = {0};
  static uint32_t change[5] = {0}, pressed[5] = {0};
  for (int i = 0; i < 5; i++) {
    uint8_t down = HAL_GPIO_ReadPin(ports[i], pins[i]) == GPIO_PIN_RESET;
    if (down != raw[i]) {
      raw[i] = down;
      change[i] = now;
    }
    if (now - change[i] >= 30 && stable[i] != down) {
      stable[i] = down;
      if (down) {
        pressed[i] = now;
        long_sent[i] = 0;
      } else if (!long_sent[i])
        button_action(i, 0);
    }
    if (stable[i] && !long_sent[i] && now - pressed[i] > 1000) {
      long_sent[i] = 1;
      button_action(i, 1);
    }
  }
}
int main(void) {
  init_hw();
  charge_init(&charge_control);
  control_init(&control);
  for (int i = 0; i < 7; i++)
    volts[i] = amps[i] = NAN;
  memset(&solar_report, 0, sizeof(solar_report));
  solar_report.isolated = 15;
  radio.select = rselect;
  radio.transfer = transfer;
  radio.ms = HAL_GetTick;
  HAL_GPIO_WritePin(GPIOB, GPIO_PIN_0, GPIO_PIN_RESET);
  HAL_Delay(2);
  HAL_GPIO_WritePin(GPIOB, GPIO_PIN_0, GPIO_PIN_SET);
  HAL_Delay(10);
  radio_ok = radio_init(&radio);
  display_init();
  uint8_t raw[256];
  for (;;) {
    uint32_t now = HAL_GetTick();
    HAL_IWDG_Refresh(&watchdog);
    buttons(now);
    if (now - sense_at >= 30) {
      sense_at = now;
      acquire(now);
      if (HAL_ADC_Start(&pv_adc) == HAL_OK &&
          HAL_ADC_PollForConversion(&pv_adc, 2) == HAL_OK)
        pv_voltage = HAL_ADC_GetValue(&pv_adc) * (3.3f / 4095.f) *
                     5.7f; // 47k/10k divider; calibrate VDDA/ratio.
      else
        pv_voltage = NAN;
      HAL_ADC_Stop(&pv_adc);
    }
    int valid = health == 127;
    for (int i = 0; i < 7; i++)
      if (now - sensor_at[i] > 1000)
        valid = 0;
    // A loaded 8W qualification test supplies a conservative capacity bound.
    solar_probe(now);
    float solar = solar_capacity;
    if (control.source == 1 && volts[2] < 11.4f)
      solar = 0;
    if (control.pending == 1 && now - control.transfer >= 250 &&
        volts[2] < 11.7f)
      solar = 0;
    control.battery_ready = (health & 8) && volts[3] >= 11.7f;
    if (control.source) {
      if (!source_active_at)
        source_active_at = now;
      if (now - source_active_at > 2000 &&
          (volts[1] < 10.5f || volts[1] > 13.0f))
        actuation_fault = 1;
    } else
      source_active_at = 0;
    control.inhibited |= load_fault;
    if (now - service_at > 30000)
      control.service_budget = 6;
    control_step(&control, now, solar, volts[0], soc,
                 valid && !actuation_fault);
    charge_step(&charge_control, now, pv_voltage, valid && !actuation_fault,
                probe || control.pending ||
                    (control.source == 1 && volts[2] < 11.7f));
    outputs();
    while (__HAL_UART_GET_FLAG(&uart, UART_FLAG_RXNE)) {
      uint8_t b = (uint8_t)uart.Instance->DR;
      size_t n = stream_byte(&stream, b, raw);
      if (n)
        command(raw, n);
    }
    if (__HAL_UART_GET_FLAG(&uart, UART_FLAG_ORE))
      __HAL_UART_CLEAR_OREFLAG(&uart);
    if (radio_ok) {
      size_t n = radio_receive(&radio, raw);
      if (n && valid_packet(raw, n) && raw[3] == 1) {
        last_radio = now;
        if ((raw[2] == SENSOR_REPORT || raw[2] == MEASUREMENT_RESPONSE) &&
            raw[10] == sizeof(SensorReport))
          memcpy(&solar_report, raw + 11, sizeof(solar_report));
        if (waiting && (((raw[2] == ACK || raw[2] == NACK) && raw[10] == 3 &&
                         get16(raw + 11) == waiting_id) ||
                        raw[2] == MEASUREMENT_RESPONSE)) {
          waiting = 0;
          pending_n = 0;
        }
        serial_send(raw, n);
      }
      if (pending_n && !waiting && radio_send(&radio, pending, pending_n)) {
        waiting = 1;
        sent_at = now;
        attempts++;
      }
      if (waiting && now - sent_at > 15000) {
        waiting = 0;
        if (attempts >= 3) {
          acknowledge(waiting_id, 5);
          pending_n = 0;
        }
      }
    }
    if (load_fault != last_fault) {
      fault_at = now;
      last_fault = load_fault;
    }
    if (now - report_at >= 1000) {
      report_at = now;
      telemetry = (CentralReport){
          volts[0], amps[0], soc, volts[1],       solar,        0,
          {0},      {0},     {0}, control.source, control.mask, control.state,
          health};
      for (int i = 0; i < 3; i++) {
        telemetry.load[i] = volts[i + 4] * amps[i + 4];
        telemetry.load_v[i] = volts[i + 4];
        telemetry.load_a[i] = amps[i + 4];
        if (isfinite(telemetry.load[i]))
          telemetry.load_w += telemetry.load[i];
      }
      size_t n = packet(raw, CENTRAL_REPORT, 2, ++sequence, now, &telemetry,
                        sizeof(telemetry));
      serial_send(raw, n);
      uint8_t charge_status[5];
      memcpy(charge_status, &pv_voltage, 4);
      charge_status[4] = charge_control.inhibit;
      n = packet(raw, PANEL_REPORT, 2, ++sequence, now, charge_status, 5);
      serial_send(raw, n);
    }
    if (now - display_at >= 30) {
      display_at = now;
      display(now);
    }
  }
}
