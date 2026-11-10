"""
client.py - send the same messages over TCP and over UDP and compare what you get.

Usage:
    python client.py tcp                 # to tcp_echo_server.py on 9000
    python client.py udp                 # to udp_echo_server.py on 9001
    python client.py udp --count 20      # try with the server's --drop option
"""

import argparse
import socket
import time

p = argparse.ArgumentParser()
p.add_argument("proto", choices=["tcp", "udp"])
p.add_argument("--port", type=int)
p.add_argument("--count", type=int, default=5)
args = p.parse_args()

messages = [f"message {i}" for i in range(1, args.count + 1)]

if args.proto == "tcp":
    port = args.port or 9000
    start = time.perf_counter()
    # create_connection performs the three-way handshake; it raises if the port is closed
    with socket.create_connection(("127.0.0.1", port), timeout=3) as s:
        local = s.getsockname()
        print(f"Connected in {(time.perf_counter() - start) * 1000:.1f} ms "
              f"from {local[0]}:{local[1]} (ephemeral port chosen by the OS)")
        for m in messages:
            s.sendall(f"{m}\n".encode())
            print("  <-", s.recv(1024).decode().strip())
    print("Closed (FIN sent). Every message arrived, in order - TCP guarantees it.")

else:
    port = args.port or 9001
    received = 0
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(0.5)
        for m in messages:
            s.sendto(m.encode(), ("127.0.0.1", port))  # no handshake: the first packet IS the data
            try:
                data, _ = s.recvfrom(2048)
                print("  <-", data.decode())
                received += 1
            except socket.timeout:
                print(f"  ?? no reply for {m!r} - lost, and UDP won't tell you or resend it")
            except ConnectionResetError:
                # Windows reports an ICMP 'port unreachable' as a reset on the next UDP call
                print("  !! ICMP port unreachable - is udp_echo_server.py running?")
                break
    print(f"{received}/{len(messages)} replies. Any recovery (retry, ordering) is the app's job with UDP.")
