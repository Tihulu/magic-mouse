#!/usr/bin/env bash
set -euo pipefail

BASE_URL="https://raw.githubusercontent.com/Tihulu/magic-mouse/main/cosmic-wayland"
PANEL="$HOME/.local/bin/magic-mouse-control-panel"
DESKTOP="$HOME/.local/share/applications/magic-mouse-control-panel.desktop"
ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"
ICON_FILE="$ICON_DIR/magic-mouse-control-panel.svg"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

printf '\033[1;32m[modern v1.5.1]\033[0m Installing stable COSMIC backend first...\n'
bash -c "$(curl -fsSL "$BASE_URL/setup-cosmic-v1.4.8-relaxed.sh")" -- "$@"

printf '\033[1;32m[modern v1.5.1]\033[0m Installing real modern control panel...\n'
curl -fsSL "$BASE_URL/modern-v1.5.1/magic-mouse-control-panel-modern" -o "$PANEL"
chmod +x "$PANEL"

printf '\033[1;32m[modern v1.5.1]\033[0m Installing modern app icon...\n'
mkdir -p "$ICON_DIR"
curl -fsSL "$BASE_URL/modern-v1.5.1/assets/magic-mouse-control-panel.svg" -o "$ICON_FILE"

printf '\033[1;32m[modern v1.5.1]\033[0m Applying final UI polish...\n'
curl -fsSL "$BASE_URL/modern-v1.5.1/patch-modern-panel-v1.5.1.py" -o "$TMP/patch-modern-panel-v1.5.1.py"
python3 "$TMP/patch-modern-panel-v1.5.1.py" "$PANEL"
python3 -m py_compile "$PANEL"

printf '\033[1;32m[modern v1.5.1]\033[0m Applying icon logo...\n'
curl -fsSL "$BASE_URL/modern-v1.5.1/patch-modern-icon-v1.5.1.py" -o "$TMP/patch-modern-icon-v1.5.1.py"
python3 "$TMP/patch-modern-icon-v1.5.1.py" "$PANEL"
python3 -m py_compile "$PANEL"

printf '\033[1;32m[modern v1.5.1]\033[0m Adding workspace target selector...\n'
curl -fsSL "$BASE_URL/modern-v1.5.1/patch-modern-workspace-target-fixed-v1.5.1.py" -o "$TMP/patch-modern-workspace-target-fixed-v1.5.1.py"
python3 "$TMP/patch-modern-workspace-target-fixed-v1.5.1.py" "$PANEL"
python3 -m py_compile "$PANEL"

printf '\033[1;32m[modern v1.5.1]\033[0m Fixing details refresh...\n'
curl -fsSL "$BASE_URL/modern-v1.5.1/patch-modern-details-v1.5.1.py" -o "$TMP/patch-modern-details-v1.5.1.py"
python3 "$TMP/patch-modern-details-v1.5.1.py" "$PANEL"
python3 -m py_compile "$PANEL"

if [[ -f "$DESKTOP" ]]; then
  sed -i 's/^Name=.*/Name=Magic Mouse Control Panel/' "$DESKTOP" || true
  if grep -q '^Icon=' "$DESKTOP"; then
    sed -i 's/^Icon=.*/Icon=magic-mouse-control-panel/' "$DESKTOP" || true
  else
    printf '%s\n' 'Icon=magic-mouse-control-panel' >> "$DESKTOP"
  fi
  sed -i 's/^StartupWMClass=.*/StartupWMClass=Tk/' "$DESKTOP" || true
  sed -i 's/^X-GNOME-WMClass=.*/X-GNOME-WMClass=Tk/' "$DESKTOP" || true
fi

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -q "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
fi

printf '\033[1;32m[modern v1.5.1]\033[0m Done. Launch with: gtk-launch magic-mouse-control-panel\n'
