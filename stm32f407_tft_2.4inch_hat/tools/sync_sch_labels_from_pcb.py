#!/usr/bin/env python3
"""P1/P2 schematic: delete leftover pin names in the connector band; one PCB pad-net label per stub."""
import re
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PCB = ROOT / "stm32f407_tft_2.4inch_hat.kicad_pcb"
SCH = ROOT / "stm32f407_tft_2.4inch_hat.kicad_sch"

STUB = {
    "P1": {"left": 74.93, "right": 127.0, "xmin": 70.0, "xmax": 135.0},
    "P2": {"left": 170.18, "right": 223.52, "xmin": 165.0, "xmax": 230.0},
}

PIN_Y_TOL = 0.06
HARNESS_X_ANCHORS = (224.79,)
KEEP_TEXT = {"Pin Extension", "2.4 Inches TFT", "STM32F407DISC Header"}

P1_SYMBOL = '\t(symbol\n\t\t(lib_id "stm32f407_tft_hat:Conn_Discovery_P1_2x25")'

LABEL_BLOCK_RE = re.compile(
    r'\t\(label "([^"]+)"\s*\n'
    r'\t\t\(at ([\d.]+) ([\d.]+)(?: [\d.]+)?\)\s*\n'
    r'\t\t\(effects\s*\n'
    r'(?:.*?\n)*?'
    r'\t\t\(uuid "[^"]+"\)\s*\n'
    r'\t\)\s*\n',
    re.DOTALL,
)

TEXT_BLOCK_RE = re.compile(
    r'\t\(text "([^"]+)"\s*\n'
    r'\t\t\(exclude_from_sim [^\n]+\n'
    r'\t\t\(at ([\d.]+) ([\d.]+)(?: [\d.]+)?\)\s*\n'
    r'\t\t\(effects\s*\n'
    r'(?:.*?\n)*?'
    r'\t\t\(uuid "[^"]+"\)\s*\n'
    r'\t\)\s*\n',
    re.DOTALL,
)


def silk_name(pinfunction: str) -> str:
    return re.sub(r"_\d+$", "", pinfunction)


def parse_pcb_pads() -> dict[tuple[str, int], tuple[str, str]]:
    """(ref, pad) -> (silk, net). Unused by placement; kept for debugging."""
    text = PCB.read_text(encoding="utf-8")
    out: dict[tuple[str, int], tuple[str, str]] = {}
    for ref in ("P1", "P2"):
        block = next(p for p in text.split("(footprint ") if f'"Reference" "{ref}"' in p[:3000])
        for pad_m in re.finditer(r'\(pad "(\d+)"', block):
            start = pad_m.start()
            end = block.find('(pad "', start + 1)
            chunk = block[start : end if end != -1 else len(block)]
            net_m = re.search(r'\(net "([^"]+)"\)', chunk)
            pfn_m = re.search(r'\(pinfunction "([^"]+)"\)', chunk)
            if not net_m or not pfn_m:
                continue
            out[(ref, int(pad_m.group(1)))] = (
                silk_name(pfn_m.group(1)),
                net_m.group(1).lstrip("/"),
            )
    return out


def parse_pcb_nets_by_row() -> dict[tuple[str, int, str], str]:
    """Map PCB pad nets by physical row (0=top) and side, matching the schematic stubs."""
    text = PCB.read_text(encoding="utf-8")
    out: dict[tuple[str, int, str], str] = {}
    for ref in ("P1", "P2"):
        block = next(p for p in text.split("(footprint ") if f'"Reference" "{ref}"' in p[:3000])
        rows: list[tuple[float, str, str]] = []
        for pad_m in re.finditer(r'\(pad "(\d+)"', block):
            start = pad_m.start()
            end = block.find('(pad "', start + 1)
            chunk = block[start : end if end != -1 else len(block)]
            at_m = re.search(r"\(at ([-\d.]+) ([-\d.]+)", chunk)
            net_m = re.search(r'\(net "([^"]+)"\)', chunk)
            if not at_m or not net_m:
                continue
            px, py = float(at_m.group(1)), float(at_m.group(2))
            side = "left" if px < 1.27 else "right"
            rows.append((py, side, net_m.group(1).lstrip("/")))
        ys = sorted({round(py, 2) for py, _side, _net in rows})
        y_to_row = {y: i for i, y in enumerate(ys)}
        for py, side, net in rows:
            out[(ref, y_to_row[round(py, 2)], side)] = net
    return out


def parse_symbol_pins(sch: str, sym: str) -> dict[int, tuple[float, float]]:
    m = re.search(
        rf'\(symbol "Conn_Discovery_{sym}_2x25_1_1"(.*?)\(embedded_fonts',
        sch,
        re.DOTALL,
    )
    if not m:
        raise SystemExit(f"symbol {sym} not found")
    pins: dict[int, tuple[float, float]] = {}
    for chunk in m.group(1).split("(pin passive line")[1:]:
        at_m = re.search(r"\(at ([-\d.]+) ([-\d.]+)", chunk)
        num_m = re.search(r'\(number "(\d+)"', chunk)
        if at_m and num_m:
            pins[int(num_m.group(1))] = (float(at_m.group(1)), float(at_m.group(2)))
    return pins


