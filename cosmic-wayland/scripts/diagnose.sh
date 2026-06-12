#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROFILE="${1:-profiles/cosmic.env}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "== Service =="
systemctl --user status magic-mouse-gestures.service --no-pager || true

echo
echo "== Bluetooth connected devices =="
if command -v bluetoothctl >/dev/null 2>&1; then
  bluetoothctl devices Connected || true
else
  echo "bluetoothctl: missing"
fi

echo
echo "== Kernel module =="
lsmod | grep '^hid_magicmouse' || echo "hid_magicmouse: not loaded"
modinfo hid_magicmouse >/dev/null 2>&1 && echo "hid_magicmouse: available" || echo "hid_magicmouse: not available via modinfo"

echo
echo "== hidraw nodes =="
ls -l /dev/hidraw* 2>/dev/null || echo "No /dev/hidraw* nodes"

echo
echo "== HID devices visible to hidapi =="
"$PYTHON_BIN" "$ROOT_DIR/src/magic_mouse_daemon.py" --profile "$ROOT_DIR/$PROFILE" --list-all-hid || true

echo
echo "== Kernel messages, Apple/HID/Bluetooth recent =="
journalctl -k -n 200 --no-pager | grep -Ei 'magic|apple|hid|bluetooth|05ac|0323|0269|030d' || true
