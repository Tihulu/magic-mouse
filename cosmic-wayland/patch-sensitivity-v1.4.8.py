#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

NEW_BLOCK = '''SENSITIVITY_PRESETS = {
    "Default": {"SWIPE_THRESHOLD_X": "360", "SWIPE_THRESHOLD_Y": "420", "SWIPE_COOLDOWN_MS": "450", "AXIS_LOCK_RATIO": "1.15"},
    "Sensitive": {"SWIPE_THRESHOLD_X": "280", "SWIPE_THRESHOLD_Y": "340", "SWIPE_COOLDOWN_MS": "380", "AXIS_LOCK_RATIO": "1.10"},
    "Relaxed": {"SWIPE_THRESHOLD_X": "560", "SWIPE_THRESHOLD_Y": "640", "SWIPE_COOLDOWN_MS": "700", "AXIS_LOCK_RATIO": "1.25"},
    "Very Relaxed": {"SWIPE_THRESHOLD_X": "720", "SWIPE_THRESHOLD_Y": "820", "SWIPE_COOLDOWN_MS": "900", "AXIS_LOCK_RATIO": "1.35"},
}
'''


def patch(path: Path) -> None:
    text = path.read_text()
    start = text.find('SENSITIVITY_PRESETS = {')
    if start == -1:
        raise RuntimeError('SENSITIVITY_PRESETS block was not found')
    end = text.find('\n}\n', start)
    if end == -1:
        raise RuntimeError('end of SENSITIVITY_PRESETS block was not found')
    end += len('\n}\n')
    text = text[:start] + NEW_BLOCK + text[end:]
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
