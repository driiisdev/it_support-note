"""
perm_tool.py - understand and audit file permissions.

Usage:
    python perm_tool.py explain 755            # octal -> rwx, and what it means for a file vs a directory
    python perm_tool.py explain rwxr-x---      # symbolic -> octal
    python perm_tool.py explain 4755           # special bits (setuid/setgid/sticky)
    python perm_tool.py audit <folder>         # find risky permissions under a folder
    python perm_tool.py demo                   # build a sample folder with bad permissions and audit it

audit:
    Linux/macOS: world-writable files/dirs, setuid/setgid binaries, private keys readable by others.
    Windows:     ACL entries giving Everyone / Users / Authenticated Users write-or-more (via icacls).
"""

import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

IS_WINDOWS = sys.platform == "win32"


def octal_to_symbolic(mode: int) -> str:
    out = ""
    for who, shift in (("owner", 6), ("group", 3), ("other", 0)):
        bits = (mode >> shift) & 7
        out += ("r" if bits & 4 else "-") + ("w" if bits & 2 else "-") + ("x" if bits & 1 else "-")
    s = list(out)
    if mode & 0o4000:
        s[2] = "s" if s[2] == "x" else "S"
    if mode & 0o2000:
        s[5] = "s" if s[5] == "x" else "S"
    if mode & 0o1000:
        s[8] = "t" if s[8] == "x" else "T"
    return "".join(s)


def symbolic_to_octal(sym: str) -> int:
    if not re.fullmatch(r"[r-][w-][xsS-][r-][w-][xsS-][r-][w-][xtT-]", sym):
        raise SystemExit("symbolic form must look like rwxr-x--- (9 characters)")
    mode = 0
    for i, ch in enumerate(sym):
        if ch in "rwxst":
            mode |= 1 << (8 - i)
    if sym[2] in "sS":
        mode |= 0o4000
    if sym[5] in "sS":
        mode |= 0o2000
    if sym[8] in "tT":
        mode |= 0o1000
    return mode


def explain(arg: str) -> None:
    mode = int(arg, 8) if arg.isdigit() else symbolic_to_octal(arg)
    sym = octal_to_symbolic(mode)
    print(f"{mode:04o}  =  {sym}\n")
    meaning_file = {4: "read", 2: "write (change contents)", 1: "execute (run it)"}
    meaning_dir = {4: "list names", 2: "create/delete/rename entries", 1: "enter it (cd) / access entries"}
    for who, shift in (("owner", 6), ("group", 3), ("others", 0)):
        bits = (mode >> shift) & 7
        f = ", ".join(v for k, v in meaning_file.items() if bits & k) or "nothing"
        d = ", ".join(v for k, v in meaning_dir.items() if bits & k) or "nothing"
        print(f"  {who:<7} {bits} = {'+'.join(str(k) for k in (4, 2, 1) if bits & k) or '0':<6}"
              f" file: {f:<38} dir: {d}")
    if mode & 0o4000:
        print("  setuid : runs as the FILE OWNER (e.g. /usr/bin/passwd runs as root). Risky on custom binaries.")
    if mode & 0o2000:
        print("  setgid : runs as the file's group; on a directory, new files inherit the directory's group.")
    if mode & 0o1000:
        print("  sticky : in a shared directory, users can delete only their own files (/tmp is 1777).")
    if mode & 0o002:
        print("\n  WARNING: world-writable - any user on the system can modify this.")
    print(f"\n  chmod {mode:o} <file>    (or symbolic: chmod u=...,g=...,o=...)")


# --------------------------------------------------------------------------- audit
def audit_posix(root: Path) -> list[str]:
    findings = []
    for path in [root, *root.rglob("*")]:
        try:
            st = path.lstat()
        except OSError:
            continue
        if stat.S_ISLNK(st.st_mode):
            continue
        mode = stat.S_IMODE(st.st_mode)
        kind = "dir " if path.is_dir() else "file"
        if mode & 0o002 and not (path.is_dir() and mode & 0o1000):
            findings.append(f"[HIGH] {kind} {path} is world-writable ({mode:04o}) -> chmod o-w")
        if mode & 0o4000 and path.is_file():
            findings.append(f"[MED ] file {path} is setuid ({mode:04o}) - should it be?")
        if mode & 0o2000 and path.is_file():
            findings.append(f"[LOW ] file {path} is setgid ({mode:04o})")
        if path.is_file() and re.search(r"(id_rsa|id_ed25519|\.pem|\.key)$", path.name) and mode & 0o077:
            findings.append(f"[HIGH] private key {path} readable by group/others ({mode:04o}) -> chmod 600")
    return findings


RISKY_PRINCIPALS = ("Everyone", "BUILTIN\\Users", "NT AUTHORITY\\Authenticated Users", "Users")
WRITE_RIGHTS = ("(F)", "(M)", "(W)", "(WD)", "(AD)")  # Full, Modify, Write, write data, append data


def audit_windows(root: Path) -> list[str]:
    findings = []
    for path in [root, *root.rglob("*")]:
        out = subprocess.run(["icacls", str(path)], capture_output=True, text=True, errors="replace").stdout
        for line in out.splitlines():
            line = line.replace(str(path), "").strip()
            for principal in RISKY_PRINCIPALS:
                if line.startswith(principal + ":") and any(r in line for r in WRITE_RIGHTS):
                    inherited = " (inherited)" if "(I)" in line else ""
                    findings.append(f"[HIGH] {path}: {line}{inherited} -> broad group can write/modify")
                    break
    return findings


def audit(folder: str) -> None:
    root = Path(folder).resolve()
    if not root.exists():
        raise SystemExit(f"{root} does not exist")
    findings = audit_windows(root) if IS_WINDOWS else audit_posix(root)
    print(f"Audit of {root} ({'NTFS ACLs via icacls' if IS_WINDOWS else 'POSIX mode bits'})\n")
    for f in findings:
        print("  " + f)
    print(f"\n{len(findings)} finding(s).")


def demo() -> None:
    root = Path(tempfile.mkdtemp(prefix="perm-demo-"))
    (root / "public").mkdir()
    (root / "finance").mkdir()
    (root / "finance" / "salaries.xlsx").write_text("secret")
    (root / ".ssh").mkdir()
    (root / ".ssh" / "id_ed25519").write_text("-----BEGIN OPENSSH PRIVATE KEY-----\nfake\n")
    (root / "tool").write_text("#!/bin/sh\necho hi\n")
    try:
        if IS_WINDOWS:
            # Give Everyone Modify on finance - the classic "just make it work" mistake
            subprocess.run(["icacls", str(root / "finance"), "/grant", "Everyone:(OI)(CI)M"],
                           capture_output=True, check=True)
        else:
            os.chmod(root / "finance", 0o777)
            os.chmod(root / "finance" / "salaries.xlsx", 0o666)
            os.chmod(root / ".ssh" / "id_ed25519", 0o644)
            os.chmod(root / "tool", 0o4755)
        audit(str(root))
    finally:
        shutil.rmtree(root, ignore_errors=True)
        print(f"(demo folder {root} removed)")


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    cmd = sys.argv[1]
    if cmd == "explain" and len(sys.argv) == 3:
        explain(sys.argv[2])
    elif cmd == "audit" and len(sys.argv) == 3:
        audit(sys.argv[2])
    elif cmd == "demo":
        demo()
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
