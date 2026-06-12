#!/usr/bin/env bash
set -euo pipefail

VERSION="1.4.4"
REPO="Tihulu/magic-mouse"
BRANCH="main"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

say() { printf '\033[1;32m[cosmic quick install v%s]\033[0m %s\n' "$VERSION" "$*"; }
warn() { printf '\033[1;33m[warn]\033[0m %s\n' "$*"; }

archive="$TMP/magic-mouse.tar.gz"
url="https://github.com/${REPO}/archive/refs/heads/${BRANCH}.tar.gz"

say "Downloading ${REPO}/${BRANCH}..."
if command -v curl >/dev/null 2>&1; then
  curl -fsSL "$url" -o "$archive"
elif command -v wget >/dev/null 2>&1; then
  wget -qO "$archive" "$url"
else
  echo "curl or wget is required." >&2
  exit 1
fi

tar -xzf "$archive" -C "$TMP"
cd "$TMP/magic-mouse-${BRANCH}/cosmic-wayland"
chmod +x *.sh bin/* 2>/dev/null || true

say "Running COSMIC Wayland installer..."
./install.sh "$@"

say "Applying v1.4.4 COSMIC dock icon fix..."
desktop_file="$HOME/.local/share/applications/magic-mouse-control-panel.desktop"
if [[ -f "$desktop_file" ]]; then
  sed -i 's/^StartupWMClass=.*/StartupWMClass=Tk/' "$desktop_file"
  sed -i 's/^X-GNOME-WMClass=.*/X-GNOME-WMClass=Tk/' "$desktop_file"
  if ! grep -q '^StartupNotify=' "$desktop_file"; then
    printf '%s\n' 'StartupNotify=true' >> "$desktop_file"
  fi
else
  warn "Desktop launcher was not found: $desktop_file"
fi

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -q "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
fi

say "Done. Launch with: gtk-launch magic-mouse-control-panel"
say "Or open Magic Mouse Control Panel from the app launcher."
