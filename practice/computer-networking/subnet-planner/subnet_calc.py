"""
subnet_calc.py - subnet math done by hand (bitwise AND/OR), cross-checked against Python's ipaddress.

Usage:
    python subnet_calc.py 192.168.10.70/26
    python subnet_calc.py 10.1.5.200 255.255.240.0
    python subnet_calc.py same 192.168.1.10 192.168.1.200 25      # are two hosts on the same subnet?
                                                                  # (prefix can be 25, /25 or 255.255.255.128;
                                                                  #  Git Bash mangles a bare "/25" into a path)
    python subnet_calc.py quiz                                    # 5 random practice questions
"""

import ipaddress
import random
import sys


def ip_to_int(ip: str) -> int:
    parts = [int(p) for p in ip.split(".")]
    if len(parts) != 4 or any(not 0 <= p <= 255 for p in parts):
        raise ValueError(f"bad IPv4 address: {ip}")
    return (parts[0] << 24) | (parts[1] << 16) | (parts[2] << 8) | parts[3]


def int_to_ip(n: int) -> str:
    return ".".join(str((n >> shift) & 0xFF) for shift in (24, 16, 8, 0))


def to_bits(n: int) -> str:
    b = f"{n:032b}"
    return ".".join(b[i:i + 8] for i in range(0, 32, 8))


def mask_from_prefix(prefix: int) -> int:
    return (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF


def prefix_from_mask(mask: str) -> int:
    m = ip_to_int(mask)
    prefix = bin(m).count("1")
    if mask_from_prefix(prefix) != m:
        raise ValueError(f"{mask} is not a valid subnet mask (1s must be contiguous)")
    return prefix


def parse(args: list[str]) -> tuple[str, int]:
    if len(args) == 1 and "/" in args[0]:
        ip, prefix = args[0].split("/")
        return ip, int(prefix)
    if len(args) == 2:
        return args[0], prefix_from_mask(args[1]) if "." in args[1] else int(args[1].lstrip("/"))
    raise SystemExit(__doc__)


def classify(ip: int) -> str:
    first = ip >> 24
    if first == 127:
        return "loopback"
    if (ip >> 16) == (169 << 8 | 254):
        return "link-local / APIPA (no DHCP!)"
    if first == 10 or (ip >> 20) == (172 << 4 | 1) or (ip >> 16) == (192 << 8 | 168):
        return "private (RFC 1918)"
    if 224 <= first <= 239:
        return "multicast (class D)"
    return "public"


def legacy_class(ip: int) -> str:
    first = ip >> 24
    for limit, cls in ((127, "A"), (191, "B"), (223, "C"), (239, "D")):
        if first <= limit:
            return cls
    return "E"


def calc(ip_str: str, prefix: int) -> dict:
    ip = ip_to_int(ip_str)
    mask = mask_from_prefix(prefix)
    wildcard = ~mask & 0xFFFFFFFF
    network = ip & mask              # AND keeps the network bits, zeroes the host bits
    broadcast = network | wildcard   # OR sets every host bit to 1
    host_bits = 32 - prefix
    if prefix == 32:
        first, last, usable = network, network, 1
    elif prefix == 31:               # RFC 3021: point-to-point links use both addresses
        first, last, usable = network, broadcast, 2
    else:
        first, last, usable = network + 1, broadcast - 1, 2 ** host_bits - 2
    return dict(ip=ip, mask=mask, wildcard=wildcard, network=network, broadcast=broadcast,
                first=first, last=last, usable=usable, prefix=prefix, host_bits=host_bits)


def show(ip_str: str, prefix: int) -> None:
    r = calc(ip_str, prefix)
    print(f"Address     : {ip_str}/{prefix}   ({classify(r['ip'])}, legacy class {legacy_class(r['ip'])})\n")
    print(f"  IP        {to_bits(r['ip'])}   {int_to_ip(r['ip'])}")
    print(f"  Mask      {to_bits(r['mask'])}   {int_to_ip(r['mask'])}")
    print(f"  {'-' * 35} AND")
    print(f"  Network   {to_bits(r['network'])}   {int_to_ip(r['network'])}")
    print(f"  Broadcast {to_bits(r['broadcast'])}   {int_to_ip(r['broadcast'])}  (network OR wildcard)\n")
    block = 2 ** r["host_bits"]
    print(f"Wildcard    : {int_to_ip(r['wildcard'])}   (used in ACLs / OSPF)")
    print(f"Host bits   : {r['host_bits']} -> 2^{r['host_bits']} = {block} addresses, {r['usable']} usable")
    print(f"Host range  : {int_to_ip(r['first'])} - {int_to_ip(r['last'])}")
    if r["host_bits"] <= 8 and prefix >= 24:
        octet_mask = r["mask"] & 0xFF
        print(f"Shortcut    : block size = 256 - {octet_mask} = {256 - octet_mask}; "
              f"subnets start at {', '.join(str(i) for i in range(0, 256, 256 - octet_mask)[:8])}"
              f"{' ...' if 256 // (256 - octet_mask) > 8 else ''}")

    # Cross-check with the standard library - if these ever disagree, the hand math is wrong.
    net = ipaddress.ip_network(f"{ip_str}/{prefix}", strict=False)
    assert str(net.network_address) == int_to_ip(r["network"])
    assert str(net.broadcast_address) == int_to_ip(r["broadcast"])
    print("Check       : matches Python's ipaddress module ✓")


def same_subnet(a: str, b: str, prefix: int) -> None:
    mask = mask_from_prefix(prefix)
    na, nb = ip_to_int(a) & mask, ip_to_int(b) & mask
    print(f"{a:<15} AND /{prefix} -> {int_to_ip(na)}")
    print(f"{b:<15} AND /{prefix} -> {int_to_ip(nb)}")
    if na == nb:
        print("Same network ID -> same subnet: they talk directly (ARP for each other's MAC).")
    else:
        print("Different network IDs -> different subnets: traffic must go through the default gateway.")


def quiz() -> None:
    score = 0
    for i in range(5):
        prefix = random.randint(20, 30)
        ip = int_to_ip(random.choice([10 << 24, 172 << 24 | 16 << 16, 192 << 24 | 168 << 16])
                       + random.randint(0, 2 ** 16 - 1))
        r = calc(ip, prefix)
        print(f"\nQ{i + 1}: {ip}/{prefix}")
        ans_net = input("   Network ID? ").strip()
        ans_bc = input("   Broadcast?  ").strip()
        ans_hosts = input("   Usable hosts? ").strip()
        ok = (ans_net == int_to_ip(r["network"]), ans_bc == int_to_ip(r["broadcast"]),
              ans_hosts == str(r["usable"]))
        score += all(ok)
        print(f"   {'Correct!' if all(ok) else 'Not quite.'} Network {int_to_ip(r['network'])}, "
              f"broadcast {int_to_ip(r['broadcast'])}, {r['usable']} usable hosts")
    print(f"\nScore: {score}/5")


def main() -> None:
    args = sys.argv[1:]
    if not args:
        raise SystemExit(__doc__)
    if args[0] == "quiz":
        return quiz()
    if args[0] == "same":
        if len(args) != 4:
            raise SystemExit("usage: subnet_calc.py same <ip1> <ip2> </prefix or mask>")
        p = args[3]
        prefix = prefix_from_mask(p) if "." in p else int(p.lstrip("/"))
        return same_subnet(args[1], args[2], prefix)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    show(*parse(args))


if __name__ == "__main__":
    main()
