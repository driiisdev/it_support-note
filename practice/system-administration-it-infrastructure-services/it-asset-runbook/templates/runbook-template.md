# Runbook: Monthly Windows Patching (example - copy for each recurring task)

| Field | Value |
|---|---|
| Owner | IT Operations |
| Frequency | Monthly, the weekend after Patch Tuesday |
| Maintenance window | Saturday 22:00 - Sunday 02:00 |
| Systems | All Windows servers (see asset list, type = server) |
| Last tested | 2026-03-14 |

## Purpose

Apply Microsoft security updates to servers in a controlled order with a tested rollback.

## Prerequisites

- [ ] Change request approved (link: CHG-____)
- [ ] Last night's backups succeeded for every server in scope
- [ ] Users notified 3 working days before (template: "Planned maintenance")
- [ ] Monitoring muted for the window (or the on-call person warned)

## Steps

1. **Test ring first** - patch `TEST-APP01`, reboot, confirm the app works (log in, open a record).
2. **Snapshot** each VM before patching (Hyper-V/VMware) - keep until Monday.
3. Patch **secondary** servers first (e.g. `DC02`), reboot, verify, *then* primary (`DC01`).
   - Never reboot both domain controllers at the same time.
4. For each server:
   ```powershell
   Get-WindowsUpdate -Install -AcceptAll -AutoReboot     # PSWindowsUpdate module
   # after reboot:
   Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 5
   Get-Service | Where-Object { $_.StartType -eq 'Automatic' -and $_.Status -ne 'Running' }
   ```
5. Run the health checks: `python service-health-monitor/health_check.py`

## Verification

- [ ] All servers report the new build / KB number
- [ ] No automatic services stopped
- [ ] Health check is all green
- [ ] Spot-check: users can log in, file shares open, email flows

## Rollback

- Uninstall the KB: `wusa /uninstall /kb:5031234 /quiet /norestart`, or
- Revert to the pre-patch VM snapshot (last resort - loses changes since the snapshot).

## Escalation

| Problem | Contact |
|---|---|
| Server won't boot after patch | On-call sysadmin: +44 ... |
| Business app broken | App owner: finance-apps@example.com |
| Vendor issue | Microsoft support contract #: ________ |
