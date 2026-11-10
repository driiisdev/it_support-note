"""
auditor.py - simulate and audit a firewall rule base (first match wins, implicit deny at the end).

Audit checks:
  SHADOWED    a rule that can never match because an earlier rule with the OPPOSITE action covers it
  REDUNDANT   a rule fully covered by an earlier rule with the SAME action (harmless but clutter)
  ANY-ANY     allow from any source to any destination on any port
  EXPOSED     risky service ports (RDP, SMB, Telnet, databases...) allowed from the internet ("any")
  BROAD       allow to a whole subnet on every port
  NO OWNER    rule without an owner or comment - nobody knows why it exists
  TEMPORARY   comment says temp / TODO / remove - review it
  NO CLEANUP  last rule isn't an explicit deny-all (relying on an implicit default)

Usage:
    python auditor.py audit                         # rules.csv
    python auditor.py test                          # test-packets.csv: expected vs actual decision
    python auditor.py check tcp 198.51.100.7 10.20.0.15 3389   # which rule decides this packet?
    python auditor.py audit --rules my-rules.csv
"""

import argparse
import csv
import ipaddress
import re
from pathlib import Path

HERE = Path(__file__).parent
ANY_NET = ipaddress.ip_network("0.0.0.0/0")
RISKY = {21: "FTP", 22: "SSH", 23: "Telnet", 135: "MS-RPC", 139: "NetBIOS", 445: "SMB", 1433: "MS SQL",
         3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL", 5900: "VNC", 6379: "Redis", 27017: "MongoDB"}


def net(s: str):
    return ANY_NET if s.strip().lower() == "any" else ipaddress.ip_network(s.strip(), strict=False)


def ports(s: str) -> list[tuple[int, int]]:
    s = s.strip().lower()
    if s == "any":
        return [(0, 65535)]
    out = []
    for part in s.split(";") if ";" in s else s.split("|") if "|" in s else s.split(" "):
        if "-" in part:
            lo, hi = part.split("-")
            out.append((int(lo), int(hi)))
        elif part:
            out.append((int(part), int(part)))
    return out


def load_rules(path: Path) -> list[dict]:
    rules = []
    with path.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            r["_src"], r["_dst"], r["_ports"] = net(r["src"]), net(r["dst"]), ports(r["port"])
            r["proto"] = r["proto"].lower()
            r["action"] = r["action"].lower()
            rules.append(r)
    return rules


def proto_covers(a: str, b: str) -> bool:
    return a == "any" or a == b


def ports_cover(a: list, b: list) -> bool:
    return all(any(alo <= blo and bhi <= ahi for alo, ahi in a) for blo, bhi in b)


def covers(a: dict, b: dict) -> bool:
    """True if every packet rule b could match is also matched by rule a."""
    return (proto_covers(a["proto"], b["proto"]) and b["_src"].subnet_of(a["_src"])
            and b["_dst"].subnet_of(a["_dst"]) and ports_cover(a["_ports"], b["_ports"]))


def matches(r: dict, proto: str, src, dst, port: int) -> bool:
    return (proto_covers(r["proto"], proto) and src in r["_src"] and dst in r["_dst"]
            and any(lo <= port <= hi for lo, hi in r["_ports"]))


def decide(rules: list[dict], proto: str, src: str, dst: str, port: int) -> tuple[str, dict | None]:
    s, d = ipaddress.ip_address(src), ipaddress.ip_address(dst)
    for r in rules:
        if matches(r, proto, s, d, port):
            return r["action"], r
    return "deny", None  # implicit deny


def audit(rules: list[dict]) -> None:
    findings = []

    def add(sev, rid, text):
        findings.append((sev, int(rid), text))

    for i, b in enumerate(rules):
        for a in rules[:i]:
            if covers(a, b):
                if a["action"] != b["action"]:
                    add("HIGH", b["id"], f"SHADOWED by rule {a['id']} ({a['action']}) - rule {b['id']} ({b['action']}) "
                                         "can never match. Move it above, or narrow the earlier rule.")
                else:
                    add("LOW", b["id"], f"REDUNDANT - already covered by rule {a['id']} ({a['action']})")
                break

    for r in rules:
        if r["action"] != "allow":
            continue
        any_src = r["_src"] == ANY_NET
        if any_src and r["_dst"] == ANY_NET and r["_ports"] == [(0, 65535)]:
            add("CRIT", r["id"], "ANY-ANY allow - this rule disables the firewall")
            continue
        if any_src:
            exposed = [f"{p}/{name}" for p, name in RISKY.items()
                       if any(lo <= p <= hi for lo, hi in r["_ports"])]
            if exposed and len(exposed) <= 3:
                add("HIGH", r["id"], f"EXPOSED to the internet: {', '.join(exposed)} - put behind VPN / restrict source IPs")
            elif exposed:
                add("HIGH", r["id"], f"EXPOSED to the internet on {len(exposed)} risky ports (all ports open)")
        if r["_ports"] == [(0, 65535)] and r["_dst"].num_addresses > 1:
            add("MED", r["id"], f"BROAD - every port to all of {r['_dst']} - list only the needed ports")

    for r in rules:
        if not r["owner"].strip() or not r["comment"].strip():
            add("MED", r["id"], "NO OWNER/COMMENT - nobody can say if this rule is still needed")
        if re.search(r"\b(temp|todo|remove|test)\w*", r["comment"], re.I):
            add("MED", r["id"], f"TEMPORARY - comment says '{r['comment']}'. Review and expire it.")

    last = rules[-1]
    if not (last["action"] == "deny" and last["_src"] == ANY_NET and last["_dst"] == ANY_NET
            and last["_ports"] == [(0, 65535)] and last["proto"] == "any"):
        add("LOW", int(last["id"]) + 1, "NO CLEANUP RULE - add an explicit final 'deny any any any' "
                                        "so the default is visible and denied traffic gets logged")

    order = {"CRIT": 0, "HIGH": 1, "MED": 2, "LOW": 3}
    print(f"Audited {len(rules)} rules\n")
    for sev, rid, text in sorted(findings, key=lambda f: (order[f[0]], f[1])):
        print(f"  [{sev:<4}] rule {rid:<3} {text}")
    counts = {s: sum(1 for f in findings if f[0] == s) for s in order}
    print(f"\n{len(findings)} findings: " + ", ".join(f"{n} {s}" for s, n in counts.items() if n)
          if findings else "  No findings - rule base is clean.")


def test(rules: list[dict], path: Path) -> None:
    fails = 0
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"{'RESULT':<7}{'EXPECTED':<9}{'ACTUAL':<7}{'RULE':<6}TEST")
    for t in rows:
        action, rule = decide(rules, t["proto"], t["src"], t["dst"], int(t["port"]))
        ok = action == t["expected"]
        fails += not ok
        rid = rule["id"] if rule else "impl"
        print(f"{'PASS' if ok else 'FAIL':<7}{t['expected']:<9}{action:<7}{rid:<6}{t['description']}")
    print(f"\n{len(rows) - fails}/{len(rows)} tests pass" + ("" if not fails else " - fix the rule base and re-run"))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("cmd", choices=["audit", "test", "check"])
    p.add_argument("packet", nargs="*", help="for check: proto src dst port")
    p.add_argument("--rules", default=str(HERE / "rules.csv"))
    p.add_argument("--tests", default=str(HERE / "test-packets.csv"))
    a = p.parse_args()
    rules = load_rules(Path(a.rules))

    if a.cmd == "audit":
        audit(rules)
    elif a.cmd == "test":
        test(rules, Path(a.tests))
    else:
        if len(a.packet) != 4:
            raise SystemExit("usage: auditor.py check <proto> <src> <dst> <port>")
        proto, src, dst, port = a.packet
        action, rule = decide(rules, proto.lower(), src, dst, int(port))
        if rule:
            print(f"{action.upper()} by rule {rule['id']}: {rule['comment'] or '(no comment)'}")
        else:
            print("DENY by the implicit default (no rule matched)")


if __name__ == "__main__":
    main()
