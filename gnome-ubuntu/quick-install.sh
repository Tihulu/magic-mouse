#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/Tihulu/magic-mouse.git"
TMP_DIR="$(mktemp -d)"
cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

if command -v git >/dev/null 2>&1; then
  git clone --depth 1 "$REPO_URL" "$TMP_DIR/magic-mouse"
else
  sudo apt update
  sudo apt install -y git
  git clone --depth 1 "$REPO_URL" "$TMP_DIR/magic-mouse"
fi

cd "$TMP_DIR/magic-mouse/gnome-ubuntu"
./install.sh --install-deps --install-udev "$@"
