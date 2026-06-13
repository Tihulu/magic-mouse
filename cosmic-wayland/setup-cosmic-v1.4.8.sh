#!/usr/bin/env bash
set -euo pipefail

VERSION="1.4.8"
REPO_URL="https://github.com/Tihulu/magic-mouse.git"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

say() { printf '\033[1;32m[cosmic setup v%s]\033[0m %s\n' "$VERSION" "$*"; }
warn() { printf '\033[1;33m[warn]\033[0m %s\n' "$*"; }

say "Cloning repository..."
git clone --depth 1 "$REPO_URL" "$TMP/magic-mouse"
cd "$TMP/magic-mouse/cosmic-wayland"
chmod +x *.sh bin/* patch-mode-indicator-v1.4.8.py 2>/dev/null || true

if [[ -f install.sh ]]; then
  say "Normalizing install.sh to v${VERSION}..."
  sed -i 's/^VERSION=.*/VERSION="1.4.8"/' install.sh
  sed -i 's/^StartupWMClass=.*/StartupWMClass=Tk/' install.sh
  sed -i 's/^X-GNOME-WMClass=.*/X-GNOME-WMClass=Tk/' install.sh
  if ! grep -q '^StartupNotify=true' install.sh; then
    sed -i '/^X-GNOME-WMClass=Tk/a StartupNotify=true' install.sh || true
  fi
fi

say "Running COSMIC Wayland installer..."
./install.sh "$@"

control_panel="$HOME/.local/bin/magic-mouse-control-panel"
if [[ -f "$control_panel" ]]; then
  say "Applying v1.4.8 status text fix..."
  sed -i 's/value="Loading\.\.\."/value="Checking status…"/' "$control_panel"
  if [[ -f patch-mode-indicator-v1.4.8.py ]]; then
    say "Applying mode indicator patch..."
    python3 patch-mode-indicator-v1.4.8.py "$control_panel"
  fi
  say "Checking installed control panel syntax..."
  python3 -m py_compile "$control_panel" || {
    warn "Installed control panel failed syntax check. Reinstalling clean copy from repository."
    cp "bin/magic-mouse-control-panel" "$control_panel"
    chmod +x "$control_panel"
    sed -i 's/value="Loading\.\.\."/value="Checking status…"/' "$control_panel"
    if [[ -f patch-mode-indicator-v1.4.8.py ]]; then
      python3 patch-mode-indicator-v1.4.8.py "$control_panel"
    fi
    python3 -m py_compile "$control_panel"
  }
fi

desktop_file="$HOME/.local/share/applications/magic-mouse-control-panel.desktop"
if [[ -f "$desktop_file" ]]; then
  sed -i 's/^StartupWMClass=.*/StartupWMClass=Tk/' "$desktop_file"
  sed -i 's/^X-GNOME-WMClass=.*/X-GNOME-WMClass=Tk/' "$desktop_file"
  if ! grep -q '^StartupNotify=' "$desktop_file"; then
    printf '%s\n' 'StartupNotify=true' >> "$desktop_file"
  fi
fi

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -q "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
fi

say "Done. Launch with: gtk-launch magic-mouse-control-panel"
say "This build shows the current Workspace/Browser mode under the session line."
