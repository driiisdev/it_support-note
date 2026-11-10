"""
disk_report.py - the "my disk is full" ticket, automated.

1. Free space per drive / mount, with WARN/CRIT thresholds.
2. Largest folders (one level deep) under a path - where the space went.
3. Largest files under a path.
4. Files that would NOT fit on a FAT32 drive (> 4 GiB - 1 byte).
5. Cleanup candidates: temp files, old installers, files untouched for N days.

Read-only: it never deletes anything.

Usage:
    python disk_report.py                       # drives only
    python disk_report.py C:\\Users\\me          # drives + analysis of that folder
    python disk_report.py ~ --top 15 --old-days 365
"""

import argparse
import os
import platform
import shutil
import time
from pathlib import Path

FAT32_MAX = 4 * 1024 ** 3 - 1
CLEANUP_PATTERNS = {
    "temp files": (".tmp", ".temp", ".bak", ".old", ".dmp"),
    "installers": (".exe", ".msi", ".iso", ".dmg", ".pkg", ".deb", ".rpm"),
    "archives": (".zip", ".7z", ".rar", ".tar", ".gz"),
}


def human(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:,.1f} {unit}"
        n /= 1024
    return f"{n:,.1f} PB"


def drives() -> list[str]:
    if platform.system() == "Windows":
        return [f"{c}:\\" for c in "CDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(f"{c}:\\")]
    mounts = []
    try:
        with open("/proc/mounts") as f:
            for line in f:
                dev, mnt, fstype = line.split()[:3]
                if dev.startswith("/dev/") and fstype not in ("squashfs",):
                    mounts.append(mnt)
    except OSError:
        mounts = ["/"]
    return sorted(set(mounts))


def drive_section(warn: int, crit: int) -> None:
    print(f"{'DRIVE':<12}{'SIZE':>12}{'USED':>12}{'FREE':>12}{'USED%':>8}  STATUS")
    for d in drives():
        try:
            u = shutil.disk_usage(d)
        except OSError:
            continue
        if u.total == 0:
            continue
        pct = u.used / u.total * 100
        status = "CRIT" if pct >= crit else "WARN" if pct >= warn else "ok"
        bar = "#" * int(pct // 5)
        print(f"{d:<12}{human(u.total):>12}{human(u.used):>12}{human(u.free):>12}{pct:>7.1f}%  {status:<5} {bar}")


def scan(root: Path):
    """Walk once, yielding (path, size, mtime). Skips what we can't read (permissions, locked files)."""
    for dirpath, dirnames, filenames in os.walk(root, onerror=lambda e: None):
        # don't follow into junctions/symlinks (avoid loops and double counting)
        dirnames[:] = [d for d in dirnames if not os.path.islink(os.path.join(dirpath, d))]
        for name in filenames:
            p = os.path.join(dirpath, name)
            try:
                st = os.stat(p, follow_symlinks=False)
            except OSError:
                continue
            yield Path(p), st.st_size, st.st_mtime


def folder_section(root: Path, top: int, old_days: int) -> None:
    print(f"\nAnalyzing {root} ...")
    start = time.time()
    per_child: dict[str, int] = {}
    files: list[tuple[int, Path, float]] = []
    fat32_too_big, cleanup, old = [], {k: [0, 0] for k in CLEANUP_PATTERNS}, [0, 0]
    cutoff = time.time() - old_days * 86400

    for path, size, mtime in scan(root):
        rel = path.relative_to(root)
        child = rel.parts[0] if len(rel.parts) > 1 else "(files in root)"
        per_child[child] = per_child.get(child, 0) + size
        files.append((size, path, mtime))
        if size > FAT32_MAX:
            fat32_too_big.append((size, path))
        ext = path.suffix.lower()
        for label, exts in CLEANUP_PATTERNS.items():
            if ext in exts:
                cleanup[label][0] += 1
                cleanup[label][1] += size
        if mtime < cutoff:
            old[0] += 1
            old[1] += size

    total = sum(per_child.values())
    print(f"Scanned {len(files):,} files, {human(total)} in {time.time() - start:.1f}s\n")

    print(f"Largest folders under {root}:")
    for name, size in sorted(per_child.items(), key=lambda x: -x[1])[:top]:
        pct = size / total * 100 if total else 0
        print(f"  {human(size):>11}  {pct:5.1f}%  {name}")

    print(f"\nLargest files:")
    for size, path, mtime in sorted(files, key=lambda x: -x[0])[:top]:
        print(f"  {human(size):>11}  {time.strftime('%Y-%m-%d', time.localtime(mtime))}  {path}")

    print("\nCleanup candidates (review with the user before deleting anything!):")
    for label, (count, size) in cleanup.items():
        print(f"  {label:<12} {count:>6} files  {human(size):>11}")
    print(f"  untouched {old_days}+ days: {old[0]:>5} files  {human(old[1]):>11}")

    if fat32_too_big:
        print(f"\nFiles too big for a FAT32 USB stick (> 4 GiB) - format the stick as exFAT instead:")
        for size, path in sorted(fat32_too_big, reverse=True)[:top]:
            print(f"  {human(size):>11}  {path}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("path", nargs="?")
    p.add_argument("--top", type=int, default=10)
    p.add_argument("--warn", type=int, default=80, help="percent used for WARN")
    p.add_argument("--crit", type=int, default=90, help="percent used for CRIT")
    p.add_argument("--old-days", type=int, default=180)
    args = p.parse_args()

    drive_section(args.warn, args.crit)
    if args.path:
        root = Path(args.path).expanduser().resolve()
        if not root.is_dir():
            raise SystemExit(f"{root} is not a folder")
        folder_section(root, args.top, args.old_days)


if __name__ == "__main__":
    main()
