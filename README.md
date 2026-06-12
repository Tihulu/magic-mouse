# Magic Mouse Linux

Desktop-specific Apple Magic Mouse gesture packages for Linux.

## Packages

| Folder | Version | Target desktop | Status |
|---|---:|---|---|
| `cosmic-wayland/` | `1.4.3` | Pop!_OS COSMIC / COSMIC Wayland | Stable Magic Mouse gesture setup with GUI control panel and COSMIC workspace helper |
| `gnome-ubuntu/` | `0.1.2` | Ubuntu GNOME / GNOME Wayland | GNOME workspace bridge package with Shell extension and DBus helper |

## Quick install from GitHub

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/Tihulu/magic-mouse/main/cosmic-wayland/quick-install.sh)"
```

Alternative with `wget`:

```bash
bash -c "$(wget -qO- https://raw.githubusercontent.com/Tihulu/magic-mouse/main/cosmic-wayland/quick-install.sh)"
```

Manual clone install:

```bash
git clone https://github.com/Tihulu/magic-mouse.git
cd magic-mouse/cosmic-wayland
chmod +x *.sh
./reset.sh
./install.sh
```

Launch the graphical control panel:

```bash
magic-mouse-control-panel
```

CLI fallback:

```bash
magic-mouse-control-panel-cli
```

Default COSMIC gestures:

| Gesture | Action |
|---|---|
| Two-finger swipe left | Browser back |
| Two-finger swipe right | Browser forward |
| Two-finger swipe up | Workspace up |
| Two-finger swipe down | Workspace down |

The COSMIC package uses a stateful `cosmic-ws` helper powered by `cos-cli`, because synthetic workspace keyboard shortcuts are unreliable on COSMIC Wayland.

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
- COSMIC uses direct Magic Mouse HID input plus `cos-cli` workspace activation.
- GNOME uses a Shell extension / DBus bridge because direct workspace control from outside GNOME Shell is restricted on modern GNOME Wayland sessions.
- GNOME/Ubuntu 0.1.2 supports the GNOME 45+ extension variant through GNOME Shell 50 metadata.
