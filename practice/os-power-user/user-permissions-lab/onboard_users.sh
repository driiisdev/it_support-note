#!/usr/bin/env bash
# onboard_users.sh - onboard/offboard Linux users from a CSV: groups, home dirs, shared folders, perms.
#
# DRY RUN by default - prints every command. With --apply (as root, in a VM!) it runs them.
#   ./onboard_users.sh                 # dry run
#   sudo ./onboard_users.sh --apply    # do it
#   sudo ./onboard_users.sh --cleanup --apply
#
# Shared folders get setgid (2770): new files inherit the department group, others get nothing.

set -euo pipefail

CSV="$(dirname "$0")/new-hires.csv"
SHARE_ROOT="/srv/labshares"
APPLY=false
CLEANUP=false
for arg in "$@"; do
  case "$arg" in
    --apply) APPLY=true ;;
    --cleanup) CLEANUP=true ;;
    *) echo "unknown option $arg"; exit 1 ;;
  esac
done

if $APPLY && [[ $EUID -ne 0 ]]; then
  echo "--apply must run as root (sudo)"; exit 1
fi

run() {
  # print the command; only execute it when --apply was given
  # %q re-quotes each argument, so the printed line is exactly what would run
  echo "[$($APPLY && echo APPLY || echo DRY-RUN)] $(printf '%q ' "$@")"
  if $APPLY; then "$@"; fi
}

username() { echo "${1:0:1}$2" | tr '[:upper:]' '[:lower:]'; }   # Amina Bello -> abello

mapfile -t ROWS < <(tail -n +2 "$CSV" | tr -d '\r')
mapfile -t DEPTS < <(printf '%s\n' "${ROWS[@]}" | cut -d, -f3 | sort -u)

if $CLEANUP; then
  for row in "${ROWS[@]}"; do
    IFS=, read -r first last dept action <<< "$row"
    u=$(username "$first" "$last")
    if id "$u" &>/dev/null || ! $APPLY; then run userdel -r "$u"; fi
  done
  for d in "${DEPTS[@]}"; do run groupdel "lab-${d,,}"; done
  run rm -rf "$SHARE_ROOT"
  exit 0
fi

for d in "${DEPTS[@]}"; do
  g="lab-${d,,}"   # ${d,,} = lowercase
  if ! getent group "$g" &>/dev/null; then run groupadd "$g"; fi
  run mkdir -p "$SHARE_ROOT/$d"
  run chown root:"$g" "$SHARE_ROOT/$d"
  run chmod 2770 "$SHARE_ROOT/$d"     # 2 = setgid, 7 owner rwx, 7 group rwx, 0 others nothing
done

for row in "${ROWS[@]}"; do
  IFS=, read -r first last dept action <<< "$row"
  u=$(username "$first" "$last")
  g="lab-${dept,,}"
  if [[ "$action" == "onboard" ]]; then
    if ! id "$u" &>/dev/null; then
      run useradd -m -s /bin/bash -c "$first $last" -G "$g" "$u"
      pw=$(tr -dc 'A-HJ-NP-Za-km-z2-9' </dev/urandom | head -c 16 || true)
      if $APPLY; then echo "$u:$pw" | chpasswd; else echo "[DRY-RUN] echo '$u:<random>' | chpasswd"; fi
      run passwd -e "$u"              # expire now -> must change at first login
      $APPLY && echo "    temp password for $u: $pw  (deliver securely)"
    else
      run usermod -aG "$g" "$u"       # -a = APPEND; without it the user loses every other group!
    fi
  elif [[ "$action" == "offboard" ]]; then
    run usermod -L "$u"               # lock password
    run usermod -s /usr/sbin/nologin "$u"
    run gpasswd -d "$u" "$g"
  fi
done

echo
$APPLY && echo "Verify: id abello ; ls -ld $SHARE_ROOT/* ; getent group lab-finance" \
       || echo "Dry run complete - nothing changed."
