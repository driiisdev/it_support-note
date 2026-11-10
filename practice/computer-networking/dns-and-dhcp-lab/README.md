# Practice: DNS, DHCP & NAT Lab (Networking Services)

Concept note:
[`networking-services.md`](<../../../concepts/computer networking/networking-services.md>)

## What this demonstrates

The three services that make a network usable, built from their actual mechanics:

- **`dns_query.py`** - a real DNS client **from raw bytes**: builds the query packet, sends it to a
  resolver over UDP 53, and parses A/AAAA/MX/TXT/CNAME/NS/SOA answers (including name compression).
  Shows TTLs, NXDOMAIN, and what happens when an answer is too big for UDP.
- **`dhcp_dora_sim.py`** - a DHCP server simulation: scope, exclusion, reservation, the DORA
  exchange, renewal at 50% of the lease, lease expiry, and **scope exhaustion → 169.254.x.x**.
- **`nat_table_sim.py`** - how a router rewrites private sockets to one public IP, routes replies
  back by port, drops unsolicited inbound traffic, and how port forwarding changes that.

## Scenario

Three tickets in one morning: *"a website changed servers but I still reach the old one"* (DNS
TTL/cache), *"new laptops on floor 3 get 169.254 addresses"* (DHCP exhaustion), and *"we need the
camera system reachable from outside"* (port forwarding). You build each mechanism to understand it.

## Folder structure

```
dns-and-dhcp-lab/
  dns_query.py       <- raw-socket DNS client (talks to a real resolver)
  dhcp_dora_sim.py   <- simulated DHCP server + clients (no real broadcasts sent)
  nat_table_sim.py   <- simulated NAT/PAT router
```

## Code walkthrough

**A DNS query is 12 bytes of header + the question.** Names are encoded as length-prefixed
labels:

```python
header = struct.pack("!HHHHHH", tid, 0x0100, 1, 0, 0, 0)   # ID, flags (RD=1), 1 question
qname  = b"".join(bytes([len(l)]) + l.encode() for l in name.split(".")) + b"\x00"
# "example.com" -> 07 'example' 03 'com' 00
```

**Name compression**: in answers, a byte starting with bits `11` (`0xC0`) is a pointer back to a
name that already appeared, so `example.com` isn't repeated in every record:

```python
if length & 0xC0 == 0xC0:
    pointer = struct.unpack("!H", msg[offset:offset + 2])[0] & 0x3FFF
```

**The transaction ID check** (`r["id"] != tid`) matters: a random ID is one of the defenses
against spoofed DNS replies (cache poisoning).

**Truncation (TC flag)**: when an answer doesn't fit in a UDP reply (e.g. `google.com TXT`), the
client retries over **TCP 53**, where each message gets a 2-byte length prefix (TCP is a byte stream,
so you need framing). If your network blocks TCP 53, you'll see that explained instead - a real
misconfiguration that breaks large DNS answers.

> Tested note: on the network these were built on, outbound TCP 53 was blocked, so the TCP fallback
> path was only verified to fail gracefully. Try it on a home network.

**DHCP** follows the real decision logic: reservations first, then the client's previous address
(so devices keep the same IP), then the first free address not excluded, leased, or offered.
REQUEST is **broadcast** so other DHCP servers know their offers were declined.

**NAT** keys its table on the full socket - two laptops can both use private port 50000 because the
router gives each a different **public** port.

## Run it

```bash
python dns_query.py example.com
python dns_query.py example.com AAAA
python dns_query.py gmail.com MX
python dns_query.py google.com TXT --server 1.1.1.1
python dns_query.py www.github.com CNAME
python dns_query.py doesnotexist.example NS

python dhcp_dora_sim.py
python dhcp_dora_sim.py --small     # 2-address pool -> exhaustion -> APIPA

python nat_table_sim.py
```

Expected (excerpts):

```
ANSWER SECTION  (TTL = seconds this answer may be cached)
  gmail.com                       202  MX     priority 5   gmail-smtp-in.l.google.com
  ...
Reply  : 113 bytes over UDP in 8 ms, status NXDOMAIN (name does not exist)

laptop-tunde (8C:16:45:AA:10:2F) boots - has no IP, uses source 0.0.0.0
  [server] scope exhausted - no OFFER sent
  (no OFFER after retries) -> self-assigns APIPA 169.254.81.8  <- the classic ticket clue

IN   198.51.100.7:40000 -> 203.0.113.5:443  no entry  ->  DROPPED
```

## Try this yourself

- Run `python dns_query.py example.com` twice against `8.8.8.8` - the TTL counts down between runs
  (you're seeing the resolver's cache). Then compare with `nslookup example.com` and
  `Resolve-DnsName example.com`.
- Query your **router** as the server (`--server 192.168.1.1`, check `ipconfig` for its address) and
  compare speed with `8.8.8.8` - local caching resolvers are usually fastest.
- Look up your own email domain's `MX` and `TXT` records - find the SPF record (`v=spf1 ...`).
- Add `PTR` lookups: reverse `8.8.8.8` by querying `8.8.8.8.in-addr.arpa` (octets reversed).
- In `dhcp_dora_sim.py`, add a static device at `.102` **without** excluding it, then show the IP
  conflict a real network would get. Fix it with an exclusion.
- Add a NAT **timeout** to `nat_table_sim.py`: entries idle > 300 s are removed, and a late reply
  gets dropped (a real cause of "my long-running connection randomly dies").
- On Windows: `ipconfig /all` → find **DHCP Server**, **Lease Obtained**, **Lease Expires** for your
  adapter; `ipconfig /displaydns` → your local DNS cache with remaining TTLs.

## Real-world equivalent

- `nslookup`, `dig`, `Resolve-DnsName` do exactly what `dns_query.py` does.
- Windows Server DHCP / ISC Kea / your home router implement the same scope/exclusion/reservation
  model; "scope exhausted" is a real alert in DHCP server logs.
- Every home router and office firewall does PAT; "port forwarding" and "NAT rules" are the same
  table with static entries.
