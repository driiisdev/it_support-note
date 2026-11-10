# Networking Basics

**Computer networking** is how computers talk to each other. This is the beginner-level version
of the topic; the [Computer networking module](<../computer networking/introduction-to-networking.md>)
goes layer by layer in depth.

## Key terms

| Term | Meaning |
|---|---|
| Network | two or more devices connected so they can share data |
| LAN | Local Area Network - one home, office, or building |
| WAN | Wide Area Network - connects LANs across long distances (the internet is the biggest WAN) |
| ISP | Internet Service Provider - the company that connects you to the internet |
| NIC | Network Interface Card - the hardware in a device that connects it to a network (wired or Wi-Fi) |
| Bandwidth | how much data can move per second (Mbps, Gbps) |
| Latency | how long one piece of data takes to get there (ms) |

## A short history of the internet

- **1960s-70s - ARPANET**: US research network, the first to use **packet switching** (data is
  split into small packets that can take different routes).
- **1970s-80s - TCP/IP** is created and becomes the standard that lets different networks
  "inter-network" - hence **internet**.
- **1989-91 - World Wide Web**: Tim Berners-Lee invents HTTP, HTML, and URLs - the web is *one
  service* that runs on the internet (email is another).
- **1990s-today** - commercial ISPs, broadband, Wi-Fi, mobile data, cloud.

## Network hardware

```
   [Laptop]   [Phone]                       Internet
       \        /                               |
     (Wi-Fi access point)                    [Modem]  <- converts ISP signal
              |                                 |
           [Switch] --------------------- [Router]    <- connects your LAN to other networks
          /   |    \
   [Desktop] [Printer] [Server]
```

- **Hub** (old) - repeats everything to every port. Everybody hears everything → collisions.
- **Switch** - learns which device (by MAC address) is on which port and only sends data where
  it needs to go. Connects devices **within** a network.
- **Router** - forwards data **between** networks (your LAN ↔ the internet) using IP addresses.
- **Modem** - converts the ISP's signal (cable, DSL, fiber) into Ethernet.
- **Access point** - lets wireless devices join the wired network.

Home "routers" are usually all of these in one box: router + switch + Wi-Fi AP + often modem.

> 🖼️ **Image idea: home/small-office network diagram** - ISP → modem → router → switch + AP →
> devices, like the ASCII art above but with real device icons.
> Suggested file: `assets/img/small-office-network.png`
<!-- ![small office network](<../../assets/img/small-office-network.png>) -->

## Cables and wireless

- **Ethernet (twisted-pair copper)** - Cat5e (1 Gbps), Cat6 (1 Gbps, 10 Gbps short runs),
  Cat6a (10 Gbps). RJ45 connectors. Max ~100 m per run.
- **Fiber optic** - light through glass. Very fast, long distances, immune to electrical
  interference. Used between buildings, in data centers, and for ISP lines.
- **Wi-Fi** - radio waves (2.4 GHz: longer range, more interference; 5/6 GHz: faster, shorter
  range). Convenient, but slower and less reliable than a cable.

## Addresses: how devices find each other

Every device on a network has (at least) two addresses:

| Address | Example | Layer | Purpose |
|---|---|---|---|
| **MAC address** | `3C:52:82:1A:9F:00` | data link | burned into the NIC; identifies the device on the **local** network |
| **IP address** | `192.168.1.25` | network | assigned by the network; identifies the device across networks |

- **IPv4** - 32 bits, written as four numbers 0-255 (`192.168.1.25`). ~4.3 billion addresses -
  not enough for the world.
- **IPv6** - 128 bits, written in hex (`2001:db8::1`). Practically unlimited addresses.
- **Private IPs** (`192.168.x.x`, `10.x.x.x`, `172.16-31.x.x`) are used inside LANs; the
  router uses **NAT** to share one public IP among all of them.
- **DHCP** - the service (usually on the router) that hands out IP addresses automatically.

## DNS: names instead of numbers

People remember `google.com`; computers need an IP. **DNS (Domain Name System)** is the internet's
phone book: it translates names into IP addresses.

```
You type "example.com"
  -> your computer asks its DNS server "what's the IP of example.com?"
  -> DNS answers "93.184.215.14" (example)
  -> your browser connects to that IP
```

A huge number of "the internet is down" tickets are actually **DNS** problems: the connection
works, but names don't resolve. Test with `nslookup example.com`.

## The limitations of the internet & digital divide

- **IPv4 exhaustion** - solved short-term by NAT, long-term by IPv6.
- **Privacy & security** - data crosses many networks you don't control → encryption (HTTPS, VPN)
  matters.
- **Digital divide** - not everyone has equal access to reliable internet or devices. IT support
  often bridges this inside organizations (training, loaner equipment, accessible tools).

## Quick connectivity checks every support person should know

```powershell
ipconfig /all              # Windows: my IP, gateway, DNS servers, MAC
ping 192.168.1.1           # can I reach my router?
ping 8.8.8.8               # can I reach the internet by IP?
nslookup example.com       # does DNS work?
tracert example.com        # where along the path does it break?
```

```bash
ip addr        # Linux equivalents
ping -c 4 8.8.8.8
dig example.com     # or nslookup
traceroute example.com
```

If `ping 8.8.8.8` works but `ping example.com` doesn't → it's DNS. If the router doesn't answer
→ it's local (cable, Wi-Fi, NIC). This "work outward from yourself" method is the backbone of
network troubleshooting.

## Practice project

[`practice/technical-support-fundamentals/helpdesk-troubleshooting`](<../../practice/technical-support-fundamentals/helpdesk-troubleshooting>) -
includes `connectivity_check.py`, which automates exactly that "work outward" sequence
(local IP → gateway → internet by IP → DNS → HTTPS) and tells you where it broke.

## Related

- [Introduction to networking](<../computer networking/introduction-to-networking.md>) - the 5-layer model in depth.
- [Networking services](<../computer networking/networking-services.md>) - DNS, DHCP, NAT in depth.
- [Troubleshooting](<troubleshooting.md>) - the general method behind "work outward."
