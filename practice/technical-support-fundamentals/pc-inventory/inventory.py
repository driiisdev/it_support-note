"""
inventory.py - collect a hardware/OS inventory of THIS machine and save it as JSON.

Cross-platform (Windows / Linux / macOS), standard library only.

Usage:
    python inventory.py                    # print summary + write reports/<hostname>.json
    python inventory.py --out somewhere/   # choose the output folder
"""

import argparse
import ctypes
import datetime as dt
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import uuid
from pathlib import Path


def ram_total_bytes() -> int | None:
    """Total physical RAM. Every OS exposes this differently - a good example of why
    cross-platform tools need per-OS branches."""
    system = platform.system()
    try:
        if system == "Windows":
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            return stat.ullTotalPhys
        if system == "Linux":
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        return int(line.split()[1]) * 1024  # value is in KiB
        if system == "Darwin":
            return int(subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True))
    except Exception:
        pass
    return None


def uptime_seconds() -> float | None:
    system = platform.system()
    try:
        if system == "Windows":
            return ctypes.windll.kernel32.GetTickCount64() / 1000
        if system == "Linux":
            with open("/proc/uptime") as f:
                return float(f.read().split()[0])
        if system == "Darwin":
            out = subprocess.check_output(["sysctl", "-n", "kern.boottime"], text=True)
            boot = int(out.split("sec =")[1].split(",")[0])
            return dt.datetime.now().timestamp() - boot
    except Exception:
        pass
    return None


def cpu_name() -> str:
    """platform.processor() is often vague (e.g. 'Intel64 Family 6 ...'), so ask the OS."""
    system = platform.system()
    try:
        if system == "Windows":
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                 r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
            return winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
        if system == "Linux":
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if line.startswith("model name"):
                        return line.split(":", 1)[1].strip()
        if system == "Darwin":
            return subprocess.check_output(
                ["sysctl", "-n", "machdep.cpu.brand_string"], text=True).strip()
    except Exception:
        pass
    return platform.processor() or "unknown"


def disks() -> list[dict]:
    """Free/used space per drive (Windows) or per common mount point (Linux/macOS)."""
    if platform.system() == "Windows":
        candidates = [f"{letter}:\\" for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ"
                      if os.path.exists(f"{letter}:\\")]
    else:
        candidates = [p for p in ("/", "/home", "/boot", "/var") if os.path.ismount(p)]

    result = []
    for path in candidates:
        try:
            usage = shutil.disk_usage(path)
        except OSError:  # e.g. empty card reader
            continue
        result.append({
            "mount": path,
            "total_gb": round(usage.total / 1024 ** 3, 1),
            "free_gb": round(usage.free / 1024 ** 3, 1),
            "used_pct": round(usage.used / usage.total * 100, 1),
        })
    return result


def primary_ip() -> str:
    """The IP the OS would use to reach the internet. Connecting a UDP socket sends no packets;
    it just makes the OS pick a route + source address."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return "offline"


def mac_address() -> str:
    node = uuid.getnode()
    return ":".join(f"{(node >> shift) & 0xFF:02X}" for shift in range(40, -1, -8))


def collect() -> dict:
    uptime = uptime_seconds()
    ram = ram_total_bytes()
    return {
        "collected_at": dt.datetime.now().isoformat(timespec="seconds"),
        "hostname": socket.gethostname(),
        "user": os.environ.get("USERNAME") or os.environ.get("USER") or "unknown",
        "os": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "architecture": platform.machine(),
        },
        "cpu": {
            "model": cpu_name(),
            "logical_cores": os.cpu_count(),
        },
        "ram_gb": round(ram / 1024 ** 3, 1) if ram else None,
        "disks": disks(),
        "network": {"primary_ip": primary_ip(), "mac": mac_address()},
        "uptime_hours": round(uptime / 3600, 1) if uptime else None,
        "python": sys.version.split()[0],
    }


def warnings_for(inv: dict) -> list[str]:
    """Simple rules a help desk would flag during a device health check."""
    warn = []
    if inv["ram_gb"] and inv["ram_gb"] < 8:
        warn.append(f"Only {inv['ram_gb']} GB RAM - expect slowness with modern browsers/Office.")
    for d in inv["disks"]:
        if d["used_pct"] >= 90:
            warn.append(f"Disk {d['mount']} is {d['used_pct']}% full ({d['free_gb']} GB free).")
    if inv["uptime_hours"] and inv["uptime_hours"] > 24 * 14:
        warn.append(f"Up for {inv['uptime_hours'] / 24:.0f} days - pending updates need a reboot.")
    return warn


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", default=str(Path(__file__).parent / "reports"))
    args = p.parse_args()

    inv = collect()
    inv["warnings"] = warnings_for(inv)

    print(f"Host       : {inv['hostname']}  (user: {inv['user']})")
    print(f"OS         : {inv['os']['system']} {inv['os']['release']} ({inv['os']['architecture']})")
    print(f"CPU        : {inv['cpu']['model']} - {inv['cpu']['logical_cores']} logical cores")
    print(f"RAM        : {inv['ram_gb']} GB")
    for d in inv["disks"]:
        print(f"Disk {d['mount']:<6}: {d['free_gb']} GB free of {d['total_gb']} GB ({d['used_pct']}% used)")
    print(f"Network    : {inv['network']['primary_ip']}  MAC {inv['network']['mac']}")
    print(f"Uptime     : {inv['uptime_hours']} h")
    for w in inv["warnings"]:
        print(f"  WARNING: {w}")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{inv['hostname']}.json"
    out_file.write_text(json.dumps(inv, indent=2), encoding="utf-8")
    print(f"\nSaved -> {out_file}")


if __name__ == "__main__":
    main()
