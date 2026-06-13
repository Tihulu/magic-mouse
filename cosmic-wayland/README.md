# Magic Mouse COSMIC Wayland

Apple Magic Mouse gesture setup, workspace switching, and GUI control panel for **Pop!_OS / COSMIC Wayland**.

This folder contains the current stable COSMIC Wayland package: **v1.4.8**.

The package avoids unreliable synthetic workspace keyboard shortcuts and uses a stateful `cosmic-ws` helper powered by `cos-cli` for COSMIC workspace switching.

## Stable install from GitHub

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/Tihulu/magic-mouse/main/cosmic-wayland/setup-cosmic-v1.4.8.sh)"
```

Alternative with `wget`:

```bash
bash -c "$(wget -qO- https://raw.githubusercontent.com/Tihulu/magic-mouse/main/cosmic-wayland/setup-cosmic-v1.4.8.sh)"
```

The setup script installs a clean **v1.4.8** control panel and fixes the v1.4.7 unterminated f-string regression.

## Optional modern UI preview

A lightweight Apple-like Tk/ttk skin is available in a separate folder:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/Tihulu/magic-mouse/main/cosmic-wayland/modern-v1.5.0/install.sh)"
```

Return to the stable simple UI:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/Tihulu/magic-mouse/main/cosmic-wayland/stable-v1.4.8/install.sh)"
```

## Manual install

```bash
git clone https://github.com/Tihulu/magic-mouse.git
cd magic-mouse/cosmic-wayland
chmod +x *.sh
./setup-cosmic-v1.4.8.sh
```

If your Magic Mouse Linux gestures source folder is somewhere else:

```bash
MM_SOURCE=/full/path/to/magic-mouse-linux-gestures ./setup-cosmic-v1.4.8.sh
```

Default source path used by this package:

```text
~/Desktop/magicmouse/magic-mouse-linux-gestures-v0.6/magic-mouse-linux-gestures
```

## What it installs

- `magic-mouse-control-panel` GUI
- `magic-mouse-control-panel-cli` terminal control panel
- `cosmic-ws` COSMIC workspace helper
- `magic-mouse-scroll-direction` helper
- user systemd service integration for the Magic Mouse gesture daemon
- local udev rule and immediate ACL repair for Apple Magic Mouse HID raw access
- Magic Mouse-style launcher icon
- background action runner for heavy GUI actions
- small bottom-right progress window with percentage feedback
- non-blocking natural/traditional scroll buttons
- dock icon matching fix for COSMIC
- v1.4.7 syntax regression fix

## Expected behavior

- Two-finger left/right: browser back/forward
- Up/down gesture: COSMIC workspace up/down through `cosmic-ws`
- GUI setup flow for service restart, HID repair, sensitivity, scroll direction, and gesture mapping

## Launch

```bash
magic-mouse-control-panel
```

For best dock icon matching on COSMIC:

```bash
gtk-launch magic-mouse-control-panel
```

CLI fallback:

```bash
magic-mouse-control-panel-cli
```

## Recommended GUI flow

Open **Magic Mouse Control Panel** and click:

```text
Setup Flow → Run Required Setup Steps
```

Or run the steps manually:

1. Status
2. Restart gesture service
3. Repair HID permissions
4. Sensitivity presets, optional
5. Scroll direction, native/experimental COSMIC setting
6. Gesture mapping / 2-finger direction

## Backups

`reset.sh` stores backups under:

```text
~/Documents/magicmouse-backups/
```

## Notes

Natural scrolling is a native COSMIC/libinput setting. Some COSMIC builds may ignore mouse natural scrolling at runtime. Desktop/workspace direction should be fixed in Step 6 with command swapping.

The control panel window now stays responsive while heavy actions run in the background and show a bottom-right progress window.

## Version

```text
1.4.8
```
