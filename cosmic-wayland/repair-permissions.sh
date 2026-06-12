#!/usr/bin/env bash
set -euo pipefail

VERSION="1.4.3"
DEFAULT_MM_SOURCE="$HOME/Desktop/magicmouse/magic-mouse-linux-gestures-v0.6/magic-mouse-linux-gestures"
MM_SOURCE="${MM_SOURCE:-$DEFAULT_MM_SOURCE}"
PROFILE="$HOME/.config/magic-mouse-gestures/profile.env"

say() { printf '\033[1;36m[repair v%s]\033[0m %s\n' "$VERSION" "$*"; }
warn() { printf '\033[1;33m[warn]\033[0m %s\n' "$*"; }

sudox() {
  if [[ -n "${MM_SUDO_PASSWORD:-}" ]]; then
    printf '%s\n' "$MM_SUDO_PASSWORD" | sudo -S -p "" "$@"
  else
    sudo "$@"
  fi
}

if [[ "$EUID" -eq 0 ]]; then
  echo "Do not run this script with sudo; it will ask for sudo only when needed." >&2
  exit 1
fi

install_local_udev_rule() {
  say "Installing local udev rule: /etc/udev/rules.d/99-magic-mouse-gestures-local.rules"
  tmp_rule="$(mktemp)"
  cat > "$tmp_rule" <<'RULES'
# magic-mouse-cosmic-workspaces v1.4.3
# Apple Magic Mouse / Apple HID raw access for the active local user.
# TAG+="uaccess" lets logind grant ACLs to the user in the graphical session.
SUBSYSTEM=="hidraw", KERNEL=="hidraw*", ATTRS{idVendor}=="05ac", TAG+="uaccess", MODE="0660"
SUBSYSTEM=="hidraw", KERNEL=="hidraw*", ENV{ID_VENDOR_ID}=="05ac", TAG+="uaccess", MODE="0660"
RULES
  sudox install -m 0644 "$tmp_rule" /etc/udev/rules.d/99-magic-mouse-gestures-local.rules
  rm -f "$tmp_rule"
  sudox udevadm control --reload-rules || true
  sudox udevadm trigger || true
}

run_upstream_helpers() {
  if [[ -n "${MM_SUDO_PASSWORD:-}" ]]; then
    say "GUI sudo mode detected; skipping upstream helper scripts that may require a terminal."
    return 0
  fi

  if [[ -d "$MM_SOURCE" ]]; then
    cd "$MM_SOURCE"
    if [[ -x ./install.sh ]]; then
      say "Trying upstream udev install: ./install.sh --udev"
      ./install.sh --udev || warn "./install.sh --udev failed; the local udev rule will be used."
    fi
    if [[ -x ./scripts/fix-permissions-now.sh ]]; then
      say "Running upstream immediate permission fix."
      ./scripts/fix-permissions-now.sh || warn "scripts/fix-permissions-now.sh failed; continuing with setfacl."
    fi
  else
    warn "Magic Mouse source directory was not found: $MM_SOURCE"
  fi
}

profile_hid_path() {
  [[ -f "$PROFILE" ]] || return 0
  awk -F= '/^HID_PATH=/{v=$2; gsub(/^"|"$/, "", v); print v}' "$PROFILE" | tail -n1
}

journal_hid_path() {
  journalctl --user -u magic-mouse-gestures -n 80 -o cat 2>/dev/null \
    | sed -n "s/.*\(\/dev\/hidraw[0-9][0-9]*\).*/\1/p" \
    | tail -n1
}

detect_apple_hidraw() {
  local dev props
  for dev in /dev/hidraw*; do
    [[ -e "$dev" ]] || continue
    props="$(udevadm info -q property -n "$dev" 2>/dev/null || true)"
    if grep -qiE 'ID_VENDOR_ID=05ac|HID_ID=.*000005AC|HID_NAME=.*Magic|HID_NAME=.*MaGiK' <<< "$props"; then
      printf '%s\n' "$dev"
    fi
  done
}

apply_acl() {
  local dev="$1"
  [[ -n "$dev" && -e "$dev" ]] || return 1
  say "Applying immediate ACL: $dev -> $USER rw"
  sudox setfacl -m "u:${USER}:rw" "$dev" || return 1
}

say "Checking the acl package..."
sudox apt install -y acl >/dev/null

install_local_udev_rule
run_upstream_helpers

# When the mouse reconnects, log/profile paths can change. Try known paths first, then Apple hidraw devices.
CANDIDATES=()
while IFS= read -r p; do [[ -n "$p" ]] && CANDIDATES+=("$p"); done < <(profile_hid_path || true)
while IFS= read -r p; do [[ -n "$p" ]] && CANDIDATES+=("$p"); done < <(journal_hid_path || true)
while IFS= read -r p; do [[ -n "$p" ]] && CANDIDATES+=("$p"); done < <(detect_apple_hidraw || true)

# uniq
UNIQ=()
for p in "${CANDIDATES[@]:-}"; do
  skip=0
  for q in "${UNIQ[@]:-}"; do [[ "$p" == "$q" ]] && skip=1; done
  [[ "$skip" == 0 ]] && UNIQ+=("$p")
done

if [[ "${#UNIQ[@]}" -eq 0 ]]; then
  warn "Apple/Magic Mouse hidraw path was not found. Power-cycle or reconnect the mouse, then run this script again."
else
  for p in "${UNIQ[@]}"; do
    apply_acl "$p" || warn "Could not apply ACL: $p"
  done
fi

say "Restarting magic-mouse-gestures..."
systemctl --user restart magic-mouse-gestures 2>/dev/null || true

say "Recent log:"
journalctl --user -u magic-mouse-gestures -n 20 -l --no-pager 2>/dev/null || true
