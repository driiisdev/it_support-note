#!/usr/bin/env bash
# install_workstation.sh - same build as Install-Workstation.ps1, for Debian/Ubuntu (apt).
#
#   ./install_workstation.sh                  # dry run: what's missing?
#   ./install_workstation.sh --required-only
#   sudo ./install_workstation.sh --apply     # install missing packages
#
# Idempotent: packages already installed (dpkg says "install ok installed") are skipped.

set -uo pipefail
cd "$(dirname "$0")"

APPLY=false; REQUIRED_ONLY=false
for a in "$@"; do
  case "$a" in
    --apply) APPLY=true ;;
    --required-only) REQUIRED_ONLY=true ;;
    *) echo "unknown option $a"; exit 1 ;;
  esac
done
$APPLY && [[ $EUID -ne 0 ]] && { echo "--apply needs sudo"; exit 1; }

mkdir -p logs
LOG="logs/install-$(hostname)-$(date +%Y%m%d-%H%M%S).log"
exec > >(tee -a "$LOG") 2>&1          # everything below goes to screen AND log file

# Parse apps.json with Python (always present on Ubuntu) instead of requiring jq
mapfile -t APPS < <(python3 - "$REQUIRED_ONLY" <<'PY'
import json, sys
required_only = sys.argv[1] == "true"
for app in json.load(open("apps.json"))["apps"]:
    if app["apt"] and (app["required"] or not required_only):
        print(f'{app["name"]}|{app["apt"]}|{app["required"]}')
PY
)

echo "Build on $(hostname) [$($APPLY && echo APPLY || echo DRY-RUN)]"
$APPLY && apt-get update -qq

missing_required=()
for entry in "${APPS[@]}"; do
  IFS='|' read -r name pkg required <<< "$entry"
  if dpkg-query -W -f='${Status}' "$pkg" 2>/dev/null | grep -q "install ok installed"; then
    status="already installed"
  elif ! $APPLY; then
    status="WOULD INSTALL"
    [[ "$required" == "True" ]] && missing_required+=("$name")
  else
    if DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "$pkg" >/dev/null; then
      status="installed"
    else
      status="FAILED"
      [[ "$required" == "True" ]] && missing_required+=("$name")
    fi
  fi
  printf "  %-16s %-14s %s\n" "$name" "$pkg" "$status"
done

echo
if ((${#missing_required[@]})); then
  echo "NOT COMPLIANT - required: ${missing_required[*]}"
else
  echo "COMPLIANT - all required packages present."
fi
echo "Log -> $LOG"
