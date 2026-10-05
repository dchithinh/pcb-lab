#!/usr/bin/env python3
"""Set P1/P2 pin silkscreen names to 90 deg, centered on each pad."""
import re
from pathlib import Path

PCB = Path(__file__).resolve().parent.parent / "stm32f407_tft_2.4inch_hat.kicad_pcb"

SKIP_TEXT = {"STM32F407VG-DISC\n2.4 TFT \nVersion 1.0", "P1", "P2"}


def silk_name(pinfunction: str) -> str:
    return re.sub(r"_\d+$", "", pinfunction)


def parse_pads(text: str) -> list[tuple[str, float, float]]:
    pads: list[tuple[str, float, float]] = []
    parts = text.split("(footprint ")
    for ref in ("P1", "P2"):
        block = next(p for p in parts if f'"Reference" "{ref}"' in p[:4000])
        at_fp = re.search(r"\(at ([-\d.]+) ([-\d.]+)", block)
        fx, fy = float(at_fp.group(1)), float(at_fp.group(2))
        for pad_m in re.finditer(r'\(pad "(\d+)"', block):
            start = pad_m.start()
            end = block.find('(pad "', start + 1)
            chunk = block[start : end if end != -1 else len(block)]
            at_m = re.search(r"\(at ([-\d.]+) ([-\d.]+)", chunk)
            pfn_m = re.search(r'\(pinfunction "([^"]+)"\)', chunk)
            if not at_m or not pfn_m:
                continue
            px, py = float(at_m.group(1)), float(at_m.group(2))
            pads.append((silk_name(pfn_m.group(1)), round(fx + px, 4), round(fy + py, 4)))
    return pads


def main() -> None:
    text = PCB.read_text(encoding="utf-8")
    pads = parse_pads(text)
    used: set[int] = set()

    def repl(m: re.Match[str]) -> str:
        name = m.group(1)
        if name in SKIP_TEXT or "\n" in name:
            return m.group(0)
        old_x, old_y = float(m.group(2)), float(m.group(3))
        best_i = None
        best_d = 1e9
        for i, (silk, px, py) in enumerate(pads):
            if i in used or silk != name:
                continue
            d = (old_x - px) ** 2 + (old_y - py) ** 2
            if d < best_d:
                best_d = d
                best_i = i
        if best_i is None:
            return m.group(0)
        used.add(best_i)
        _silk, px, py = pads[best_i]
        return (
            f'(gr_text "{name}"\n'
            f"\t\t(at {px} {py} 90)\n"
            f'\t\t(layer "F.SilkS")\n'
            f'\t\t(uuid "{m.group(4)}")\n'
            f"\t\t(effects\n"
            f"\t\t\t(font\n"
            f"\t\t\t\t(size 0.8 0.6)\n"
            f"\t\t\t\t(thickness 0.08)\n"
            f"\t\t\t)\n"
            f"\t\t)"
        )

    pattern = re.compile(
        r'\(gr_text "([^"]+)"\n'
        r"\t\t\(at ([-\d.]+) ([-\d.]+) [-\d.]+\)\n"
        r'\t\t\(layer "F.SilkS"\)\n'
        r'\t\t\(uuid "([^"]+)"\)\n'
        r"\t\t\(effects\n"
        r"\t\t\t\(font\n"
        r"\t\t\t\t\(size 0.8 0.6\)\n"
        r"\t\t\t\t\(thickness 0.08\)\n"
        r"\t\t\t\)\n"
        r"\t\t\t\(justify (?:left|right|bottom)\)\n"
        r"\t\t\)",
    )
    new, n = pattern.subn(repl, text)
    PCB.write_text(new, encoding="utf-8")
    print(f"Updated {n} silk texts; matched pads {len(used)}/{len(pads)}")


if __name__ == "__main__":
    main()
