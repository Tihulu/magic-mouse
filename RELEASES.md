# Releases

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
