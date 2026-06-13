#!/usr/bin/env bash
set -euo pipefail

VERSION="1.5.0-modern"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

say() { printf '\033[1;32m[modern ui %s]\033[0m %s\n' "$VERSION" "$*"; }

say "Installing stable v1.4.8 base first..."
bash -c "$(curl -fsSL https://raw.githubusercontent.com/Tihulu/magic-mouse/main/cosmic-wayland/setup-cosmic-v1.4.8.sh)"

say "Downloading modern UI patch..."
curl -fsSL https://raw.githubusercontent.com/Tihulu/magic-mouse/main/cosmic-wayland/modern-v1.5.0/patch-modern-ui-v1.5.0.py -o "$TMP/patch-modern-ui-v1.5.0.py"

panel="$HOME/.local/bin/magic-mouse-control-panel"
if [[ ! -f "$panel" ]]; then
  echo "Control panel was not installed: $panel" >&2
  exit 1
fi

say "Applying lightweight Apple-like Tk styling..."
python3 "$TMP/patch-modern-ui-v1.5.0.py" "$panel"
python3 -m py_compile "$panel"

say "Done. Launch with: gtk-launch magic-mouse-control-panel"
