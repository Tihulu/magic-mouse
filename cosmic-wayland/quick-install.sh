#!/usr/bin/env bash
set -euo pipefail

REPO="Tihulu/magic-mouse"
BRANCH="main"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

archive="$TMP/magic-mouse.tar.gz"
url="https://github.com/${REPO}/archive/refs/heads/${BRANCH}.tar.gz"

echo "Downloading ${REPO}/${BRANCH}..."
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
./install.sh "$@"
