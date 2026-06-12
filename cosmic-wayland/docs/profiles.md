# Profiles

Profiles are simple `.env` files. The daemon reads gesture commands and tuning values from a selected profile.

## Included profiles

- `profiles/cosmic.env` — COSMIC / Pop!_OS 24.04 style shortcuts
- `profiles/gnome-ubuntu.env` — GNOME/Ubuntu style shortcuts

## Commands

Each gesture maps to a shell-style command string:

```env
GESTURE_LEFT="wtype -M alt -P left -p left -m alt"
GESTURE_RIGHT="wtype -M alt -P right -p right -m alt"
GESTURE_UP="wtype -M ctrl -M alt -P up -p up -m alt -m ctrl"
GESTURE_DOWN="wtype -M ctrl -M alt -P down -p down -m alt -m ctrl"
```

## Tuning

```env
MIN_TOUCHES=2
SWIPE_THRESHOLD_X=360
SWIPE_THRESHOLD_Y=420
MAX_GESTURE_TIME_MS=900
SWIPE_COOLDOWN_MS=450
AXIS_LOCK_RATIO=1.15
INVERT_X=0
INVERT_Y=0
COMMAND_TIMEOUT_SEC=2.0
```

Use higher thresholds if gestures fire accidentally. Use lower thresholds if gestures rarely fire.

`AXIS_LOCK_RATIO` prevents diagonal movement from being misread as a swipe. Higher values require a cleaner horizontal or vertical gesture.

`INVERT_X` and `INVERT_Y` reverse gesture direction after parsing. Use these when a device reports coordinates differently.
