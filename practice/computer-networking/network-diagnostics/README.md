# Practice: Network Diagnostics (Connecting to the Internet, Troubleshooting & the Future of Networking)

Concept notes:
[`connecting-to-the-internet.md`](<../../../concepts/computer networking/connecting-to-the-internet.md>) ·
[`troubleshooting-and-future-of-networking.md`](<../../../concepts/computer networking/troubleshooting-and-future-of-networking.md>)

## What this demonstrates

The full **bottom-up troubleshooting order** as one tool that writes a report you can attach to a
ticket, plus two helpers for the topics around it:

- **`net_doctor.py`** - IP config sanity checks → gateway → internet by IP → DNS (your server vs a
  public one vs the hosts file) → traceroute → the exact service port. Ends with **findings** in
  plain English.
- **`wifi_report.py`** - your current Wi-Fi link: band, channel, signal, standard, security - and what's
  wrong with it (weak signal, overlapping 2.4 GHz channel, WEP/TKIP, old radio standard).
- **`ipv6_tool.py`** - IPv6 shortening rules step by step, address type classification, and spotting
  MAC-derived (EUI-64) interface IDs.

## Scenario

A remote user says "Outlook works but Teams doesn't, and the Wi-Fi is slow." You ask them to run
`net_doctor.py` and `wifi_report.py` and send you the output - now you're troubleshooting with
facts instead of guesses.

## Folder structure

```
network-diagnostics/
  net_doctor.py   <- 6-step bottom-up diagnosis, saves reports/net_doctor-<timestamp>.txt
  wifi_report.py  <- netsh wlan (Windows) / nmcli (Linux) parser + assessment; --sample for demo
  ipv6_tool.py    <- expand/compress/classify; `mine` = this machine's IPv6 addresses
  reports/        <- created on run (gitignored - contains your network details)
```

## Code walkthrough

**Config sanity checks catch static-IP mistakes before any packet is sent:**

```python
net = ipaddress.ip_network(f"{cfg['ip']}/{cfg['mask']}", strict=False)
if ipaddress.ip_address(cfg["gateway"]) not in net:
    findings.append("Gateway is outside the subnet - wrong mask or gateway")
```

**DNS three ways** isolates *which* part of name resolution is broken:

| Check | Uses | If only this one fails... |
|---|---|---|
| OS resolver (`gethostbyname_ex`) | hosts file + configured DNS | hosts-file or client config issue |
| raw query to **your** DNS server | that server only | your/internal DNS server is broken |
| raw query to **8.8.8.8** | public DNS | upstream/internet DNS issue (rare) |

**Traceroute** shells out to `tracert -d` / `traceroute -n` (`-d`/`-n` = don't reverse-resolve each
hop - much faster). Rows of `* * *` in the middle are normal (routers that don't answer probes);
only trailing timeouts that never reach the target point at a block.

**`wifi_report.py`** applies the rules from the note: 2.4 GHz channels should be 1, 6, or 11; signal
below ~40% is weak; WEP/TKIP are broken/deprecated.

**`ipv6_tool.py`** shows both shortening rules separately and detects EUI-64 addresses (`ff:fe` in the
middle of the interface ID) - which embed the device's MAC, the reason OSes now use random
"privacy" interface IDs.

## Run it

```bash
python net_doctor.py
python net_doctor.py --target outlook.office365.com --port 443
python net_doctor.py --target example.com --port 8443          # see a FILTERED port finding
python wifi_report.py
python wifi_report.py --sample
python ipv6_tool.py 2001:0db8:0000:0000:0000:ff00:0042:8329 fe80::1c2b:3cff:fe4d:5e6f ff02::1
python ipv6_tool.py mine
```

Expected (excerpts):

```
[4] DNS for www.google.com
    OS resolver (hosts file + your DNS servers): ['142.251.156.119', ...]
    your DNS server 10.254.21.22   : [...]
    public DNS 8.8.8.8             : [...]
[6] Service port example.com:8443
    FILTERED (timeout - firewall or host down)
FINDINGS
  - Port 8443 not open - service down, wrong port, or firewall.

Assessment:
  - Weak signal (38%). Move closer to the AP, remove obstacles, or add an access point.
  - Channel 3 overlaps neighbors - 2.4 GHz APs should use 1, 6 or 11.

  Rule 1 (drop leading zeros in each group): 2001:db8:0:0:0:ff00:42:8329
  Rule 2 (longest run of 0 groups -> '::', once): 2001:db8::ff00:42:8329
```

## Try this yourself

- Break DNS on purpose (set your adapter's DNS to `10.255.255.1`) and run `net_doctor.py` - the
  "your DNS fails but public DNS works" finding should appear. Put it back afterwards!
- Add a hosts-file line for your target (admin rights; remove it afterwards) - the hosts-file
  override finding appears and the OS resolver answer differs from both DNS servers.
- Run `wifi_report.py` in different rooms; note signal % and RSSI. Build a mini "site survey"
  table: room → signal → band → channel.
- Run `netsh wlan show networks mode=bssid` and count how many neighbor networks share your
  2.4 GHz channel.
- Add a step to `net_doctor.py`: **MTU test** with `ping -f -l 1472 8.8.8.8` (Windows; Linux:
  `ping -M do -s 1472`) - if it fails but smaller sizes work, something on the path (often a VPN)
  has a smaller MTU.
- Add an **IPv6 connectivity** step: `socket.create_connection(("ipv6.google.com", 443))`.

## Real-world equivalent

- Windows "Network troubleshooter," `pathping`, `mtr`, PingPlotter - the same layered idea.
- RMM tools run scripts like `net_doctor.py` remotely on a user's laptop and attach the output to
  the ticket.
- Wi-Fi site surveys (Ekahau, NetSpot) are `wifi_report.py` with a floor plan.
