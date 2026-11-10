# Network & Infrastructure Services

The behind-the-scenes services every organization depends on: server operating systems,
virtualization, remote access, file transfer, time sync, DNS, and DHCP - from the point of view
of the person **running** them.

## Types of IT infrastructure services

| Model | What the company runs itself | Example |
|---|---|---|
| On-premises | everything | own servers in a server room |
| **IaaS** | OS and up | VMs in AWS/Azure/GCP |
| **PaaS** | the app only | managed database, App Service |
| **SaaS** | nothing but configuration | Microsoft 365, Google Workspace |

Choosing between them is a trade-off of **control vs. maintenance effort vs. cost**.

## Server operating systems

- **Windows Server** - Active Directory, file/print, IIS, Hyper-V. Managed via Server Manager,
  PowerShell, Remote Server Administration Tools (RSAT), Windows Admin Center.
- **Linux** (Ubuntu Server, Red Hat Enterprise Linux, Rocky, Debian) - web servers, databases,
  containers. Usually no GUI; managed over SSH and with automation tools.

Server OSes differ from desktop OSes in what they include: more connection limits, server roles,
long-term support, and often no desktop by default (smaller attack surface).

## Virtualizing servers

Running many virtual servers on fewer physical hosts:

- **Better utilization** - a physical server running one service is often 90% idle.
- **Easier recovery** - VMs are files: back up, snapshot, move to another host.
- **Faster provisioning** - a new server from a template in minutes.
- **Risk**: a host failure takes down **every VM on it** → clusters with failover.

## Remote access services

| Service | Port | Use |
|---|---|---|
| **SSH** | TCP 22 | Linux/network device administration |
| **RDP** | TCP/UDP 3389 | Windows GUI administration |
| VPN | varies | remote users reaching internal resources |

See [Operating systems in practice](<../os power user/operating-systems-in-practice.md>) for usage.

## File transfer services

| Protocol | Port | Notes |
|---|---|---|
| **FTP** | TCP 20/21 | old; **unencrypted** - credentials sent in plain text |
| **SFTP** | TCP 22 | file transfer over SSH - encrypted. Preferred. |
| **FTPS** | TCP 990 (implicit) / 21 (explicit) | FTP with TLS |
| **TFTP** | UDP 69 | "trivial" FTP: no authentication; used for PXE boot images and network device configs on trusted networks |

## NTP - Network Time Protocol

Keeps clocks in sync. Uses **UDP port 123**.

Why it matters more than you'd think:

- **Kerberos** (Active Directory logons) fails if clocks differ by more than **5 minutes** (default).
- **TLS certificates** look "not yet valid" or "expired" on a machine with the wrong date.
- **Logs** from different servers can't be correlated if their clocks disagree.

NTP is hierarchical, by **stratum**:

```
Stratum 0:  atomic clocks / GPS (reference clocks, not on the network)
Stratum 1:  servers directly attached to stratum 0
Stratum 2:  sync from stratum 1 (e.g. pool.ntp.org, time.windows.com)
Stratum 3:  your internal NTP server / domain controller
            -> all your clients sync from it
```

In an AD domain, clients sync from domain controllers, and the **PDC emulator** DC syncs from an
external source.

```powershell
w32tm /query /status            # source, stratum, last sync
w32tm /resync
```

```bash
timedatectl                     # Linux: is NTP synchronized?
chronyc sources                 # if using chrony
```

> 🖼️ **Image idea: NTP stratum hierarchy** - pyramid from stratum 0 (atomic clock) down to office
> laptops.
> Suggested file: `assets/img/ntp-stratum.png`
<!-- ![ntp stratum](<../../assets/img/ntp-stratum.png>) -->

## Network support services

- **Intranet** - internal website for company info, docs, tools.
- **Proxy server** - filters/logs/caches web traffic for the organization.
- These are often SaaS now (SharePoint, cloud web gateways).

## DNS for sysadmins

Beyond understanding DNS (see [Networking services](<../computer networking/networking-services.md>)),
sysadmins run it:

- **Internal DNS** - names for internal hosts (`fileserver.corp.example.com`). In Windows
  networks, DNS is usually hosted on the domain controllers and **AD depends on it** (clients find
  DCs via SRV records).
- **External DNS** - public records for the company website and email (often managed at the
  registrar or a DNS host like Cloudflare/Route 53).
- **Forwarders** - internal DNS servers forward anything they don't know to upstream resolvers.
- Hosting a website needs: domain registration → **A/AAAA** record (or CNAME) → web server.
- Change TTL to something short (e.g. 300 s) a day **before** a planned migration, so the switch
  propagates fast.

## DHCP for sysadmins

- **Scope** - the range of addresses handed out on a subnet (e.g. `192.168.10.100-200`) plus
  **options**: gateway (option 3), DNS servers (option 6), domain name (option 15), lease time.
- **Exclusions** - addresses inside the range that DHCP must not hand out (static devices).
- **Reservations** - fixed IP for a MAC (printers, servers, cameras).
- **Relay / IP helper** - one central DHCP server serves many subnets.
- Watch for **scope exhaustion** (more devices than addresses → new devices get `169.254.x.x`).
- **Redundancy** - DHCP failover (Windows Server) or split scopes across two servers.

## Troubleshooting network services

| Problem | Investigate |
|---|---|
| Can't resolve a hostname | `nslookup` with the internal DNS server; does the record exist? Is the client using the right DNS server? |
| IP address conflict | a static IP inside the DHCP range → add an exclusion or reservation |
| Users get 169.254.x.x | DHCP service down, scope exhausted, relay broken |
| Domain logon fails with time errors | NTP / clock skew |
| Can't reach server by name but can by IP | DNS, or the hosts file |

## Managing system services

```powershell
Get-Service DNS, DHCPServer, W32Time
Restart-Service W32Time
```

```bash
systemctl status chrony
sudo systemctl restart isc-dhcp-server
```

## Practice project

[`practice/system-administration-it-infrastructure-services/infra-services-check`](<../../practice/system-administration-it-infrastructure-services/infra-services-check>) -
an **SNTP client written from scratch** (sends a real NTP packet to `pool.ntp.org` and calculates
your clock offset), a DNS health check for a list of expected records, and a DHCP scope planner
that validates reservations and exclusions against the scope.

## Related

- [Networking services](<../computer networking/networking-services.md>) - how DNS/DHCP/NAT work.
- [Software and platform services](<software-and-platform-services.md>) - services that run on top.
- [Directory services](<directory-services.md>) - why AD needs DNS and NTP.
