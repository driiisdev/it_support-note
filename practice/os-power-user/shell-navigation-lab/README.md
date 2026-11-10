# Practice: Shell Navigation Lab (Navigating the System)

Concept note:
[`navigating-the-system.md`](<../../../concepts/os power user/navigating-the-system.md>)

## What this demonstrates

Command-line fluency in **both** PowerShell and Bash, on a realistic mess: a fake user profile
with logs full of errors, duplicate installers, a suspicious double-extension download, hidden files
(dotfiles *and* the Windows hidden attribute), file names with spaces, and old large files.

The point isn't memorizing commands - it's seeing the same task in two shells and noticing the
difference: **PowerShell pipes objects** (`Where-Object LastWriteTime -lt ...`), **Bash pipes text**
(`grep | cut | sort | uniq -c`).

## Scenario

A user's laptop is "full and slow," their logs show errors, and they downloaded something odd. You
connect remotely - no GUI, shell only - and investigate.

## Folder structure

```
shell-navigation-lab/
  setup_lab.py     <- builds lab/home/amina/ (seeded - same files every time); --clean removes it
  challenges.md    <- 14 challenges, each with PowerShell + Bash answers in collapsible blocks
  lab/             <- generated practice area (gitignored)
```

Generated layout:

```
lab/home/amina/
  .bashrc  .secret-notes.txt  .ssh/config  desktop.ini (Windows-hidden)
  Documents/   "Q1 Budget.xlsx"  "Q2 Budget.xlsx"  "meeting notes.txt"  Projects/vpn-rollout/{plan.md,users.csv}
  Downloads/   setup-7zip.exe  "setup-7zip (1).exe"  "setup-7zip (2).exe"  holiday-video.mp4  invoice_8841.pdf.exe  report.PDF
  logs/        app.log  debug.tmp  old/app-2026-02.log
  a/b/c/d/treasure.txt
```

## Code walkthrough

`setup_lab.py` does three things worth noticing:

```python
random.seed(42)                       # deterministic lab -> the answer key in challenges.md stays valid
os.utime(path, (t, t))                # backdate files so "older than 180 days" challenges work
subprocess.run(["attrib", "+h", ...]) # Windows hidden attribute (different from Linux dotfiles!)
```

The logs are generated with a timestamp, level, service, and message - the same shape as real
syslog lines - so `grep`/`Select-String`/`awk` practice transfers directly to real servers.

## Run it

```bash
python setup_lab.py
cd lab/home/amina
# now work through challenges.md
python ../../../setup_lab.py --clean   # when done (or just rerun setup to reset)
```

Sample answers you should reproduce:

| Challenge | Answer |
|---|---|
| ERROR lines in `logs/app.log` | 14 |
| Largest file | `Downloads/holiday-video.mp4` (6 MB) |
| Files older than 180 days | the video + 3 installers |
| Suspicious file | `invoice_8841.pdf.exe` |
| Finance users | tunde, sara |
| Lines per level | INFO 229, WARN 57, ERROR 14 |

## Try this yourself

- Time yourself: do all 14 in PowerShell, then all 14 in Bash. Redo a week later.
- Turn challenge 6 + 7 into a reusable script `cleanup-report.ps1` that takes a path parameter and
  prints the largest and oldest files - a real tool for "my disk is full" tickets (then compare
  with the [disk-report](../disk-report) project).
- Use `Get-Help Select-String -Examples` and `man grep` to find one option you didn't know.
- Add your own challenge: find all files with uppercase extensions (`report.PDF`) - hint: `-cmatch`
  in PowerShell, `grep -E '\.[A-Z]+$'` in Bash.
- Practice over SSH: copy the lab to a Linux VM with `scp -r lab user@vm:~` and solve it there.

## Real-world equivalent

This is daily work on servers and remote sessions: searching logs for errors around the time of
an incident, finding what filled a disk, cleaning up safely (list → `-WhatIf` → delete), and
pulling a column out of a CSV export for a report.
