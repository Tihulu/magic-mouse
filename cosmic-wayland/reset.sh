#!/usr/bin/env bash
set -euo pipefail

VERSION="1.4.3"
TS="$(date +%Y%m%d-%H%M%S)"
BACKUP_ROOT="$HOME/Documents/magicmouse-backups"
BACKUP="$BACKUP_ROOT/magicmouse-backup-$TS"

say() { printf '\033[1;34m[reset v%s]\033[0m %s\n' "$VERSION" "$*"; }
warn() { printf '\033[1;33m[warn]\033[0m %s\n' "$*"; }

DISPLAY_BACKUP_ROOT="~/Documents/magicmouse-backups"
DISPLAY_BACKUP="$DISPLAY_BACKUP_ROOT/magicmouse-backup-$TS"
say "Backup root: $DISPLAY_BACKUP_ROOT"
say "Backup directory: $DISPLAY_BACKUP"
mkdir -p "$BACKUP"

say "Stopping the magic-mouse-gestures user service..."
systemctl --user stop magic-mouse-gestures 2>/dev/null || true
systemctl --user disable magic-mouse-gestures 2>/dev/null || true

say "Backing up existing files..."
cp -a "$HOME/.config/magic-mouse-gestures" "$BACKUP/" 2>/dev/null || true
cp -a "$HOME/.config/systemd/user/magic-mouse-gestures.service" "$BACKUP/" 2>/dev/null || true
cp -a "$HOME/.local/share/magic-mouse-linux-gestures" "$BACKUP/" 2>/dev/null || true
cp -a "$HOME/.local/bin/cosmic-ws" "$BACKUP/" 2>/dev/null || true
cp -a /etc/udev/rules.d/99-magic-mouse-gestures-local.rules "$BACKUP/" 2>/dev/null || true
cp -a "$HOME/.cargo/bin/cos-cli" "$BACKUP/" 2>/dev/null || true

say "Cleaning old Magic Mouse user installations..."
rm -rf "$HOME/.config/magic-mouse-gestures"
rm -rf "$HOME/.local/share/magic-mouse-linux-gestures"
rm -f "$HOME/.config/systemd/user/magic-mouse-gestures.service"
rm -f "$HOME/.local/bin/cosmic-ws"
rm -f "$HOME/.local/bin/magic-mouse-control-panel"
rm -f "$HOME/.local/bin/magic-mouse-control-panel-cli"
rm -f "$HOME/.local/bin/magic-mouse-scroll-direction"
rm -f "$HOME/.local/share/applications/magic-mouse-control-panel.desktop"
rm -f "$HOME/.local/share/applications/magic-mouse-control-panel-cli.desktop"
rm -f "$HOME/.local/share/icons/hicolor/16x16/apps/magic-mouse-control-panel.png"
rm -f "$HOME/.local/share/icons/hicolor/24x24/apps/magic-mouse-control-panel.png"
rm -f "$HOME/.local/share/icons/hicolor/32x32/apps/magic-mouse-control-panel.png"
rm -f "$HOME/.local/share/icons/hicolor/48x48/apps/magic-mouse-control-panel.png"
rm -f "$HOME/.local/share/icons/hicolor/64x64/apps/magic-mouse-control-panel.png"
rm -f "$HOME/.local/share/icons/hicolor/128x128/apps/magic-mouse-control-panel.png"
rm -f "$HOME/.local/share/icons/hicolor/256x256/apps/magic-mouse-control-panel.png"
rm -f "$HOME/.local/share/icons/hicolor/512x512/apps/magic-mouse-control-panel.png"
rm -f "$HOME/.local/share/icons/hicolor/1024x1024/apps/magic-mouse-control-panel.png"
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -q "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
fi
rm -rf "$HOME/.local/share/magic-mouse-cosmic-workspaces"
rm -f "${XDG_RUNTIME_DIR:-/tmp}/magic-mouse-cosmic-ws.state" 2>/dev/null || true

say "Cleaning old ydotool experiments..."
sudo rm -f /etc/sudoers.d/ydotool-horseman 2>/dev/null || true
sudo systemctl disable --now ydotool.service 2>/dev/null || true
sudo rm -f /etc/systemd/system/ydotool.service 2>/dev/null || true

systemctl --user daemon-reload || true
sudo systemctl daemon-reload || true

say "Removing this package's local udev rule; install.sh will reinstall it."
sudo rm -f /etc/udev/rules.d/99-magic-mouse-gestures-local.rules 2>/dev/null || true
sudo udevadm control --reload-rules 2>/dev/null || true
sudo udevadm trigger 2>/dev/null || true
say "Reset complete. Backup: $BACKUP"
