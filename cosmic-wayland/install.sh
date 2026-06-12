#!/usr/bin/env bash
set -euo pipefail

VERSION="1.4.3"
DEFAULT_MM_SOURCE="$HOME/Desktop/magicmouse/magic-mouse-linux-gestures-v0.6/magic-mouse-linux-gestures"
MM_SOURCE="${MM_SOURCE:-$DEFAULT_MM_SOURCE}"
PROFILE="$HOME/.config/magic-mouse-gestures/profile.env"
INSTALLED_DAEMON="$HOME/.local/share/magic-mouse-linux-gestures/src/magic_mouse_daemon.py"

say() { printf '\033[1;32m[install v%s]\033[0m %s\n' "$VERSION" "$*"; }
warn() { printf '\033[1;33m[warn]\033[0m %s\n' "$*"; }
err() { printf '\033[1;31m[error]\033[0m %s\n' "$*" >&2; }

if [[ "$EUID" -eq 0 ]]; then
  err "Do not run this script with sudo. It will ask for sudo only when needed."
  exit 1
fi

say "Installing magic-mouse-cosmic-workspaces."
say "Magic Mouse source directory: $MM_SOURCE"

if [[ ! -x "$MM_SOURCE/install.sh" ]]; then
  err "Magic Mouse install.sh was not found: $MM_SOURCE/install.sh"
  echo
  echo "Pass the correct directory like this:"
  echo "  MM_SOURCE=/full/path/to/magic-mouse-linux-gestures ./install.sh"
  exit 1
fi

say "Installing required packages..."
sudo apt update
sudo apt install -y git curl jq cargo rustc pkg-config libwayland-dev python3 python3-venv python3-tk wtype bluez acl

say "Installing/updating cos-cli..."
cargo install --git https://github.com/estin/cos-cli --force

mkdir -p "$HOME/.local/bin"

say "Installing the cosmic-ws helper..."
cat > "$HOME/.local/bin/cosmic-ws" <<'EOS'
#!/usr/bin/env bash
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
  echo "cos-cli was not found. Run install.sh again to install it." >&2
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

GROUP=""
CUR=""

if [[ -f "$STATE_FILE" ]]; then
  read -r GROUP CUR < "$STATE_FILE" || true
  if [[ -n "${GROUP:-}" && -n "${CUR:-}" ]]; then
    if ! workspace_exists "$GROUP" "$CUR"; then
      GROUP=""
      CUR=""
    fi
  fi
fi

if [[ -z "$GROUP" || -z "$CUR" ]]; then
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

  if [[ -z "$CURRENT" ]]; then
    echo "No active window/workspace was found. Focus a window, such as the terminal, and try again." >&2
    exit 1
  fi

  read -r GROUP CUR <<< "$CURRENT"
fi

mapfile -t IDX < <(
  jq -r --argjson g "$GROUP" '
    .workspace_groups[]?
    | select(.index == $g)
    | .workspaces[]?
    | .index
  ' <<< "$JSON"
)

if [[ "${#IDX[@]}" -eq 0 ]]; then
  echo "Workspace list was not found." >&2
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
  echo "The active workspace was not found in the workspace list." >&2
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
"$COS_CLI" ws-activate -g "$GROUP" -w "$TARGET"
echo "$GROUP $TARGET" > "$STATE_FILE"
EOS
chmod +x "$HOME/.local/bin/cosmic-ws"

say "Checking PATH configuration..."
mkdir -p "$HOME/.config"
if ! grep -q 'HOME/.cargo/bin' "$HOME/.bashrc" 2>/dev/null; then
  echo 'export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_DIR="$HOME/.local/share/magic-mouse-cosmic-workspaces"
mkdir -p "$RUNTIME_DIR" "$HOME/.local/bin" "$HOME/.local/share/applications"

say "Installing control panel scripts..."
cp "$SCRIPT_DIR/verify.sh" "$RUNTIME_DIR/verify.sh"
cp "$SCRIPT_DIR/repair-permissions.sh" "$RUNTIME_DIR/repair-permissions.sh"
cp "$SCRIPT_DIR/bin/magic-mouse-control-panel" "$HOME/.local/bin/magic-mouse-control-panel"
cp "$SCRIPT_DIR/bin/magic-mouse-control-panel-cli" "$HOME/.local/bin/magic-mouse-control-panel-cli"
cp "$SCRIPT_DIR/bin/magic-mouse-scroll-direction" "$HOME/.local/bin/magic-mouse-scroll-direction"
chmod +x "$RUNTIME_DIR/verify.sh" "$RUNTIME_DIR/repair-permissions.sh" \
  "$HOME/.local/bin/magic-mouse-control-panel" "$HOME/.local/bin/magic-mouse-control-panel-cli" \
  "$HOME/.local/bin/magic-mouse-scroll-direction"

say "Installing application icons..."
ICON_NAME="magic-mouse-control-panel"
mkdir -p "$HOME/.local/share/icons/hicolor/256x256/apps"
mkdir -p "$HOME/.local/share/icons/hicolor/scalable/apps"
if [[ -f "$SCRIPT_DIR/assets/${ICON_NAME}.png.b64" ]]; then
  base64 -d "$SCRIPT_DIR/assets/${ICON_NAME}.png.b64" > "$HOME/.local/share/icons/hicolor/256x256/apps/${ICON_NAME}.png"
