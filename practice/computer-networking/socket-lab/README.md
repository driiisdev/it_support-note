# Practice: Socket Lab - TCP vs UDP + Port Checker (Transport & Application Layers)

Concept note:
[`the-transport-and-application-layers.md`](<../../../concepts/computer networking/the-transport-and-application-layers.md>)

## What this demonstrates

- **TCP vs UDP side by side**: the same messages sent both ways. TCP connects first, delivers
  everything in order, and closes with FIN. UDP just sends, and when the server "loses" a datagram,
  nobody notices or resends it.
- **Ports and sockets**: the server listens on a fixed port; each client gets an **ephemeral** port
  from the OS - visible in both sides' output and in `netstat`.
- **OPEN vs CLOSED vs FILTERED** - the three answers a port test can give, and what each one tells
  you in a "the app can't connect" ticket.

## Scenario

A user says "the app can't connect to the server." Is the server down, is the service not running,
or is a firewall in the way? You build small servers to see what each case looks like from
the client side, then use the port checker on real tickets.

## Folder structure

```
socket-lab/
  tcp_echo_server.py   <- listen/accept, one thread per connection, logs ESTABLISHED and FIN
  udp_echo_server.py   <- recvfrom/sendto only; --drop N simulates N% packet loss
  client.py            <- `tcp` or `udp` mode, same messages
  port_check.py        <- OPEN / CLOSED / FILTERED / DNS-FAIL for host:port lists
```

## Code walkthrough

**The socket type is the whole difference:**

```python
socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # TCP: bind, listen, accept, then a byte stream
socket.socket(socket.AF_INET, socket.SOCK_DGRAM)   # UDP: bind, then recvfrom/sendto individual datagrams
```

**TCP's handshake is hidden inside `accept()` / `create_connection()`** - by the time your code
runs, SYN → SYN-ACK → ACK has already happened. An **empty `recv()`** means the other side sent FIN.

**UDP has no connection to fail**, so a lost datagram is just... silence. The client only finds out
because *it* chose to wait 0.5 s for a reply:

```python
except socket.timeout:
    print("no reply - lost, and UDP won't tell you or resend it")
```

**Port states map to TCP behavior:**

| Result | What happened on the wire | Meaning in a ticket |
|---|---|---|
| OPEN | SYN → SYN-ACK → ACK | service is up and reachable - problem is higher up (app, auth, TLS) |
| CLOSED | SYN → **RST** | host is up, nothing listening → service stopped / wrong port |
| FILTERED | SYN → *(nothing)* | firewall dropping traffic, or host down |

> **Windows quirk you'll see**: on Windows, a refused connection takes **~2 seconds** to report,
> because Windows retries the SYN twice after getting a RST (Linux reports it instantly). With a
> short timeout a closed port on Windows looks "filtered" - which is why `port_check.py` defaults
> to 3 s.

## Run it

```bash
# terminal 1
python tcp_echo_server.py
# terminal 2
python udp_echo_server.py --drop 40
# terminal 3
python client.py tcp
python client.py udp --count 10
python port_check.py
python port_check.py 127.0.0.1 9000 9001 135 445
netstat -an | findstr "9000 9001"        # Linux: ss -tuan | grep -E "9000|9001"
```

Expected:

```
Connected in 2.3 ms from 127.0.0.1:64808 (ephemeral port chosen by the OS)
  <- echo: message 1 ... message 5
Closed (FIN sent). Every message arrived, in order - TCP guarantees it.

  ?? no reply for 'message 5' - lost, and UDP won't tell you or resend it
7/8 replies. Any recovery (retry, ordering) is the app's job with UDP.

HOST                    PORT  SERVICE       STATE       DETAIL
127.0.0.1               9000  lab TCP echo  OPEN        9 ms
127.0.0.1               9999                CLOSED      refused in 2041 ms
```

Notice `port_check.py` itself shows up in the TCP server's log as a connection that opens and
immediately closes - that's all a port check is.

## Try this yourself

- While a TCP client is connected, run `netstat -an | findstr 9000` and find **LISTENING** (server)
  and two **ESTABLISHED** rows (one per side). Stop the client and look for **TIME_WAIT**.
- Use Windows Defender Firewall to **block inbound TCP 9000**, then test from another machine on
  your LAN (change `HOST` to `0.0.0.0` in the server) - the port goes from OPEN to FILTERED.
- Run `udp_echo_server.py --drop 50` and add **retry logic** to the UDP client (resend up to 3 times).
  You've just reinvented a tiny piece of TCP - which is exactly what DNS clients do.
- `Test-NetConnection 127.0.0.1 -Port 9000` (PowerShell) - compare with `port_check.py`.
- Add a `services.txt` with your company's (or home lab's) critical services and run
  `python port_check.py --file services.txt` as a morning health check.

## Real-world equivalent

- `Test-NetConnection`, `nc -zv`, `telnet host port`, and **nmap** (for authorized scans) all report
  these same states.
- TCP vs UDP choice in practice: web, email, SSH, SMB use TCP; DNS lookups, DHCP, NTP, VoIP, and
  video calls use UDP - because a late packet is worse than a lost one, or the exchange is one tiny
  request/response.
