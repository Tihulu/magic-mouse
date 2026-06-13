#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

EXAMPLE = "Example / default custom: X 550 · Y 480 · Cooldown 550 ms · Axis lock 1.35"


def patch(path: Path) -> None:
    text = path.read_text()
    text = text.replace(
        "messagebox.showinfo('Busy','Another action is already running.')",
        "messagebox.showinfo('Action already running','Another action is already running. Please wait for it to finish.')",
    )
    if EXAMPLE not in text:
        old = "self.button(sp,\"Apply Custom Sensitivity\",self.apply_custom,row=5,column=0,columnspan=4,padx=4,pady=(8,0),sticky='ew')"
        new = "self.label(sp,\"" + EXAMPLE + "\",size=9,color=C['muted'],row=5,column=0,columnspan=4,sticky='w',padx=4,pady=(8,0)); " + \
              "self.button(sp,\"Apply Custom Sensitivity\",self.apply_custom,row=6,column=0,columnspan=4,padx=4,pady=(8,0),sticky='ew')"
        text = text.replace(old, new, 1)
    path.write_text(text)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: patch-modern-panel-v1.5.1.py /path/to/magic-mouse-control-panel", file=sys.stderr)
        return 2
    target = Path(sys.argv[1]).expanduser()
    if not target.exists():
        print(f"control panel not found: {target}", file=sys.stderr)
        return 1
    patch(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
