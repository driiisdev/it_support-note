# Practice: Process & Log Monitor (Process Management, Operating Systems in Practice)

Concept notes:
[`process-management.md`](<../../../concepts/os power user/process-management.md>) ·
[`operating-systems-in-practice.md`](<../../../concepts/os power user/operating-systems-in-practice.md>)

## What this demonstrates

- **`process_watch.py`** - Task Manager / `top` in a script: top processes by CPU % or memory,
  measured properly (CPU-seconds used between two samples ÷ elapsed time ÷ cores), with alerts
  and "total for all `chrome` processes."
- **`signals_demo.py`** - why you stop a process **gracefully first**: a worker holding a lock file
  cleans up after a graceful signal, but a forced kill leaves a stale lock and loses its progress.
  Also shows the real Windows vs Linux difference (Windows has no deliverable SIGTERM).
- **`log_analyzer.py`** - reading logs like an investigator: a Linux `auth.log` brute-force attack
  followed by a suspicious successful login and a `sudo cat /etc/shadow`; and a Windows System log
  where a crashing service, disk warnings, and an unexpected reboot tell a story - with the
  **first error** highlighted.

## Scenario

Two tickets: *"the server was slow overnight and rebooted itself"* and *"security asked if anyone
got into web01."* You check what's running, then go to the logs to find out what happened and in
what order.

## Folder structure

```
process-and-log-monitor/
  process_watch.py          <- top N by CPU/mem, --watch, --name aggregation, alerts
  signals_demo.py           <- graceful vs forced stop experiment (spawns its own child process)
  log_analyzer.py           <- `auth` (Linux auth.log) and `events` (Windows Event Log CSV / --live)
  sample-logs/
    auth.log                <- fictional sshd/sudo log: brute force + compromise pattern
    system-events.csv       <- fictional Windows System log export: spooler crashes, disk errors, reboot
```

All IPs in the samples are from documentation ranges (`192.0.2.0/24`, `198.51.100.0/24`,
`203.0.113.0/24`).

## Code walkthrough

**CPU % needs two samples** - a single snapshot only gives total CPU time since the process started:

```python
used = after["cpu_seconds"] - before["cpu_seconds"]
cpu_pct = used / elapsed / CORES * 100      # % of the whole machine, like Task Manager
```

**Graceful vs forced**: the worker registers handlers so it can save state and remove its lock:

```python
signal.signal(signal.SIGTERM, graceful)      # Linux: `kill PID`
signal.signal(signal.SIGBREAK, graceful)     # Windows: CTRL_BREAK_EVENT
p.kill()                                     # SIGKILL / TerminateProcess: no handler ever runs
```

**Log parsing = regex + correlation.** Counting failures per IP finds brute force; correlating
*successes* with recent failures from the same IP finds the more dangerous case - a guessed password:

```python
prior = [t for t in failed_by_ip[ip] if t <= ts and (ts - t).total_seconds() < 3600]
if len(prior) >= 3: "SUSPICIOUS: success after N failures"
```

**Windows events**: grouped by **source + Event ID** (the pair you search online), well-known IDs
annotated (41 unexpected reboot, 7031 service crash, 7 / 153 disk trouble), and a timeline built
around boots. `--live` pulls your own last 24 h of System events via `Get-WinEvent` (read-only).

## Run it

```bash
python process_watch.py
python process_watch.py --sort mem --top 15 --mem-alert 1000
python process_watch.py --name chrome
python process_watch.py --watch 5 --cpu-alert 30      # Ctrl+C to stop

python signals_demo.py

python log_analyzer.py auth sample-logs/auth.log
python log_analyzer.py events sample-logs/system-events.csv
python log_analyzer.py events --live                  # Windows: your real System log
```

Expected (excerpts):

```
  198.51.100.7          48  02:14:06-02:16:03     24.6/min  admin, root, ubuntu, guest  <-- BRUTE FORCE
  Mar 04 03:05:22  tunde    from 203.0.113.50     via password  <-- SUSPICIOUS: success after 7 failures ...
  Mar 04 03:07:22  tunde    /usr/bin/cat /etc/shadow  <-- reading password hashes!

FIRST error in the window (later errors are often consequences of this one):
  2026-03-04 09:12:03  Service Control Manager 7031: The Print Spooler service terminated unexpectedly...

Experiment 2: forced kill
    lock file left behind? YES - stale lock, next run may refuse to start
```

## Try this yourself

- Open a CPU-heavy page or run `python -c "while True: pass"` and watch `process_watch.py --watch 2`
  flag it. Kill it gracefully first.
- Read the story in `system-events.csv`: what would you check first? (Hint: the disk errors after
  the reboot matter more than the spooler crashes - back up and check SMART.)
- Run `log_analyzer.py events --live` and look up your top source/ID pair. Most "errors" on a
  healthy PC are noise - learning to tell noise from signal is the skill.
- On a Linux VM: `sudo python3 log_analyzer.py auth /var/log/auth.log` after a few wrong SSH
  passwords from another machine.
- Add a `--since "Mar 04 03:00"` filter, and a CSV export of the brute-force IPs (to feed a firewall
  block list - see [firewall-rule-auditor](../../it-security/firewall-rule-auditor)).

## Real-world equivalent

- Task Manager, Resource Monitor, Process Explorer, `top`/`htop`; RMM agents alerting on high CPU.
- `fail2ban` does the brute-force detection automatically and blocks IPs.
- SIEMs (Splunk, Sentinel, Wazuh) run correlation rules exactly like "success after N failures"
  across every server's logs at once.
