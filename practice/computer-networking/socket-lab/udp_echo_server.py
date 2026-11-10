"""
udp_echo_server.py - a UDP server: no listen(), no accept(), no connection. Just datagrams.

Usage:
    python udp_echo_server.py            # 127.0.0.1:9001
    python udp_echo_server.py 9101 --drop 30    # randomly "lose" 30% of datagrams to see what UDP doesn't fix
"""

import argparse
import random
import socket

p = argparse.ArgumentParser()
p.add_argument("port", nargs="?", type=int, default=9001)
p.add_argument("--drop", type=int, default=0, help="percent of datagrams to silently drop")
args = p.parse_args()

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as srv:  # SOCK_DGRAM = UDP
    srv.bind(("127.0.0.1", args.port))
    srv.settimeout(1.0)
    print(f"UDP echo server on 127.0.0.1:{args.port} (drop rate {args.drop}%)  - Ctrl+C to stop")
    print("Note: netstat shows UDP sockets with no state - there is no connection to be in.")
    try:
        while True:
            try:
                data, addr = srv.recvfrom(2048)  # each recvfrom = exactly one datagram
            except socket.timeout:
                continue
            text = data.decode(errors="replace")
            if random.randint(1, 100) <= args.drop:
                print(f"    {addr[1]} -> {text!r}  (DROPPED - client gets nothing, nobody retransmits)")
                continue
            print(f"    {addr[1]} -> {text!r}")
            srv.sendto(f"echo: {text}".encode(), addr)
    except KeyboardInterrupt:
        print("\nstopped")
