"""
connectivity_check.py - "the internet is down" ticket, diagnosed by working outward from the PC.

Each step only makes sense if the previous one passed, which is exactly the isolate-the-problem
method: local IP -> default gateway -> internet by IP -> DNS -> a real HTTPS request.

Usage:
    python connectivity_check.py
    python connectivity_check.py --host example.com --dns-test-ip 1.1.1.1
"""

import argparse
import ipaddress
import platform
import re
import socket
import ssl
import subprocess
import time

IS_WINDOWS = platform.system() == "Windows"


def run(cmd: list[str], timeout: int = 15) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                              errors="replace").stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def local_ip() -> str | None:
    """Ask the OS which source IP it would use for internet traffic (no packet is sent)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return None


def default_gateway() -> str | None:
    if IS_WINDOWS:
        out = run(["route", "print", "-4", "0.0.0.0"])
        # line looks like: 0.0.0.0   0.0.0.0   192.168.1.1   192.168.1.25   35
        m = re.search(r"^\s*0\.0\.0\.0\s+0\.0\.0\.0\s+(\d+\.\d+\.\d+\.\d+)", out, re.M)
    else:
        out = run(["ip", "route", "show", "default"]) or run(["netstat", "-rn"])
        m = re.search(r"default\s+(?:via\s+)?(\d+\.\d+\.\d+\.\d+)", out)
    return m.group(1) if m else None


def ping(host: str) -> tuple[bool, str]:
    count_flag = "-n" if IS_WINDOWS else "-c"
    out = run(["ping", count_flag, "2", host])
    # Windows prints "TTL=" on replies, Linux/mac print "ttl="; "Destination host unreachable"
    # from the local machine also contains no TTL, so this check is reliable for both.
    ok = "ttl=" in out.lower()
    times = re.findall(r"time[=<]\s*([\d.]+)\s*ms", out, re.I)
    return ok, (f"{times[0]} ms" if times else "")


def tcp_connect(host: str, port: int, timeout: float = 3) -> tuple[bool, str]:
    start = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, f"{(time.perf_counter() - start) * 1000:.0f} ms"
    except OSError as e:
        return False, str(e)


def resolve(name: str) -> tuple[bool, str]:
    try:
        return True, socket.gethostbyname(name)
    except socket.gaierror as e:
        return False, str(e)


def https_get(host: str) -> tuple[bool, str]:
    ctx = ssl.create_default_context()
    try:
        with socket.create_connection((host, 443), timeout=5) as raw:
            with ctx.wrap_socket(raw, server_hostname=host) as tls:
                tls.sendall(f"HEAD / HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n".encode())
                status_line = tls.recv(200).decode(errors="replace").splitlines()[0]
                return True, f"{status_line} ({tls.version()})"
    except ssl.SSLCertVerificationError as e:
        return False, f"certificate problem: {e.verify_message} (check the PC's date/time, or a proxy)"
    except OSError as e:
        return False, str(e)


def main() -> None:
    p = argparse.ArgumentParser(description="Work-outward network diagnosis.")
    p.add_argument("--host", default="www.google.com", help="site to test DNS + HTTPS against")
    p.add_argument("--dns-test-ip", default="8.8.8.8", help="public IP to test raw internet reachability")
    args = p.parse_args()

    results = []

    def step(name: str, ok: bool, detail: str, if_fail: str) -> bool:
        mark = "PASS" if ok else "FAIL"
        print(f"[{mark}] {name:<34} {detail}")
        results.append((name, ok, if_fail))
        return ok

    print("Working outward from this PC...\n")

    ip = local_ip()
    ip_ok = bool(ip) and not ip.startswith("169.254.")
    detail = ip or "no route / no address"
    if ip and ip.startswith("169.254."):
        detail += "  (APIPA - DHCP server not reachable)"
    elif ip and ipaddress.ip_address(ip).is_private:
        detail += "  (private address, behind NAT)"
    if not step("1. Local IP address", ip_ok, detail,
                "Check cable/Wi-Fi, then DHCP: ipconfig /release && ipconfig /renew"):
        return summarize(results)

    gw = default_gateway()
    gw_ok, gw_detail = ping(gw) if gw else (False, "no default gateway found")
    # Some routers block ping; a gateway that exists but doesn't answer ICMP isn't proof of failure.
    step("2. Default gateway reachable", gw_ok, f"{gw or '-'} {gw_detail}",
         "Local network problem: cable, Wi-Fi signal, switch port, router/AP down")

    inet_ok, inet_detail = tcp_connect(args.dns_test_ip, 53)
    if not step(f"3. Internet by IP ({args.dns_test_ip}:53)", inet_ok, inet_detail,
                "Router has no internet: ISP outage, modem/ONT, or firewall blocking outbound"):
        return summarize(results)

    dns_ok, dns_detail = resolve(args.host)
    if not step(f"4. DNS resolves {args.host}", dns_ok, dns_detail,
                "DNS problem: check DNS servers in ipconfig /all, try nslookup <name> 8.8.8.8, ipconfig /flushdns"):
        return summarize(results)

    web_ok, web_detail = https_get(args.host)
    step(f"5. HTTPS to {args.host}", web_ok, web_detail,
         "App-layer problem: proxy settings, TLS inspection, wrong date/time, or the site itself is down")

    summarize(results)


def summarize(results) -> None:
    failed = [r for r in results if not r[1]]
    print()
    if not failed:
        print("Everything passed - the network is fine from this PC. Problem is likely the app/site/account.")
        return
    first = failed[0]
    print(f"First failure: {first[0]}")
    print(f"Likely cause : {first[2]}")
    print("\nPaste this output into the ticket - it shows exactly which layer failed.")


if __name__ == "__main__":
    main()
