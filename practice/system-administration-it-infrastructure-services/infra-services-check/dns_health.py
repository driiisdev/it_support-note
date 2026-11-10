"""
dns_health.py - check that DNS records are what they're SUPPOSED to be, on every DNS server you rely on.

Typical uses: after a migration, before/after changing records, a daily check that the website,
MX, SPF, and internal names haven't drifted.

expected-records.csv columns: name,type,expected
  - `expected` may contain several values separated by `;` (all must be present), or `*` (any answer is fine)
  - for TXT, a value is matched as a substring (so you can check just "v=spf1")

Usage:
    python dns_health.py                                    # expected-records.csv vs 8.8.8.8 and 1.1.1.1
    python dns_health.py --servers 192.168.10.10 8.8.8.8    # compare internal vs public
    python dns_health.py --file my-records.csv
"""

import argparse
import csv
import random
import socket
import struct
from pathlib import Path

TYPES = {"A": 1, "NS": 2, "CNAME": 5, "MX": 15, "TXT": 16, "AAAA": 28}


def _name(msg: bytes, off: int) -> tuple[str, int]:
    labels, end, jumped = [], off, False
    while True:
        n = msg[off]
        if n & 0xC0 == 0xC0:
            if not jumped:
                end = off + 2
            off, jumped = struct.unpack("!H", msg[off:off + 2])[0] & 0x3FFF, True
        elif n == 0:
            return ".".join(labels), (end if jumped else off + 1)
        else:
            labels.append(msg[off + 1:off + 1 + n].decode(errors="replace"))
            off += n + 1


def resolve(name: str, rtype: str, server: str) -> list[str] | str:
    """Minimal raw DNS query (same technique as computer-networking/dns-and-dhcp-lab/dns_query.py)."""
    tid = random.randint(0, 0xFFFF)
    q = struct.pack("!HHHHHH", tid, 0x0100, 1, 0, 0, 0)
    q += b"".join(bytes([len(p)]) + p.encode() for p in name.rstrip(".").split(".")) + b"\x00"
    q += struct.pack("!HH", TYPES[rtype], 1)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(3)
        try:
            s.sendto(q, (server, 53))
            msg, _ = s.recvfrom(4096)
        except OSError:
            return "TIMEOUT"
    flags, qd, an = struct.unpack("!HHH", msg[2:8])
    if flags & 0xF == 3:
        return "NXDOMAIN"
    off = 12
    for _ in range(qd):
        _, off = _name(msg, off)
        off += 4
    out = []
    for _ in range(an):
        _, off = _name(msg, off)
        t, _, _, ln = struct.unpack("!HHIH", msg[off:off + 10])
        off += 10
        data = msg[off:off + ln]
        if t == TYPES[rtype]:
            if t == 1:
                out.append(socket.inet_ntoa(data))
            elif t == 28:
                out.append(socket.inet_ntop(socket.AF_INET6, data))
            elif t in (2, 5):
                out.append(_name(msg, off)[0].lower())
            elif t == 15:
                out.append(_name(msg, off + 2)[0].lower())
            elif t == 16:
                parts, i = [], 0
                while i < len(data):
                    parts.append(data[i + 1:i + 1 + data[i]].decode(errors="replace"))
                    i += data[i] + 1
                out.append("".join(parts))
        off += ln
    if flags & 0x0200 and not out:
        return "TRUNCATED (needs TCP)"
    return out or "NODATA"


def check(expected: str, got, rtype: str) -> tuple[bool, str]:
    if isinstance(got, str):
        return False, got
    if expected.strip() == "*":
        return bool(got), ", ".join(got)
    wanted = [e.strip().lower().rstrip(".") for e in expected.split(";") if e.strip()]
    have = [g.lower().rstrip(".") for g in got]
    if rtype == "TXT":
        missing = [w for w in wanted if not any(w in h for h in have)]
    else:
        missing = [w for w in wanted if w not in have]
    shown = ", ".join(g if len(g) < 60 else g[:57] + "..." for g in got)
    return (not missing), (shown if not missing else f"missing {', '.join(missing)} | got: {shown}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--file", default=str(Path(__file__).parent / "expected-records.csv"))
    p.add_argument("--servers", nargs="+", default=["8.8.8.8", "1.1.1.1"])
    args = p.parse_args()

    with open(args.file, newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["name"] and not r["name"].startswith("#")]

    failures = 0
    for server in args.servers:
        print(f"\n=== DNS server {server} ===")
        for r in rows:
            got = resolve(r["name"], r["type"].upper(), server)
            ok, detail = check(r["expected"], got, r["type"].upper())
            failures += not ok
            if len(detail) > 110:
                detail = detail[:107] + "..."
            print(f"  [{'OK  ' if ok else 'FAIL'}] {r['name']:<28} {r['type']:<6} {detail}")
    print(f"\n{failures} check(s) failed." if failures else "\nAll records as expected.")
    if failures and len(args.servers) > 1:
        print("If a record fails on one server but passes on another: replication/propagation (TTL) "
              "or a split-DNS difference.")
    raise SystemExit(1 if failures else 0)  # non-zero exit lets a scheduler/monitor alert on it


if __name__ == "__main__":
    main()
