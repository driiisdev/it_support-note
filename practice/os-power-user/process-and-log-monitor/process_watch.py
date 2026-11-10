"""
process_watch.py - "my computer is slow": top processes by CPU and memory, with threshold alerts.

No psutil needed: it asks the OS (PowerShell Get-Process on Windows, ps on Linux/macOS).
CPU % is measured the way Task Manager does it: CPU-seconds used between two samples / elapsed time.

Usage:
    python process_watch.py                       # one snapshot (2 s sample), top 10
    python process_watch.py --sort mem --top 15
    python process_watch.py --watch 5 --cpu-alert 50 --mem-alert 1500    # refresh every 5 s, alert
    python process_watch.py --name chrome         # total CPU/RAM of all processes with that name
"""

import argparse
import csv
import io
import os
import platform
import subprocess
import time
from collections import defaultdict

IS_WINDOWS = platform.system() == "Windows"
CORES = os.cpu_count() or 1


def sample() -> dict[int, dict]:
    """Return {pid: {name, cpu_seconds, mem_mb}}."""
    procs = {}
    if IS_WINDOWS:
        cmd = ["powershell", "-NoProfile", "-Command",
               "Get-Process | Select-Object Id,ProcessName,CPU,WorkingSet64 | ConvertTo-Csv -NoTypeInformation"]
        text = subprocess.run(cmd, capture_output=True, text=True, errors="replace").stdout
        for row in csv.DictReader(io.StringIO(text)):
            try:
                procs[int(row["Id"])] = {
                    "name": row["ProcessName"],
                    "cpu_seconds": float(row["CPU"] or 0),   # total processor time so far
                    "mem_mb": int(row["WorkingSet64"] or 0) / 1024 ** 2,
                }
            except (ValueError, KeyError):
                continue
    else:
        text = subprocess.run(["ps", "-eo", "pid=,rss=,time=,comm="], capture_output=True, text=True).stdout
        for line in text.splitlines():
            parts = line.split(None, 3)
            if len(parts) < 4:
                continue
            pid, rss, cputime, name = parts
            # cputime looks like [[dd-]hh:]mm:ss
            days, _, hms = cputime.rpartition("-")
            secs = 0
            for piece in hms.split(":"):
                secs = secs * 60 + int(piece)
            secs += int(days or 0) * 86400
            procs[int(pid)] = {"name": os.path.basename(name), "cpu_seconds": secs, "mem_mb": int(rss) / 1024}
    return procs


def measure(interval: float) -> list[dict]:
    a = sample()
    t0 = time.perf_counter()
    time.sleep(interval)
    b = sample()
    elapsed = time.perf_counter() - t0
    rows = []
    for pid, p in b.items():
        before = a.get(pid)
        used = p["cpu_seconds"] - before["cpu_seconds"] if before else 0
        # % of the WHOLE machine (all cores), like Task Manager's Processes tab
        rows.append({"pid": pid, "name": p["name"], "mem_mb": p["mem_mb"],
                     "cpu_pct": max(0.0, used / elapsed / CORES * 100)})
    return rows


def show(rows: list[dict], sort: str, top: int, cpu_alert: float, mem_alert: float) -> None:
    key = "cpu_pct" if sort == "cpu" else "mem_mb"
    rows = sorted(rows, key=lambda r: r[key], reverse=True)
    total_mem = sum(r["mem_mb"] for r in rows)
    print(f"{len(rows)} processes, {total_mem / 1024:.1f} GB working set total, {CORES} logical cores")
    print(f"{'PID':>7}  {'NAME':<28}{'CPU %':>7}{'MEM MB':>10}")
    for r in rows[:top]:
        flag = ""
        if r["cpu_pct"] >= cpu_alert:
            flag += "  <-- HIGH CPU"
        if r["mem_mb"] >= mem_alert:
            flag += "  <-- HIGH MEMORY"
        print(f"{r['pid']:>7}  {r['name'][:27]:<28}{r['cpu_pct']:>7.1f}{r['mem_mb']:>10.0f}{flag}")


def by_name(rows: list[dict], name: str) -> None:
    groups = defaultdict(lambda: [0, 0.0, 0.0])
    for r in rows:
        if name.lower() in r["name"].lower():
            g = groups[r["name"]]
            g[0] += 1
            g[1] += r["cpu_pct"]
            g[2] += r["mem_mb"]
    if not groups:
        print(f"No process matching '{name}'.")
    for n, (count, cpu, mem) in groups.items():
        print(f"{n}: {count} processes, {cpu:.1f}% CPU, {mem:,.0f} MB RAM total")
    print("\nTo stop them:  Stop-Process -Name <name>   |   pkill <name>   (SIGTERM first, -9 only if stuck)")


def main() -> None:
    p = argparse.ArgumentParser(description="Top processes with alerts.")
    p.add_argument("--sort", choices=["cpu", "mem"], default="cpu")
    p.add_argument("--top", type=int, default=10)
    p.add_argument("--interval", type=float, default=2.0, help="CPU sample window in seconds")
    p.add_argument("--watch", type=float, help="repeat every N seconds until Ctrl+C")
    p.add_argument("--cpu-alert", type=float, default=50.0)
    p.add_argument("--mem-alert", type=float, default=2000.0, help="MB")
    p.add_argument("--name", help="aggregate all processes whose name contains this")
    args = p.parse_args()

    try:
        while True:
            rows = measure(args.interval)
            print(f"\n=== {time.strftime('%H:%M:%S')} ===")
            if args.name:
                by_name(rows, args.name)
            else:
                show(rows, args.sort, args.top, args.cpu_alert, args.mem_alert)
            if not args.watch:
                break
            time.sleep(max(0, args.watch - args.interval))
    except KeyboardInterrupt:
        print("\nstopped")


if __name__ == "__main__":
    main()
