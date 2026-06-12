# Magic Mouse Linux Gestures

Magic Mouse gesture support for Linux desktops: **COSMIC** and **GNOME/Ubuntu** profiles.

This project adds configurable swipe gestures for Apple Magic Mouse on Linux. It uses a small Python daemon that reads Magic Mouse HID reports and sends desktop shortcuts through `wtype` on Wayland.

> Status: v1.1.0. The project includes install scripts, a systemd user service, COSMIC and GNOME/Ubuntu profiles, device selection, JSONL calibration logging, a graphical control panel, and basic tests. Real-device tuning may still be needed because Magic Mouse firmware/kernel behavior can vary by model, connection mode, and distribution.

## Supported profiles

### COSMIC

For Pop!_OS 24.04 and other COSMIC desktop environments.

Default mappings:

| Gesture | Action |
|---|---|
| Two-finger swipe left | Browser back |
| Two-finger swipe right | Browser forward |
| Two-finger swipe up | Previous/up workspace |
| Two-finger swipe down | Next/down workspace |

### GNOME/Ubuntu

For Ubuntu, Pop!_OS 22.04, Fedora Workstation, Debian GNOME, and other GNOME-based desktops.

Default mappings:

| Gesture | Action |
|---|---|
| Two-finger swipe left | Browser back |
| Two-finger swipe right | Browser forward |
| Two-finger swipe up | Previous workspace |
| Two-finger swipe down | Next workspace |

## Requirements

- Linux desktop using Wayland
- Apple Magic Mouse or Magic Mouse 2
- `hid_magicmouse` kernel driver available
- `wtype` for sending shortcuts on Wayland
- Python 3.10+
- Permission to read the Magic Mouse hidraw device

## Install

COSMIC:

```bash
./install.sh --profile cosmic --udev --start
```

GNOME/Ubuntu:

```bash
./install.sh --profile gnome-ubuntu --udev --start
```

Auto-detect profile:

```bash
./install.sh --profile auto --udev --start
```

View logs:

```bash
journalctl --user -u magic-mouse-gestures.service -f
```

Stop/start:

```bash
systemctl --user stop magic-mouse-gestures.service
systemctl --user start magic-mouse-gestures.service
```

## Control panel

After installation, launch the graphical settings tool:

```bash
magic-mouse-control-panel
```

The control panel lets you:

- switch between COSMIC and GNOME/Ubuntu profiles
- edit gesture commands
- adjust thresholds and timing
- toggle single-finger X/Y inversion
- toggle two-finger X/Y inversion
- start, stop, restart, enable, or disable the user service
- simulate configured gestures for quick testing


## Test without installing

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python3 src/magic_mouse_daemon.py --profile profiles/cosmic.env --debug
```

Dry-run mode prints the detected gesture without sending shortcuts:

```bash
python3 src/magic_mouse_daemon.py --profile profiles/gnome-ubuntu.env --dry-run --debug
```

Simulate a gesture:

```bash
python3 src/magic_mouse_daemon.py --profile profiles/cosmic.env --simulate left --dry-run
```

List detected Magic Mouse HID devices:

```bash
python3 src/magic_mouse_daemon.py --profile profiles/cosmic.env --list-devices
```

Pick a specific device from the list:

```bash
python3 src/magic_mouse_daemon.py --profile profiles/cosmic.env --device-index 0 --debug
```

## Calibration logging

Use calibration mode when gestures are reversed, too sensitive, not sensitive enough, or not detected:

```bash
./scripts/calibrate.sh profiles/cosmic.env
```

The script creates a local JSONL log under `calibration/`. Logs are ignored by git.

Each line contains:

```json
{"ts": 0, "report_id": 18, "raw_hex": "...", "touches": [], "gesture": null}
```

Common profile tuning values:

```env
SWIPE_THRESHOLD_X=360
SWIPE_THRESHOLD_Y=420
AXIS_LOCK_RATIO=1.15
INVERT_X=0
INVERT_Y=0
```

If up/down are reversed, set:

```env
INVERT_Y=1
```

## Doctor/check script

```bash
./scripts/check.sh profiles/cosmic.env
```

This checks session variables, required commands, kernel module status, Python syntax, profile simulation, and detected HID devices.

## Troubleshooting

### Check session type

```bash
echo "$XDG_SESSION_TYPE"
```

Expected:

```text
wayland
```

### Check Magic Mouse kernel module

```bash
lsmod | grep hid_magicmouse
modinfo hid_magicmouse
```

Load manually:

```bash
sudo modprobe hid_magicmouse
```

### Check libinput gesture events

```bash
sudo libinput debug-events
```

If libinput does not emit `GESTURE_*` events for Magic Mouse, this project can still work because it reads HID reports directly.

### Permission denied on hidraw

Run once with sudo for debugging:

```bash
sudo .venv/bin/python src/magic_mouse_daemon.py --profile profiles/cosmic.env --debug
```

For normal usage, install the udev rule:

```bash
sudo cp udev/99-magic-mouse-gestures.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
```

Then reconnect the Magic Mouse.

## Repository description

```text
Magic Mouse gesture support for Linux desktops: COSMIC and GNOME/Ubuntu profiles.
```

## Development

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pytest
python3 -m py_compile src/*.py
```

