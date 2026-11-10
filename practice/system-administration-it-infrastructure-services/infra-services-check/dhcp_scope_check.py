"""
dhcp_scope_check.py - validate a DHCP scope design BEFORE you type it into a DHCP server.

Catches the mistakes that cause real tickets: gateway inside the dynamic pool, reservations that
collide with the pool or each other, static devices not excluded, a pool too small for the devices,
DNS servers on the wrong subnet with no route, absurd lease times.

Usage:
    python dhcp_scope_check.py                     # checks scope.json (has deliberate mistakes)
    python dhcp_scope_check.py my-scope.json
"""

import ipaddress
import json
import sys
from collections import Counter
from pathlib import Path


def check(cfg: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    net = ipaddress.ip_network(cfg["subnet"])
    start, end = (ipaddress.ip_address(cfg["pool"][k]) for k in ("start", "end"))
    gateway = ipaddress.ip_address(cfg["gateway"])
    exclusions = {ipaddress.ip_address(x) for x in cfg.get("exclusions", [])}
    pool = {ipaddress.ip_address(i) for i in range(int(start), int(end) + 1)} - exclusions

    def inside(ip):
        return ip in net

    for label, ip in (("pool start", start), ("pool end", end), ("gateway", gateway)):
        if not inside(ip):
            errors.append(f"{label} {ip} is outside the subnet {net}")
    if start > end:
        errors.append("pool start is after pool end")
    if ip_is_special(start, net) or ip_is_special(end, net):
        errors.append(f"pool includes the network ID or broadcast address of {net}")
    if gateway in pool:
        errors.append(f"gateway {gateway} is inside the dynamic pool - DHCP could hand it to a laptop "
                      "(IP conflict with the router = whole subnet offline)")

    # Reservations
    res = cfg.get("reservations", [])
    macs = Counter(r["mac"].upper() for r in res)
    ips = Counter(r["ip"] for r in res)
    for mac, n in macs.items():
        if n > 1:
            errors.append(f"MAC {mac} has {n} reservations")
    for ip, n in ips.items():
        if n > 1:
            errors.append(f"IP {ip} is reserved for {n} different devices")
    for r in res:
        ip = ipaddress.ip_address(r["ip"])
        if not inside(ip):
            errors.append(f"reservation {r['name']} {ip} is outside {net}")
        if ip == gateway:
            errors.append(f"reservation {r['name']} uses the gateway address {ip}")
        if ip in pool:
            warnings.append(f"reservation {r['name']} {ip} is inside the pool - fine on Windows DHCP "
                            "(it won't lease it), but many admins keep reservations outside the pool for clarity")

    # Static devices (configured by hand on the device) must never be leasable
    for s in cfg.get("static_devices", []):
        ip = ipaddress.ip_address(s["ip"])
        if ip in pool:
            errors.append(f"static device {s['name']} {ip} is inside the pool and NOT excluded "
                          "-> sooner or later DHCP leases it to someone else = IP conflict")
        if ip == gateway and s["name"].lower() not in ("router", "gateway", "firewall"):
            errors.append(f"static device {s['name']} uses the gateway address")

    # Capacity
    expected = cfg.get("expected_clients", 0)
    if expected:
        free = len(pool) - sum(1 for r in res if ipaddress.ip_address(r["ip"]) in pool)
        if free < expected:
            errors.append(f"pool has {free} leasable addresses for {expected} expected clients -> "
                          "scope exhaustion (new devices get 169.254.x.x)")
        elif free < expected * 1.2:
            warnings.append(f"pool has {free} addresses for {expected} clients - under 20% headroom")

    # Options
    for dns in cfg.get("dns_servers", []):
        d = ipaddress.ip_address(dns)
        if d.is_private and not inside(d) and not cfg.get("routed_networks"):
            warnings.append(f"DNS server {dns} is on another private subnet - make sure it's routed/reachable")
    hours = cfg.get("lease_hours", 8)
    if hours < 1:
        warnings.append(f"lease time {hours} h is very short - lots of DHCP traffic")
    if hours > 24 * 8 and cfg.get("guest", False):
        warnings.append(f"lease time {hours} h on a guest network - visitors' addresses stay tied up for days")
    return errors, warnings


def ip_is_special(ip, net) -> bool:
    return ip in (net.network_address, net.broadcast_address)


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "scope.json"
    cfg = json.loads(path.read_text(encoding="utf-8"))
    print(f"Scope '{cfg['name']}': {cfg['subnet']}, pool {cfg['pool']['start']} - {cfg['pool']['end']}, "
          f"gateway {cfg['gateway']}\n")
    errors, warnings = check(cfg)
    for e in errors:
        print(f"  [ERROR] {e}")
    for w in warnings:
        print(f"  [WARN ] {w}")
    if not errors and not warnings:
        print("  Scope design looks good.")
    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
