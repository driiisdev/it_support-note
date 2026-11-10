# Connecting to the Internet: Dial-up, Broadband, WANs & Wireless

A LAN is only half the story - at some point traffic has to leave the building. This note covers
the **technologies that connect a home or office to an ISP**, how organizations connect sites
together (WANs), and how wireless networking works.

## Dial-up and modems (the origin)

- **POTS** (Plain Old Telephone Service) / **PSTN** - the phone network.
- **Dial-up** - a **modem** (*mo*dulator-*dem*odulator) converts digital data into audio tones
  over a phone line and back. Max ~56 kbps; the line is busy while you're online.
- **Baud rate** - number of signal changes (symbols) per second. Not always equal to bits per
  second, since one symbol can carry several bits.

Still worth knowing: the word "modem" stuck around for all the boxes that convert an ISP's signal
into Ethernet.

## Broadband

**Broadband** = always-on internet, much faster than dial-up.

| Technology | Medium | Notes |
|---|---|---|
| **T-carrier (T1/T3)** | copper | T1 = 1.544 Mbps, 24 channels. Older business lines. |
| **DSL** | phone line (different frequencies than voice, so both work at once) | **ADSL** (asymmetric: faster download than upload), **SDSL** (symmetric). Speed drops with distance from the provider's **DSLAM**. |
| **Cable** | coaxial TV cable | **DOCSIS** standard. Bandwidth is **shared** with neighbors on the same segment → slower at peak hours. Uses a **cable modem**; provider side is the **CMTS**. |
| **Fiber** | glass fiber, light | Fastest, most reliable. Variants by how close fiber gets: **FTTN** (node/neighborhood), **FTTB** (building), **FTTH/FTTP** (home/premises). Ends at an **ONT** (Optical Network Terminal) that converts to Ethernet. |
| **Cellular (4G/5G)** | radio | Mobile and fixed-wireless home internet; also used as office **failover**. |
| **Satellite** | radio via satellites | Remote areas. Traditional geostationary = high latency (~600 ms); low-orbit constellations are much lower. |

> 🖼️ **Image idea: FTTN vs FTTB vs FTTH** - a street diagram showing where fiber ends and copper
> begins for each variant.
> Suggested file: `assets/img/fiber-variants.png`
<!-- ![fiber variants](<../../assets/img/fiber-variants.png>) -->

## WAN technologies

A **WAN** connects networks over long distances, usually using lines leased from an ISP.

- **Demarcation point** ("demarc") - where the ISP's responsibility ends and yours begins. When
  a WAN link is down, the first question is: *which side of the demarc is broken?*
- **Point-to-point / leased line** - a dedicated link between two sites.
- **Frame Relay** (legacy), **MPLS** (provider-managed private WAN; routes by labels instead of
  IP lookups).
- **Site-to-site VPN** over the regular internet - cheaper than a leased line.
- **SD-WAN** - software-managed WAN that combines several links (fiber + 5G + broadband) and
  steers traffic over the best one.

```
 Branch office LAN -- router --(MPLS / VPN / SD-WAN)-- router -- HQ LAN -- data center
```

## Wireless networking (Wi-Fi)

Wi-Fi is defined by the **IEEE 802.11** family of standards - the data link layer for wireless.

### Standards

| Standard | Marketing name | Band(s) | Typical max |
|---|---|---|---|
| 802.11b/g | - | 2.4 GHz | 11 / 54 Mbps |
| 802.11n | Wi-Fi 4 | 2.4 / 5 GHz | 600 Mbps |
| 802.11ac | Wi-Fi 5 | 5 GHz | ~3.5 Gbps |
| 802.11ax | Wi-Fi 6 / 6E | 2.4 / 5 / 6 GHz (6E) | ~9.6 Gbps |
| 802.11be | Wi-Fi 7 | 2.4 / 5 / 6 GHz | much higher, multi-link |

Real-world throughput is much lower than these numbers (shared medium, distance, walls).

### Frequency bands and channels

- **2.4 GHz** - longer range, goes through walls better, but crowded (microwaves, Bluetooth,
  neighbors). Only **3 non-overlapping channels**: **1, 6, 11**.
- **5 GHz / 6 GHz** - faster and many more channels, but shorter range.
- **Interference** from overlapping channels is a top cause of slow Wi-Fi in offices and
  apartment buildings.

> 🖼️ **Image idea: 2.4 GHz channel overlap** - the 11 (or 13) channels drawn as overlapping arcs,
> with 1, 6, and 11 highlighted as non-overlapping.
> Suggested file: `assets/img/wifi-channels.png`
<!-- ![wifi channels](<../../assets/img/wifi-channels.png>) -->

### Network configurations

- **Infrastructure** (normal) - devices connect through a **wireless access point (AP)**.
- **Ad-hoc** - devices connect directly to each other, no AP.
- **Mesh** - multiple APs connect to each other wirelessly to extend coverage.
- **Wireless LAN controller** - manages many APs centrally in an enterprise.

### Collision avoidance (CSMA/CA)

Radio can't detect collisions while transmitting, so Wi-Fi uses **CSMA/CA** (Collision
*Avoidance*): listen, wait a random backoff, transmit, and require an acknowledgment for each frame.

### Wireless security

| Protocol | Status |
|---|---|
| **WEP** | broken - can be cracked in minutes. Never use. |
| **WPA** | deprecated (TKIP) |
| **WPA2** | AES-CCMP. **Personal** (pre-shared password) or **Enterprise** (802.1X: each user authenticates against a RADIUS server). Still common. |
| **WPA3** | current best - SAE handshake resists offline password guessing. |

Other notes:

- **MAC filtering** - allowing only listed MAC addresses. Weak (MACs are easy to spoof), but
  sometimes used as an extra layer.
- **WPS** (push-button pairing) has known PIN-brute-force weaknesses - disable it.
- **Guest networks** should be isolated from the internal network (separate VLAN/SSID).

## Cellular networking

Phones (and hotspots) connect to **cell towers**; each covers a "cell," and devices hand off
between cells as they move. Generations: 3G → 4G LTE → 5G (higher bandwidth, lower latency).
In IT support: mobile hotspots for travelers, cellular failover for offices, managing corporate
SIMs/eSIMs.

## How it's used in real IT support

| Symptom | Things to check |
|---|---|
| Whole office offline | ISP outage? modem/ONT lights? which side of the demarc? |
| Slow internet at 7-10 pm only | cable segment congestion (shared bandwidth) |
| Wi-Fi slow in one area | signal strength (RSSI), distance, channel interference, add an AP |
| Can't join Wi-Fi | wrong password, WPA3 device compatibility, MAC filter, 802.1X certificate |
| DSL slow | distance from provider, noisy line |

Useful commands:

```powershell
netsh wlan show interfaces          # SSID, signal %, channel, radio type, speed
netsh wlan show networks mode=bssid # nearby networks and channels
```

```bash
nmcli dev wifi list                 # Linux
```

## Practice project

[`practice/computer-networking/network-diagnostics`](<../../practice/computer-networking/network-diagnostics>) -
includes `wifi_report.py`, which reads your current Wi-Fi connection (SSID, signal, channel,
band, radio type) and flags common problems, plus a layer-by-layer connectivity diagnostic.

## Related

- [Networking services](<networking-services.md>) - NAT and VPNs used over these links.
- [Securing your networks](<../it security/securing-your-networks.md>) - Wi-Fi hardening in depth.
- [Troubleshooting & the future of networking](<troubleshooting-and-future-of-networking.md>) - diagnosing connection problems.
