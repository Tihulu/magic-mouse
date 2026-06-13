#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


def patch(path: Path) -> None:
    text = path.read_text()

    if "self.mode_var =" not in text:
        text = text.replace(
            '        self.session_var = tk.StringVar(value=f"Session: {os.getenv(\'XDG_SESSION_TYPE\', \'unknown\')} / {os.getenv(\'XDG_CURRENT_DESKTOP\', \'unknown\')}")\n',
            '        self.session_var = tk.StringVar(value=f"Session: {os.getenv(\'XDG_SESSION_TYPE\', \'unknown\')} / {os.getenv(\'XDG_CURRENT_DESKTOP\', \'unknown\')}")\n'
            '        self.mode_var = tk.StringVar(value="Mode: checking…")\n',
            1,
        )

    old_header = (
        '        ttk.Label(header, textvariable=self.session_var).grid(row=1, column=0, sticky="w", pady=(4, 0))\n'
        '        ttk.Label(header, textvariable=self.status_var).grid(row=2, column=0, sticky="w", pady=(4, 0))\n'
    )
    new_header = (
        '        ttk.Label(header, textvariable=self.session_var).grid(row=1, column=0, sticky="w", pady=(4, 0))\n'
        '        ttk.Label(header, textvariable=self.mode_var).grid(row=2, column=0, sticky="w", pady=(4, 0))\n'
        '        ttk.Label(header, textvariable=self.status_var).grid(row=3, column=0, sticky="w", pady=(4, 0))\n'
    )
    text = text.replace(old_header, new_header, 1)

    start = text.find('    def mapping_status(self, data):\n')
    end = text.find('    def permission_status(self):\n', start)
    if start != -1 and end != -1:
        replacement = '''    def mapping_status(self, data):
        up = data.get("GESTURE_UP", "")
        down = data.get("GESTURE_DOWN", "")
        left = data.get("GESTURE_LEFT", "")
        right = data.get("GESTURE_RIGHT", "")

        if up.endswith(" up") and down.endswith(" down"):
            ws = "Workspace: Normal"
        elif up.endswith(" down") and down.endswith(" up"):
            ws = "Workspace: Inverted"
        elif up == "true" and down == "true":
            ws = "Workspace: Disabled"
        else:
            ws = "Workspace: Custom"

        if "left" in left and "right" in right:
            browser = "Browser: Normal"
        elif "right" in left and "left" in right:
            browser = "Browser: Inverted"
        else:
            browser = "Browser: Custom"

        return f"{ws} · {browser}"

'''
        text = text[:start] + replacement + text[end:]

    old_apply = '    def apply_mapping(self, values, msg):\n        self.run_background(\n'
    new_apply = '''    def apply_mapping(self, values, msg):
        try:
            preview = read_profile()
            preview.update(values)
            self.mode_var.set(f"Mode: {self.mapping_status(preview)}")
        except Exception:
            self.mode_var.set("Mode: applying changes…")
        self.run_background(
'''
    if old_apply in text and 'preview.update(values)' not in text:
        text = text.replace(old_apply, new_apply, 1)

    text = text.replace(
        'self.status_var.set(f"Service: {state} | Mapping: {mapping} | HID: {hid} | Scroll: {scroll}")',
        'self.mode_var.set(f"Mode: {mapping}")\n                    self.status_var.set(f"Service: {state} | HID: {hid} | Scroll: {scroll}")',
        1,
    )

    path.write_text(text)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: patch-mode-indicator-v1.4.8.py /path/to/magic-mouse-control-panel", file=sys.stderr)
        return 2
    target = Path(sys.argv[1]).expanduser()
    if not target.exists():
        print(f"control panel not found: {target}", file=sys.stderr)
        return 1
    patch(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
