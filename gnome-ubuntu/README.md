# Magic Mouse GNOME/Ubuntu workspace backend 0.1.1

This package is a GNOME/Ubuntu backend for Magic Mouse workspace gestures. It replaces COSMIC-specific workspace switching with `magic-mouse-ws`.

## What changed in 0.1.1

- Adds two GNOME Shell extension variants:
  - GNOME 42-44 legacy `imports.*` extension for Ubuntu 22.04-era desktops.
  - GNOME 45-49 ESM extension for Ubuntu 24.04+ and newer GNOME desktops.
- `install.sh` detects the installed GNOME Shell major version and installs the correct variant.
- Adds `magic-mouse-ws status` for active workspace/count debugging.
- Adds `magic-mouse-gnome-integrate install-cosmic-ws-shim` for old daemons that still call `cosmic-ws`.
- Improves `magic-mouse-gnome-probe` output.

## Install

```bash
unzip magic-mouse-gnome-ubuntu-0.1.1.zip
cd magic-mouse-gnome-ubuntu-0.1.1
./install.sh
```

On GNOME Wayland, log out and log back in after installing/enabling the extension.

## Test

```bash
magic-mouse-gnome-probe
magic-mouse-ws status
magic-mouse-ws down
sleep 0.5
magic-mouse-ws up
```

Expected behavior:

- two-finger down -> next workspace
- two-finger up -> previous workspace

## Hook into the existing daemon

If your existing detector can call commands directly, use:

```bash
magic-mouse-ws down
magic-mouse-ws up
```

If the old detector is hardcoded to call `cosmic-ws`, install the compatibility shim:

```bash
magic-mouse-gnome-integrate install-cosmic-ws-shim
```

That creates `~/.local/bin/cosmic-ws` which delegates to `~/.local/bin/magic-mouse-ws`.

## Debug info to send back

```bash
magic-mouse-gnome-probe
journalctl --user -u magic-mouse-gestures.service -n 80 --no-pager
```

## Notes

GNOME Wayland normally does not accept old X11 synthetic-input approaches reliably, so the primary path is a tiny GNOME Shell extension that exports a private DBus API:

- `Switch("up"|"down"|"left"|"right"|"next"|"prev")`
- `SwitchTo(1..12)`
- `Ping()`
- `Status()`

The fallback `org.gnome.Shell.Eval` path is kept for debugging but should not be the main backend.
