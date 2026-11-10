# Introduction to Networking: Layers, Cables & Ethernet

Networking is easiest to understand as a **stack of layers**, each one solving one problem and
relying on the layer below it. This note covers the model and the bottom two layers (physical
and data link); the next notes climb the stack.

## The TCP/IP five-layer model

This course uses a 5-layer model (a practical middle ground between the 4-layer TCP/IP model
and the 7-layer OSI model):

| # | Layer | Protocol examples | Addressing | Data unit | Hardware |
|---|---|---|---|---|---|
| 5 | Application | HTTP, DNS, SMTP, SSH | - | message | - |
| 4 | Transport | TCP, UDP | port numbers | segment (TCP) / datagram (UDP) | - |
| 3 | Network | IP, ICMP | IP addresses | packet (datagram) | router |
| 2 | Data link | Ethernet, Wi-Fi (802.11) | MAC addresses | frame | switch |
| 1 | Physical | copper, fiber, radio | - | bits | cables, hubs, NICs |

**OSI comparison**: OSI splits the top layer into Session (5), Presentation (6), Application (7).
"Layer 2 switch" and "Layer 7 load balancer" come from OSI numbering - but layers 1-4 mean the
same thing in both models.

### Encapsulation: each layer wraps the one above

```
Application:                          [ HTTP request data ]
Transport:                    [ TCP hdr | HTTP request data ]
Network:            [ IP hdr | TCP hdr | HTTP request data ]
Data link: [ Eth hdr | IP hdr | TCP hdr | HTTP request data | FCS ]
Physical:  0101011100101010101010101... (electrical/light/radio signals)
```

Sending = wrapping downward. Receiving = unwrapping upward. Each device only looks at the layers
it cares about: a switch reads the Ethernet header; a router reads the IP header; only the end
hosts look at TCP and HTTP.

> 🖼️ **Image idea: encapsulation diagram** - nested boxes like the ASCII above, color-coded per
> layer, with sender on the left (wrapping) and receiver on the right (unwrapping).
> Suggested file: `assets/img/encapsulation.png`
<!-- ![encapsulation](<../../assets/img/encapsulation.png>) -->

## Physical layer

How bits actually travel as signals.

### Cables

- **Copper twisted pair** - pairs of wires twisted together to reduce **crosstalk** (one wire's
  signal interfering with another).
  - **Cat5** (100 Mbps, obsolete), **Cat5e** (1 Gbps, less crosstalk), **Cat6** (1 Gbps; 10 Gbps
    up to ~55 m), **Cat6a** (10 Gbps up to 100 m).
  - Max run length ~**100 m**.
- **Fiber** - light pulses through glass/plastic. Single-mode (long distance, km) vs multi-mode
  (shorter, cheaper). Immune to electromagnetic interference.
- **Modulation** - varying a signal (voltage, light, radio) to encode 0s and 1s; **line coding**
  is the scheme that maps bits onto that signal.

### Duplex

- **Simplex** - one direction only.
- **Half-duplex** - both directions, but one at a time (walkie-talkie).
- **Full-duplex** - both directions at once (modern switched Ethernet).

A **duplex mismatch** (one side full, one side half) causes slow, error-prone links - a classic
"it works but it's terribly slow" issue.

### Ports and patch panels

- **RJ45** - the standard Ethernet connector. Link LED = physical connection; activity LED
  blinks with traffic. *No link light → layer 1 problem.*
- **Patch panel** - a panel of ports in a network closet; each port is wired to a wall jack
  somewhere in the building. Short patch cables connect the panel to the switch.

## Hubs, switches, and routers

- **Hub** (layer 1) - repeats every signal to every port. All devices share one **collision
  domain**: if two send at once, the signals collide and both must retry.
- **Switch** (layer 2) - reads the destination **MAC address** and forwards only to the right
  port. Each port is its own collision domain → collisions basically disappear.
- **Router** (layer 3) - forwards between **networks** based on **IP addresses**.

## Data link layer: Ethernet

**Ethernet** is the protocol that gets frames from one device to another on the *same* local
network.

### CSMA/CD

*Carrier Sense Multiple Access with Collision Detection* - the original rule for sharing a wire:
listen before talking; if a collision happens, wait a random time and retry. On modern
full-duplex switched networks collisions don't happen, but this is why the old hub model was slow.

### MAC addresses

- 48 bits, written as 6 hex pairs: `00:1A:2B:3C:4D:5E`.
- First 3 bytes = **OUI** (Organizationally Unique Identifier) - identifies the manufacturer.
- Last 3 bytes = assigned by the manufacturer, unique per NIC.
- Find yours: `ipconfig /all` (Windows, "Physical Address") or `ip link` (Linux).

### Unicast, multicast, broadcast

| Type | Who receives it | How it's recognized |
|---|---|---|
| Unicast | one device | least significant bit of the first byte is **0** |
| Multicast | a group of devices that opted in | that bit is **1** |
| Broadcast | every device on the LAN | destination `FF:FF:FF:FF:FF:FF` |

### The Ethernet frame

```
+----------+-----+----------+----------+-----------+-------------------+-----+
| Preamble | SFD | Dest MAC | Src MAC  | EtherType | Payload           | FCS |
| 7 bytes  | 1   | 6 bytes  | 6 bytes  | 2 bytes   | 46 - 1500 bytes   | 4   |
+----------+-----+----------+----------+-----------+-------------------+-----+
```

- **Preamble + SFD (Start Frame Delimiter)** - sync pattern so the receiver knows a frame is
  starting. (Not usually shown in packet captures.)
- **Destination / source MAC** - who it's for, who sent it.
- **EtherType** - what protocol is inside: `0x0800` = IPv4, `0x86DD` = IPv6, `0x0806` = ARP.
- **VLAN tag** (optional, 4 bytes, 802.1Q) - goes before EtherType when VLANs are used.
- **Payload** - the data (usually an IP packet). 1500 bytes max = the standard **MTU**.
- **FCS (Frame Check Sequence)** - a **CRC** checksum. If it doesn't match, the frame is
  dropped. Ethernet *detects* errors but doesn't *fix* them - higher layers (TCP) retransmit.

> 🖼️ **Image idea: Ethernet frame layout** - the frame above as a colored bar with byte sizes.
> Suggested file: `assets/img/ethernet-frame.png`
<!-- ![ethernet frame](<../../assets/img/ethernet-frame.png>) -->

### VLANs

A **Virtual LAN** splits one physical switch into several logical networks (e.g. staff, guests,
VoIP phones) that can't talk to each other without going through a router. Good for security and
for keeping broadcast traffic contained.

## How it's used in real IT support

- **No link light** → cable, port, or NIC (layer 1). Try another cable/port.
- **Link light, but no IP** → layer 2/3: wrong VLAN, DHCP problem.
- **"Who is this device on our network?"** → look up the MAC's OUI to find the manufacturer.
- **Packet captures** (Wireshark) show you exactly these headers - learning the frame layout
  makes captures readable.

## Practice project

[`practice/computer-networking/packet-dissector`](<../../practice/computer-networking/packet-dissector>) -
parses a raw Ethernet frame (hex bytes) by hand: MAC addresses, unicast/multicast/broadcast,
OUI lookup, EtherType, then the IPv4 and TCP/UDP headers inside it - layer by layer, exactly
like Wireshark does.

## Related

- [The network layer](<the-network-layer.md>) - what's inside the Ethernet payload.
- [The transport and application layers](<the-transport-and-application-layers.md>) - the top of the stack.
- [Networking basics](<../technical support fundamentals/networking.md>) - the beginner overview.
