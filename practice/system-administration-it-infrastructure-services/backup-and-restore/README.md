# Practice: Backup & Restore (Data Recovery & Backups)

Concept note:
[`data-recovery-backups.md`](<../../../concepts/system administration it infrastructure services/data-recovery-backups.md>)

## What this demonstrates

A working backup tool, and a drill that proves it works - because **a backup you've never restored
is a hope, not a backup**:

- **Full vs incremental** backups: the full copies everything; each incremental copies only what
  changed since the previous backup.
- **Manifests with SHA-256 hashes**: every restore point records the full state of the source, so any
  point in time can be restored, and every stored file can be **verified** later (catches bit rot,
  tampering, a half-copied file).
- **Incremental chains**: one corrupt file in the full breaks *every* restore point built on it -
  `verify` tells you exactly which.
- **Retention**: prune old backups by **whole chains** (deleting a full but keeping its incrementals
  would make them useless).
- **Safe restore**: restore into an *empty* folder, verify, then copy back - never over the only copy.

## Scenario

A ransomware infection encrypts the company file share on a Thursday. You have a full backup from
Monday and incrementals from Tuesday and Wednesday. Can you get everything back - and how sure are you?

## Folder structure

```
backup-and-restore/
  backup.py          <- full / incr / list / verify / restore / prune
  disaster_drill.py  <- the whole story end to end in ./drill/ (recreated on every run)
  drill/             <- created by the drill (gitignored)
```

Backup store layout:

```
backup-store/
  20260304-020000-full/  files/<everything>             manifest.json
  20260305-020000-incr/  files/<only changed files>     manifest.json  (lists ALL files + where each lives)
  20260306-020000-incr/  files/<only changed files>     manifest.json
```

## Code walkthrough

**Change detection** - the same shortcut real tools use, with a hash as the safety net:

```python
if prev and prev["size"] == st.st_size and prev["mtime"] == st.st_mtime:
    files[rel] = prev            # unchanged -> reuse the previous entry, copy nothing
digest = sha256(path)            # otherwise hash it; same hash = metadata-only change
```

**Each manifest is a complete restore point** - every file maps to the backup folder that physically
holds that version (`"stored_in"`). Restoring any point = read one manifest, copy each file from where
it lives, re-hash to confirm:

```python
src = store / info["stored_in"] / "files" / rel
shutil.copy2(src, dst)
assert sha256(dst) == info["sha256"]
```

**Deletions** are handled naturally: a file deleted on Day 3 simply isn't in Day 3's manifest
(restore latest → it's gone; restore Day 1 → it's back).

## Run it

```bash
python disaster_drill.py                       # the full story, ~10 seconds

# or by hand:
python backup.py full    C:\path\to\folder D:\backup-store
python backup.py incr    C:\path\to\folder D:\backup-store
python backup.py list    D:\backup-store
python backup.py verify  D:\backup-store
python backup.py restore D:\backup-store latest C:\restore-test
python backup.py prune   D:\backup-store --keep-chains 2
```

Expected (`disaster_drill.py`, excerpts):

```
20261109-093612-incr: 2 file(s) copied (86 bytes), 3 unchanged, 0 deleted since previous, 5 total
files on the share now: ['HOW_TO_DECRYPT.txt', 'budget-2026.csv.locked', ...]
Verified 7 stored file(s) used by 3 restore point(s): all OK
Restored 5/5 files from 20261109-093613-incr ... - all verified by SHA-256
Day 1 budget line: IT,120000 | invoices.txt present: True
CORRUPT  readme.txt in 20261109-093649-full - breaks 3 restore point(s): ...
```

## Try this yourself

- Back up a real folder (e.g. your Documents) to an external drive, then restore it to a test folder
  and compare file counts and sizes. Time it - that's your real **RTO** for that data.
- Schedule `backup.py incr` nightly with Task Scheduler / cron and `backup.py full` weekly. What's your
  **RPO** now? (Up to 24 h of changes can be lost.)
- Add a **differential** mode: copy everything changed since the last **full** (not the last backup).
  Compare how many folders a restore needs.
- Add **retention by age** (`--keep-days 30`) as well as by chain count.
- Make the store **3-2-1**: a second store on another disk, and a third synced to cloud storage.
- Add encryption at rest: compress each backup folder to a `.zip`, then encrypt it with
  `openssl enc -aes-256-cbc -pbkdf2` (see [crypto-lab](../../it-security/crypto-lab)).
- Compare with `robocopy /MIR` and `rsync -a --delete`: those keep **one** mirror - what happens to your
  "backup" when ransomware encrypts the source and the mirror job runs?

## Real-world equivalent

- **Veeam**, **Windows Server Backup**, **Time Machine**, **restic**, **borg** - all use the same ideas:
  full/incremental chains, content hashes, verification jobs, and retention policies.
- Ransomware-resilient backup = offline or **immutable** copies (object lock / WORM storage) that the
  attacker can't encrypt or delete, plus regular restore tests.
