"""
net_doctor.py - bottom-up network diagnosis with a written report for the ticket.

Goes further than the beginner connectivity check: inspects the adapter config, compares your DNS
server against a public one, checks the hosts file for overrides, traces the route, and tests the
specific service port the user cares about.

Usage:
    python net_doctor.py                                   # defaults: www.google.com:443
    python net_doctor.py --target outlook.office365.com --port 443
    python net_doctor.py --target intranet.example.local --port 80 --no-trace
"""

import argparse
import datetime as dt
import ipaddress
import platform
import random
import re
import socket
import struct
import subprocess
from pathlib import Path

IS_WINDOWS = platform.system() == "Windows"
HOSTS = Path(r"C:\Windows\System32\drivers\etc\hosts") if IS_WINDOWS else Path("/etc/hosts")
report: list[str] = []


def out(line: str = "") -> None:
    print(line)
    report.append(line)


def run(cmd: list[str], timeout: int = 60) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, errors="replace").stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


# ---------------------------------------------------------------- layer 1-3: adapter + IP config
def ip_config() -> dict:
    """Pull IP, mask, gateway, DNS servers out of ipconfig /all (Windows) or ip/resolv.conf (Linux)."""
    cfg = {"ip": None, "mask": None, "gateway": None, "dns": [], "dhcp": None}
    if IS_WINDOWS:
        text = run(["ipconfig", "/all"])
        # Find the adapter block that has a default gateway (the one actually in use)
        for block in re.split(r"\r?\n(?=\S)", text):
            gw = re.search(r"Default Gateway[ .]*: ([\d.]+)", block)
            if not gw:
                continue
            cfg["gateway"] = gw.group(1)
            m = re.search(r"IPv4 Address[ .]*: ([\d.]+)", block)
            cfg["ip"] = m.group(1) if m else None
            m = re.search(r"Subnet Mask[ .]*: ([\d.]+)", block)
            cfg["mask"] = m.group(1) if m else None
            m = re.search(r"DHCP Server[ .]*: ([\d.]+)", block)
            cfg["dhcp"] = m.group(1) if m else "static / none"
            dns_part = re.search(r"DNS Servers[ .]*: ([\s\S]*?)(?:\r?\n\s{3}\S[^:\n]*:|\Z)", block)
            if dns_part:
                cfg["dns"] = re.findall(r"\d+\.\d+\.\d+\.\d+", dns_part.group(1))
            break
    else:
        route = run(["ip", "route", "show", "default"])
        m = re.search(r"default via ([\d.]+) dev (\S+)", route)
        if m:
            cfg["gateway"], dev = m.groups()
            addr = run(["ip", "-4", "addr", "show", dev])
            m2 = re.search(r"inet ([\d.]+)/(\d+)", addr)
            if m2:
                cfg["ip"] = m2.group(1)
                cfg["mask"] = str(ipaddress.ip_network(f"0.0.0.0/{m2.group(2)}").netmask)
        try:
            cfg["dns"] = re.findall(r"^nameserver\s+([\d.]+)", Path("/etc/resolv.conf").read_text(), re.M)
        except OSError:
            pass
    return cfg


def ping(host: str) -> tuple[bool, str]:
    text = run(["ping", "-n" if IS_WINDOWS else "-c", "3", host], timeout=20)
    loss = re.search(r"(\d+)% (?:packet )?loss", text)
    avg = re.search(r"Average = (\d+)ms", text) or re.search(r"= [\d.]+/([\d.]+)/", text)
    ok = "ttl=" in text.lower()
    return ok, f"loss {loss.group(1) if loss else '?'}%, avg {avg.group(1) + ' ms' if avg else '-'}"


# ---------------------------------------------------------------- DNS
def raw_dns_a(name: str, server: str) -> list[str] | str:
    """Minimal A-record query straight to a chosen server, bypassing the OS resolver and hosts file."""
    tid = random.randint(0, 0xFFFF)
    q = struct.pack("!HHHHHH", tid, 0x0100, 1, 0, 0, 0)
    q += b"".join(bytes([len(p)]) + p.encode() for p in name.split(".")) + b"\x00" + struct.pack("!HH", 1, 1)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(3)
        try:
            s.sendto(q, (server, 53))
            resp, _ = s.recvfrom(2048)
        except OSError as e:
            return f"no answer ({e.__class__.__name__})"
    rcode = struct.unpack("!H", resp[2:4])[0] & 0xF
    if rcode == 3:
        return "NXDOMAIN"
    # Skip header + question, then read A records (type 1, 4-byte data); names are usually 2-byte pointers
    ancount = struct.unpack("!H", resp[6:8])[0]
    i = 12
    while resp[i] != 0:
        i += resp[i] + 1
    i += 5
    ips = []
    for _ in range(ancount):
        i += 2 if resp[i] & 0xC0 == 0xC0 else resp.index(b"\x00", i) - i + 1
        rtype, _, _, rdlen = struct.unpack("!HHIH", resp[i:i + 10])
        i += 10
        if rtype == 1:
            ips.append(socket.inet_ntoa(resp[i:i + 4]))
        i += rdlen
    return ips or "no A records"


