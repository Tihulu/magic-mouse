# v1.4.3 stable — COSMIC Wayland Magic Mouse Control Panel

Stable Magic Mouse gesture setup for Pop!_OS / COSMIC Wayland.

## Highlights

- COSMIC Wayland workspace switching through the stateful `cosmic-ws` helper.
- GUI and CLI control panels.
- HID permission repair flow.
- Scrollable GUI tabs.
- Magic Mouse-style SVG application icon.
- Safer Tk display fallback after the v1.4.2 display regression.
- Desktop/workspace direction controls through direct command swapping.
- Reset backups stored under `~/Documents/magicmouse-backups/`.

## Install

```bash
cd cosmic-wayland/releases/v1.4.3-stable
chmod +x *.sh
./reset.sh
./install.sh
```
