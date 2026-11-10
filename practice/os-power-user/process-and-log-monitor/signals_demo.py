"""
signals_demo.py - why you try a graceful stop (SIGTERM / Ctrl+C) before a forced kill (SIGKILL / End task).

Runs two experiments on a child "worker" process that holds a lock file while it works:
  1. graceful stop -> the worker catches the signal, saves state, removes its lock file, exits cleanly
  2. forced kill   -> the worker gets no chance to react; the stale lock file is left behind

Usage:
    python signals_demo.py            # run both experiments
    python signals_demo.py worker     # (internal) the child process

Platform note:
    Linux/macOS: graceful = SIGTERM, forced = SIGKILL (kill -9).
    Windows has no SIGTERM delivery between processes: os.kill(pid, SIGTERM) is TerminateProcess,
    i.e. a forced kill. The closest graceful signal is CTRL_BREAK_EVENT (like Ctrl+Break in a console),
    which Python sees as SIGBREAK. That's also why `taskkill /F` vs plain `taskkill` behave differently.
"""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
LOCK = HERE / "worker.lock"
STATE = HERE / "worker.state"
IS_WINDOWS = sys.platform == "win32"


def worker() -> None:
    LOCK.write_text(str(os.getpid()))
    processed = 0

    def graceful(signum, frame):
        name = signal.Signals(signum).name
        print(f"    [worker] caught {name} -> saving progress ({processed} items) and removing lock", flush=True)
        STATE.write_text(f"processed={processed}\n")
        LOCK.unlink(missing_ok=True)
        sys.exit(0)

    signal.signal(signal.SIGINT, graceful)
    signal.signal(signal.SIGTERM, graceful)
    if IS_WINDOWS:
        signal.signal(signal.SIGBREAK, graceful)

    print(f"    [worker] PID {os.getpid()} started, holding {LOCK.name}", flush=True)
    while True:
        processed += 1
        time.sleep(0.1)


def start_worker() -> subprocess.Popen:
    kwargs = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if IS_WINDOWS else {}
    p = subprocess.Popen([sys.executable, "-u", __file__, "worker"], **kwargs)
    time.sleep(1.5)
    return p


def status() -> None:
    print(f"    lock file left behind? {'YES - stale lock, next run may refuse to start' if LOCK.exists() else 'no'}")
    print(f"    state saved?           {STATE.read_text().strip() if STATE.exists() else 'NO - progress lost'}")


def cleanup() -> None:
    LOCK.unlink(missing_ok=True)
    STATE.unlink(missing_ok=True)


def main() -> None:
    sys.stdout.reconfigure(line_buffering=True)  # keep our lines in order with the child's output
    cleanup()
    print("Experiment 1: graceful stop")
    p = start_worker()
    graceful_sig = signal.CTRL_BREAK_EVENT if IS_WINDOWS else signal.SIGTERM
    print(f"  sending {'CTRL_BREAK_EVENT' if IS_WINDOWS else 'SIGTERM (kill PID)'} to {p.pid}")
    p.send_signal(graceful_sig)
    p.wait(timeout=10)
    print(f"  exit code {p.returncode}")
    status()
    cleanup()

    print("\nExperiment 2: forced kill")
    p = start_worker()
    print(f"  sending {'TerminateProcess (taskkill /F)' if IS_WINDOWS else 'SIGKILL (kill -9 PID)'} to {p.pid}")
    p.kill()
    p.wait(timeout=10)
    print(f"  exit code {p.returncode}")
    status()
    cleanup()

    print("\nLesson: graceful first (SIGTERM / taskkill without /F / closing the app), force only if it's hung.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "worker":
        worker()
    else:
        main()
