"""Baseline posture calibration storage."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_baseline(path: str | Path) -> dict[str, Any] | None:
    """Load a baseline posture file if it exists."""

    baseline_path = Path(path)
    if not baseline_path.exists():
        return None

    try:
        return json.loads(baseline_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def save_baseline(path: str | Path, neck_angle: float, back_angle: float) -> dict[str, Any]:
    """Persist a new baseline posture file."""

    baseline_path = Path(path)
    baseline_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "neck_angle": round(neck_angle, 2),
        "back_angle": round(back_angle, 2),
    }

    temp_path = baseline_path.with_suffix(".tmp")
    temp_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    temp_path.replace(baseline_path)
    return payload