## Roadmap

- [x] COSMIC and GNOME/Ubuntu profile files
- [x] Wayland shortcut sender via `wtype`
- [x] Magic Mouse HID report parser for report IDs `0x29` and `0x12`
- [x] systemd user service
- [x] device selection with `--device-index`
- [x] JSONL calibration logs
- [x] basic tests
- [ ] real-device calibration feedback
- [ ] optional tap/overview gesture
- [ ] X11 fallback with `xdotool`
- [ ] Debian/Ubuntu package


## No Magic Mouse HID devices found

If the user service says `No Magic Mouse HID devices found`, first stop the restart loop:

```bash
systemctl --user stop magic-mouse-gestures.service
systemctl --user reset-failed magic-mouse-gestures.service
```

Then check what Linux can see:

```bash
~/.local/share/magic-mouse-linux-gestures/.venv/bin/python \
  ~/.local/share/magic-mouse-linux-gestures/src/magic_mouse_daemon.py \
  --profile ~/.config/magic-mouse-gestures/profile.env \
  --list-all-hid
```

Version 0.2 runs the service with `--wait-device`, so it waits for the mouse instead of crashing when the mouse is off or disconnected.


## v0.4 permission note

If diagnostics show the Magic Mouse as `/dev/hidraw8` or similar but `access=rw:0`, run:

```bash
./scripts/fix-permissions-now.sh
systemctl --user restart magic-mouse-gestures.service
```

For permanent access, run:

```bash
./install.sh --profile cosmic --udev --start
```

Then reconnect the mouse. v0.4 installs both `TAG+="uaccess"` and a `magicmouse` group fallback; log out/in once for the group fallback to apply.

## v0.5 hidraw backend note

If diagnostics show the Magic Mouse at a real node such as `/dev/hidraw8` but the daemon prints `open failed`, use the direct hidraw backend:

```bash
./scripts/fix-permissions-now.sh
./scripts/test-hidraw-open.sh /dev/hidraw8
python3 src/magic_mouse_daemon.py --profile profiles/cosmic.env --hid-path /dev/hidraw8 --backend hidraw --debug --debug-hid --dry-run
```

To install the user service pinned to that known path during debugging:

```bash
./install.sh --profile cosmic --udev --hid-path /dev/hidraw8 --backend hidraw --start
```


## v0.6 real-device calibration note

A Pop!_OS/COSMIC Magic Mouse 1 device with `vendor=0x05ac product=0x030d` was verified against the direct `hidraw` backend. The parser recognized all four dry-run gestures:

```text
left  -> wtype -M alt -P left -p left -m alt
right -> wtype -M alt -P right -p right -m alt
up    -> wtype -M logo -M ctrl -P up -p up -m ctrl -m logo
down  -> wtype -M logo -M ctrl -P down -p down -m ctrl -m logo
```

If permissions reset after reconnect, install v0.6 with the udev rule and a pinned hidraw backend:

```bash
./install.sh --profile cosmic --udev --hid-path /dev/hidraw8 --backend hidraw --start
```

Then reconnect the mouse. v0.6 generates a local udev rule that grants a per-user ACL for the installing user in addition to `TAG+="uaccess"` and the `magicmouse` group fallback.

After installing, verify:

```bash
getfacl /dev/hidraw8
systemctl --user restart magic-mouse-gestures.service
journalctl --user -u magic-mouse-gestures.service -f -l
```
