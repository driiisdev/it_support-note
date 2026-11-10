"""
passwords.py - why password storage needs SALT and a SLOW hash.

Simulates a leaked user table three ways and attacks each with a small "common passwords" list:
  1. unsalted SHA-256       -> a precomputed (rainbow-style) lookup table cracks it instantly,
                               and identical passwords have identical hashes
  2. salted SHA-256         -> lookup table useless, but each guess is still extremely cheap
  3. salted PBKDF2 (600k)   -> each guess costs real time; brute force becomes expensive

All passwords and users are fictional. Standard library only.

Usage:
    python passwords.py
"""

import hashlib
import hmac
import os
import time

USERS = {"amina": "Summer2026!", "tunde": "password123", "chen": "correct-horse-battery-staple",
         "sara": "password123", "grace": "Qw3rty!"}
# A tiny stand-in for real leaked-password lists (which have billions of entries)
COMMON = ["123456", "password", "password123", "qwerty", "Qw3rty!", "letmein", "Summer2026!",
          "Winter2025!", "iloveyou", "admin", "welcome1", "football"]
PBKDF2_ITERATIONS = 600_000  # OWASP's 2023+ recommendation for PBKDF2-HMAC-SHA256


def pbkdf2(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)


def main() -> None:
    print("=== 1. Unsalted SHA-256 (how NOT to store passwords) ===")
    table1 = {u: hashlib.sha256(p.encode()).hexdigest() for u, p in USERS.items()}
    for u, h in table1.items():
        print(f"  {u:<6} {h[:40]}...")
    print("  Notice tunde and sara have the SAME hash -> same password, visible without cracking anything.\n")

    t = time.perf_counter()
    rainbow = {hashlib.sha256(p.encode()).hexdigest(): p for p in COMMON}  # attacker builds this once, reuses forever
    cracked = {u: rainbow[h] for u, h in table1.items() if h in rainbow}
    print(f"  Lookup-table attack: cracked {len(cracked)}/{len(USERS)} in {(time.perf_counter() - t) * 1000:.2f} ms ->",
          ", ".join(f"{u}={p}" for u, p in cracked.items()))

    print("\n=== 2. Salted SHA-256 ===")
    table2 = {}
    for u, p in USERS.items():
        salt = os.urandom(16)
        table2[u] = (salt, hashlib.sha256(salt + p.encode()).hexdigest())
    print(f"  tunde: salt {table2['tunde'][0].hex()[:12]}... hash {table2['tunde'][1][:24]}...")
    print(f"  sara : salt {table2['sara'][0].hex()[:12]}... hash {table2['sara'][1][:24]}...  <- same password, different hash")
    print(f"  Precomputed table hits: {sum(h in rainbow for _, h in table2.values())}  (salt makes it useless)")
    t = time.perf_counter()
    cracked = {u: g for u, (s, h) in table2.items() for g in COMMON if hashlib.sha256(s + g.encode()).hexdigest() == h}
    elapsed = time.perf_counter() - t
    guesses = len(USERS) * len(COMMON)
    print(f"  ...but per-user guessing still cracked {len(cracked)}/{len(USERS)} in {elapsed * 1000:.2f} ms "
          f"(~{guesses / elapsed:,.0f} guesses/s on ONE CPU core; GPUs do billions)")

    print(f"\n=== 3. Salted PBKDF2-HMAC-SHA256, {PBKDF2_ITERATIONS:,} iterations ===")
    t = time.perf_counter()
    salt = os.urandom(16)
    stored = pbkdf2(USERS["chen"], salt)
    one = time.perf_counter() - t
    print(f"  one hash takes {one * 1000:.0f} ms - fine for a login, painful for an attacker")
    print(f"  the same {guesses} guesses would take ~{guesses * one:.1f} s instead of milliseconds;")
    print(f"  a 1-billion-word list would take ~{1e9 * one / 86400 / 365:,.0f} CPU-years per user")

    print("\n  Verifying a login (what the server does):")
    for attempt in ("correct-horse-battery-staple", "Correct-horse-battery-staple"):
        ok = hmac.compare_digest(pbkdf2(attempt, salt), stored)
        print(f"    {attempt:<30} -> {'ACCEPT' if ok else 'REJECT'}")

    print("\nTakeaways: never store plaintext or fast unsalted hashes; use bcrypt / scrypt / Argon2 / PBKDF2")
    print("with a unique salt per user. And chen's long passphrase isn't in ANY list - length beats complexity.")


if __name__ == "__main__":
    main()
