# Packages & Software Management

Installing, updating, and removing software reliably across many machines - plus drivers and OS
updates, which are just special kinds of software.

## Software packages

A **package** is an archive containing a program's files **plus metadata**: name, version,
description, and **dependencies** (other packages it needs). A **package manager** reads that
metadata to install everything in the right place, in the right order, and to cleanly remove it.

### Windows

| Format / tool | What it is |
|---|---|
| `.exe` installer | a program that installs a program - behavior varies by vendor; silent-install flags differ (`/S`, `/quiet`, `/silent`) |
| `.msi` | Windows Installer package - standardized, supports silent installs and rollback. Great for mass deployment. |
| `.msix` / `.appx` | modern, sandboxed app packages (Microsoft Store) |
| **winget** | built-in command-line package manager |
| **Chocolatey** | popular third-party package manager |
| **NuGet** | package manager for .NET libraries (and PowerShell modules via PowerShellGet) |

```powershell
winget search 7zip
winget install --id 7zip.7zip -e --silent
winget list                         # installed software (incl. non-winget)
winget upgrade --all
winget uninstall --id 7zip.7zip
winget export -o apps.json          # snapshot of installed apps -> re-import on a new PC
winget import -i apps.json

msiexec /i app.msi /qn /l*v install.log    # silent MSI install with verbose log
```

### Linux

| Family | Package format | Low-level tool | High-level tool (resolves dependencies) |
|---|---|---|---|
| Debian, Ubuntu | `.deb` | `dpkg` | `apt` |
| Red Hat, Fedora, Rocky | `.rpm` | `rpm` | `dnf` (formerly `yum`) |

```bash
sudo apt update                    # refresh the package list from repositories
apt search nginx
sudo apt install nginx
apt show nginx                     # version, dependencies, description
dpkg -l | grep nginx               # is it installed?
sudo apt upgrade                   # upgrade installed packages
sudo apt remove nginx              # remove (keep config)
sudo apt purge nginx               # remove + config
sudo apt autoremove                # remove dependencies nothing needs anymore

sudo dpkg -i package.deb           # install a downloaded .deb (no dependency resolution!)
sudo apt install ./package.deb     # same, but resolves dependencies
```

**Repositories** - servers hosting packages, listed in `/etc/apt/sources.list` and
`/etc/apt/sources.list.d/`. Adding a third-party repository = trusting that vendor with root on
your machine (packages run install scripts as root) - only add trusted ones.

### macOS

`.dmg` disk images, `.pkg` installers, App Store, and **Homebrew** (`brew install wget`).

## Archives

Not packages (no install logic), just compressed bundles of files:

| Format | Tool |
|---|---|
| `.zip` | Windows built-in, `Compress-Archive` / `Expand-Archive`, `unzip` |
| `.tar`, `.tar.gz` (`.tgz`) | `tar -czf out.tar.gz folder/`, `tar -xzf file.tar.gz` (also built into modern Windows) |
| `.7z` | 7-Zip - high compression |

## Dependencies

- **Windows**: programs depend on **DLLs** (Dynamic Link Libraries) and runtimes (Visual C++
  Redistributable, .NET). "VCRUNTIME140.dll is missing" = install the right Visual C++ runtime.
  Windows keeps multiple versions side by side in the **WinSxS** folder.
- **Linux**: **shared libraries** (`.so` files). Package managers resolve these automatically;
  `ldd /usr/bin/program` lists what a binary needs.
- **Dependency hell** - two programs needing incompatible versions of the same library. Package
  managers, side-by-side assemblies, and containers exist largely to avoid it.

## Device drivers

A **driver** lets the OS talk to a specific piece of hardware.

### Windows

- **Device Manager** (`devmgmt.msc`) - lists all hardware; a **yellow triangle** = missing or
  broken driver. Right-click → Update / Roll back / Uninstall driver.
- Drivers come via Windows Update, the manufacturer's website, or OEM tools (Dell Command Update,
  Lenovo Vantage, HP Support Assistant).
- **Roll back driver** is the fix when "it broke right after the update."

```powershell
Get-PnpDevice -Status ERROR          # devices with problems
pnputil /enum-drivers                # third-party drivers installed
```

### Linux

- Most drivers are **kernel modules** shipped with the kernel.
- Devices appear as files under **`/dev`** (`/dev/sda` = first disk). **udev** creates these
  entries dynamically when hardware is plugged in.

```bash
lspci -k            # PCI devices and the driver ("Kernel driver in use") for each
lsusb               # USB devices
lsmod               # loaded kernel modules
sudo modprobe <mod> # load a module
dmesg | tail        # kernel messages - shows what happened when you plugged something in
```

> 🖼️ **Image idea: Device Manager with a yellow-warning device** - screenshot showing the
> triangle icon and the Driver tab (Update / Roll Back / Uninstall).
> Suggested file: `assets/img/device-manager-warning.png`
<!-- ![device manager warning](<../../assets/img/device-manager-warning.png>) -->

## Operating system updates

Updates fix **security vulnerabilities** (most important), bugs, and add features. Unpatched
systems are one of the top causes of security incidents.

### Windows

- **Windows Update** (Settings → Windows Update). Monthly security updates arrive on
  **Patch Tuesday** (2nd Tuesday of each month).
- Organizations control rollout with **WSUS**, **Intune / Windows Update for Business**, or
  **Configuration Manager**: test group first, then everyone.
- Updates are **cumulative** - the latest one includes all previous fixes.

### Linux

```bash
sudo apt update && sudo apt upgrade     # packages, including kernel packages
uname -r                                # current running kernel version
# a new kernel only takes effect after reboot
```

## How it's used in real IT support

- Setting up a new laptop: one script that installs the standard app list (winget/Chocolatey).
- "App X won't install" → read the installer log (`/l*v` for MSI), check for a missing runtime,
  check disk space, check admin rights.
- "Printer stopped working after update" → Device Manager → roll back driver.
- Patch compliance reports: which machines are missing which updates.

## Practice project

[`practice/os-power-user/software-deployment`](<../../practice/os-power-user/software-deployment>) -
a "standard workstation build" defined in one manifest file (`apps.json`) with an installer
script for Windows (winget) and Linux (apt), both supporting dry-run, idempotency (skip already
installed), and a log file - the way small IT teams automate new-PC setup.

## Related

- [Software](<../technical support fundamentals/software.md>) - software basics and versioning.
- [Users and permissions](<users-and-permissions.md>) - why installs need admin/sudo.
- [Defense in depth](<../it security/defense-in-depth.md>) - patch management as a security control.
