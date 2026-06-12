#!/usr/bin/env bash
set -euo pipefail

VERSION="1.4.5"
REPO="Tihulu/magic-mouse"
BRANCH="main"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

say() { printf '\033[1;32m[cosmic quick install v%s]\033[0m %s\n' "$VERSION" "$*"; }
warn() { printf '\033[1;33m[warn]\033[0m %s\n' "$*"; }

archive="$TMP/magic-mouse.tar.gz"
url="https://github.com/${REPO}/archive/refs/heads/${BRANCH}.tar.gz"

say "Downloading ${REPO}/${BRANCH}..."
if command -v curl >/dev/null 2>&1; then
  curl -fsSL "$url" -o "$archive"
elif command -v wget >/dev/null 2>&1; then
  wget -qO "$archive" "$url"
else
  echo "curl or wget is required." >&2
  exit 1
fi

tar -xzf "$archive" -C "$TMP"
cd "$TMP/magic-mouse-${BRANCH}/cosmic-wayland"
chmod +x *.sh bin/* 2>/dev/null || true

say "Running COSMIC Wayland installer..."
./install.sh "$@"

say "Applying v1.4.5 fast startup and dock icon fixes..."
control_panel="$HOME/.local/bin/magic-mouse-control-panel"
if [[ -f "$control_panel" ]]; then
  python3 - "$control_panel" <<'PY'
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
text = path.read_text()
text = re.sub(r'VERSION = "[^"]+"', 'VERSION = "1.4.5"', text, count=1)

old_init = '''        self._build_ui()
        self.load_profile_to_ui()
        self.refresh_status()

    def _build_ui(self):
'''
new_init = '''        self._build_ui()
        self.load_profile_to_ui(refresh_info=False)
        self.status_var.set("Service status: loading...")
        for var in self.setup_status_vars.values():
            var.set("Loading")
        self.root.after(150, self.refresh_status_async)

    def _build_ui(self):
'''
text = text.replace(old_init, new_init)

text = text.replace('    def load_profile_to_ui(self):\n', '    def load_profile_to_ui(self, refresh_info=True):\n')
text = text.replace('        self.sensitivity_var.set(self.detect_sensitivity_name(data))\n        self.refresh_info_text()\n\n    def load_defaults(self):\n', '        self.sensitivity_var.set(self.detect_sensitivity_name(data))\n        if refresh_info:\n            self.refresh_info_text()\n\n    def load_defaults(self):\n', 1)

if 'def refresh_status_async' not in text:
    needle = '    def refresh_status(self):\n        result = run_command(["systemctl", "--user", "is-active", "magic-mouse-gestures"])\n'
    async_methods = '''    def refresh_status_async(self):
        if getattr(self, "_refresh_status_running", False):
            return
        self._refresh_status_running = True
        threading.Thread(target=self._refresh_status_worker, daemon=True).start()

    def _refresh_status_worker(self):
        try:
            result = run_command(["systemctl", "--user", "is-active", "magic-mouse-gestures"])
            state = (result.stdout or "unknown").strip() or "unknown"
            data = read_profile()
            permission = self.permission_status()
            scroll = self.scroll_status()
            mapping = self.mapping_status(data)
            sensitivity = self.detect_sensitivity_name(data)

            info_lines = []
            service = run_command(["systemctl", "--user", "status", "magic-mouse-gestures", "-l", "--no-pager"])
            info_lines.append("== Service ==\\n" + (service.stdout or service.stderr or "Unavailable"))
            if PROFILE.exists():
                info_lines.append("\\n== Profile ==\\n" + PROFILE.read_text())
            else:
                info_lines.append(f"\\n== Profile ==\\nMissing: {PROFILE}\\n")
            state_file = Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp")) / "magic-mouse-cosmic-ws.state"
            if state_file.exists():
                info_lines.append("\\n== cosmic-ws state ==\\n" + state_file.read_text())
            else:
                info_lines.append(f"\\n== cosmic-ws state ==\\nNo state file yet: {state_file}\\n")
            info_text = "\\n".join(info_lines)

            def apply():
                self.status_var.set(f"Service status: {state} | Mapping: {mapping} | HID: {permission} | Scroll: {scroll}")
                self.setup_status_vars["1"].set("Ready" if PROFILE.exists() else "Profile not found")
                self.setup_status_vars["2"].set(f"Service is {state}")
                self.setup_status_vars["3"].set(permission)
                self.setup_status_vars["4"].set(sensitivity)
                self.setup_status_vars["5"].set(scroll)
                self.setup_status_vars["6"].set(mapping)
                self.info_text.configure(state="normal")
                self.info_text.delete("1.0", "end")
                self.info_text.insert("1.0", info_text)
                self.info_text.configure(state="disabled")
                self._refresh_status_running = False

            self.root.after(0, apply)
        except Exception as exc:
            def fail():
                self.status_var.set(f"Status check failed: {exc}")
                self._refresh_status_running = False
            self.root.after(0, fail)

'''
    text = text.replace(needle, async_methods + needle)

path.write_text(text)
PY
  python3 -m py_compile "$control_panel" || warn "Control panel fast-start patch was applied but py_compile failed."
else
  warn "Control panel was not found: $control_panel"
fi

desktop_file="$HOME/.local/share/applications/magic-mouse-control-panel.desktop"
if [[ -f "$desktop_file" ]]; then
  sed -i 's/^StartupWMClass=.*/StartupWMClass=Tk/' "$desktop_file"
  sed -i 's/^X-GNOME-WMClass=.*/X-GNOME-WMClass=Tk/' "$desktop_file"
  if ! grep -q '^StartupNotify=' "$desktop_file"; then
    printf '%s\n' 'StartupNotify=true' >> "$desktop_file"
  fi
else
  warn "Desktop launcher was not found: $desktop_file"
fi

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -q "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
fi

say "Done. Launch with: gtk-launch magic-mouse-control-panel"
say "The window should appear first; status checks load in the background."
