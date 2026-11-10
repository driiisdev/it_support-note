#!/usr/bin/env bash
# audit_host.sh - READ-ONLY Linux hardening audit (Debian/Ubuntu-oriented). Writes results/<host>.json.
#   bash audit_host.sh          # some checks are more complete with sudo
#   python3 report.py results/<host>.json
set -uo pipefail
cd "$(dirname "$0")"
mkdir -p results
HOST=$(hostname)
OUT="results/$HOST.json"
ROWS=()

add() {  # layer check status detail fix
  printf "[%-7s] %-12s %-34s %s\n" "$3" "$1" "$2" "$4"
  ROWS+=("$(python3 -c 'import json,sys; print(json.dumps(dict(zip(["layer","check","status","detail","fix"], sys.argv[1:]))))' "$@")")
}

# --- firewall
if command -v ufw >/dev/null; then
  s=$(sudo -n ufw status 2>/dev/null | head -1)
  case "$s" in
    *active*) add firewall "ufw" PASS "$s" "" ;;
    "") add firewall "ufw" UNKNOWN "needs sudo" "" ;;
    *) add firewall "ufw" FAIL "$s" "sudo ufw default deny incoming && sudo ufw enable" ;;
  esac
elif command -v firewall-cmd >/dev/null; then
  s=$(firewall-cmd --state 2>&1); [[ "$s" == running ]] && add firewall firewalld PASS running "" || add firewall firewalld FAIL "$s" "systemctl enable --now firewalld"
else
  add firewall "host firewall" FAIL "no ufw/firewalld found" "install and enable ufw"
fi

# --- patching
if command -v apt >/dev/null; then
  n=$(apt list --upgradable 2>/dev/null | grep -c upgradable || true)
  sec=$(apt list --upgradable 2>/dev/null | grep -ci security || true)
  st=PASS; ((n > 0)) && st=WARN; ((sec > 0)) && st=FAIL
  add patching "Pending updates" $st "$n pending ($sec security)" "sudo apt update && sudo apt upgrade"
  if dpkg -s unattended-upgrades >/dev/null 2>&1; then add patching "Automatic security updates" PASS "unattended-upgrades installed" ""
  else add patching "Automatic security updates" WARN "not installed" "sudo apt install unattended-upgrades"; fi
fi
[[ -f /var/run/reboot-required ]] && add patching "Reboot required" WARN "yes (kernel/libs updated)" "schedule a reboot" \
                                  || add patching "Reboot required" PASS "no" ""

# --- encryption
if lsblk -o TYPE 2>/dev/null | grep -q crypt; then add encryption "Disk encryption (LUKS)" PASS "encrypted volume present" ""
else add encryption "Disk encryption (LUKS)" WARN "no dm-crypt volume found" "use LUKS full-disk encryption on laptops"; fi

# --- accounts
uid0=$(awk -F: '$3==0{print $1}' /etc/passwd | tr '\n' ' ')
[[ "$uid0" == "root " ]] && add accounts "UID 0 accounts" PASS "$uid0" "" || add accounts "UID 0 accounts" FAIL "$uid0" "only root should have UID 0"
sudoers=$(getent group sudo wheel 2>/dev/null | cut -d: -f4 | tr '\n' ',' | sed 's/,$//')
add accounts "sudo/wheel members" WARN "${sudoers:-none}" "review: does each person need admin?"
empty=$(sudo -n awk -F: '$2==""{print $1}' /etc/shadow 2>/dev/null | tr '\n' ' ')
if sudo -n true 2>/dev/null; then
  [[ -z "$empty" ]] && add accounts "Empty passwords" PASS "none" "" || add accounts "Empty passwords" FAIL "$empty" "passwd -l <user>"
else add accounts "Empty passwords" UNKNOWN "needs sudo" ""; fi

# --- SSH / attack surface
if [[ -f /etc/ssh/sshd_config ]]; then
  cfg=$(sudo -n sshd -T 2>/dev/null || cat /etc/ssh/sshd_config)
  root=$(grep -i '^permitrootlogin' <<< "$cfg" | awk '{print $2}' | head -1)
  pass=$(grep -i '^passwordauthentication' <<< "$cfg" | awk '{print $2}' | head -1)
  [[ "${root,,}" == "no" || "${root,,}" == "prohibit-password" ]] && add surface "SSH PermitRootLogin" PASS "$root" "" \
    || add surface "SSH PermitRootLogin" FAIL "${root:-default}" "PermitRootLogin no"
  [[ "${pass,,}" == "no" ]] && add surface "SSH PasswordAuthentication" PASS "no (keys only)" "" \
    || add surface "SSH PasswordAuthentication" WARN "${pass:-yes (default)}" "use keys, then PasswordAuthentication no"
else
  add surface "SSH server" PASS "not installed" ""
fi
ports=$(ss -tlnH 2>/dev/null | awk '{print $4}' | grep -E '^(0\.0\.0\.0|\*|\[::\]):' | sed 's/.*://' | sort -un | tr '\n' ' ')
add surface "Ports listening on all interfaces" WARN "${ports:-none}" "is each one needed? firewall it if not"
ww=$(find /etc -xdev -type f -perm -0002 2>/dev/null | head -5 | tr '\n' ' ')
[[ -z "$ww" ]] && add surface "World-writable files in /etc" PASS "none" "" || add surface "World-writable files in /etc" FAIL "$ww" "chmod o-w"

# --- output
{
  printf '{"host": "%s", "os": "%s", "elevated": %s, "collected": "%s", "results": [' \
    "$HOST" "$(. /etc/os-release 2>/dev/null; echo "${PRETTY_NAME:-Linux}")" \
    "$( [[ $EUID -eq 0 ]] && echo true || echo false )" "$(date +%FT%T)"
  (IFS=,; printf '%s' "${ROWS[*]}")
  printf ']}\n'
} > "$OUT"
echo; echo "Saved -> $OUT   (python3 report.py $OUT)"
