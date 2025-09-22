"""Logging utilities for writing structured JSON logs to disk."""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


def write_json_log(event: Dict[str, Any], *, directory: str = "logs", prefix: str = "log") -> Path:
    """Create a new JSON log file with the initial event payload."""
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


def append_json_log(path: Path, event: Dict[str, Any]) -> None:
    """Append an event to an existing JSON log file."""
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {"events": []}

    data.setdefault("events", []).append(event)

    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

