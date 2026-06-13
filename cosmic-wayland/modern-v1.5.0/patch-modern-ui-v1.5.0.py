#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

MODERN_STYLE = '''    def _apply_modern_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        bg = "#f5f5f7"
        card = "#ffffff"
        text = "#1d1d1f"
        muted = "#6e6e73"
        accent = "#007aff"
        self.root.configure(bg=bg)
        style.configure("TFrame", background=bg)
        style.configure("TLabel", background=bg, foreground=text, font=("SF Pro Display", 10))
        style.configure("Title.TLabel", background=bg, foreground=text, font=("SF Pro Display", 22, "bold"))
        style.configure("Muted.TLabel", background=bg, foreground=muted, font=("SF Pro Display", 10))
        style.configure("TLabelframe", background=card, borderwidth=1, relief="solid")
        style.configure("TLabelframe.Label", background=card, foreground=text, font=("SF Pro Display", 12, "bold"))
        style.configure("TNotebook", background=bg, borderwidth=0)
        style.configure("TNotebook.Tab", padding=(14, 7), background="#ececf1", foreground=text)
        style.map("TNotebook.Tab", background=[("selected", card), ("active", "#ffffff")])
        style.configure("TButton", padding=(14, 8), background="#ffffff", foreground=text, borderwidth=1, focusthickness=0)
        style.map("TButton", background=[("active", "#f2f2f7"), ("pressed", "#e5e5ea")])
        style.configure("Accent.TButton", padding=(14, 8), background=accent, foreground="#ffffff", borderwidth=0, focusthickness=0)
        style.map("Accent.TButton", background=[("active", "#0063cc"), ("pressed", "#0063cc")])
        style.configure("TProgressbar", troughcolor="#e5e5ea", background=accent, borderwidth=0)

'''


def patch(path: Path) -> None:
    text = path.read_text()
    text = re.sub(r'VERSION = "[^"]+"', 'VERSION = "1.5.0-modern"', text, count=1)
    text = text.replace('self.root.title(f"Magic Mouse Control Panel v{VERSION}")', 'self.root.title(f"Magic Mouse Control Panel {VERSION}")')
    text = text.replace('self.root.geometry("920x680")', 'self.root.geometry("960x700")')
    text = text.replace('self.root.minsize(760, 520)', 'self.root.minsize(820, 560)')
    text = text.replace('self.status_var = tk.StringVar(value="Loading...")', 'self.status_var = tk.StringVar(value="Checking status…")')
    text = text.replace('ttk.Label(header, text=f"Magic Mouse Control Panel v{VERSION}", font=("Sans", 16, "bold"))', 'ttk.Label(header, text="Magic Mouse", style="Title.TLabel")')
    text = text.replace('ttk.Label(header, textvariable=self.session_var)', 'ttk.Label(header, textvariable=self.session_var, style="Muted.TLabel")')
    text = text.replace('ttk.Label(header, textvariable=self.status_var)', 'ttk.Label(header, textvariable=self.status_var, style="Muted.TLabel")')
    text = text.replace('ttk.Button(setup, text="Apply Stable Defaults", command=self.apply_stable_defaults)', 'ttk.Button(setup, text="Apply Stable Defaults", command=self.apply_stable_defaults, style="Accent.TButton")')

    if 'def _apply_modern_style' not in text:
        marker = '    def _build_ui(self):\n'
        text = text.replace(marker, MODERN_STYLE + marker + '        self._apply_modern_style()\n', 1)

    path.write_text(text)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: patch-modern-ui-v1.5.0.py /path/to/magic-mouse-control-panel", file=sys.stderr)
        return 2
    target = Path(sys.argv[1]).expanduser()
    if not target.exists():
        print(f"control panel not found: {target}", file=sys.stderr)
        return 1
    patch(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
