"""
fleet_report.py - merge many inventory JSON files (one per PC) into one CSV + a health summary.

In a real company each PC would run inventory.py at login (or via a management tool) and drop
its JSON on a file share; this script is what the IT team runs to see the whole fleet.

Usage:
    python fleet_report.py                       # reads reports/*.json and sample-fleet/*.json
    python fleet_report.py path/to/folder ...    # custom folders
"""

import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent


def load(folders: list[Path]) -> list[dict]:
    machines = []
    for folder in folders:
        for f in sorted(folder.glob("*.json")):
            if f.name.endswith("-full.json"):  # skip the PowerShell deep reports
                continue
            try:
                machines.append(json.loads(f.read_text(encoding="utf-8-sig")))
            except (json.JSONDecodeError, OSError) as e:
                print(f"skipping {f}: {e}")
    return machines


def main() -> None:
    folders = [Path(a) for a in sys.argv[1:]] or [HERE / "reports", HERE / "sample-fleet"]
    machines = load([f for f in folders if f.exists()])
    if not machines:
        sys.exit("No inventory JSON found. Run inventory.py first.")

    rows = []
    for m in machines:
        system_disk = m["disks"][0] if m["disks"] else {}
        rows.append({
            "hostname": m["hostname"],
            "user": m["user"],
            "os": f"{m['os']['system']} {m['os']['release']}",
            "cpu": m["cpu"]["model"],
            "ram_gb": m["ram_gb"],
            "system_disk_used_pct": system_disk.get("used_pct"),
            "uptime_hours": m["uptime_hours"],
            "warnings": len(m.get("warnings", [])),
        })

    out = HERE / "fleet.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"{'HOST':<14}{'USER':<10}{'OS':<14}{'RAM':>6}{'DISK%':>7}{'UP(h)':>8}  WARNINGS")
    for r, m in zip(rows, machines):
        print(f"{r['hostname'][:13]:<14}{r['user'][:9]:<10}{r['os'][:13]:<14}{r['ram_gb'] or '-':>6}"
              f"{r['system_disk_used_pct'] or '-':>7}{r['uptime_hours'] or '-':>8}  {r['warnings']}")
        for w in m.get("warnings", []):
            print(f"{'':<16}- {w}")

    needs_attention = sum(1 for r in rows if r["warnings"])
    print(f"\n{len(rows)} machines, {needs_attention} need attention. CSV -> {out}")


if __name__ == "__main__":
    main()
