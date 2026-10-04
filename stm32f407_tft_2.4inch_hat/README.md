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

## Net names (schematic = PCB)

Use the **same label on the schematic** as the PCB net (KiCad adds a leading `/` on the board).

| Use on schematic | PCB net | Notes |
|------------------|---------|--------|
| `GND` | `/GND` | |
| `3V` | `/3V` | 3.3 V on 1×4 headers |
| `5V` | `/5V` | Discovery 5 V |
| `VDD` | `/VDD` | Discovery 3.3 V pins (tie to `3V` on the schematic if one rail) |
| `DBG_UART2_TX`, `DBG_UART2_RX` | same | USART2 on **PA2 / PA3** (not USART1) |
| `I2C2_SCL`, `I2C2_SDA` | same | **PB10 / PB11** — not `I2C_SCL` / `I2C_SDA` |
| `LCD_*` | same | Display / SPI2 / SPI3 (see planned column below) |

**Discovery pin** = MCU name on the P1/P2 footprint (`pinfunction`, e.g. `PA2_13` → pad **13** = **PA2**).  
**MCU (Discovery)** in the tables below is that name. **PCB net (now)** is from `stm32f407_tft_2.4inch_hat.kicad_pcb` (many pads do not match plan yet).

Regenerate tables after PCB changes:

```bash
python tools/export_p1_p2_table.py
```

### HAT connectors (PCB)

**`DBG_UART1`** (1×4): 1=`3V`, 2=`DBG_UART2_RX`, 3=`DBG_UART2_TX`, 4=`GND`

**`I2C-Sensor1`** / **`I2C-RealTime1`** (1×4): 1=`I2C2_SCL`, 2=`I2C2_SDA`, 3=`3V`, 4=`GND`

### Planned functional nets (rev 0)

| Function | Discovery | Planned net |
|----------|-----------|-------------|
| USART2 TX / RX | P2 **13** PA2, **14** PA3 | `DBG_UART2_TX`, `DBG_UART2_RX` |
| I2C2 | P2 **33** PB10, **36** PB11 | `I2C2_SCL`, `I2C2_SDA` |
| SPI2 display | P2 **38** PB13, **37** PB14, **40** PB15 | `LCD_SCK`, `LCD_MISO`, `LCD_MOSI` |
| LCD GPIO | P2 **9** PC2, **10** PC3; P1 **34** PD0 | `LCD_RESET`, `LCD_DC`, `LCD_CS` |
| SPI3 touch + SD (shared) | P1 **37** PC10, **36** PC11, **35** PC12 | `LCD_SD_CLK`, `LCD_SD_MISO`, `LCD_SD_MOSI` (alias `LCD_T_CLK`, `LCD_T_MOSI`, `LCD_T_MISO` on same nets) |
| Touch / SD CS, IRQ | P1 **14** PE3, **13** PE4, **40** PA13 | `LCD_T_CS`, `LCD_SD_CS`, `LCD_T_IRQ` |

### P1 (STM32F407-Discovery P1) — full pad map

| Pad | MCU (Discovery) | PCB net (now) | Planned HAT net | Match |
|-----|-----------------|---------------|-----------------|-------|
| 1 | GND | `GND` | - | - |
| 2 | GND | `GND` | - | - |
| 3 | 5V | `PC6` | - | - |
| 4 | 5V | `GND` | - | - |
| 5 | 3V | `PC8` | - | - |
| 6 | 3V | `PC7` | - | - |
| 7 | PH0 | `PA8` | - | - |
| 8 | PH1 | `PC9` | - | - |
| 9 | PC14 | `PA10` | - | - |
| 10 | PC15 | `PA9` | - | - |
| 11 | PE6 | `PA14` | - | - |
| 12 | PE5 | `PA13` | - | - |
| 13 | PE4 | `LCD_SD_CLK` | `LCD_SD_CS` | **no** |
| 14 | PE3 | `PA15` | `LCD_T_CS` | **no** |
| 15 | PE2 | `LCD_SD_MOSI` | - | - |
| 16 | PE1 | `LCD_SD_MISO` | - | - |
| 17 | PE0 | `PD1` | - | - |
| 18 | PB9 | `PD0` | - | - |
| 19 | PB8 | `PD3` | - | - |
| 20 | VDD | `PD2` | - | - |
| 21 | BOOT0 | `PD5` | - | - |
| 22 | PB7 | `PD4` | - | - |
| 23 | PB6 | `PD7` | - | - |
| 24 | PB5 | `PD6` | - | - |
| 25 | PB4 | `PB4` | - | - |
| 26 | PB3 | `PB3` | - | - |
| 27 | PD7 | `PB6` | - | - |
| 28 | PD6 | `PB5` | - | - |
| 29 | PD5 | `BOOT0` | - | - |
| 30 | PD4 | `PB7` | - | - |
| 31 | PD3 | `PB8` | - | - |
| 32 | PD2 | `VDD` | - | - |
| 33 | PD1 | `PE0` | - | - |
| 34 | PD0 | `LCD_CS` | `LCD_CS` | yes |
| 35 | PC12 | `PE2` | `LCD_SD_MOSI` | **no** |
| 36 | PC11 | `PE1` | `LCD_SD_MISO` | **no** |
| 37 | PC10 | `LCD_SD_CS` | `LCD_SD_CLK` | **no** |
| 38 | PA15 | `LCD_T_CS` | - | - |
| 39 | PA14 | `PE6` | - | - |
| 40 | PA13 | `LCD_T_IRQ` | `LCD_T_IRQ` | yes |
| 41 | PA10 | `PC14` | - | - |
| 42 | PA9 | `PC15` | - | - |
| 43 | PA8 | `PH0` | - | - |
| 44 | PC9 | `PH1` | - | - |
| 45 | PC8 | `3V` | - | - |
| 46 | PC7 | `3V` | - | - |
| 47 | PC6 | `5V` | - | - |
| 48 | GND | `5V` | - | - |
| 49 | GND | `GND` | - | - |
| 50 | GND | `GND` | - | - |

