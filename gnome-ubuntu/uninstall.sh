#!/usr/bin/env bash
set -euo pipefail
UUID="magic-mouse-workspaces@horseman.local"

systemctl --user disable --now magic-mouse-gestures.service 2>/dev/null || true

if command -v gnome-extensions >/dev/null 2>&1; then
  gnome-extensions disable "$UUID" 2>/dev/null || true
fi

rm -rf "$HOME/.local/share/gnome-shell/extensions/$UUID"
rm -f \
  "$HOME/.local/bin/magic-mouse-ws" \
  "$HOME/.local/bin/magic-mouse-gesture-daemon" \
  "$HOME/.local/bin/magic-mouse-control-panel" \
  "$HOME/.local/bin/magic-mouse-gnome-probe" \
  "$HOME/.local/bin/magic-mouse-gnome-integrate" \
  "$HOME/.local/bin/magic-mouse-diagnose" \
  "$HOME/.local/bin/magic-mouse-service"

if [[ -f "$HOME/.local/bin/cosmic-ws" ]] && grep -q 'magic-mouse-ws' "$HOME/.local/bin/cosmic-ws"; then
  rm -f "$HOME/.local/bin/cosmic-ws"
fi

rm -f "$HOME/.config/systemd/user/magic-mouse-gestures.service"
rm -rf "$HOME/.config/systemd/user/magic-mouse-gestures.service.d"
rm -f "$HOME/.local/share/applications/magic-mouse-control-panel.desktop"
systemctl --user daemon-reload 2>/dev/null || true

echo "Uninstalled Magic Mouse GNOME package."
echo "User config is preserved at: $HOME/.config/magic-mouse/config.json"
echo "If you installed the udev rule, remove it manually with: sudo rm /etc/udev/rules.d/99-magic-mouse-gestures.rules"
echo "Log out/in to unload the extension fully on Wayland."
