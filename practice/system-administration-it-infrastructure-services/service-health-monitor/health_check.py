"""
health_check.py - a tiny service monitor: HTTP status + latency, TCP ports, TLS certificate expiry.

Reads services.json, checks everything in parallel, prints a status board, exits non-zero if
anything is DOWN (so Task Scheduler / cron / CI can alert on it).

Usage:
    python health_check.py                      # services.json
    python health_check.py --config my.json
    python health_check.py --watch 30           # re-check every 30 s (Ctrl+C to stop)
"""

import argparse
import datetime as dt
import json
import socket
import ssl
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

UP, WARN, DOWN = "UP", "WARN", "DOWN"


def check_http(svc: dict) -> tuple[str, str]:
    url = svc["url"]
    expect = svc.get("expect_status", 200)
    max_ms = svc.get("max_ms", 1000)
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": "health-check/1.0"})
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=svc.get("timeout", 5)) as r:
            code = r.status
            body = r.read(2048).decode(errors="replace")
    except urllib.error.HTTPError as e:            # 4xx / 5xx still tell us a lot
        code, body = e.code, ""
    except urllib.error.URLError as e:
        reason = e.reason
        if isinstance(reason, ssl.SSLCertVerificationError):
            return DOWN, f"TLS certificate error: {reason.verify_message}"
        return DOWN, f"unreachable: {reason}"
    except (socket.timeout, TimeoutError):
        return DOWN, "timeout"
    ms = (time.perf_counter() - start) * 1000

    if code != expect:
        hint = {401: "auth required", 403: "forbidden", 404: "wrong URL/path", 500: "app crashed",
                502: "proxy can't reach the app", 503: "overloaded/maintenance", 504: "app too slow behind proxy"}
        return DOWN, f"HTTP {code} (expected {expect}) {hint.get(code, '')}".strip()
    if svc.get("expect_text") and svc["expect_text"] not in body:
        return DOWN, f"HTTP {code} but page doesn't contain {svc['expect_text']!r} (wrong site? error page?)"
    if ms > max_ms:
        return WARN, f"HTTP {code} but slow: {ms:.0f} ms (limit {max_ms})"
    return UP, f"HTTP {code} in {ms:.0f} ms"


def check_tcp(svc: dict) -> tuple[str, str]:
    start = time.perf_counter()
    try:
        with socket.create_connection((svc["host"], svc["port"]), timeout=svc.get("timeout", 4)):
            return UP, f"port {svc['port']} open in {(time.perf_counter() - start) * 1000:.0f} ms"
    except ConnectionRefusedError:
        return DOWN, f"port {svc['port']} refused - service not running?"
    except (socket.timeout, TimeoutError):
        return DOWN, f"port {svc['port']} timeout - firewall or host down"
    except OSError as e:
        return DOWN, str(e)


def check_tls(svc: dict) -> tuple[str, str]:
    host, port = svc["host"], svc.get("port", 443)
    warn_days = svc.get("warn_days", 21)
    ctx = ssl.create_default_context()
    try:
        with socket.create_connection((host, port), timeout=5) as raw:
            with ctx.wrap_socket(raw, server_hostname=host) as tls:
                cert = tls.getpeercert()
                version = tls.version()
    except ssl.SSLCertVerificationError as e:
        return DOWN, f"certificate invalid: {e.verify_message}"
    except OSError as e:
        return DOWN, f"TLS connect failed: {e}"

    expires = dt.datetime.fromtimestamp(ssl.cert_time_to_seconds(cert["notAfter"]), dt.timezone.utc)
    days = (expires - dt.datetime.now(dt.timezone.utc)).days
    issuer = dict(x[0] for x in cert["issuer"]).get("organizationName", "?")
    detail = f"{version}, expires {expires:%Y-%m-%d} ({days} days), issuer {issuer}"
    if days < 0:
        return DOWN, "EXPIRED - " + detail
    if days <= warn_days:
        return WARN, "renew soon - " + detail
    return UP, detail


CHECKS = {"http": check_http, "tcp": check_tcp, "tls": check_tls}


def run_all(services: list[dict]) -> int:
    with ThreadPoolExecutor(max_workers=16) as pool:
        results = list(pool.map(lambda s: (s, *CHECKS[s["type"]](s)), services))
    colors = {UP: "\033[32m", WARN: "\033[33m", DOWN: "\033[31m"}
    print(f"\n{dt.datetime.now():%Y-%m-%d %H:%M:%S}  {len(services)} checks")
    print(f"{'STATUS':<7}{'SERVICE':<28}{'TYPE':<6}DETAIL")
    for svc, status, detail in sorted(results, key=lambda r: [DOWN, WARN, UP].index(r[1])):
        print(f"{colors[status]}{status:<7}\033[0m{svc['name'][:27]:<28}{svc['type']:<6}{detail}")
    down = sum(1 for _, s, _ in results if s == DOWN)
    warn = sum(1 for _, s, _ in results if s == WARN)
    print(f"-> {down} down, {warn} warning, {len(results) - down - warn} up")
    return down


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--config", default=str(Path(__file__).parent / "services.json"))
    p.add_argument("--watch", type=int, help="seconds between runs")
    args = p.parse_args()
    services = json.loads(Path(args.config).read_text(encoding="utf-8"))["services"]

    import os
    if os.name == "nt":
        os.system("")  # enables ANSI colors in the Windows console

    try:
        while True:
            down = run_all(services)
            if not args.watch:
                raise SystemExit(1 if down else 0)
            time.sleep(args.watch)
    except KeyboardInterrupt:
        print("\nstopped")


if __name__ == "__main__":
    main()
