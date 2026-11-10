# Practice: Packet Dissector (Introduction to Networking, Network layer)

Concept notes:
[`introduction-to-networking.md`](<../../../concepts/computer networking/introduction-to-networking.md>) ·
[`the-network-layer.md`](<../../../concepts/computer networking/the-network-layer.md>) ·
[`the-transport-and-application-layers.md`](<../../../concepts/computer networking/the-transport-and-application-layers.md>)

## What this demonstrates

**Encapsulation, for real.** A frame on the wire is just bytes. This tool takes a raw Ethernet
frame and peels it apart one layer at a time - Ethernet → IPv4 (or ARP) → TCP/UDP → DNS - pulling
out every header field by its byte offset and **verifying the checksums**. Once you've done this,
Wireshark's packet details pane stops looking like magic.

## Scenario

A senior colleague sends you a few packets copied from a capture and asks: "What is this host
doing, and why can't it connect to the RDP server?" You decode them by hand.

## Folder structure

```
packet-dissector/
  dissect.py   <- 4 built-in sample frames + a decoder for Ethernet, ARP, IPv4, TCP, UDP, DNS
  README.md
```

The samples:

| Name | What it is |
|---|---|
| `tcp_syn` | PC → web server on 443: first packet of the TCP handshake (with MSS/SACK/window-scale options) |
| `dns_query` | PC → 8.8.8.8: "what is the A record of example.com?" over UDP 53 |
| `arp_request` | broadcast "who has 192.168.1.1?" - how a PC finds its gateway's MAC |
| `tcp_rst` | server replies RST/ACK to a connection on 3389 - port closed |

## Code walkthrough

**Every header is a fixed layout**, so `struct.unpack` with the right format string *is* the
protocol spec:

```python
# Ethernet: 6-byte dst MAC, 6-byte src MAC, 2-byte EtherType ("!" = network byte order, big-endian)
dst, src, ethertype = struct.unpack("!6s6sH", frame[:14])

# IPv4: version+IHL, ToS, total length, ID, flags+fragment offset, TTL, protocol, checksum, src, dst
(ver_ihl, tos, total_len, ident, flags_frag, ttl, proto, hdr_csum,
 src, dst) = struct.unpack("!BBHHHBBH4s4s", p[:20])
```

**The EtherType and Protocol fields are "what's inside" pointers** - that's how each layer knows
which dissector to hand the payload to (`0x0800` → IPv4, `0x0806` → ARP; protocol `6` → TCP,
`17` → UDP).

**Checksums are verified, not just printed.** The IPv4 checksum is recomputed over the header with
the checksum field zeroed; TCP/UDP checksums also include a **pseudo-header** of the source and
destination IPs - a neat example of layers 3 and 4 overlapping:

```python
pseudo = src + dst + struct.pack("!BBH", 0, proto, len(seg))
checksum(pseudo + segment) == stored
```

**MAC addresses are classified** using the low bits of the first byte: bit 0 = multicast,
bit 1 = locally administered (which is what randomized "private Wi-Fi addresses" on phones look like).

## Run it

```bash
python dissect.py              # list samples
python dissect.py tcp_syn
python dissect.py dns_query
python dissect.py arp_request
python dissect.py tcp_rst
python dissect.py --hex "<hex stream copied from Wireshark>"
```

Expected (excerpt of `tcp_rst`):

```
=== Layer 4 - TCP ===============================================
Source port     : 3389 (RDP)
Destination port: 50122 (ephemeral)
Flags           : RST ACK
In English: connection refused - nothing is listening on that port (or a firewall rejected it).
```

## Try this yourself

- **Capture your own packets**: install [Wireshark](https://www.wireshark.org/), capture while
  running `nslookup example.com`, filter `dns`, right-click a packet → **Copy → ...as a Hex Stream**,
  and run `python dissect.py --hex <paste>`. Compare against Wireshark's own decoding.
- Flip one byte of a sample's IP address with `--hex` and watch the checksum say **MISMATCH**.
  (Captures from your own machine may show TCP checksum mismatches too - that's
  **checksum offload**: the NIC fills it in after capture.)
- In the `tcp_rst` sample the TTL is 128 and the source MAC is VMware's OUI - what can you guess
  about the server? (Windows VM.)
- Add a dissector for **ICMP** (protocol 1): type 8 = echo request, 0 = echo reply, 11 = time exceeded.
- Add a DNS **response** sample and parse the answer section (watch for name compression pointers,
  bytes starting with `0xC0`).

## Real-world equivalent

- **Wireshark / tcpdump** do exactly this, for thousands of protocols.
- Reading captures is how you prove *where* a problem is: "the SYN leaves the PC, the server
  answers RST → the port is closed on the server, it's not the network" ends a lot of
  network-vs-server finger pointing.
