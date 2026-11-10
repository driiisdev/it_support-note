"""
auth.py - the 3 As in one small system.

  Authentication  salted PBKDF2 passwords + TOTP second factor + lockout after repeated failures
  Authorization   role-based access control (roles.json) - least privilege, deny by default
  Accounting      append-only audit log (audit.log, JSON lines) + a report of what happened

State lives in users.json and audit.log next to this file (both gitignored). Fictional users only.

Usage:
    python auth.py demo                              # scripted walkthrough of everything below
    python auth.py register <user>                   # asks for a password
    python auth.py enroll-mfa <user>                 # prints a TOTP secret for an authenticator app
    python auth.py login <user>                      # password, then TOTP code if enrolled
    python auth.py can <user> <permission>           # e.g. can amina finance-share:write
    python auth.py unlock <user> --by <helpdesk-user>
    python auth.py report                            # accounting: failed logins, lockouts, denials
"""

import argparse
import datetime as dt
import getpass
import hashlib
import hmac
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

import totp

HERE = Path(__file__).parent
USERS = HERE / "users.json"
AUDIT = HERE / "audit.log"
ROLES = json.loads((HERE / "roles.json").read_text())
ITERATIONS = 600_000
MAX_FAILS = 5
LOCK_MINUTES = 15


# ---------------------------------------------------------------- accounting
def audit(event: str, user: str, **details) -> None:
    rec = {"ts": dt.datetime.now().isoformat(timespec="seconds"), "event": event, "user": user, **details}
    with AUDIT.open("a", encoding="utf-8") as f:   # append-only; a real system ships this to a SIEM
        f.write(json.dumps(rec) + "\n")


def load() -> dict:
    return json.loads(USERS.read_text()) if USERS.exists() else {}


def save(db: dict) -> None:
    USERS.write_text(json.dumps(db, indent=1))


# ---------------------------------------------------------------- authentication
def hash_pw(password: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS).hex()


def password_policy(pw: str, user: str) -> str | None:
    if len(pw) < 12:
        return "at least 12 characters (a passphrase is easiest: three-random-words)"
    if user.lower() in pw.lower():
        return "must not contain the username"
    if pw.lower() in {"password1234", "qwertyuiop12", "123456789012", "welcome12345"}:
        return "too common"
    return None


def register(user: str, password: str) -> None:
    db = load()
    if user in db:
        sys.exit(f"{user} already exists")
    if problem := password_policy(password, user):
        sys.exit(f"Password rejected: {problem}")
    salt = os.urandom(16)
    db[user] = {"salt": salt.hex(), "hash": hash_pw(password, salt), "totp": None,
                "fails": 0, "locked_until": None}
    save(db)
    audit("user_created", user)
    print(f"Created {user} (password stored as salted PBKDF2, {ITERATIONS:,} iterations)")


def enroll(user: str) -> str:
    db = load()
    secret = totp.new_secret()
    db[user]["totp"] = secret
    save(db)
    audit("mfa_enrolled", user)
    return secret


def login(user: str, password: str, code_provider) -> bool:
    db = load()
    rec = db.get(user)
    # Same message for "no such user" and "wrong password" - don't tell attackers which usernames exist
    if rec is None:
        audit("login_failed", user, reason="unknown user")
        print("Login failed.")
        return False
    if rec["locked_until"] and time.time() < rec["locked_until"]:
        mins = (rec["locked_until"] - time.time()) / 60
        audit("login_blocked_locked", user)
        print(f"Account locked - try again in {mins:.0f} min or contact the help desk.")
        return False

    if not hmac.compare_digest(hash_pw(password, bytes.fromhex(rec["salt"])), rec["hash"]):
        rec["fails"] += 1
        reason = "bad password"
        if rec["fails"] >= MAX_FAILS:
            rec["locked_until"] = time.time() + LOCK_MINUTES * 60
            audit("account_locked", user, fails=rec["fails"])
            reason += f", LOCKED after {rec['fails']} failures"
        save(db)
        audit("login_failed", user, reason="bad password", fails=rec["fails"])
        print(f"Login failed. ({reason})")
        return False

    if rec["totp"]:  # second factor: something you HAVE (the phone holding the secret)
        code = code_provider(rec["totp"])
        if not totp.verify(totp.b32_decode(rec["totp"]), code):
            rec["fails"] += 1
            save(db)
            audit("login_failed", user, reason="bad MFA code")
            print("Login failed. (password OK, MFA code wrong - if you didn't try to log in, your password is known!)")
            return False

    rec["fails"], rec["locked_until"] = 0, None
    save(db)
    audit("login_success", user, mfa=bool(rec["totp"]))
    print(f"Welcome {user}. ({'password + TOTP' if rec['totp'] else 'password only - enroll MFA!'})")
    return True


# ---------------------------------------------------------------- authorization
def permissions(user: str) -> set[str]:
    perms = set()
    for role in ROLES["user_roles"].get(user, []):
        perms |= set(ROLES["roles"][role])
    return perms


