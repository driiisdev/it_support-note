# IT Support - Notes

Personal study notes for the **Fundamentals of IT Support** course - lecture notes turned into
proper write-ups, plus small hands-on projects for each topic so the ideas stick beyond just
reading about them.

## How notes are organized

```
concepts/
  <module name>/            <- matches a course section (e.g. "computer networking")
    topic name.txt           <- raw notes taken live, during the lecture
    topic-name.md            <- write-up: definition, how it works, real support use, commands,
                                tables, image callouts, links to related topics
practice/
  <module-name>/             <- kebab-case, these are project folders
    <project>/
      README.md               <- what it demonstrates, scenario, folder structure, code walkthrough,
                                 run it, try this yourself, real-world equivalent
      ...code...
assets/img/                  <- images for the notes (add as you find/create them - see below)
```

**Why a `.txt` *and* a `.md` for the same topic?** The `.txt` stays as the honest, messy,
in-the-moment note - good for review. The `.md` is the "I actually understand this now" version,
written after connecting it to how it's used in real IT support.

> **Status of the `.txt` files:** all 29 were still empty when the `.md` write-ups were created, so
> every `.md` was written from scratch, following the course's section titles. As you take lecture
> notes into the `.txt` files, compare them with the `.md` and add anything the course covered that
> the write-up missed (or correct anything it explains differently).

**Why do some `practice/` folders cover multiple topics at once?** Some topics only make sense
together - e.g. hardware, OS, and software are all answers to "what is this machine?", so one
**pc-inventory** project collects all three. Where that's true, one project covers several topics.

**Image callouts.** Every note marks the places where a diagram would help, like this:

```markdown
> 🖼️ **Image idea: TCP handshake + teardown sequence diagram** - two vertical timelines, ...
> Suggested file: `assets/img/tcp-handshake.png`
<!-- ![tcp handshake](<../../assets/img/tcp-handshake.png>) -->
```

Save the image under that file name in `assets/img/`, then delete the `<!-- -->` around the image
line to make it show up.

## Modules

| # | Module | Course section | Notes | Practice projects |
|---|---|---|---|---|
| 1 | [Technical support fundamentals](<concepts/technical support fundamentals>) | Technical Support Fundamentals | 6 | 3 |
| 2 | [Computer networking](<concepts/computer networking>) | The Bits and Bytes of Computer Networking | 6 | 5 |
| 3 | [OS power user](<concepts/os power user>) | Operating Systems and You: Becoming a Power User | 6 | 5 |
| 4 | [System administration](<concepts/system administration it infrastructure services>) | System Administration and IT Infrastructure Services | 5 | 5 |
| 5 | [IT security](<concepts/it security>) | IT Security: Defense against the digital dark arts | 6 | 6 |

The `practice/<module-name>` folder name always matches its `concepts/<module name>` folder
(hyphenated instead of spaced), so the two stay easy to find side by side.

## Technical support fundamentals - topics

What IT support is, how computers represent information, the hardware/OS/software stack, networking
basics, and the troubleshooting + customer service method everything else builds on.

| # | Topic | Note | Practice project |
|---|---|---|---|
| 1 | Introduction (history, binary, encoding, logic gates) | [introduction.md](<concepts/technical support fundamentals/introduction.md>) | [bits-and-encoding](practice/technical-support-fundamentals/bits-and-encoding) |
| 2 | Hardware | [hardware.md](<concepts/technical support fundamentals/hardware.md>) | [pc-inventory](practice/technical-support-fundamentals/pc-inventory) |
| 3 | Operating system | [operating-system.md](<concepts/technical support fundamentals/operating-system.md>) | [pc-inventory](practice/technical-support-fundamentals/pc-inventory) |
| 4 | Networking | [networking.md](<concepts/technical support fundamentals/networking.md>) | [helpdesk-troubleshooting](practice/technical-support-fundamentals/helpdesk-troubleshooting) (`connectivity_check.py`) |
| 5 | Software | [software.md](<concepts/technical support fundamentals/software.md>) | [pc-inventory](practice/technical-support-fundamentals/pc-inventory) (`Get-Inventory.ps1`) |
| 6 | Troubleshooting & customer service | [troubleshooting.md](<concepts/technical support fundamentals/troubleshooting.md>) | [helpdesk-troubleshooting](practice/technical-support-fundamentals/helpdesk-troubleshooting) (`ticket.py`) |

## Computer networking - topics

The five-layer model from the cable up: Ethernet frames, IP and subnetting, TCP/UDP and ports, the
services that make networks usable (DNS, DHCP, NAT), how sites connect to the internet, and how to
troubleshoot all of it - plus IPv6 and the cloud.