def hosts_overrides(name: str) -> list[str]:
    try:
        lines = HOSTS.read_text(errors="replace").splitlines()
    except OSError:
        return []
    hits = []
    for line in lines:
        line = line.split("#", 1)[0].strip()
        if line and name.lower() in [w.lower() for w in line.split()[1:]]:
            hits.append(line)
    return hits


# ---------------------------------------------------------------- path + service
def traceroute(host: str) -> list[str]:
    if IS_WINDOWS:
        text = run(["tracert", "-d", "-h", "15", "-w", "800", host], timeout=120)
        return [l.rstrip() for l in text.splitlines() if re.match(r"^\s+\d+\s", l)]
    text = run(["traceroute", "-n", "-m", "15", "-w", "1", host], timeout=120)
    return [l.rstrip() for l in text.splitlines()[1:]]


def tcp_check(host: str, port: int) -> str:
    try:
        with socket.create_connection((host, port), timeout=4):
            return "OPEN"
    except ConnectionRefusedError:
        return "CLOSED (RST - nothing listening)"
    except socket.timeout:
        return "FILTERED (timeout - firewall or host down)"
    except OSError as e:
        return f"ERROR ({e})"


def main() -> None:
    p = argparse.ArgumentParser(description="Bottom-up network diagnosis.")
    p.add_argument("--target", default="www.google.com")
    p.add_argument("--port", type=int, default=443)
    p.add_argument("--public-dns", default="8.8.8.8")
    p.add_argument("--no-trace", action="store_true")
    args = p.parse_args()
    findings = []

    out(f"net_doctor report - {dt.datetime.now():%Y-%m-%d %H:%M} - host {socket.gethostname()}")
    out(f"Target: {args.target}:{args.port}\n")

    out("[1] IP configuration")
    cfg = ip_config()
    for k in ("ip", "mask", "gateway", "dhcp"):
        out(f"    {k:<8}: {cfg[k]}")
    out(f"    dns     : {', '.join(cfg['dns']) or 'none found'}")
    if not cfg["ip"]:
        findings.append("No IPv4 address on an adapter with a gateway - check cable/Wi-Fi, adapter enabled.")
    elif cfg["ip"].startswith("169.254."):
        findings.append("APIPA address (169.254.x.x): DHCP server unreachable or scope exhausted.")
    elif cfg["mask"] and cfg["gateway"]:
        net = ipaddress.ip_network(f"{cfg['ip']}/{cfg['mask']}", strict=False)
        if ipaddress.ip_address(cfg["gateway"]) not in net:
            findings.append(f"Gateway {cfg['gateway']} is outside {net} - wrong mask or gateway (static config error?).")

    out("\n[2] Local network: ping default gateway")
    if cfg["gateway"]:
        ok, detail = ping(cfg["gateway"])
        out(f"    {cfg['gateway']}: {'reply' if ok else 'NO reply'} ({detail})")
        if not ok:
            findings.append("Gateway did not answer ping (may just block ICMP - check next steps).")

    out(f"\n[3] Internet by IP: ping {args.public_dns}")
    ok, detail = ping(args.public_dns)
    out(f"    {'reply' if ok else 'NO reply'} ({detail})")
    if not ok:
        findings.append("No reply from the internet by IP - router/ISP problem, or ICMP blocked upstream.")

    out(f"\n[4] DNS for {args.target}")
    try:
        system_answer = socket.gethostbyname_ex(args.target)[2]
    except socket.gaierror as e:
        system_answer = f"FAILED ({e})"
    out(f"    OS resolver (hosts file + your DNS servers): {system_answer}")
    if cfg["dns"]:
        out(f"    your DNS server {cfg['dns'][0]:<15}: {raw_dns_a(args.target, cfg['dns'][0])}")
    public = raw_dns_a(args.target, args.public_dns)
    out(f"    public DNS {args.public_dns:<20}: {public}")
    overrides = hosts_overrides(args.target)
    if overrides:
        out(f"    hosts file overrides: {overrides}")
        findings.append(f"{HOSTS} overrides {args.target} - stale entry or malware? Check and remove.")
    if isinstance(system_answer, str) and isinstance(public, list):
        findings.append("Your DNS fails but public DNS works - fix the DNS server setting or the internal DNS server.")

    if not args.no_trace:
        out(f"\n[5] Route to {args.target} (max 15 hops)")
        hops = traceroute(args.target)
        for h in hops:
            out(f"    {h}")
        if hops and all("*" in h for h in hops[-3:]):
            findings.append("Last hops time out - path blocked/filtered beyond that point (or target drops ICMP/UDP probes).")

    out(f"\n[6] Service port {args.target}:{args.port}")
    state = tcp_check(args.target, args.port)
    out(f"    {state}")
    if not state.startswith("OPEN"):
        findings.append(f"Port {args.port} not open - service down, wrong port, or firewall.")

    out("\nFINDINGS")
    if findings:
        for f in findings:
            out(f"  - {f}")
    else:
        out("  - No network problem found from this PC. Look at the application, account, or the remote service.")

    reports = Path(__file__).parent / "reports"
    reports.mkdir(exist_ok=True)
    path = reports / f"net_doctor-{dt.datetime.now():%Y%m%d-%H%M%S}.txt"
    path.write_text("\n".join(report), encoding="utf-8")
    print(f"\nReport saved -> {path}  (attach it to the ticket)")


if __name__ == "__main__":
    main()
