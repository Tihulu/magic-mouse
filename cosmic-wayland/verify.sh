#!/usr/bin/env bash
set -euo pipefail

VERSION="1.4.3"
echo "== magic-mouse-cosmic-workspaces v$VERSION =="
echo

echo "== Session =="
echo "XDG_SESSION_TYPE=${XDG_SESSION_TYPE:-}"
echo "XDG_CURRENT_DESKTOP=${XDG_CURRENT_DESKTOP:-}"
echo

echo "== Binaries =="
command -v wtype || true
command -v jq || true
command -v cargo || true
command -v cos-cli || true
ls -l "$HOME/.cargo/bin/cos-cli" 2>/dev/null || true
ls -l "$HOME/.local/bin/cosmic-ws" 2>/dev/null || true
command -v magic-mouse-control-panel || true
ls -l "$HOME/.local/bin/magic-mouse-control-panel" 2>/dev/null || true
command -v magic-mouse-control-panel-cli || true
ls -l "$HOME/.local/bin/magic-mouse-control-panel-cli" 2>/dev/null || true

echo
echo "== Application icons =="
for size in 16 24 32 48 64 128 256 512 1024; do
  icon="$HOME/.local/share/icons/hicolor/${size}x${size}/apps/magic-mouse-control-panel.png"
  if [[ -f "$icon" ]]; then
    ls -l "$icon"
  else
    echo "missing: $icon"
  fi
done

echo
echo "== Magic Mouse service =="
systemctl --user status magic-mouse-gestures -l --no-pager || true

echo
echo "== Profile =="
sed -n '1,260p' "$HOME/.config/magic-mouse-gestures/profile.env" 2>/dev/null || true

echo
echo "== Udev local rule =="
sed -n '1,120p' /etc/udev/rules.d/99-magic-mouse-gestures-local.rules 2>/dev/null || echo "local udev rule not found"

echo
echo "== hidraw candidates =="
for dev in /dev/hidraw*; do
  [[ -e "$dev" ]] || continue
  echo "-- $dev"
  ls -l "$dev" || true
  getfacl -p "$dev" 2>/dev/null | sed -n '1,20p' || true
  udevadm info -q property -n "$dev" 2>/dev/null | grep -Ei 'ID_VENDOR_ID|ID_MODEL_ID|HID_ID|HID_NAME|DEVNAME' || true
done

echo
echo "== Recent service log =="
journalctl --user -u magic-mouse-gestures -n 40 -l --no-pager || true

echo
echo "== cos-cli info =="
if [[ -x "$HOME/.cargo/bin/cos-cli" ]]; then
  "$HOME/.cargo/bin/cos-cli" info --json | jq . || true
elif command -v cos-cli >/dev/null 2>&1; then
  cos-cli info --json | jq . || true
else
  echo "cos-cli not found"
fi

echo
echo "== cosmic-ws runtime state =="
STATE_FILE="${XDG_RUNTIME_DIR:-/tmp}/magic-mouse-cosmic-ws.state"
if [[ -f "$STATE_FILE" ]]; then
  echo "$STATE_FILE"
  cat "$STATE_FILE"
else
  echo "No runtime state file yet: $STATE_FILE"
fi

echo
echo "== Magic Mouse scroll direction =="
if [[ -x "$HOME/.local/bin/magic-mouse-scroll-direction" ]]; then
  "$HOME/.local/bin/magic-mouse-scroll-direction" status || true
else
  echo "magic-mouse-scroll-direction not found"
fi

echo
echo "== COSMIC input config files =="
for cfg in input_default input_mouse input_touchpad; do
  path="$HOME/.config/cosmic/com.system76.CosmicComp/v1/$cfg"
  echo "-- $path"
  sed -n '1,160p' "$path" 2>/dev/null || echo "missing"
done
