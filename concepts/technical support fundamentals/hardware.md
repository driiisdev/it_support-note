# Computer Hardware

The physical parts of a computer. In IT support you don't need to design hardware, but you do
need to **identify parts, know what they do, recognize when one is failing, and replace it
safely**.

## The core components

```
            +-------------------- Motherboard --------------------+
            |                                                     |
 Power ---> |  [CPU] <---> [RAM]        [PCIe slots: GPU, NIC]    |
 Supply     |    |                                                |
            |  Chipset <---> [SATA / M.2: SSD, HDD]               |
            |    |                                                |
            |  [USB, audio, network ports]   [BIOS/UEFI chip]     |
            +-----------------------------------------------------+
```

> 🖼️ **Image idea: labeled motherboard** - photo or drawing of an ATX motherboard with the CPU
> socket, RAM slots, PCIe slots, M.2 slot, SATA ports, 24-pin power, and CMOS battery labeled.
> Suggested file: `assets/img/motherboard-labeled.png`
<!-- ![motherboard labeled](<../../assets/img/motherboard-labeled.png>) -->

### CPU (Central Processing Unit)

The "brain" - it executes instructions.

- **Instruction set** - the list of operations the CPU understands. Most PCs are **x86-64**
  (Intel, AMD); phones, newer Macs, and many tablets are **ARM**. Software compiled for one
  won't run natively on the other.
- **Clock speed** (GHz) - how many cycles per second. Higher is faster *within the same
  generation*; comparing GHz across generations is misleading.
- **Cores / threads** - each core can work on a task independently. More cores help with
  multitasking and parallel workloads.
- **Socket** - the CPU must physically match the motherboard socket (e.g. LGA 1700, AM5).
- **Cooling** - CPUs need a heat sink + fan (or liquid cooler) and **thermal paste** between the
  CPU and the cooler. Overheating causes throttling (slowness) and random shutdowns.

### RAM (Random Access Memory)

Short-term, **volatile** working memory: fast, but erased when the power goes off.

- Programs and open files are loaded from disk into RAM so the CPU can work on them quickly.
- Common type: **DRAM** on **DIMM** sticks (desktops) or **SO-DIMM** (laptops).
- Generations: DDR3 → DDR4 → DDR5 - **not interchangeable**, they're keyed differently.
- Too little RAM → the OS starts using disk as overflow (swap/pagefile) → everything feels slow.

### Motherboard

The circuit board everything plugs into.

- **Chipset** - manages data flow between CPU, RAM, and peripherals.
- **Expansion slots** - **PCIe** (x1, x4, x16) for graphics cards, network cards, NVMe adapters.
- **Form factor** - physical size/layout: **ATX** (full-size desktop), **micro-ATX**,
  **mini-ITX** (small builds). The case must support the board's form factor.

### Storage

Long-term, **non-volatile** storage - survives power-off.

| Type | How it works | Pros | Cons |
|---|---|---|---|
| HDD | spinning magnetic platters + moving read/write head | cheap per GB, large capacity | slow, fragile, noisy |
| SATA SSD | flash memory, SATA interface | much faster, no moving parts | ~550 MB/s cap of SATA |
| NVMe SSD | flash memory directly on PCIe (M.2 slot) | very fast (3,000-7,000+ MB/s) | more expensive, can run hot |

Interfaces you'll see: **SATA** (cable), **M.2** (a slot shape - can be SATA *or* NVMe, check!),
**USB** (external drives).

Signs a drive is failing: clicking noises (HDD), very slow boots, files that won't open,
SMART warnings in the BIOS or tools like CrystalDiskInfo.

### Power Supply (PSU)

Converts wall **AC** power to the **DC** voltages components use (3.3V, 5V, 12V).

- **Wattage** must cover all components (graphics cards are the hungriest).
- Some PSUs have a 115V/230V switch - setting it wrong can destroy the PSU.
- Laptops use an external **AC adapter** ("power brick") instead.

### Peripherals & ports

Anything connected to the computer from outside.

| Port | Used for |
|---|---|
| USB 2.0 / 3.x / USB-C | keyboards, drives, phones, docks (USB-C is a *connector shape*; speed depends on the standard behind it) |
| HDMI / DisplayPort | monitors, TVs |
| RJ45 (Ethernet) | wired network |
| 3.5mm audio | headphones, mics |
| Thunderbolt | high-speed docks, displays (uses USB-C connector) |

## BIOS / UEFI and POST

When you press the power button, the CPU doesn't know about your OS yet. It runs firmware stored
on a chip on the motherboard:

1. **BIOS** (older) or **UEFI** (modern replacement - supports large disks/GPT, Secure Boot,
   mouse-driven setup).
2. **POST** (Power-On Self Test) checks that essential hardware (CPU, RAM, video) works. If it
   fails you may get **beep codes** or diagnostic LEDs - look them up in the motherboard manual.
3. Firmware finds a **boot device** (by boot order) and hands control to its bootloader.

Settings are kept in **CMOS** memory, powered by a coin battery. A dead CMOS battery → the clock
resets every time the PC is unplugged.

## Building / repairing a computer safely

1. **Prevent ESD** (electrostatic discharge) - wear an anti-static wrist strap or touch a
   grounded metal surface first. Static you can't even feel can kill components.
2. Install **CPU** into the socket (match the triangle/notch, no force needed).
3. Apply **thermal paste** and mount the cooler.
4. Insert **RAM** (check the motherboard manual for which slots to use for dual channel).
5. Mount the motherboard in the case on standoffs.
6. Connect **storage**, **PSU** cables (24-pin motherboard, 8-pin CPU, GPU power), front-panel
   connectors.
7. Install expansion cards.
8. Power on, enter UEFI, check that everything is detected, then install the OS.

> 🖼️ **Image idea: ESD wrist strap + RAM installation** - a photo showing correct RAM notch
> alignment and a grounded wrist strap.
> Suggested file: `assets/img/esd-and-ram.png`
<!-- ![esd and ram](<../../assets/img/esd-and-ram.png>) -->

## Mobile devices

Phones and tablets have the same building blocks (CPU, RAM, storage, battery) but integrated into
a **System on a Chip (SoC)** and usually not user-replaceable.

- **Batteries** are Li-ion: they wear out over charge cycles. A swollen battery is a safety
  hazard - stop using the device.
- Repair is often "replace the whole device" or send to the manufacturer.
- Common support tasks: charging issues (try a different cable/charger first), storage full,
  backups before a reset.

## How this shows up in real support tickets

| Symptom | Likely hardware cause |
|---|---|
| PC won't power on at all | PSU, power cable, wall outlet, power button cable |
| Powers on, no display, beeps | RAM not seated, GPU issue - check beep code |
| Random shutdowns under load | overheating (dust, dried thermal paste), weak PSU |
| Very slow, disk light always on | HDD failing, or RAM too small → heavy swapping |
| Clock resets after unplugging | dead CMOS battery |

## Practice project

[`practice/technical-support-fundamentals/pc-inventory`](<../../practice/technical-support-fundamentals/pc-inventory>) -
a script that collects CPU, RAM, disk, and OS details from the machine it runs on and writes an
inventory report - exactly what an IT team does when onboarding a fleet of devices.

## Related

- [Introduction](<introduction.md>) - bits, bytes, and storage units.
- [Operating system](<operating-system.md>) - what takes over after the BIOS/UEFI.
- [Troubleshooting](<troubleshooting.md>) - isolating hardware vs software problems.
