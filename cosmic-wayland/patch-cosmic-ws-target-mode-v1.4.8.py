#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = r'''#!/usr/bin/env bash
set -euo pipefail

DIR="${1:-}"
case "$DIR" in
  prev) DIR="up" ;;
  next) DIR="down" ;;
esac
if [[ "$DIR" != "up" && "$DIR" != "down" && "$DIR" != "status" ]]; then
  echo "usage: cosmic-ws up|down|status" >&2
  exit 2
fi

COS_CLI="${COS_CLI:-$HOME/.cargo/bin/cos-cli}"
if [[ ! -x "$COS_CLI" ]]; then
  COS_CLI="$(command -v cos-cli || true)"
fi
if [[ -z "$COS_CLI" || ! -x "$COS_CLI" ]]; then
  echo "cos-cli was not found" >&2
  exit 1
fi
if ! command -v jq >/dev/null 2>&1; then
  echo "jq was not found" >&2
  exit 1
fi

PROFILE="${MAGIC_MOUSE_PROFILE:-$HOME/.config/magic-mouse-gestures/profile.env}"
STATE_FILE="${XDG_RUNTIME_DIR:-/tmp}/magic-mouse-cosmic-ws.state"
JSON="$($COS_CLI info --json)"

MODE="auto"
if [[ -f "$PROFILE" ]]; then
  M="$(grep -E '^WORKSPACE_TARGET=' "$PROFILE" | tail -n1 | cut -d= -f2- || true)"
  M="${M//\"/}"
  M="${M//\'/}"
  [[ -n "$M" ]] && MODE="$M"
fi
MODE="${MODE,,}"
case "$MODE" in
  auto|stable|focused|focused-window) MODE="auto" ;;
  screen1|monitor1|display1|1) MODE="screen1" ;;
  screen2|monitor2|display2|2) MODE="screen2" ;;
  all|both|sync) MODE="all" ;;
  *) MODE="auto" ;;
esac

mapfile -t GROUPS < <(jq -r '.workspace_groups[]? | .index' <<< "$JSON" | sort -n)
if [[ "${#GROUPS[@]}" -eq 0 ]]; then
  echo "No COSMIC workspace groups found" >&2
  exit 1
fi

workspace_exists() {
  jq -e --argjson g "$1" --argjson w "$2" '.workspace_groups[]? | select(.index == $g) | .workspaces[]? | select(.index == $w)' <<< "$JSON" >/dev/null
}

workspace_list() {
  jq -r --argjson g "$1" '.workspace_groups[]? | select(.index == $g) | .workspaces[]? | .index' <<< "$JSON" | sort -n
}

first_ws_for_group() {
  jq -r --argjson g "$1" '.workspace_groups[]? | select(.index == $g) | .workspaces[0].index' <<< "$JSON"
}

saved_ws_for_group() {
  local sg="" sw=""
  if [[ -f "$STATE_FILE" ]]; then
    read -r sg sw < "$STATE_FILE" || true
    if [[ "$sg" == "$1" && -n "$sw" ]] && workspace_exists "$1" "$sw"; then
      echo "$sw"
      return 0
    fi
  fi
  first_ws_for_group "$1"
}

active_window_group_ws() {
  jq -r 'first(.apps[]? | select((.state // []) | index("activated")) | .workspaces[0]?) | if . == null then empty else "\(.group_index) \(.index)" end' <<< "$JSON"
}

GROUP=""
CUR=""
SOURCE=""

if [[ "$MODE" == "screen1" ]]; then
  GROUP="${GROUPS[0]}"
  CUR="$(saved_ws_for_group "$GROUP")"
  SOURCE="screen1"
elif [[ "$MODE" == "screen2" ]]; then
  GROUP="${GROUPS[1]:-${GROUPS[0]}}"
  CUR="$(saved_ws_for_group "$GROUP")"
  SOURCE="screen2"
else
  CURRENT="$(active_window_group_ws)"
  if [[ -n "$CURRENT" ]]; then
    read -r GROUP CUR <<< "$CURRENT"
    SOURCE="activated-window"
  fi
  if [[ -z "${GROUP:-}" || -z "${CUR:-}" ]]; then
    if [[ -f "$STATE_FILE" ]]; then
      read -r GROUP CUR < "$STATE_FILE" || true
      if [[ "${GROUP:-}" == "all" ]] || ! workspace_exists "$GROUP" "$CUR"; then
        GROUP=""
        CUR=""
      else
        SOURCE="last-state"
      fi
    fi
  fi
  if [[ -z "${GROUP:-}" || -z "${CUR:-}" ]]; then
    GROUP="${GROUPS[0]}"
    CUR="$(saved_ws_for_group "$GROUP")"
    SOURCE="fallback-first-group"
  fi
fi

if [[ -z "${GROUP:-}" || -z "${CUR:-}" ]]; then
  echo "No target workspace group found" >&2
  exit 1
fi

if [[ "$DIR" == "status" ]]; then
  echo "mode=$MODE source=$SOURCE group=$GROUP workspace=$CUR groups=${GROUPS[*]}"
  exit 0
fi

mapfile -t IDX < <(workspace_list "$GROUP")
if [[ "${#IDX[@]}" -eq 0 ]]; then
  echo "No workspaces found for group $GROUP" >&2
  exit 1
fi

POS=-1
for i in "${!IDX[@]}"; do
  if [[ "${IDX[$i]}" == "$CUR" ]]; then
    POS="$i"
    break
  fi
done
if [[ "$POS" == "-1" ]]; then
  echo "Workspace $CUR not found in group $GROUP" >&2
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

if [[ "$MODE" == "all" ]]; then
  for G in "${GROUPS[@]}"; do
    if workspace_exists "$G" "$TARGET"; then
      "$COS_CLI" ws-activate -g "$G" -w "$TARGET" >/dev/null 2>&1 || true
    fi
  done
  echo "all $TARGET" > "$STATE_FILE"
else
  if workspace_exists "$GROUP" "$TARGET"; then
    "$COS_CLI" ws-activate -g "$GROUP" -w "$TARGET"
    echo "$GROUP $TARGET" > "$STATE_FILE"
  fi
fi
'''

def main() -> int:
    if len(sys.argv) != 2:
        print('usage: patch-cosmic-ws-target-mode-v1.4.8.py /path/to/cosmic-ws', file=sys.stderr)
        return 2
    target = Path(sys.argv[1]).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(SCRIPT)
    target.chmod(0o755)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
