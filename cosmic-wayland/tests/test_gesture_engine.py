from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from magic_mouse_daemon import GestureEngine, Touch, load_env  # noqa: E402


class FakeSender:
    def __init__(self):
        self.sent: list[str] = []

    def send(self, gesture: str):
        self.sent.append(gesture)


def touch(x: int, y: int, tracking_id: int = 1) -> Touch:
    return Touch(tracking_id=tracking_id, x=x, y=y, size=20, down=True, state=0x80)


def test_load_env_keeps_gesture_command_string():
    profile = load_env(ROOT / "profiles" / "cosmic.env")
    assert profile["PROFILE_NAME"] == "cosmic"
    assert profile["GESTURE_LEFT"].startswith("wtype -M alt")


def test_horizontal_swipe_fires_right():
    sender = FakeSender()
    engine = GestureEngine(
        {
            "MIN_TOUCHES": "2",
            "SWIPE_THRESHOLD_X": "100",
            "SWIPE_THRESHOLD_Y": "100",
            "MAX_GESTURE_TIME_MS": "2000",
            "SWIPE_COOLDOWN_MS": "0",
        },
        sender,  # type: ignore[arg-type]
    )
    engine.feed([touch(0, 0, 1), touch(0, 20, 2)])
    result = engine.feed([touch(160, 0, 1), touch(160, 20, 2)])
    assert result == "right"
    assert sender.sent == ["right"]


def test_vertical_swipe_fires_up_when_y_decreases():
    sender = FakeSender()
    engine = GestureEngine(
        {
            "MIN_TOUCHES": "2",
            "SWIPE_THRESHOLD_X": "100",
            "SWIPE_THRESHOLD_Y": "100",
            "MAX_GESTURE_TIME_MS": "2000",
            "SWIPE_COOLDOWN_MS": "0",
        },
        sender,  # type: ignore[arg-type]
    )
    engine.feed([touch(0, 200, 1), touch(20, 200, 2)])
    result = engine.feed([touch(0, 20, 1), touch(20, 20, 2)])
    assert result == "up"
    assert sender.sent == ["up"]


def test_waits_for_release_after_fire():
    sender = FakeSender()
    engine = GestureEngine(
        {
            "MIN_TOUCHES": "2",
            "SWIPE_THRESHOLD_X": "100",
            "SWIPE_THRESHOLD_Y": "100",
            "MAX_GESTURE_TIME_MS": "2000",
            "SWIPE_COOLDOWN_MS": "0",
            "WAIT_RELEASE_AFTER_FIRE": "1",
        },
        sender,  # type: ignore[arg-type]
    )
    engine.feed([touch(0, 0, 1), touch(0, 20, 2)])
    assert engine.feed([touch(160, 0, 1), touch(160, 20, 2)]) == "right"
    # Fingers are still down and have moved far enough for another gesture, but
    # the release guard prevents a second accidental fire.
    assert engine.feed([touch(320, 0, 1), touch(320, 20, 2)]) is None
    assert sender.sent == ["right"]
    # Releasing both fingers arms the next gesture.
    assert engine.feed([]) is None
    engine.feed([touch(0, 0, 1), touch(0, 20, 2)])
    assert engine.feed([touch(-160, 0, 1), touch(-160, 20, 2)]) == "left"
    assert sender.sent == ["right", "left"]


def test_single_finger_invert_x_flips_direction():
    sender = FakeSender()
    engine = GestureEngine(
        {
            "MIN_TOUCHES": "1",
            "SWIPE_THRESHOLD_X": "100",
            "SWIPE_THRESHOLD_Y": "100",
            "MAX_GESTURE_TIME_MS": "2000",
            "SWIPE_COOLDOWN_MS": "0",
            "SINGLE_FINGER_INVERT_X": "1",
            "TWO_FINGER_INVERT_X": "0",
        },
        sender,  # type: ignore[arg-type]
    )
    engine.feed([touch(0, 0, 1)])
    result = engine.feed([touch(160, 0, 1)])
    assert result == "left"
    assert sender.sent == ["left"]


def test_two_finger_invert_y_flips_direction():
    sender = FakeSender()
    engine = GestureEngine(
        {
            "MIN_TOUCHES": "2",
            "SWIPE_THRESHOLD_X": "100",
            "SWIPE_THRESHOLD_Y": "100",
            "MAX_GESTURE_TIME_MS": "2000",
            "SWIPE_COOLDOWN_MS": "0",
            "TWO_FINGER_INVERT_Y": "1",
        },
        sender,  # type: ignore[arg-type]
    )
    engine.feed([touch(0, 200, 1), touch(20, 200, 2)])
    result = engine.feed([touch(0, 20, 1), touch(20, 20, 2)])
    assert result == "down"
    assert sender.sent == ["down"]
