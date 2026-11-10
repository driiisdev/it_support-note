# Practice: Firewall Rule Auditor (Securing Your Networks)

Concept note:
[`securing-your-networks.md`](<../../../concepts/it security/securing-your-networks.md>)

## What this demonstrates

Firewalls are only as good as their rule base, and rule bases rot: "temporary" rules that never
leave, rules nobody owns, a broad rule that silently hides a specific one. This tool:

- **Simulates** a firewall: rules evaluated **top to bottom, first match wins**, then the implicit deny.
- **Audits** the rule base for the classic problems: **shadowed** and **redundant** rules, **any-any**
  allows, risky services (**RDP, SMB, Telnet, databases**) **exposed to the internet**, overly broad
  rules, missing owner/comment, "temporary" rules, and a missing explicit **cleanup (deny-all)** rule.
- **Tests** the rule base against expected outcomes - firewall changes with test cases, like code.

## Scenario

You inherit a firewall with 11 rules and no documentation. The security team says RDP is open to the
internet; the guest network team says the captive portal "randomly" doesn't work. Find out why, fix
the rule base, and prove it with tests.

## Folder structure

```
firewall-rule-auditor/
  auditor.py               <- audit | test | check <proto> <src> <dst> <port>
  rules.csv                <- the messy inherited rule base (every problem type is in here)
  test-packets.csv         <- traffic that should / shouldn't pass
  solution/rules-fixed.csv <- one possible fix: 0 findings, 7/7 tests pass (try it yourself first!)
```

Rule format: `id,action,proto,src,dst,port,owner,comment`, where addresses are CIDR or `any`,
and ports are `443`, `1000-2000`, `80;443`, or `any`.

## Code walkthrough

**First match wins** - the whole firewall is this loop:

```python
for r in rules:
    if matches(r, proto, src, dst, port):
        return r["action"], r
return "deny", None     # implicit deny
```

**Shadowing** = an earlier rule *covers* a later one (protocol, source, destination, and ports are all
supersets) with the **opposite** action. Python's `ipaddress` makes the network part one call:

```python
b["_src"].subnet_of(a["_src"]) and b["_dst"].subnet_of(a["_dst"])
```

In `rules.csv`, rule 7 (*deny guests → 10.20.0.0/16*) sits above rule 8 (*allow guests → captive
portal 10.20.0.25*), so the portal rule can **never** match. That's the "randomly doesn't work" ticket.

**Exposure** = an `allow` from `any` that includes a port in the risky list (3389 RDP, 445 SMB,
3306 MySQL...).

## Run it

```bash
python auditor.py audit
python auditor.py test
python auditor.py check tcp 198.51.100.7 10.20.0.15 3389      # which rule decides this?
python auditor.py audit --rules solution/rules-fixed.csv
python auditor.py test  --rules solution/rules-fixed.csv
```

Expected:

```
  [CRIT] rule 9   ANY-ANY allow - this rule disables the firewall
  [HIGH] rule 5   EXPOSED to the internet: 3389/RDP - put behind VPN / restrict source IPs
  [HIGH] rule 8   SHADOWED by rule 7 (deny) - rule 8 (allow) can never match. ...
  [LOW ] rule 4   REDUNDANT - already covered by rule 3 (allow)
  [LOW ] rule 12  NO CLEANUP RULE - add an explicit final 'deny any any any' ...

FAIL   allow    deny   7     guest -> captive portal
3/7 tests pass - fix the rule base and re-run
```

## Try this yourself

- **Fix `rules.csv` yourself** (copy it first) until `audit` is clean and `test` passes 7/7, then compare
  with `solution/rules-fixed.csv`. There's more than one right answer.
- Add test packets for things that must keep working (staff DNS, staff → file server) **before** you
  change rules, so you notice if a fix breaks them.
- Export your real Windows Firewall inbound rules and read them (read-only):
  ```powershell
  Get-NetFirewallRule -Direction Inbound -Enabled True -Action Allow |
    Select-Object DisplayName, Profile, @{n='Port';e={($_ | Get-NetFirewallPortFilter).LocalPort}} |
    Sort-Object DisplayName | Format-Table -AutoSize
  ```
  Which ones apply to the **Public** profile? Why might that matter on café Wi-Fi?
- Add rule **hit counters**: replay a list of logged connections and report rules that never matched
  (candidates for removal).
- Add support for **expiry dates** (`expires` column) and flag expired rules.

## Real-world equivalent

- Firewall policy analyzers: AlgoSec, Tufin, FireMon; built-in "shadowed rule" warnings in Palo Alto,
  FortiGate, and pfSense.
- Cloud security groups (AWS/Azure NSGs) have the same problems - `0.0.0.0/0` on port 3389 or 22 is one
  of the most common cloud findings in security audits.
