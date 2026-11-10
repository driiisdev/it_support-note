# Practice: Service Health Monitor (Software & Platform Services)

Concept note:
[`software-and-platform-services.md`](<../../../concepts/system administration it infrastructure services/software-and-platform-services.md>)

## What this demonstrates

How you find out a service is broken **before users call**:

- **HTTP checks** - status code, response time, and *content* (a 200 that returns an error page
  is still broken). Status codes are translated into likely causes (502 = proxy can't reach the app).
- **TCP port checks** - is SMTP (587), IMAPS (993), SMB (445), RDP (3389)... actually listening?
- **TLS certificate checks** - days until expiry, issuer, and the three classic certificate failures:
  **expired**, **self-signed**, **hostname mismatch** (live demos via `badssl.com`).
- A local **lab web app** with a healthy page, a slow page, and a broken page, so you can watch the
  board turn green / yellow / red.

## Scenario

Last quarter the company website's certificate expired at 2 a.m. on a Saturday and nobody noticed
until Monday. Your manager asks for "something that tells us when services are down, slow, or about
to expire."

## Folder structure

```
service-health-monitor/
  health_check.py    <- runs all checks in parallel, status board, exit code 1 if anything is DOWN
  services.json      <- what to check (lab app, public site, mail ports, certs incl. failure demos)
  lab_web_server.py  <- local app on :8080 with /health, /slow, /broken + an access log
```

The runbook template in [it-asset-runbook](../it-asset-runbook/templates/runbook-template.md) uses
this script as its post-patching verification step.

## Code walkthrough

**HTTP errors are information, not crashes** - `urllib` raises on 4xx/5xx, so the check catches
`HTTPError` and still reports the code:

```python
except urllib.error.HTTPError as e:
    code = e.code          # 500 -> "app crashed", 502 -> "proxy can't reach the app", ...
```

**Certificate expiry** comes straight from the server's certificate after a real TLS handshake:

```python
cert = tls.getpeercert()
expires = ssl.cert_time_to_seconds(cert["notAfter"])
```

and verification failures are reported with OpenSSL's reason (`certificate has expired`,
`self-signed certificate`, `Hostname mismatch`).

**Exit codes** make it automatable: `0` = all up, `1` = something is down. Task Scheduler, cron, or a
CI pipeline can alert on that without parsing output.

## Run it

```bash
# terminal 1
python lab_web_server.py
# terminal 2
python health_check.py
python health_check.py --watch 30        # then stop the lab server and watch it go DOWN
```

Expected:

```
STATUS SERVICE                     TYPE  DETAIL
DOWN   Lab web app - broken        http  HTTP 500 (expected 200) app crashed
DOWN   Lab SMTP (nothing)          tcp   port 2525 refused - service not running?
DOWN   Cert: expired (demo)        tls   certificate invalid: certificate has expired
DOWN   Cert: self-signed (demo)    tls   certificate invalid: self-signed certificate
DOWN   Cert: wrong host (demo)     tls   certificate invalid: Hostname mismatch, ...
WARN   Lab web app - slow page     http  HTTP 200 but slow: 1426 ms (limit 500)
UP     Lab web app (local)         http  HTTP 200 in 228 ms
UP     Cert: github.com            tls   TLSv1.3, expires 2027-01-27 (79 days), issuer Sectigo Limited
```

### Two real-world lessons from testing this

- **Mail ports timing out** (`smtp.gmail.com:587`, `imap.gmail.com:993`) on a corporate or guest
  network usually means the network **blocks outbound mail ports** - a common policy. The check is
  right; the network is the reason. Try from home.
- **"unable to get local issuer certificate"** on a site that works fine in the browser: the
  certificate chain ends at a root CA that isn't in **this machine's** trust store yet. Windows
  downloads missing roots on demand for browsers, but other programs (Python, Java, some agents)
  don't trigger that. On the test machine, `example.com` failed this way (its chain ends at
  *SSL.com TLS ECC Root CA 2022*). Diagnose with
  `openssl s_client -connect example.com:443 -servername example.com` and look at the last `i:` line.

## Try this yourself

- Add your own services: your router's admin page, a NAS, your company's VPN portal (TCP 443), etc.
- Set `warn_days` to `100` on the github.com check and watch it turn yellow.
- Add a `"type": "dns"` check that resolves a name and compares with an expected IP (borrow
  `resolve()` from [infra-services-check](../infra-services-check/dns_health.py)).
- Write results to a CSV each run and compute **uptime %** per service over a day.
- Schedule it every 5 minutes with Task Scheduler (`Action: python health_check.py`, alert on exit
  code 1 by sending an email or a Teams/Slack webhook).
- Put `lab_web_server.py` behind a reverse proxy (Nginx or IIS) and stop the app: the monitor should
  now show **502**, not "unreachable" - that's how you tell "proxy up, app down" apart.

## Real-world equivalent

- **Uptime Kuma**, **Nagios/Icinga**, **Zabbix**, **PRTG**, **Pingdom**, **StatusCake** - same checks,
  plus history, graphs, and notifications.
- Certificate monitoring is so important that ACME clients (Let's Encrypt's `certbot`) auto-renew at
  30 days remaining, and many monitors alert at 21 / 14 / 7 days.
