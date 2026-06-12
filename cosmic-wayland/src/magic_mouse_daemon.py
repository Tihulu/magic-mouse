#!/usr/bin/env python3
"""Magic Mouse gesture daemon for Linux desktops.

Reads Magic Mouse HID reports, detects simple multi-touch swipes, and maps them
through configurable desktop profile commands.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import select
import signal
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

try:
    import hid  # type: ignore
except ImportError:  # pragma: no cover - shown to users at runtime
    hid = None

# Make sibling imports work both as a script and from a package.
SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from keysend import KeySender  # noqa: E402

APPLE_VENDOR_ID = 0x05AC
APPLE_BLUETOOTH_VENDOR_ID = 0x004C
KNOWN_MAGIC_MOUSE_PRODUCT_IDS = {0x030D, 0x0269, 0x0323}
MOUSE_REPORT_ID = 0x29
MOUSE2_REPORT_ID = 0x12
DOUBLE_REPORT_ID = 0xF7
TOUCH_STATE_NONE = 0x00

RUNNING = True


def _handle_signal(signum: int, frame: object) -> None:  # noqa: ARG001
    global RUNNING
    RUNNING = False


signal.signal(signal.SIGINT, _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)


@dataclass(frozen=True)
class Touch:
    tracking_id: int
    x: int
    y: int
    size: int
    down: bool
    state: int


@dataclass(frozen=True)
class HidDeviceInfo:
    path: bytes | str
    vendor_id: int
    product_id: int
    product_string: str
    manufacturer_string: str
    serial_number: str
    interface_number: int | None

    def path_text(self) -> str:
        if isinstance(self.path, bytes):
            return self.path.decode(errors="replace")
        return str(self.path)


def load_env(path: Path) -> dict[str, str]:
    """Load a simple KEY=VALUE env profile file."""
    values: dict[str, str] = {}
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"Invalid env line {path}:{line_no}: {raw}")
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        try:
            parsed = shlex.split(value, comments=False, posix=True)
        except ValueError as exc:
            raise ValueError(f"Invalid env value at {path}:{line_no}: {exc}") from exc

        # Keep command strings intact, but normalize single quoted scalar values.
        if key.startswith("GESTURE_"):
            values[key] = value.strip().strip('"').strip("'")
        elif len(parsed) == 1:
            values[key] = parsed[0]
        else:
            values[key] = value.strip().strip('"').strip("'")
    return values


def env_int(profile: dict[str, str], key: str, default: int) -> int:
    try:
        return int(profile.get(key, str(default)))
    except ValueError:
        return default


def env_float(profile: dict[str, str], key: str, default: float) -> float:
    try:
        return float(profile.get(key, str(default)))
    except ValueError:
        return default


def sign_extend(value: int, bits: int) -> int:
    sign_bit = 1 << (bits - 1)
    return (value & (sign_bit - 1)) - (value & sign_bit)


def decode_mouse_touch(tdata: bytes) -> Touch:
    """Decode an 8-byte Magic Mouse touch record.

    This follows the same field layout used by Linux's hid-magicmouse driver
    for Magic Mouse, Magic Mouse 2, and USB-C Magic Mouse 2 touch records.
    """
    if len(tdata) != 8:
        raise ValueError(f"touch record must be 8 bytes, got {len(tdata)}")

    tracking_id = ((tdata[6] << 2) | (tdata[5] >> 6)) & 0x0F
    x = sign_extend((tdata[1] << 8) | tdata[0], 12)
    y = -sign_extend((tdata[2] << 4) | (tdata[1] >> 4), 12)
    size = tdata[5] & 0x3F
    state = tdata[7] & 0xF0
    down = state != TOUCH_STATE_NONE
    return Touch(tracking_id=tracking_id, x=x, y=y, size=size, down=down, state=state)


def parse_hid_report(data: bytes) -> list[Touch]:
    """Parse Magic Mouse HID input reports.

    Supported report IDs:
    - 0x29: Magic Mouse
    - 0x12: Magic Mouse 2 / Magic Mouse 2 USB-C
    - 0xF7: double report wrapper seen on some transports
    """
    if not data:
        return []

    report_id = data[0]

    # Some transports can combine reports. Keep this small and conservative.
    if report_id == DOUBLE_REPORT_ID and len(data) >= 2:
        first_len = data[1]
        first = data[2 : 2 + first_len]
        second = data[2 + first_len :]
        return parse_hid_report(first) + parse_hid_report(second)

    if report_id == MOUSE_REPORT_ID:
        if len(data) < 6 or (len(data) - 6) % 8 != 0:
            return []
        return [decode_mouse_touch(data[offset : offset + 8]) for offset in range(6, len(data), 8)]

    if report_id == MOUSE2_REPORT_ID:
        if len(data) == 8:
            return []
        if len(data) < 14 or (len(data) - 14) % 8 != 0:
            return []
        return [decode_mouse_touch(data[offset : offset + 8]) for offset in range(14, len(data), 8)]

    return []


def centroid(touches: Iterable[Touch]) -> tuple[float, float]:
    down = [t for t in touches if t.down]
    if not down:
        return (0.0, 0.0)
    return (
        sum(t.x for t in down) / len(down),
        sum(t.y for t in down) / len(down),
    )


class GestureEngine:
    def __init__(self, profile: dict[str, str], sender: KeySender, debug: bool = False):
        self.sender = sender
        self.debug = debug
        self.min_touches = env_int(profile, "MIN_TOUCHES", 2)
        self.threshold_x = env_int(profile, "SWIPE_THRESHOLD_X", 360)
        self.threshold_y = env_int(profile, "SWIPE_THRESHOLD_Y", 420)
        self.max_gesture_time = env_int(profile, "MAX_GESTURE_TIME_MS", 900) / 1000.0
        self.cooldown = env_int(profile, "SWIPE_COOLDOWN_MS", 450) / 1000.0
        self.axis_lock_ratio = env_float(profile, "AXIS_LOCK_RATIO", 1.15)
        self.invert_x = env_int(profile, "INVERT_X", 0) == 1
        self.invert_y = env_int(profile, "INVERT_Y", 0) == 1
        self.single_finger_invert_x = env_int(
            profile,
            "SINGLE_FINGER_INVERT_X",
            1 if self.invert_x else 0,
        ) == 1
        self.single_finger_invert_y = env_int(
            profile,
            "SINGLE_FINGER_INVERT_Y",
            1 if self.invert_y else 0,
        ) == 1
        self.two_finger_invert_x = env_int(
            profile,
            "TWO_FINGER_INVERT_X",
            1 if self.invert_x else 0,
        ) == 1
        self.two_finger_invert_y = env_int(
            profile,
            "TWO_FINGER_INVERT_Y",
            1 if self.invert_y else 0,
        ) == 1

        self.active = False
        self.start_xy = (0.0, 0.0)
        self.last_xy = (0.0, 0.0)
        self.start_time = 0.0
        self.last_fire_time = 0.0
        self.max_seen_touches = 0
        self.gesture_touch_count = 0
        self.wait_release_after_fire = env_int(profile, "WAIT_RELEASE_AFTER_FIRE", 1) == 1
        self.waiting_for_release = False

    def reset(self, *, keep_release_guard: bool = False) -> None:
        self.active = False
        self.start_xy = (0.0, 0.0)
        self.last_xy = (0.0, 0.0)
        self.start_time = 0.0
        self.max_seen_touches = 0
        self.gesture_touch_count = 0
        if not keep_release_guard:
            self.waiting_for_release = False

    def _gesture_inversion(self) -> tuple[bool, bool]:
        touches = self.gesture_touch_count or self.max_seen_touches or self.min_touches
        if touches <= 1:
            return (self.single_finger_invert_x, self.single_finger_invert_y)
        return (self.two_finger_invert_x, self.two_finger_invert_y)

    def feed(self, touches: list[Touch]) -> str | None:
        now = time.monotonic()
        down = [t for t in touches if t.down]
        count = len(down)

        if self.waiting_for_release:
            if count == 0:
                if self.debug:
                    print("[gesture] release after fire", flush=True)
                self.reset()
            return None

        if count >= self.min_touches and not self.active:
            self.active = True
            self.start_xy = centroid(down)
            self.last_xy = self.start_xy
            self.start_time = now
            self.max_seen_touches = count
            self.gesture_touch_count = count
            if self.debug:
                print(f"[gesture] start touches={count} xy={self.start_xy}", flush=True)
            return None

        if self.active:
            self.max_seen_touches = max(self.max_seen_touches, count)

            if count == 0:
                if self.debug:
                    print("[gesture] end without threshold", flush=True)
                self.reset()
                return None

            self.last_xy = centroid(down)
            elapsed = now - self.start_time
            if elapsed > self.max_gesture_time:
                if self.debug:
                    print(f"[gesture] timeout elapsed={elapsed:.3f}", flush=True)
                self.reset()
                return None

            dx = self.last_xy[0] - self.start_xy[0]
            dy = self.last_xy[1] - self.start_xy[1]
            invert_x, invert_y = self._gesture_inversion()
            if invert_x:
                dx = -dx
            if invert_y:
                dy = -dy

            if self.debug:
                print(
                    f"[gesture] touches={count} dx={dx:.1f} dy={dy:.1f} elapsed={elapsed:.3f}",
                    flush=True,
                )

            if now - self.last_fire_time < self.cooldown:
                return None

            gesture: str | None = None
            if abs(dx) >= self.threshold_x and abs(dx) > abs(dy) * self.axis_lock_ratio:
                gesture = "right" if dx > 0 else "left"
            elif abs(dy) >= self.threshold_y and abs(dy) > abs(dx) * self.axis_lock_ratio:
                # Coordinate direction can vary. Toggle INVERT_Y=1 in the profile if reversed.
                gesture = "up" if dy < 0 else "down"

            if gesture:
                self.last_fire_time = now
                if self.debug:
                    print(f"[gesture] fire {gesture}", flush=True)
                self.sender.send(gesture)
                if self.wait_release_after_fire:
                    self.waiting_for_release = True
                    self.reset(keep_release_guard=True)
                else:
                    self.reset()
                return gesture

        return None



class HidrawDevice:
    """Small Linux hidraw reader used when hidapi cannot open /dev/hidrawX.

    python-hidapi open_path() expects the opaque path returned by hid.enumerate().
    Our sysfs fallback knows the real /dev/hidrawX node, so this backend opens
    that node directly and reads raw reports from it.
    """

    def __init__(self, path: str):
        self.path = path
        self.fd: int | None = None

    def open(self) -> None:
        try:
            self.fd = os.open(self.path, os.O_RDONLY | os.O_NONBLOCK)
        except PermissionError as exc:
            raise DeviceAccessError(
                f"Magic Mouse found at {self.path}, but this user cannot read it: {exc}. "
                "Run scripts/fix-permissions-now.sh, reconnect after ./install.sh --udev, "
                "or test once with: sudo setfacl -m u:$USER:rw " + self.path
            ) from exc
        except OSError as exc:
            raise OSError(f"hidraw open failed for {self.path}: {exc}") from exc

    def set_nonblocking(self, value: bool) -> None:  # hidapi compatibility
        return None

    def read(self, size: int, timeout_ms: int = 500) -> list[int]:
        if self.fd is None:
            return []
        timeout = max(timeout_ms, 0) / 1000.0
        ready, _, _ = select.select([self.fd], [], [], timeout)
        if not ready:
            return []
        try:
            data = os.read(self.fd, size)
        except BlockingIOError:
            return []
        except OSError as exc:
            raise OSError(f"hidraw read failed for {self.path}: {exc}") from exc
        return list(data)

    def close(self) -> None:
        if self.fd is not None:
            try:
                os.close(self.fd)
            finally:
                self.fd = None




class DeviceAccessError(RuntimeError):
    """Raised when a Magic Mouse exists but the current user cannot open it."""


def _decode_hid_id(value: str) -> tuple[int, int] | None:
    """Parse HID_ID values like 0005:000005AC:00000269."""
    parts = value.strip().split(":")
    if len(parts) != 3:
        return None
    try:
        return int(parts[1], 16), int(parts[2], 16)
    except ValueError:
        return None


def _parse_sysfs_uevent(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                values[key] = value
    except OSError:
        pass
    return values


def _sysfs_hidraw_item(node: Path) -> dict | None:
    """Build a hidapi-like dict from /sys/class/hidraw when hidapi cannot see it.

    This is useful on Linux because permission-denied hidraw nodes can make the
    device look like it does not exist from a normal user service.
    """
    name = node.name
    dev_path = f"/dev/{name}"
    device_link = node / "device"
    try:
        real = device_link.resolve()
    except OSError:
        real = device_link

    candidates = [real / "uevent", real.parent / "uevent", real.parent.parent / "uevent"]
    merged: dict[str, str] = {}
    for candidate in candidates:
        merged.update(_parse_sysfs_uevent(candidate))

    vendor_id = 0
    product_id = 0
    if "HID_ID" in merged:
        parsed = _decode_hid_id(merged["HID_ID"])
        if parsed:
            vendor_id, product_id = parsed

    if not vendor_id or not product_id:
        text = str(real).upper()
        match = re.search(r"(?:000[35]:)?([0-9A-F]{4}):([0-9A-F]{4})", text)
        if match:
            vendor_id = int(match.group(1), 16)
            product_id = int(match.group(2), 16)

    product = merged.get("HID_NAME") or merged.get("NAME") or ""
    manufacturer = "Apple" if vendor_id in {APPLE_VENDOR_ID, APPLE_BLUETOOTH_VENDOR_ID} else ""

    if not vendor_id and "05AC" in str(real).upper():
        vendor_id = APPLE_VENDOR_ID

    return {
        "path": dev_path,
        "vendor_id": vendor_id,
        "product_id": product_id,
        "product_string": product,
        "manufacturer_string": manufacturer,
        "serial_number": "",
        "interface_number": None,
        "readable": os.access(dev_path, os.R_OK),
        "writable": os.access(dev_path, os.W_OK),
        "source": "sysfs",
    }


def enumerate_sysfs_hidraw_items() -> list[dict]:
    base = Path("/sys/class/hidraw")
    if not base.exists():
        return []
    items: list[dict] = []
    for node in sorted(base.glob("hidraw*")):
        item = _sysfs_hidraw_item(node)
        if item:
            items.append(item)
    return items


def _item_key(item: dict) -> tuple[int, int, str]:
    path = item.get("path")
    if isinstance(path, bytes):
        path_text = path.decode(errors="replace")
    else:
        path_text = str(path or "")
    return (int(item.get("vendor_id") or 0), int(item.get("product_id") or 0), path_text)


def enumerate_all_items_with_sysfs_fallback() -> list[dict]:
    items: list[dict] = []
    try:
        items.extend(enumerate_hid_items())
    except Exception:
        # Keep diagnostics useful even when hidapi is missing/broken.
        pass
    seen = {_item_key(item) for item in items}
    for item in enumerate_sysfs_hidraw_items():
        key = _item_key(item)
        if key not in seen:
            items.append(item)
            seen.add(key)
    return items


def _device_from_hid_item(item: dict) -> HidDeviceInfo:
    return HidDeviceInfo(
        path=item.get("path"),
        vendor_id=int(item.get("vendor_id") or 0),
        product_id=int(item.get("product_id") or 0),
        product_string=str(item.get("product_string") or ""),
        manufacturer_string=str(item.get("manufacturer_string") or ""),
        serial_number=str(item.get("serial_number") or ""),
        interface_number=item.get("interface_number"),
    )


def looks_like_magic_mouse_item(item: dict) -> bool:
    """Return True for Magic Mouse HID entries, even when product strings are sparse.

    Some Bluetooth stacks expose Apple HID devices with an empty product string.
    Matching by Apple vendor + known product IDs catches Magic Mouse 1, Magic
    Mouse 2 Lightning, and Magic Mouse 2 USB-C where the kernel exposes hidraw.
    """
    product = str(item.get("product_string") or "").lower()
    manufacturer = str(item.get("manufacturer_string") or "").lower()
    vendor_id = int(item.get("vendor_id") or 0)
    product_id = int(item.get("product_id") or 0)

    if "magic mouse" in product:
        return True
    if product_id in KNOWN_MAGIC_MOUSE_PRODUCT_IDS and vendor_id in {APPLE_VENDOR_ID, APPLE_BLUETOOTH_VENDOR_ID}:
        return True
    if vendor_id == APPLE_VENDOR_ID and "mouse" in product:
        return True
    if "apple" in manufacturer and "mouse" in product:
        return True
    return False


def enumerate_hid_items() -> list[dict]:
    if hid is None:
        raise SystemExit("Python package 'hidapi' is not installed. Run: pip install -r requirements.txt")
    return list(hid.enumerate())


def list_magic_mouse_devices() -> list[HidDeviceInfo]:
    devices: list[HidDeviceInfo] = []
    for item in enumerate_all_items_with_sysfs_fallback():
        if looks_like_magic_mouse_item(item):
            devices.append(_device_from_hid_item(item))
    return devices


def print_devices(all_hid: bool = False) -> None:
    raw_items = enumerate_all_items_with_sysfs_fallback()
    if all_hid:
        print("All HID devices visible via hidapi + sysfs fallback:")
        items = raw_items
    else:
        items = [item for item in raw_items if looks_like_magic_mouse_item(item)]

    if not items:
        print("No Magic Mouse HID devices found." if not all_hid else "No HID devices found.")
        print("Tip: check Bluetooth pairing, hid_magicmouse, and /dev/hidraw permissions.")
        return

    for index, item in enumerate(items):
        dev = _device_from_hid_item(item)
        path = dev.path_text()
        readable = os.access(path, os.R_OK) if path.startswith("/dev/") else None
        writable = os.access(path, os.W_OK) if path.startswith("/dev/") else None
        access = ""
        if readable is not None:
            access = f" access=rw:{int(readable and writable)} r:{int(readable)} w:{int(writable)}"
        source = item.get("source", "hidapi")
        print(
            f"[{index}] vendor=0x{dev.vendor_id:04x} product=0x{dev.product_id:04x} "
            f"interface={dev.interface_number} product='{dev.product_string}' "
            f"manufacturer='{dev.manufacturer_string}' path='{path}' source={source}{access}"
        )


def choose_device(device_index: int | None = None, path: str | None = None) -> HidDeviceInfo:
    devices = list_magic_mouse_devices()
    if not devices:
        raise LookupError("No Magic Mouse HID devices found. Pair/connect the mouse and try --list-devices.")

    if path:
        for dev in devices:
            if dev.path_text() == path:
                return dev
        raise LookupError(f"Magic Mouse HID path not found: {path}")

    if device_index is not None:
        if device_index < 0 or device_index >= len(devices):
            raise LookupError(f"Invalid --device-index {device_index}. Use --list-devices first.")
        return devices[device_index]

    # Prefer product strings that explicitly mention Magic Mouse, then known PIDs, then low interfaces.
    return sorted(
        devices,
        key=lambda d: (
            "magic mouse" not in d.product_string.lower(),
            d.product_id not in KNOWN_MAGIC_MOUSE_PRODUCT_IDS,
            d.interface_number or 0,
        ),
    )[0]


def open_device(device_index: int | None = None, path: str | None = None, backend: str = "auto"):
    selected = choose_device(device_index=device_index, path=path)
    raw_path = selected.path
    path_text = selected.path_text()

    if backend not in {"auto", "hidapi", "hidraw"}:
        raise SystemExit(f"Invalid backend: {backend}. Expected auto, hidapi, or hidraw.")

    # /dev/hidrawX paths discovered via sysfs are not valid hidapi open_path()
    # inputs on some systems. Prefer the direct hidraw backend for those paths.
    use_hidraw = backend == "hidraw" or (backend == "auto" and path_text.startswith("/dev/hidraw"))

    if use_hidraw:
        if not path_text.startswith("/dev/"):
            raise SystemExit(f"--backend hidraw requires a /dev/hidrawX path, got: {path_text}")
        if not os.access(path_text, os.R_OK):
            raise DeviceAccessError(
                f"Magic Mouse found at {path_text}, but this user cannot read it. "
                "Run scripts/fix-permissions-now.sh, reconnect after ./install.sh --udev, "
                f"or test once with: sudo setfacl -m u:$USER:rw {path_text}"
            )
        dev = HidrawDevice(path_text)
        dev.open()
        print(
            f"[hidraw] opened product='{selected.product_string or 'Magic Mouse'}' "
            f"vendor=0x{selected.vendor_id:04x} product=0x{selected.product_id:04x} "
            f"path='{path_text}'",
            flush=True,
        )
        return dev, selected

    if hid is None:
        raise SystemExit("Python package 'hidapi' is not installed. Run: pip install -r requirements.txt")

    if path_text.startswith("/dev/"):
        raise SystemExit(
            f"{path_text} is a real hidraw node. Use --backend hidraw, or leave --backend auto. "
            "hidapi open_path() needs the opaque path from hid.enumerate(), not always /dev/hidrawX."
        )

    dev = hid.device()
    try:
        dev.open_path(raw_path.encode() if isinstance(raw_path, str) else raw_path)
    except OSError as exc:
        message = str(exc)
        if "permission" in message.lower() or "access" in message.lower():
            raise DeviceAccessError(
                f"Magic Mouse found at {path_text}, but opening it failed: {exc}. "
                "Install udev rules, reconnect the mouse, or run scripts/fix-permissions-now.sh."
            ) from exc
        raise OSError(
            f"hidapi open_path failed for {path_text}: {exc}. "
            "Try again with --backend hidraw --hid-path /dev/hidrawX."
        ) from exc

    print(
        f"[hidapi] opened product='{selected.product_string or 'Magic Mouse'}' "
        f"vendor=0x{selected.vendor_id:04x} product=0x{selected.product_id:04x} "
        f"interface={selected.interface_number} path='{path_text}'",
        flush=True,
    )
    return dev, selected


def wait_for_device(args: argparse.Namespace):
    started = time.monotonic()
    logged_missing = False
    while RUNNING:
        try:
            return open_device(device_index=args.device_index, path=args.hid_path, backend=args.backend)
        except (LookupError, DeviceAccessError, OSError) as exc:
            if not args.wait_device:
                raise SystemExit(str(exc)) from exc
            if not logged_missing or args.debug:
                print(f"[hid] {exc}", flush=True)
                print("[hid] waiting for Magic Mouse/access. Pair/connect it, install udev rules, or run --list-all-hid.", flush=True)
                logged_missing = True
            if args.device_timeout and (time.monotonic() - started) >= args.device_timeout:
                raise SystemExit("Timed out waiting for Magic Mouse HID device/access.") from exc
            time.sleep(args.wait_interval)
    raise SystemExit(0)


class JsonlRecorder:
    def __init__(self, path: Path | None):
        self.path = path
        self.file = None
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            self.file = path.open("a", encoding="utf-8")

    def close(self) -> None:
        if self.file:
            self.file.close()

    def write_packet(self, data: bytes, touches: list[Touch], gesture: str | None = None) -> None:
        if not self.file:
            return
        self.file.write(
            json.dumps(
                {
                    "ts": time.time(),
                    "report_id": data[0] if data else None,
                    "raw_hex": data.hex(" "),
                    "touches": [asdict(t) for t in touches],
                    "gesture": gesture,
                },
                ensure_ascii=False,
            )
            + "\n"
        )
        self.file.flush()


def run_loop(args: argparse.Namespace, profile: dict[str, str]) -> None:
    sender = KeySender(profile, dry_run=args.dry_run, debug=args.debug)
    engine = GestureEngine(profile, sender, debug=args.debug)

    if args.simulate:
        sender.send(args.simulate)
        return

    record_path = Path(args.record_log).expanduser() if args.record_log else None
    recorder = JsonlRecorder(record_path)

    if record_path:
        print(f"[record] writing calibration log: {record_path}", flush=True)

    try:
        while RUNNING:
            dev = None
            try:
                dev, selected = wait_for_device(args)
                dev.set_nonblocking(False)
                print(
                    f"[daemon] profile={profile.get('PROFILE_NAME', 'unknown')} "
                    f"dry_run={args.dry_run} device='{selected.product_string}'",
                    flush=True,
                )

                while RUNNING:
                    try:
                        raw = dev.read(args.read_size, timeout_ms=500)
                    except OSError as exc:
                        if args.wait_device:
                            print(f"[hid] read failed/disconnected: {exc}; waiting for reconnect", flush=True)
                            break
                        raise SystemExit(f"HID read failed: {exc}") from exc

                    if not raw:
                        continue

                    data = bytes(raw)
                    if args.debug_hid:
                        print("[hid] " + data.hex(" "), flush=True)

                    touches = parse_hid_report(data)
                    if args.debug and touches:
                        compact = ", ".join(
                            f"id={t.tracking_id} x={t.x} y={t.y} size={t.size} down={int(t.down)} state=0x{t.state:02x}"
                            for t in touches
                        )
                        print(f"[touch] {compact}", flush=True)

                    gesture = engine.feed(touches) if touches else None
                    recorder.write_packet(data, touches, gesture)
            finally:
                if dev is not None:
                    try:
                        dev.close()
                    except Exception:
                        pass

            if not args.wait_device:
                break
            time.sleep(args.wait_interval)
    finally:
        recorder.close()

    print("[daemon] stopped", flush=True)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Magic Mouse gesture daemon for Linux desktops.")
    parser.add_argument("--profile", required=True, help="Path to profile .env file")
    parser.add_argument("--hid-path", help="Exact hidraw path from --list-devices")
    parser.add_argument("--backend", choices=["auto", "hidapi", "hidraw"], default="auto", help="Input backend. Default: auto; /dev/hidrawX paths use hidraw.")
    parser.add_argument("--device-index", type=int, help="Device index from --list-devices")
    parser.add_argument("--list-devices", action="store_true", help="List detected Magic Mouse HID devices")
    parser.add_argument("--list-all-hid", action="store_true", help="List every HID device visible to hidapi for diagnostics")
    parser.add_argument("--debug", action="store_true", help="Print gesture/touch debug logs")
    parser.add_argument("--debug-hid", action="store_true", help="Print raw HID packets in hex")
    parser.add_argument("--dry-run", action="store_true", help="Do not run commands; print them")
    parser.add_argument("--record-log", help="Write calibration packets to a JSONL file")
    parser.add_argument("--read-size", type=int, default=128, help="HID read size. Default: 128")
    parser.add_argument("--wait-device", action="store_true", help="Keep running and wait until a Magic Mouse HID device appears")
    parser.add_argument("--wait-interval", type=float, default=3.0, help="Seconds between device scans when --wait-device is enabled")
    parser.add_argument("--device-timeout", type=float, default=0.0, help="Seconds to wait for a device; 0 means forever")
    parser.add_argument(
        "--simulate",
        choices=["left", "right", "up", "down", "overview"],
        help="Trigger a configured gesture command and exit",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if args.list_devices or args.list_all_hid:
        print_devices(all_hid=args.list_all_hid)
        return 0

    profile_path = Path(args.profile).expanduser()
    if not profile_path.exists():
        parser.error(f"profile does not exist: {profile_path}")

    profile = load_env(profile_path)

    # Allow installed service configs to pin a device/backend without editing the
    # systemd unit. CLI flags still win.
    if not args.hid_path and profile.get("HID_PATH"):
        args.hid_path = profile["HID_PATH"]
    if args.backend == "auto" and profile.get("BACKEND"):
        args.backend = profile["BACKEND"]

    run_loop(args, profile)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
