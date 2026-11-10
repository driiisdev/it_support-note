"""
dissect.py - decode a raw Ethernet frame layer by layer, the way Wireshark does.

Usage:
    python dissect.py                 # list built-in sample frames
    python dissect.py tcp_syn         # dissect a sample (tcp_syn, dns_query, arp_request, tcp_rst)
    python dissect.py --hex 001a2b... # dissect your own frame
                                      # (Wireshark: right-click packet -> Copy -> ...as a Hex Stream)

Standard library only. Every field is pulled out with struct.unpack so you can see exactly
which bytes mean what.
"""

import argparse
import struct
import sys

# Real frames, built with correct IPv4/TCP/UDP checksums (addresses are documentation/private ranges).
SAMPLES = {
    "tcp_syn": (
        "PC opens an HTTPS connection: the first packet of the TCP three-way handshake",
        "001a2b3c4d5e3c52821a9f000800450000341c464000400627f6c0a801195db8d70ec93b01bb"
        "9a3b1c00000000008002faf0fc640000020405b40101040201030308",
    ),
    "dns_query": (
        "PC asks 8.8.8.8 for the IPv4 address (A record) of example.com",
        "001a2b3c4d5e3c52821a9f000800450000392a10400040113ed3c0a8011908080808cf090035"
        "0025d036beef01000001000000000000076578616d706c6503636f6d0000010001",
    ),
    "arp_request": (
        "PC broadcasts 'who has 192.168.1.1?' to find the gateway's MAC address",
        "ffffffffffff3c52821a9f00080600010800060400013c52821a9f00c0a80119000000000000c0a80101",
    ),
    "tcp_rst": (
        "Server answers a connection to port 3389 (RDP) with RST: port closed",
        "8c1645aa102f005056010203080045000028000040008006e6ad0a0000140a00000f0d3dc3ca"
        "000000001122334550140000863f0000",
    ),
}

# A tiny OUI table. The full registry is public: https://regauth.standards.ieee.org/
OUI = {
    "00:50:56": "VMware (virtual NIC)",
    "00:0C:29": "VMware (virtual NIC)",
    "08:00:27": "Oracle VirtualBox (virtual NIC)",
    "00:15:5D": "Microsoft Hyper-V (virtual NIC)",
    "B8:27:EB": "Raspberry Pi Foundation",
    "DC:A6:32": "Raspberry Pi Trading",
}

ETHERTYPES = {0x0800: "IPv4", 0x0806: "ARP", 0x86DD: "IPv6", 0x8100: "802.1Q VLAN tag"}
IP_PROTOCOLS = {1: "ICMP", 6: "TCP", 17: "UDP"}
WELL_KNOWN_PORTS = {
    22: "SSH", 25: "SMTP", 53: "DNS", 67: "DHCP server", 68: "DHCP client", 80: "HTTP",
    123: "NTP", 143: "IMAP", 389: "LDAP", 443: "HTTPS", 445: "SMB", 587: "SMTP submission",
    993: "IMAPS", 3389: "RDP",
}


def fmt_mac(b: bytes) -> str:
    return ":".join(f"{x:02X}" for x in b)


def fmt_ip(b: bytes) -> str:
    return ".".join(str(x) for x in b)


def checksum(data: bytes) -> int:
    """The 16-bit one's complement sum used by IPv4, TCP, UDP, and ICMP."""
    if len(data) % 2:
        data += b"\x00"
    total = sum(struct.unpack(f"!{len(data) // 2}H", data))
    while total >> 16:
        total = (total & 0xFFFF) + (total >> 16)
    return ~total & 0xFFFF


def port_name(p: int) -> str:
    if p in WELL_KNOWN_PORTS:
        return f"{p} ({WELL_KNOWN_PORTS[p]})"
    if p >= 49152:
        return f"{p} (ephemeral)"
    return str(p)


def mac_kind(b: bytes) -> str:
    if b == b"\xff" * 6:
        return "broadcast - every device on the LAN receives it"
    kind = "multicast" if b[0] & 0x01 else "unicast"
    # 2nd-least-significant bit of the first byte: locally administered (e.g. randomized phone MACs)
    admin = "locally administered (randomized/virtual)" if b[0] & 0x02 else "globally unique (burned-in)"
    vendor = OUI.get(fmt_mac(b[:3]), "not in local table - look the OUI up in the IEEE registry")
    return f"{kind}, {admin}; OUI {fmt_mac(b[:3])} = {vendor}"


def section(title: str) -> None:
    print(f"\n=== {title} " + "=" * (60 - len(title)))


