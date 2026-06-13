#!/usr/bin/env bash
set -euo pipefail

say() { printf '\033[1;32m[cosmic relaxed setup]\033[0m %s\n' "$*"; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

say "Installing stable v1.4.8 base..."
bash -c "$(curl -fsSL https://raw.githubusercontent.com/Tihulu/magic-mouse/main/cosmic-wayland/setup-cosmic-v1.4.8.sh)" -- "$@"

panel="$HOME/.local/bin/magic-mouse-control-panel"
cosmic_ws="$HOME/.local/bin/cosmic-ws"

say "Applying Tihulu/custom sensitivity presets..."
curl -fsSL "https://raw.githubusercontent.com/Tihulu/magic-mouse/main/cosmic-wayland/patch-sensitivity-v1.4.8.py" -o "$TMP/patch-sensitivity-v1.4.8.py"
python3 "$TMP/patch-sensitivity-v1.4.8.py" "$panel"
python3 -m py_compile "$panel"

say "Applying focused-monitor COSMIC workspace helper..."
curl -fsSL "https://raw.githubusercontent.com/Tihulu/magic-mouse/main/cosmic-wayland/patch-cosmic-ws-desktop-focus-v1.4.8.py" -o "$TMP/patch-cosmic-ws-desktop-focus-v1.4.8.py"
python3 "$TMP/patch-cosmic-ws-desktop-focus-v1.4.8.py" "$cosmic_ws"

say "Done. Workspaces now follow the focused COSMIC monitor group."
