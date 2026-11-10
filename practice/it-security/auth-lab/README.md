# Practice: Auth Lab - Authentication, Authorization, Accounting (The 3 As)

Concept note:
[`the-3-as-of-cybersecurity.md`](<../../../concepts/it security/the-3-as-of-cybersecurity.md>)

## What this demonstrates

A tiny login system where each of the three As is a separate, visible piece:

| A | Implementation |
|---|---|
| **Authentication** | password policy (length > complexity), salted **PBKDF2** storage, **TOTP** second factor built from scratch, **lockout** after 5 failures, the same error for unknown user and wrong password |
| **Authorization** | **RBAC** from `roles.json`: users → roles → permissions, **deny by default**, separation of duties (no unlocking your own account) |
| **Accounting** | every login, failure, lockout, unlock, and access decision appended to `audit.log` (JSON lines), plus a report |

`totp.py` passes the official **RFC 6238 test vectors**, so it produces the same codes as Google /
Microsoft Authenticator - you can enroll a real phone.

## Scenario

Your company is rolling out MFA and wants the help desk to understand what it protects against (and
what it doesn't), why accounts lock, who's allowed to unlock them, and how to answer "was my account
used by someone else?" from logs.

## Folder structure

```
auth-lab/
  totp.py      <- HOTP/TOTP (RFC 4226/6238): selftest / new / now
  auth.py      <- demo / register / enroll-mfa / login / can / unlock / report
  roles.json   <- roles -> permissions, users -> roles
  users.json   <- created at runtime (gitignored)
  audit.log    <- created at runtime (gitignored)
```

## Code walkthrough

**TOTP in a dozen lines** - HMAC the current 30-second time step with the shared secret, then
"dynamically truncate" to 6 digits:

```python
counter = int(time.time() // 30)
mac = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
offset = mac[-1] & 0x0F
code = (struct.unpack(">I", mac[offset:offset + 4])[0] & 0x7FFFFFFF) % 10**6
```

`verify()` accepts ±1 time step to tolerate clock drift - which is why a phone with the wrong time
produces "invalid code" errors (and why [NTP](../../system-administration-it-infrastructure-services/infra-services-check) matters).

**Authentication details that matter:**

- Unknown user and wrong password print the same `Login failed.` - don't help attackers enumerate
  usernames.
- Password OK + MFA wrong gets a specific warning: *your password is known*. That's the real value of
  MFA - the phished password alone wasn't enough.

**Authorization is deny-by-default:**

```python
allowed = "*" in perms or perm in perms     # nothing granted -> DENIED
```

**Accounting**: `audit()` appends one JSON object per event; `report()` answers "who failed to log in,
who got locked, who unlocked whom, what was denied."

## Run it

```bash
python totp.py selftest
python auth.py demo
python auth.py report

# interactive
python auth.py register grace
python auth.py enroll-mfa grace          # add the setup key to a real authenticator app
python auth.py login grace
python auth.py can amina hr-share:read
```

Expected (excerpts of `demo`):

```
--- Attacker has Amina's password (phished) but not her phone
Login failed. (password OK, MFA code wrong - if you didn't try to log in, your password is known!)

--- Brute force against tunde -> lockout after 5 failures
Login failed. (bad password, LOCKED after 5 failures)
Account locked - try again in 15 min or contact the help desk.

amina [staff, finance] -> hr-share:read: DENIED
tunde can't unlock their own account - another help desk member must verify and do it.

Failed logins per user: {'amina': 1, 'tunde': 5}
```

## Try this yourself

- `python totp.py new`, add the secret to Google/Microsoft Authenticator ("enter a setup key"), then
  compare `python totp.py now <secret>` with the app - they match.
- Set your PC clock 2 minutes off and try `login` with your phone's code. Then 10 minutes off.
- Add **HOTP** login (counter-based, like hardware tokens) and handle counter resync.
- Add **backup codes**: 10 one-time codes, stored hashed, each usable once - what MFA-lost-phone
  tickets rely on.
- Add **MFA fatigue protection**: if a user gets more than 3 MFA failures in 5 minutes, alert and
  require a help desk callback.
- Add a time-based **ABAC** rule: `finance-share:write` only between 07:00 and 19:00.
- Turn `audit.log` into a detection: alert when a login succeeds right after several failures (see
  the same idea in [log_analyzer.py](../../os-power-user/process-and-log-monitor/log_analyzer.py)).

## Real-world equivalent

- Microsoft Entra ID / Okta / Google: password + MFA (TOTP, push with number matching, FIDO2), smart
  lockout, conditional access (ABAC), sign-in logs (accounting).
- Active Directory: account lockout policy, security groups (RBAC), Security event IDs 4624/4625/4740
  (accounting).
- Separation of duties for privileged actions is a standard audit requirement (e.g. SOX, ISO 27001).
