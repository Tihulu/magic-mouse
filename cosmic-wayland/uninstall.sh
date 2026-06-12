#!/usr/bin/env bash
set -euo pipefail

PROJECT_NAME="magic-mouse-linux-gestures"
INSTALL_DIR="$HOME/.local/share/$PROJECT_NAME"
CONFIG_DIR="$HOME/.config/magic-mouse-gestures"
SERVICE_FILE="$HOME/.config/systemd/user/magic-mouse-gestures.service"
BIN_FILE="$HOME/.local/bin/magic-mouse-control-panel"
DESKTOP_FILE="$HOME/.local/share/applications/magic-mouse-control-panel.desktop"
REMOVE_CONFIG=0

usage() {
  cat <<USAGE
Usage: ./uninstall.sh [--remove-config]

Options:
  --remove-config  Also remove ~/.config/magic-mouse-gestures
  -h, --help       Show this help.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --remove-config)
      REMOVE_CONFIG=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

systemctl --user disable --now magic-mouse-gestures.service 2>/dev/null || true
rm -f "$SERVICE_FILE" "$BIN_FILE" "$DESKTOP_FILE"
rm -rf "$INSTALL_DIR"

if [[ "$REMOVE_CONFIG" -eq 1 ]]; then
  rm -rf "$CONFIG_DIR"
fi

systemctl --user daemon-reload

echo "Uninstalled Magic Mouse Linux Gestures."
