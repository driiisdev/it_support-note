"""
gpo_sim.py - which Group Policy setting wins? Simulates LSDOU processing, Enforced, and Block Inheritance.

Processing order: Local -> Site -> Domain -> OU (parent -> child). Later GPOs overwrite earlier ones,
so the closest OU normally wins. Two exceptions:
  - Block Inheritance on an OU: GPOs linked ABOVE it are ignored (unless Enforced)
  - Enforced on a GPO link: it can't be blocked, and it wins over GPOs linked below it

Also includes a DN parser so you can see how an object's DN maps to the OUs that apply to it.

Usage:
    python gpo_sim.py                                   # built-in scenario
    python gpo_sim.py "CN=Amina Bello,OU=Finance,OU=Users,DC=corp,DC=example,DC=com"
"""

import sys

# GPO links: container -> list of (gpo name, enforced, {setting: value})
LINKS = {
    "Local": [("Local Policy", False, {"Screen lock (min)": 30, "USB storage": "Allowed"})],
    "Site:HQ": [("HQ Proxy", False, {"Proxy": "proxy-hq:8080"})],
    "DC=corp,DC=example,DC=com": [
        ("Default Domain Policy", False, {"Min password length": 12, "Screen lock (min)": 15}),
        ("Security Baseline", True, {"USB storage": "Blocked", "SMBv1": "Disabled"}),  # ENFORCED
    ],
    "OU=Users,DC=corp,DC=example,DC=com": [
        ("All Users - Drives", False, {"Mapped drive S:": r"\\fs01\shared", "Wallpaper": "corp.jpg"}),
    ],
    "OU=Finance,OU=Users,DC=corp,DC=example,DC=com": [
        ("Finance Apps", False, {"Mapped drive F:": r"\\fs01\finance", "Screen lock (min)": 5,
                                 "USB storage": "Allowed"}),  # tries to allow USB - but Baseline is Enforced
    ],
    "OU=Lab,OU=Users,DC=corp,DC=example,DC=com": [
        ("Lab Freedom", False, {"Screen lock (min)": 60, "Wallpaper": "lab.jpg"}),
    ],
}
BLOCK_INHERITANCE = {"OU=Lab,OU=Users,DC=corp,DC=example,DC=com"}


def parse_dn(dn: str) -> list[tuple[str, str]]:
    """Split a DN on unescaped commas -> [(type, value), ...] from the object up to the domain root."""
    parts, current, escaped = [], "", False
    for ch in dn:
        if escaped:
            current += ch
            escaped = False
        elif ch == "\\":
            current += ch
            escaped = True
        elif ch == ",":
            parts.append(current)
            current = ""
        else:
            current += ch
    parts.append(current)
    return [tuple(p.strip().split("=", 1)) for p in parts]


def containers_for(dn: str) -> list[str]:
    """Return the domain and every OU above the object, top-down (processing order)."""
    rdns = parse_dn(dn)
    domain = ",".join(f"DC={v}" for t, v in rdns if t.upper() == "DC")
    ous = [(t, v) for t, v in rdns if t.upper() == "OU"]
    chain = [domain]
    for i in range(len(ous) - 1, -1, -1):  # walk from the top OU down to the closest one
        chain.append(",".join(f"OU={v}" for _, v in ous[i:]) + "," + domain)
    return chain


def simulate(dn: str, site: str = "HQ") -> None:
    print(f"Object: {dn}")
    print("Path  : " + " > ".join(f"{t}={v}" for t, v in reversed(parse_dn(dn))) + "\n")
    order = ["Local", f"Site:{site}"] + containers_for(dn)

    # Block inheritance: find the deepest blocked container in the path; drop non-enforced links above it
    blocked_at = max((i for i, c in enumerate(order) if c in BLOCK_INHERITANCE), default=None)

    effective: dict[str, tuple] = {}  # setting -> (value, gpo, enforced)
    enforced_links = []
    print("Processing order (L-S-D-OU):")
    for i, container in enumerate(order):
        for gpo, enforced, settings in LINKS.get(container, []):
            # Block Inheritance stops GPOs from the site, domain and parent OUs - not the local policy
            skipped = (blocked_at is not None and i < blocked_at and not enforced and container != "Local")
            tag = " [ENFORCED]" if enforced else ""
            print(f"  {'(skipped - blocked) ' if skipped else ''}{container:<48} -> {gpo}{tag}")
            if skipped:
                continue
            if enforced:
                enforced_links.append((gpo, settings))
            for k, v in settings.items():
                effective[k] = (v, gpo, enforced)
    # Enforced GPOs win over everything linked below them: re-apply them last (highest-level first wins
    # among enforced, so apply in reverse order of appearance).
    for gpo, settings in reversed(enforced_links):
        for k, v in settings.items():
            effective[k] = (v, gpo, True)

    print("\nResultant Set of Policy (what gpresult /r would show):")
    for k, (v, gpo, enf) in sorted(effective.items()):
        print(f"  {k:<22} = {str(v):<20} from {gpo}{' (enforced)' if enf else ''}")
    print()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        simulate(sys.argv[1])
    else:
        simulate("CN=Amina Bello,OU=Finance,OU=Users,DC=corp,DC=example,DC=com")
        simulate("CN=Test PC\\, Bench 3,OU=Lab,OU=Users,DC=corp,DC=example,DC=com")
