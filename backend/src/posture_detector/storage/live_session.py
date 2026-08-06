"""Live session snapshot persistence."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def write_live_session_snapshot(user_id: int, snapshot: dict[str, Any]) -> None:
    """Upsert a live session snapshot in the database for the user."""

    from posture_detector.storage.database import SessionLocal
    from posture_detector.storage.models import LiveSessionSnapshot

    with SessionLocal() as db:
        record = db.query(LiveSessionSnapshot).filter(LiveSessionSnapshot.user_id == user_id).first()
        if not record:
            record = LiveSessionSnapshot(user_id=user_id)
            db.add(record)
        
        record.timestamp = snapshot.get("timestamp", "")
        record.current_posture_label = snapshot.get("current_posture_label", "")
        record.neck_angle = snapshot.get("neck_angle")
        record.back_angle = snapshot.get("back_angle")
        record.good_posture_percent = snapshot.get("good_posture_percent", 0.0)
        record.bad_posture_percent = snapshot.get("bad_posture_percent", 0.0)
        record.bad_posture_seconds = snapshot.get("bad_posture_seconds", 0.0)
        record.good_posture_seconds = snapshot.get("good_posture_seconds", 0.0)
        record.mild_slouch_seconds = snapshot.get("mild_slouch_seconds", 0.0)
        record.severe_slouch_seconds = snapshot.get("severe_slouch_seconds", 0.0)
        record.total_tracked_seconds = snapshot.get("total_tracked_seconds", 0.0)
        record.good_posture_count = snapshot.get("good_posture_count", 0)
        record.mild_slouch_count = snapshot.get("mild_slouch_count", 0)
        record.severe_slouch_count = snapshot.get("severe_slouch_count", 0)
        
        db.commit()
