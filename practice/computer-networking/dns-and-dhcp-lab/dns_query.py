"""
dns_query.py - a DNS client from scratch: build the query bytes, send them over UDP 53, parse the answer.

No dnspython, no nslookup - just struct and socket, so you can see exactly what a resolver does.

Usage:
    python dns_query.py example.com                 # A record via 8.8.8.8
    python dns_query.py example.com AAAA
    python dns_query.py gmail.com MX
    python dns_query.py google.com TXT --server 1.1.1.1
    python dns_query.py www.github.com CNAME
    python dns_query.py doesnotexist.example NS     # see an NXDOMAIN response
"""

import argparse
import ipaddress
import random
import socket
import struct
import time

TYPES = {"A": 1, "NS": 2, "CNAME": 5, "SOA": 6, "PTR": 12, "MX": 15, "TXT": 16, "AAAA": 28}
TYPE_NAMES = {v: k for k, v in TYPES.items()}
RCODES = {0: "NOERROR", 1: "FORMERR", 2: "SERVFAIL", 3: "NXDOMAIN (name does not exist)", 5: "REFUSED"}


def build_query(name: str, qtype: int) -> tuple[int, bytes]:
    tid = random.randint(0, 0xFFFF)
    flags = 0x0100  # standard query, Recursion Desired = 1 ("please do the full lookup for me")
    header = struct.pack("!HHHHHH", tid, flags, 1, 0, 0, 0)  # 1 question, 0 answers/authority/additional
    # Names are encoded as length-prefixed labels: www.example.com -> 3www7example3com0
    qname = b"".join(bytes([len(label)]) + label.encode() for label in name.rstrip(".").split(".")) + b"\x00"
    return tid, header + qname + struct.pack("!HH", qtype, 1)  # class 1 = IN (internet)


def read_name(msg: bytes, offset: int) -> tuple[str, int]:
    """Decode a (possibly compressed) name. Returns (name, offset just after the name in the record).

    Compression: if the top two bits of a length byte are 11 (0xC0), the next 14 bits are a pointer
    to where the rest of the name already appears in the message - saves repeating 'example.com'.
    """
    labels, jumped, end = [], False, offset
    while True:
        length = msg[offset]
        if length & 0xC0 == 0xC0:
            pointer = struct.unpack("!H", msg[offset:offset + 2])[0] & 0x3FFF
            if not jumped:
                end = offset + 2
            offset, jumped = pointer, True
            continue
        if length == 0:
            if not jumped:
                end = offset + 1
            return ".".join(labels) or ".", end
        labels.append(msg[offset + 1:offset + 1 + length].decode(errors="replace"))
        offset += length + 1


def parse_rdata(msg: bytes, rtype: int, start: int, length: int) -> str:
    data = msg[start:start + length]
    if rtype == 1:
        return str(ipaddress.IPv4Address(data))
    if rtype == 28:
        return str(ipaddress.IPv6Address(data))
    if rtype in (2, 5, 12):
        return read_name(msg, start)[0]
    if rtype == 15:
        pref = struct.unpack("!H", data[:2])[0]
        return f"priority {pref:<3} {read_name(msg, start + 2)[0]}"
    if rtype == 16:  # TXT: one or more length-prefixed strings
        parts, i = [], 0
        while i < len(data):
            n = data[i]
            parts.append(data[i + 1:i + 1 + n].decode(errors="replace"))
            i += n + 1
        return '"' + "".join(parts) + '"'
    if rtype == 6:
        mname, off = read_name(msg, start)
        rname, off = read_name(msg, off)
        serial = struct.unpack("!I", msg[off:off + 4])[0]
        return f"primary {mname}, admin {rname}, serial {serial}"
    return data.hex()


