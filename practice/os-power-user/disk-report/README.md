# Practice: Disk Report (File Systems)

Concept note:
[`file-systems.md`](<../../../concepts/os power user/file-systems.md>)

## What this demonstrates

The "my C: drive is full" ticket - one of the most common there is - handled methodically and
**read-only**:

1. Space per drive/mount with WARN/CRIT thresholds (same idea as monitoring alerts).
2. **Where** the space went: biggest folders one level down, then biggest files.
3. **What's safe to discuss removing**: temp files, old installers, archives, files untouched for N days.
4. **FAT32's 4 GiB file limit** - flags files that won't copy to a FAT32 USB stick (the "file too
   large for the destination file system" ticket).

## Scenario

A user's laptop says "Low disk space" and Outlook stopped syncing. You run the report, show the
user that 40 GB is old installers and a forgotten video export, agree on what to remove, and note
that their 6 GB video won't copy to the FAT32 USB stick they're holding.

## Folder structure

```
disk-report/
  disk_report.py   <- drives + optional folder analysis, cross-platform, standard library only
```

## Code walkthrough

**Drives**: Windows drive letters vs Linux mount points (from `/proc/mounts`), each checked with
`shutil.disk_usage` - the same numbers Explorer and `df` show.

**One walk, many answers** - `os.walk` visits every file once and the stats are built up in a
single pass (sizes per top-level child folder, a file list for "largest", counts by cleanup
category, old-file totals):

```python
for path, size, mtime in scan(root):
    per_child[child] += size          # where the space went
    if size > FAT32_MAX: ...           # 4 GiB - 1 byte
    if ext in CLEANUP_PATTERNS[...]:   # .tmp, .msi, .iso, .zip ...
    if mtime < cutoff: ...             # untouched for N days
```

**Defensive walking**, like real tools:

- `onerror=lambda e: None` - skip folders you don't have permission to read instead of crashing.
- Don't follow symlinks/junctions - avoids infinite loops and counting the same data twice.

It never deletes anything: cleanup is a conversation with the user, not a script decision.

## Run it

```bash
python disk_report.py                          # drives only
python disk_report.py C:\Users\<you> --top 15  # where did my space go?
python disk_report.py ~/Downloads --old-days 365
# great test data: the shell lab (installers, old files)
python ../shell-navigation-lab/setup_lab.py && python disk_report.py ../shell-navigation-lab/lab
```

Expected:

```
DRIVE               SIZE        USED        FREE   USED%  STATUS
C:\             237.1 GB    224.0 GB     13.1 GB   94.5%  CRIT  ##################

Cleanup candidates (review with the user before deleting anything!):
  temp files        1 files      300.0 B
  installers        4 files       4.5 MB
  untouched 180+ days:     4 files      10.3 MB
```

## Try this yourself

- Run it on your own user folder. Compare with Windows **Settings → System → Storage** and with
  **Disk Cleanup** (`cleanmgr`) - what do they find that this doesn't? (Windows Update cache,
  hibernation file, restore points.)
- Run `Get-Volume` (PowerShell) or `lsblk -f` / `df -hT` (Linux) and add the **file system type**
  column to the drive section; flag FAT32 drives.
- Add a `--duplicates` option: group files by size, then compare SHA-256 hashes for same-size files.
- Add a `--csv` option so the report can be attached to a ticket or opened in Excel.
- Format a spare USB stick as FAT32, try copying a 5 GB file, read the error, then reformat as exFAT
  and retry.

## Real-world equivalent

- **WinDirStat / WizTree / TreeSize** (Windows), **ncdu** / `du -h --max-depth=1 | sort -h` (Linux).
- Monitoring systems (PRTG, Zabbix, Datadog) alert at exactly these WARN/CRIT thresholds - usually
  around 80% / 90%.
