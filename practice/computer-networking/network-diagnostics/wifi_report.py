"""
wifi_report.py - read the current Wi-Fi connection and flag common problems.

Windows: parses `netsh wlan show interfaces`. Linux: parses `nmcli`. Read-only.

Usage:
    python wifi_report.py
    python wifi_report.py --sample      # use a saved example output (no Wi-Fi needed)
"""

import argparse
import platform
import re
import subprocess

SAMPLE = """
    Name                   : Wi-Fi
    Description            : Intel(R) Wi-Fi 6 AX201 160MHz
    State                  : connected
    SSID                   : CorpNet
    BSSID                  : 70:3a:0e:12:34:56
    Network type           : Infrastructure
    Radio type             : 802.11n
    Authentication         : WPA2-Personal
    Cipher                 : CCMP
    Band                   : 2.4 GHz
    Channel                : 3
    Receive rate (Mbps)    : 72.2
    Transmit rate (Mbps)   : 72.2
    Signal                 : 38%
    Rssi                   : -79
"""


def read_windows(text: str) -> dict:
    def field(name: str) -> str | None:
        m = re.search(rf"^\s*{name}\s*:\s*(.+)$", text, re.M)
        return m.group(1).strip() if m else None
    return {
        "state": field("State"), "ssid": field("SSID"), "bssid": field("BSSID"),
        "radio": field("Radio type"), "auth": field("Authentication"), "cipher": field("Cipher"),
        "band": field("Band"), "channel": field("Channel"),
        "rx_mbps": field(r"Receive rate \(Mbps\)"), "signal_pct": (field("Signal") or "").rstrip("%"),
        "rssi": field("Rssi"),
    }


def read_linux() -> dict:
    text = subprocess.run(["nmcli", "-t", "-f", "ACTIVE,SSID,BSSID,CHAN,FREQ,RATE,SIGNAL,SECURITY",
                           "dev", "wifi"], capture_output=True, text=True).stdout
    for line in text.splitlines():
        parts = re.split(r"(?<!\\):", line)
        if parts and parts[0] == "yes":
            _, ssid, bssid, chan, freq, rate, signal, sec = parts[:8]
            return {"state": "connected", "ssid": ssid, "bssid": bssid.replace("\\", ""), "channel": chan,
                    "band": "2.4 GHz" if freq.startswith("24") else "5/6 GHz", "rx_mbps": rate.split()[0],
                    "signal_pct": signal, "auth": sec, "radio": None, "cipher": None, "rssi": None}
    return {"state": "disconnected"}


def assess(w: dict) -> list[str]:
    tips = []
    sig = int(w["signal_pct"]) if w.get("signal_pct", "").isdigit() else None
    if sig is not None:
        if sig < 40:
            tips.append(f"Weak signal ({sig}%). Move closer to the AP, remove obstacles, or add an access point.")
        elif sig < 60:
            tips.append(f"Fair signal ({sig}%). Video calls may stutter.")
    if w.get("band", "").startswith("2.4"):
        tips.append("On 2.4 GHz: more range but slower and crowded. Prefer 5/6 GHz if the device supports it.")
        ch = w.get("channel")
        if ch and ch.isdigit() and int(ch) not in (1, 6, 11):
            tips.append(f"Channel {ch} overlaps neighbors - 2.4 GHz APs should use 1, 6 or 11.")
    auth = (w.get("auth") or "").upper()
    if "WEP" in auth or auth in ("OPEN", "") and w.get("state") == "connected":
        tips.append(f"Security '{w.get('auth')}' is weak/none - use WPA2-AES or WPA3.")
    if "TKIP" in (w.get("cipher") or "").upper():
        tips.append("TKIP cipher is deprecated - switch the AP to AES/CCMP.")
    if w.get("radio") in ("802.11b", "802.11g"):
        tips.append(f"Old radio standard {w['radio']} - very slow; check the adapter driver or hardware.")
    return tips


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--sample", action="store_true")
    args = p.parse_args()

    if args.sample:
        w = read_windows(SAMPLE)
        print("(using built-in sample output)\n")
    elif platform.system() == "Windows":
        w = read_windows(subprocess.run(["netsh", "wlan", "show", "interfaces"],
                                        capture_output=True, text=True, errors="replace").stdout)
    else:
        w = read_linux()

    if w.get("state") != "connected" or not w.get("ssid"):
        print("Not connected to Wi-Fi (wired, or Wi-Fi off). Try --sample to see a report.")
        return
    for k in ("ssid", "bssid", "radio", "band", "channel", "auth", "cipher", "rx_mbps", "signal_pct", "rssi"):
        if w.get(k):
            print(f"  {k:<11}: {w[k]}{' %' if k == 'signal_pct' else ''}{' dBm' if k == 'rssi' else ''}")
    tips = assess(w)
    print("\nAssessment:")
    for t in tips or ["Looks healthy."]:
        print(f"  - {t}")


if __name__ == "__main__":
    main()
