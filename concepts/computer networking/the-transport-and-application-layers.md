# The Transport and Application Layers

IP gets a packet to the right **computer**. The **transport layer** gets it to the right
**program** on that computer, and (with TCP) makes sure it arrives completely and in order. The
**application layer** is the actual content the program understands (a web page, an email).

## Multiplexing, demultiplexing and ports

One computer runs many network programs at once (browser, email, Teams). The transport layer
uses **port numbers** (16 bits → 0-65535) to keep them apart:

- **Multiplexing** - many programs' data sent out over one network connection.
- **Demultiplexing** - incoming data delivered to the correct program by port number.

A **socket address** = IP + port, e.g. `10.1.1.100:443`.

| Range | Name | Examples |
|---|---|---|
| 0-1023 | system / well-known ports | 22 SSH, 25 SMTP, 53 DNS, 80 HTTP, 443 HTTPS |
| 1024-49151 | registered ports | 3306 MySQL, 3389 RDP, 5432 PostgreSQL |
| 49152-65535 | ephemeral (dynamic) ports | temporary source ports your client picks for each outgoing connection |

Common ports worth memorizing:

| Port | Protocol | Port | Protocol |
|---|---|---|---|
| 20/21 | FTP | 110 / 995 | POP3 / POP3S |
| 22 | SSH, SFTP, SCP | 123 | NTP (UDP) |
| 23 | Telnet (insecure) | 143 / 993 | IMAP / IMAPS |
| 25 / 587 | SMTP / submission | 389 / 636 | LDAP / LDAPS |
| 53 | DNS (UDP & TCP) | 443 | HTTPS |
| 67/68 | DHCP (UDP) | 445 | SMB (file sharing) |
| 80 | HTTP | 3389 | RDP |

## TCP vs UDP

| | TCP | UDP |
|---|---|---|
| Connection | connection-oriented (handshake first) | connectionless (just send) |
| Reliability | guaranteed delivery, retransmits lost data | no guarantee |
| Ordering | in order | may arrive out of order |
| Overhead | higher (headers, acknowledgments) | low |
| Used by | web, email, file transfer, SSH | DNS lookups, DHCP, VoIP, video calls, gaming, streaming |

UDP is used when **speed matters more than perfection** (a dropped video frame is better than a
frozen call) or when the request is tiny (DNS).

## The TCP segment

```
+---------------------------+---------------------------+
|      Source port (16)     |   Destination port (16)   |
+---------------------------+---------------------------+
|                 Sequence number (32)                  |
+-------------------------------------------------------+
|              Acknowledgment number (32)               |
+--------+--------+---------+---------------------------+
| Offset |Reserved| Flags   |        Window (16)        |
+--------+--------+---------+---------------------------+
|       Checksum (16)       |    Urgent pointer (16)    |
+---------------------------+---------------------------+
|                Options (optional)                     |
+-------------------------------------------------------+
|                Data (payload)                         |
+-------------------------------------------------------+
```

- **Sequence number** - position of this segment's data in the stream (lets the receiver put
  segments back in order).
- **Acknowledgment number** - the next sequence number the sender of this segment expects to
  receive ("I've got everything up to here").
- **Window** - how much data the receiver can accept right now (**flow control**).
- **Checksum** - error detection.

### TCP control flags

| Flag | Meaning |
|---|---|
| **SYN** | synchronize - start a connection |
| **ACK** | the acknowledgment number field is valid |
| **FIN** | I'm done sending - close gracefully |
| **RST** | reset - abort the connection immediately (e.g. port closed) |
| **PSH** | push this data to the application now, don't buffer |
| **URG** | urgent pointer field is valid (rarely used) |

## The three-way handshake

```
Client                               Server
  |  ---- SYN (seq=x) ------------->   |   "I'd like to talk"
  |  <--- SYN-ACK (seq=y, ack=x+1) -   |   "OK, and I'd like to talk too"
  |  ---- ACK (ack=y+1) ----------->   |   "Great"
  |        ESTABLISHED - data flows    |
```

Closing uses a **four-way** exchange: FIN → ACK, then the other side's FIN → ACK (each direction
closes independently).

> 🖼️ **Image idea: TCP handshake + teardown sequence diagram** - two vertical timelines, SYN /
> SYN-ACK / ACK at the top, data in the middle, FIN/ACK/FIN/ACK at the bottom.
> Suggested file: `assets/img/tcp-handshake.png`
<!-- ![tcp handshake](<../../assets/img/tcp-handshake.png>) -->

## TCP socket states

| State | Meaning |
|---|---|
| LISTEN | server waiting for connections on a port |
| SYN_SENT | client sent SYN, waiting for SYN-ACK |
| SYN_RECEIVED | server got SYN, sent SYN-ACK |
| ESTABLISHED | open, data flowing |
| FIN_WAIT | this side sent FIN, waiting |
| CLOSE_WAIT | other side closed; this side's app hasn't closed yet |
| TIME_WAIT | waiting a bit before fully closing (catches stray late packets) |
| CLOSED | done |

See them live with `netstat -an` (Windows/Linux) or `ss -tan` (Linux). Lots of `CLOSE_WAIT` on a
server = an app that isn't closing its connections (bug).

## Firewalls (transport-layer view)

A **firewall** allows or blocks traffic based on rules - usually by **IP, port, and protocol**.
"The app can't connect" is very often a firewall blocking a port. Quick test:

```powershell
Test-NetConnection server01 -Port 443      # Windows
```

```bash
nc -zv server01 443                         # Linux/macOS
```

- **Connection refused** (fast RST) → host is reachable, nothing listening on that port.
- **Timeout** → packets dropped silently (firewall) or host unreachable.

## The application layer

The **application layer** is the protocol the program itself speaks: HTTP for web, SMTP/IMAP for
email, SSH for remote shells, DNS for names. Each defines message formats and rules - e.g. HTTP's
`GET /index.html` request and `200 OK` response.

**OSI vs 5-layer**: OSI adds **Session** (setting up/managing sessions) and **Presentation**
(encryption, encoding, compression) between transport and application. In practice those jobs
happen inside the app or libraries (TLS, for example).

## All the layers working together

What happens when a laptop at `10.1.1.100` opens `http://172.16.1.100`:

1. **Application** - browser builds an HTTP `GET` request.
2. **Transport** - OS picks an ephemeral source port (e.g. 50000), destination port 80; TCP
   handshake happens first.
3. **Network** - destination 172.16.1.100 is on a different subnet → send to the **default
   gateway** (e.g. 10.1.1.1). IP header: src 10.1.1.100, dst 172.16.1.100, TTL 64.
4. **Data link** - ARP for the gateway's MAC; build an Ethernet frame to the gateway's MAC.
5. **Physical** - bits go out over the cable/Wi-Fi.
6. **Router** - strips the frame, checks the IP destination in its routing table, decrements TTL,
   builds a new frame for the next hop's MAC. (Repeat per router.)
7. **Server** - unwraps frame → IP → TCP (port 80 → the web server process) → HTTP request.
8. The response comes back the same way, in reverse.

## Practice project

[`practice/computer-networking/socket-lab`](<../../practice/computer-networking/socket-lab>) -
a TCP echo server vs a UDP echo server side by side, plus a **port checker** that tells "open"
vs "refused" vs "filtered/timeout" apart - the exact distinction you use when debugging firewall
tickets.

## Related

- [The network layer](<the-network-layer.md>) - what carries TCP/UDP.
- [Networking services](<networking-services.md>) - DNS and DHCP, two key application-layer services.
- [Securing your networks](<../it security/securing-your-networks.md>) - firewalls in depth.
