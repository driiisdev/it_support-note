# Securing Your Networks

Hardening the network itself: firewall rules, switch-level protections, Wi-Fi security, and
monitoring traffic so you notice attacks.

## Network hardening best practices

- **Implicit deny** - block everything by default, allow only what's needed. (Allow-listing is
  far safer than trying to block-list every bad thing.)
- **Network separation / segmentation** - put different kinds of devices on different
  **VLANs/subnets** (staff, guests, servers, printers, IoT cameras) and control traffic between
  them with firewall rules. A compromised smart TV shouldn't be able to reach the finance server.
- **Analyze logs** - firewall and network device logs, centrally collected.
- **Flood guards** - detect and block floods (SYN floods, etc.).
- Disable unused switch ports and services; change default credentials on every device.

> 🖼️ **Image idea: segmented office network** - firewall in the middle, separate VLANs for Staff,
> Guests, Servers, IoT, with arrows showing which flows are allowed.
> Suggested file: `assets/img/network-segmentation.png`
<!-- ![network segmentation](<../../assets/img/network-segmentation.png>) -->

## Network hardware hardening (switch features)

| Feature | Protects against | How |
|---|---|---|
| **DHCP snooping** | rogue DHCP servers (attacker hands out a malicious gateway/DNS) | switch only trusts DHCP offers from designated ports; builds a table of IP ↔ MAC ↔ port |
| **Dynamic ARP Inspection (DAI)** | ARP spoofing / MITM | checks ARP replies against the DHCP snooping table |
| **IP Source Guard** | IP spoofing | drops traffic whose source IP doesn't match the snooping table for that port |
| **Port security** | unknown devices plugging in | limit MAC addresses per port |
| **802.1X** | unauthorized devices on wired/wireless ports | devices must authenticate before the port opens |

### 802.1X and EAP

**802.1X** is port-based network access control:

```
Supplicant (laptop) <--EAP--> Authenticator (switch / AP) <--RADIUS--> Authentication server
```

- The port stays closed (except for authentication traffic) until the RADIUS server says yes.
- **EAP-TLS** - the strongest common method: both client and server present **certificates**
  (mutual authentication). No passwords to phish.
- PEAP / EAP-TTLS - server certificate + user password inside a TLS tunnel.

## Network software hardening

- **Firewalls** - network firewalls at the perimeter and between segments; **host-based**
  firewalls on every machine (see [Defense in depth](<defense-in-depth.md>)).
- **Proxies** - forward proxies inspect/filter outbound web traffic; reverse proxies protect
  internal web servers.
- **VPNs** - encrypted access for remote users and between sites; require MFA.

### Firewall rules

Rules are evaluated **top to bottom; first match wins**. A typical rule:

```
#  Action  Proto  Source           Destination      Port   Comment
1  allow   tcp    10.10.0.0/16     10.20.0.10       443    staff -> intranet
2  allow   udp    10.10.0.0/16     10.20.0.53       53     DNS
3  deny    any    10.30.0.0/24     10.20.0.0/16     any    guests -> servers blocked
4  deny    any    any              any              any    implicit deny (cleanup rule)
```

Common rule-base problems:

- **Shadowed rules** - a broad rule above a specific one means the specific one never matches.
- **Any-any allows** - `allow any any any` defeats the firewall.
- **Unused / undocumented rules** - nobody knows why they exist; every rule should have an owner
  and a reason.
- Risky services open to the internet: RDP 3389, SMB 445, Telnet 23, databases.

```powershell
Get-NetFirewallProfile | Select-Object Name, Enabled, DefaultInboundAction
Get-NetFirewallRule -Enabled True -Direction Inbound | Select-Object DisplayName, Action, Profile
```

```bash
sudo ufw status verbose       # Ubuntu
sudo iptables -L -n -v        # raw iptables
sudo nft list ruleset         # nftables
```

## Wireless security

| Option | Verdict |
|---|---|
| **WEP** | broken, crackable in minutes. Never. |
| **WPA (TKIP)** | deprecated |
| **WPA2-Personal (PSK, AES-CCMP)** | OK for home/small office **with a long passphrase** - captured handshakes can be cracked offline if the password is weak |
| **WPA2/WPA3-Enterprise (802.1X)** | per-user credentials or certificates via RADIUS - recommended for organizations |
| **WPA3-Personal (SAE)** | resists offline dictionary attacks - best for PSK networks |
| **WPS** | PIN can be brute-forced - **disable** |

Also: separate **guest SSID** on its own VLAN with client isolation; change the router admin
password; keep AP firmware updated; scan for **rogue APs**.

## Network monitoring

### Packet sniffing

Capturing network traffic to analyze it.

- **Promiscuous mode** - the NIC accepts all frames it sees, not just ones addressed to it.
- **Monitor mode** (Wi-Fi) - captures all wireless frames in the air, without joining a network.
- On switched networks you only see your own traffic unless you use a **mirror/SPAN port** or a
  network **tap**.

Tools:

```bash
sudo tcpdump -i eth0 -n port 53                # live DNS traffic
sudo tcpdump -i eth0 -w capture.pcap host 10.0.0.5
```

- **Wireshark** - GUI analyzer; display filters like `dns`, `tcp.port == 443`, `ip.addr == 10.0.0.5`,
  `tcp.flags.syn == 1 && tcp.flags.ack == 0` (SYN scan / flood).

> Only capture traffic on networks you own or are authorized to monitor.

### IDS / IPS

| | IDS - Intrusion Detection System | IPS - Intrusion Prevention System |
|---|---|---|
| Action | **detects and alerts** | **detects and blocks** |
| Placement | passive (copy of traffic) | inline (traffic flows through it) |
| Risk | missed alerts | false positives block legitimate traffic |

- **NIDS** - network-based (watches traffic); **HIDS** - host-based (watches one machine's files,
  logs, processes).
- Detection: **signature-based** (known attack patterns) vs **anomaly-based** (deviation from
  normal behavior).
- Tools: **Snort**, **Suricata**, **Zeek** (network); **OSSEC/Wazuh** (host).

### SIEM

A **Security Information and Event Management** system collects logs from firewalls, servers,
endpoints, and cloud services, normalizes them, correlates events, and alerts (Splunk, Microsoft
Sentinel, Elastic, Wazuh).

## Practice project

[`practice/it-security/firewall-rule-auditor`](<../../practice/it-security/firewall-rule-auditor>) -
loads a firewall rule base from CSV, simulates "first match wins" for test packets, and audits the
rules for **shadowed rules**, **any-any allows**, risky ports exposed to the internet, missing
cleanup (implicit deny) rule, and undocumented rules. Includes a bad sample rule set to fix.

## Related

- [Understanding security threats](<understanding-security-threats.md>) - the attacks these controls stop.
- [The 3 As of cybersecurity](<the-3-as-of-cybersecurity.md>) - RADIUS and 802.1X authentication.
- [Connecting to the internet](<../computer networking/connecting-to-the-internet.md>) - Wi-Fi standards.
