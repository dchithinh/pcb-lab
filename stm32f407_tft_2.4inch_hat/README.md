# stm32f407_tft_2.4inch_hat

KiCad project: a **plug-on HAT** for the **STM32F407 Discovery**.  
Schematic and PCB only — no firmware in this repo.

**Not** Arduino / Nucleo shield spacing. Mate the Discovery **P1/P2** headers (copy the hole grid and 3.3 V / 5 V / GND from ST’s Discovery schematic / UM1472).

## Goal

One board you can solder and plug onto the Discovery:

| Block | On the HAT |
|--------|------------|
| SPI display | 2.4" ILI9341: SCK, MOSI, MISO, CS, D/C, RST, LED |
| I2C | Shared bus, pull-ups, extra connector (Grove / 2.54" / Qwiic) for sensors (e.g. HDC1080) |
| USART A | Debug console header (USB–UART) |
| USART B | ESP32 TX/RX (plus RST, BOOT) — **unstuffed** on first spin is fine |
| Power | 3.3 V / GND from Discovery; ESP32 uses a **5 V → 3.3 V LDO** on the HAT |

STM32 = application MCU. ESP32 (later) = Wi‑Fi / OTA sidecar.

## Rev 0 (draw this first)

1. Discovery header: power + the SPI / I2C / UART pins you choose.
2. ILI9341 module footprint or a 2.54" display header.
3. I2C: sensor + connector + **2.2k–4.7k to 3.3 V**.
4. Backlight (GPIO or MOSFET).
5. ESP32-WROOM (or 2.54" socket) + LDO, **do-not-populate**.
6. Jumpers so ESP32 UART can be isolated from the console.
7. Scope pads: SCK, MOSI, CS, SCL, SDA, GND.
8. ERC → **2-layer** board, silk `HAT v0`.

Leave RTOS / OTA / UI out of this project. They belong in firmware elsewhere.

## Electrical

- F407 I/O is **3.3 V only**. Use a 3.3 V LCD module, or regulate 5 V on the HAT.
- Common **GND**.
- Discovery **3.3 V** is weak for ESP32 TX current — do not power ESP32 from that rail alone.
- I2C pull-ups on the **HAT**, to 3.3 V.

## Pins to avoid (onboard Discovery)

| Avoid | Why |
|--------|-----|
| I2C1 **PB6 / PB9** | Audio codec |
| SPI1 **PA5 / PA6 / PA7** | MEMS |

Prefer **I2C2** (e.g. PB10 SCL, PB11 SDA) and **SPI2** (e.g. PB13 SCK, PB15 MOSI, PB14 MISO, GPIO CS). Confirm alternate functions in the STM32F407 datasheet before you lock the netlist.

## Pin table (fill when you pick nets)

| Net | F407 pin | HAT |
|-----|----------|-----|
| SPI_SCK | | ILI9341 SCK |
| SPI_MOSI | | SDI |
| SPI_MISO | | SDO (optional) |
| LCD_CS | GPIO | CS |
| LCD_DC | GPIO | D/C |
| LCD_RST | GPIO | RESET |
| LCD_LED | GPIO | LED |
| I2C_SCL | PB10 (I2C2) | SCL on both 1×4 headers |
| I2C_SDA | PB11 (I2C2) | SDA on both 1×4 headers |
| UART_DBG_TX / RX | PA2 / PA3 (USART2) | UART1 header (MCU TX → adapter RX) |
| UART_ESP_TX / RX | | ESP32 |
| ESP_RST / BOOT | GPIO | ESP32 |
| 3V3 / 5V / GND | header | power |

## Files

| File | Role |
|------|------|
| `stm32f407_tft_2.4inch_hat.kicad_pro` | Project |
| `stm32f407_tft_2.4inch_hat.kicad_sch` | Schematic |
| `stm32f407_tft_2.4inch_hat.kicad_pcb` | Board |
