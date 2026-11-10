# The Operating System

The **operating system (OS)** is the software that manages the hardware and lets every other
program use it without needing to know the details. Your browser doesn't talk to the SSD
directly - it asks the OS to "open this file," and the OS handles the rest.

## The two parts of an OS

```
+---------------------------------------------+
| User space: apps, shell, GUI, services      |   <- what users see & touch
+------------------ system calls -------------+
| Kernel: processes, memory, files, devices   |   <- the core, talks to hardware
+---------------------------------------------+
| Hardware                                    |
+---------------------------------------------+
```

- **Kernel** - the core of the OS. Manages:
  - **Processes** - which program gets the CPU and for how long.
  - **Memory** - giving each program its own RAM space; using disk as overflow
    (**virtual memory**: the *pagefile* on Windows, *swap* on Linux).
  - **Files** - reading/writing data on storage through a **file system** (NTFS, ext4, APFS).
  - **I/O / devices** - keyboards, disks, network cards, through **drivers**.
- **User space** - everything you interact with: the **shell** (command line), the **GUI**
  (desktop, windows, icons), and applications.

## Common operating systems

| OS | Kernel | Where you'll see it |
|---|---|---|
| Windows | Windows NT kernel (closed source) | most business desktops/laptops, Windows Server |
| macOS | XNU (Darwin, Unix-based) | Apple computers |
| Linux | Linux kernel (open source) - many **distributions**: Ubuntu, Debian, Red Hat, Fedora | servers, cloud, embedded devices |
| ChromeOS | Linux kernel | Chromebooks (education, kiosk) |
| Android | Linux kernel | phones, tablets |
| iOS / iPadOS | XNU | iPhones, iPads |

Linux "distros" share the same kernel but differ in package managers, default software, and
release cycles (e.g. Ubuntu/Debian use `apt` + `.deb`, Red Hat/Fedora use `dnf` + `.rpm`).

## The boot process

What happens between pressing the power button and seeing the login screen:

```
Power on
  -> BIOS/UEFI firmware runs POST (hardware check)
  -> finds boot device (boot order)
  -> Bootloader  (Windows Boot Manager / GRUB on Linux)
  -> Kernel loads into memory, initializes drivers
  -> First user-space process starts (Linux: systemd/init, PID 1; Windows: smss.exe ...)
  -> System services start (networking, logging, antivirus ...)
  -> Login screen
```

> 🖼️ **Image idea: boot process flowchart** - the steps above as a vertical flowchart with the
> Windows and Linux names of each stage side by side.
> Suggested file: `assets/img/boot-process.png`
<!-- ![boot process](<../../assets/img/boot-process.png>) -->

Knowing the stages tells you where a boot problem is:

- Nothing on screen, beeps → **hardware/POST**.
- "No bootable device" → **firmware can't find a bootloader** (wrong boot order, dead disk).
- Logo then crash/blue screen → **kernel or driver** problem.
- Boots, but slow login → **services / startup programs**.

## Interacting with the OS: GUI vs shell

- **GUI** - easy for users, discoverable.
- **Shell / CLI** - text commands. Faster for repetitive tasks, scriptable, works over remote
  connections. As IT support, you'll use both:
  - Windows: **PowerShell** (modern) and **Command Prompt** (`cmd.exe`, legacy).
  - Linux/macOS: **Bash** or **zsh**.

```powershell
# Windows PowerShell - who am I, what OS is this?
whoami
Get-ComputerInfo | Select-Object OsName, OsVersion, CsTotalPhysicalMemory
```

```bash
# Linux
whoami
uname -a
cat /etc/os-release
```

## Installing an operating system

1. **Get installation media** - USB stick (e.g. made with the Windows Media Creation Tool or
   Rufus), ISO for a VM, or **network boot (PXE)** in larger organizations.
2. **Boot from the media** (change boot order or use the one-time boot menu, often F12/F10/Esc).
3. **Partition the disk** - divide it into sections. Partition table types:
   - **MBR** - older; max 4 primary partitions, max ~2 TB disk.
   - **GPT** - modern, used with UEFI; huge disks, up to 128 partitions on Windows.
4. **Format** the partition with a file system (NTFS for Windows, ext4 for Linux).
5. Copy OS files, configure language, users, and network.
6. Install **drivers** and **updates** right away.

In organizations, this is usually automated with **disk images** (a pre-built copy of a
configured OS) deployed to many machines - see [Operating systems in practice](<../os power user/operating-systems-in-practice.md>).

## Virtual machines

A **virtual machine (VM)** is a whole computer simulated in software: virtual CPU, RAM, disk,
and network, running on a physical **host**.

- Software: VirtualBox, VMware Workstation, Hyper-V (Type 2 / desktop), or ESXi, Proxmox,
  Hyper-V Server (Type 1 / bare-metal servers).
- Uses in IT support: testing an update before rolling it out, trying a new OS, running an old
  app that only works on an old OS, practicing without breaking your own machine.
- **Snapshots** let you save the VM's state and roll back - ideal for learning.

## Practice project

[`practice/technical-support-fundamentals/pc-inventory`](<../../practice/technical-support-fundamentals/pc-inventory>) -
part of the inventory report is the OS name, version, architecture, uptime, and boot time.

**Highly recommended extra:** install VirtualBox and create one Windows and one Ubuntu VM. Most
of the OS Power User module is easier to practice inside VMs you're allowed to break.

## Related

- [Hardware](<hardware.md>) - what the OS manages.
- [Software](<software.md>) - what runs on top of the OS.
- [Navigating the system](<../os power user/navigating-the-system.md>) - using the shell in depth.
- [File systems](<../os power user/file-systems.md>) - partitioning and formatting in depth.
