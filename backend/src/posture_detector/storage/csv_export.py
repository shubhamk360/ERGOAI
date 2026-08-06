"""CSV export helpers for posture statistics."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


def write_daily_posture_summary(user_id: int, summary: dict[str, Any]) -> None:
    """Write a single daily posture summary to the database for the user."""

    from datetime import datetime
    from posture_detector.storage.database import SessionLocal
    from posture_detector.storage.models import DailyPostureSummary

    # Extract date from summary or use current date
    date_str = summary.get("date", datetime.now().strftime("%Y-%m-%d"))
    try:
        dt_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        dt_date = datetime.now().date()

    with SessionLocal() as db:
        record = db.query(DailyPostureSummary).filter(
            DailyPostureSummary.user_id == user_id,
            DailyPostureSummary.date == dt_date
        ).first()

        if not record:
            record = DailyPostureSummary(user_id=user_id, date=dt_date)
            db.add(record)
            
        record.good_posture_seconds = summary.get("good_posture_seconds", 0.0)
        record.mild_slouch_seconds = summary.get("mild_slouch_seconds", 0.0)
        record.severe_slouch_seconds = summary.get("severe_slouch_seconds", 0.0)
        record.total_tracked_seconds = summary.get("total_tracked_seconds", 0.0)
        record.good_posture_count = summary.get("good_posture_count", 0)
        record.mild_slouch_count = summary.get("mild_slouch_count", 0)
        record.severe_slouch_count = summary.get("severe_slouch_count", 0)
        record.avg_neck_angle = summary.get("avg_neck_angle")
        record.avg_back_angle = summary.get("avg_back_angle")
        record.fatigue_alerts_count = summary.get("fatigue_alerts_count", 0)

        db.commit()
