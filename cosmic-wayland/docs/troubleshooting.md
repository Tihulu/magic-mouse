# Troubleshooting

## Service logs

```bash
journalctl --user -u magic-mouse-gestures.service -f
```

## Check everything quickly

```bash
./scripts/check.sh profiles/cosmic.env
```

## Magic Mouse not detected

1. Confirm the mouse is paired and connected in Bluetooth settings.
2. Check that the kernel driver is available:

```bash
modinfo hid_magicmouse
lsmod | grep hid_magicmouse
```

3. Load it manually:

```bash
sudo modprobe hid_magicmouse
```

4. List HID devices:

```bash
python3 src/magic_mouse_daemon.py --profile profiles/cosmic.env --list-devices
```

## Permission denied

Install the udev rule and reconnect the mouse:

```bash
./install.sh --profile cosmic --udev
```

Or manually:

```bash
sudo cp udev/99-magic-mouse-gestures.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
```

## Gestures are reversed

Edit the active profile:

```bash
nano ~/.config/magic-mouse-gestures/profile.env
```

Then change:

```env
INVERT_X=1
```

or:

```env
INVERT_Y=1
```

Restart:

```bash
systemctl --user restart magic-mouse-gestures.service
```

## Gestures are too sensitive

Increase thresholds:

```env
SWIPE_THRESHOLD_X=480
SWIPE_THRESHOLD_Y=560
```

## Gestures are not detected

Run calibration mode:

```bash
./scripts/calibrate.sh profiles/cosmic.env
```

Try several slow two-finger swipes, then inspect the JSONL file under `calibration/`.

## `wtype` does nothing

Check that you are on Wayland:

```bash
echo "$XDG_SESSION_TYPE"
```

Expected:

```text
wayland
```

Some compositors may restrict synthetic input. Start by testing a simple command manually:

```bash
wtype hello
```


## Service restarts with “No Magic Mouse HID devices found”

This means hidapi did not see a Magic Mouse hidraw device. It can happen when the mouse is off, not paired, still connected to another computer, missing udev access, or using a USB-C Magic Mouse on a kernel that does not expose the device through `hid-magicmouse`.

Stop the loop first:

```bash
systemctl --user stop magic-mouse-gestures.service
systemctl --user reset-failed magic-mouse-gestures.service
```

Diagnostics:

```bash
bluetoothctl devices Connected
lsmod | grep hid_magicmouse || sudo modprobe hid_magicmouse
ls -l /dev/hidraw*
python3 src/magic_mouse_daemon.py --profile profiles/cosmic.env --list-all-hid
```

Known product IDs currently matched by the daemon:

- `05ac:030d` Magic Mouse
- `05ac:0269` Magic Mouse 2 Lightning
- `05ac:0323` Magic Mouse 2 USB-C, kernel support required


## Magic Mouse is connected, but the service says no device was found

Check the permissions:

```bash
ls -l /dev/hidraw*
./scripts/list-hidraw.sh
```

If the relevant Magic Mouse node is `root:root` and has no ACL for your user, the user service cannot read it. Install udev rules and reconnect the mouse:

```bash
./install.sh --profile cosmic --udev --start
```

For immediate testing without reconnecting:

```bash
./scripts/fix-permissions-now.sh
systemctl --user restart magic-mouse-gestures.service
```


## v0.4 permission note

If diagnostics show the Magic Mouse as `/dev/hidraw8` or similar but `access=rw:0`, run:

```bash
./scripts/fix-permissions-now.sh
systemctl --user restart magic-mouse-gestures.service
```

For permanent access, run:

```bash
./install.sh --profile cosmic --udev --start
```

Then reconnect the mouse. v0.4 installs both `TAG+="uaccess"` and a `magicmouse` group fallback; log out/in once for the group fallback to apply.

## `open failed` with `--hid-path /dev/hidrawX`

v0.4 and older tried to pass `/dev/hidrawX` to hidapi `open_path()`. On some Linux systems hidapi expects its own opaque path from `hid.enumerate()`, not the real device node. v0.5 adds a direct Linux hidraw backend.

Try:

```bash
./scripts/fix-permissions-now.sh
./scripts/test-hidraw-open.sh /dev/hidraw8
python3 src/magic_mouse_daemon.py --profile profiles/cosmic.env --hid-path /dev/hidraw8 --backend hidraw --debug --debug-hid --dry-run
```

For a service pinned to that path:

```bash
./install.sh --profile cosmic --udev --hid-path /dev/hidraw8 --backend hidraw --start
systemctl --user restart magic-mouse-gestures.service
```
