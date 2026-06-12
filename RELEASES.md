# Releases

## gnome-ubuntu v0.2.1

- Full GNOME package for Ubuntu GNOME, Pop!_OS GNOME, and other GNOME Shell desktops.
- Includes gesture daemon, Tk control panel, GNOME Shell workspace bridge, user systemd service, udev permission rule, and diagnostics.
- Reworked the GNOME control panel UI to match the COSMIC panel more closely.
- Converted the remaining Turkish UI text to English.
- Added quick direction buttons for normal/inverted workspace direction and normal/inverted horizontal direction.
- Added physical axis inversion buttons for X, Y, both axes, and normal axes.

## cosmic-wayland v1.4.3 stable

- Stable Magic Mouse setup for Pop!_OS / COSMIC Wayland.
- Graphical control panel and terminal fallback.
- Stateful COSMIC workspace switching through `cosmic-ws` and `cos-cli`.
- HID permission repair with local udev rule and immediate ACL repair.
- Scrollable GUI layout for smaller windows.
- Desktop and browser direction controls.
- Safer Tk display fallback.
- Reset backups under `~/Documents/magicmouse-backups/`.
- Magic Mouse-style launcher icon.

## gnome-ubuntu v0.1.2

- Adds GNOME Shell 50 metadata support for Ubuntu 26.04-era desktops.
- GNOME Shell extension bridge for workspace switching.
- Separate GNOME 42-44 and GNOME 45+ extension variants.
- `install.sh` detects GNOME 45, 46, 47, 48, 49, and 50 for the ESM extension path.
- `magic-mouse-ws` CLI helper.
- `magic-mouse-gnome-probe` diagnostics.
- Optional `cosmic-ws` shim for older daemon configs.
