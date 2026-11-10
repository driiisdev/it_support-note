# Practice: Host Hardening Audit (Defense in Depth)

Concept note:
[`defense-in-depth.md`](<../../../concepts/it security/defense-in-depth.md>)

## What this demonstrates

The defense-in-depth checklist as a **read-only** audit you can run on any machine, scored per
layer so you can see which ring of the "onion" is weakest:

| Layer | Windows checks (`Audit-Host.ps1`) | Linux checks (`audit_host.sh`) |
|---|---|---|
| firewall | each profile enabled, default inbound Block | ufw / firewalld active |
| antimalware | Defender real-time on, signature age | (n/a - add ClamAV/EDR if used) |
| patching | days since last update, uptime / pending reboot | pending (security) updates, unattended-upgrades, reboot-required |
| encryption | BitLocker on the system drive | LUKS volume present |
| accounts | local admins count, built-in Administrator & Guest disabled, UAC on | only root has UID 0, sudo members, empty passwords |
| surface | SMBv1, RDP (+NLA), AutoRun, ports listening on all interfaces | SSH root login / password auth, listening ports, world-writable files in /etc |

Every check reports **PASS / WARN / FAIL / UNKNOWN** with the fix, and **nothing is changed**.

## Scenario

Before a security review, your manager asks: "How hardened are our PCs, really?" You run the audit
on a few machines (including the reception PC nobody has touched in months) and present a scored
report with specific fixes.

## Folder structure

```
host-hardening-audit/
  Audit-Host.ps1        <- Windows audit -> results/<COMPUTERNAME>.json
  audit_host.sh         <- Linux audit   -> results/<hostname>.json
  report.py             <- scores one or many results files, per layer, worst machines first
  sample-results.json   <- a fictional, poorly hardened "RECEPTION-PC" to practice reading a report
  results/              <- created on run (gitignored - describes your real machine)
```

## Code walkthrough

**Same output format on both OSes**, so one report tool handles a mixed fleet:

```json
{"layer": "surface", "check": "SMBv1 server", "status": "FAIL", "detail": "ENABLED",
 "fix": "Set-SmbServerConfiguration -EnableSMB1Protocol $false"}
```

**Graceful without admin rights**: checks that need elevation (BitLocker, SMB config) report
`UNKNOWN` instead of failing, and the report says "re-run elevated." UNKNOWN doesn't count toward
the score, so a non-admin run isn't punished or flattered.

**Details that avoid false alarms:**

- Firewall `DefaultInboundAction = NotConfigured` means *not set by policy* → Windows' default
  (**Block**) applies, so it's a PASS.
- "Listening on all interfaces" only counts `0.0.0.0` / `::` listeners - services bound to
  `127.0.0.1` aren't reachable from the network.
- The built-in Administrator and Guest accounts are found by **SID** (`-500`, `-501`), not by name,
  because they're often renamed.

**Scoring**: PASS = 1, WARN = 0.5, FAIL = 0, averaged per layer and overall.

## Run it

```powershell
powershell -ExecutionPolicy Bypass -File .\Audit-Host.ps1          # normal (some UNKNOWN)
# elevated PowerShell for the complete picture:
.\Audit-Host.ps1
python report.py results\*.json
python report.py sample-results.json
```

```bash
bash audit_host.sh            # Linux VM; with sudo access for the shadow/ufw checks
python3 report.py results/*.json
```

Expected (`sample-results.json`):

```
RECEPTION-PC - Microsoft Windows 10 Pro
  firewall      67%
      [FAIL   ] Public profile: disabled  -> Set-NetFirewallProfile -Name Public -Enabled True
  patching      25%
      [FAIL   ] Last update installed: KB5021233 on 2025-11-12 (112 days ago)  -> Run Windows Update
  encryption     0%
      [FAIL   ] BitLocker C:: protection Off  -> Enable BitLocker and escrow the recovery key
  surface       25%
      [FAIL   ] SMBv1 server: ENABLED ...
  SCORE 50/100 (grade D) from 16 checks
```

> Tested note: `Audit-Host.ps1` was run on a real Windows 11 machine (non-elevated). `audit_host.sh`
> passed a syntax check but needs a Linux machine/VM to run.

## Try this yourself

- Run it non-elevated, then elevated - compare which checks move from UNKNOWN to PASS/FAIL.
- In a **Windows VM snapshot**, deliberately weaken settings (disable the Public firewall profile,
  enable the Guest account, enable SMBv1 via *Windows Features*), re-run, then fix each finding using
  the suggested command and confirm it turns green. Revert the snapshot after.
- Add checks: **screen lock timeout**, **PowerShell script block logging**, **LSA protection**,
  **Secure Boot** (`Confirm-SecureBootUEFI`), **password policy** (`net accounts`).
- Map each check to a **CIS Benchmark** control ID in the `check` name - that's how real audit reports
  are written.
- Run `audit_host.sh` on an Ubuntu VM before and after `sudo ufw enable` and
  `sudo apt install unattended-upgrades`.

## Real-world equivalent

- **CIS-CAT**, **Microsoft Secure Score / Defender Vulnerability Management**, **Lynis** (Linux),
  **OpenSCAP** - automated hardening audits against benchmarks.
- Intune / Group Policy **security baselines** then *enforce* the settings this script only checks.
