#!/usr/bin/env bash
set -euo pipefail

for node in /sys/class/hidraw/hidraw*; do
  [[ -e "$node" ]] || { echo "No hidraw nodes found."; exit 0; }
  name="$(basename "$node")"
  dev="/dev/$name"
  real="$(readlink -f "$node/device" || true)"
  echo "== $dev =="
  ls -l "$dev" || true
  if command -v getfacl >/dev/null 2>&1; then
    getfacl -p "$dev" 2>/dev/null | sed 's/^/  /' || true
  fi
  echo "  sysfs: $real"
  for f in "$real/uevent" "$(dirname "$real")/uevent" "$(dirname "$(dirname "$real")")/uevent"; do
    [[ -f "$f" ]] || continue
    grep -E '^(HID_ID|HID_NAME|PRODUCT|NAME|DRIVER|MODALIAS)=' "$f" 2>/dev/null | sed 's/^/  /' || true
  done
  if command -v udevadm >/dev/null 2>&1; then
    udevadm info -q property -n "$dev" 2>/dev/null | grep -E '^(ID_VENDOR_ID|ID_MODEL_ID|ID_VENDOR|ID_MODEL|TAGS|DEVNAME)=' | sed 's/^/  /' || true
  fi
  echo
done
