"""Baseline posture calibration storage."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_baseline(user_id: int) -> dict[str, Any] | None:
    """Load a baseline posture from the database if it exists."""
    from posture_detector.storage.database import SessionLocal
    from posture_detector.storage.models import CalibrationBaseline

    with SessionLocal() as db:
        record = db.query(CalibrationBaseline).filter(CalibrationBaseline.user_id == user_id).first()
        if not record:
            return None
        return {
            "timestamp": record.timestamp,
            "neck_angle": record.neck_angle,
            "back_angle": record.back_angle,
            "neck_good_delta": record.neck_good_delta if record.neck_good_delta is not None else 5.0,
            "neck_severe_delta": record.neck_severe_delta if record.neck_severe_delta is not None else 15.0,
            "back_good_delta": record.back_good_delta if record.back_good_delta is not None else 4.0,
            "back_severe_delta": record.back_severe_delta if record.back_severe_delta is not None else 10.0,
        }

def save_baseline(
    user_id: int,
    neck_angle: float,
    back_angle: float,
    neck_good_delta: float = 5.0,
    neck_severe_delta: float = 15.0,
    back_good_delta: float = 4.0,
    back_severe_delta: float = 10.0,
) -> dict[str, Any]:
    """Persist a new baseline posture to the database."""
    from posture_detector.storage.database import SessionLocal
    from posture_detector.storage.models import CalibrationBaseline

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "neck_angle": round(neck_angle, 2),
        "back_angle": round(back_angle, 2),
        "neck_good_delta": round(neck_good_delta, 2),
        "neck_severe_delta": round(neck_severe_delta, 2),
        "back_good_delta": round(back_good_delta, 2),
        "back_severe_delta": round(back_severe_delta, 2),
    }

    with SessionLocal() as db:
        record = db.query(CalibrationBaseline).filter(CalibrationBaseline.user_id == user_id).first()
        if not record:
            record = CalibrationBaseline(user_id=user_id)
            db.add(record)
        record.timestamp = payload["timestamp"]
        record.neck_angle = payload["neck_angle"]
        record.back_angle = payload["back_angle"]
        record.neck_good_delta = payload["neck_good_delta"]
        record.neck_severe_delta = payload["neck_severe_delta"]
        record.back_good_delta = payload["back_good_delta"]
        record.back_severe_delta = payload["back_severe_delta"]
        db.commit()

    return payload
