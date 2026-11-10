# The Network Layer: IP, Subnetting & Routing

Ethernet (layer 2) only works inside one local network. The **network layer** (layer 3) is what
lets data cross *many* networks to reach any device on the internet. Its protocol is **IP**.

## IP addresses (IPv4)

- 32 bits, written as 4 **octets** in decimal: `192.168.10.25`.
- Each octet is 8 bits → 0-255.
- Unlike MAC addresses, IP addresses are **assigned by the network** (manually or by DHCP), and
  they're **hierarchical**: part of the address identifies the network, part identifies the host.

```
192.168.10.25 in binary:
11000000.10101000.00001010.00011001
```

## The IP datagram (packet) header

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-------+-------+---------------+-------------------------------+
|Version|  IHL  |  DSCP / ToS   |         Total Length          |
+-------+-------+---------------+-----+-------------------------+
|         Identification        |Flags|     Fragment Offset     |
+---------------+---------------+-----+-------------------------+
|  TTL          |   Protocol    |        Header Checksum        |
+---------------+---------------+-------------------------------+
|                       Source IP Address                       |
+---------------------------------------------------------------+
|                    Destination IP Address                     |
+---------------------------------------------------------------+
|                    Options (rare)  + Padding                  |
+---------------------------------------------------------------+
```

| Field | Purpose |
|---|---|
| Version | `4` for IPv4 |
| IHL | header length in 32-bit words (usually 5 = 20 bytes) |
| DSCP/ToS | priority / quality of service (e.g. voice traffic first) |
| Total length | header + data, max 65,535 bytes |
| Identification, flags, fragment offset | used when a packet is split (**fragmented**) to fit a smaller MTU |
| **TTL** (Time To Live) | decremented by 1 at every router; at 0 the packet is dropped. Prevents packets looping forever. `traceroute` abuses this on purpose. |
| Protocol | what's inside: `6` = TCP, `17` = UDP, `1` = ICMP |
| Header checksum | detects header corruption |
| Source / destination IP | where from, where to |

**Encapsulation reminder**: the entire IP datagram is the **payload** of the Ethernet frame. At
each router hop, the Ethernet frame is stripped and a *new* one is built for the next link - but
the IP packet inside (except TTL and checksum) stays the same end to end.

> 🖼️ **Image idea: packet crossing two routers** - show the same IP packet (same src/dst IP)
> wrapped in a different Ethernet frame (different src/dst MAC) on each hop.
> Suggested file: `assets/img/ip-hop-by-hop.png`
<!-- ![ip hop by hop](<../../assets/img/ip-hop-by-hop.png>) -->

## Address classes (historical)

Before CIDR, the first bits of an address decided how much was network vs host:

| Class | First octet | Default mask | Networks / hosts |
|---|---|---|---|
| A | 1-126 | 255.0.0.0 (/8) | few networks, ~16 million hosts each |
| B | 128-191 | 255.255.0.0 (/16) | ~65,534 hosts each |
| C | 192-223 | 255.255.255.0 (/24) | 254 hosts each |
| D | 224-239 | - | multicast |
| E | 240-255 | - | reserved/experimental |

(`127.x.x.x` is **loopback** - `127.0.0.1` always means "this computer".)
Classes are mostly obsolete, but the terms still come up.

## ARP: from IP address to MAC address

To send a frame on the local network, you need the destination's **MAC** - but you only know its
**IP**. **ARP (Address Resolution Protocol)** asks:

```
Host A (broadcast to FF:FF:FF:FF:FF:FF): "Who has 192.168.1.1? Tell 192.168.1.25"
Router (unicast reply):                  "192.168.1.1 is at 00:1A:2B:3C:4D:5E"
```

Answers are cached in the **ARP table** (`arp -a` on Windows/Linux). If the destination is on
another network, the host ARPs for its **default gateway's** MAC instead and sends the frame there.

## Subnetting

**Subnetting** splits one large network into smaller ones (for organization, security, and less
broadcast traffic).

### Subnet masks

A subnet mask marks which bits are the **network** part (1s) and which are the **host** part (0s):

```
IP:    192.168.10.25   = 11000000.10101000.00001010.00011001
Mask:  255.255.255.0   = 11111111.11111111.11111111.00000000
AND -> network ID:       11000000.10101000.00001010.00000000  = 192.168.10.0
```

A bitwise **AND** of IP and mask gives the network ID (the same AND gate from the
[intro note](<../technical support fundamentals/introduction.md>)). Two hosts are on the same
subnet if they produce the same network ID → they can talk directly; otherwise traffic goes
through the gateway.

### CIDR notation

**CIDR** (Classless Inter-Domain Routing) writes the mask as the number of 1-bits:
`192.168.10.0/24` = mask `255.255.255.0`. Masks no longer have to follow class boundaries.

### Working out a subnet

Number of addresses = 2^(host bits). Usable hosts = **2^(host bits) − 2** (first address =
**network ID**, last = **broadcast address**).

| CIDR | Mask | Host bits | Addresses | Usable hosts |
|---|---|---|---|---|
| /24 | 255.255.255.0 | 8 | 256 | 254 |
| /25 | 255.255.255.128 | 7 | 128 | 126 |
| /26 | 255.255.255.192 | 6 | 64 | 62 |
| /27 | 255.255.255.224 | 5 | 32 | 30 |
| /28 | 255.255.255.240 | 4 | 16 | 14 |
| /30 | 255.255.255.252 | 2 | 4 | 2 (point-to-point links) |

Example - `192.168.10.70/26`:

```
Block size = 256 - 192 = 64  -> subnets start at .0, .64, .128, .192
.70 falls in the .64 block
Network ID:  192.168.10.64
First host:  192.168.10.65
Last host:   192.168.10.126
Broadcast:   192.168.10.127
```

## Private (non-routable) address space - RFC 1918

These ranges are reserved for internal networks and are **not routed on the public internet**:

| Range | CIDR |
|---|---|
| 10.0.0.0 - 10.255.255.255 | 10.0.0.0/8 |
| 172.16.0.0 - 172.31.255.255 | 172.16.0.0/12 |
| 192.168.0.0 - 192.168.255.255 | 192.168.0.0/16 |

Also worth knowing: `169.254.x.x` = **APIPA / link-local** - a Windows PC gives itself this
address when it **couldn't reach a DHCP server**. Seeing it in `ipconfig` is a big clue.

## Routing

A **router** receives a packet, looks at the destination IP, checks its **routing table**, and
forwards the packet toward its destination. Repeat at every router = **hop**.

A routing table row contains:

| Destination network | Next hop | Total hops (metric) | Interface |
|---|---|---|---|
| 10.1.0.0/16 | 10.0.0.2 | 2 | eth1 |
| 0.0.0.0/0 (default) | 203.0.113.1 | - | eth0 |

The **most specific match** wins (/24 beats /16). `0.0.0.0/0` is the **default route** - "anything
I don't know about, send here." See yours with `route print` (Windows) or `ip route` (Linux).

### Routing protocols

Routers share what they know so tables are built automatically:

- **Interior gateway protocols** (inside one organization / **autonomous system**):
  - **Distance-vector** (e.g. **RIP**) - each router tells neighbors "here's everything I can
    reach and how far." Simple, slow to react to changes.
  - **Link-state** (e.g. **OSPF**) - each router shares the state of its own links with
    everyone, and everyone computes the best paths themselves. Faster, more CPU/memory.
- **Exterior gateway protocol** - **BGP**: how autonomous systems (ISPs, big companies), each
  with an **ASN** (Autonomous System Number), exchange routes. It is how the internet as a whole
  is routed.

> 🖼️ **Image idea: distance-vector vs link-state** - two small 4-router diagrams: one where
> routers pass distance lists to neighbors only, one where each floods its links to all.
> Suggested file: `assets/img/dv-vs-link-state.png`
<!-- ![distance vector vs link state](<../../assets/img/dv-vs-link-state.png>) -->

## How it's used in real IT support

- **"I can reach some things but not others"** → check IP, mask, and gateway in `ipconfig`. A
  wrong mask makes a host think local machines are remote (or vice versa).
- **`169.254.x.x` address** → DHCP failure.
- **Two machines with the same IP** → "IP address conflict" warning, intermittent connectivity.
- **Planning a network** for a new office floor → subnetting: how many hosts per subnet, room
  to grow, separate subnets for guests/printers/servers.

## Practice project

[`practice/computer-networking/subnet-planner`](<../../practice/computer-networking/subnet-planner>) -
a subnet calculator that does the bitwise AND by hand (and cross-checks with Python's `ipaddress`
module), plus a **VLSM planner** that carves an office's address block into right-sized subnets
for each department.

## Related

- [Introduction to networking](<introduction-to-networking.md>) - Ethernet frames that carry IP packets.
- [The transport and application layers](<the-transport-and-application-layers.md>) - what's inside the IP packet.
- [Troubleshooting & the future of networking](<troubleshooting-and-future-of-networking.md>) - ICMP, traceroute, IPv6.
