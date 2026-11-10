# Practice: Software Deployment (Packages and Software Management)

Concept note:
[`packages-and-software-management.md`](<../../../concepts/os power user/packages-and-software-management.md>)

## What this demonstrates

Package managers as an IT tool: one **manifest** (`apps.json`) defines the standard workstation,
and an installer script per OS makes any machine match it.

Real deployment tools share these properties:

- **Declarative** - you describe the desired state (these apps), not the clicks.
- **Idempotent** - running it twice is safe; already-installed apps are skipped.
- **Dry run first** - see what would change before changing it.
- **Logged** - transcript + summary CSV = evidence for the ticket and for compliance.
- **Compliance** - "are all *required* apps present?" is a yes/no answer per machine.

## Scenario

New laptops arrive every week and each takes an hour of clicking through installers. Your lead
asks you to automate the standard build so any tech gets the same result in minutes - and to
report which existing machines are missing required software.

## Folder structure

```
software-deployment/
  apps.json                <- the standard build: name, winget ID, apt package, required?
  Install-Workstation.ps1  <- Windows (winget): dry run | -Apply | -RequiredOnly
  install_workstation.sh   <- Debian/Ubuntu (apt): dry run | --apply | --required-only
  logs/                    <- transcripts + summary CSVs (created on run, gitignored)
```

## Code walkthrough

**One manifest, two package managers** - each app has both IDs; `null` means "not on this OS":

```json
{"name": "7-Zip", "winget": "7zip.7zip", "apt": "p7zip-full", "required": true}
```

**Idempotency** comes from checking before installing:

```powershell
winget list --id $app.winget -e *> $null      # exit code 0 = installed
```

```bash
dpkg-query -W -f='${Status}' "$pkg" | grep -q "install ok installed"
```

**Silent installs** - no prompts, so it can run unattended:

```powershell
winget install --id $id -e --silent --accept-package-agreements --accept-source-agreements
```

```bash
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "$pkg"
```

**Logging**: PowerShell's `Start-Transcript` records everything; the Bash script uses
`exec > >(tee -a "$LOG") 2>&1` to send all output to the screen and a log file at once.

## Run it

```powershell
powershell -ExecutionPolicy Bypass -File .\Install-Workstation.ps1               # dry run
powershell -ExecutionPolicy Bypass -File .\Install-Workstation.ps1 -RequiredOnly
powershell -ExecutionPolicy Bypass -File .\Install-Workstation.ps1 -Apply        # install missing
```

```bash
./install_workstation.sh                     # Ubuntu VM
sudo ./install_workstation.sh --apply
```

Expected (dry run):

```
Build: Standard Office Workstation v2026.03 on DRIIISDEV  [DRY-RUN]

  7-Zip            7zip.7zip                        WOULD INSTALL
  VLC              VideoLAN.VLC                     already installed
  ...
NOT COMPLIANT - required apps missing/failed: 7-Zip, Google Chrome, Adobe Reader
```

> Tested note: the Windows dry run was run against a real machine's winget inventory; `-Apply` and
> the Linux script's `--apply` install software, so try them in a VM.

## Try this yourself

- Run `-Apply` in a fresh Windows VM, then run it again - the second run should install nothing
  (idempotency).
- `winget export -o my-apps.json` on your own PC, then turn it into an `apps.json` for "my perfect
  machine."
- Add a `"version"` field and make the script **pin** versions (`winget install --version`) - why do
  companies sometimes pin instead of always taking latest?
- Add an **uninstall list** (apps that must *not* be present, e.g. unapproved remote-access tools)
  and report them as non-compliant.
- Add an MSI-only app (not in winget): download it, verify its SHA-256 hash, and install with
  `msiexec /i app.msi /qn /l*v install.log`.
- Run `python ../../technical-support-fundamentals/pc-inventory/inventory.py` before and after, and
  compare.

## Real-world equivalent

- **Intune** (Win32 apps / winget integration), **Configuration Manager**, **PDQ Deploy**,
  **Chocolatey for Business**, and on Linux **Ansible** (`apt: name=... state=present` is exactly
  this idea).
- **Windows Autopilot** + Intune runs a "required apps" list like this automatically when a new
  laptop is first signed in.
