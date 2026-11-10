# File Systems, Disks & Partitions

How an OS organizes storage: partitioning a disk, formatting it with a file system, mounting it,
and keeping it healthy.

## Steps to make a disk usable

```
Raw disk  ->  Partition table (MBR / GPT)  ->  Partitions  ->  Format (file system)  ->  Mount (drive letter / mount point)
```

1. **Partition** - divide the disk into sections. Each partition is managed separately.
2. **Format** - write a **file system** onto a partition (the structure that tracks files,
   folders, sizes, permissions, and where the data blocks are).
3. **Mount** - attach the file system so the OS can use it (`D:` on Windows, `/mnt/data` on Linux).

> 🖼️ **Image idea: disk → partitions → file systems → mount points** - one physical disk split
> into an EFI partition, a C: (NTFS) partition, and a recovery partition, and a Linux disk with
> `/boot`, `/`, and swap.
> Suggested file: `assets/img/disk-partitions.png`
<!-- ![disk partitions](<../../assets/img/disk-partitions.png>) -->

## Partition tables: MBR vs GPT

| | MBR (Master Boot Record) | GPT (GUID Partition Table) |
|---|---|---|
| Era | 1980s, BIOS | modern, UEFI |
| Max disk size | ~2 TB | ~9.4 ZB (effectively unlimited) |
| Partitions | 4 primary (or 3 + an extended with logical drives) | 128 on Windows |
| Resilience | one copy of the table | backup header at the end of the disk + CRC checks |

New systems should use **GPT + UEFI**. Converting MBR → GPT on a system disk: Windows has
`mbr2gpt.exe`.

## File system types

| File system | Used by | Notes |
|---|---|---|
| **NTFS** | Windows | permissions (ACLs), journaling, encryption, compression, large files. Default for Windows drives. |
| **FAT32** | USB sticks, old devices | universally compatible, but **max file size 4 GB**, max partition (Windows formats) 32 GB. No permissions. |
| **exFAT** | USB drives, SD cards | like FAT32 without the 4 GB limit; works on Windows + macOS (+ Linux). Best for portable drives. |
| **ext4** | Linux | default on most distros; journaling, permissions. |
| **XFS / Btrfs** | Linux servers | XFS: large files & high performance; Btrfs: snapshots, checksums. |
| **APFS** | macOS / iOS | snapshots, encryption, optimized for SSDs. (HFS+ before it.) |

"I can't copy a 6 GB video to my USB stick" → the stick is **FAT32**. Reformat as **exFAT**
(after backing up!).

**Journaling** - the file system writes what it's *about to do* to a journal first. After a crash
or power loss it replays/rolls back the journal instead of being left half-written.

## Managing disks

### Windows

- **Disk Management** (`diskmgmt.msc`) - GUI: create, delete, extend, shrink, format partitions.
- **DiskPart** - CLI (careful: there is no undo):

  ```
  diskpart
  list disk
  select disk 1
  clean                  # WIPES the disk's partition table
  convert gpt
  create partition primary
  format fs=ntfs quick label="Data"
  assign letter=E
  ```

- PowerShell: `Get-Disk`, `Get-Partition`, `Get-Volume`, `Format-Volume`.

### Linux

```bash
lsblk                       # block devices and partitions in a tree
sudo fdisk -l               # partition tables
sudo parted /dev/sdb        # create/resize partitions (MBR or GPT)
sudo mkfs.ext4 /dev/sdb1    # format as ext4
sudo mount /dev/sdb1 /mnt/data
sudo umount /mnt/data       # always unmount before removing a drive
blkid                       # UUIDs of each partition
```

To mount automatically at boot, add a line to **`/etc/fstab`** (use the UUID - device names like
`/dev/sdb` can change):

```
UUID=1a2b3c4d-...  /mnt/data  ext4  defaults  0  2
```

## Swap and the pagefile (virtual memory)

When RAM fills up, the OS moves memory pages it isn't actively using to disk.

- Windows: **`pagefile.sys`** on C:, managed automatically (System Properties → Advanced →
  Performance → Virtual memory).
- Linux: a **swap partition** or **swap file** (`swapon --show`, `free -h`).

Heavy swapping = everything becomes slow (disk is far slower than RAM). The fix is more RAM or
fewer running programs - not a bigger pagefile.

## Files: metadata and links

A file system stores data plus **metadata**: name, size, owner, permissions, timestamps (created,
modified, accessed), and where the blocks are.

- **NTFS** keeps this in the **MFT** (Master File Table) - one record per file.
- **ext4** keeps it in **inodes** - one inode per file; the filename is just a directory entry
  that points to an inode (`ls -i` shows inode numbers).

### Hard links vs symbolic links

| | Hard link | Symbolic (soft) link |
|---|---|---|
| Points to | the same data (same inode / MFT record) | a **path** |
| If the original is deleted | data still exists through the hard link | link breaks ("dangling") |
| Across drives/partitions | no | yes |
| Linux | `ln original link` | `ln -s /path/original link` |
| Windows | `mklink /H link original` | `mklink link original` (`/D` for directories); `.lnk` **shortcuts** are a separate Explorer feature, not file-system links |

## Disk usage

```powershell
Get-PSDrive -PSProvider FileSystem             # free/used per drive
Get-ChildItem C:\Users -Recurse -ErrorAction SilentlyContinue |
  Sort-Object Length -Descending | Select-Object -First 20 FullName, Length
cleanmgr                                        # Disk Cleanup
```

```bash
df -h                           # free space per mounted file system
du -sh /var/log/*               # size of each item
du -h --max-depth=1 / | sort -h # biggest top-level folders
```

## Repairing file systems

Crashes, power loss, and failing drives corrupt file systems.

- **Windows**: `chkdsk C: /f` (fix errors; on the system drive it runs at next reboot),
  `chkdsk /r` (also find bad sectors). `sfc /scannow` repairs **system files**, not the file
  system - different tool.
- **Linux**: `fsck /dev/sdb1` - **only on an unmounted** file system (running it on a mounted
  one can corrupt it further).
- If a disk is physically failing, **back up first** - repair attempts stress the drive.

## How it's used in real IT support

| Ticket | Approach |
|---|---|
| "C: drive is full" | find big folders (temp files, Downloads, old installers, OST/PST files), Disk Cleanup, move data |
| New external drive must work on Mac and PC | format exFAT |
| Can't copy file > 4 GB to USB | FAT32 limit |
| New 4 TB disk only shows 2 TB | it was initialized as MBR - reinitialize as GPT |
| Corrupt files after power cut | `chkdsk` / `fsck`, then restore from backup if needed |

## Practice project

[`practice/os-power-user/disk-report`](<../../practice/os-power-user/disk-report>) -
a cross-platform Python script that reports free space per drive with warning thresholds, finds
the largest files and folders under a path, and flags files that wouldn't fit on a FAT32 drive -
the "my disk is full" ticket, automated.

## Related

- [Operating system](<../technical support fundamentals/operating-system.md>) - partitioning during OS install.
- [Data recovery & backups](<../system administration it infrastructure services/data-recovery-backups.md>) - RAID and backups.
- [Defense in depth](<../it security/defense-in-depth.md>) - full-disk encryption.
