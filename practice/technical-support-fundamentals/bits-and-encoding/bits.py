"""
bits.py - binary, encoding, storage units and logic gates, the way a computer sees them.

Usage:
    python bits.py binary 200            # decimal -> binary, with the "subtract powers of 2" steps
    python bits.py decimal 11001000      # binary  -> decimal, with each position's value
    python bits.py encode "Café ☕"       # how text becomes bytes in ASCII vs UTF-8
    python bits.py mojibake "Café"       # what an encoding mismatch looks like to a user
    python bits.py storage 1 TB          # why a "1 TB" drive shows ~931 GB in Windows
    python bits.py gates                 # truth tables for AND / OR / NOT / XOR
    python bits.py color "#1E90FF"       # a hex color as 3 bytes of RGB
"""

import argparse
import sys

# Windows terminals default to a legacy code page; force UTF-8 so emoji/accents print correctly.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def to_binary(n: int) -> None:
    if n < 0:
        sys.exit("Only non-negative integers, please.")
    bits_needed = max(8, n.bit_length())
    # round up to a whole number of bytes so the output looks like what you'd see in a hex editor
    bits_needed = ((bits_needed + 7) // 8) * 8

    print(f"Converting {n} to binary ({bits_needed} bits):\n")
    remaining = n
    bits = []
    for position in range(bits_needed - 1, -1, -1):
        value = 2 ** position
        if value <= remaining:
            print(f"  {remaining:>6} - {value:>6} = {remaining - value:<6} -> 1 in the {value}s place")
            remaining -= value
            bits.append("1")
        else:
            bits.append("0")

    grouped = " ".join("".join(bits[i:i + 4]) for i in range(0, len(bits), 4))
    print(f"\nResult : {grouped}")
    print(f"Check  : Python says bin({n}) = {bin(n)}, hex = {hex(n)}")


def to_decimal(bit_string: str) -> None:
    bit_string = bit_string.replace(" ", "")
    if not bit_string or any(c not in "01" for c in bit_string):
        sys.exit("A binary number may only contain 0 and 1.")

    total = 0
    print(f"Converting {bit_string} to decimal:\n")
    print("  position value :", " ".join(f"{2 ** p:>4}" for p in range(len(bit_string) - 1, -1, -1)))
    print("  bit            :", " ".join(f"{b:>4}" for b in bit_string))
    parts = []
    for position, bit in zip(range(len(bit_string) - 1, -1, -1), bit_string):
        if bit == "1":
            total += 2 ** position
            parts.append(str(2 ** position))
    print(f"\n  {' + '.join(parts) or '0'} = {total}")
    print(f"  Check: int('{bit_string}', 2) = {int(bit_string, 2)}")


def encode(text: str) -> None:
    print(f"Text: {text!r}\n")
    print(f"{'char':<6}{'code point':<12}{'ASCII?':<8}{'UTF-8 bytes (hex)':<22}{'UTF-8 bits'}")
    for ch in text:
        utf8 = ch.encode("utf-8")
        ascii_ok = "yes" if ord(ch) < 128 else "no"
        print(
            f"{ch!s:<6}U+{ord(ch):04X}{'':<6}{ascii_ok:<8}"
            f"{utf8.hex(' '):<22}{' '.join(f'{b:08b}' for b in utf8)}"
        )
    total = len(text.encode("utf-8"))
    print(f"\n{len(text)} characters -> {total} bytes in UTF-8.")
    try:
        text.encode("ascii")
        print("Fits in ASCII (every character < 128).")
    except UnicodeEncodeError as e:
        print(f"Does NOT fit in ASCII: {e.object[e.start]!r} has no 7-bit code.")


def mojibake(text: str) -> None:
    """Show the garbled text a user sees when UTF-8 bytes are decoded with the wrong code page."""
    raw = text.encode("utf-8")
    wrong = raw.decode("cp1252", errors="replace")
    print(f"Original text           : {text}")
    print(f"Saved as UTF-8 bytes    : {raw.hex(' ')}")
    print(f"Opened as Windows-1252  : {wrong}")
    print("\nThat garbage is the classic 'Ã©' ticket: same bytes, wrong lookup table.")
    print("Fix: open/import the file as UTF-8 (e.g. Excel: Data -> From Text/CSV -> File origin 65001: UTF-8).")


UNITS = ["B", "KB", "MB", "GB", "TB", "PB"]


def storage(amount: float, unit: str) -> None:
    unit = unit.upper()
    if unit not in UNITS:
        sys.exit(f"Unit must be one of {UNITS}")
    power = UNITS.index(unit)
    total_bytes = amount * (1000 ** power)  # what the box / drive maker means
    print(f"Advertised: {amount:g} {unit} = {total_bytes:,.0f} bytes (decimal, powers of 1000)\n")
    print("What Windows shows (binary, powers of 1024 - labeled GB but really GiB):")
    binary_units = ["B", "KiB", "MiB", "GiB", "TiB", "PiB"]
    # show the same size one unit below and at the advertised unit, e.g. 931.32 GiB / 0.91 TiB
    for i in range(max(0, power - 1), power + 1):
        print(f"  {total_bytes / (1024 ** i):,.2f} {binary_units[i]}")
    lost_pct = (1 - (1000 / 1024) ** power) * 100 if power else 0
    print(f"\nNothing is missing - the same bytes counted in 1024s look ~{lost_pct:.1f}% smaller.")


def gates() -> None:
    print("Logic gates - the building blocks of every CPU\n")
    print(f"{'A':>3}{'B':>3} | {'AND':>4}{'OR':>4}{'XOR':>5}{'NAND':>6} | {'NOT A':>6}")
    print("-" * 36)
    for a in (0, 1):
        for b in (0, 1):
            print(f"{a:>3}{b:>3} | {a & b:>4}{a | b:>4}{a ^ b:>5}{1 - (a & b):>6} | {1 - a:>6}")

    print("\nA half adder is just XOR (sum) + AND (carry):")
    for a in (0, 1):
        for b in (0, 1):
            print(f"  {a} + {b} = carry {a & b}, sum {a ^ b}  -> binary {a & b}{a ^ b} = {a + b}")

    print("\nAnd AND is how a subnet mask finds a network ID (see the network-layer note):")
    ip, mask = [192, 168, 10, 70], [255, 255, 255, 192]
    net = [i & m for i, m in zip(ip, mask)]
    print(f"  {'.'.join(map(str, ip))} AND {'.'.join(map(str, mask))} = {'.'.join(map(str, net))}")


def color(hex_code: str) -> None:
    hex_code = hex_code.lstrip("#")
    if len(hex_code) != 6:
        sys.exit("Use a 6-digit hex color like #1E90FF")
    r, g, b = (int(hex_code[i:i + 2], 16) for i in (0, 2, 4))
    print(f"#{hex_code.upper()} = 3 bytes = 24 bits")
    for name, v in (("Red", r), ("Green", g), ("Blue", b)):
        print(f"  {name:<6} {v:>3}  {v:08b}  {'#' * (v // 16)}")
    print(f"256^3 = {256 ** 3:,} possible colors")


def main() -> None:
    p = argparse.ArgumentParser(description="See how computers represent numbers, text, and colors.")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("binary").add_argument("number", type=int)
    sub.add_parser("decimal").add_argument("bits")
    sub.add_parser("encode").add_argument("text")
    sub.add_parser("mojibake").add_argument("text")
    s = sub.add_parser("storage")
    s.add_argument("amount", type=float)
    s.add_argument("unit")
    sub.add_parser("gates")
    sub.add_parser("color").add_argument("hex")
    args = p.parse_args()

    {
        "binary": lambda: to_binary(args.number),
        "decimal": lambda: to_decimal(args.bits),
        "encode": lambda: encode(args.text),
        "mojibake": lambda: mojibake(args.text),
        "storage": lambda: storage(args.amount, args.unit),
        "gates": gates,
        "color": lambda: color(args.hex),
    }[args.cmd]()


if __name__ == "__main__":
    main()
