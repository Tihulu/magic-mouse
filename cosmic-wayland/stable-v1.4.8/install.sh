#!/usr/bin/env bash
set -euo pipefail

exec bash -c "$(curl -fsSL https://raw.githubusercontent.com/Tihulu/magic-mouse/main/cosmic-wayland/setup-cosmic-v1.4.8.sh)" -- "$@"
