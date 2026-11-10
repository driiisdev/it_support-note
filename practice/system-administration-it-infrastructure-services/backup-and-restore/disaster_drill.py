"""
disaster_drill.py - a complete backup/restore drill, start to finish, in a throwaway folder.

    Day 1  create sample "company data", FULL backup
    Day 2  edit a file, add a file           -> INCREMENTAL
    Day 3  delete a file, add a file         -> INCREMENTAL
    Disaster: "ransomware" scrambles every file and drops a ransom note
    Recovery: verify backups -> restore latest to a clean folder -> prove every file matches
    Bonus:   restore Day 1 (point-in-time) and show a backup copy getting corrupted -> verify catches it

Usage:
    python disaster_drill.py          # everything happens under ./drill/ (deleted and recreated each run)
"""

import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
DRILL = HERE / "drill"
DATA = DRILL / "company-data"
STORE = DRILL / "backup-store"   # in real life: a different disk / NAS / cloud, ideally immutable
BACKUP = [sys.executable, str(HERE / "backup.py")]


def run(*args: str) -> str:
    out = subprocess.run(BACKUP + list(args), capture_output=True, text=True)
    text = (out.stdout + out.stderr).strip()
    print("   $ backup.py " + " ".join(Path(a).name if "drill" in a else a for a in args))
    for line in text.splitlines():
        print("     " + line)
    return text


def step(title: str) -> None:
    print(f"\n=== {title} " + "=" * (58 - len(title)))
    time.sleep(1.1)  # backup names use second resolution


def main() -> None:
    shutil.rmtree(DRILL, ignore_errors=True)
    (DATA / "finance").mkdir(parents=True)
    (DATA / "hr").mkdir()
    (DATA / "finance" / "budget-2026.csv").write_text("dept,amount\nIT,120000\nHR,80000\n")
    (DATA / "finance" / "invoices.txt").write_text("INV-1001 paid\nINV-1002 due\n")
    (DATA / "hr" / "staff-list.csv").write_text("name,role\nAmina,Accountant\nTunde,Analyst\n")
    (DATA / "readme.txt").write_text("Shared drive - do not store personal files here.\n")

    step("Day 1: full backup")
    run("full", str(DATA), str(STORE))

    step("Day 2: edit budget, add a contract -> incremental")
    (DATA / "finance" / "budget-2026.csv").write_text("dept,amount\nIT,135000\nHR,80000\nSales,60000\n")
    (DATA / "contract-acme.txt").write_text("Contract with ACME, signed 2026-03-05\n")
    run("incr", str(DATA), str(STORE))

    step("Day 3: invoices deleted, new hire added -> incremental")
    (DATA / "finance" / "invoices.txt").unlink()
    (DATA / "hr" / "new-hire-chen.txt").write_text("Chen Wei starts 2026-03-16\n")
    run("incr", str(DATA), str(STORE))
    run("list", str(STORE))

    step("DISASTER: ransomware encrypts the share")
    for f in DATA.rglob("*"):
        if f.is_file():
            scrambled = bytes(b ^ 0x5A for b in f.read_bytes())
            f.with_name(f.name + ".locked").write_bytes(scrambled)
            f.unlink()
    (DATA / "HOW_TO_DECRYPT.txt").write_text("Pay 2 BTC to get your files back.\n")
    print("   files on the share now:", sorted(p.name for p in DATA.rglob("*") if p.is_file()))
    print("   Response: isolate the machine, do NOT pay, check backups are clean, restore.")

    step("Recovery 1: verify the backups before trusting them")
    run("verify", str(STORE))

    step("Recovery 2: restore the latest point to a clean folder")
    restored = DRILL / "restored-latest"
    run("restore", str(STORE), "latest", str(restored))
    print("   restored files:", sorted(p.relative_to(restored).as_posix() for p in restored.rglob("*") if p.is_file()))
    print("   budget line:", (restored / "finance" / "budget-2026.csv").read_text().splitlines()[1])

    step("Bonus: point-in-time restore of Day 1")
    day1 = sorted(p.name for p in STORE.iterdir())[0]
    restored1 = DRILL / "restored-day1"
    run("restore", str(STORE), day1, str(restored1))
    print("   Day 1 budget line:", (restored1 / "finance" / "budget-2026.csv").read_text().splitlines()[1],
          "| invoices.txt present:", (restored1 / "finance" / "invoices.txt").exists())

    step("Bonus: a backup copy silently corrupts (bit rot)")
    victim = next((STORE / day1 / "files").rglob("readme.txt"))
    victim.write_text("Shared drive - do not store personal files here!\n")  # one character changed
    run("verify", str(STORE))
    print("\nLesson: backups you never verify or test-restore are hopes, not backups.")
    print(f"Drill files left in {DRILL} for you to inspect (deleted on the next run).")


if __name__ == "__main__":
    main()
