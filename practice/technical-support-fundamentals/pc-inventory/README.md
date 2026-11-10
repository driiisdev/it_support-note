# Practice: PC Inventory (Hardware, Operating System, Software)

Concept notes:
[`hardware.md`](<../../../concepts/technical support fundamentals/hardware.md>) ·
[`operating-system.md`](<../../../concepts/technical support fundamentals/operating-system.md>) ·
[`software.md`](<../../../concepts/technical support fundamentals/software.md>)

## What this demonstrates

How an IT team knows **what it actually owns**: each machine reports its hardware (CPU, RAM,
disks), OS (version, architecture, uptime), and installed software, and a fleet report combines
them and flags machines that need attention. This is a tiny version of what Intune, SCCM, Lansweeper,
or any RMM tool does.

It also shows that "hardware," "OS," and "software" aren't just chapters in a course - they're
the three things every inventory asks about.

## Scenario

Your company has ~40 laptops and nobody knows which ones are low on RAM, almost out of disk, or
haven't rebooted for updates in weeks. Before buying upgrades, your manager asks for a report.

## Folder structure

```
pc-inventory/
  inventory.py        <- cross-platform: hardware + OS summary of THIS machine -> reports/<host>.json
  Get-Inventory.ps1   <- Windows deep dive: model, serial number, SSD/HDD, BIOS, installed software
  fleet_report.py     <- merges many JSON reports into fleet.csv + health summary
  sample-fleet/       <- 3 fictional machines so the fleet report has something to show
  reports/            <- created when you run the scripts (gitignored - contains real machine data)
```

## Code walkthrough

**Every OS exposes hardware info differently**, so `inventory.py` branches per OS - a very
real problem in cross-platform IT tooling:

```python
if system == "Windows":   # Win32 API via ctypes
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
if system == "Linux":     # the kernel exposes it as a text file
    open("/proc/meminfo")
if system == "Darwin":    # macOS
    subprocess.check_output(["sysctl", "-n", "hw.memsize"])
```

**Health rules** turn raw data into help desk action items:

```python
if inv["ram_gb"] < 8:                -> "expect slowness"
if disk["used_pct"] >= 90:           -> "disk almost full"
if inv["uptime_hours"] > 24 * 14:    -> "pending updates need a reboot"
```

**`Get-Inventory.ps1`** uses the same sources enterprise tools use:

| Data | Source |
|---|---|
| Manufacturer, model, RAM | `Win32_ComputerSystem` |
| Serial number (for warranty) | `Win32_BIOS` |
| SSD vs HDD, bus type, health | `Get-PhysicalDisk` |
| Installed software | registry `...\CurrentVersion\Uninstall\*` (64-bit, 32-bit `WOW6432Node`, and per-user `HKCU`) |

The three Uninstall keys are worth remembering: forgetting `WOW6432Node` is the classic reason a
software audit "misses" 32-bit apps.

## Run it

```bash
python inventory.py               # summary + reports/<hostname>.json
python fleet_report.py            # combines reports/ + sample-fleet/ -> fleet.csv
```

```powershell
# Windows only - read-only, no admin needed for most fields
powershell -ExecutionPolicy Bypass -File .\Get-Inventory.ps1
```

Expected output (`fleet_report.py`):

```
HOST          USER      OS               RAM  DISK%   UP(h)  WARNINGS
ACC-LT-014    m.okafor  Windows 11       7.8   95.3   501.6  3
                - Only 7.8 GB RAM - expect slowness with modern browsers/Office.
                - Disk C:\ is 95.3% full (11.2 GB free).
                - Up for 21 days - pending updates need a reboot.
...
```

## Try this yourself

- Open `reports/<host>-software.csv` in Excel and find every app from one publisher, or anything
  that looks unapproved.
- Add a rule: warn if the OS is **Windows 10** (end of support) or if `architecture` is 32-bit.
- Add **battery health** for laptops: `powercfg /batteryreport` produces an HTML report with
  design vs full-charge capacity - parse those two numbers.
- Make `inventory.py` also record the **BIOS serial number** on Linux
  (`/sys/class/dmi/id/product_serial`, needs root).
- Run `inventory.py` in a Linux VM and compare what's easy vs hard to get on each OS.
- Schedule it: Windows Task Scheduler (at logon) writing to a shared folder; then run
  `fleet_report.py` against that folder.

## Real-world equivalent

- **Asset management / CMDB** - Lansweeper, Snipe-IT, ServiceNow discovery.
- **Endpoint management** - Microsoft Intune hardware inventory, SCCM hardware inventory, RMM tools
  (NinjaOne, Datto) - all collect exactly these fields.
- **Warranty claims** - vendors (Dell, Lenovo, HP) ask for the serial number / service tag that
  `Win32_BIOS` returns.