| # | Topic | Note | Practice project |
|---|---|---|---|
| 1 | Introduction to networking (layers, cables, Ethernet) | [introduction-to-networking.md](<concepts/computer networking/introduction-to-networking.md>) | [packet-dissector](practice/computer-networking/packet-dissector) |
| 2 | The network layer (IP, subnetting, routing) | [the-network-layer.md](<concepts/computer networking/the-network-layer.md>) | [subnet-planner](practice/computer-networking/subnet-planner) (+ IPv4 header in [packet-dissector](practice/computer-networking/packet-dissector)) |
| 3 | The transport and application layers | [the-transport-and-application-layers.md](<concepts/computer networking/the-transport-and-application-layers.md>) | [socket-lab](practice/computer-networking/socket-lab) |
| 4 | Networking services (DNS, DHCP, NAT, VPN, proxies) | [networking-services.md](<concepts/computer networking/networking-services.md>) | [dns-and-dhcp-lab](practice/computer-networking/dns-and-dhcp-lab) |
| 5 | Connecting to the internet (broadband, WAN, Wi-Fi) | [connecting-to-the-internet.md](<concepts/computer networking/connecting-to-the-internet.md>) | [network-diagnostics](practice/computer-networking/network-diagnostics) (`wifi_report.py`) |
| 6 | Troubleshooting & the future of networking (ICMP, cloud, IPv6) | [troubleshooting-and-future-of-networking.md](<concepts/computer networking/troubleshooting-and-future-of-networking.md>) | [network-diagnostics](practice/computer-networking/network-diagnostics) (`net_doctor.py`, `ipv6_tool.py`) |

## OS power user - topics

Windows and Linux side by side: the command line, users and permissions, package management, file
systems, processes, and the day-to-day practice of remote access, VMs, logs, and deployment.

| # | Topic | Note | Practice project |
|---|---|---|---|
| 1 | Navigating the system | [navigating-the-system.md](<concepts/os power user/navigating-the-system.md>) | [shell-navigation-lab](practice/os-power-user/shell-navigation-lab) |
| 2 | Users and permissions | [users-and-permissions.md](<concepts/os power user/users-and-permissions.md>) | [user-permissions-lab](practice/os-power-user/user-permissions-lab) |
| 3 | Packages and software management | [packages-and-software-management.md](<concepts/os power user/packages-and-software-management.md>) | [software-deployment](practice/os-power-user/software-deployment) |
| 4 | File systems | [file-systems.md](<concepts/os power user/file-systems.md>) | [disk-report](practice/os-power-user/disk-report) |
| 5 | Process management | [process-management.md](<concepts/os power user/process-management.md>) | [process-and-log-monitor](practice/os-power-user/process-and-log-monitor) (`process_watch.py`, `signals_demo.py`) |
| 6 | Operating systems in practice (remote access, VMs, logs, imaging) | [operating-systems-in-practice.md](<concepts/os power user/operating-systems-in-practice.md>) | [process-and-log-monitor](practice/os-power-user/process-and-log-monitor) (`log_analyzer.py`) |

## System administration & IT infrastructure services - topics

Running IT for an organization: what sysadmins are responsible for, the infrastructure services
everything depends on (DNS, DHCP, NTP), the platform services people use (email, files, web),
directory services (LDAP / Active Directory / Group Policy), and backups + disaster recovery.

| # | Topic | Note | Practice project |
|---|---|---|---|
| 1 | What is system administration | [what-is-system-administration.md](<concepts/system administration it infrastructure services/what-is-system-administration.md>) | [it-asset-runbook](practice/system-administration-it-infrastructure-services/it-asset-runbook) |
| 2 | Network and infrastructure services | [network-and-infrastructure-services.md](<concepts/system administration it infrastructure services/network-and-infrastructure-services.md>) | [infra-services-check](practice/system-administration-it-infrastructure-services/infra-services-check) |
| 3 | Software and platform services | [software-and-platform-services.md](<concepts/system administration it infrastructure services/software-and-platform-services.md>) | [service-health-monitor](practice/system-administration-it-infrastructure-services/service-health-monitor) |
| 4 | Directory services | [directory-services.md](<concepts/system administration it infrastructure services/directory-services.md>) | [ad-bulk-provisioning](practice/system-administration-it-infrastructure-services/ad-bulk-provisioning) |
| 5 | Data recovery & backups | [data-recovery-backups.md](<concepts/system administration it infrastructure services/data-recovery-backups.md>) | [backup-and-restore](practice/system-administration-it-infrastructure-services/backup-and-restore) |

## IT security - topics

*(The cryptology note keeps the course's playful title "pelcgbybtl" - that's "cryptology" in ROT13,
which the note explains.)*

