"""
port_check.py - is a TCP port OPEN, CLOSED (refused) or FILTERED (timeout)? The firewall-ticket question.

    OPEN      -> handshake completed: something is listening.
    CLOSED    -> got a RST back fast: host is reachable, nothing listening on that port.
    FILTERED  -> no answer at all before timeout: a firewall silently dropped it, or host is down.

Only check hosts you own or are authorized to test.

Usage:
    python port_check.py                                  # default checks: localhost lab ports + common services on example.com
    python port_check.py server01 22 80 443 3389
    python port_check.py --file services.txt              # lines like: mail.example.com 587
"""

import argparse
import errno
import socket
import time
from concurrent.futures import ThreadPoolExecutor

COMMON = {22: "SSH", 25: "SMTP", 53: "DNS", 80: "HTTP", 110: "POP3", 143: "IMAP", 443: "HTTPS",
          445: "SMB", 587: "SMTP-submit", 993: "IMAPS", 3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL",
          9000: "lab TCP echo"}


def check(host: str, port: int, timeout: float) -> tuple[str, int, str, str]:
    start = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return host, port, "OPEN", f"{(time.perf_counter() - start) * 1000:.0f} ms"
    except socket.timeout:
        return host, port, "FILTERED", f"no reply in {timeout}s"
    except ConnectionRefusedError:
        return host, port, "CLOSED", f"refused in {(time.perf_counter() - start) * 1000:.0f} ms"
    except socket.gaierror:
        return host, port, "DNS-FAIL", "name does not resolve"
    except OSError as e:
        if e.errno in (errno.EHOSTUNREACH, errno.ENETUNREACH) or getattr(e, "winerror", 0) in (10065, 10051):
            return host, port, "UNREACHABLE", "no route to host"
        return host, port, "ERROR", str(e)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("host", nargs="?")
    p.add_argument("ports", nargs="*", type=int)
    p.add_argument("--file")
    p.add_argument("--timeout", type=float, default=3.0,
                   help="Windows needs >2s: it retries the SYN twice after a RST before reporting refused")
    args = p.parse_args()

    targets: list[tuple[str, int]] = []
    if args.file:
        with open(args.file) as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    h, port = line.split()[:2]
                    targets.append((h, int(port)))
    elif args.host:
        targets = [(args.host, port) for port in (args.ports or [22, 80, 443, 3389])]
    else:
        targets = [("127.0.0.1", 9000), ("127.0.0.1", 9999), ("example.com", 443), ("example.com", 81)]

    with ThreadPoolExecutor(max_workers=20) as pool:
        results = list(pool.map(lambda t: check(*t, args.timeout), targets))

    print(f"{'HOST':<22}{'PORT':>6}  {'SERVICE':<14}{'STATE':<12}DETAIL")
    for host, port, state, detail in results:
        print(f"{host:<22}{port:>6}  {COMMON.get(port, ''):<14}{state:<12}{detail}")


if __name__ == "__main__":
    main()
