# Networking Services: DNS, DHCP, NAT, VPNs & Proxies

The layers so far explain *how* data moves. **Networking services** are what make networks
usable at scale: you don't type IP addresses (DNS), you don't configure IPs by hand (DHCP), and a
whole office can share one public IP (NAT).

## DNS - Domain Name System

DNS translates **human-readable names** (`www.example.com`) into **IP addresses**.

### Anatomy of a domain name

```
        www   .   example   .   com   .
        ---       -------       ---   -
    subdomain   second-level    TLD   root (usually hidden)
   (hostname)      domain
```

- A **FQDN** (Fully Qualified Domain Name) is the complete name, e.g. `www.example.com.`
- Each label up to 63 characters; full name up to 255.

### The DNS servers involved

| Server | Role |
|---|---|
| **Caching / recursive resolver** | the server your computer asks (your router, ISP, `8.8.8.8`, `1.1.1.1`). Does the legwork and caches answers. |
| **Root name servers** | 13 logical root server addresses (hundreds of physical servers via anycast). Know where every TLD's servers are. |
| **TLD name servers** | for `.com`, `.org`, `.uk`, ... Know which servers are authoritative for each domain. |
| **Authoritative name servers** | hold the real records for a domain - the final answer. |

### A full lookup (recursive resolution)

```
Laptop -> resolver:          "IP for www.example.com?"
resolver -> root server:     "Who handles .com?"           -> "ask the .com TLD servers"
resolver -> .com TLD server: "Who handles example.com?"    -> "ask ns1.example.com"
resolver -> ns1.example.com: "IP for www.example.com?"     -> "93.184.215.14, TTL 3600"
resolver -> laptop:          "93.184.215.14"  (and caches it for 3600 s)
```

> 🖼️ **Image idea: recursive DNS lookup** - laptop, resolver, root, TLD, authoritative server
> with numbered arrows for each step above.
> Suggested file: `assets/img/dns-resolution.png`
<!-- ![dns resolution](<../../assets/img/dns-resolution.png>) -->

**Caching** happens at every level (browser, OS, resolver). **TTL** (Time To Live, seconds) says
how long an answer may be cached. That's why a DNS change "takes time to propagate" - old answers
live in caches until their TTL expires.

DNS uses **UDP port 53** for normal queries (small, fast) and **TCP port 53** for large responses
and zone transfers.

### Resource record types

| Record | Purpose | Example |
|---|---|---|
| **A** | name → IPv4 address | `www → 93.184.215.14` |
| **AAAA** | name → IPv6 address | `www → 2606:2800:21f:cb07::1` (example) |
| **CNAME** | alias → another name | `shop → shops.myplatform.com` |
| **MX** | mail servers for the domain (with priority) | `10 mail.example.com` |
| **TXT** | free text - used for SPF, DKIM, domain verification | `"v=spf1 include:_spf.google.com -all"` |
| **NS** | authoritative name servers for the zone | `ns1.example.com` |
| **SRV** | location of a service (host + port) | used by Active Directory, VoIP |
| **PTR** | IP → name (reverse lookup) | `14.215.184.93.in-addr.arpa → www.example.com` |
| **SOA** | Start of Authority - zone admin info, serial number | |

### DNS zones

A **zone** is the part of the namespace one organization manages (e.g. `example.com`). Its
records live in a **zone file**. Zones can be delegated: `example.com` can hand `eu.example.com`
to a different set of servers.

### Tools

```powershell
nslookup www.example.com
nslookup -type=MX example.com
Resolve-DnsName example.com -Type TXT       # PowerShell
ipconfig /displaydns                         # local DNS cache
ipconfig /flushdns                           # clear it
```

```bash
dig www.example.com
dig MX example.com +short
dig @1.1.1.1 example.com          # ask a specific resolver
```

## DHCP - Dynamic Host Configuration Protocol

Every device needs an IP, subnet mask, gateway, and DNS server. **DHCP** hands them out
automatically. It's an application-layer protocol using **UDP 67 (server) and 68 (client)**.

### DORA - the four-step lease process

```
Client (no IP yet, src 0.0.0.0)                 DHCP server
  | -- DISCOVER  (broadcast) ------------------->  |  "Any DHCP servers out there?"
  | <- OFFER     (192.168.1.50, 24h lease) -----  |  "You can have .50"
  | -- REQUEST   (broadcast) ------------------->  |  "I'll take .50"
  | <- ACK       --------------------------------  |  "Confirmed, it's yours for 24h"
```

