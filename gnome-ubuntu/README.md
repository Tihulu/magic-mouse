# Magic Mouse GNOME package 0.2.1

Full Magic Mouse gesture package for Ubuntu GNOME, Pop!_OS GNOME, and other GNOME Shell desktops.

This is no longer only a workspace bridge. It includes:

- `magic-mouse-gesture-daemon` evdev gesture reader
- `magic-mouse-control-panel` Tk settings panel
- `magic-mouse-ws` GNOME workspace helper
- GNOME Shell extension DBus bridge
- user `systemd` service
- udev permission rule
- diagnostics and service helpers

## What changed in 0.2.1

- Reworked the GNOME control panel UI to match the COSMIC panel more closely.
- Converted the remaining Turkish UI text to English.
- Added quick direction buttons:
  - `Apply Stable Default`
  - `Normal Workspace Direction`
  - `Invert Workspace Direction`
  - `Normal Horizontal Direction`
  - `Invert Horizontal Direction`
  - `Disable Workspace Gestures`
- Added physical axis inversion buttons:
  - `Normal Physical Axes`
  - `Invert X Axis`
  - `Invert Y Axis`
  - `Invert Both Axes`

Use the workspace/horizontal direction buttons first when the direction feels wrong. Use physical axis inversion only when the raw detected swipe direction itself is reversed.

## Supported GNOME Shell ranges

The installer chooses the extension variant automatically:

| GNOME Shell | Extension variant |
|---|---|
| 3.36, 3.38, 40, 41, 42, 43, 44 | legacy `imports.*` extension |
| 45, 46, 47, 48, 49, 50, 51+ | modern ESM extension |

The installer patches `metadata.json` with the exact detected Shell major version so future GNOME versions are not blocked only by metadata.

## Quick install from GitHub

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/Tihulu/magic-mouse/main/gnome-ubuntu/quick-install.sh)"
```

Alternative with `wget`:

```bash
bash -c "$(wget -qO- https://raw.githubusercontent.com/Tihulu/magic-mouse/main/gnome-ubuntu/quick-install.sh)"
```

## Manual install

```bash
git clone https://github.com/Tihulu/magic-mouse.git
cd magic-mouse/gnome-ubuntu
./install.sh --install-deps --install-udev
```

Log out and log back in after installing, especially on GNOME Wayland or after udev rule changes.

## Test

```bash
magic-mouse-gnome-probe
magic-mouse-ws ping
magic-mouse-ws status
magic-mouse-ws down
sleep 0.5
magic-mouse-ws up
magic-mouse-gesture-daemon --list-devices
```

Expected default behavior:

| Gesture | Action |
|---|---|
| Two-finger swipe down | Next workspace |
| Two-finger swipe up | Previous workspace |
| Two-finger swipe left | Previous workspace |
| Two-finger swipe right | Next workspace |

## Control panel

```bash
magic-mouse-control-panel
```

The first tab is `Setup Flow`, with quick buttons for status, service restart, sensitivity presets, workspace direction, horizontal direction, physical axis inversion, and direct workspace tests.

Do not run the panel with `sudo`; it needs the logged-in desktop display session.

## Service and logs

```bash
magic-mouse-service status
magic-mouse-service logs 200
magic-mouse-service monitor
```

## Compatibility with old COSMIC-oriented configs

If an old daemon or config still calls `cosmic-ws`, install the shim:

```bash
magic-mouse-gnome-integrate install-cosmic-ws-shim
systemctl --user restart magic-mouse-gestures.service
```

Or rerun the installer with:

```bash
./install.sh --cosmic-compat
```

## Uninstall

```bash
cd magic-mouse/gnome-ubuntu
./uninstall.sh
```

Then log out and back in to fully unload the GNOME Shell extension on Wayland.

## Notes

GNOME Wayland normally does not accept old X11 synthetic-input approaches reliably, so the primary path is a tiny GNOME Shell extension that exports a private DBus API:

- `Switch("up"|"down"|"left"|"right"|"next"|"prev")`
- `SwitchTo(1..20)`
- `Overview()`
- `Ping()`
- `Status()`

The fallback `org.gnome.Shell.Eval` path is kept for debugging but should not be the main backend.
