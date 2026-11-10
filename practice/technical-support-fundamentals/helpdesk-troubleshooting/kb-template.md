# KB-0001: Outlook can't send after mail migration (error 0x800CCC0E)

> Copy this file for each new knowledge-base article. Keep it short - someone will read it
> while on the phone with an upset user.

| Field | Value |
|---|---|
| Applies to | Outlook desktop (Windows), users migrated to the new mail server |
| Audience | Help desk (tier 1) |
| Last reviewed | 2026-03-04 |
| Related tickets | #1 |

## Symptoms

- Outlook **receives** mail but **sending** fails with `0x800CCC0E` / "Cannot connect to server".
- Webmail works for the same user.

## Cause

The user's Outlook profile still points to the old SMTP server, which was shut down after the
migration.

## Resolution

1. Close Outlook.
2. Control Panel → **Mail (Microsoft Outlook)** → **Show Profiles** → **Add...**
3. Name it `Outlook-New`, sign in with the user's email; autodiscover sets the new server.
4. Select **Always use this profile** → `Outlook-New` → OK.
5. Open Outlook, wait for sync, send a test email.

## If that doesn't work

- Confirm webmail sending works (if not → account issue, not Outlook).
- Escalate to **Messaging team** with: username, error code, screenshot, steps already tried.

## Prevention

Migration checklist updated to include a profile reset for all migrated users.
