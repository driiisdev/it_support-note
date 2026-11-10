"""
vlsm_planner.py - carve one address block into right-sized subnets for each department (VLSM).

VLSM = Variable Length Subnet Masking: instead of giving every department the same /24, each one
gets the smallest subnet that fits its hosts (+ growth). Allocate biggest first so blocks stay aligned.

Usage:
    python vlsm_planner.py                          # uses office-requirements.csv, block 10.20.0.0/22
    python vlsm_planner.py 172.16.8.0/23 my.csv     # custom block + requirements
    python vlsm_planner.py --growth 50              # reserve 50% extra hosts per subnet
"""

import argparse
import csv
import ipaddress
import math
from pathlib import Path

HERE = Path(__file__).parent


def prefix_for(hosts: int) -> int:
    """Smallest prefix whose usable host count (2^h - 2) fits `hosts` (+2 for network & broadcast)."""
    host_bits = max(2, math.ceil(math.log2(hosts + 2)))
    return 32 - host_bits


def plan(block: str, reqs: list[dict], growth_pct: int) -> None:
    network = ipaddress.ip_network(block)
    for r in reqs:
        r["needed"] = math.ceil(int(r["hosts"]) * (1 + growth_pct / 100))
        r["prefix"] = prefix_for(r["needed"])

    # Biggest subnets first: a /24 must start on a multiple of 256, a /26 on a multiple of 64...
    # Allocating large ones first keeps every subnet aligned without gaps.
    reqs.sort(key=lambda r: r["prefix"])

    cursor = int(network.network_address)
    end = int(network.broadcast_address)
    print(f"Block {network} ({network.num_addresses} addresses), growth reserve {growth_pct}%\n")
    print(f"{'NAME':<14}{'VLAN':>5}{'HOSTS':>7}{'NEED':>6}  {'SUBNET':<18}{'MASK':<17}"
          f"{'GATEWAY':<15}{'RANGE':<33}{'FREE':>5}")
    for r in reqs:
        size = 2 ** (32 - r["prefix"])
        if cursor + size - 1 > end:
            print(f"{r['name']:<14} DOES NOT FIT - block {network} is too small for the remaining requirements")
            return
        subnet = ipaddress.ip_network(f"{ipaddress.ip_address(cursor)}/{r['prefix']}")
        hosts = list(subnet.hosts())
        gateway = hosts[0]  # convention: first usable address = router/gateway
        usable = len(hosts) - 1  # minus the gateway
        print(f"{r['name']:<14}{r['vlan']:>5}{r['hosts']:>7}{r['needed']:>6}  {str(subnet):<18}"
              f"{str(subnet.netmask):<17}{str(gateway):<15}{f'{hosts[1]} - {hosts[-1]}':<33}"
              f"{usable - int(r['hosts']):>5}")
        cursor += size

    left = end - cursor + 1
    print(f"\nUnallocated: {left} addresses"
          + (f" starting at {ipaddress.ip_address(cursor)}" if left else ""))
    print("Tip: document this table - it becomes your DHCP scopes and VLAN config.")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("block", nargs="?", default="10.20.0.0/22")
    p.add_argument("csv", nargs="?", default=str(HERE / "office-requirements.csv"))
    p.add_argument("--growth", type=int, default=20, help="extra percent of hosts to reserve")
    args = p.parse_args()
    with open(args.csv, newline="", encoding="utf-8") as f:
        reqs = list(csv.DictReader(f))
    plan(args.block, reqs, args.growth)


if __name__ == "__main__":
    main()
