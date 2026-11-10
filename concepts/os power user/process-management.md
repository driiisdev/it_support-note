# Process Management

A **program** is a file on disk. A **process** is a running instance of a program - with its own
memory, a process ID (PID), an owner, and a share of the CPU. Process management is how you see
what's running, why the machine is slow, and how to stop something that's misbehaving.

## Programs, processes, and threads

- One program can have **many processes** (each Chrome tab is often a separate process).
- Each process has one or more **threads** (units of work the CPU schedules).
- Every process has:
  - **PID** - unique number while it runs.
  - **Parent (PPID)** - the process that started it.
  - **Owner** - the user it runs as (determines what it can access).
  - **State** - running, sleeping/waiting, stopped, zombie.

The CPU switches between processes very quickly (**time slicing**) so they appear to run at once.

## How processes are created

### Windows

- The kernel starts **`smss.exe`** (Session Manager), which starts `csrss.exe` and `wininit.exe`
  / `winlogon.exe`; services are run by **`services.exe`**.
- New processes are created with the `CreateProcess` API; the child is independent - it keeps
  running even if its parent exits.

### Linux

- At boot the kernel starts **PID 1** - **`systemd`** on most modern distros (older: `init`).
  Every other process descends from it.
- New processes are made with **`fork()`** (copy the current process) + **`exec()`** (replace the
  copy with a new program). That's how your shell runs `ls`.
- If a parent dies, its children are re-parented to PID 1.
- **Zombie** - a finished process whose parent hasn't collected its exit status yet. Harmless in
  small numbers; lots of them = a buggy parent program.

```bash
pstree -p          # process tree with PIDs
```

> 🖼️ **Image idea: process tree** - systemd → sshd → bash → ls on the Linux side; wininit →
> services.exe → svchost.exe and explorer.exe → chrome.exe on the Windows side.
> Suggested file: `assets/img/process-tree.png`
<!-- ![process tree](<../../assets/img/process-tree.png>) -->

## Viewing processes

### Windows

- **Task Manager** (`Ctrl+Shift+Esc`) - Processes, Performance, Startup apps, Users, Details
  (shows PIDs), Services tabs.
- **Resource Monitor** (`resmon`) - per-process CPU, memory, disk, network detail.
- **Process Explorer** (Sysinternals) - Task Manager on steroids: process tree, which process
  has a file locked, DLLs loaded, VirusTotal check.

```powershell
Get-Process
Get-Process chrome | Measure-Object WorkingSet64 -Sum     # total RAM of all chrome processes
Get-Process | Sort-Object CPU -Descending | Select-Object -First 10 Name, Id, CPU, WorkingSet64
tasklist /v
Get-CimInstance Win32_Process -Filter "Name='notepad.exe'" | Select-Object ProcessId, ParentProcessId, CommandLine
```

### Linux

```bash
ps aux                     # all processes: USER PID %CPU %MEM ... COMMAND
ps -ef --forest            # with parent PIDs, as a tree
pgrep -a nginx             # find PIDs by name
top                        # live view; press M to sort by memory, P by CPU, q to quit
htop                       # friendlier top (may need installing)
uptime                     # how long it's been up + load average (1, 5, 15 min)
free -h                    # memory and swap usage
lsof -p 1234               # files opened by PID 1234
lsof -i :443               # which process is using port 443
```

**Load average** (Linux) - average number of processes waiting for CPU. Compare to the number of
cores (`nproc`): load 4.0 on a 4-core machine = fully busy; 12.0 = overloaded.

## Stopping processes: signals

On Linux (and macOS), you control processes by sending **signals**:

| Signal | Number | Shortcut | Effect |
|---|---|---|---|
| **SIGINT** | 2 | `Ctrl+C` | interrupt - "please stop" (program can catch it and clean up) |
| **SIGTERM** | 15 | `kill PID` (default) | terminate - polite request to exit |
| **SIGKILL** | 9 | `kill -9 PID` | kill immediately - can't be caught or ignored; no cleanup |
| **SIGTSTP** | 20 | `Ctrl+Z` | suspend (pause) |
| **SIGCONT** | 18 | `fg` / `bg` | resume a stopped process |
| **SIGHUP** | 1 | - | "hang up" - many daemons reload their config on it |

**Always try SIGTERM before SIGKILL** - `kill -9` can leave half-written files or locks behind.

```bash
kill 1234            # SIGTERM
kill -9 1234         # SIGKILL - last resort
pkill firefox        # by name
killall -HUP nginx   # reload nginx config
```

### Windows

```powershell
Stop-Process -Name notepad
Stop-Process -Id 1234 -Force
taskkill /IM notepad.exe            # polite
taskkill /PID 1234 /F               # force
taskkill /IM chrome.exe /T /F       # /T = also kill child processes
```

## Background and foreground jobs (Linux shell)

```bash
long_task &           # start in the background
jobs                  # list jobs in this shell
Ctrl+Z                # suspend the foreground job
bg %1                 # continue job 1 in the background
fg %1                 # bring it back to the foreground
nohup long_task &     # keep running after you log out
```

## Resource monitoring: what's "slow"?

| Resource | Bottleneck sign | Typical cause |
|---|---|---|
| CPU | constantly near 100% | runaway process, malware, antivirus scan, too-weak CPU |
| Memory | near 100%, heavy pagefile/swap use | too many apps/tabs, memory leak |
| Disk | 100% active time, high queue | HDD instead of SSD, updates, indexing, failing disk |
| Network | link saturated | big downloads/sync, backup jobs |

```powershell
Get-Counter '\Processor(_Total)\% Processor Time','\Memory\Available MBytes' -SampleInterval 2 -MaxSamples 5
```

## Services / daemons

Long-running background processes without a user interface:

```powershell
Get-Service | Where-Object Status -eq Running
Restart-Service Spooler          # the classic "fix the print queue"
Set-Service -Name Spooler -StartupType Automatic
```

```bash
systemctl status ssh
sudo systemctl restart ssh
sudo systemctl enable --now nginx       # start now + at every boot
journalctl -u ssh --since "1 hour ago"  # that service's logs
```

## How it's used in real IT support

- "My computer is frozen" → Task Manager → which process is pegging CPU/RAM/disk → end task.
- "I can't delete this file, it's in use" → find the process holding it (Process Explorer
  `Find Handle`, or `lsof`), close it.
- "Printing stuck" → restart the Print Spooler service.
- "Slow since login" → Task Manager → Startup apps → disable unnecessary ones.

## Practice project

[`practice/os-power-user/process-and-log-monitor`](<../../practice/os-power-user/process-and-log-monitor>) -
`process_watch.py` shows top processes by memory/CPU and alerts when a process crosses a threshold;
`signals_demo.py` lets you watch a process handle SIGINT/SIGTERM cleanly (and see why SIGKILL
can't be handled).

## Related

- [Navigating the system](<navigating-the-system.md>) - pipes and filters used above.
- [Operating systems in practice](<operating-systems-in-practice.md>) - logs to explain *why* a process failed.
- [Operating system](<../technical support fundamentals/operating-system.md>) - the kernel's role in scheduling.
