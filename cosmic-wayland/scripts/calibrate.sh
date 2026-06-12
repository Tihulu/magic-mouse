#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROFILE="${1:-profiles/cosmic.env}"
OUT_DIR="$ROOT_DIR/calibration"
LOG="$OUT_DIR/magic-mouse-$(date +%Y%m%d-%H%M%S).jsonl"
mkdir -p "$OUT_DIR"

cat <<MSG
Calibration mode
----------------
1. Use two-finger swipe left 3 times.
2. Use two-finger swipe right 3 times.
3. Use two-finger swipe up 3 times.
4. Use two-finger swipe down 3 times.
5. Press Ctrl+C.

Log file: $LOG
MSG

python3 "$ROOT_DIR/src/magic_mouse_daemon.py" \
  --profile "$ROOT_DIR/$PROFILE" \
  --debug \
  --debug-hid \
  --dry-run \
  --record-log "$LOG"
