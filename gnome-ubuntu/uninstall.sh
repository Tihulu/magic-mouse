#!/usr/bin/env bash
set -euo pipefail
UUID="magic-mouse-workspaces@horseman.local"
if command -v gnome-extensions >/dev/null 2>&1; then
  gnome-extensions disable "$UUID" 2>/dev/null || true
fi
rm -rf "$HOME/.local/share/gnome-shell/extensions/$UUID"
rm -f "$HOME/.local/bin/magic-mouse-ws" "$HOME/.local/bin/magic-mouse-gnome-probe" "$HOME/.local/bin/magic-mouse-gnome-integrate"
if [[ -f "$HOME/.local/bin/cosmic-ws" ]] && grep -q 'magic-mouse-ws' "$HOME/.local/bin/cosmic-ws"; then
  rm -f "$HOME/.local/bin/cosmic-ws"
fi
rm -f "$HOME/.config/systemd/user/magic-mouse-gestures.service.d/10-gnome-workspaces.conf"
systemctl --user daemon-reload 2>/dev/null || true
echo "Uninstalled Magic Mouse GNOME/Ubuntu workspace backend. Log out/in to unload the extension fully on Wayland."
