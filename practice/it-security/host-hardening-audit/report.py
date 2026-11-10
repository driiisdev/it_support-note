"""
report.py - turn audit results (from Audit-Host.ps1 or audit_host.sh) into a scored hardening report.

Score: PASS = full points, WARN = half, FAIL = zero, UNKNOWN = not counted (re-run elevated).
Also groups by defense-in-depth layer, so you can see which layer of the "onion" is weakest.

Usage:
    python report.py results/<host>.json
    python report.py sample-results.json
    python report.py results/*.json          # compare several machines
"""

import glob
import json
import sys
from collections import defaultdict

POINTS = {"PASS": 1.0, "WARN": 0.5, "FAIL": 0.0}
LAYER_ORDER = ["firewall", "antimalware", "patching", "encryption", "accounts", "surface"]


def report(path: str) -> float:
    with open(path, encoding="utf-8-sig") as f:
        data = json.load(f)
    results = data["results"]
    scored = [r for r in results if r["status"] in POINTS]
    score = 100 * sum(POINTS[r["status"]] for r in scored) / (len(scored) or 1)

    print(f"\n{data['host']} - {data.get('os', '')}  (collected {data.get('collected', '?')}, "
          f"elevated: {data.get('elevated')})")
    by_layer = defaultdict(list)
    for r in results:
        by_layer[r["layer"]].append(r)
    for layer in sorted(by_layer, key=lambda l: LAYER_ORDER.index(l) if l in LAYER_ORDER else 99):
        rows = by_layer[layer]
        s = [r for r in rows if r["status"] in POINTS]
        layer_score = 100 * sum(POINTS[r["status"]] for r in s) / len(s) if s else None
        print(f"  {layer:<12} {'n/a' if layer_score is None else f'{layer_score:3.0f}%'}")
        for r in rows:
            if r["status"] != "PASS":
                fix = f"  -> {r['fix']}" if r.get("fix") else ""
                print(f"      [{r['status']:<7}] {r['check']}: {r['detail']}{fix}")

    unknown = sum(1 for r in results if r["status"] == "UNKNOWN")
    grade = "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D"
    print(f"  SCORE {score:.0f}/100 (grade {grade}) from {len(scored)} checks"
          + (f"; {unknown} UNKNOWN - re-run elevated for a complete picture" if unknown else ""))
    return score


def main() -> None:
    paths = [p for a in sys.argv[1:] for p in (glob.glob(a) or [a])]
    if not paths:
        raise SystemExit(__doc__)
    scores = {p: report(p) for p in paths}
    if len(scores) > 1:
        print("\nFleet summary (worst first):")
        for p, s in sorted(scores.items(), key=lambda x: x[1]):
            print(f"  {s:5.0f}  {p}")


if __name__ == "__main__":
    main()
