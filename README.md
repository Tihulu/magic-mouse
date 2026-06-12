# Magic Mouse Linux

Two desktop-specific Magic Mouse gesture implementations for Linux.

## Folders

| Folder | Version | Target desktop | Status |
|---|---:|---|---|
| `cosmic-wayland/` | `1.1.0` | Pop!_OS COSMIC / COSMIC Wayland | Working COSMIC gesture daemon with control panel |
| `gnome-ubuntu/` | `0.1.1` | Ubuntu GNOME / GNOME Wayland | GNOME workspace bridge package with Shell extension + DBus helper |

## COSMIC / Wayland

```bash
cd cosmic-wayland
./install.sh --profile cosmic --udev --start
```

Useful commands:

```bash
journalctl --user -u magic-mouse-gestures.service -f
magic-mouse-control-panel
```

Default gestures:

| Gesture | Action |
|---|---|
| Two-finger swipe left | Browser back |
| Two-finger swipe right | Browser forward |
| Two-finger swipe up | Previous/up workspace |
| Two-finger swipe down | Next/down workspace |

## GNOME / Ubuntu

```bash
cd gnome-ubuntu
./install.sh
```

Log out and log back in after installing the GNOME Shell extension, then test:

```bash
magic-mouse-gnome-probe
magic-mouse-ws status
magic-mouse-ws down
sleep 0.5
magic-mouse-ws up
```

If an existing gesture daemon still calls `cosmic-ws`, install the compatibility shim:

```bash
magic-mouse-gnome-integrate install-cosmic-ws-shim
systemctl --user restart magic-mouse-gestures.service
```

## Notes

- COSMIC and GNOME use different workspace mechanisms, so they are kept in separate folders.
- COSMIC uses the Python HID gesture daemon and Wayland key sending.
- GNOME uses a Shell extension/DBus bridge because direct workspace control from outside GNOME Shell is restricted on modern GNOME Wayland sessions.
