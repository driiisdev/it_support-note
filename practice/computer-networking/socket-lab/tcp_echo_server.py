"""
tcp_echo_server.py - a TCP server that shows the connection lifecycle (accept -> data -> close).

Usage:
    python tcp_echo_server.py            # listens on 127.0.0.1:9000
    python tcp_echo_server.py 9100
While it runs, look at it from another terminal:
    netstat -an | findstr 9000           # Windows: LISTENING, then ESTABLISHED per client
    ss -tan | grep 9000                  # Linux
"""

import socket
import sys
import threading

HOST = "127.0.0.1"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 9000


def handle(conn: socket.socket, addr: tuple) -> None:
    # By the time accept() returns, the three-way handshake (SYN, SYN-ACK, ACK) already happened.
    print(f"[+] ESTABLISHED with {addr[0]}:{addr[1]} (client's ephemeral port)")
    with conn:
        while True:
            data = conn.recv(1024)
            if not data:  # empty read = the client sent FIN (closed its side)
                print(f"[-] {addr[0]}:{addr[1]} closed the connection (FIN)")
                break
            text = data.decode(errors="replace").strip()
            print(f"    {addr[1]} -> {text!r}")
            conn.sendall(f"echo: {text}\n".encode())


def main() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:  # SOCK_STREAM = TCP
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((HOST, PORT))
        srv.listen()
        print(f"TCP echo server LISTENING on {HOST}:{PORT}  (Ctrl+C to stop)")
        srv.settimeout(1.0)  # so Ctrl+C works on Windows
        try:
            while True:
                try:
                    conn, addr = srv.accept()
                except socket.timeout:
                    continue
                threading.Thread(target=handle, args=(conn, addr), daemon=True).start()
        except KeyboardInterrupt:
            print("\nstopped")


if __name__ == "__main__":
    main()
