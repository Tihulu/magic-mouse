#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = r'''#!/usr/bin/env bash
set -euo pipefail

DIR="${1:-}"
if [[ "$DIR" != "up" && "$DIR" != "down" && "$DIR" != "prev" && "$DIR" != "next" && "$DIR" != "status" ]]; then
  echo "usage: cosmic-ws up|down|prev|next|status" >&2
  exit 2
fi
case "$DIR" in prev) DIR="up" ;; next) DIR="down" ;; esac

COS_CLI="${COS_CLI:-$HOME/.cargo/bin/cos-cli}"
[[ -x "$COS_CLI" ]] || COS_CLI="$(command -v cos-cli || true)"
[[ -n "$COS_CLI" && -x "$COS_CLI" ]] || { echo "cos-cli not found" >&2; exit 1; }
command -v jq >/dev/null 2>&1 || { echo "jq not found" >&2; exit 1; }

PROFILE="${MAGIC_MOUSE_PROFILE:-$HOME/.config/magic-mouse-gestures/profile.env}"
STATE_FILE="${XDG_RUNTIME_DIR:-/tmp}/magic-mouse-cosmic-ws.state"
JSON="$($COS_CLI info --json)"

mode="${WORKSPACE_TARGET:-auto}"
if [[ -f "$PROFILE" ]]; then
  raw="$(grep -E '^WORKSPACE_TARGET=' "$PROFILE" | tail -n1 | cut -d= -f2- || true)"
  raw="${raw%\"}"; raw="${raw#\"}"; raw="${raw%\'}"; raw="${raw#\'}"
  [[ -n "$raw" ]] && mode="$raw"
fi
mode="${mode,,}"
case "$mode" in
  auto|stable|focused|focused-window) mode="auto" ;;
  screen1|monitor1|display1|1) mode="screen1" ;;
  screen2|monitor2|display2|2) mode="screen2" ;;
  all|both|sync) mode="all" ;;
  *) mode="auto" ;;
esac

workspace_exists() {
  local group="$1" ws="$2"
  jq -e --argjson g "$group" --argjson w "$ws" '.workspace_groups[]? | select(.index == $g) | .workspaces[]? | select(.index == $w)' <<< "$JSON" >/dev/null
}

active_ws_for_group() {
  local group="$1"
  jq -r --argjson g "$group" '.workspace_groups[]? | select(.index == $g) | (.active_workspace_index // .current_workspace_index // .focused_workspace_index // .workspaces[0].index)' <<< "$JSON"
}

mapfile -t GROUPS < <(jq -r '.workspace_groups[]? | .index' <<< "$JSON" | sort -n)
[[ "${#GROUPS[@]}" -gt 0 ]] || { echo "No COSMIC workspace groups found" >&2; exit 1; }

active_window="$(jq -r 'first(.apps[]? | select((.state // []) | index("activated")) | .workspaces[0]?) | if . == null then empty else "\(.group_index) \(.index)" end' <<< "$JSON")"

GROUP=""; CUR=""; source=""
if [[ "$mode" == "screen1" ]]; then
  GROUP="${GROUPS[0]}"; CUR="$(active_ws_for_group "$GROUP")"; source="screen1-override"
elif [[ "$mode" == "screen2" ]]; then
  GROUP="${GROUPS[1]:-${GROUPS[0]}}"; CUR="$(active_ws_for_group "$GROUP")"; source="screen2-override"
else
  # Default/stable principle: use the activated window's workspace group.
  if [[ -n "$active_window" ]]; then
    read -r GROUP CUR <<< "$active_window"; source="activated-window"
  fi
  if [[ -z "${GROUP:-}" || -z "${CUR:-}" ]]; then
    if [[ -f "$STATE_FILE" ]]; then
      read -r GROUP CUR < "$STATE_FILE" || true
      [[ "${GROUP:-}" == "all" ]] && GROUP="" && CUR=""
      source="last-saved-group"
    fi
  fi
  if [[ -z "${GROUP:-}" || -z "${CUR:-}" ]]; then
    GROUP="${GROUPS[0]}"; CUR="$(active_ws_for_group "$GROUP")"; source="first-group-fallback"
  fi
fi

[[ -n "${GROUP:-}" && -n "${CUR:-}" ]] || { echo "No target COSMIC workspace group found" >&2; exit 1; }

if [[ "$DIR" == "status" ]]; then
  echo "mode=$mode source=$source group=$GROUP workspace=$CUR groups=${GROUPS[*]}"
  exit 0
fi

mapfile -t IDX < <(jq -r --argjson g "$GROUP" '.workspace_groups[]? | select(.index == $g) | .workspaces[]? | .index' <<< "$JSON" | sort -n)
[[ "${#IDX[@]}" -gt 0 ]] || exit 1

POS=-1
for i in "${!IDX[@]}"; do
  [[ "${IDX[$i]}" == "$CUR" ]] && POS="$i" && break
done
[[ "$POS" != "-1" ]] || exit 1

if [[ "$DIR" == "up" ]]; then TARGET_POS=$((POS - 1)); else TARGET_POS=$((POS + 1)); fi
(( TARGET_POS >= 0 && TARGET_POS < ${#IDX[@]} )) || exit 0
TARGET="${IDX[$TARGET_POS]}"

if [[ "$mode" == "all" ]]; then
  for G in "${GROUPS[@]}"; do
    workspace_exists "$G" "$TARGET" && "$COS_CLI" ws-activate -g "$G" -w "$TARGET" >/dev/null 2>&1 || true
  done
  echo "all $TARGET" > "$STATE_FILE"
else
  workspace_exists "$GROUP" "$TARGET" && "$COS_CLI" ws-activate -g "$GROUP" -w "$TARGET" && echo "$GROUP $TARGET" > "$STATE_FILE"
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
