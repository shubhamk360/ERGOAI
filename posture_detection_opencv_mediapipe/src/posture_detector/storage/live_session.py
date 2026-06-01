"""Live session snapshot persistence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_live_session_snapshot(output_path: str | Path, snapshot: dict[str, Any]) -> Path:
    """Write the latest live session snapshot to JSON."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(".tmp")
    temp_path.write_text(json.dumps(snapshot, ensure_ascii=True, indent=2), encoding="utf-8")
    temp_path.replace(path)
    return path