def dissect_ethernet(frame: bytes) -> None:
    section("Layer 2 - Ethernet II")
    dst, src, ethertype = struct.unpack("!6s6sH", frame[:14])
    print(f"Destination MAC : {fmt_mac(dst)}   [{mac_kind(dst)}]")
    print(f"Source MAC      : {fmt_mac(src)}   [{mac_kind(src)}]")
    print(f"EtherType       : 0x{ethertype:04X} ({ETHERTYPES.get(ethertype, 'unknown')})")
    print(f"(Preamble/SFD and the 4-byte FCS are stripped by the NIC before capture software sees the frame.)")
    payload = frame[14:]
    if ethertype == 0x0800:
        dissect_ipv4(payload)
    elif ethertype == 0x0806:
        dissect_arp(payload)
    else:
        print("(dissector only handles IPv4 and ARP)")


def dissect_arp(p: bytes) -> None:
    section("ARP (sits between layer 2 and 3)")
    htype, ptype, hlen, plen, op = struct.unpack("!HHBBH", p[:8])
    sha, spa, tha, tpa = struct.unpack("!6s4s6s4s", p[8:28])
    print(f"Operation       : {op} ({'request' if op == 1 else 'reply' if op == 2 else '?'})")
    print(f"Sender MAC / IP : {fmt_mac(sha)} / {fmt_ip(spa)}")
    print(f"Target MAC / IP : {fmt_mac(tha)} / {fmt_ip(tpa)}")
    if op == 1:
        print(f"\nIn English: \"Who has {fmt_ip(tpa)}? Tell {fmt_ip(spa)}.\"")
        print("Target MAC is all zeros because that's exactly what the sender doesn't know yet.")


def dissect_ipv4(p: bytes) -> None:
    section("Layer 3 - IPv4")
    (ver_ihl, tos, total_len, ident, flags_frag, ttl, proto, hdr_csum,
     src, dst) = struct.unpack("!BBHHHBBH4s4s", p[:20])
    version, ihl = ver_ihl >> 4, ver_ihl & 0x0F
    header_len = ihl * 4
    df = bool(flags_frag & 0x4000)
    mf = bool(flags_frag & 0x2000)
    offset = (flags_frag & 0x1FFF) * 8

    # Verify the checksum: recompute over the header with the checksum field zeroed.
    header = bytearray(p[:header_len])
    header[10:12] = b"\x00\x00"
    calc = checksum(bytes(header))

    print(f"Version         : {version}")
    print(f"Header length   : {ihl} x 4 = {header_len} bytes")
    print(f"DSCP/ToS        : 0x{tos:02X}")
    print(f"Total length    : {total_len} bytes (header + data)")
    print(f"Identification  : 0x{ident:04X}")
    print(f"Flags           : DF={int(df)} (don't fragment)  MF={int(mf)} (more fragments)   offset={offset}")
    print(f"TTL             : {ttl}   (typical start: 64 = Linux/macOS, 128 = Windows, 255 = network gear)")
    print(f"Protocol        : {proto} ({IP_PROTOCOLS.get(proto, 'other')})")
    print(f"Header checksum : 0x{hdr_csum:04X}  -> recomputed 0x{calc:04X} "
          f"{'OK' if calc == hdr_csum else 'MISMATCH (corrupt or offloaded)'}")
    print(f"Source IP       : {fmt_ip(src)}")
    print(f"Destination IP  : {fmt_ip(dst)}")

    data = p[header_len:total_len]
    if proto == 6:
        dissect_tcp(data, src, dst)
    elif proto == 17:
        dissect_udp(data, src, dst)


def transport_checksum_ok(segment: bytes, src: bytes, dst: bytes, proto: int, csum_offset: int) -> bool:
    """TCP/UDP checksums also cover a 'pseudo-header' of IP addresses - a layer 3/4 overlap."""
    seg = bytearray(segment)
    stored = struct.unpack("!H", seg[csum_offset:csum_offset + 2])[0]
    seg[csum_offset:csum_offset + 2] = b"\x00\x00"
    pseudo = src + dst + struct.pack("!BBH", 0, proto, len(seg))
    return checksum(pseudo + bytes(seg)) == stored


