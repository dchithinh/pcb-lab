#!/usr/bin/env python3
"""Export P1/P2 pad -> MCU pin -> PCB net from kicad_pcb (for README refresh)."""
import re
from pathlib import Path

PCB = Path(__file__).resolve().parent.parent / "stm32f407_tft_2.4inch_hat.kicad_pcb"

# Rev-0 target nets on Discovery pins (footprint pinfunction = MCU name).
PLANNED: dict[tuple[str, int], str] = {
    ("P2", 13): "/DBG_UART2_TX",
    ("P2", 14): "/DBG_UART2_RX",
    ("P2", 33): "/I2C2_SCL",
    ("P2", 36): "/I2C2_SDA",
    ("P2", 37): "/LCD_MISO",
    ("P2", 38): "/LCD_SCK",
    ("P2", 40): "/LCD_MOSI",
    ("P2", 9): "/LCD_RESET",
    ("P2", 10): "/LCD_DC",
    ("P1", 35): "/LCD_SD_MOSI",
    ("P1", 36): "/LCD_SD_MISO",
    ("P1", 37): "/LCD_SD_CLK",
    ("P1", 13): "/LCD_SD_CS",
    ("P1", 14): "/LCD_T_CS",
    ("P1", 40): "/LCD_T_IRQ",
    ("P1", 34): "/LCD_CS",
}


def parse_footprint(block: str) -> list[tuple[int, str, str, str]]:
    pads = []
    for pad_m in re.finditer(r'\(pad "(\d+)"', block):
        start = pad_m.start()
        end = block.find('(pad "', start + 1)
        if end == -1:
            end = len(block)
        chunk = block[start:end]
        net_m = re.search(r'\(net "([^"]+)"\)', chunk)
        pfn_m = re.search(r'\(pinfunction "([^"]+)"\)', chunk)
        if not net_m or not pfn_m:
            continue
        pad = int(pad_m.group(1))
        net = net_m.group(1)
        pfn = pfn_m.group(1)
        mcu = re.sub(r"_\d+$", "", pfn)
        pads.append((pad, mcu, net, pfn))
    return sorted(pads, key=lambda x: x[0])


def markdown_table(ref: str, rows: list[tuple[int, str, str, str]]) -> str:
    lines = [
        f"| Pad | MCU (Discovery) | PCB net (now) | Planned HAT net | Match |",
        f"|-----|-----------------|---------------|-----------------|-------|",
    ]
    for pad, mcu, net, _pfn in rows:
        plan = PLANNED.get((ref, pad), "")
        if not plan:
            match = ""
        elif net == plan:
            match = "yes"
        else:
            match = "**no**"
        plan_disp = f"`{plan.lstrip('/')}`" if plan else "-"
        lines.append(
            f"| {pad} | {mcu} | `{net.lstrip('/')}` | {plan_disp} | {match or '-'} |"
        )
    return "\n".join(lines)


def main() -> None:
    text = PCB.read_text(encoding="utf-8")
    parts = text.split("(footprint ")
    for ref in ("P1", "P2"):
        block = next(p for p in parts if f'"Reference" "{ref}"' in p[:4000])
        rows = parse_footprint(block)
        print(f"### {ref}\n")
        print(markdown_table(ref, rows))
        print()


if __name__ == "__main__":
    main()
