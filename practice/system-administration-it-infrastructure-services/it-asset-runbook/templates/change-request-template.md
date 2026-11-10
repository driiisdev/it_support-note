# Change Request CHG-0042: Replace floor-2 access switch

| Field | Value |
|---|---|
| Requested by | Tunde Okafor (IT) |
| Date requested | 2026-03-02 |
| Type | Normal (needs approval) - *Standard* = pre-approved routine, *Emergency* = fix now, document after |
| Risk | Medium |
| Impact | ~25 users on floor 2 lose network for ~20 minutes |
| Scheduled | Saturday 2026-03-07, 08:00 - 09:00 |
| Approver | IT Manager |

## What and why

The floor-2 switch (asset IT-0012) is out of warranty and logged 14 port errors last month.
Replace it with the spare Catalyst 9200 (IT-0009-spare), pre-configured with the same VLANs.

## Implementation plan

1. Back up the running config of the old switch (`show running-config` → save to the config repo).
2. Label every cable with its port number.
3. Power down the old switch, swap hardware, move cables port-for-port.
4. Power up, verify uplink and VLANs (`show interfaces status`, `show vlan brief`).

## Test plan

- Link lights on all previously used ports
- Test PC on floor 2 gets a DHCP address in the right VLAN and reaches the internet
- Printer IT-0007 reachable at its reserved IP

## Backout plan

Re-install the old switch with its saved config (kept on the shelf until Monday). Time to back out: 15 minutes.

## Communication

- [ ] Floor-2 users emailed Wednesday and Friday
- [ ] Reception aware

## Post-implementation

| Field | Value |
|---|---|
| Result | Success / Partial / Rolled back |
| Notes | |
| Asset inventory updated | `python assets.py retire IT-0012 "replaced by CHG-0042"` |
