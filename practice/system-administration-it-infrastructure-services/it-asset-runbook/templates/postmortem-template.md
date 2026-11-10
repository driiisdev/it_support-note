# Post-mortem: Floor 2 network outage (2026-03-05)

> **Blameless**: we describe what happened and why the *system* allowed it, not who to blame.
> People who make mistakes are the best source of information about how to prevent them.

| Field | Value |
|---|---|
| Severity | P1 - ~25 users without network |
| Duration | 08:20 - 09:02 (42 minutes) |
| Detected by | Users calling the help desk (no monitoring alert) |
| Author | Help desk team |
| Status | Action items in progress |

## Summary

All PCs on floor 2 lost network access. The switch uplink cable had been pulled loose during a
desk move the previous evening. PCs showed `169.254.x.x` addresses (no DHCP).

## Timeline (all times local)

| Time | Event |
|---|---|
| 17:40 (day before) | Facilities moves desks on floor 2 |
| 08:20 | First user call: "no internet" |
| 08:31 | Ticket #2 opened as P1 after 5 more calls |
| 08:35 | Help desk notices 169.254 addresses → DHCP unreachable; floor 1 fine → floor-2 switch suspected |
| 08:50 | Uplink port LED off; cable reseated; link up |
| 09:02 | Clients renewed DHCP; service restored |

## Root cause

The floor-2 switch has a single uplink, unlabeled, running behind a desk where it can be knocked out.

## What went well

- Help desk used the 169.254 clue and "floor 1 works" to isolate to the floor-2 switch in 15 minutes.

## What went poorly

- No monitoring - users detected the outage, not IT.
- Facilities didn't know there was network gear behind the desks.

## Action items

| # | Action | Owner | Due |
|---|---|---|---|
| 1 | Add the floor-2 switch uplink to monitoring (ping + alert) | IT Ops | 2026-03-12 |
| 2 | Route the uplink through cable management; label both ends | IT Ops | 2026-03-09 |
| 3 | Add "notify IT before desk moves" to facilities' checklist | Facilities | 2026-03-15 |
| 4 | Evaluate a second uplink (redundancy) | Network | 2026-04-01 |
