"""CSV export helpers for posture statistics."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


def write_daily_posture_summary(output_path: str | Path, summary: dict[str, Any]) -> Path:
    """Write a single daily posture summary row to a CSV file."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = list(summary.keys())
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(summary)

    return path
