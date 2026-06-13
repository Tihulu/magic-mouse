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
        style.configure("Mode.TLabel", background=bg, foreground=text, font=("SF Pro Display", 11, "bold"))
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

SENSITIVITY_BLOCK = '''SENSITIVITY_PRESETS = {
    "Default": {"SWIPE_THRESHOLD_X": "360", "SWIPE_THRESHOLD_Y": "420", "SWIPE_COOLDOWN_MS": "450", "AXIS_LOCK_RATIO": "1.15"},
    "Tihulu": {"SWIPE_THRESHOLD_X": "550", "SWIPE_THRESHOLD_Y": "480", "SWIPE_COOLDOWN_MS": "550", "AXIS_LOCK_RATIO": "1.35"},
    "Sensitive": {"SWIPE_THRESHOLD_X": "280", "SWIPE_THRESHOLD_Y": "340", "SWIPE_COOLDOWN_MS": "380", "AXIS_LOCK_RATIO": "1.10"},
    "Relaxed": {"SWIPE_THRESHOLD_X": "460", "SWIPE_THRESHOLD_Y": "520", "SWIPE_COOLDOWN_MS": "550", "AXIS_LOCK_RATIO": "1.20"},
    "Very Relaxed": {"SWIPE_THRESHOLD_X": "720", "SWIPE_THRESHOLD_Y": "820", "SWIPE_COOLDOWN_MS": "900", "AXIS_LOCK_RATIO": "1.35"},
    "Custom": {},
}
'''

CUSTOM_VARS = '''        self.custom_x_var = tk.StringVar(value="550")
        self.custom_y_var = tk.StringVar(value="480")
        self.custom_cooldown_var = tk.StringVar(value="550")
        self.custom_axis_var = tk.StringVar(value="1.35")
'''

CUSTOM_UI = '''
        custom = ttk.LabelFrame(setup, text="Custom sensitivity", padding=8)
        custom.grid(row=9, column=0, columnspan=3, padx=4, pady=(10, 4), sticky="ew")
        for col in range(4):
            custom.columnconfigure(col, weight=1)
        for col, (label, var) in enumerate((
            ("X threshold", self.custom_x_var),
            ("Y threshold", self.custom_y_var),
            ("Cooldown ms", self.custom_cooldown_var),
            ("Axis lock", self.custom_axis_var),
        )):
            ttk.Label(custom, text=label).grid(row=0, column=col, sticky="w", padx=4)
            ttk.Entry(custom, textvariable=var, width=10).grid(row=1, column=col, sticky="ew", padx=4, pady=(3, 0))
        ttk.Button(setup, text="Apply Custom Sensitivity", command=self.apply_custom_sensitivity).grid(row=10, column=0, columnspan=3, padx=4, pady=4, sticky="ew")
'''

CUSTOM_METHODS = '''
    def custom_sensitivity_values(self):
        raw = {
            "SWIPE_THRESHOLD_X": self.custom_x_var.get().strip(),
            "SWIPE_THRESHOLD_Y": self.custom_y_var.get().strip(),
            "SWIPE_COOLDOWN_MS": self.custom_cooldown_var.get().strip(),
            "AXIS_LOCK_RATIO": self.custom_axis_var.get().strip(),
        }
        try:
            x = int(raw["SWIPE_THRESHOLD_X"])
            y = int(raw["SWIPE_THRESHOLD_Y"])
            cooldown = int(raw["SWIPE_COOLDOWN_MS"])
            axis = float(raw["AXIS_LOCK_RATIO"])
        except ValueError:
            raise ValueError("Custom sensitivity values must be numeric.")
        if x < 120 or y < 120 or cooldown < 100:
            raise ValueError("Custom X/Y thresholds and cooldown are too low.")
        if axis < 1.0 or axis > 3.0:
            raise ValueError("Axis lock should be between 1.0 and 3.0.")
        return {
            "SWIPE_THRESHOLD_X": str(x),
            "SWIPE_THRESHOLD_Y": str(y),
            "SWIPE_COOLDOWN_MS": str(cooldown),
            "AXIS_LOCK_RATIO": f"{axis:.2f}",
        }

    def apply_custom_sensitivity(self):
        try:
            values = self.custom_sensitivity_values()
        except ValueError as exc:
            messagebox.showerror("Custom sensitivity", str(exc))
            return
        self.apply_mapping(values, "Applied custom sensitivity and restarted the gesture service.")

'''