Threats first, then the tools (cryptography, the 3 As), then defending networks and hosts in layers,
and finally the people/process side that makes security stick.

| # | Topic | Note | Practice project |
|---|---|---|---|
| 1 | Understanding security threats | [understanding-security-threats.md](<concepts/it security/understanding-security-threats.md>) | [phishing-analyzer](practice/it-security/phishing-analyzer) |
| 2 | Pelcgbybtl (cryptology) | [pelcgbybtl-cryptology.md](<concepts/it security/pelcgbybtl-cryptology.md>) | [crypto-lab](practice/it-security/crypto-lab) |
| 3 | The 3 As of cybersecurity | [the-3-as-of-cybersecurity.md](<concepts/it security/the-3-as-of-cybersecurity.md>) | [auth-lab](practice/it-security/auth-lab) |
| 4 | Securing your networks | [securing-your-networks.md](<concepts/it security/securing-your-networks.md>) | [firewall-rule-auditor](practice/it-security/firewall-rule-auditor) |
| 5 | Defense in depth | [defense-in-depth.md](<concepts/it security/defense-in-depth.md>) | [host-hardening-audit](practice/it-security/host-hardening-audit) |
| 6 | Creating a company culture for security | [company-culture-for-security.md](<concepts/it security/company-culture-for-security.md>) | [security-policy-kit](practice/it-security/security-policy-kit) |

## Learning roadmap

A suggested order for tying the topics together - roughly the order the dependencies make sense in:

1. **How a computer thinks** - [Introduction](<concepts/technical support fundamentals/introduction.md>):
   binary, encoding, and the hardware → OS → software → user layers. Every later topic assumes
   you can read binary and know which layer a problem lives in.
2. **The machine itself** - [Hardware](<concepts/technical support fundamentals/hardware.md>) →
   [Operating system](<concepts/technical support fundamentals/operating-system.md>) →
   [Software](<concepts/technical support fundamentals/software.md>). Build the
   [pc-inventory](practice/technical-support-fundamentals/pc-inventory) project here.
3. **The method** - [Troubleshooting](<concepts/technical support fundamentals/troubleshooting.md>):
   ask, isolate, follow the crumbs, start simple, fix the root cause, document. Re-read it after every
   module; it's the skill all the others plug into.
4. **Networking basics** - [Networking](<concepts/technical support fundamentals/networking.md>)
   gives you the vocabulary; then go deep with the networking module in order:
   [layers & Ethernet](<concepts/computer networking/introduction-to-networking.md>) →
   [IP & subnetting](<concepts/computer networking/the-network-layer.md>) →
   [TCP/UDP & ports](<concepts/computer networking/the-transport-and-application-layers.md>) →
   [DNS/DHCP/NAT](<concepts/computer networking/networking-services.md>) →
   [WAN & Wi-Fi](<concepts/computer networking/connecting-to-the-internet.md>) →
   [troubleshooting & IPv6](<concepts/computer networking/troubleshooting-and-future-of-networking.md>).
   Each layer only makes sense once the one below it does. Practice subnetting until it's fast.
5. **Driving the OS** - [Navigating the system](<concepts/os power user/navigating-the-system.md>)
   first (everything after it uses the shell), then
   [users & permissions](<concepts/os power user/users-and-permissions.md>),
   [packages](<concepts/os power user/packages-and-software-management.md>),
   [file systems](<concepts/os power user/file-systems.md>),
   [processes](<concepts/os power user/process-management.md>), and
   [OS in practice](<concepts/os power user/operating-systems-in-practice.md>) - logs tie them all together.
6. **From one machine to an organization** -
   [What is system administration](<concepts/system administration it infrastructure services/what-is-system-administration.md>) →
   [infrastructure services](<concepts/system administration it infrastructure services/network-and-infrastructure-services.md>)
   (DNS/DHCP from step 4, now run by *you*) →
   [platform services](<concepts/system administration it infrastructure services/software-and-platform-services.md>) →
   [directory services](<concepts/system administration it infrastructure services/directory-services.md>)
   (users & permissions from step 5, at company scale) →
   [backups](<concepts/system administration it infrastructure services/data-recovery-backups.md>).
7. **Know the enemy** - [Understanding security threats](<concepts/it security/understanding-security-threats.md>):
   now that you know how everything works, see how each piece gets attacked.
8. **The building blocks of defense** - [Cryptology](<concepts/it security/pelcgbybtl-cryptology.md>) →
   [the 3 As](<concepts/it security/the-3-as-of-cybersecurity.md>). Hashing, keys, and certificates
   reappear in passwords, TLS, VPNs, Wi-Fi, and Active Directory.
