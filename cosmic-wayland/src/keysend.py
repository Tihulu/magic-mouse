"""Shortcut sender for Magic Mouse Linux Gestures."""

from __future__ import annotations

import os
import shlex
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class SendResult:
    gesture: str
    command: str
    returncode: int
    stderr: str = ""


class KeySender:
    """Executes profile commands for detected gestures."""

    def __init__(self, profile: dict[str, str], dry_run: bool = False, debug: bool = False):
        self.profile = profile
        self.dry_run = dry_run
        self.debug = debug
        self.timeout = self._env_float("COMMAND_TIMEOUT_SEC", 2.0)

    def _env_float(self, key: str, default: float) -> float:
        try:
            return float(self.profile.get(key, str(default)))
        except ValueError:
            return default

    def command_for(self, gesture: str) -> str | None:
        return self.profile.get(f"GESTURE_{gesture.upper()}")

    def send(self, gesture: str) -> SendResult | None:
        command = self.command_for(gesture)
        if not command:
            if self.debug:
                print(f"[keysend] no command configured for gesture={gesture}", flush=True)
            return None

        if self.dry_run:
            print(f"[dry-run] {gesture}: {command}", flush=True)
            return SendResult(gesture=gesture, command=command, returncode=0)

        if self.debug:
            print(f"[keysend] {gesture}: {command}", flush=True)

        env = os.environ.copy()
        try:
            completed = subprocess.run(
                shlex.split(command),
                check=False,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                timeout=self.timeout,
            )
        except FileNotFoundError as exc:
            stderr = str(exc)
            print(f"[keysend] command not found gesture={gesture}: {stderr}", flush=True)
            return SendResult(gesture=gesture, command=command, returncode=127, stderr=stderr)
        except subprocess.TimeoutExpired as exc:
            stderr = f"command timed out after {self.timeout:.1f}s"
            print(f"[keysend] timeout gesture={gesture}: {stderr}", flush=True)
            return SendResult(gesture=gesture, command=command, returncode=124, stderr=stderr)

        stderr = completed.stderr.strip()
        if completed.returncode != 0:
            print(
                f"[keysend] command failed gesture={gesture} rc={completed.returncode}: {stderr}",
                flush=True,
            )
        return SendResult(
            gesture=gesture,
            command=command,
            returncode=completed.returncode,
            stderr=stderr,
        )
