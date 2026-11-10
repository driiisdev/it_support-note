"""
provision.py - turn an HR new-hire CSV into reviewable directory changes: a PowerShell script for
Active Directory and an LDIF file for OpenLDAP. Nothing touches a real directory.

What it handles (the things that go wrong when people do this by hand):
  - validation: missing names, unknown departments, missing managers, bad dates
  - usernames: first initial + last name, accents stripped (José Muñoz -> jmunoz), punctuation removed,
    sAMAccountName max 20 chars, duplicates resolved (abello exists -> abello2)
  - placement: the correct OU per department -> distinguished name
  - groups: department security group + all-staff
  - safety: generated PowerShell uses -WhatIf unless you remove it

Usage:
    python provision.py                      # new-hires.csv -> out/New-ADUsers.ps1 + out/new-users.ldif
    python provision.py --domain corp.example.com --csv my.csv
"""

import argparse
import csv
import datetime as dt
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).parent

# Department -> OU path (inside OU=Users) and security group. In real life this mapping lives in a config file.
DEPARTMENTS = {
    "Finance":   {"ou": ["Finance"],           "group": "SG-Finance"},
    "IT":        {"ou": ["IT"],                "group": "SG-IT"},
    "Sales":     {"ou": ["Sales", "EMEA"],     "group": "SG-Sales"},
    "HR":        {"ou": ["HR"],                "group": "SG-HR"},
    "Marketing": {"ou": ["Marketing"],         "group": "SG-Marketing"},
}


def ascii_clean(text: str) -> str:
    """José -> Jose, Muñoz -> Munoz, O'Neill -> ONeill, Montgomery-Wellington -> MontgomeryWellington"""
    no_accents = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]", "", no_accents)


def make_username(first: str, last: str, taken: set[str]) -> str:
    base = (ascii_clean(first)[:1] + ascii_clean(last)).lower()[:18]  # leave room for a digit suffix
    candidate, n = base, 1
    while candidate in taken:
        n += 1
        candidate = f"{base}{n}"
    taken.add(candidate)
    assert len(candidate) <= 20, "sAMAccountName must be 20 characters or fewer"
    return candidate


def domain_dn(domain: str) -> str:
    return ",".join(f"DC={part}" for part in domain.split("."))


def ou_dn(dept: str, domain: str) -> str:
    # OU path is listed top-down in the mapping, but a DN is written bottom-up (most specific first)
    ous = ["Users"] + DEPARTMENTS[dept]["ou"]
    return ",".join(f"OU={ou}" for ou in reversed(ous)) + "," + domain_dn(domain)


def escape_dn(value: str) -> str:
    """Characters with special meaning in a DN must be backslash-escaped."""
    return re.sub(r'([,+"\\<>;=])', r"\\\1", value)


def validate(row: dict, line: int) -> list[str]:
    problems = []
    if not row["first"].strip() or not row["last"].strip():
        problems.append(f"line {line}: first and last name are required")
    if row["department"] not in DEPARTMENTS:
        problems.append(f"line {line}: unknown department {row['department']!r} (known: {', '.join(DEPARTMENTS)})")
    if not row["manager"].strip():
        problems.append(f"line {line}: no manager - who approves access requests? (warning, still created)")
    try:
        dt.date.fromisoformat(row["start_date"])
    except ValueError:
        problems.append(f"line {line}: start_date {row['start_date']!r} is not YYYY-MM-DD")
    return problems