def parse_instance_xy(sch: str, ref: str) -> tuple[float, float]:
    m = re.search(
        rf'lib_id "stm32f407_tft_hat:Conn_Discovery_{ref}_2x25".*?\(at ([\d.]+) ([\d.]+)',
        sch,
        re.DOTALL,
    )
    if not m:
        raise SystemExit(f"instance {ref} not found")
    return float(m.group(1)), float(m.group(2))


def pcb_pad_for_sch_pin(ref: str, pin: int) -> int:
    """P1 schematic left/right is swapped vs the footprint (1↔2, 3↔4, ...). P2 matches."""
    if ref == "P1":
        return pin + 1 if pin % 2 == 1 else pin - 1
    return pin


def build_targets(sch: str, pcb_pads: dict):
    """Schematic pin N gets the PCB net for the paired pad (P1 swaps odd/even)."""
    net_labels: dict[tuple[str, float, str], str] = {}
    pin_ys: dict[str, set[float]] = {"P1": set(), "P2": set()}
    for ref in ("P1", "P2"):
        pins = parse_symbol_pins(sch, ref)
        _sx, sy = parse_instance_xy(sch, ref)
        for pin, (px, py) in pins.items():
            entry = pcb_pads.get((ref, pcb_pad_for_sch_pin(ref, pin)))
            if not entry:
                continue
            _silk, net = entry
            wy = round(sy + py, 2)
            side = "left" if px < 0 else "right"
            pin_ys[ref].add(wy)
            net_labels[(ref, wy, side)] = net
    return net_labels, pin_ys


def on_pin_row(y: float, ys: set[float]) -> bool:
    return any(abs(y - wy) < PIN_Y_TOL for wy in ys)


def is_harness_label(x: float) -> bool:
    return any(abs(x - hx) < 1.0 for hx in HARNESS_X_ANCHORS)


def in_connector_band(x: float, y: float, pin_ys: dict[str, set[float]]) -> bool:
    if is_harness_label(x):
        return False
    for ref, ys in pin_ys.items():
        if not on_pin_row(y, ys):
            continue
        band = STUB[ref]
        if band["xmin"] <= x <= band["xmax"]:
            return True
    return False


def strip_in_band(sch: str, pin_ys: dict, regex: re.Pattern[str], keep_names: set[str] | None = None) -> str:
    keep_names = keep_names or set()

    def repl(m: re.Match[str]) -> str:
        name, x, y = m.group(1), float(m.group(2)), float(m.group(3))
        if name in keep_names:
            return m.group(0)
        if in_connector_band(x, y, pin_ys):
            return ""
        return m.group(0)

    return regex.sub(repl, sch)


def peel_owned_blocks(sch: str) -> str:
    idx = sch.find(P1_SYMBOL)
    if idx == -1:
        raise SystemExit("P1 symbol marker not found")
    head, tail = sch[:idx], sch[idx:]
    one_block = re.compile(
        r'\t\((?:label|text) "[^"]+"\n'
        r'(?:\t\t.*\n)+'
        r'\t\)\n\Z'
    )
    while True:
        m = one_block.search(head)
        if not m:
            break
        head = head[: m.start()]
    return head + tail


def _label_block(name: str, x: float, y: float, justify: str) -> str:
    return (
        f'\t(label "{name}"\n'
        f"\t\t(at {x} {y} 0)\n"
        f"\t\t(effects\n"
        f"\t\t\t(font\n"
        f"\t\t\t\t(size 1.27 1.27)\n"
        f"\t\t\t)\n"
        f"\t\t\t(justify {justify})\n"
        f"\t\t)\n"
        f'\t\t(uuid "{uuid.uuid4()}")\n'
        f"\t)\n"
    )


def add_blocks(sch: str, net_labels: dict[tuple[str, float, str], str]) -> str:
    blocks: list[str] = []
    for (ref, wy, side), net in sorted(net_labels.items()):
        x = STUB[ref]["left" if side == "left" else "right"]
        justify = "right bottom" if side == "left" else "left bottom"
        blocks.append(_label_block(net, x, wy, justify))
    return sch.replace(P1_SYMBOL, "".join(blocks) + P1_SYMBOL, 1)


def main() -> None:
    sch = SCH.read_text(encoding="utf-8")
    pcb_pads = parse_pcb_pads()
    net_labels, pin_ys = build_targets(sch, pcb_pads)
    print(f"P1/P2 pads: {len(pcb_pads)}; schematic stub labels: {len(net_labels)}")
    sch = strip_in_band(sch, pin_ys, LABEL_BLOCK_RE)
    sch = strip_in_band(sch, pin_ys, TEXT_BLOCK_RE, KEEP_TEXT)
    sch = peel_owned_blocks(sch)
    sch = add_blocks(sch, net_labels)
    SCH.write_text(sch, encoding="utf-8")
    print(f"Wrote {SCH}")


if __name__ == "__main__":
    main()