fi
if [[ -f "$SCRIPT_DIR/assets/${ICON_NAME}.svg" ]]; then
  cp "$SCRIPT_DIR/assets/${ICON_NAME}.svg" "$HOME/.local/share/icons/hicolor/scalable/apps/${ICON_NAME}.svg"
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -q "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
fi
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
fi

cat > "$HOME/.local/share/applications/magic-mouse-control-panel.desktop" <<EOF2
[Desktop Entry]
Type=Application
Name=Magic Mouse Control Panel
Comment=Configure Magic Mouse gestures for COSMIC Wayland
Exec=$HOME/.local/bin/magic-mouse-control-panel
Icon=magic-mouse-control-panel
StartupWMClass=MagicMouseControlPanel
X-GNOME-WMClass=MagicMouseControlPanel
Terminal=false
Categories=Settings;Utility;
EOF2

cat > "$HOME/.local/share/applications/magic-mouse-control-panel-cli.desktop" <<EOF3
[Desktop Entry]
Type=Application
Name=Magic Mouse Control Panel (CLI)
Comment=Terminal control panel for Magic Mouse gestures
Exec=$HOME/.local/bin/magic-mouse-control-panel-cli
Icon=magic-mouse-control-panel
StartupWMClass=magic-mouse-control-panel-cli
X-GNOME-WMClass=magic-mouse-control-panel-cli
Terminal=true
Categories=Settings;Utility;
EOF3

say "Installing Magic Mouse Linux Gestures..."
cd "$MM_SOURCE"
./install.sh

if [[ ! -f "$PROFILE" ]]; then
  err "profile.env was not created: $PROFILE"
  exit 1
fi

say "Patching the installed gesture daemon for per-finger inversion..."
python3 - "$INSTALLED_DAEMON" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
if not path.exists():
    raise SystemExit(f"Installed daemon not found: {path}")

text = path.read_text()
if 'INVERT_X_1F' in text and 'invert_for_touches' in text:
    print(f"already patched: {path}")
    raise SystemExit(0)

old_init = '''        self.axis_lock_ratio = env_float(profile, "AXIS_LOCK_RATIO", 1.15)
        self.invert_x = env_int(profile, "INVERT_X", 0) == 1
        self.invert_y = env_int(profile, "INVERT_Y", 0) == 1

        self.active = False
        self.start_xy = (0.0, 0.0)
        self.last_xy = (0.0, 0.0)
        self.start_time = 0.0
        self.last_fire_time = 0.0
        self.max_seen_touches = 0
'''
new_init = '''        self.axis_lock_ratio = env_float(profile, "AXIS_LOCK_RATIO", 1.15)
        legacy_invert_x = env_int(profile, "INVERT_X", 0)
        legacy_invert_y = env_int(profile, "INVERT_Y", 0)
        self.invert_x_1f = env_int(profile, "INVERT_X_1F", legacy_invert_x) == 1
        self.invert_y_1f = env_int(profile, "INVERT_Y_1F", legacy_invert_y) == 1
        self.invert_x_2f = env_int(profile, "INVERT_X_2F", legacy_invert_x) == 1
        self.invert_y_2f = env_int(profile, "INVERT_Y_2F", legacy_invert_y) == 1

        self.active = False
        self.start_xy = (0.0, 0.0)
        self.last_xy = (0.0, 0.0)
        self.start_time = 0.0
        self.last_fire_time = 0.0
        self.start_touches = 0
        self.max_seen_touches = 0
'''
text2 = text.replace(old_init, new_init)
if text2 == text:
    raise SystemExit('failed to patch init block')
text = text2

old_reset = '''        self.last_xy = (0.0, 0.0)
        self.start_time = 0.0
        self.max_seen_touches = 0
        if not keep_release_guard:
'''
new_reset = '''        self.last_xy = (0.0, 0.0)
        self.start_time = 0.0
        self.start_touches = 0
        self.max_seen_touches = 0
        if not keep_release_guard:
'''
text2 = text.replace(old_reset, new_reset)
if text2 == text:
    raise SystemExit('failed to patch reset block')
text = text2

needle = '    def feed(self, touches: list[Touch]) -> str | None:\n'
if needle not in text:
    raise SystemExit('feed method not found')
insert = '''    def invert_for_touches(self, touches: int) -> tuple[bool, bool]:\n        if touches <= 1:\n            return self.invert_x_1f, self.invert_y_1f\n        return self.invert_x_2f, self.invert_y_2f\n\n'''
text = text.replace(needle, insert + needle, 1)

old_start = '''            self.start_xy = centroid(down)
            self.last_xy = self.start_xy
            self.start_time = now
            self.max_seen_touches = count
'''
new_start = '''            self.start_xy = centroid(down)
            self.last_xy = self.start_xy
            self.start_time = now
            self.start_touches = count
            self.max_seen_touches = count
'''
text2 = text.replace(old_start, new_start)
if text2 == text:
    raise SystemExit('failed to patch start block')
