"""
ipv6_tool.py - expand, compress, and classify IPv6 addresses; show the two shortening rules step by step.

Usage:
    python ipv6_tool.py 2001:0db8:0000:0000:0000:ff00:0042:8329
    python ipv6_tool.py fe80::1c2b:3cff:fe4d:5e6f
    python ipv6_tool.py ::1 ::ffff:192.0.2.1 ff02::1
    python ipv6_tool.py mine          # classify the IPv6 addresses on this machine
"""

import ipaddress
import re
import socket
import subprocess
import sys


def shorten_steps(addr: ipaddress.IPv6Address) -> None:
    full = addr.exploded
    groups = full.split(":")
    no_leading = [g.lstrip("0") or "0" for g in groups]
    print(f"  Full form      : {full}")
    print(f"  Rule 1 (drop leading zeros in each group): {':'.join(no_leading)}")
    print(f"  Rule 2 (longest run of 0 groups -> '::', once): {addr.compressed}")


def classify(addr: ipaddress.IPv6Address) -> str:
    if addr.is_loopback:
        return "loopback (::1 = this machine, like 127.0.0.1)"
    if addr.is_unspecified:
        return "unspecified (::) - 'no address yet'"
    if addr.ipv4_mapped:
        return f"IPv4-mapped - represents IPv4 {addr.ipv4_mapped}"
    if addr.is_link_local:
        return "link-local (fe80::/10) - auto-configured, only valid on this network segment"
    if addr.is_multicast:
        known = {"ff02::1": "all nodes on the link", "ff02::2": "all routers on the link"}
        return f"multicast (ff00::/8){' - ' + known[str(addr)] if str(addr) in known else ''} (IPv6 has no broadcast)"
    if addr in ipaddress.ip_network("2001:db8::/32"):
        return "documentation range (2001:db8::/32) - for examples only"
    if addr in ipaddress.ip_network("fc00::/7"):
        return "unique local (fc00::/7) - private, like RFC 1918"
    if addr in ipaddress.ip_network("2000::/3"):
        return "global unicast (2000::/3) - public internet address"
    return "other/reserved"


def describe(text: str) -> None:
    try:
        addr = ipaddress.IPv6Address(text.split("%")[0])  # strip zone id like fe80::1%12
    except ipaddress.AddressValueError as e:
        print(f"{text}: not a valid IPv6 address ({e})\n")
        return
    print(f"{text}")
    shorten_steps(addr)
    print(f"  Type           : {classify(addr)}")
    unicast = not addr.is_multicast and not addr.ipv4_mapped
    if unicast and (addr.is_global or addr.is_link_local or addr in ipaddress.ip_network("fc00::/7")):
        g = addr.exploded.split(":")
        print(f"  /64 split      : prefix {':'.join(g[:4])}  |  interface ID {':'.join(g[4:])}")
        if g[5].endswith("ff") and g[6].startswith("fe"):
            iid = bytes.fromhex("".join(g[4:]))
            mac = bytes([iid[0] ^ 0x02]) + iid[1:3] + iid[5:8]
            print(f"  EUI-64         : interface ID derived from MAC {mac.hex(':')} "
                  "(ff:fe in the middle, U/L bit flipped) - privacy extensions avoid this")
    print(f"  Bits           : 128 ({2 ** 128:.2e} possible addresses)\n")


def mine() -> list[str]:
    if sys.platform == "win32":
        text = subprocess.run(["ipconfig"], capture_output=True, text=True, errors="replace").stdout
        return re.findall(r"IPv6 Address[ .]*: ([0-9a-fA-F:%]+)", text)
    found = set()
    for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET6):
        found.add(info[4][0])
    text = subprocess.run(["ip", "-6", "addr"], capture_output=True, text=True).stdout
    found.update(re.findall(r"inet6 ([0-9a-f:]+)/", text))
    return sorted(found)


def main() -> None:
    args = sys.argv[1:] or ["2001:0db8:0000:0000:0000:ff00:0042:8329"]
    if args == ["mine"]:
        args = mine() or []
        if not args:
            print("No IPv6 addresses found (IPv6 may be disabled on this network).")
        args = args + ["::1"]
    for a in args:
        describe(a)


if __name__ == "__main__":
    main()
