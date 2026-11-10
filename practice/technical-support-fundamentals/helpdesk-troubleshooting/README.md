# Practice: Help Desk Troubleshooting (Troubleshooting, Networking basics)

Concept notes:
[`troubleshooting.md`](<../../../concepts/technical support fundamentals/troubleshooting.md>) ·
[`networking.md`](<../../../concepts/technical support fundamentals/networking.md>)

## What this demonstrates

The troubleshooting method as tools you actually use:

1. **`connectivity_check.py`** - "isolate the problem" for the most common ticket of all, *"the
   internet is down"*: it works outward from the PC layer by layer and stops at the **first
   failure**, which is where the cause is.
2. **`ticket.py`** - a minimal ticket tracker that **forces good documentation**: impact,
   symptoms, every step tried, root cause, and fix. Escalating carries the full history along,
   so tier 2 doesn't repeat your steps.
3. **`scenarios.md`** + **`kb-template.md`** - practice drills and a knowledge-base article format.

## Scenario

You're on a help desk. Tickets come in by phone; you need to diagnose network complaints
quickly, keep a clean record of each ticket, and turn repeat problems into KB articles.

## Folder structure

```
helpdesk-troubleshooting/
  connectivity_check.py   <- local IP -> gateway -> internet by IP -> DNS -> HTTPS
  ticket.py               <- new / list / show / note / escalate / close / report / demo
  sample-tickets.json     <- 4 realistic tickets (loaded by `ticket.py demo`)
  kb-template.md          <- knowledge-base article format, filled in from ticket #1
  scenarios.md            <- 6 practice drills with collapsible hints
  tickets.json            <- created when you use ticket.py (gitignored)
```

## Code walkthrough

**Each check depends on the one before it** - that ordering *is* the isolation method:

```python
if not step("1. Local IP address", ...):           return   # no IP? nothing else can work
step("2. Default gateway reachable", ...)                   # (some routers block ping - not fatal)
if not step("3. Internet by IP (8.8.8.8:53)", ...): return  # router/ISP problem
if not step("4. DNS resolves www.google.com", ...): return  # works by IP but not by name = DNS
step("5. HTTPS to www.google.com", ...)                     # proxy, TLS, clock, or the site
```

Details that come from real tickets:

- `169.254.x.x` is detected and labeled **APIPA → DHCP unreachable**.
- Step 3 uses a **TCP connection to port 53** instead of ping, because many networks block ICMP -
  a failed ping doesn't always mean "no internet."
- A TLS certificate failure suggests checking the **PC's date/time** - a wrong clock makes valid
  certificates look expired.

**`ticket.py close` refuses to close without a root cause and fix**, and `report` highlights
**repeat root causes** - the signal that something needs a permanent fix or a KB article.

## Run it

```bash
python connectivity_check.py
python connectivity_check.py --host intranet.example.com

python ticket.py demo              # load sample tickets
python ticket.py list --all
python ticket.py show 3
python ticket.py note 3 "Added AV exclusion for OneDrive folder per policy"
python ticket.py close 3 --cause "AV scanning OneDrive folder on every change" --fix "Added exclusion"
python ticket.py report
python ticket.py new               # interactive
```

Expected (`connectivity_check.py` on a healthy network):

```
[PASS] 1. Local IP address                192.168.1.25  (private address, behind NAT)
[PASS] 2. Default gateway reachable       192.168.1.1 3 ms
[PASS] 3. Internet by IP (8.8.8.8:53)     14 ms
[PASS] 4. DNS resolves www.google.com     142.250.x.x
[PASS] 5. HTTPS to www.google.com         HTTP/1.1 200 OK (TLSv1.3)
```

## Try this yourself

Break things on purpose (in a VM ideally) and watch which step fails:

- **Disable Wi-Fi / unplug the cable** → step 1 fails.
- **Set a wrong DNS server** (e.g. `10.255.255.1`) in adapter settings → steps 1-3 pass, step 4 fails.
  That's the "internet is down but it's really DNS" ticket.
- **Add `127.0.0.1 www.google.com` to your hosts file** (admin, then remove it!) → DNS "resolves"
  but HTTPS fails - a malware/hosts-file scenario.
- **Set your clock a year ahead** → step 5 fails with a certificate error.
- Work through every drill in `scenarios.md` and log each as a ticket with `ticket.py new`.
- Write a second KB article from sample ticket #2 using `kb-template.md`.
- Extend `ticket.py` with an **SLA check**: flag P1 tickets open > 1 h and P2 > 4 h.

## Real-world equivalent

- Ticketing systems: ServiceNow, Jira Service Management, Zendesk, Freshservice - same fields
  (priority, category, impact, work notes, resolution), same escalation flow.
- Connectivity diagnostics: Windows' built-in network troubleshooter, and the first 5 minutes of
  every network ticket a help desk tech handles manually with `ipconfig`, `ping`, and `nslookup`.
