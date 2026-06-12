#!/usr/bin/env bash
set -euo pipefail

USER_NAME="${SUDO_USER:-${USER}}"
FOUND=0

read_uevent_chain() {
  local node="$1"
  local real
  real="$(readlink -f "$node/device" 2>/dev/null || true)"
  [[ -n "$real" ]] || return 0

  local cur="$real"
  local depth=0
  while [[ -n "$cur" && "$cur" != "/" && "$depth" -lt 8 ]]; do
    [[ -f "$cur/uevent" ]] && cat "$cur/uevent"
    [[ -f "$cur/name" ]] && printf 'NAME=%s\n' "$(cat "$cur/name" 2>/dev/null || true)"
    cur="$(dirname "$cur")"
    depth=$((depth + 1))
  done
  printf 'SYSFS_PATH=%s\n' "$real"
}

is_magic_mouse_hidraw() {
  local node="$1"
  local text
  text="$(read_uevent_chain "$node" | tr '[:lower:]' '[:upper:]')"

  # Pop!_OS Bluetooth sample: HID_ID=0005:000005AC:0000030D, HID_NAME=MaGiK MoUsE
  echo "$text" | grep -Eq 'HID_ID=.*000005AC:00000(30D|269|323)' && return 0
  echo "$text" | grep -Eq '05AC:0*(030D|0269|0323)' && return 0
  echo "$text" | grep -Eq 'HID_NAME=.*MAGI[CK].*MOUS?E|NAME=.*MAGI[CK].*MOUS?E' && return 0
  return 1
}

for node in /sys/class/hidraw/hidraw*; do
  [[ -e "$node" ]] || continue
  if is_magic_mouse_hidraw "$node"; then
    dev="/dev/$(basename "$node")"
    FOUND=1
    echo "Granting temporary ACL for $USER_NAME on $dev"
    if command -v setfacl >/dev/null 2>&1; then
      sudo setfacl -m "u:${USER_NAME}:rw" "$dev"
    else
      echo "setfacl not found; installing acl is recommended: sudo apt install acl" >&2
      sudo chmod a+rw "$dev"
    fi
    getfacl -p "$dev" 2>/dev/null || ls -l "$dev"
  fi
done

if [[ "$FOUND" -eq 0 ]]; then
  echo "No Apple/Magic Mouse hidraw node found. Run scripts/list-hidraw.sh for diagnostics." >&2
  exit 1
fi

echo "Temporary permission applied. It lasts until reconnect/reboot. For permanent access, run ./install.sh --udev and reconnect the mouse."
