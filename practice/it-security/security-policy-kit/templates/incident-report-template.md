# Incident Report INC-2026-007 (example - copy for each incident)

| Field | Value |
|---|---|
| Severity | 2 |
| Status | Closed |
| Reported | 2026-03-04 09:41 by Amina Bello (Finance) via "Report phishing" button |
| Incident lead | Tunde Okafor (Service Desk) |
| Data involved | No personal data confirmed accessed |

## Summary

A phishing email impersonating Microsoft 365 reached 14 staff. One user entered their password on the
fake page at 09:22. The attacker attempted to sign in from an overseas IP at 09:30, but the sign-in was
blocked because **MFA** was required. The account password was reset and the email was purged from all
mailboxes.

## Timeline

| Time | Event |
|---|---|
| 09:12 | Phishing email delivered to 14 mailboxes |
| 09:22 | User A enters credentials on fake login page |
| 09:30 | Sign-in attempt from 198.51.100.23 - password correct, **MFA denied** |
| 09:41 | User B reports the email |
| 09:48 | Service desk identifies all recipients via message trace |
| 09:55 | Email purged from all mailboxes; sender domain and URL blocked |
| 10:05 | User A's password reset, sessions revoked, MFA methods re-verified |
| 10:30 | Sign-in logs reviewed - no successful attacker sign-ins |

## Root cause

Look-alike domain (`micros0ft-support.example`) passed basic filtering; one user didn't recognize the
fake login page.

## What worked

- MFA stopped the attacker even with the correct password.
- A user reported quickly; message trace + purge removed the email from everyone else.

## Actions

| # | Action | Owner | Due |
|---|---|---|---|
| 1 | Enable number matching on MFA push | IT | 2026-03-11 |
| 2 | Add look-alike domain protection to the mail filter | IT | 2026-03-18 |
| 3 | Short phishing refresher for Finance (most targeted team) | IT + HR | 2026-03-31 |
| 4 | Thank User B publicly for reporting (reinforce the behavior) | IT Manager | 2026-03-05 |