def can(user: str, perm: str, quiet: bool = False) -> bool:
    perms = permissions(user)
    allowed = "*" in perms or perm in perms   # anything not explicitly granted is denied
    audit("authz_allowed" if allowed else "authz_denied", user, permission=perm)
    if not quiet:
        roles = ", ".join(ROLES["user_roles"].get(user, [])) or "none"
        print(f"{user} [{roles}] -> {perm}: {'ALLOWED' if allowed else 'DENIED'}")
    return allowed


def unlock(user: str, by: str) -> None:
    if not can(by, "users:unlock", quiet=True):
        print(f"{by} is not allowed to unlock accounts.")
        return
    if by == user:
        # Separation of duties: the person whose account is locked can't approve their own unlock -
        # otherwise an attacker who owns a help desk account could undo the lockout protection.
        audit("authz_denied", by, permission="users:unlock (self)")
        print(f"{by} can't unlock their own account - another help desk member must verify and do it.")
        return
    db = load()
    db[user]["fails"], db[user]["locked_until"] = 0, None
    save(db)
    audit("account_unlocked", user, by=by)
    print(f"{user} unlocked by {by} (logged - did {by} verify the caller's identity first?)")


# ---------------------------------------------------------------- reporting (accounting)
def report() -> None:
    if not AUDIT.exists():
        sys.exit("No audit log yet - run: python auth.py demo")
    events = [json.loads(l) for l in AUDIT.read_text(encoding="utf-8").splitlines() if l.strip()]
    print(f"{len(events)} audit events\n")
    print("By type:", dict(Counter(e["event"] for e in events)))
    fails = Counter(e["user"] for e in events if e["event"] == "login_failed")
    print("Failed logins per user:", dict(fails))
    for e in events:
        if e["event"] in ("account_locked", "account_unlocked", "authz_denied", "mfa_enrolled"):
            extra = {k: v for k, v in e.items() if k not in ("ts", "event", "user")}
            print(f"  {e['ts']}  {e['event']:<17} {e['user']:<8} {extra or ''}")


# ---------------------------------------------------------------- demo
def demo() -> None:
    for f in (USERS, AUDIT):
        f.unlink(missing_ok=True)

    def step(t):
        print(f"\n--- {t}")

    step("Register users (policy rejects a weak password)")
    for u, pw in (("amina", "maple-orbit-violin-42"), ("tunde", "copper-lantern-river-7"),
                  ("chen", "quiet-harbor-pencil-19")):
        register(u, pw)
    try:
        register("grace", "password1234")
    except SystemExit as e:
        print(e)

    step("Password-only login works... but is one factor")
    login("chen", "quiet-harbor-pencil-19", None)

    step("Amina enrolls MFA (TOTP)")
    secret = enroll("amina")
    print(f"secret {secret} -> {totp.otpauth_uri(secret, 'amina@example-corp.com')}")
    phone = lambda s: totp.totp(totp.b32_decode(s))   # simulates her authenticator app
    login("amina", "maple-orbit-violin-42", phone)

    step("Attacker has Amina's password (phished) but not her phone")
    login("amina", "maple-orbit-violin-42", lambda s: "123456")

    step("Brute force against tunde -> lockout after 5 failures")
    for guess in ("Password1", "Summer2026!", "tunde123", "letmein", "copper"):
        login("tunde", guess, None)
    login("tunde", "copper-lantern-river-7", None)   # right password, but locked

    step("Authorization: least privilege (RBAC)")
    can("amina", "finance-share:write")
    can("amina", "hr-share:read")
    can("chen", "users:reset-password")
    can("tunde", "users:unlock")

    step("Help desk unlock - only a role with users:unlock may do it")
    unlock("tunde", by="chen")    # HR role - no unlock permission
    unlock("tunde", by="tunde")   # help desk role, but it's his own account -> separation of duties
    unlock("tunde", by="admin")   # IT admin, after verifying tunde's identity
    login("tunde", "copper-lantern-river-7", None)

    step("Accounting: what does the audit log say?")
    report()


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    s = p.add_subparsers(dest="cmd", required=True)
    s.add_parser("demo")
    x = s.add_parser("register"); x.add_argument("user")
    x = s.add_parser("enroll-mfa"); x.add_argument("user")
    x = s.add_parser("login"); x.add_argument("user")
    x = s.add_parser("can"); x.add_argument("user"); x.add_argument("permission")
    x = s.add_parser("unlock"); x.add_argument("user"); x.add_argument("--by", required=True)
    s.add_parser("report")
    a = p.parse_args()

    if a.cmd == "demo":
        demo()
    elif a.cmd == "register":
        register(a.user, getpass.getpass("New password: "))
    elif a.cmd == "enroll-mfa":
        secret = enroll(a.user)
        print(f"Add to your authenticator app (setup key): {secret}\n{totp.otpauth_uri(secret, a.user)}")
    elif a.cmd == "login":
        login(a.user, getpass.getpass("Password: "), lambda s: input("6-digit code: ").strip())
    elif a.cmd == "can":
        can(a.user, a.permission)
    elif a.cmd == "unlock":
        unlock(a.user, a.by)
    elif a.cmd == "report":
        report()


if __name__ == "__main__":
    main()
