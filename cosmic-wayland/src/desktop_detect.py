"""Desktop profile detection."""

from __future__ import annotations

import os
from pathlib import Path


KNOWN_PROFILES = {"cosmic", "gnome-ubuntu"}


def desktop_tokens() -> str:
    """Return lower-case desktop/session environment tokens."""
    return " ".join(
        filter(
            None,
            [
                os.environ.get("XDG_CURRENT_DESKTOP"),
                os.environ.get("XDG_SESSION_DESKTOP"),
                os.environ.get("DESKTOP_SESSION"),
                os.environ.get("GDMSESSION"),
            ],
        )
    ).lower()


def detect_profile_name() -> str | None:
    """Return the best profile name for the current desktop, or None."""
    candidates = desktop_tokens()
    if "cosmic" in candidates:
        return "cosmic"
    if "gnome" in candidates or "ubuntu" in candidates:
        return "gnome-ubuntu"
    return None


def profile_path(base_dir: Path, requested: str) -> Path:
    """Resolve a profile name or path."""
    if requested == "auto":
        detected = detect_profile_name()
        if not detected:
            raise SystemExit(
                "Could not auto-detect desktop profile. Use --profile cosmic or --profile gnome-ubuntu."
            )
        requested = detected

    if requested in KNOWN_PROFILES:
        return base_dir / "profiles" / f"{requested}.env"

    path = Path(requested).expanduser()
    if not path.exists():
        raise SystemExit(f"Profile not found: {requested}")
    return path