### P2 (STM32F407-Discovery P2) — full pad map

| Pad | MCU (Discovery) | PCB net (now) | Planned HAT net | Match |
|-----|-----------------|---------------|-----------------|-------|
| 1 | GND | `GND` | - | - |
| 2 | GND | `GND` | - | - |
| 3 | VDD | `NC` | - | - |
| 4 | VDD | `PD15` | - | - |
| 5 | NRST | `PD14` | - | - |
| 6 | GND | `PD13` | - | - |
| 7 | PC0 | `PD12` | - | - |
| 8 | PC1 | `PD11` | - | - |
| 9 | PC2 | `LCD_RESET` | `LCD_RESET` | yes |
| 10 | PC3 | `LCD_DC` | `LCD_DC` | yes |
| 11 | PA0 | `PD8` | - | - |
| 12 | PA1 | `LCD_MOSI` | - | - |
| 13 | PA2 | `PB14` | `DBG_UART2_TX` | **no** |
| 14 | PA3 | `LCD_SCK` | `DBG_UART2_RX` | **no** |
| 15 | PA4 | `PB12` | - | - |
| 16 | PA5 | `I2C2_SDA` | - | - |
| 17 | PA6 | `I2C2_SCL` | - | - |
| 18 | PA7 | `PE15` | - | - |
| 19 | PC4 | `PE14` | - | - |
| 20 | PC5 | `PE13` | - | - |
| 21 | PB0 | `PE12` | - | - |
| 22 | PB1 | `PE11` | - | - |
| 23 | PB2 | `PE10` | - | - |
| 24 | GND | `PE9` | - | - |
| 25 | PE8 | `PE8` | - | - |
| 26 | PE7 | `PE7` | - | - |
| 27 | PE10 | `PB2` | - | - |
| 28 | PE9 | `GND` | - | - |
| 29 | PE12 | `PB0` | - | - |
| 30 | PE11 | `PB1` | - | - |
| 31 | PE14 | `PC4` | - | - |
| 32 | PE13 | `PC5` | - | - |
| 33 | PB10 | `PA6` | `I2C2_SCL` | **no** |
| 34 | PE15 | `PA7` | - | - |
| 35 | PB12 | `PA4` | - | - |
| 36 | PB11 | `PA5` | `I2C2_SDA` | **no** |
| 37 | PB14 | `DBG_UART2_RX` | `LCD_MISO` | **no** |
| 38 | PB13 | `DBG_UART2_TX` | `LCD_SCK` | **no** |
| 39 | PD8 | `PA0` | - | - |
| 40 | PB15 | `PA1` | `LCD_MOSI` | **no** |
| 41 | PD10 | `LCD_MISO` | - | - |
| 42 | PD9 | `PC3` | - | - |
| 43 | PD12 | `PC0` | - | - |
| 44 | PD11 | `PC1` | - | - |
| 45 | PD14 | `NRST` | - | - |
| 46 | PD13 | `GND` | - | - |
| 47 | NC | `VDD` | - | - |
| 48 | PD15 | `VDD` | - | - |
| 49 | GND | `GND` | - | - |
| 50 | GND | `GND` | - | - |

## Files

| File | Role |
|------|------|
| `stm32f407_tft_2.4inch_hat.kicad_pro` | Project |
| `stm32f407_tft_2.4inch_hat.kicad_sch` | Schematic |
| `stm32f407_tft_2.4inch_hat.kicad_pcb` | Board |
| `tools/export_p1_p2_table.py` | Regenerate P1/P2 pad ↔ net table from PCB |
