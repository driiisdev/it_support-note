# The 3 As of Cybersecurity: Authentication, Authorization, Accounting

Three separate questions, often confused:

| A | Question | Example |
|---|---|---|
| **Authentication** | *Who are you?* (prove it) | password + MFA code |
| **Authorization** | *What are you allowed to do?* | Jane may read the Finance share but not write |
| **Accounting** | *What did you do?* | log: Jane opened `budget.xlsx` at 10:42 |

**Identification** (claiming an identity - typing a username) comes before authentication
(proving it).

> 🖼️ **Image idea: AAA flow** - a user passing three gates in order: "Who are you?" →
> "What can you do?" → "Logged: what you did".
> Suggested file: `assets/img/aaa-flow.png`
<!-- ![aaa flow](<../../assets/img/aaa-flow.png>) -->

## Authentication

### Authentication factors

| Factor | Something you... | Examples |
|---|---|---|
| Knowledge | **know** | password, PIN, security question |
| Possession | **have** | phone authenticator app, hardware security key, smart card |
| Inherence | **are** | fingerprint, face, iris |

(Sometimes added: **somewhere you are** - location/IP; **something you do** - typing pattern.)

**Multi-factor authentication (MFA)** = two or more **different** factors. Password + security
question is *not* MFA (both are "know").

### Strong passwords

- **Length beats complexity**: a long passphrase (`correct-horse-battery-staple`) beats `P@ss1!`.
- Don't reuse passwords → use a **password manager**.
- Check against lists of breached passwords.
- Lock out after repeated failures (but beware of locking out users as a DoS).

### One-time passwords (OTP)

| Type | How it works |
|---|---|
| **HOTP** (HMAC-based) | code = HMAC(secret, **counter**); counter increments on each use |
| **TOTP** (time-based) | code = HMAC(secret, **current 30-second window**); used by Google/Microsoft Authenticator |
| SMS / email codes | convenient but weaker (SIM swapping, interception) |

TOTP setup: the server and app share a **secret** (the QR code). Both compute the same 6-digit
code from the secret + time, so no network connection is needed on the phone.

### Stronger second factors

- **Push notifications with number matching** (Microsoft Authenticator) - resists "MFA fatigue"
  spamming attacks.
- **FIDO2 / U2F / passkeys / hardware keys (YubiKey)** - cryptographic challenge-response bound to
  the real website's domain → **phishing-resistant**: a fake site can't use the response.
- **Smart cards / certificates** - a private key on a chip; common in government and enterprise.

### Biometrics

Convenient, but you can't change your fingerprint if it leaks. Usually used to **unlock a local
key** (Windows Hello, Face ID) rather than sent to a server.

### Network authentication protocols

| Protocol | What it does |
|---|---|
| **RADIUS** | central AAA server for network access - Wi-Fi (WPA2-Enterprise / 802.1X), VPN, switch logins. UDP 1812/1813. |
| **Kerberos** | ticket-based authentication used by **Active Directory**. Users get a **Ticket Granting Ticket** at logon, then service tickets for each resource - the password isn't sent over the network. Needs clocks in sync (5 min). |
| **TACACS+** | Cisco's AAA protocol for administering network devices; separates the 3 As and encrypts the full payload. TCP 49. |
| **LDAP** | directory lookups and (with bind) authentication |

### Single sign-on (SSO)

Log in **once**, access many applications. Implemented with Kerberos (inside the AD network) or
**SAML** / **OpenID Connect** (web/cloud apps via an identity provider like Entra ID, Okta,
Google). Pros: fewer passwords, central control. Cons: the SSO account becomes a high-value
target → protect it with strong MFA.

## Authorization

Once you know *who* someone is, decide *what they can do*.

### Access control models

| Model | How access is decided |
|---|---|
| **ACLs** (access control lists) | list of who can do what on each resource (NTFS permissions, firewall rules) |
| **RBAC** - role-based | permissions are assigned to **roles** ("HR", "Helpdesk"); users get roles |
| **ABAC** - attribute-based | rules on attributes (department = Finance AND device = compliant AND time = working hours) |
| **DAC** | the owner of a resource decides who gets access |
| **MAC** (mandatory) | system-wide labels (Secret, Top Secret) decide; owners can't override |

### Principle of least privilege

Only the minimum access needed, only for as long as needed. Practices:

- Separate **admin accounts** from daily accounts.
- **Just-in-time** elevation for admin tasks.
- Regular **access reviews** - remove access people no longer need (people change roles and keep
  collecting permissions: "privilege creep").

### OAuth

**OAuth 2.0** is an **authorization** framework: lets you grant an app limited access to your data
on another service **without giving it your password** ("Allow this app to read your calendar?").
The app receives an **access token** with specific **scopes**. (OpenID Connect adds
authentication on top of OAuth.) Users should be careful what scopes they approve - malicious
apps abuse consent prompts.

## Accounting

Recording **what happened**, so you can audit, investigate, and bill.

- What's recorded: who logged in, when, from where, what they accessed or changed, failed attempts.
- **TACACS+** accounting: commands run on network devices.
- **RADIUS** accounting: session start/stop, duration, data transferred (ISPs bill this way).
- **Audit logs**: Windows Security log (4624 logon, 4625 failed logon, 4720 user created, 4728
  added to a group), Linux `auth.log`, cloud admin audit logs.
- Logs should go to a **central** place (SIEM) so an attacker on one host can't erase their tracks.

## How it's used in real IT support

| Ticket | Which A |
|---|---|
| "I can't log in" / locked out / MFA phone lost | authentication |
| "Access denied to the HR folder" | authorization |
| "Who deleted this file?" / "Was my account used from another country?" | accounting |

Always verify identity before resetting passwords or MFA - attackers target the help desk exactly
because it can bypass authentication.

## Practice project

[`practice/it-security/auth-lab`](<../../practice/it-security/auth-lab>) -
a mini login system covering all three As: salted PBKDF2 password storage, **TOTP implemented from
scratch** (verified against the RFC 6238 test vector, and compatible with real authenticator
apps), lockout after failed attempts, **RBAC** permission checks, and an append-only audit log with
a report of failed logins.

## Related

- [Pelcgbybtl (cryptology)](<pelcgbybtl-cryptology.md>) - hashing and HMAC behind passwords and OTPs.
- [Directory services](<../system administration it infrastructure services/directory-services.md>) - Kerberos and AD.
- [Users and permissions](<../os power user/users-and-permissions.md>) - OS-level authorization.
