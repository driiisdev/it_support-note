"""
setup_lab.py - build a messy fake user profile to practice shell navigation on.

Creates ./lab/ (safe to delete and recreate any time):
    python setup_lab.py          # create (or recreate) the lab
    python setup_lab.py --clean  # delete it
"""

import os
import random
import shutil
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

LAB = Path(__file__).parent / "lab"
random.seed(42)  # same lab every time, so the answer key matches


def write(path: Path, text: str = "", size_kb: int = 0, days_old: int = 0) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if size_kb:
        path.write_bytes(os.urandom(size_kb * 1024))
    else:
        path.write_text(text, encoding="utf-8")
    if days_old:
        t = (datetime.now() - timedelta(days=days_old)).timestamp()
        os.utime(path, (t, t))


def make_log(path: Path, lines: int, error_every: int) -> None:
    services = ["sshd", "nginx", "backup", "cron", "spooler"]
    start = datetime(2026, 3, 1, 8, 0, 0)
    out = []
    for i in range(lines):
        ts = (start + timedelta(minutes=7 * i)).strftime("%Y-%m-%d %H:%M:%S")
        svc = services[i % len(services)]
        if i % error_every == 0:
            level, msg = "ERROR", random.choice(["disk quota exceeded", "connection refused",
                                                  "permission denied", "timeout after 30s"])
        elif i % 5 == 0:
            level, msg = "WARN", "retrying operation"
        else:
            level, msg = "INFO", "operation completed"
        out.append(f"{ts} {level:<5} {svc}: {msg}")
    write(path, "\n".join(out) + "\n")


def build() -> None:
    if LAB.exists():
        shutil.rmtree(LAB)
    home = LAB / "home" / "amina"

    # Documents, some with spaces in names (quoting practice)
    write(home / "Documents" / "Q1 Budget.xlsx", size_kb=48, days_old=40)
    write(home / "Documents" / "Q2 Budget.xlsx", size_kb=52, days_old=10)
    write(home / "Documents" / "meeting notes.txt", "Agenda:\n- printer refresh\n- VPN rollout\nTODO: renew SSL certificate\n")
    write(home / "Documents" / "Projects" / "vpn-rollout" / "plan.md", "# VPN rollout\nTODO: test on pilot group\n")
    write(home / "Documents" / "Projects" / "vpn-rollout" / "users.csv",
          "username,dept\namina,IT\ntunde,Finance\nchen,HR\nsara,Finance\n")

    # Downloads: installers, duplicates, a big old file
    write(home / "Downloads" / "setup-7zip.exe", size_kb=1500, days_old=200)
    write(home / "Downloads" / "setup-7zip (1).exe", size_kb=1500, days_old=199)
    write(home / "Downloads" / "setup-7zip (2).exe", size_kb=1500, days_old=198)
    write(home / "Downloads" / "holiday-video.mp4", size_kb=6000, days_old=400)
    write(home / "Downloads" / "invoice_8841.pdf.exe", size_kb=90, days_old=2)  # suspicious double extension
    write(home / "Downloads" / "report.PDF", size_kb=200)

    # Logs
    make_log(home / "logs" / "app.log", 300, error_every=23)
    make_log(home / "logs" / "old" / "app-2026-02.log", 200, error_every=11)
    write(home / "logs" / "debug.tmp", "temp\n" * 50)

    # Hidden files: dotfiles (hidden on Linux/macOS) + a Windows hidden attribute
    write(home / ".bashrc", "alias ll='ls -la'\nexport PATH=$PATH:~/bin\n")
    write(home / ".ssh" / "config", "Host server01\n  HostName 10.20.2.5\n  User amina\n")
    write(home / ".secret-notes.txt", "wifi password is on the sticky note (bad idea!)\n")
    hidden_win = home / "desktop.ini"
    write(hidden_win, "[.ShellClassInfo]\n")
    if sys.platform == "win32":
        subprocess.run(["attrib", "+h", str(hidden_win)], check=False)

    # A deep folder to practice cd / relative paths
    write(home / "a" / "b" / "c" / "d" / "treasure.txt", "You found it. Relative path from home: a/b/c/d/treasure.txt\n")

    print(f"Lab created at {LAB}")
    print("Open challenges.md and start in:", home)


if __name__ == "__main__":
    if "--clean" in sys.argv:
        shutil.rmtree(LAB, ignore_errors=True)
        print("Lab removed.")
    else:
        build()