def parse_response(msg: bytes) -> dict:
    tid, flags, qd, an, ns, ar = struct.unpack("!HHHHHH", msg[:12])
    offset = 12
    for _ in range(qd):  # skip the echoed question
        _, offset = read_name(msg, offset)
        offset += 4

    sections = {"answer": [], "authority": []}
    for section, count in (("answer", an), ("authority", ns)):
        for _ in range(count):
            name, offset = read_name(msg, offset)
            rtype, rclass, ttl, rdlen = struct.unpack("!HHIH", msg[offset:offset + 10])
            offset += 10
            sections[section].append((name, TYPE_NAMES.get(rtype, str(rtype)), ttl,
                                      parse_rdata(msg, rtype, offset, rdlen)))
            offset += rdlen
    return {
        "id": tid,
        "authoritative": bool(flags & 0x0400),
        "truncated": bool(flags & 0x0200),
        "recursion_available": bool(flags & 0x0080),
        "rcode": flags & 0x000F,
        **sections,
    }


def recv_exact(sock: socket.socket, n: int) -> bytes:
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise SystemExit("TCP connection closed mid-response")
        buf += chunk
    return buf


def main() -> None:
    p = argparse.ArgumentParser(description="DNS lookup built from raw bytes.")
    p.add_argument("name")
    p.add_argument("type", nargs="?", default="A", choices=TYPES.keys())
    p.add_argument("--server", default="8.8.8.8", help="resolver to ask (default Google 8.8.8.8)")
    args = p.parse_args()

    tid, query = build_query(args.name, TYPES[args.type])
    print(f"Query  : {args.name} {args.type} -> {args.server}:53 over UDP")
    print(f"Bytes  : {len(query)} - {query.hex(' ')}")

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(3)
        start = time.perf_counter()
        s.sendto(query, (args.server, 53))
        try:
            resp, _ = s.recvfrom(4096)
        except socket.timeout:
            raise SystemExit("No answer in 3 s - resolver unreachable or UDP 53 blocked by a firewall.")
        ms = (time.perf_counter() - start) * 1000

    r = parse_response(resp)
    if r["id"] != tid:
        raise SystemExit("Transaction ID mismatch - ignoring (this check is a defense against spoofed replies).")
    transport = "UDP"

    if r["truncated"]:
        # The answer didn't fit in a UDP reply (TC flag set). Real resolvers retry the same query
        # over TCP 53, where every message is prefixed with its 2-byte length (TCP is a byte stream).
        print(f"Reply  : {len(resp)} bytes over UDP with TC=1 (truncated) -> retrying over TCP 53")
        start = time.perf_counter()
        try:
            with socket.create_connection((args.server, 53), timeout=3) as t:
                t.sendall(struct.pack("!H", len(query)) + query)
                length = struct.unpack("!H", recv_exact(t, 2))[0]
                resp = recv_exact(t, length)
        except OSError as e:
            raise SystemExit(f"TCP 53 to {args.server} failed ({e}).\n"
                             "A firewall that allows DNS over UDP but blocks TCP 53 breaks large answers "
                             "(long TXT/DNSSEC records) - a real-world misconfiguration worth recognizing.")
        ms = (time.perf_counter() - start) * 1000
        r = parse_response(resp)
        transport = "TCP"

    print(f"Reply  : {len(resp)} bytes over {transport} in {ms:.0f} ms, status {RCODES.get(r['rcode'], r['rcode'])}")
    print(f"Flags  : authoritative={r['authoritative']} recursion_available={r['recursion_available']}"
          f" truncated={r['truncated']}")
    if r["answer"]:
        print("\nANSWER SECTION  (TTL = seconds this answer may be cached)")
        for name, rtype, ttl, value in r["answer"]:
            print(f"  {name:<28} {ttl:>6}  {rtype:<6} {value}")
    if r["authority"]:
        print("\nAUTHORITY SECTION")
        for name, rtype, ttl, value in r["authority"]:
            print(f"  {name:<28} {ttl:>6}  {rtype:<6} {value}")
    if not r["answer"] and r["rcode"] == 0:
        print("\nNo records of that type (NOERROR/NODATA) - the name exists, but not with this record type.")
    print("\nRun the same query twice: a lower TTL the 2nd time means you got the resolver's cached copy.")


if __name__ == "__main__":
    main()
