"""
log_analyzer.py - read logs like an investigator: summarize, find attacks, find the FIRST error.

Two formats:
  auth   - Linux /var/log/auth.log (sshd + sudo lines)
  events - Windows Event Log exported to CSV, e.g.:
           Get-WinEvent -LogName System -MaxEvents 500 |
             Select-Object TimeCreated,Id,LevelDisplayName,ProviderName,Message |
             Export-Csv system-events.csv -NoTypeInformation

Usage:
    python log_analyzer.py auth sample-logs/auth.log
    python log_analyzer.py auth /var/log/auth.log --threshold 5
    python log_analyzer.py events sample-logs/system-events.csv
    python log_analyzer.py events --live          # Windows: pull the last 24 h of System log (read-only)
"""

import argparse
import csv
import datetime as dt
import io
import re
import subprocess
import sys
from collections import Counter, defaultdict

# "Mar  4 02:14:07 web01 sshd[2231]: Failed password for invalid user admin from 198.51.100.7 port 40001 ssh2"
LINE = re.compile(r"^(?P<ts>\w{3}\s+\d{1,2} \d\d:\d\d:\d\d) (?P<host>\S+) (?P<proc>[\w.-]+)(?:\[\d+\])?: (?P<msg>.*)$")
FAILED = re.compile(r"Failed password for (?:invalid user )?(?P<user>\S+) from (?P<ip>[\d.:a-fA-F]+)")
ACCEPTED = re.compile(r"Accepted (?P<method>\w+) for (?P<user>\S+) from (?P<ip>[\d.:a-fA-F]+)")
SUDO = re.compile(r"^\s*(?P<user>\S+) : .*COMMAND=(?P<cmd>.*)$")


def parse_ts(ts: str, year: int) -> dt.datetime:
    return dt.datetime.strptime(f"{year} {' '.join(ts.split())}", "%Y %b %d %H:%M:%S")


def analyze_auth(path: str, threshold: int) -> None:
    year = dt.date.today().year  # syslog lines don't include the year
    failed_by_ip = defaultdict(list)
    users_by_ip = defaultdict(Counter)
    accepted = []
    sudo_cmds = []
    total = 0

    with open(path, encoding="utf-8", errors="replace") as f:
        for raw in f:
            m = LINE.match(raw.rstrip())
            if not m:
                continue
            total += 1
            ts = parse_ts(m["ts"], year)
            msg = m["msg"]
            if fm := FAILED.search(msg):
                failed_by_ip[fm["ip"]].append(ts)
                users_by_ip[fm["ip"]][fm["user"]] += 1
            elif am := ACCEPTED.search(msg):
                accepted.append((ts, am["user"], am["ip"], am["method"]))
            elif m["proc"] == "sudo" and (sm := SUDO.match(msg)):
                sudo_cmds.append((ts, sm["user"], sm["cmd"]))

    print(f"Parsed {total} lines from {path}\n")
    print("Failed SSH logins by source IP:")
    print(f"  {'IP':<18}{'FAILS':>6}  {'WINDOW':<20}{'RATE':>10}  TOP USERNAMES TRIED")
    for ip, times in sorted(failed_by_ip.items(), key=lambda x: -len(x[1])):
        span = (max(times) - min(times)).total_seconds() or 1
        rate = len(times) / span * 60
        users = ", ".join(u for u, _ in users_by_ip[ip].most_common(4))
        flag = "  <-- BRUTE FORCE" if len(times) >= threshold else ""
        print(f"  {ip:<18}{len(times):>6}  {min(times):%H:%M:%S}-{max(times):%H:%M:%S}   {rate:>6.1f}/min  {users}{flag}")

    print("\nSuccessful logins:")
    for ts, user, ip, method in accepted:
        prior = [t for t in failed_by_ip.get(ip, []) if t <= ts and (ts - t).total_seconds() < 3600]
        note = ""
        if len(prior) >= 3:
            note = f"  <-- SUSPICIOUS: success after {len(prior)} failures from the same IP in the last hour"
        elif method == "password":
            note = "  (password auth - consider keys only)"
        print(f"  {ts:%b %d %H:%M:%S}  {user:<8} from {ip:<16} via {method}{note}")

    if sudo_cmds:
        print("\nsudo commands:")
        for ts, user, cmd in sudo_cmds:
            note = "  <-- reading password hashes!" if "/etc/shadow" in cmd else ""
            print(f"  {ts:%b %d %H:%M:%S}  {user:<8} {cmd}{note}")

    print("\nNext steps for a real incident: block brute-force IPs (fail2ban/firewall), disable password "
          "auth (PasswordAuthentication no), reset any account that logged in after failures, escalate.")


