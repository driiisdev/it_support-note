# Data Recovery & Backups

Hardware fails, people delete things, ransomware encrypts everything. **Backups** are the only
thing that turns "we lost it" into "we restored it." A backup you have never tested restoring is
only a hope.

## What is data recovery?

Getting data back after it's lost, deleted, corrupted, or unreachable. Two ways:

1. **Restore from backup** - the reliable way.
2. **Recover from the damaged device** - undelete tools, file system repair, or professional
   data-recovery services for physically failed drives. Expensive and never guaranteed.

The goal of backup planning is to make sure you always have option 1.

## What to back up

- **Business data** - documents, databases, email, accounting.
- **Configurations** - server configs, network device configs, GPOs, DNS zones (often forgotten,
  painful to rebuild by memory).
- **System images** - for fast full recovery of critical servers.
- Usually **not** needed: OS files and apps that can be reinstalled from images/installers.

Ask: *If this disappeared tomorrow, what would we need, and how quickly?*

## Backup types

| Type | Backs up | Backup speed | Restore needs | Storage |
|---|---|---|---|---|
| **Full** | everything | slowest | just the full | most |
| **Differential** | everything changed **since the last full** | grows each day | last full + **last differential** | medium |
| **Incremental** | everything changed **since the last backup of any kind** | fastest | last full + **every incremental since** | least |

```
            Sun     Mon     Tue     Wed
Full:       [F]
Diff:               [M]     [M+T]   [M+T+W]     restore Wed = F + Diff(Wed)
Incr:               [M]     [T]     [W]         restore Wed = F + M + T + W
```

> 🖼️ **Image idea: full vs differential vs incremental** - a week of colored bars for each strategy
> showing what each backup contains and which files a Wednesday restore needs.
> Suggested file: `assets/img/backup-types.png`
<!-- ![backup types](<../../assets/img/backup-types.png>) -->

## The 3-2-1 rule

- **3** copies of your data (the original + 2 backups),
- on **2** different types of media/storage,
- with **1** copy **offsite** (another building or the cloud).

Modern additions: **1 copy immutable or offline** (can't be changed or deleted - protects against
ransomware, which deliberately goes after backups), and **0 errors** after verification
(sometimes written 3-2-1-1-0).

### Onsite vs offsite

| | Onsite | Offsite / cloud |
|---|---|---|
| Restore speed | fast | slower (bandwidth) |
| Survives fire/flood/theft | **no** | yes |
| Cost | hardware | subscription, bandwidth |

Encrypt backups - especially offsite ones. A stolen backup tape/drive is a data breach.

## RAID is not a backup

**RAID** (Redundant Array of Independent Disks) combines disks for performance and/or
**availability** - it keeps a server running when a disk dies. It does **not** protect against
deletion, corruption, ransomware, or fire: those happen to every disk in the array at once.

| Level | How | Min disks | Survives | Notes |
|---|---|---|---|---|
| **RAID 0** | striping | 2 | **no failures** | fast, full capacity, zero redundancy |
| **RAID 1** | mirroring | 2 | 1 disk | 50% capacity |
| **RAID 5** | striping + distributed parity | 3 | 1 disk | capacity = n−1 disks; slow rebuilds on big disks |
| **RAID 6** | striping + double parity | 4 | 2 disks | capacity = n−2 |
| **RAID 10** | mirrors, then striped | 4 | 1 per mirror pair | fast + redundant; 50% capacity |

## Backup tools

- **Windows**: File History (user files), Windows Server Backup, `robocopy` for scripted copies,
  Volume Shadow Copy (previous versions). Enterprise: Veeam, Commvault, Azure Backup.
- **macOS**: Time Machine.
- **Linux**: `rsync`, `tar`, `borg`, `restic`.

```bash
rsync -avh --delete /srv/data/ /mnt/backup/data/      # mirror (careful: --delete removes files from the target)
tar -czf /mnt/backup/etc-$(date +%F).tar.gz /etc      # dated archive of configs
```

```powershell
robocopy D:\Shares E:\Backup\Shares /MIR /R:2 /W:5 /LOG:E:\Backup\robocopy.log   # /MIR also deletes extras!
```

Also back up **SaaS data** (Microsoft 365, Google Workspace): the provider protects their
service, not your deleted mailbox 90 days later.

## Testing restores

Schedule restore tests:

- Restore a random file / folder monthly; restore a full server quarterly.
- Verify **integrity** - checksums (hashes) of restored files match the originals.
- Time it - the result tells you your real recovery time.

## Disaster recovery planning

A **disaster recovery plan (DRP)** documents how the organization recovers from a major incident
(server room flood, ransomware, region-wide cloud outage).

Two key numbers, agreed with the business:

| Metric | Question | Example |
|---|---|---|
| **RPO** - Recovery Point Objective | how much **data** can we afford to lose? | 24 h → nightly backups OK; 15 min → frequent snapshots/replication |
| **RTO** - Recovery Time Objective | how long can we be **down**? | 4 h → need images/standby hardware, not reinstalling from scratch |

The plan includes three kinds of measures:

- **Preventive** - backups, redundancy (RAID, redundant power/internet), surge protection, offsite copies.
- **Detective** - monitoring and alerts (disk health, backup job failures, environmental sensors).
- **Corrective** - the actual recovery steps: who does what, in what order, contact lists,
  where backups and credentials are.

Rank systems by priority (what must come back first?), and keep a copy of the plan **outside**
the systems it describes (printed / offsite) - you can't read it from a dead file server.

## Post-mortems after data loss

Same blameless format as in [What is system administration](<what-is-system-administration.md>):
timeline, root cause, what worked (did the backup restore?), and action items (shorten RPO? add
an immutable copy?).

## Practice project

[`practice/system-administration-it-infrastructure-services/backup-and-restore`](<../../practice/system-administration-it-infrastructure-services/backup-and-restore>) -
a Python backup tool that does **full and incremental** backups using a manifest of file hashes,
keeps a retention policy, and has a **restore + verify** command that checks every restored file's
SHA-256 - plus a script that simulates data loss so you can prove your restore works.

## Related

- [File systems](<../os power user/file-systems.md>) - disks, partitions, and repair.
- [What is system administration](<what-is-system-administration.md>) - risk assessment and post-mortems.
- [Understanding security threats](<../it security/understanding-security-threats.md>) - ransomware.
