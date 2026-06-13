#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

NEW_BLOCK = '''SENSITIVITY_PRESETS = {
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
        ttk.Label(custom, text="Example / default custom: X 550 · Y 480 · Cooldown 550 ms · Axis lock 1.35").grid(row=2, column=0, columnspan=4, sticky="w", padx=4, pady=(8, 0))
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


def replace_presets(text: str) -> str:
    start = text.find('SENSITIVITY_PRESETS = {')
    if start == -1:
        raise RuntimeError('SENSITIVITY_PRESETS block was not found')
    end = text.find('\n}\n', start)
    if end == -1:
        raise RuntimeError('end of SENSITIVITY_PRESETS block was not found')
    end += len('\n}\n')
    return text[:start] + NEW_BLOCK + text[end:]


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


def add_custom_example(text: str) -> str:
    if 'Example / default custom: X 550' in text:
        return text
    needle = '            ttk.Entry(custom, textvariable=var, width=10).grid(row=1, column=col, sticky="ew", padx=4, pady=(3, 0))\n'
    extra = '        ttk.Label(custom, text="Example / default custom: X 550 · Y 480 · Cooldown 550 ms · Axis lock 1.35").grid(row=2, column=0, columnspan=4, sticky="w", padx=4, pady=(8, 0))\n'
    return text.replace(needle, needle + extra, 1)


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


def update_busy_notice(text: str) -> str:
    text = text.replace(
        'messagebox.showinfo("Busy", "Another action is already running. Please wait.")',
        'messagebox.showinfo("Action already running", "Another action is already running. Please wait for it to finish.")',
    )
    text = text.replace(
        "messagebox.showinfo('Busy','Another action is already running.')",
        "messagebox.showinfo('Action already running','Another action is already running. Please wait for it to finish.')",
    )
    return text


def patch(path: Path) -> None:
    text = path.read_text()
    text = replace_presets(text)
    text = add_custom_vars(text)
    text = add_custom_ui(text)
    text = add_custom_example(text)
    text = add_custom_methods(text)
    text = update_apply_sensitivity(text)
    text = update_busy_notice(text)
    path.write_text(text)


def main() -> int:
    if len(sys.argv) != 2:
        print('usage: patch-sensitivity-v1.4.8.py /path/to/magic-mouse-control-panel', file=sys.stderr)
        return 2
    target = Path(sys.argv[1]).expanduser()
    if not target.exists():
        print(f'control panel not found: {target}', file=sys.stderr)
        return 1
    patch(target)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