def dissect_tcp(seg: bytes, src: bytes, dst: bytes) -> None:
    section("Layer 4 - TCP")
    sport, dport, seq, ack, off_byte, flags, window, csum, urg = struct.unpack("!HHIIBBHHH", seg[:20])
    data_offset = (off_byte >> 4) * 4
    names = ["FIN", "SYN", "RST", "PSH", "ACK", "URG", "ECE", "CWR"]
    set_flags = [n for i, n in enumerate(names) if flags & (1 << i)]

    print(f"Source port     : {port_name(sport)}")
    print(f"Destination port: {port_name(dport)}")
    print(f"Sequence number : {seq}")
    print(f"Ack number      : {ack}" + ("" if "ACK" in set_flags else "  (ignored - ACK flag not set)"))
    print(f"Header length   : {data_offset} bytes")
    print(f"Flags           : {' '.join(set_flags)}")
    print(f"Window          : {window} bytes  (how much the sender can receive right now)")
    print(f"Checksum        : 0x{csum:04X} "
          f"{'OK' if transport_checksum_ok(seg, src, dst, 6, 16) else 'MISMATCH'}")

    # Parse a few common TCP options (only present on SYN packets usually)
    opts, i = seg[20:data_offset], 0
    while i < len(opts):
        kind = opts[i]
        if kind == 0:
            break
        if kind == 1:
            i += 1
            continue
        length = opts[i + 1]
        if kind == 2:
            print(f"Option          : MSS = {struct.unpack('!H', opts[i + 2:i + 4])[0]} bytes (max segment size)")
        elif kind == 3:
            print(f"Option          : window scale = x{2 ** opts[i + 2]}")
        elif kind == 4:
            print("Option          : SACK permitted (selective acknowledgments)")
        i += length

    meaning = {
        ("SYN",): "first step of the three-way handshake: 'I'd like to connect'",
        ("SYN", "ACK"): "second step of the handshake: 'OK, and I'd like to connect too'",
        ("RST",): "connection refused/aborted",
        ("RST", "ACK"): "connection refused - nothing is listening on that port (or a firewall rejected it)",
        ("FIN", "ACK"): "graceful close: 'I'm done sending'",
    }.get(tuple(f for f in set_flags if f in ("SYN", "ACK", "RST", "FIN")))
    if meaning:
        print(f"\nIn English: {meaning}.")


def dissect_udp(seg: bytes, src: bytes, dst: bytes) -> None:
    section("Layer 4 - UDP")
    sport, dport, length, csum = struct.unpack("!HHHH", seg[:8])
    print(f"Source port     : {port_name(sport)}")
    print(f"Destination port: {port_name(dport)}")
    print(f"Length          : {length} bytes (8 header + {length - 8} data)")
    print(f"Checksum        : 0x{csum:04X} "
          f"{'OK' if transport_checksum_ok(seg[:length], src, dst, 17, 6) else 'MISMATCH'}")
    print("(No sequence numbers, no handshake, no ACKs - that's the whole UDP header.)")
    if 53 in (sport, dport):
        dissect_dns(seg[8:length])


def dissect_dns(msg: bytes) -> None:
    section("Layer 5 - DNS (application)")
    tid, flags, qd, an, ns, ar = struct.unpack("!HHHHHH", msg[:12])
    is_response = bool(flags & 0x8000)
    print(f"Transaction ID  : 0x{tid:04X} (the reply will carry the same ID)")
    print(f"Type            : {'response' if is_response else 'query'}; recursion desired = {bool(flags & 0x0100)}")
    print(f"Questions       : {qd}, answers: {an}")
    i, labels = 12, []
    while msg[i] != 0:
        n = msg[i]
        labels.append(msg[i + 1:i + 1 + n].decode())
        i += n + 1
    qtype, qclass = struct.unpack("!HH", msg[i + 1:i + 5])
    types = {1: "A", 28: "AAAA", 15: "MX", 16: "TXT", 5: "CNAME", 2: "NS", 12: "PTR"}
    print(f"Question        : {'.'.join(labels)}  type {types.get(qtype, qtype)}  class {'IN' if qclass == 1 else qclass}")
    print("Name encoding   : each label is length-prefixed: "
          + " ".join(f"[{len(lab)}]{lab}" for lab in labels) + " [0]")


def main() -> None:
    p = argparse.ArgumentParser(description="Decode an Ethernet frame layer by layer.")
    p.add_argument("sample", nargs="?", choices=SAMPLES.keys())
    p.add_argument("--hex", help="raw frame as hex (spaces/colons allowed)")
    args = p.parse_args()

    if args.hex:
        raw = args.hex
        title = "your frame"
    elif args.sample:
        title, raw = SAMPLES[args.sample]
    else:
        print("Built-in samples:")
        for name, (desc, _) in SAMPLES.items():
            print(f"  {name:<12} {desc}")
        print("\nRun: python dissect.py tcp_syn")
        return

    try:
        frame = bytes.fromhex(raw.replace(" ", "").replace(":", ""))
    except ValueError:
        sys.exit("Not valid hex.")
    print(f"Frame: {title}\n{len(frame)} bytes: {frame.hex(' ')}")
    dissect_ethernet(frame)


if __name__ == "__main__":
    main()