def ps_quote(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"  # PowerShell single-quote escaping: ' -> ''


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--csv", default=str(HERE / "new-hires.csv"))
    p.add_argument("--existing", default=str(HERE / "existing-users.txt"))
    p.add_argument("--domain", default="corp.example.com")
    args = p.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # so names like José Muñoz print correctly on Windows

    taken ={l.strip().lower() for l in Path(args.existing).read_text(encoding="utf-8").splitlines()
             if l.strip() and not l.startswith("#")}
    with open(args.csv, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    accepted, report = [], []
    for i, row in enumerate(rows, start=2):  # line 1 is the header
        problems = validate(row, i)
        hard = [x for x in problems if "warning" not in x]
        report += problems
        if hard:
            continue
        user = make_username(row["first"], row["last"], taken)
        display = f"{row['first']} {row['last']}"
        accepted.append({**row, "sam": user, "display": display,
                         "upn": f"{user}@{args.domain}",
                         "dn": f"CN={escape_dn(display)},{ou_dn(row['department'], args.domain)}",
                         "ou": ou_dn(row["department"], args.domain),
                         "group": DEPARTMENTS[row["department"]]["group"]})

    out = HERE / "out"
    out.mkdir(exist_ok=True)

    # ---------------- PowerShell for Active Directory
    ps = [
        "# Generated by provision.py - REVIEW BEFORE RUNNING.",
        "# Runs in -WhatIf mode (shows what would happen). Remove $WhatIf = $true to apply.",
        "#Requires -Modules ActiveDirectory",
        "$WhatIf = $true",
        "",
    ]
    for u in accepted:
        ps += [
            f"# {u['display']} - {u['title']}, {u['department']}, starts {u['start_date']}",
            "$pw = Read-Host -AsSecureString " + ps_quote(f"Temp password for {u['sam']}"),
            "New-ADUser -WhatIf:$WhatIf `",
            f"  -Name {ps_quote(u['display'])} -GivenName {ps_quote(u['first'])} -Surname {ps_quote(u['last'])} `",
            f"  -SamAccountName {ps_quote(u['sam'])} -UserPrincipalName {ps_quote(u['upn'])} `",
            f"  -Title {ps_quote(u['title'])} -Department {ps_quote(u['department'])} `",
            f"  -Path {ps_quote(u['ou'])} `",
            "  -AccountPassword $pw -ChangePasswordAtLogon $true -Enabled $true",
        ]
        if u["manager"]:
            ps.append(f"Set-ADUser -WhatIf:$WhatIf {ps_quote(u['sam'])} -Manager {ps_quote(u['manager'])}")
        ps += [f"Add-ADGroupMember -WhatIf:$WhatIf -Identity {ps_quote(g)} -Members {ps_quote(u['sam'])}"
               for g in (u["group"], "SG-AllStaff")]
        ps.append("")
    (out / "New-ADUsers.ps1").write_text("\n".join(ps), encoding="utf-8-sig")

    # ---------------- LDIF for OpenLDAP (inetOrgPerson; LDAP DNs use uid= and ou=People here)
    base = ",".join(f"dc={p}" for p in args.domain.split("."))
    ldif = ["# Generated by provision.py - import with:",
            f"#   ldapadd -x -D \"cn=admin,{base}\" -W -f new-users.ldif", ""]
    for u in accepted:
        ldif += [
            f"dn: uid={u['sam']},ou={u['department']},ou=People,{base}",
            "objectClass: inetOrgPerson",
            f"uid: {u['sam']}",
            f"cn: {ascii_clean(u['first'])} {ascii_clean(u['last'])}",
            f"givenName: {ascii_clean(u['first'])}",
            f"sn: {ascii_clean(u['last'])}",
            f"title: {u['title']}",
            f"departmentNumber: {u['department']}",
            f"mail: {u['sam']}@{args.domain}",
            "",
        ]
    (out / "new-users.ldif").write_text("\n".join(ldif), encoding="utf-8")

    # ---------------- Summary
    print(f"{'USERNAME':<20}{'NAME':<36}DISTINGUISHED NAME")
    for u in accepted:
        print(f"{u['sam']:<20}{u['display'][:35]:<36}{u['dn']}")
    print(f"\n{len(accepted)} of {len(rows)} rows accepted.")
    if report:
        print("\nValidation report (send hard errors back to HR):")
        for r in report:
            print(f"  - {r}")
    print(f"\nReview: {out / 'New-ADUsers.ps1'}\n        {out / 'new-users.ldif'}")


if __name__ == "__main__":
    main()
