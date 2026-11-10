# Operating Systems in Practice: Remote Access, VMs, Logs & Deployment

Day-to-day OS work in a real IT environment: connecting to machines you can't touch, running
virtual machines, reading logs to find out what went wrong, and installing an OS on many
computers at once.

## Remote access

### SSH (Secure Shell)

Encrypted remote command-line access - the standard way to manage Linux servers (and available on
Windows too). Uses **TCP port 22**.

```bash
ssh amina@server01.company.local
ssh -p 2222 amina@203.0.113.10        # non-default port
scp report.pdf amina@server01:/tmp/   # copy a file over SSH
```

**Authentication methods**:

- **Password** - simple, but can be brute-forced.
- **SSH keys** (recommended) - a **key pair**: the **private key** stays on your computer, the
  **public key** goes on the server in `~/.ssh/authorized_keys`.

```bash
ssh-keygen -t ed25519 -C "amina@laptop"   # create a key pair (~/.ssh/id_ed25519 + .pub)
ssh-copy-id amina@server01                # install the public key on the server
```

Windows: OpenSSH client is built in (`ssh` in PowerShell); **PuTTY** is the classic GUI client
(and `pscp` for file copies).

### RDP (Remote Desktop Protocol)

Microsoft's protocol for full **graphical** remote desktop. **TCP/UDP 3389**.

```powershell
mstsc /v:pc-042.company.local
```

- Never expose RDP directly to the internet - a top target for attacks. Put it behind a VPN or
  an RD Gateway, and use MFA.
- For helping users, organizations often use remote-support tools (Quick Assist, TeamViewer,
  etc.) where **the user approves** the session.

> 🖼️ **Image idea: SSH key authentication** - client holding the private key, server with the
> public key in `authorized_keys`, and the challenge/response arrows between them.
> Suggested file: `assets/img/ssh-key-auth.png`
<!-- ![ssh key auth](<../../assets/img/ssh-key-auth.png>) -->

## Virtualization

A **virtual machine** runs a complete OS on virtual hardware provided by a **hypervisor**.

| Type | Runs on | Examples | Used for |
|---|---|---|---|
| Type 1 (bare-metal) | directly on hardware | VMware ESXi, Hyper-V Server, Proxmox, KVM | servers, data centers |
| Type 2 (hosted) | on top of a normal OS | VirtualBox, VMware Workstation, Hyper-V on Windows 11 Pro | testing, training, labs |

Key features:

- **Snapshots** - save the VM's exact state; roll back after a failed experiment.
- **Templates / cloning** - build once, copy many times.
- **Isolation** - a broken or infected VM doesn't affect the host (mostly).
- **Resource allocation** - give each VM a set amount of CPU, RAM, and disk.

**Containers** (Docker) are lighter: they share the host's kernel and isolate only the
application and its dependencies. VMs virtualize hardware; containers virtualize the OS.

## Logs

**Logs** are the system's diary - the first place to look when something went wrong and you don't
know why.

### Windows: Event Viewer (`eventvwr.msc`)

| Log | Contains |
|---|---|
| **Application** | events from apps (crashes, errors from Office, SQL, etc.) |
| **System** | Windows components and drivers (service failures, disk errors, unexpected shutdowns) |
| **Security** | logons, failed logons, permission changes (audit events) |
| Setup | update/installation events |
| Applications and Services Logs | per-feature logs (PowerShell, Windows Defender, ...) |

Levels: **Information**, **Warning**, **Error**, **Critical**. Every event has a **source** and
**Event ID** - search those two together online.

Useful Event IDs:

| ID | Log | Meaning |
|---|---|---|
| 41 | System | Kernel-Power: rebooted without clean shutdown (crash/power loss) |
| 6005 / 6006 | System | Event log started / stopped (≈ boot / clean shutdown) |
| 1074 | System | who/what initiated a shutdown or restart |
| 4624 / 4625 | Security | successful / **failed** logon |
| 4740 | Security | account locked out |

```powershell
Get-WinEvent -LogName System -MaxEvents 20
Get-WinEvent -FilterHashtable @{LogName='System'; Level=2; StartTime=(Get-Date).AddDays(-1)}  # errors, last 24h
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4625} -MaxEvents 10                     # failed logons (needs admin)
```

Use **Custom Views** / filters in Event Viewer - there are thousands of events; searching beats
scrolling.

### Linux

- Traditional text logs in **`/var/log/`**:

  | File | Contains |
  |---|---|
  | `/var/log/syslog` (Debian/Ubuntu) or `/var/log/messages` (Red Hat) | general system messages |
  | `/var/log/auth.log` / `/var/log/secure` | logins, sudo, SSH |
  | `/var/log/kern.log` | kernel messages |
  | `/var/log/nginx/`, `/var/log/apache2/` | app-specific logs |

- **systemd journal** - binary log, queried with `journalctl`:

```bash
journalctl -xe                       # recent entries with explanations
journalctl -u nginx --since today    # one service
journalctl -p err -b                 # errors since last boot
tail -f /var/log/syslog              # follow live
grep "Failed password" /var/log/auth.log | tail
```

- **Log rotation** (`logrotate`) compresses and deletes old logs so they don't fill the disk.

### Reading a log line

```
Mar  4 10:15:32 web01 sshd[2211]: Failed password for invalid user admin from 198.51.100.7 port 51234 ssh2
└── timestamp ─┘ └host┘└ process[PID]┘ └──────────────────────── message ─────────────────────────┘
```

**Method**: note the time the user saw the problem → look at logs around that time → find the
first error (later errors are often consequences of the first).

## OS deployment

Installing an OS by hand on 200 laptops doesn't scale.

- **Disk imaging / cloning** - configure one "golden image," capture it, deploy it to many
  machines. Tools: Clonezilla, Windows Deployment Services (WDS), Microsoft Deployment Toolkit
  (MDT), Configuration Manager; in the cloud era, **Windows Autopilot + Intune** (the laptop
  configures itself from the internet on first boot).
- On Linux, raw copies can be made with `dd` (careful - it overwrites without asking):

  ```bash
  sudo dd if=/dev/sda of=/mnt/backup/sda.img bs=4M status=progress
  ```

- **PXE boot** - computers boot from the network to pull an image from a deployment server.
- Windows images must be **generalized** with **Sysprep** before capture (removes unique IDs).

## Mobile devices in practice

- **MDM** (Mobile Device Management - Intune, Jamf, etc.) enforces passcodes, encryption, app
  deployment, and can **remote wipe** a lost phone.
- Troubleshooting order: restart → update OS/app → check storage → reset network settings →
  **back up**, then factory reset as last resort.

## Practice project

[`practice/os-power-user/process-and-log-monitor`](<../../practice/os-power-user/process-and-log-monitor>) -
`log_analyzer.py` parses Linux auth logs (sample included) and Windows Event Log CSV exports,
counts errors by source, detects brute-force SSH attempts by IP, and builds a timeline - the
"find the first error" method, automated.

## Related

- [Process management](<process-management.md>) - services whose failures show up in logs.
- [Understanding security threats](<../it security/understanding-security-threats.md>) - what attacks look like in logs.
- [What is system administration](<../system administration it infrastructure services/what-is-system-administration.md>) - managing fleets of machines.
