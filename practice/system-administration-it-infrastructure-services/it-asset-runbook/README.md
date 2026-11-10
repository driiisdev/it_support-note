# Practice: IT Asset Inventory & Runbooks (What Is System Administration)

Concept note:
[`what-is-system-administration.md`](<../../../concepts/system administration it infrastructure services/what-is-system-administration.md>)

## What this demonstrates

The non-glamorous half of sysadmin work that keeps everything else possible:

- **Hardware lifecycle** as a state machine: `in-stock → deployed → in-repair → retired`, with
  rules (you can't assign a laptop that's already deployed) and a dated note for every change.
- **Warranty tracking** - what to claim under warranty, what to plan to replace.
- **Documentation templates** for the three documents every IT team needs: a **runbook**, a
  **change request** (with backout plan), and a **blameless post-mortem**.

## Scenario

You've joined a small company where "the inventory" is someone's memory. Your manager wants to know:
how many spare laptops do we have, whose warranty is expiring, and can we stop changing network
gear without telling anyone?

## Folder structure

```
it-asset-runbook/
  assets.py                <- list / show / add / assign / return / repair / retire / warranty / report
  assets.csv               <- 10 sample assets (laptops, desktop, server, printer, switch)
  templates/
    runbook-template.md          <- monthly patching runbook (prereqs, steps, verification, rollback)
    change-request-template.md   <- switch replacement CR (risk, impact, test plan, backout)
    postmortem-template.md       <- blameless post-mortem of a floor outage (timeline, root cause, actions)
```

## Code walkthrough

**Lifecycle transitions are validated**, so the data can't drift into nonsense:

```python
def cmd_assign(a):
    transition(a.tag, allowed_from=["in-stock"], new_status="deployed", ...)
# -> "IT-0005 is 'deployed' - can't go to 'deployed' from there"
```

**Every change leaves an audit trail** in the notes column (`2026-03-04: assigned to new.hire`) -
accounting, applied to hardware.

**Safe writes**: the CSV is written to a temp file and then renamed over the original, so a crash
halfway through can't leave a corrupt inventory:

```python
tmp.replace(DB)
```

**`repair` checks the warranty first** and tells you whether to open a vendor claim (with the
serial number the vendor will ask for) or plan a paid repair.

## Run it

```bash
python assets.py list
python assets.py list --status deployed --type laptop
python assets.py warranty --days 120
python assets.py report
python assets.py add laptop "Dell Latitude 5450" ABC1234
python assets.py assign IT-0005 new.hire --location HQ-3F
python assets.py repair IT-0001 "battery swelling"
python assets.py retire IT-0004 "wiped, cert #D-4480"
python assets.py show IT-0004
```

> These commands **modify `assets.csv`**. Copy it first if you want to keep the sample data
> pristine (`cp assets.csv assets.backup.csv`).

Expected:

```
Warranty expiring within 90 days:
  IT-0010  Lenovo ThinkPad T14      sara.nguyen     in 21 days (2026-11-30)
Warranty already expired (still in use):
  IT-0007  HP LaserJet M507         deployed   1100 days ago - plan replacement
...
Spare laptops in stock: 1  <-- order more before the next hire wave
```

(Day counts depend on today's date.)

## Try this yourself

- Merge in the output of [pc-inventory](../../technical-support-fundamentals/pc-inventory): match on
  serial number (`Get-Inventory.ps1` collects it) and flag machines on the network that aren't in
  the asset list, or assets that haven't reported in 30 days.
- Add a `--csv` export of the warranty report for the budget meeting.
- Write a runbook for something you actually do (e.g. "set up a new starter's laptop") using
  `runbook-template.md`. Have someone else follow it and note where they got stuck.
- Write a post-mortem for a real (small) failure you've had - lost files, a broken update - using the
  template. Be blameless toward yourself.
- Add a `checkout` command for loaner laptops with a due date and an `overdue` report.

## Real-world equivalent

- **Snipe-IT** (open source), **Lansweeper**, ServiceNow/Jira **CMDB**, Intune device inventory.
- Change management in ITIL / ServiceNow "Change" records; post-mortems as practiced by SRE teams.