def load_events(path: str | None, live: bool) -> list[dict]:
    if live:
        if sys.platform != "win32":
            raise SystemExit("--live only works on Windows")
        ps = ("Get-WinEvent -FilterHashtable @{LogName='System'; StartTime=(Get-Date).AddDays(-1)} "
              "-ErrorAction SilentlyContinue | Select-Object @{n='TimeCreated';e={$_.TimeCreated.ToString('s')}},"
              "Id,LevelDisplayName,ProviderName,Message "
              "| ConvertTo-Csv -NoTypeInformation")
        text = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                              capture_output=True, text=True, errors="replace").stdout
        return list(csv.DictReader(io.StringIO(text)))
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


KNOWN_IDS = {
    "41": "unexpected reboot (crash or power loss)",
    "6005": "event log started (~ boot)",
    "6006": "event log stopped (~ clean shutdown)",
    "1074": "shutdown/restart initiated by a user/process",
    "7031": "a service crashed",
    "7034": "a service crashed",
    "7": "disk bad block - back up NOW",
    "153": "disk I/O retried - possible failing disk/cable",
    "1014": "DNS name resolution timeout",
}


def parse_event_time(text: str) -> dt.datetime:
    """Export-Csv writes dates in the machine's locale format, so try ISO first, then common ones.
    Tip: export with @{n='TimeCreated';e={$_.TimeCreated.ToString('s')}} to always get ISO."""
    text = text.strip()
    try:
        return dt.datetime.fromisoformat(text)
    except ValueError:
        pass
    for fmt in ("%m/%d/%Y %I:%M:%S %p", "%m/%d/%Y %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%d.%m.%Y %H:%M:%S"):
        try:
            return dt.datetime.strptime(text, fmt)
        except ValueError:
            continue
    raise SystemExit(f"Unrecognized date format: {text!r} - re-export with TimeCreated.ToString('s')")


def analyze_events(rows: list[dict]) -> None:
    if not rows:
        raise SystemExit("No events found.")
    for r in rows:
        r["_t"] = parse_event_time(r["TimeCreated"])
        r["Message"] = (r.get("Message") or "").replace("\r", " ").replace("\n", " ")
    rows.sort(key=lambda r: r["_t"])

    print(f"{len(rows)} events from {rows[0]['_t']:%Y-%m-%d %H:%M} to {rows[-1]['_t']:%Y-%m-%d %H:%M}\n")
    print("By level:", dict(Counter(r["LevelDisplayName"] for r in rows)))

    problems = [r for r in rows if r["LevelDisplayName"] in ("Error", "Critical", "Warning")]
    print("\nProblem events by source + ID (search these two together online):")
    for (src, eid), n in Counter((r["ProviderName"], r["Id"]) for r in problems).most_common(10):
        print(f"  {n:>3} x  {src} / {eid}  {KNOWN_IDS.get(str(eid), '')}")

    errors = [r for r in rows if r["LevelDisplayName"] in ("Error", "Critical")]
    if errors:
        first = errors[0]
        print(f"\nFIRST error in the window (later errors are often consequences of this one):")
        print(f"  {first['_t']:%Y-%m-%d %H:%M:%S}  {first['ProviderName']} {first['Id']}: {first['Message'][:120]}")

    print("\nTimeline of errors/critical + boots:")
    for r in rows:
        if r["LevelDisplayName"] in ("Error", "Critical") or str(r["Id"]) in ("41", "6005", "1074"):
            print(f"  {r['_t']:%H:%M:%S}  {r['LevelDisplayName']:<11} {r['ProviderName'][:28]:<28} {r['Id']:>5}  "
                  f"{r['Message'][:70]}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("kind", choices=["auth", "events"])
    p.add_argument("path", nargs="?")
    p.add_argument("--threshold", type=int, default=10, help="failed logins from one IP = brute force")
    p.add_argument("--live", action="store_true")
    args = p.parse_args()

    if args.kind == "auth":
        if not args.path:
            raise SystemExit("give a path, e.g. sample-logs/auth.log")
        analyze_auth(args.path, args.threshold)
    else:
        if not args.path and not args.live:
            raise SystemExit("give a CSV path or --live")
        analyze_events(load_events(args.path, args.live))


if __name__ == "__main__":
    main()
