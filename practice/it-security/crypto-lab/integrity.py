"""
integrity.py - hashing for integrity: avalanche effect, download verification, a file integrity
monitor, and HMAC (integrity + authenticity with a shared key).

Usage:
    python integrity.py hash "hello"                     # SHA-256 / SHA-1 / MD5 of a string
    python integrity.py avalanche "hello" "hellp"        # one character -> ~half the bits change
    python integrity.py file <path> [expected-sha256]    # verify a download like Get-FileHash
    python integrity.py baseline <folder>                # record hashes of every file (FIM baseline)
    python integrity.py check <folder>                   # report added / modified / deleted files
    python integrity.py hmac-demo                        # why a plain hash isn't enough over a network
"""

import hashlib
import hmac
import json
import secrets
import sys
from pathlib import Path

BASELINE = ".integrity-baseline.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def cmd_hash(text: str) -> None:
    data = text.encode()
    for name in ("md5", "sha1", "sha256", "sha512"):
        d = hashlib.new(name, data).hexdigest()
        status = {"md5": "BROKEN (collisions)", "sha1": "BROKEN (collision 2017)"}.get(name, "ok")
        print(f"{name:<7}{len(d) * 4:>4} bits  {d[:64]}{'...' if len(d) > 64 else ''}  [{status}]")
    print("\nSame input -> same hash, every time, on every computer. That's what makes it useful for checking.")


def cmd_avalanche(a: str, b: str) -> None:
    ha, hb = hashlib.sha256(a.encode()).digest(), hashlib.sha256(b.encode()).digest()
    diff = sum(bin(x ^ y).count("1") for x, y in zip(ha, hb))
    print(f"{a!r:<12} {ha.hex()}")
    print(f"{b!r:<12} {hb.hex()}")
    print(f"\n{diff} of 256 bits differ ({diff / 256:.0%}). A good hash changes ~50% of bits for any change -")
    print("so you can't 'tweak' a file and keep its hash, or learn anything about the input from the output.")


def cmd_file(path: str, expected: str | None) -> None:
    digest = sha256_file(Path(path))
    print(f"SHA256  {digest}  {path}")
    if expected:
        ok = hmac.compare_digest(digest, expected.lower().strip())
        print("MATCH - file is exactly what the publisher released" if ok
              else "MISMATCH - corrupted download or tampered file. Do NOT run it.")
    print("Same as:  Get-FileHash <file> -Algorithm SHA256   |   certutil -hashfile <file> SHA256   |   sha256sum <file>")


def cmd_baseline(folder: str) -> None:
    root = Path(folder)
    hashes = {p.relative_to(root).as_posix(): sha256_file(p)
              for p in sorted(root.rglob("*")) if p.is_file() and p.name != BASELINE}
    (root / BASELINE).write_text(json.dumps(hashes, indent=1))
    print(f"Baseline of {len(hashes)} files saved to {root / BASELINE}")
    print("(A real FIM stores the baseline somewhere the attacker can't write to, or signs it.)")


def cmd_check(folder: str) -> None:
    root = Path(folder)
    base = json.loads((root / BASELINE).read_text())
    now = {p.relative_to(root).as_posix(): sha256_file(p)
           for p in sorted(root.rglob("*")) if p.is_file() and p.name != BASELINE}
    added = sorted(set(now) - set(base))
    deleted = sorted(set(base) - set(now))
    modified = sorted(f for f in set(now) & set(base) if now[f] != base[f])
    for f in modified:
        print(f"  MODIFIED  {f}")
    for f in added:
        print(f"  ADDED     {f}")
    for f in deleted:
        print(f"  DELETED   {f}")
    print(f"{len(modified)} modified, {len(added)} added, {len(deleted)} deleted"
          + ("  - no changes since baseline" if not (modified or added or deleted) else ""))


def cmd_hmac_demo() -> None:
    message = b"PAY 100 GBP TO ACCOUNT 12345678"
    print(f"Original message: {message.decode()}\n")

    print("1) Sending message + plain SHA-256:")
    tampered = b"PAY 9000 GBP TO ACCOUNT 87654321"
    forged_hash = hashlib.sha256(tampered).hexdigest()
    print(f"   attacker changes it to {tampered.decode()!r} and simply recomputes the hash")
    print(f"   receiver checks: sha256(msg) == hash ? {hashlib.sha256(tampered).hexdigest() == forged_hash}"
          "  <- passes! A plain hash proves nothing if the attacker can replace it too.\n")

    key = secrets.token_bytes(32)  # shared secret between sender and receiver only
    tag = hmac.new(key, message, hashlib.sha256).hexdigest()
    print("2) Sending message + HMAC-SHA256 (needs a secret key the attacker doesn't have):")
    print(f"   tag = {tag[:32]}...")
    attacker_tag = hmac.new(secrets.token_bytes(32), tampered, hashlib.sha256).hexdigest()  # wrong key
    ok_original = hmac.compare_digest(hmac.new(key, message, hashlib.sha256).hexdigest(), tag)
    ok_tampered = hmac.compare_digest(hmac.new(key, tampered, hashlib.sha256).hexdigest(), attacker_tag)
    print(f"   receiver verifies original  -> {ok_original}")
    print(f"   receiver verifies tampered  -> {ok_tampered}  <- forgery detected")
    print("\nhmac.compare_digest is constant-time, so an attacker can't learn the tag byte-by-byte from timing.")


def main() -> None:
    a = sys.argv[1:]
    if not a:
        raise SystemExit(__doc__)
    cmds = {
        "hash": lambda: cmd_hash(a[1]),
        "avalanche": lambda: cmd_avalanche(a[1], a[2]),
        "file": lambda: cmd_file(a[1], a[2] if len(a) > 2 else None),
        "baseline": lambda: cmd_baseline(a[1]),
        "check": lambda: cmd_check(a[1]),
        "hmac-demo": cmd_hmac_demo,
    }
    if a[0] not in cmds:
        raise SystemExit(__doc__)
    cmds[a[0]]()


if __name__ == "__main__":
    main()
