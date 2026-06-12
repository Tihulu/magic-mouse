#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UUID="magic-mouse-workspaces@horseman.local"
EXT_DIR="$HOME/.local/share/gnome-shell/extensions/$UUID"
BIN_DIR="$HOME/.local/bin"

major_from_gnome_shell() {
  if command -v gnome-shell >/dev/null 2>&1; then
    gnome-shell --version | awk '{print $NF}' | cut -d. -f1
  else
    printf '0\n'
  fi
}

MAJOR="${GNOME_SHELL_MAJOR:-$(major_from_gnome_shell)}"
case "$MAJOR" in
  42|43|44) SRC="$ROOT/extension-src/gnome-42-44/$UUID" ;;
  45|46|47|48|49) SRC="$ROOT/extension-src/gnome-45-plus/$UUID" ;;
  0) SRC="$ROOT/extension-src/gnome-45-plus/$UUID" ;;
  *)
    echo "Warning: untested GNOME Shell major version '$MAJOR'. Installing GNOME 45+ extension variant." >&2
    SRC="$ROOT/extension-src/gnome-45-plus/$UUID"
    ;;
esac

mkdir -p "$EXT_DIR" "$BIN_DIR"
rm -rf "$EXT_DIR"
mkdir -p "$EXT_DIR"
cp -a "$SRC/"* "$EXT_DIR/"
cp -a "$ROOT/bin/magic-mouse-ws" "$ROOT/bin/magic-mouse-gnome-probe" "$ROOT/bin/magic-mouse-gnome-integrate" "$BIN_DIR/"
chmod +x "$BIN_DIR/magic-mouse-ws" "$BIN_DIR/magic-mouse-gnome-probe" "$BIN_DIR/magic-mouse-gnome-integrate"

if command -v gnome-extensions >/dev/null 2>&1; then
  gnome-extensions enable "$UUID" 2>/dev/null || true
fi

cat <<MSG
Installed Magic Mouse GNOME/Ubuntu workspace backend 0.1.1.

Detected GNOME Shell major version: $MAJOR
Installed extension variant: $SRC

Next steps:
  1) On GNOME Wayland, log out and log back in.
  2) Run: magic-mouse-gnome-probe
  3) Test: magic-mouse-ws down && sleep 0.5 && magic-mouse-ws up

Optional integration if the old daemon still calls cosmic-ws:
  magic-mouse-gnome-integrate install-cosmic-ws-shim
MSG
