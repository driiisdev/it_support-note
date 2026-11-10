"""
risk_register.py - score risks (likelihood x impact), prioritize them, and draw the heat map.

risks.csv columns: id,risk,asset,likelihood(1-5),impact(1-5),owner,response,control,status
  response: mitigate | transfer | avoid | accept

Usage:
    python risk_register.py              # prioritized register + heat map
    python risk_register.py --open       # only risks that aren't done/accepted
"""

import argparse
import csv
from pathlib import Path

HERE = Path(__file__).parent


def level(score: int) -> str:
    return "CRITICAL" if score >= 20 else "HIGH" if score >= 12 else "MEDIUM" if score >= 6 else "LOW"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--csv", default=str(HERE / "risks.csv"))
    p.add_argument("--open", action="store_true")
    a = p.parse_args()

    with open(a.csv, newline="", encoding="utf-8") as f:
        risks = list(csv.DictReader(f))
    for r in risks:
        r["L"], r["I"] = int(r["likelihood"]), int(r["impact"])
        r["score"] = r["L"] * r["I"]
    if a.open:
        risks = [r for r in risks if r["status"] not in ("done", "accepted")]
    risks.sort(key=lambda r: (-r["score"], -r["I"]))  # ties: higher impact first

    print(f"{'ID':<5}{'SCORE':>5}  {'LEVEL':<9}{'RESPONSE':<10}{'STATUS':<12}{'OWNER':<12}RISK")
    for r in risks:
        print(f"{r['id']:<5}{r['score']:>5}  {level(r['score']):<9}{r['response']:<10}{r['status']:<12}"
              f"{r['owner'][:11]:<12}{r['risk']}")
        print(f"{'':<43}control: {r['control']}")

    # Heat map: rows = likelihood (5 at top), cols = impact
    print("\nHeat map (likelihood x impact) - risk IDs in each cell")
    print("              " + "".join(f"{'impact ' + str(i):^12}" for i in range(1, 6)))
    for L in range(5, 0, -1):
        cells = []
        for I in range(1, 6):
            ids = ",".join(r["id"] for r in risks if r["L"] == L and r["I"] == I)
            shade = {"CRITICAL": "!!", "HIGH": "! ", "MEDIUM": ". ", "LOW": "  "}[level(L * I)]
            cells.append(f"{shade}{ids:<10}")
        print(f"likelihood {L} |" + "|".join(cells) + "|")
    print("  legend: !! critical (>=20)   ! high (>=12)   . medium (>=6)   blank low")

    top = [r for r in risks if r["score"] >= 12 and r["status"] not in ("done", "accepted")]
    if top:
        print("\nFix first (high/critical and still open): " + ", ".join(f"{r['id']} ({r['score']})" for r in top))


if __name__ == "__main__":
    main()
