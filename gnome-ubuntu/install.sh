#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UUID="magic-mouse-workspaces@horseman.local"
EXT_DIR="$HOME/.local/share/gnome-shell/extensions/$UUID"
BIN_DIR="$HOME/.local/bin"
CFG_DIR="$HOME/.config/magic-mouse"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
APP_DIR="$HOME/.local/share/applications"
INSTALL_DEPS=0
INSTALL_UDEV=0
NO_SERVICE=0
COSMIC_COMPAT=0

for arg in "$@"; do
  case "$arg" in
    --install-deps) INSTALL_DEPS=1 ;;
    --install-udev) INSTALL_UDEV=1 ;;
    --no-service) NO_SERVICE=1 ;;
    --cosmic-compat) COSMIC_COMPAT=1 ;;
    -h|--help)
      cat <<HELP
Usage: ./install.sh [--install-deps] [--install-udev] [--no-service] [--cosmic-compat]

--install-deps   Install Ubuntu/Pop apt dependencies with sudo apt.
--install-udev   Install udev rule with sudo for input permissions.
--no-service     Do not enable/start the user gesture daemon.
--cosmic-compat  Create ~/.local/bin/cosmic-ws compatibility wrapper.
HELP
      exit 0
      ;;
    *) echo "Unknown option: $arg" >&2; exit 2 ;;
  esac
done

has() { command -v "$1" >/dev/null 2>&1; }

if [[ "$INSTALL_DEPS" == 1 ]]; then
  sudo apt update
  sudo apt install -y gnome-shell gnome-shell-extension-prefs libglib2.0-bin python3 python3-evdev python3-tk bluez unzip systemd xdotool
fi

mkdir -p "$BIN_DIR" "$CFG_DIR" "$SYSTEMD_USER_DIR" "$APP_DIR" "$EXT_DIR"
install -m 0755 "$ROOT/bin/magic-mouse-ws" "$BIN_DIR/magic-mouse-ws"
install -m 0755 "$ROOT/bin/magic-mouse-gesture-daemon" "$BIN_DIR/magic-mouse-gesture-daemon"
install -m 0755 "$ROOT/bin/magic-mouse-control-panel" "$BIN_DIR/magic-mouse-control-panel"
install -m 0755 "$ROOT/bin/magic-mouse-gnome-probe" "$BIN_DIR/magic-mouse-gnome-probe"
install -m 0755 "$ROOT/bin/magic-mouse-diagnose" "$BIN_DIR/magic-mouse-diagnose"
install -m 0755 "$ROOT/bin/magic-mouse-service" "$BIN_DIR/magic-mouse-service"
install -m 0755 "$ROOT/bin/magic-mouse-gnome-integrate" "$BIN_DIR/magic-mouse-gnome-integrate"

if [[ ! -f "$CFG_DIR/config.json" ]]; then
  install -m 0644 "$ROOT/config/default.json" "$CFG_DIR/config.json"
fi
install -m 0644 "$ROOT/systemd/user/magic-mouse-gestures.service" "$SYSTEMD_USER_DIR/magic-mouse-gestures.service"
install -m 0644 "$ROOT/desktop/magic-mouse-control-panel.desktop" "$APP_DIR/magic-mouse-control-panel.desktop"

SHELL_VERSION=""
SHELL_MAJOR=""
if has gnome-shell; then
  SHELL_VERSION="$(gnome-shell --version 2>/dev/null | awk '{print $NF}' || true)"
  if [[ "$SHELL_VERSION" =~ ^3\. ]]; then
    SHELL_MAJOR="$(echo "$SHELL_VERSION" | awk -F. '{print $1"."$2}')"
  else
    SHELL_MAJOR="$(echo "$SHELL_VERSION" | awk -F. '{print $1}')"
  fi
fi

rm -rf "$EXT_DIR"
mkdir -p "$EXT_DIR"
if [[ -n "$SHELL_MAJOR" && ( "$SHELL_MAJOR" == "3.36" || "$SHELL_MAJOR" == "3.38" || "$SHELL_MAJOR" == "40" || "$SHELL_MAJOR" == "41" || "$SHELL_MAJOR" == "42" || "$SHELL_MAJOR" == "43" || "$SHELL_MAJOR" == "44" ) ]]; then
  SRC="$ROOT/extension-src/gnome-42-44/$UUID"
  EXT_KIND="legacy"
else
  SRC="$ROOT/extension-src/gnome-45-plus/$UUID"
  EXT_KIND="modern"
fi
cp -a "$SRC/"* "$EXT_DIR/"

if [[ -n "$SHELL_MAJOR" ]]; then
  python3 - "$EXT_DIR/metadata.json" "$SHELL_MAJOR" <<'PY' || true
import json, sys
path, ver = sys.argv[1], sys.argv[2]
data = json.load(open(path, encoding='utf-8'))
versions = list(data.get('shell-version', []))
if ver and ver not in versions:
    versions.append(ver)
    data['shell-version'] = versions
    open(path, 'w', encoding='utf-8').write(json.dumps(data, indent=2) + '\n')
PY
fi

if [[ "$INSTALL_UDEV" == 1 ]]; then
  sudo install -m 0644 "$ROOT/udev/99-magic-mouse-gestures.rules" /etc/udev/rules.d/99-magic-mouse-gestures.rules
  sudo udevadm control --reload-rules
  sudo udevadm trigger
else
  install -m 0644 "$ROOT/udev/99-magic-mouse-gestures.rules" "$CFG_DIR/99-magic-mouse-gestures.rules"
fi

systemctl --user daemon-reload >/dev/null 2>&1 || true
if [[ "$NO_SERVICE" == 0 ]]; then
  systemctl --user enable magic-mouse-gestures.service >/dev/null 2>&1 || true
  systemctl --user restart magic-mouse-gestures.service >/dev/null 2>&1 || true
fi

if has gnome-extensions; then
  gnome-extensions enable "$UUID" 2>/dev/null || true
fi

if [[ "$COSMIC_COMPAT" == 1 ]]; then
  "$BIN_DIR/magic-mouse-gnome-integrate" install-cosmic-ws-shim
fi

cat <<MSG
Installed Magic Mouse GNOME package 0.2.0.

Installed pieces:
  - Workspace backend: $BIN_DIR/magic-mouse-ws
  - Gesture daemon:    $BIN_DIR/magic-mouse-gesture-daemon
  - Control panel:     $BIN_DIR/magic-mouse-control-panel
  - GNOME extension:   $EXT_DIR ($EXT_KIND, shell=$SHELL_MAJOR)
  - Config:            $CFG_DIR/config.json
  - User service:      $SYSTEMD_USER_DIR/magic-mouse-gestures.service

Next steps:
  1) Log out/in once, especially on GNOME Wayland or after installing udev rules.
  2) Run: magic-mouse-gnome-probe
  3) Test: magic-mouse-ws status && magic-mouse-ws down && sleep 0.5 && magic-mouse-ws up
  4) Open panel: magic-mouse-control-panel

Fresh Ubuntu/Pop install:
  ./install.sh --install-deps --install-udev
MSG
