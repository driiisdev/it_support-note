"""
nat_table_sim.py - how a home/office router lets many private IPs share one public IP (PAT / masquerading),
and why inbound connections need port forwarding.

Usage:
    python nat_table_sim.py
"""

import itertools

PUBLIC_IP = "203.0.113.5"  # documentation range (RFC 5737) - stands in for your ISP-assigned address


class NATRouter:
    def __init__(self) -> None:
        self.table: dict[int, tuple[str, int]] = {}         # public port -> (private ip, private port)
        self.reverse: dict[tuple[str, int, str, int], int] = {}
        self.port_forwards: dict[int, tuple[str, int]] = {}
        self._ports = itertools.count(62000)

    def outbound(self, src_ip: str, src_port: int, dst_ip: str, dst_port: int) -> None:
        key = (src_ip, src_port, dst_ip, dst_port)
        if key not in self.reverse:
            public_port = next(self._ports)
            self.reverse[key] = public_port
            self.table[public_port] = (src_ip, src_port)
        pp = self.reverse[key]
        print(f"OUT  {src_ip}:{src_port:<5} -> {dst_ip}:{dst_port:<4}  rewritten to  "
              f"{PUBLIC_IP}:{pp} -> {dst_ip}:{dst_port}")

    def inbound(self, src_ip: str, src_port: int, dst_port: int) -> None:
        if dst_port in self.table:
            ip, port = self.table[dst_port]
            print(f"IN   {src_ip}:{src_port} -> {PUBLIC_IP}:{dst_port}  matches NAT table  ->  {ip}:{port}")
        elif dst_port in self.port_forwards:
            ip, port = self.port_forwards[dst_port]
            print(f"IN   {src_ip}:{src_port} -> {PUBLIC_IP}:{dst_port}  port-forward rule  ->  {ip}:{port}")
        else:
            print(f"IN   {src_ip}:{src_port} -> {PUBLIC_IP}:{dst_port}  no entry  ->  DROPPED "
                  "(unsolicited inbound traffic has nowhere to go)")

    def show(self) -> None:
        print(f"\nNAT table on the router (public IP {PUBLIC_IP}):")
        print(f"  {'PUBLIC PORT':<12} {'PRIVATE SOCKET':<22}")
        for pp, (ip, port) in self.table.items():
            print(f"  {pp:<12} {ip}:{port}")
        for pp, (ip, port) in self.port_forwards.items():
            print(f"  {pp:<12} {ip}:{port}   (static port forward)")


def main() -> None:
    r = NATRouter()
    print("Three devices on 192.168.1.0/24 browse the web - all leave as ONE public IP:\n")
    r.outbound("192.168.1.20", 50000, "93.184.215.14", 443)
    r.outbound("192.168.1.21", 50000, "93.184.215.14", 443)  # same private port, different host!
    r.outbound("192.168.1.30", 51123, "142.250.1.1", 443)
    r.show()

    print("\nReplies come back - the router uses the destination PORT to find the right private host:\n")
    r.inbound("93.184.215.14", 443, 62000)
    r.inbound("93.184.215.14", 443, 62001)
    r.inbound("142.250.1.1", 443, 62002)

    print("\nSomeone on the internet tries to reach an internal server directly:\n")
    r.inbound("198.51.100.7", 40000, 443)

    print("\nAdmin adds a port forward: public 443 -> internal web server 192.168.1.10:443\n")
    r.port_forwards[443] = ("192.168.1.10", 443)
    r.inbound("198.51.100.7", 40000, 443)
    r.show()
    print("\nThat port forward is also an attack surface: only forward what you must, and patch what's behind it.")


if __name__ == "__main__":
    main()
