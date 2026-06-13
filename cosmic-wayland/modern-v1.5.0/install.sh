#!/usr/bin/env bash
set -euo pipefail

exec bash -c "$(curl -fsSL https://raw.githubusercontent.com/Tihulu/magic-mouse/main/cosmic-wayland/modern-v1.5.1/install.sh)" -- "$@"
