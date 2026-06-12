#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROFILE="${1:-profiles/cosmic.env}"

echo "== Session =="
echo "XDG_SESSION_TYPE=${XDG_SESSION_TYPE:-unknown}"
echo "XDG_CURRENT_DESKTOP=${XDG_CURRENT_DESKTOP:-unknown}"
echo "XDG_SESSION_DESKTOP=${XDG_SESSION_DESKTOP:-unknown}"

echo
echo "== Commands =="
for cmd in python3 wtype systemctl; do
  if command -v "$cmd" >/dev/null 2>&1; then
    echo "$cmd: $(command -v "$cmd")"
  else
    echo "$cmd: missing"
  fi
done

echo
echo "== Kernel =="
if lsmod | grep -q '^hid_magicmouse'; then
  echo "hid_magicmouse: loaded"
else
  echo "hid_magicmouse: not loaded"
fi
if command -v modinfo >/dev/null 2>&1; then
  modinfo hid_magicmouse >/dev/null 2>&1 && echo "hid_magicmouse: available" || echo "hid_magicmouse: modinfo unavailable"
fi

echo
echo "== Python syntax =="
python3 -m py_compile "$ROOT_DIR/src/"*.py

echo
echo "== Profile simulation =="
python3 "$ROOT_DIR/src/magic_mouse_daemon.py" --profile "$ROOT_DIR/$PROFILE" --simulate left --dry-run
python3 "$ROOT_DIR/src/magic_mouse_daemon.py" --profile "$ROOT_DIR/$PROFILE" --simulate up --dry-run

echo
echo "== HID devices =="
python3 "$ROOT_DIR/src/magic_mouse_daemon.py" --profile "$ROOT_DIR/$PROFILE" --list-devices || true
echo
echo "== All HID devices =="
python3 "$ROOT_DIR/src/magic_mouse_daemon.py" --profile "$ROOT_DIR/$PROFILE" --list-all-hid || true