The REQUEST is broadcast so any *other* DHCP servers that offered an address know it was declined.

> 🖼️ **Image idea: DHCP DORA sequence** - client and server timelines with the four messages,
> noting broadcast vs unicast.
> Suggested file: `assets/img/dhcp-dora.png`
<!-- ![dhcp dora](<../../assets/img/dhcp-dora.png>) -->

### Allocation types

| Type | How it works | Use for |
|---|---|---|
| Dynamic | address from a **pool/scope**, returned when the lease expires | laptops, phones |
| Automatic | from a pool, but the server remembers and tries to give the same one back | |
| Fixed / **reservation** | always the same IP for a specific MAC address | printers, servers, cameras |

A client renews at 50% of its lease time. If no DHCP server answers, Windows assigns itself a
`169.254.x.x` (APIPA) address - a big red flag in troubleshooting.

```powershell
ipconfig /release
ipconfig /renew
```

**DHCP relay**: DHCP uses broadcasts, which routers don't forward. A **relay agent** (often on
the router: Cisco calls it "IP helper") forwards DHCP requests from one subnet to a central server.

## NAT - Network Address Translation

NAT lets many devices with **private IPs** share **one public IP**.

```
Laptop 192.168.1.20:50000  --->  Router rewrites source  --->  203.0.113.5:62001 ---> Internet
                                 192.168.1.20:50000 <-> 62001 (stored in NAT table)
Reply to 203.0.113.5:62001  --->  Router looks up table  --->  192.168.1.20:50000
```

- **IP masquerading** - hiding the private network behind one public address.
- **Port preservation / PAT** - using the source port to tell connections apart.
- **Port forwarding** - static rule for *incoming* traffic: "anything to public port 443 goes to
  internal server 192.168.1.10:443." Needed to host a service behind NAT.

NAT is a big reason IPv4 hasn't run out completely, but it also breaks the "every device is
directly reachable" model - which IPv6 restores.

## VPNs - Virtual Private Networks

A **VPN** creates an **encrypted tunnel** over a public network so a remote device behaves as if
it were on the private network.

- **Remote-access VPN** - a laptop at home connects to the office network.
- **Site-to-site VPN** - two office routers/firewalls link their networks permanently.
- Protocols: IPsec, OpenVPN, WireGuard, SSL VPNs.
- Supports two-factor authentication; common source of tickets ("VPN connected but can't reach
  the file share" → often DNS or split-tunnel routing).

## Proxy servers

A **proxy** makes requests **on behalf of** a client.

- **Forward proxy** - sits in front of clients: filtering web access, caching, logging,
  hiding internal IPs.
- **Reverse proxy** - sits in front of servers: load balancing, TLS termination, caching
  (e.g. Nginx in front of web servers).

## How it's used in real IT support

| Symptom | Likely service |
|---|---|
| "Internet is down", but `ping 8.8.8.8` works | DNS |
| `169.254.x.x` address | DHCP server unreachable / scope full |
| Printer IP keeps changing | needs a DHCP reservation |
| Website changed IP, some users still hit the old one | DNS cache / TTL - `ipconfig /flushdns` |
| Email bouncing / marked as spam | MX / SPF (TXT) records |
| Remote user can't reach internal app by name | VPN DNS settings |

## Practice project

[`practice/computer-networking/dns-and-dhcp-lab`](<../../practice/computer-networking/dns-and-dhcp-lab>) -
`dns_query.py` builds a real DNS query packet by hand, sends it over UDP 53, and parses the answer
(A, AAAA, MX, TXT...); `dhcp_dora_sim.py` simulates a DHCP server's lease pool, reservations, and
the DORA exchange; `nat_table_sim.py` shows how a router's NAT table maps private sockets to
public ports.

## Related

- [The transport and application layers](<the-transport-and-application-layers.md>) - ports and UDP these services use.
- [Network and infrastructure services](<../system administration it infrastructure services/network-and-infrastructure-services.md>) - running DNS/DHCP as a sysadmin.
- [Troubleshooting & the future of networking](<troubleshooting-and-future-of-networking.md>) - DNS troubleshooting tools.
