# Magic Mouse COSMIC Wayland — v1.4.3 stable

Apple Magic Mouse gesture setup, workspace switching, and GUI control panel for Pop!_OS / COSMIC Wayland.

This stable package was tested around COSMIC Wayland behavior where synthetic workspace shortcuts are unreliable. Workspace switching is handled through a stateful `cosmic-ws` helper using `cos-cli`.

## Features

- Magic Mouse gesture daemon integration.
- COSMIC workspace up/down helper with empty-workspace state tracking.
- GUI control panel and CLI fallback.
- HID permission repair flow.
- Scrollable GUI tabs for smaller windows.
- Desktop/workspace direction controls through command swapping.
- Browser back/forward direction controls.
- Magic Mouse-style SVG application icon.
- Reset backups stored under `~/Documents/magicmouse-backups/`.

## Install

```bash
cd cosmic-wayland/releases/v1.4.3-stable
chmod +x *.sh
./reset.sh
./install.sh
```

If your upstream Magic Mouse Linux gestures source folder is elsewhere:

```bash
MM_SOURCE=/full/path/to/magic-mouse-linux-gestures ./install.sh
```

Default source path expected by this package:

```text
~/Desktop/magicmouse/magic-mouse-linux-gestures-v0.6/magic-mouse-linux-gestures
```

## Launch

```bash
magic-mouse-control-panel
```

CLI fallback:

```bash
magic-mouse-control-panel-cli
```

## Recommended GUI flow

Open **Magic Mouse Control Panel**, then use:

```text
Setup Flow → Run Required Setup Steps
```

Or run steps manually:

1. Status
2. Restart gesture service
3. Repair HID permissions
4. Sensitivity presets, optional
5. Scroll direction, native/experimental COSMIC setting
6. Gesture mapping / 2-finger direction

## Notes

If the dock icon does not match under COSMIC Wayland, this is likely a Tk/Wayland app-id limitation. The GUI remains functional; a future GTK UI would provide cleaner dock integration.

Natural scrolling is a native COSMIC/libinput setting. Some COSMIC builds may ignore mouse natural scrolling at runtime; desktop/workspace direction should be fixed in Step 6 with command swapping.