def add_custom_vars(text: str) -> str:
    if 'self.custom_x_var' in text:
        return text
    needle = '        self.sensitivity_var = tk.StringVar(value="Default")\n'
    return text.replace(needle, needle + CUSTOM_VARS, 1)


def add_custom_ui(text: str) -> str:
    if 'Apply Custom Sensitivity' in text:
        return text
    needle = '        ttk.Button(setup, text="Refresh Status", command=self.refresh_status_async).grid(row=8, column=2, padx=4, pady=4, sticky="ew")\n'
    return text.replace(needle, needle + CUSTOM_UI, 1)


def add_custom_methods(text: str) -> str:
    if 'def apply_custom_sensitivity' in text:
        return text
    marker = '    def apply_sensitivity(self):\n'
    return text.replace(marker, CUSTOM_METHODS + marker, 1)


def update_apply_sensitivity(text: str) -> str:
    old = '''    def apply_sensitivity(self):
        preset = self.sensitivity_var.get()
        values = SENSITIVITY_PRESETS.get(preset)
        if not values:
            messagebox.showerror("Sensitivity", "Choose a valid preset.")
            return
        self.apply_mapping(values, f"Applied the '{preset}' preset and restarted the gesture service.")
'''
    new = '''    def apply_sensitivity(self):
        preset = self.sensitivity_var.get()
        if preset == "Custom":
            self.apply_custom_sensitivity()
            return
        values = SENSITIVITY_PRESETS.get(preset)
        if not values:
            messagebox.showerror("Sensitivity", "Choose a valid preset.")
            return
        self.apply_mapping(values, f"Applied the '{preset}' preset and restarted the gesture service.")
'''
    return text.replace(old, new, 1)


def patch(path: Path) -> None:
    text = path.read_text()
    text = re.sub(r'VERSION = "[^"]+"', 'VERSION = "1.5.0-modern"', text, count=1)
    text = text.replace('self.root.title(f"Magic Mouse Control Panel v{VERSION}")', 'self.root.title(f"Magic Mouse Control Panel {VERSION}")')
    text = text.replace('self.root.geometry("920x680")', 'self.root.geometry("960x700")')
    text = text.replace('self.root.minsize(760, 520)', 'self.root.minsize(820, 560)')
    text = text.replace('self.status_var = tk.StringVar(value="Loading...")', 'self.status_var = tk.StringVar(value="Checking status…")')
    text = text.replace('ttk.Label(header, text=f"Magic Mouse Control Panel v{VERSION}", font=("Sans", 16, "bold"))', 'ttk.Label(header, text="Magic Mouse", style="Title.TLabel")')
    text = text.replace('ttk.Label(header, textvariable=self.session_var)', 'ttk.Label(header, textvariable=self.session_var, style="Muted.TLabel")')
    text = text.replace('ttk.Label(header, textvariable=self.mode_var)', 'ttk.Label(header, textvariable=self.mode_var, style="Mode.TLabel")')
    text = text.replace('ttk.Label(header, textvariable=self.status_var)', 'ttk.Label(header, textvariable=self.status_var, style="Muted.TLabel")')
    text = text.replace('ttk.Button(setup, text="Apply Stable Defaults", command=self.apply_stable_defaults)', 'ttk.Button(setup, text="Apply Stable Defaults", command=self.apply_stable_defaults, style="Accent.TButton")')

    start = text.find('SENSITIVITY_PRESETS = {')
    if start != -1:
        end = text.find('\n}\n', start)
        if end != -1:
            end += len('\n}\n')
            text = text[:start] + SENSITIVITY_BLOCK + text[end:]

    text = add_custom_vars(text)
    text = add_custom_ui(text)
    text = add_custom_methods(text)
    text = update_apply_sensitivity(text)

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
