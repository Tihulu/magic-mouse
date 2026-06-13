# Magic Mouse Linux

Desktop-specific Apple Magic Mouse gesture packages for Linux.

## Packages

| Folder | Version | Target desktop | Status |
|---|---:|---|---|
| `cosmic-wayland/` | `1.4.7` | Pop!_OS COSMIC / COSMIC Wayland | Stable Magic Mouse gesture setup with GUI control panel, bottom-right progress window, background actions, COSMIC workspace helper, and dock icon matching fix |
| `gnome-ubuntu/` | `0.2.1` | Ubuntu GNOME / Pop!_OS GNOME / GNOME Wayland | Full GNOME package with gesture daemon, GUI control panel, Shell extension, DBus workspace helper, systemd service, udev rule, and diagnostics |

## Pop!_OS COSMIC / COSMIC Wayland

<p align="left">
  <img src="cosmic-wayland/assets/magic-mouse-control-panel.svg" width="96" alt="Magic Mouse Control Panel icon">
</p>

### Quick install from GitHub

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/Tihulu/magic-mouse/main/cosmic-wayland/setup-cosmic-v1.4.7.sh)"
```

Alternative with `wget`:

```bash
bash -c "$(wget -qO- https://raw.githubusercontent.com/Tihulu/magic-mouse/main/cosmic-wayland/setup-cosmic-v1.4.7.sh)"
```

### Manual clone install

```bash
git clone https://github.com/Tihulu/magic-mouse.git
cd magic-mouse/cosmic-wayland
chmod +x *.sh
./setup-cosmic-v1.4.7.sh
```

Launch the graphical control panel:

```bash
magic-mouse-control-panel
```

For best dock icon matching on COSMIC, launch it from the app launcher or run:

```bash
gtk-launch magic-mouse-control-panel
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

The COSMIC package uses a stateful `cosmic-ws` helper powered by `cos-cli`, because synthetic workspace keyboard shortcuts are unreliable on COSMIC Wayland. The v1.4.7 setup script patches heavy control-panel actions so they run in the background and show a small bottom-right progress window instead of freezing the UI.

## GNOME / Ubuntu

The GNOME package is for Ubuntu GNOME, Pop!_OS GNOME, and other GNOME Shell sessions. It includes the Magic Mouse gesture daemon, graphical control panel, GNOME Shell workspace extension, DBus workspace helper, user systemd service, udev permissions, and diagnostic tools.

It supports two GNOME extension paths:

- GNOME 42-44: legacy `imports.*` extension path.
- GNOME 45 and newer: modern ES module extension path.

### Quick install from GitHub

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/Tihulu/magic-mouse/main/gnome-ubuntu/quick-install.sh)"
```

Alternative with `wget`:

```bash
bash -c "$(wget -qO- https://raw.githubusercontent.com/Tihulu/magic-mouse/main/gnome-ubuntu/quick-install.sh)"
```

### Manual clone install

```bash
git clone https://github.com/Tihulu/magic-mouse.git
cd magic-mouse/gnome-ubuntu
./install.sh --install-deps --install-udev
```

After installing on GNOME Wayland, log out and log back in so GNOME Shell loads the extension cleanly. Reconnect the Magic Mouse if needed.

### Test the GNOME package

```bash
magic-mouse-gnome-probe
magic-mouse-ws ping
magic-mouse-ws status
magic-mouse-ws down
sleep 0.5
magic-mouse-ws up
magic-mouse-gesture-daemon --list-devices
```

Expected default workspace gestures:

| Gesture | Action |
|---|---|
| Two-finger swipe up | Previous workspace |
| Two-finger swipe down | Next workspace |

Open the graphical control panel:

```bash
magic-mouse-control-panel
```

The GNOME panel uses the same quick direction idea as the COSMIC panel:

- `Normal Workspace Direction`
- `Invert Workspace Direction`
- `Normal Horizontal Direction`
- `Invert Horizontal Direction`
- `Normal Physical Axes`, `Invert X Axis`, `Invert Y Axis`, and `Invert Both Axes`

Use the workspace/horizontal direction buttons first. Physical axis inversion is only for cases where the raw detected swipe direction itself is reversed.

Service and log helpers:

```bash
magic-mouse-service status
magic-mouse-service logs 200
magic-mouse-service monitor
```

Export diagnostics if something does not work:

```bash
magic-mouse-diagnose
```

If an old gesture daemon or config still calls `cosmic-ws`, install the compatibility shim:

```bash
./install.sh --cosmic-compat
```

or after installation:

```bash
magic-mouse-gnome-integrate install-cosmic-ws-shim
systemctl --user restart magic-mouse-gestures.service
```

### GNOME vs COSMIC

Use `gnome-ubuntu/` only for GNOME Shell sessions. If you are on the new COSMIC desktop, use `cosmic-wayland/` instead.

Check your session:

```bash
echo "$XDG_CURRENT_DESKTOP"
echo "$XDG_SESSION_TYPE"
gnome-shell --version 2>/dev/null || true
```

## Notes

- COSMIC and GNOME use different workspace mechanisms, so they are kept in separate folders.
- COSMIC uses direct Magic Mouse HID input plus `cos-cli` workspace activation.
- GNOME uses a Shell extension / DBus bridge because direct workspace control from outside GNOME Shell is restricted on modern GNOME Wayland sessions.
- GNOME/Ubuntu 0.2.1 is the full GNOME package: daemon, GUI control panel, workspace backend, service helpers, udev permissions, and diagnostics.
