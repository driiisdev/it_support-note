# Introduction to IT Support & How Computers Think

IT support is the job of **keeping people productive with technology**: setting up machines,
fixing what breaks, explaining what's going on, and preventing the same problem twice. The
technical side (hardware, OS, networks) is only half of it. The other half is people: listening,
asking the right questions, and writing things down so the next person doesn't start from zero.

## What an IT support specialist actually does

| Area | Typical day-to-day task |
|---|---|
| Hardware | imaging a new laptop, swapping a failed SSD, setting up printers |
| Software | installing/updating apps, fixing a crashing program, licensing |
| Accounts | creating users, resetting passwords, granting folder access |
| Networking | "the Wi-Fi is down", VPN won't connect, can't reach a shared drive |
| Security | removing malware, enforcing updates, spotting phishing |
| Documentation | writing tickets, knowledge-base articles, runbooks |

The common thread: **take a vague complaint ("my computer is slow") and turn it into a specific,
fixable cause ("the disk is 99% full because of a sync folder")**.

## A very short history of computing

Knowing where things came from explains a lot of today's weird naming and limits.

1. **Abacus (~500 BC)** - the first "computer": a tool that stores numbers and helps you calculate.
2. **Mechanical calculators (1600s-1800s)** - Pascal's and Leibniz's machines; Charles Babbage's
   *Difference Engine* and *Analytical Engine*. Ada Lovelace wrote what's considered the first
   algorithm for it - the idea that a machine could follow instructions, not just add.
3. **Punch cards (1800s-1900s)** - Jacquard looms, then Herman Hollerith's tabulating machines
   for the 1890 US census (his company eventually became IBM). Data stored as holes/no-holes =
   the first practical binary storage.
4. **Electronic computers (1940s)** - ENIAC: room-sized, vacuum tubes, programmed by rewiring.
   Grace Hopper popularized the term "bug" and created early compilers (code humans can read →
   machine instructions).
5. **Transistors & integrated circuits (1950s-60s)** - replaced vacuum tubes: smaller, cheaper,
   cooler, more reliable. Microchips put many transistors on one piece of silicon.
6. **Personal computers (1970s-80s)** - Apple II, IBM PC, then Windows and Mac GUIs.
7. **Internet, mobile, cloud (1990s-today)** - computers become connected, then pocket-sized,
   then rented by the hour in someone else's data center.

> 🖼️ **Image idea: timeline of computing** - a horizontal timeline from abacus → Babbage →
> ENIAC → transistor → PC → smartphone → cloud.
> Suggested file: `assets/img/computing-timeline.png`
<!-- ![computing timeline](<../../assets/img/computing-timeline.png>) -->

## Digital logic: why everything is 0s and 1s

A computer is made of billions of tiny switches (transistors) that are either **on (1)** or
**off (0)**. One of those values is a **bit**. Eight bits are a **byte**.

- 1 bit → 2 possible values (0, 1)
- 8 bits (1 byte) → 2^8 = **256** possible values (0-255)
- Each extra bit **doubles** the number of values you can represent.

### Counting in binary

Each position is a power of 2 (just like decimal positions are powers of 10):

```
Position value:  128  64  32  16   8   4   2   1
Bits:              0   1   0   0   0   0   0   1   = 64 + 1 = 65
```

Decimal → binary, the "subtract the biggest power of 2 that fits" way:

```
Convert 200:
200 - 128 = 72   -> 1 in the 128s place
 72 -  64 =  8   -> 1 in the 64s place
 (32? no) (16? no)
  8 -   8 =  0   -> 1 in the 8s place
Result: 1100 1000
```

### Storage units (and why your "1 TB" drive shows 931 GB)

| Unit | Decimal (drive makers) | Binary (Windows shows this) |
|---|---|---|
| Kilobyte | 1,000 bytes (KB) | 1,024 bytes (KiB) |
| Megabyte | 1,000 KB | 1,024 KiB (MiB) |
| Gigabyte | 1,000 MB | 1,024 MiB (GiB) |
| Terabyte | 1,000 GB | 1,024 GiB (TiB) |

A "1 TB" drive = 1,000,000,000,000 bytes ÷ 1024³ ≈ **931 GiB**. Nothing is missing - it's the
same number of bytes counted two different ways. This is a *very* common user question.

### Character encoding: turning bits into text

A byte is just a number. **Character encoding** is the agreed-upon table that says which number
means which character.

- **ASCII** - 7 bits, 128 characters (English letters, digits, punctuation). `A` = 65, `a` = 97.
- **UTF-8** - the modern standard. Backward-compatible with ASCII for the first 128 characters,
  but uses 1-4 bytes per character so it can represent every language and emoji.

When a user sees garbage like `Ã©` instead of `é`, that's an encoding mismatch: the file was
written as UTF-8 and read as something else (e.g. Windows-1252).

### Colors are numbers too

Screens use **RGB**: one byte each for red, green, and blue = 24 bits per pixel.
`(255, 0, 0)` is pure red, `#FFFFFF` is white. 256³ ≈ 16.7 million colors.

### Logic gates

Transistors are combined into **logic gates** - the building blocks of every calculation:

| Gate | Output is 1 when... | Example |
|---|---|---|
| AND | both inputs are 1 | 1 AND 1 = 1, 1 AND 0 = 0 |
| OR | at least one input is 1 | 1 OR 0 = 1 |
| NOT | input is 0 (it flips the bit) | NOT 1 = 0 |
| XOR | inputs are different | 1 XOR 0 = 1, 1 XOR 1 = 0 |

Combine enough of these and you get an adder, then an ALU, then a CPU. You'll meet AND again in
networking - it's exactly how a **subnet mask** finds a network address.

> 🖼️ **Image idea: logic gate symbols + truth tables** - AND/OR/NOT/XOR symbols side by side.
> Suggested file: `assets/img/logic-gates.png`
<!-- ![logic gates](<../../assets/img/logic-gates.png>) -->

## The layers of a computer

Every IT problem lives in one (or more) of these layers. Knowing which one is half of
troubleshooting.

```
+-------------------------------------------+
|  User          (the person, their habits) |
+-------------------------------------------+
|  Software      (apps: browser, Office)    |
+-------------------------------------------+
|  Operating     (Windows, Linux, macOS -   |
|  System         manages everything below) |
+-------------------------------------------+
|  Hardware      (CPU, RAM, disk, NIC)      |
+-------------------------------------------+
```

- "Excel crashes on one spreadsheet" → probably **software**.
- "Every app is slow" → **OS** or **hardware** (RAM, disk).
- "It works when I do it but not when they do it" → often the **user** layer (permissions,
  workflow, a setting only they changed).

## Practice project

[`practice/technical-support-fundamentals/bits-and-encoding`](<../../practice/technical-support-fundamentals/bits-and-encoding>) -
a small CLI that converts decimal ↔ binary, shows how text becomes bytes in ASCII vs UTF-8,
explains the "931 GB" drive question, and simulates logic gates.

## Related

- [Hardware](<hardware.md>) - the physical layer this all runs on.
- [Operating system](<operating-system.md>) - the layer that manages the hardware.
- [Troubleshooting](<troubleshooting.md>) - using the layers above to find a problem fast.
- [The network layer](<../computer networking/the-network-layer.md>) - binary + AND gates come back as subnet masks.
