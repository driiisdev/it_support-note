# Practice: Bits & Encoding (Introduction)

Concept note:
[`introduction.md`](<../../../concepts/technical support fundamentals/introduction.md>)

## What this demonstrates

That "computers think in 0s and 1s" is something you can check, not just a phrase to memorize.
One small CLI shows how numbers, text, storage sizes, and colors all come down to bits, and
explains two of the most common "is my computer broken?" questions you'll get in IT support:

- *"I bought a 1 TB drive but Windows says 931 GB - was I ripped off?"*
- *"My CSV/email shows `CafÃ©` instead of `Café`."*

## Scenario

You're the help desk. A user is upset about their "missing" disk space, and another sent you a
customer list full of garbled characters. You use this tool to understand (and explain) both,
and practice binary along the way - you'll need it for subnetting later.

## Folder structure

```
bits-and-encoding/
  bits.py     <- one CLI, seven subcommands (binary, decimal, encode, mojibake, storage, gates, color)
  README.md
```

## Code walkthrough

**Decimal → binary** uses the same "subtract the biggest power of 2 that fits" method you'd do on
paper, and prints each step:

```python
for position in range(bits_needed - 1, -1, -1):
    value = 2 ** position
    if value <= remaining:
        remaining -= value
        bits.append("1")
    else:
        bits.append("0")
```

**Encoding** shows that a character is a *code point* (a number), and UTF-8 turns that number into
1-4 bytes. ASCII characters stay 1 byte; `é` becomes 2 bytes, `☕` becomes 3:

```python
utf8 = ch.encode("utf-8")     # e.g. 'é' -> b'\xc3\xa9'
```

**Mojibake** (garbled text) is reproduced by decoding UTF-8 bytes with the wrong table:

```python
"Café".encode("utf-8").decode("cp1252")   # -> 'CafÃ©'
```

**Storage** compares decimal units (what the drive box uses, powers of 1000) with binary units
(what Windows shows, powers of 1024).

**Gates** prints truth tables, builds a half adder from XOR + AND, and previews how AND is used
with a subnet mask.

## Run it

```bash
python bits.py binary 200
python bits.py decimal "1100 1000"
python bits.py encode "Café ☕"
python bits.py mojibake "Café"
python bits.py storage 1 TB
python bits.py gates
python bits.py color "#1E90FF"
```

Requires Python 3.8+ only (standard library).

Expected highlights:

```
Result : 1100 1000                                  <- binary 200
é     U+00E9      no      c3 a9                     <- 'é' takes 2 bytes in UTF-8
Opened as Windows-1252  : CafÃ©                     <- the classic garbled-text ticket
  931.32 GiB                                        <- the "missing" disk space
```

## Try this yourself

- Convert your own IP address octets to binary by hand, then check with `python bits.py binary`.
- Run `python bits.py storage 512 GB` and `python bits.py storage 2 TB` - notice the "loss" grows
  with bigger units (KB is 2.4% off, TB is ~9.1% off).
- Save a text file in Notepad as **ANSI**, then as **UTF-8**, with the word `Café` in it. Compare
  file sizes in Explorer (`Properties`) - one byte difference, for the `é`.
- Add a `hex` subcommand that converts decimal ↔ hexadecimal (you'll need hex for MAC and IPv6
  addresses).
- Extend `gates` to build a **full adder** (two half adders + an OR) and add two 4-bit numbers.

## Real-world equivalent

- Disk space explanations: every help desk gets the "931 GB" question weekly.
- Encoding issues: CSV imports into Excel, emails from old systems, database exports - fixing
  them is choosing the right encoding (UTF-8) when opening or importing.
- Binary/hex fluency: subnet masks, MAC addresses, IPv6, file permissions (`chmod 755`), and error
  codes like `0x80070005` (= "access denied") all assume it.
