# Troubleshooting Scenarios (practice drills)

Work through each one **before** reading the hints. For each, write down:
the questions you'd ask → how you'd isolate → most likely cause → fix → what you'd put in the
ticket. Then log it with `python ticket.py new`.

---

## 1. "The internet is down"

A user calls: *"Nothing works, the internet is down."* Their colleague next to them is working
fine.

<details><summary>Hints</summary>

- Colleague is fine → not a building-wide outage; it's this PC/user.
- Run `connectivity_check.py` (or `ipconfig /all`). `169.254.x.x` → DHCP; check cable / Wi-Fi.
- If IP is fine but names don't resolve → DNS (check the DNS server in `ipconfig /all`).
- If everything passes but one website fails → the problem is the site, a proxy, or the browser.

</details>

## 2. "My computer is slow"

Started this week. Every application is slow, not just one.

<details><summary>Hints</summary>

- "Every app" → OS/hardware layer, not one app.
- Task Manager → which resource is at 100%? CPU / memory / disk.
- Disk 100% + HDD → failing or slow disk; disk 100% + an AV process → scanning exclusions.
- Memory 100% → too many apps/tabs, or a leaking process.
- "This week" → what changed? Updates? New software?

</details>

## 3. "I can't print"

One user can't print to the 2nd-floor printer. Others can.

<details><summary>Hints</summary>

- Others can → printer is fine; it's this PC/user.
- Is the right printer selected? Any stuck job in the queue?
- Restart the Print Spooler service; clear the queue.
- Driver - remove and re-add the printer.

</details>

## 4. "I can't open the shared Finance folder"

New hire, first day. "Access denied."

<details><summary>Hints</summary>

- New user → are they in the right **group**? (Permissions should be on groups.)
- If you just added them: they must **log off and on** (group membership is in the logon token).
- Share permissions vs NTFS permissions - the most restrictive wins.

</details>

## 5. "My account keeps locking"

Unlocked 5 minutes ago, locked again.

<details><summary>Hints</summary>

- Something keeps trying an **old password**: phone email app, mapped drive with saved
  credentials, a scheduled task, Wi-Fi profile.
- AD: Security event **4740** on the PDC emulator shows the source computer of the lockout.
- If the source is unknown/external → could be an attack; escalate to security.

</details>

## 6. "Laptop won't turn on"

No lights, no fan, nothing.

<details><summary>Hints</summary>

- Charger LED on? Try a different known-good charger and outlet.
- Battery fully drained → leave charging 30 minutes.
- Hard reset: unplug, hold power 30 seconds, plug in, try again.
- Still dead → hardware (motherboard/power circuit) → warranty claim with the serial number.

</details>
