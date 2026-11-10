"""
dhcp_dora_sim.py - simulate a DHCP server: scope, exclusions, reservations, leases, renewals, exhaustion.

No real network traffic (real DHCP needs broadcast + admin rights + would fight your router).
The logic is the same as a real server's, so you can watch DORA and its failure modes.

Usage:
    python dhcp_dora_sim.py            # run the scripted scenario
    python dhcp_dora_sim.py --small    # tiny scope to trigger exhaustion -> APIPA
"""

import argparse
import ipaddress
import random


class DHCPServer:
    def __init__(self, network: str, start: str, end: str, gateway: str, dns: list[str],
                 lease_hours: int, exclusions=(), reservations=None):
        self.network = ipaddress.ip_network(network)
        lo, hi = int(ipaddress.ip_address(start)), int(ipaddress.ip_address(end))
        excluded = {ipaddress.ip_address(e) for e in exclusions}
        self.pool = [ipaddress.ip_address(i) for i in range(lo, hi + 1)
                     if ipaddress.ip_address(i) not in excluded]
        self.reservations = {mac.upper(): ipaddress.ip_address(ip) for mac, ip in (reservations or {}).items()}
        self.options = {"subnet mask (opt 1)": str(self.network.netmask), "router (opt 3)": gateway,
                        "DNS servers (opt 6)": ", ".join(dns), "lease time (opt 51)": f"{lease_hours} h"}
        self.lease_hours = lease_hours
        self.leases: dict[str, tuple[ipaddress.IPv4Address, float]] = {}  # mac -> (ip, expires_at_hour)
        self.offers: dict[str, ipaddress.IPv4Address] = {}
        self.clock = 0.0  # simulated hours

    def _free_ip(self, mac: str):
        if mac in self.reservations:
            return self.reservations[mac]
        if mac in self.leases:  # "automatic" behavior: give the same address back if we can
            return self.leases[mac][0]
        in_use = {ip for ip, _ in self.leases.values()} | set(self.offers.values()) | set(self.reservations.values())
        for ip in self.pool:
            if ip not in in_use:
                return ip
        return None

    def expire(self) -> None:
        for mac, (ip, exp) in list(self.leases.items()):
            if exp <= self.clock:
                print(f"  [server] lease for {ip} ({mac}) expired - back in the pool")
                del self.leases[mac]

    def discover(self, mac: str):
        self.expire()
        ip = self._free_ip(mac)
        if ip is None:
            print("  [server] scope exhausted - no OFFER sent")
            return None
        self.offers[mac] = ip
        return ip

    def request(self, mac: str, ip) -> bool:
        if self.offers.get(mac) != ip and not (mac in self.leases and self.leases[mac][0] == ip):
            return False  # would send DHCPNAK
        self.offers.pop(mac, None)
        self.leases[mac] = (ip, self.clock + self.lease_hours)
        return True


class Client:
    def __init__(self, name: str, mac: str):
        self.name, self.mac, self.ip, self.lease_start = name, mac.upper(), None, None

    def boot(self, server: DHCPServer) -> None:
        print(f"\n{self.name} ({self.mac}) boots - has no IP, uses source 0.0.0.0")
        print("  DISCOVER  0.0.0.0:68 -> 255.255.255.255:67 (broadcast)  'Any DHCP servers?'")
        offer = server.discover(self.mac)
        if offer is None:
            # Windows/macOS self-assign a link-local address when DHCP fails
            self.ip = ipaddress.ip_address(f"169.254.{random.randint(1, 254)}.{random.randint(1, 254)}")
            print(f"  (no OFFER after retries) -> self-assigns APIPA {self.ip}  <- the classic ticket clue")
            return
        kind = "reserved address" if self.mac in server.reservations else "from the pool"
        print(f"  OFFER     server -> client               'You can have {offer}' ({kind})")
        print(f"  REQUEST   0.0.0.0:68 -> 255.255.255.255:67 (broadcast) 'I'll take {offer}'"
              " (broadcast so other DHCP servers know their offers were declined)")
        if server.request(self.mac, offer):
            self.ip, self.lease_start = offer, server.clock
            print(f"  ACK       server -> client               'Confirmed: {offer}'")
            for k, v in server.options.items():
                print(f"            {k:<20} {v}")

    def maybe_renew(self, server: DHCPServer) -> None:
        if self.ip is None or self.ip.is_link_local:
            return
        elapsed = server.clock - self.lease_start
        if elapsed >= server.lease_hours / 2:  # T1 = 50% of lease time
            print(f"\n{self.name}: 50% of lease elapsed -> unicast REQUEST to renew {self.ip}")
            if server.request(self.mac, self.ip):
                self.lease_start = server.clock
                print(f"  ACK - lease renewed for another {server.lease_hours} h, same address")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--small", action="store_true", help="2-address scope to show exhaustion")
    args = p.parse_args()

    end = "192.168.10.102" if args.small else "192.168.10.200"  # small: only .100 and .102 usable
    server = DHCPServer(
        network="192.168.10.0/24", start="192.168.10.100", end=end,
        gateway="192.168.10.1", dns=["192.168.10.10", "1.1.1.1"], lease_hours=8,
        exclusions=["192.168.10.101"],                       # a static device someone put inside the range
        reservations={"AA:BB:CC:00:00:50": "192.168.10.50"},  # printer: always the same IP
    )
    print(f"Scope 192.168.10.100-{end}, excluded .101, reservation .50 for the printer")
    print(f"Usable pool: {len(server.pool)} addresses")

    devices = [Client("laptop-amina", "3C:52:82:1A:9F:00"),
               Client("printer-2F", "AA:BB:CC:00:00:50"),
               Client("phone-guest", "DA:11:22:33:44:55"),
               Client("laptop-tunde", "8C:16:45:AA:10:2F")]
    for d in devices:
        d.boot(server)

    print("\n--- 4 hours pass ---")
    server.clock = 4
    for d in devices:
        d.maybe_renew(server)

    print("\n--- phone-guest leaves the building (never renews); 9 more hours pass ---")
    devices = [d for d in devices if d.name != "phone-guest"]
    server.clock = 13
    for d in devices:
        d.maybe_renew(server)
    server.expire()

    late = Client("laptop-new-hire", "00:15:5D:01:02:03")
    late.boot(server)

    print("\nCurrent leases:")
    for mac, (ip, exp) in sorted(server.leases.items(), key=lambda x: x[1][0]):
        print(f"  {str(ip):<16} {mac}  expires at hour {exp:g}")


if __name__ == "__main__":
    main()
