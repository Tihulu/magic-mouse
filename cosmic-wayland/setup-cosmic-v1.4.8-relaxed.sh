#!/usr/bin/env bash
set -euo pipefail

say() { printf '\033[1;32m[cosmic relaxed setup]\033[0m %s\n' "$*"; }

say "Installing stable v1.4.8 base..."
bash -c "$(curl -fsSL https://raw.githubusercontent.com/Tihulu/magic-mouse/main/cosmic-wayland/setup-cosmic-v1.4.8.sh)" -- "$@"

panel="$HOME/.local/bin/magic-mouse-control-panel"
patch_url="https://raw.githubusercontent.com/Tihulu/magic-mouse/main/cosmic-wayland/patch-sensitivity-v1.4.8.py"
patch_file="$(mktemp)"
trap 'rm -f "$patch_file"' EXIT

say "Applying calmer Relaxed and new Very Relaxed preset..."
curl -fsSL "$patch_url" -o "$patch_file"
python3 "$patch_file" "$panel"
python3 -m py_compile "$panel"

say "Done. Open the panel and choose Relaxed or Very Relaxed."