text = text2

old_invert = '''            dx = self.last_xy[0] - self.start_xy[0]
            dy = self.last_xy[1] - self.start_xy[1]
            if self.invert_x:
                dx = -dx
            if self.invert_y:
                dy = -dy

            if self.debug:
                print(
                    f"[gesture] touches={count} dx={dx:.1f} dy={dy:.1f} elapsed={elapsed:.3f}",
                    flush=True,
                )
'''
new_invert = '''            dx = self.last_xy[0] - self.start_xy[0]
            dy = self.last_xy[1] - self.start_xy[1]
            gesture_touches = max(self.start_touches, self.max_seen_touches, count)
            invert_x, invert_y = self.invert_for_touches(gesture_touches)
            if invert_x:
                dx = -dx
            if invert_y:
                dy = -dy

            if self.debug:
                print(
                    f"[gesture] touches={count} gesture_touches={gesture_touches} dx={dx:.1f} dy={dy:.1f} elapsed={elapsed:.3f}",
                    flush=True,
                )
'''
text2 = text.replace(old_invert, new_invert)
if text2 == text:
    raise SystemExit('failed to patch invert block')
text = text2

path.write_text(text)
print(f"patched: {path}")
PY

say "Updating profile.env..."
PROFILE_PATH="$PROFILE" python3 - <<'PY'
import os
from pathlib import Path

profile = Path(os.environ["PROFILE_PATH"])
home = Path.home()

updates = {
    "GESTURE_LEFT": "wtype -M alt -P left -p left -m alt",
    "GESTURE_RIGHT": "wtype -M alt -P right -p right -m alt",
    "GESTURE_UP": f"{home}/.local/bin/cosmic-ws up",
    "GESTURE_DOWN": f"{home}/.local/bin/cosmic-ws down",
    "GESTURE_OVERVIEW": "wtype -M logo -P w -p w -m logo",
    "MIN_TOUCHES": "2",
    "MAX_FINGERS": "5",
    "SWIPE_THRESHOLD_X": "360",
    "SWIPE_THRESHOLD_Y": "420",
    "MAX_GESTURE_TIME_MS": "900",
    "SWIPE_COOLDOWN_MS": "450",
    "AXIS_LOCK_RATIO": "1.15",
    "INVERT_X": "0",
    "INVERT_Y": "0",
    "INVERT_X_1F": "0",
    "INVERT_Y_1F": "0",
    "INVERT_X_2F": "0",
    "INVERT_Y_2F": "0",
    "COMMAND_TIMEOUT_SEC": "2.0",
    "WAIT_RELEASE_AFTER_FIRE": "1",
}

plain = {
    "MIN_TOUCHES", "MAX_FINGERS", "SWIPE_THRESHOLD_X", "SWIPE_THRESHOLD_Y",
    "MAX_GESTURE_TIME_MS", "SWIPE_COOLDOWN_MS", "AXIS_LOCK_RATIO",
    "INVERT_X", "INVERT_Y", "INVERT_X_1F", "INVERT_Y_1F", "INVERT_X_2F", "INVERT_Y_2F",
    "COMMAND_TIMEOUT_SEC", "WAIT_RELEASE_AFTER_FIRE",
}

lines = profile.read_text().splitlines()
out = []
seen = set()
for line in lines:
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or "=" not in line:
        out.append(line)
        continue
    key = line.split("=", 1)[0].strip()
    if key in updates:
        val = updates[key]
        out.append(f"{key}={val}" if key in plain else f'{key}="{val}"')
        seen.add(key)
    else:
        out.append(line)
for key, val in updates.items():
    if key not in seen:
        out.append(f"{key}={val}" if key in plain else f'{key}="{val}"')
profile.write_text("\n".join(out) + "\n")
PY

say "Starting the service..."
systemctl --user daemon-reload
systemctl --user enable --now magic-mouse-gestures
systemctl --user restart magic-mouse-gestures

say "Fixing HID/udev permissions..."
if [[ -x "$SCRIPT_DIR/repair-permissions.sh" ]]; then
  MM_SOURCE="$MM_SOURCE" "$SCRIPT_DIR/repair-permissions.sh" || warn "Automatic permission repair did not complete. Reconnect the mouse and run ./repair-permissions.sh."
else
  warn "repair-permissions.sh was not found; if needed, use sudo setfacl -m u:$USER:rw /dev/hidrawX."
fi

say "Install complete."
echo
echo "Launch the GUI control panel:"
echo "  magic-mouse-control-panel"
echo
echo "Launch the terminal control panel:"
echo "  magic-mouse-control-panel-cli"
echo "Scroll direction helper:"
echo "  magic-mouse-scroll-direction status"
echo
echo "Test commands:"
echo "  ~/.local/bin/cosmic-ws down"
echo "  ~/.local/bin/cosmic-ws up"
echo
echo "Service/log:"
echo "  systemctl --user status magic-mouse-gestures"
echo "  journalctl --user -u magic-mouse-gestures -f"
echo
echo "If permissions fail:"
echo "  ./repair-permissions.sh"
