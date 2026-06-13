#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

COSMIC_WS = r'''#!/usr/bin/env bash
set -euo pipefail

DIR="${1:-}"

if [[ "$DIR" != "up" && "$DIR" != "down" && "$DIR" != "prev" && "$DIR" != "next" ]]; then
  echo "usage: cosmic-ws up|down|prev|next" >&2
  exit 2
fi

case "$DIR" in
  prev) DIR="up" ;;
  next) DIR="down" ;;
esac

COS_CLI="${COS_CLI:-$HOME/.cargo/bin/cos-cli}"
if [[ ! -x "$COS_CLI" ]]; then
  COS_CLI="$(command -v cos-cli || true)"
fi

if [[ -z "$COS_CLI" || ! -x "$COS_CLI" ]]; then
  echo "cos-cli was not found. Run the installer again to install it." >&2
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "jq was not found." >&2
  exit 1
fi

STATE_FILE="${XDG_RUNTIME_DIR:-/tmp}/magic-mouse-cosmic-ws.state"
JSON="$($COS_CLI info --json)"

workspace_exists() {
  local group="$1"
  local ws="$2"
  jq -e --argjson g "$group" --argjson w "$ws" '
    .workspace_groups[]?
    | select(.index == $g)
    | .workspaces[]?
    | select(.index == $w)
  ' <<< "$JSON" >/dev/null
}

# Per-monitor behavior: choose the workspace group from the currently
# focused/activated window. Focus monitor 1 => monitor 1 changes.
# Focus monitor 2 => monitor 2 changes.
CURRENT="$(
  jq -r '
    first(
      .apps[]?
      | select((.state // []) | index("activated"))
      | .workspaces[0]?
    )
    | if . == null then empty else "\(.group_index) \(.index)" end
  ' <<< "$JSON"
)"

GROUP=""
CUR=""
if [[ -n "$CURRENT" ]]; then
  read -r GROUP CUR <<< "$CURRENT"
fi

# Fallback to the last focused group if no activated window is visible.
if [[ -z "${GROUP:-}" || -z "${CUR:-}" ]]; then
  if [[ -f "$STATE_FILE" ]]; then
    read -r GROUP CUR < "$STATE_FILE" || true
    if [[ "${GROUP:-}" == "all" ]]; then
      GROUP=""
      CUR=""
    fi
  fi
fi

# Final fallback: first workspace group, so the helper still does something.
if [[ -z "${GROUP:-}" || -z "${CUR:-}" ]]; then
  CURRENT="$(
    jq -r '
      first(.workspace_groups[]?)
      | if . == null then empty else "\(.index) \(.workspaces[0].index)" end
    ' <<< "$JSON"
  )"
  if [[ -n "$CURRENT" ]]; then
    read -r GROUP CUR <<< "$CURRENT"
  fi
fi

if [[ -z "${GROUP:-}" || -z "${CUR:-}" ]]; then
  echo "No active COSMIC workspace group was found. Focus a window on the target monitor and try again." >&2
  exit 1
fi

mapfile -t IDX < <(
  jq -r --argjson g "$GROUP" '
    .workspace_groups[]?
    | select(.index == $g)
    | .workspaces[]?
    | .index
  ' <<< "$JSON" | sort -n
)

if [[ "${#IDX[@]}" -eq 0 ]]; then
  echo "Workspace list was not found for group $GROUP." >&2
  exit 1
fi

POS="-1"
for i in "${!IDX[@]}"; do
  if [[ "${IDX[$i]}" == "$CUR" ]]; then
    POS="$i"
    break
  fi
done

if [[ "$POS" == "-1" ]]; then
  echo "The active workspace was not found in group $GROUP." >&2
  exit 1
fi

if [[ "$DIR" == "up" ]]; then
  TARGET_POS=$((POS - 1))
else
  TARGET_POS=$((POS + 1))
fi

if (( TARGET_POS < 0 || TARGET_POS >= ${#IDX[@]} )); then
  exit 0
fi

TARGET="${IDX[$TARGET_POS]}"

# Activate only the focused/active monitor's workspace group.
if workspace_exists "$GROUP" "$TARGET"; then
  "$COS_CLI" ws-activate -g "$GROUP" -w "$TARGET"
  echo "$GROUP $TARGET" > "$STATE_FILE"
fi
'''


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: patch-cosmic-ws-multimonitor-v1.4.8.py /path/to/cosmic-ws", file=sys.stderr)
        return 2
    target = Path(sys.argv[1]).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(COSMIC_WS)
    target.chmod(0o755)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
