# Practice: Infrastructure Services Check (Network & Infrastructure Services)

Concept note:
[`network-and-infrastructure-services.md`](<../../../concepts/system administration it infrastructure services/network-and-infrastructure-services.md>)

## What this demonstrates

Three services everything else silently depends on - checked the way a sysadmin would:

- **`sntp_client.py`** - an **NTP client from scratch**: one 48-byte UDP packet to port 123, four
  timestamps, and the two formulas NTP uses to compute round-trip **delay** and your clock's
  **offset**. Flags the 5-minute skew that breaks Kerberos / Active Directory logons.
- **`dns_health.py`** - checks that DNS records match what they *should* be (A, AAAA, MX, TXT/SPF,
  CNAME, NS) on **each** DNS server you rely on - catches drift, failed migrations, and split-DNS
  differences. Exits non-zero on failure so a scheduler can alert.
- **`dhcp_scope_check.py`** - validates a DHCP scope design **before** you build it: gateway in the
  pool, duplicate reservations, static devices not excluded, pool too small for the expected clients.

## Scenario

Monday morning: "some people can't log in" (clock skew?), "email to us is bouncing since the
migration" (MX record?), and a new floor's DHCP scope needs reviewing before go-live.

## Folder structure

```
infra-services-check/
  sntp_client.py         <- SNTP (RFC 4330) query, offset/delay math, stratum + reference
  dns_health.py          <- expected vs actual records across several DNS servers
  expected-records.csv   <- name,type,expected  (includes 2 deliberate failures)
  dhcp_scope_check.py    <- scope design validator
  scope.json             <- a scope with deliberate mistakes to find and fix
```

## Code walkthrough

**NTP in four timestamps:**

```
T1 client sends  ->  T2 server receives ... T3 server replies  ->  T4 client receives

delay  = (T4 - T1) - (T3 - T2)          # network round trip, minus server processing time
offset = ((T2 - T1) + (T3 - T4)) / 2    # how far your clock is from the server's
```

The first byte `0x23` packs three fields: leap indicator 0, version 4, mode 3 (client). NTP
timestamps count from **1900**, hence `NTP_EPOCH_OFFSET = 2208988800` seconds to convert to Unix time.
The reply's **stratum** tells you how far the server is from a reference clock.

**DNS health** sends raw queries straight to each server (bypassing your OS cache and hosts file,
which could hide problems), then compares:

```csv
gmail.com,MX,gmail-smtp-in.l.google.com      # this value must be among the answers
gmail.com,TXT,v=spf1                         # TXT: substring match
example.com,A,*                              # any answer is fine, just must resolve
```

**DHCP scope check** uses Python's `ipaddress` to test membership: `gateway in pool`,
`static_ip in pool - exclusions`, capacity vs `expected_clients`.

## Run it

```bash
python sntp_client.py
python sntp_client.py time.windows.com time.google.com
python dns_health.py
python dns_health.py --servers 192.168.1.1 8.8.8.8      # your router/internal DNS vs public
python dhcp_scope_check.py                              # exits 1 while errors remain
```

Expected:

```
pool.ntp.org (23.132.28.58)
  stratum     : 3  (syncs from 148.113.173.205)
  round trip  : 18.0 ms
  clock offset: -1122.9 ms  (+ = your clock is behind)
  ! more than 1 second off - check the Windows Time service (w32tm /query /status)

  [FAIL] gmail.com     MX     missing mail.example.com | got: alt4.gmail-smtp-in.l.google.com, ...

  [ERROR] gateway 10.20.0.1 is inside the dynamic pool - DHCP could hand it to a laptop ...
  [ERROR] static device ip-camera-lobby 10.20.0.30 is inside the pool and NOT excluded ...
  [ERROR] pool has 148 leasable addresses for 180 expected clients -> scope exhaustion ...
```

## Try this yourself

- Compare `sntp_client.py`'s offset with `w32tm /stripchart /computer:pool.ntp.org /samples:3`.
  Then run `w32tm /query /status` to see which source your PC actually syncs from.
- Change your PC clock by 10 minutes (and back!) and watch the 5-minute warning appear.
- **Fix `scope.json`** until `dhcp_scope_check.py` reports 0 errors: move the pool to start at `.21`,
  exclude the camera, de-duplicate the reservations, and decide whether a /24 is enough for 180
  clients plus growth (see [subnet-planner](../../computer-networking/subnet-planner)).
- Put your own domain (or your company's, read-only) into `expected-records.csv`: website A/CNAME,
  MX, SPF TXT, and `_dmarc` TXT.
- Schedule `dns_health.py` with Windows Task Scheduler / cron and alert on a non-zero exit code.

## Real-world equivalent

- `w32tm`, `chronyc tracking`, `ntpq -p`; AD's time hierarchy (PDC emulator → DCs → clients).
- DNS monitoring in tools like Uptime Kuma, Pingdom, or a simple scheduled `dig` script after
  every DNS change.
- Windows Server DHCP / Kea / router DHCP - with the same scope, exclusion, and reservation
  concepts this validator checks.
