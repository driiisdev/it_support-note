# Troubleshooting & the Future of Networking

How to find out *where* a network problem is (ICMP, ping, traceroute, port tests, DNS tools),
and where networking is heading (cloud and IPv6).

## Error detection vs error recovery

- **Error detection** - noticing data is corrupted (Ethernet's CRC, IP and TCP checksums).
- **Error recovery** - fixing it (TCP retransmits lost/corrupted segments; UDP doesn't).

When something goes wrong in the middle of the network, routers report back using **ICMP**.

## ICMP - Internet Control Message Protocol

ICMP carries **error and diagnostic messages** between network devices. It sits on top of IP
(protocol number 1) but isn't used to carry user data.

ICMP header fields: **Type** (8 bits), **Code** (8 bits), **Checksum** (16), **Rest of header**
(32), then **Data** (includes the IP header + first 8 bytes of the packet that caused the error).

| Type | Code | Meaning |
|---|---|---|
| 0 | 0 | Echo reply (ping response) |
| 3 | 0-15 | Destination unreachable (0 = network, 1 = host, 3 = port unreachable, ...) |
| 8 | 0 | Echo request (ping) |
| 11 | 0 | Time exceeded - TTL hit 0 (traceroute relies on this) |

**Many firewalls block ICMP**, so "ping fails" does not always mean "host is down."

## ping

Sends ICMP **Echo Request** and waits for **Echo Reply**.

```powershell
ping 8.8.8.8            # Windows sends 4 by default
ping -t 8.8.8.8         # continuous, Ctrl+C to stop
ping -n 20 server01     # 20 pings
```

```bash
ping -c 4 8.8.8.8       # Linux/macOS run forever by default; -c sets count
```

Read the output: **time** (latency in ms), **TTL**, and **packet loss %**. Intermittent loss →
flaky link, Wi-Fi interference, or an overloaded device.

## traceroute / tracert

Shows **every router hop** along the path. How it works: it sends packets with **TTL = 1, then 2,
then 3, ...**. Each router that decrements TTL to 0 sends back ICMP "Time exceeded" - revealing
itself.

```
TTL=1 -> router 1 replies "time exceeded"   -> hop 1 = 192.168.1.1
TTL=2 -> router 2 replies "time exceeded"   -> hop 2 = 10.20.0.1
TTL=3 -> ...                                -> ...
TTL=n -> destination replies                -> done
```

> 🖼️ **Image idea: how traceroute uses TTL** - a path of routers with three probes stopping one
> hop further each time, each returning an ICMP "time exceeded" arrow.
> Suggested file: `assets/img/traceroute-ttl.png`
<!-- ![traceroute ttl](<../../assets/img/traceroute-ttl.png>) -->

```powershell
tracert example.com           # Windows (ICMP)
pathping example.com          # Windows: traceroute + per-hop loss stats over time
```

```bash
traceroute example.com        # Linux/macOS (UDP by default; -I for ICMP)
mtr example.com               # live traceroute + ping combined
```

`* * *` on a hop means that router didn't reply (often just configured not to) - only a problem
if *all* hops after it also fail.

## Testing port connectivity

ping proves the **host** is reachable; it says nothing about whether a **service** (port) is.

```powershell
Test-NetConnection mail.example.com -Port 587
# TcpTestSucceeded : True / False
```

```bash
nc -zv mail.example.com 587      # netcat: -z just scan, -v verbose
```

## DNS troubleshooting

```powershell
nslookup intranet.company.local           # uses your configured DNS server
nslookup intranet.company.local 8.8.8.8   # ask a specific server (compare answers!)
ipconfig /flushdns
```

- **Public DNS servers**: Google `8.8.8.8` / `8.8.4.4`, Cloudflare `1.1.1.1`, Quad9 `9.9.9.9`.
  Useful for testing "is it my DNS server or DNS in general?"
- **Hosts file** - local name overrides checked *before* DNS:
  - Windows: `C:\Windows\System32\drivers\etc\hosts`
  - Linux/macOS: `/etc/hosts`
  - A stale entry here (or one added by malware) can make one site "broken" on one PC only.
- `localhost` → `127.0.0.1` (IPv4) / `::1` (IPv6) is defined here too.

## A troubleshooting order that works

Work **bottom-up** (from the cable to the app) or **outward** (from you to the destination):

```
1. Physical    link light? cable? Wi-Fi connected?           (ipconfig / netsh wlan)
2. IP config   valid IP? not 169.254.x.x? right gateway/DNS? (ipconfig /all)
3. Local       ping the default gateway
4. Internet    ping 8.8.8.8
5. DNS         nslookup a name
6. Path        tracert to find where it stops
7. Service     Test-NetConnection host -Port N
8. App         browser/app-specific errors, certificates, proxy settings
```

## The cloud

**Cloud computing** = renting computing resources (servers, storage, apps) over the network
instead of owning them. Built on **virtualization**: one physical **host** runs many **guest**
VMs, managed by a **hypervisor**.

| Model | You manage | Provider manages | Examples |
|---|---|---|---|
| **IaaS** - Infrastructure as a Service | OS, apps, data | hardware, network, virtualization | AWS EC2, Azure VMs |
| **PaaS** - Platform as a Service | apps, data | everything below the app | Azure App Service, Heroku |
| **SaaS** - Software as a Service | just your data/users | the entire application | Microsoft 365, Gmail, Salesforce |

Deployment types: **public cloud** (shared provider), **private cloud** (dedicated to one org),
**hybrid** (mix of on-prem and cloud).

**Cloud storage** - files live in the provider's data centers, replicated across locations; good
for backups and sharing (OneDrive, Google Drive, S3).

## IPv6

IPv4's ~4.3 billion addresses ran out. **IPv6** uses **128-bit** addresses: 2^128 ≈ 3.4 × 10^38.

### Writing IPv6 addresses

8 groups of 4 hex digits (each group = 16 bits, a "hextet"):

```
Full:        2001:0db8:0000:0000:0000:ff00:0042:8329
Rule 1 - drop leading zeros in each group:
             2001:db8:0:0:0:ff00:42:8329
Rule 2 - replace ONE run of consecutive all-zero groups with "::":
             2001:db8::ff00:42:8329
```

`::` can only appear **once** (otherwise you couldn't tell how many zeros each one hides).

### Special addresses

| Address / range | Meaning |
|---|---|
| `::1` | loopback (IPv6 version of 127.0.0.1) |
| `::` | unspecified |
| `fe80::/10` | **link-local** - auto-assigned on every interface, only valid on the local link |
| `ff00::/8` | multicast (IPv6 has no broadcast) |
| `2001:db8::/32` | documentation/examples only |
| `fc00::/7` | unique local (similar role to RFC 1918 private ranges) |

A typical address: first 64 bits = **network prefix**, last 64 bits = **interface ID**.
Devices can configure themselves with **SLAAC** (stateless autoconfiguration) or use **DHCPv6**.

### IPv6 header

Simpler than IPv4: version, traffic class, **flow label**, payload length, **next header**
(like IPv4's protocol field), **hop limit** (like TTL), source and destination (128 bits each).
No header checksum and no router fragmentation - optional features go in extension headers.

### Coexistence with IPv4

- **Dual stack** - devices run both IPv4 and IPv6 at the same time (most common today).
- **Tunneling** - IPv6 packets wrapped inside IPv4 to cross IPv4-only networks.
- **IPv4-mapped addresses** - `::ffff:192.0.2.1`.

## Practice project

[`practice/computer-networking/network-diagnostics`](<../../practice/computer-networking/network-diagnostics>) -
`net_doctor.py` runs the full bottom-up troubleshooting order above automatically and prints a
layer-by-layer report with a likely cause; `ipv6_tool.py` expands/compresses IPv6 addresses and
classifies them (loopback, link-local, documentation, ...).

## Related

- [The network layer](<the-network-layer.md>) - TTL and routing behind traceroute.
- [Networking services](<networking-services.md>) - DNS in depth.
- [Network and infrastructure services](<../system administration it infrastructure services/network-and-infrastructure-services.md>) - cloud and virtualization from the sysadmin side.
