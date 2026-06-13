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

mapfile -t GROUPS < <(
  jq -r '.workspace_groups[]? | .index' <<< "$JSON" | sort -n
)

if [[ "${#GROUPS[@]}" -eq 0 ]]; then
  echo "No COSMIC workspace groups were found." >&2
  exit 1
fi

ACTIVE="$(
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
if [[ -n "$ACTIVE" ]]; then
  read -r GROUP CUR <<< "$ACTIVE"
fi

if [[ -z "${CUR:-}" && -f "$STATE_FILE" ]]; then
  # Current format: all <workspace-index>. Legacy format: <group> <workspace-index>.
  read -r A B < "$STATE_FILE" || true
  if [[ "${A:-}" == "all" && -n "${B:-}" ]]; then
    CUR="$B"
  elif [[ -n "${B:-}" ]]; then
    CUR="$B"
  fi
fi

if [[ -z "${GROUP:-}" ]]; then
  GROUP="${GROUPS[0]}"
fi

if [[ -z "${CUR:-}" ]]; then
  echo "No active workspace was found. Focus a window and try again." >&2
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
  # Fall back to the closest valid workspace in the active/reference group.
  POS="0"
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

# COSMIC can expose one workspace group per monitor. Activate the same target
# workspace index on every group so multi-monitor desktops move together.
for G in "${GROUPS[@]}"; do
  if workspace_exists "$G" "$TARGET"; then
    "$COS_CLI" ws-activate -g "$G" -w "$TARGET" >/dev/null 2>&1 || true
  fi
done

echo "all $TARGET" > "$STATE_FILE"
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
