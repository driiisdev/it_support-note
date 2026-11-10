"""
ticket.py - a tiny help desk ticket tracker (JSON file backed).

It enforces the habits from the troubleshooting note: every ticket records impact, symptoms,
what was tried, root cause, and fix - so the next person never starts from zero.

Usage:
    python ticket.py new                       # interactive: create a ticket
    python ticket.py list [--all]              # open tickets (or all)
    python ticket.py show 3                    # full history of ticket #3
    python ticket.py note 3 "Restarted Outlook - no change"
    python ticket.py escalate 3 "Needs Exchange admin"
    python ticket.py close 3                   # asks for root cause + fix (required)
    python ticket.py report                    # counts by status / category, avg time to close
    python ticket.py demo                      # load sample tickets to play with
"""

import argparse
import datetime as dt
import json
import sys
from collections import Counter
from pathlib import Path

DB = Path(__file__).parent / "tickets.json"
CATEGORIES = ["hardware", "software", "network", "account", "security", "other"]
PRIORITIES = {
    "P1": "outage - many users / business stopped",
    "P2": "one user fully blocked, or many degraded",
    "P3": "one user degraded, workaround exists",
    "P4": "request / question",
}


def now() -> str:
    return dt.datetime.now().isoformat(timespec="minutes")


def load() -> list[dict]:
    if DB.exists():
        return json.loads(DB.read_text(encoding="utf-8"))
    return []


def save(tickets: list[dict]) -> None:
    DB.write_text(json.dumps(tickets, indent=2), encoding="utf-8")


def find(tickets: list[dict], tid: int) -> dict:
    for t in tickets:
        if t["id"] == tid:
            return t
    sys.exit(f"No ticket #{tid}")


def ask(prompt: str, required: bool = True, choices: list[str] | None = None) -> str:
    while True:
        hint = f" [{'/'.join(choices)}]" if choices else ""
        value = input(f"{prompt}{hint}: ").strip()
        if choices and value not in choices:
            print(f"  choose one of: {', '.join(choices)}")
            continue
        if value or not required:
            return value
        print("  required - a ticket without this is hard for the next person to pick up")


def cmd_new(args) -> None:
    tickets = load()
    print("Priority guide:")
    for k, v in PRIORITIES.items():
        print(f"  {k}: {v}")
    t = {
        "id": max((x["id"] for x in tickets), default=0) + 1,
        "title": ask("Short title (symptom + who)"),
        "requester": ask("Requester"),
        "category": ask("Category", choices=CATEGORIES),
        "priority": ask("Priority", choices=list(PRIORITIES)),
        "impact": ask("Impact (who/how many affected?)"),
        "symptoms": ask("Symptoms / exact error message"),
        "status": "open",
        "opened": now(),
        "history": [],
    }
    tickets.append(t)
    save(tickets)
    print(f"Created ticket #{t['id']}")


def add_history(t: dict, kind: str, text: str) -> None:
    t["history"].append({"at": now(), "type": kind, "text": text})


def cmd_note(args) -> None:
    tickets = load()
    t = find(tickets, args.id)
    add_history(t, "tried", args.text)
    save(tickets)
    print(f"#{t['id']}: note added")


def cmd_escalate(args) -> None:
    tickets = load()
    t = find(tickets, args.id)
    t["status"] = "escalated"
    add_history(t, "escalated", args.reason)
    save(tickets)
    print(f"#{t['id']} escalated. Everything tried so far travels with it:")
    for h in t["history"]:
        print(f"  - {h['text']}")


def cmd_close(args) -> None:
    tickets = load()
    t = find(tickets, args.id)
    t["root_cause"] = args.cause or ask("Root cause (why did it happen?)")
    t["fix"] = args.fix or ask("Fix applied")
    t["status"] = "closed"
    t["closed"] = now()
    add_history(t, "closed", f"Cause: {t['root_cause']} | Fix: {t['fix']}")
    save(tickets)
    print(f"#{t['id']} closed. Consider a KB article if this could happen again (see kb-template.md).")


def cmd_list(args) -> None:
    tickets = load()
    shown = [t for t in tickets if args.all or t["status"] != "closed"]
    order = {"P1": 0, "P2": 1, "P3": 2, "P4": 3}
    shown.sort(key=lambda t: (t["status"] == "closed", order[t["priority"]], t["opened"]))
    print(f"{'#':>3}  {'PRI':<4}{'STATUS':<11}{'CATEGORY':<10}{'OPENED':<18}TITLE")
    for t in shown:
        print(f"{t['id']:>3}  {t['priority']:<4}{t['status']:<11}{t['category']:<10}{t['opened']:<18}{t['title']}")
    if not shown:
        print("  (nothing open - nice)")


def cmd_show(args) -> None:
    t = find(load(), args.id)
    print(f"Ticket #{t['id']}: {t['title']}")
    for field in ("requester", "category", "priority", "status", "opened", "impact", "symptoms",
                  "root_cause", "fix", "closed"):
        if field in t:
            print(f"  {field:<11}: {t[field]}")
    print("  history    :")
    for h in t["history"]:
        print(f"    {h['at']}  [{h['type']}] {h['text']}")


def cmd_report(args) -> None:
    tickets = load()
    if not tickets:
        sys.exit("No tickets yet - try: python ticket.py demo")
    print("By status  :", dict(Counter(t["status"] for t in tickets)))
    print("By category:", dict(Counter(t["category"] for t in tickets)))
    closed = [t for t in tickets if t["status"] == "closed"]
    if closed:
        hours = [(dt.datetime.fromisoformat(t["closed"]) - dt.datetime.fromisoformat(t["opened"]))
                 .total_seconds() / 3600 for t in closed]
        print(f"Avg time to close: {sum(hours) / len(hours):.1f} h over {len(closed)} tickets")
    causes = Counter(t.get("root_cause", "").lower() for t in closed)
    repeat = [c for c, n in causes.items() if n > 1 and c]
    if repeat:
        print("Repeat root causes (write a KB article / fix permanently):", repeat)


def cmd_demo(args) -> None:
    sample = Path(__file__).parent / "sample-tickets.json"
    DB.write_text(sample.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Loaded sample tickets into {DB.name}. Try: python ticket.py list --all")


def main() -> None:
    p = argparse.ArgumentParser(description="Tiny help desk ticket tracker.")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("new").set_defaults(fn=cmd_new)
    lp = sub.add_parser("list")
    lp.add_argument("--all", action="store_true")
    lp.set_defaults(fn=cmd_list)
    sp = sub.add_parser("show")
    sp.add_argument("id", type=int)
    sp.set_defaults(fn=cmd_show)
    np_ = sub.add_parser("note")
    np_.add_argument("id", type=int)
    np_.add_argument("text")
    np_.set_defaults(fn=cmd_note)
    ep = sub.add_parser("escalate")
    ep.add_argument("id", type=int)
    ep.add_argument("reason")
    ep.set_defaults(fn=cmd_escalate)
    cp = sub.add_parser("close")
    cp.add_argument("id", type=int)
    cp.add_argument("--cause")
    cp.add_argument("--fix")
    cp.set_defaults(fn=cmd_close)
    sub.add_parser("report").set_defaults(fn=cmd_report)
    sub.add_parser("demo").set_defaults(fn=cmd_demo)
    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
