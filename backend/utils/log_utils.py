"""Logging utilities for writing structured JSON logs to disk."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


def is_debug_logging_enabled() -> bool:
    """Check if debug file logging is enabled via environment variable."""
    return os.getenv("ENABLE_DEBUG_FILE_LOGGING", "false").lower() in ("true", "1", "yes")


def write_json_log(event: Dict[str, Any], *, directory: str = "logs", prefix: str = "log") -> Path | None:
    """Create a new JSON log file with the initial event payload.

    Returns None if debug logging is disabled.
    """
    if not is_debug_logging_enabled():
        return None

    logs_dir = Path(directory)
    logs_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    filename = logs_dir / f"{prefix}_{timestamp}_{int(time.time() * 1000)}.json"

    content = {
        "events": [event],
    }

    with filename.open("w", encoding="utf-8") as f:
        json.dump(content, f, indent=2)

    return filename


def append_json_log(path: Path | None, event: Dict[str, Any]) -> None:
    """Append an event to an existing JSON log file.

    Does nothing if path is None (debug logging disabled).
    """
    if path is None or not is_debug_logging_enabled():
        return

    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {"events": []}

    data.setdefault("events", []).append(event)

    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def write_markdown_log(content: str, *, directory: str = "logs", prefix: str = "log") -> Path | None:
    """Write content to a markdown log file.

    Returns None if debug logging is disabled.
    """
    if not is_debug_logging_enabled():
        return None

    logs_dir = Path(directory)
    logs_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    filename = logs_dir / f"{prefix}_{timestamp}_{int(time.time() * 1000)}.md"

    with filename.open("w", encoding="utf-8") as f:
        f.write(content)

    return filename

