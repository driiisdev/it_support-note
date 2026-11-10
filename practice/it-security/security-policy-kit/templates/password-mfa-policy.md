# Password & MFA Policy (template)

> Based on current guidance (e.g. NIST SP 800-63B): **length over complexity, no forced periodic
> changes, block known-breached passwords, MFA everywhere.** Adjust to your regulatory requirements.

| | |
|---|---|
| Applies to | All user, admin, and service accounts |
| Owner | IT Security |
| Version / date | 1.0 / [date] |

## Passwords

| Rule | Standard accounts | Admin accounts |
|---|---|---|
| Minimum length | 12 characters (passphrases encouraged) | 16 characters |
| Complexity rules | not required - length matters more | not required |
| Breached / common passwords | blocked (checked against a banned list) | blocked |
| Periodic forced change | **no** - change only on suspected compromise | no |
| Reuse | never reuse company passwords elsewhere | same |
| Storage | approved password manager only | password manager / PAM vault |

## Multi-factor authentication

- **Required** for: email/Microsoft 365, VPN, remote access, all admin accounts, any internet-facing app.
- Approved methods, strongest first: **FIDO2 security key / passkey** → authenticator app push with
  **number matching** → authenticator TOTP code. **SMS only as a last resort.**
- Never approve an MFA prompt you didn't trigger - report it (your password may be known).

## Lockout

- Account locks for 15 minutes after **5** failed attempts (balances brute-force protection against
  lockout-as-denial-of-service).

## Resets (service desk procedure)

1. **Verify identity** before any password or MFA reset: callback to the number on file, manager
   confirmation, or ID check in person. Never reset based on caller ID or email alone.
2. Set a **temporary** password with **"change at next logon."**
3. Log the reset in the ticket (who, verified how, when).

## Admin and service accounts

- Admins use a **separate** admin account for admin tasks; daily account has no admin rights.
- Service accounts: long random passwords (or managed service accounts / gMSA), no interactive logon,
  owner documented.
