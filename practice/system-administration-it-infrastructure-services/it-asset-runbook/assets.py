"""
assets.py - a small IT asset inventory (CSV-backed) that follows the hardware lifecycle:
procurement -> in-stock -> deployed -> in-repair -> retired.

Usage:
    python assets.py list [--status deployed] [--type laptop]
    python assets.py show IT-0003
    python assets.py add laptop "Dell Latitude 5450" ABC1234 --warranty-years 3
    python assets.py assign IT-0005 new.hire --location HQ-3F
    python assets.py return IT-0002 "laptop refresh"          # back to in-stock, unassigned
    python assets.py repair IT-0001 "battery swelling"
    python assets.py retire IT-0004 "wiped, cert #D-4480"
    python assets.py warranty [--days 90]                      # expiring / expired warranties
    python assets.py report                                    # counts by status / type, who has what
"""

import argparse
import csv
import datetime as dt
import sys
from collections import Counter
from pathlib import Path

DB = Path(__file__).parent / "assets.csv"
FIELDS = ["asset_tag", "type", "model", "serial", "status", "assigned_to", "location",
          "purchased", "warranty_end", "notes"]
STATUSES = ["in-stock", "deployed", "in-repair", "retired"]
TODAY = dt.date.today()


def load() -> list[dict]:
    with DB.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save(rows: list[dict]) -> None:
    tmp = DB.with_suffix(".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    tmp.replace(DB)  # write-then-rename: a crash mid-write can't corrupt the inventory


def get(rows: list[dict], tag: str) -> dict:
    for r in rows:
        if r["asset_tag"].upper() == tag.upper():
            return r
    sys.exit(f"No asset {tag}")


def log_note(r: dict, text: str) -> None:
    entry = f"{TODAY.isoformat()}: {text}"
    r["notes"] = f"{r['notes']} | {entry}" if r["notes"] else entry


def table(rows: list[dict]) -> None:
    print(f"{'TAG':<9}{'TYPE':<9}{'MODEL':<24}{'STATUS':<11}{'ASSIGNED':<16}{'LOCATION':<20}{'WARRANTY'}")
    for r in rows:
        print(f"{r['asset_tag']:<9}{r['type']:<9}{r['model'][:23]:<24}{r['status']:<11}"
              f"{r['assigned_to'][:15]:<16}{r['location'][:19]:<20}{r['warranty_end']}")
    print(f"({len(rows)} assets)")


def cmd_list(a) -> None:
    rows = [r for r in load() if (not a.status or r["status"] == a.status) and (not a.type or r["type"] == a.type)]
    table(rows)


def cmd_show(a) -> None:
    r = get(load(), a.tag)
    for k in FIELDS:
        print(f"{k:<13}: {r[k]}")


def cmd_add(a) -> None:
    rows = load()
    if any(r["serial"].upper() == a.serial.upper() for r in rows):
        sys.exit(f"Serial {a.serial} already in inventory - duplicate?")
    next_num = max(int(r["asset_tag"].split("-")[1]) for r in rows) + 1
    purchased = TODAY
    warranty = purchased.replace(year=purchased.year + a.warranty_years)
    r = {"asset_tag": f"IT-{next_num:04d}", "type": a.type, "model": a.model, "serial": a.serial,
         "status": "in-stock", "assigned_to": "", "location": "IT-store",
         "purchased": purchased.isoformat(), "warranty_end": warranty.isoformat(), "notes": ""}
    log_note(r, "received")
    rows.append(r)
    save(rows)
    print(f"Added {r['asset_tag']} - put the asset tag sticker on it now!")


def transition(tag: str, allowed_from: list[str], new_status: str, note: str, **fields) -> None:
    rows = load()
    r = get(rows, tag)
    if r["status"] not in allowed_from:
        sys.exit(f"{tag} is '{r['status']}' - can't go to '{new_status}' from there (allowed from: {allowed_from})")
    r["status"] = new_status
    r.update(fields)
    log_note(r, note)
    save(rows)
    print(f"{tag}: -> {new_status}" + (f", assigned to {fields['assigned_to']}" if fields.get("assigned_to") else ""))


def cmd_assign(a) -> None:
    transition(a.tag, ["in-stock"], "deployed", f"assigned to {a.user}",
               assigned_to=a.user, location=a.location or "")


def cmd_return(a) -> None:
    transition(a.tag, ["deployed", "in-repair"], "in-stock", f"returned: {a.reason}",
               assigned_to="", location="IT-store")


def cmd_repair(a) -> None:
    rows = load()
    r = get(rows, a.tag)
    under = r["warranty_end"] and dt.date.fromisoformat(r["warranty_end"]) >= TODAY
    print(f"Warranty {'VALID until ' + r['warranty_end'] + ' -> open a vendor claim with serial ' + r['serial'] if under else 'EXPIRED - paid repair or replace?'}")
    transition(a.tag, ["deployed", "in-stock"], "in-repair", f"repair: {a.reason}")


def cmd_retire(a) -> None:
    transition(a.tag, ["in-stock", "in-repair", "deployed"], "retired", f"retired: {a.note}",
               assigned_to="", location="disposal")
    print("Reminder: data must be securely wiped/destroyed and the certificate recorded before disposal.")


def cmd_warranty(a) -> None:
    rows = [r for r in load() if r["status"] != "retired" and r["warranty_end"]]
    soon, expired = [], []
    for r in rows:
        days = (dt.date.fromisoformat(r["warranty_end"]) - TODAY).days
        if days < 0:
            expired.append((days, r))
        elif days <= a.days:
            soon.append((days, r))
    print(f"Warranty expiring within {a.days} days:")
    for days, r in sorted(soon, key=lambda x: x[0]):
        print(f"  {r['asset_tag']}  {r['model']:<24} {r['assigned_to']:<15} in {days} days ({r['warranty_end']})")
    print("\nWarranty already expired (still in use):")
    for days, r in sorted(expired, key=lambda x: x[0]):
        print(f"  {r['asset_tag']}  {r['model']:<24} {r['status']:<10} {-days} days ago - plan replacement")


def cmd_report(a) -> None:
    rows = load()
    print("By status:", dict(Counter(r["status"] for r in rows)))
    print("By type  :", dict(Counter(r["type"] for r in rows)))
    ages = [(TODAY - dt.date.fromisoformat(r["purchased"])).days / 365 for r in rows if r["status"] == "deployed"]
    if ages:
        print(f"Deployed fleet average age: {sum(ages) / len(ages):.1f} years")
    stock = [r for r in rows if r["status"] == "in-stock" and r["type"] == "laptop"]
    print(f"Spare laptops in stock: {len(stock)}" + ("  <-- order more before the next hire wave" if len(stock) < 2 else ""))


def main() -> None:
    p = argparse.ArgumentParser(description="IT asset inventory")
    s = p.add_subparsers(dest="cmd", required=True)
    x = s.add_parser("list"); x.add_argument("--status", choices=STATUSES); x.add_argument("--type"); x.set_defaults(fn=cmd_list)
    x = s.add_parser("show"); x.add_argument("tag"); x.set_defaults(fn=cmd_show)
    x = s.add_parser("add"); x.add_argument("type"); x.add_argument("model"); x.add_argument("serial")
    x.add_argument("--warranty-years", type=int, default=3); x.set_defaults(fn=cmd_add)
    x = s.add_parser("assign"); x.add_argument("tag"); x.add_argument("user"); x.add_argument("--location"); x.set_defaults(fn=cmd_assign)
    x = s.add_parser("return"); x.add_argument("tag"); x.add_argument("reason"); x.set_defaults(fn=cmd_return)
    x = s.add_parser("repair"); x.add_argument("tag"); x.add_argument("reason"); x.set_defaults(fn=cmd_repair)
    x = s.add_parser("retire"); x.add_argument("tag"); x.add_argument("note"); x.set_defaults(fn=cmd_retire)
    x = s.add_parser("warranty"); x.add_argument("--days", type=int, default=90); x.set_defaults(fn=cmd_warranty)
    x = s.add_parser("report"); x.set_defaults(fn=cmd_report)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
