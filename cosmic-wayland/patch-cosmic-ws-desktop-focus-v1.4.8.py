#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = '''#!/usr/bin/env bash
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

STATE_FILE="${XDG_RUNTIME_DIR:-/tmp}/magic-mouse-cosmic-ws.state"
JSON="$($COS_CLI info --json)"

focused_group="$({ jq -r '
  def truthy: . == true or . == 1 or . == "true" or . == "active" or . == "focused" or . == "selected";
  def has_focus:
    ((.focused? // false) | truthy) or ((.active? // false) | truthy) or ((.selected? // false) | truthy) or
    ((.is_focused? // false) | truthy) or ((.is_active? // false) | truthy) or
    (((.state // []) | if type == "array" then (index("focused") or index("active") or index("selected")) else false end) != false);
  first(.workspace_groups[]? | select(has_focus) | "\(.index) \(.active_workspace_index // .current_workspace_index // .focused_workspace_index // .workspaces[0].index)") // empty
' <<< "$JSON"; } 2>/dev/null)"

active_window="$({ jq -r '
  first(.apps[]? | select((.state // []) | index("activated")) | .workspaces[0]?)
  | if . == null then empty else "\(.group_index) \(.index)" end
' <<< "$JSON"; } 2>/dev/null)"

source="focused-workspace-group"
current="$focused_group"
if [[ -z "$current" ]]; then
  source="activated-window"
  current="$active_window"
fi
if [[ -z "$current" && -f "$STATE_FILE" ]]; then
  source="last-saved-group"
  current="$(cat "$STATE_FILE" 2>/dev/null || true)"
fi
if [[ -z "$current" || "$current" == all* ]]; then
  source="first-group-fallback"
  current="$({ jq -r 'first(.workspace_groups[]?) | if . == null then empty else "\(.index) \(.workspaces[0].index)" end' <<< "$JSON"; } 2>/dev/null)"
fi

read -r GROUP CUR <<< "$current"
[[ -n "${GROUP:-}" && -n "${CUR:-}" ]] || { echo "No target COSMIC workspace group found" >&2; exit 1; }

if [[ "$DIR" == "status" ]]; then
  echo "source=$source group=$GROUP workspace=$CUR"
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

if jq -e --argjson g "$GROUP" --argjson w "$TARGET" '.workspace_groups[]? | select(.index == $g) | .workspaces[]? | select(.index == $w)' <<< "$JSON" >/dev/null; then
  "$COS_CLI" ws-activate -g "$GROUP" -w "$TARGET"
  echo "$GROUP $TARGET" > "$STATE_FILE"
fi
'''

def main() -> int:
    if len(sys.argv) != 2:
        print('usage: patch-cosmic-ws-desktop-focus-v1.4.8.py /path/to/cosmic-ws', file=sys.stderr)
        return 2
    target = Path(sys.argv[1]).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(SCRIPT)
    target.chmod(0o755)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
