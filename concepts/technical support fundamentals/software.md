# Software

**Software** is the set of instructions that tells hardware what to do. A big chunk of IT support
tickets are software tickets: "install this," "update that," "it crashed," "it says I don't have
a license."

## Types of software

| Type | What it is | Examples |
|---|---|---|
| Application software | programs users run to get work done | browser, Office, Slack, Zoom |
| System software | software that runs and maintains the computer | OS, drivers, system utilities |
| Firmware | software stored on hardware chips, rarely changed | BIOS/UEFI, router firmware, SSD firmware |

> **Driver** - a special piece of system software that lets the OS talk to a specific hardware
> device (printer, graphics card, Wi-Fi card). Wrong or outdated driver = device doesn't work,
> works badly, or crashes the system.

## How software is made

1. A developer writes **source code** in a programming language (C, Python, Java, ...).
2. The code is either:
   - **Compiled** - translated ahead of time into machine code the CPU runs directly
     (C, C++, Go, Rust → `.exe` on Windows). Fast, but built for one OS/CPU type.
   - **Interpreted** - read and executed line by line by an interpreter at run time
     (Python, PowerShell, Bash, JavaScript). Portable, slightly slower.
3. Programmers rarely start from scratch - they use **libraries** (shared code). This is why
   software has **dependencies**: to work, program A needs library B version X.

**Scripts** are small interpreted programs used to automate tasks. In IT support, scripting is a
superpower: a 10-line PowerShell script can do in 5 seconds what takes an hour by hand across 50
machines.

```powershell
# Example: list the 5 processes using the most memory
Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 5 Name, WorkingSet64
```

## Installing, updating, and removing software

### Windows

- **`.exe` installers** - a program that installs another program; behavior varies per vendor.
- **`.msi` packages** - Windows Installer format; standardized, supports silent install
  (`msiexec /i app.msi /qn`) - preferred in organizations.
- **Microsoft Store / MSIX** - sandboxed, auto-updating apps.
- **winget** - Windows' built-in package manager:

  ```powershell
  winget search vlc
  winget install --id VideoLAN.VLC -e
  winget upgrade --all
  ```

### Linux

- Software comes as **packages** from **repositories** managed by a **package manager**:

  ```bash
  sudo apt update            # refresh the list of available packages
  sudo apt install htop      # install
  sudo apt upgrade           # update everything
  sudo apt remove htop       # uninstall
  ```

### macOS

- `.dmg` (drag the app to Applications), `.pkg` installers, the App Store, or Homebrew.

## Software versions

Most software uses **semantic versioning**: `MAJOR.MINOR.PATCH` (e.g. `2.4.1`).

- **Major** - big changes, may break compatibility.
- **Minor** - new features, backward-compatible.
- **Patch** - bug and security fixes.

Why it matters in support: "it works on my machine" is often a **version difference**. Always
note the version in tickets (`Help → About`, or `program --version`).

## Updates and patches

- **Security patches** close vulnerabilities - delaying them is one of the most common causes of
  breaches.
- **Feature updates** may change behavior users rely on - organizations often test them first
  on a small group (a "pilot ring") before rolling out to everyone.
- Rule of thumb: **test → pilot → deploy broadly → monitor**.

## Licensing

Software is usually licensed, not owned:

- **Proprietary** (per-user, per-device, subscription - e.g. Microsoft 365).
- **Open source** (source code available; licenses like MIT, GPL, Apache define what you can do).
- **Freeware / shareware** - free to use, or free with limits.

IT support tracks licenses so the company stays compliant and doesn't pay for unused seats.

## Common software problems and first steps

| Symptom | First steps |
|---|---|
| App won't open | restart it, restart the PC, check for updates, run as the user vs admin |
| App crashes on one file | try another file → is it the file or the app? |
| "Missing DLL" / "library not found" | reinstall the app (dependency missing or corrupted) |
| Worked yesterday, broken today | what changed? recent update? new plugin? |
| Slow app | check CPU/RAM in Task Manager; too many extensions/add-ins |

## Practice project

[`practice/technical-support-fundamentals/pc-inventory`](<../../practice/technical-support-fundamentals/pc-inventory>) -
the PowerShell part of the inventory lists installed software (name + version) from the registry,
which is how software audits and license checks start.

## Related

- [Operating system](<operating-system.md>) - the layer software runs on.
- [Packages and software management](<../os power user/packages-and-software-management.md>) - package managers in depth.
- [Troubleshooting](<troubleshooting.md>) - "what changed?" is the first question for software issues.
