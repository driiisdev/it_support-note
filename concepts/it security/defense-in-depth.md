# Defense in Depth

No single control is perfect. **Defense in depth** means layering many independent defenses so
that when one fails (and one always does), the next one still stops or slows the attacker - and
logging makes sure you notice.

```
 +-----------------------------------------------------------+
 | Policies, training, physical security                     |
 |  +-----------------------------------------------------+  |
 |  | Network: firewall, segmentation, IDS/IPS, VPN        | |
 |  |  +-----------------------------------------------+   | |
 |  |  | Host: hardening, host firewall, antimalware,  |   | |
 |  |  |       patching, allow-listing, disk encryption|   | |
 |  |  |  +-----------------------------------------+  |   | |
 |  |  |  | Application: least privilege, input val. |  |  | |
 |  |  |  |  +-----------------------------------+  |  |   | |
 |  |  |  |  |  DATA: encryption, backups, ACLs  |  |  |   | |
 |  |  |  |  +-----------------------------------+  |  |   | |
 |  |  |  +-----------------------------------------+  |   | |
 |  |  +-----------------------------------------------+   | |
 |  +-----------------------------------------------------+  |
 +-----------------------------------------------------------+
```

> 🖼️ **Image idea: defense in depth "onion"** - concentric rings like the ASCII above, an arrow
> representing an attack being stopped at different layers.
> Suggested file: `assets/img/defense-in-depth.png`
<!-- ![defense in depth](<../../assets/img/defense-in-depth.png>) -->

## Disabling unnecessary components

- **Attack vector** - a path an attacker can use to get in (an open port, an email attachment, a
  USB port).
- **Attack surface** - the sum of all attack vectors.
- Every service, open port, installed app, and enabled feature adds attack surface. If it's not
  needed, **disable or remove it**: old protocols (SMBv1, Telnet), unused services, browser
  plugins, default accounts, unused admin tools.

## Host-based firewalls

A firewall on each machine, in addition to the network firewall:

- Protects the host even on **untrusted networks** (café Wi-Fi) and from **other internal hosts**
  (stops malware spreading laterally).
- Windows Defender Firewall (profiles: Domain, Private, Public), `ufw`/`firewalld` on Linux,
  macOS Application Firewall.
- Users shouldn't be able to disable it - enforce via Group Policy/MDM.

## Logging and auditing

- Collect logs from every system into a **central** location (**SIEM**) - an attacker on a host
  can delete local logs.
- **Normalization** - converting different log formats into a common one so events can be
  correlated.
- Decide **what to log** (logons, privilege use, policy changes, process creation), **retention**
  (how long - often driven by regulation), and **alerting** (failed logon spikes, new admin
  accounts, disabled antivirus).
- Synchronized clocks (NTP) are essential for building a timeline.

## Antimalware

| Approach | How | Weakness |
|---|---|---|
| **Signature-based** | matches files against a database of known malware fingerprints | misses new/modified malware |
| **Heuristic / behavior-based** | flags suspicious behavior (encrypting many files, injecting into other processes) | more false positives |
| **EDR** (Endpoint Detection & Response) | records endpoint activity, detects attack chains, allows remote isolation | cost, needs people to respond |

Keep definitions updated; antimalware itself is software with an attack surface - it must be
patched too. Microsoft Defender is built into Windows and is a solid baseline.

## Allow-listing (whitelisting)

Instead of blocking known bad software, **only allow known good software** to run.

- Windows: **AppLocker**, **Windows Defender Application Control (WDAC)**.
- Rules by publisher (code-signing certificate), path, or file hash.
- Very effective against malware and unapproved software; requires maintenance as software
  changes.

## Disk encryption

**Full-disk encryption (FDE)** protects data at rest: if a laptop is lost or stolen, the disk is
unreadable without the key.

| OS | Tool |
|---|---|
| Windows | **BitLocker** (uses the **TPM** chip; optional PIN) |
| macOS | **FileVault** |
| Linux | **LUKS** (dm-crypt) |

- **Key escrow** - store recovery keys centrally (Active Directory, Entra ID/Intune, MDM) so IT can
  unlock a machine when the user forgets their PIN or the TPM detects a hardware change.
  *No escrowed key + lost PIN = data is gone.*
- FDE does **not** protect a running, unlocked machine (malware sees decrypted files).

```powershell
manage-bde -status                      # BitLocker status per volume
Get-BitLockerVolume
```

## Software patch management

- Most successful attacks use **known** vulnerabilities that already have patches.
- Patch **OS, applications, browsers, firmware**, and network devices.
- Process: inventory → assess (severity, exploited in the wild?) → test → deploy in rings →
  verify compliance → handle exceptions.
- Prioritize internet-facing systems and actively exploited vulnerabilities.

## Application policies

- Define which software is allowed (and which is banned - e.g. P2P file sharing, unapproved remote
  tools).
- Users run as **standard users**, not admins - most malware needs admin rights to dig in.
- Keep browser extensions under control; disable Office **macros** from the internet.
- Only download software from trusted sources; verify signatures/hashes.

## Putting it together - a hardening checklist (Windows example)

| Layer | Check |
|---|---|
| Firewall | enabled on all profiles, default inbound = block |
| Antimalware | Defender real-time protection on, definitions current |
| Patching | no updates pending > 30 days |
| Encryption | BitLocker on the OS drive, recovery key escrowed |
| Accounts | built-in Administrator disabled; few members in local Administrators; guest disabled |
| Attack surface | SMBv1 disabled, RDP off unless needed, AutoRun disabled |
| Logging | audit policy for logon events, logs forwarded |

## Practice project

[`practice/it-security/host-hardening-audit`](<../../practice/it-security/host-hardening-audit>) -
a **read-only** audit script for Windows (PowerShell) and Linux (Bash) that checks firewall,
antimalware, pending updates, disk encryption, local admins, SMBv1/RDP/SSH settings and outputs a
PASS/WARN/FAIL report - the checklist above, automated. A Python report tool turns the results
into a score.

## Related

- [Securing your networks](<securing-your-networks.md>) - the network layer of the onion.
- [Packages and software management](<../os power user/packages-and-software-management.md>) - patching mechanics.
- [Company culture for security](<company-culture-for-security.md>) - the people/policy outer layer.
