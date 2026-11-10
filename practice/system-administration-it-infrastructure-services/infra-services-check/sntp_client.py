"""
sntp_client.py - ask an NTP server for the time over UDP 123 and work out how wrong YOUR clock is.

Implements the core of SNTP (RFC 4330): one 48-byte request, one 48-byte reply, four timestamps.

Usage:
    python sntp_client.py                       # pool.ntp.org
    python sntp_client.py time.windows.com time.google.com
"""

import datetime as dt
import socket
import struct
import sys
import time

NTP_EPOCH_OFFSET = 2208988800  # seconds between 1900-01-01 (NTP epoch) and 1970-01-01 (Unix epoch)


def to_ntp(t: float) -> bytes:
    secs = int(t) + NTP_EPOCH_OFFSET
    frac = int((t % 1) * 2 ** 32)
    return struct.pack("!II", secs, frac)


def from_ntp(secs: int, frac: int) -> float:
    return secs - NTP_EPOCH_OFFSET + frac / 2 ** 32


def query(server: str) -> None:
    # Byte 0: LI=0 (no leap warning), VN=4 (version), Mode=3 (client)  -> 0b00_100_011 = 0x23
    packet = bytearray(48)
    packet[0] = 0x23
    t1 = time.time()                       # T1: client send time
    packet[40:48] = to_ntp(t1)             # put it in "transmit timestamp"; server echoes it back

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(3)
        try:
            s.sendto(packet, (server, 123))
            data, (ip, _) = s.recvfrom(48)
        except socket.gaierror:
            print(f"{server}: DNS lookup failed")
            return
        except socket.timeout:
            print(f"{server}: no reply - UDP 123 blocked by a firewall? (common on guest/corporate networks)")
            return
    t4 = time.time()                       # T4: client receive time

    li_vn_mode, stratum, poll, precision = struct.unpack("!BBbb", data[:4])
    ref_id = data[12:16]
    t2 = from_ntp(*struct.unpack("!II", data[32:40]))   # T2: server receive time
    t3 = from_ntp(*struct.unpack("!II", data[40:48]))   # T3: server transmit time

    # The two classic NTP formulas:
    delay = (t4 - t1) - (t3 - t2)          # round trip, minus the time the server spent processing
    offset = ((t2 - t1) + (t3 - t4)) / 2   # how far the local clock is from the server's

    if stratum == 1:
        ref = ref_id.decode(errors="replace").strip("\x00")   # e.g. "GPS", "PPS", "ATOM"
        ref_desc = f"reference clock '{ref}'"
    elif stratum == 0:
        ref_desc = "kiss-of-death / unsynchronized"
    else:
        ref_desc = f"syncs from {socket.inet_ntoa(ref_id)}"

    server_time = dt.datetime.fromtimestamp(t3, dt.timezone.utc)
    print(f"{server} ({ip})")
    print(f"  stratum     : {stratum}  ({ref_desc})")
    print(f"  server time : {server_time:%Y-%m-%d %H:%M:%S.%f} UTC")
    print(f"  round trip  : {delay * 1000:.1f} ms")
    print(f"  clock offset: {offset * 1000:+.1f} ms  (+ = your clock is behind)")
    if abs(offset) > 300:
        print("  !! more than 5 minutes off - Kerberos/AD logons will FAIL (max skew 5 min)")
    elif abs(offset) > 1:
        print("  ! more than 1 second off - check the Windows Time service (w32tm /query /status)")
    else:
        print("  ok - well within tolerance")
    print()


if __name__ == "__main__":
    for srv in sys.argv[1:] or ["pool.ntp.org"]:
        query(srv)