9. **Defense in layers** - [Securing your networks](<concepts/it security/securing-your-networks.md>) →
   [Defense in depth](<concepts/it security/defense-in-depth.md>): the network ring, then the host ring.
10. **Making it last** - [Company culture for security](<concepts/it security/company-culture-for-security.md>):
    risk, policy, training, and incident response. This closes the loop with step 3, since incident
    response is troubleshooting under pressure, with documentation and post-mortems.

## Best practices for learning IT support fundamentals

- **Always ask "which layer is this?"** User, software, OS, hardware - or physical, data link,
  network, transport, application. Naming the layer is half of diagnosing the problem, and it's the
  thread running through every module.
- **Build a home lab you're allowed to break.** VirtualBox/Hyper-V with one Windows and one Ubuntu VM
  (snapshots!) covers almost every practice project - users, permissions, packages, services, logs,
  even a domain controller. Most of the "Try this yourself" sections assume one.
- **Learn both shells.** PowerShell and Bash solve the same problems differently (objects vs text).
  Most jobs need both; the [shell-navigation-lab](practice/os-power-user/shell-navigation-lab) drills them side by side.
- **Look at real data, not just diagrams.** `ipconfig /all`, `nslookup`, `tracert`, Event Viewer,
  Wireshark, `Get-Process`. The tools show what's actually happening, often more precisely than a slide.
- **Break things on purpose, then fix them.** Set a wrong DNS server, fill a DHCP scope, stop a
  service, expire a certificate - and watch which check fails. You'll recognize the symptom instantly
  when a user reports it.
- **Write it down as you go.** Tickets, KB articles, runbooks, post-mortems - documentation is a
  core part of the job, not paperwork after it. The templates in
  [helpdesk-troubleshooting](practice/technical-support-fundamentals/helpdesk-troubleshooting) and
  [it-asset-runbook](practice/system-administration-it-infrastructure-services/it-asset-runbook) are a
  good start.
- **Dry run first, least privilege always.** Every script here that changes things defaults to a dry
  run, and every permission example grants to groups, not people. Make both habits automatic.
- **Security is everyone's layer.** Phishing, weak passwords, and unpatched machines cause most
  incidents. A support person who verifies identity before resets and reports oddities quickly is a
  big part of the defense.
- **Write the note after building the project.** The write-up gets sharper once you've hit the
  edge case in code - e.g. you don't really understand DHCP exhaustion until you've watched a client
  fall back to `169.254.x.x`.

## Practice projects

Every project uses the **Python 3.10+ standard library only** - no `pip install` - plus
**PowerShell** (Windows) and **Bash** (Linux / Git Bash) where the topic is OS administration.
Run any project from its own folder:

```bash
cd practice/<module-name>/<project>
python <script>.py --help      # or open the project's README.md first
```

Things to know before running them:

- **Safe by default.** Scripts that could change a system (`Onboard-Users.ps1`, `onboard_users.sh`,
  `Install-Workstation.ps1`, `install_workstation.sh`) only print what they'd do unless you pass
  `-Apply` / `--apply`. Run the apply mode **in a VM**. Audits (`Audit-Host.ps1`, `perm_tool.py audit`,
  `disk_report.py`) are read-only.
- **Some projects talk to the real network.** `dns_query.py`, `sntp_client.py`, `net_doctor.py`,
  `health_check.py`, and `port_check.py` send real traffic (DNS to 8.8.8.8, NTP to pool.ntp.org, TLS to
  public sites). Corporate or guest networks may block some of it (e.g. UDP 123, TCP 53, mail ports);
  the READMEs explain what a blocked result looks like. Only port-check hosts you own or may test.
- **Some need two terminals** - `socket-lab` (server + client) and `service-health-monitor` (lab web
  server + monitor). Each README shows the exact commands.
- **Simulations where the real thing isn't safe to run locally**: `dhcp_dora_sim.py` (a real DHCP
  server would fight your router), `nat_table_sim.py`, and `gpo_sim.py` (needs an AD domain) model the
  real logic without touching the network.
- **Generated output stays out of git.** Several scripts write reports containing real details about
  your machine (serial numbers, IP/MAC addresses, installed software, security posture). Those paths
  are in [.gitignore](.gitignore).
- **Sample data is fictional.** Users, companies, emails, and logs use reserved `example` domains and
  documentation IP ranges (`192.0.2.0/24`, `198.51.100.0/24`, `203.0.113.0/24`).

Each project's `README.md` explains: what it demonstrates, the scenario, the folder structure, a
walkthrough of the key code with the concept called out inline, how to run it with expected output,
"try this yourself" extensions, and the real-world tools it stands in for.
