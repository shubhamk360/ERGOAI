from typing import List, Dict, Any
from sqlalchemy import func
from posture_detector.storage.database import SessionLocal
from posture_detector.storage.models import DailyPostureSummary, LiveSessionSnapshot
from posture_detector.api import schemas

def get_daily_history(user_id: int) -> List[schemas.DailySummary]:
    with SessionLocal() as db:
        records = db.query(
            DailyPostureSummary.date,
            func.sum(DailyPostureSummary.good_posture_seconds).label("good_posture_seconds"),
            func.sum(DailyPostureSummary.mild_slouch_seconds).label("mild_slouch_seconds"),
            func.sum(DailyPostureSummary.severe_slouch_seconds).label("severe_slouch_seconds"),
            func.sum(DailyPostureSummary.total_tracked_seconds).label("total_tracked_seconds"),
            func.sum(DailyPostureSummary.good_posture_count).label("good_posture_count"),
            func.sum(DailyPostureSummary.mild_slouch_count).label("mild_slouch_count"),
            func.sum(DailyPostureSummary.severe_slouch_count).label("severe_slouch_count"),
            func.avg(DailyPostureSummary.avg_neck_angle).label("avg_neck_angle"),
            func.avg(DailyPostureSummary.avg_back_angle).label("avg_back_angle")
        ).filter(DailyPostureSummary.user_id == user_id).group_by(DailyPostureSummary.date).order_by(DailyPostureSummary.date).all()
        
        results = []
        for r in records:
            total = r.total_tracked_seconds or 0.0
            good_pct = round((r.good_posture_seconds / total) * 100, 2) if total > 0 else 0.0
            bad_sec = (r.mild_slouch_seconds or 0.0) + (r.severe_slouch_seconds or 0.0)
            bad_pct = round((bad_sec / total) * 100, 2) if total > 0 else 0.0
            
            summary = schemas.DailySummary(
                date=r.date.strftime("%Y-%m-%d"),
                good_posture_seconds=r.good_posture_seconds or 0.0,
                mild_slouch_seconds=r.mild_slouch_seconds or 0.0,
                severe_slouch_seconds=r.severe_slouch_seconds or 0.0,
                total_tracked_seconds=total,
                good_posture_count=r.good_posture_count or 0,
                mild_slouch_count=r.mild_slouch_count or 0,
                severe_slouch_count=r.severe_slouch_count or 0,
                good_posture_percent=good_pct,
                bad_posture_percent=bad_pct,
                bad_posture_seconds=bad_sec,
                avg_neck_angle=round(r.avg_neck_angle, 2) if r.avg_neck_angle is not None else None,
                avg_back_angle=round(r.avg_back_angle, 2) if r.avg_back_angle is not None else None
            )
            results.append(summary)
            
        return results

def get_live_snapshot(user_id: int) -> Dict[str, Any] | None:
    with SessionLocal() as db:
        record = db.query(LiveSessionSnapshot).filter(LiveSessionSnapshot.user_id == user_id).first()
        if not record:
            return None
        return {
            "timestamp": record.timestamp,
            "current_posture_label": record.current_posture_label,
            "neck_angle": record.neck_angle,
            "back_angle": record.back_angle,
            "good_posture_percent": record.good_posture_percent,
            "bad_posture_percent": record.bad_posture_percent,
            "bad_posture_seconds": record.bad_posture_seconds,
            "good_posture_seconds": record.good_posture_seconds,
            "mild_slouch_seconds": record.mild_slouch_seconds,
            "severe_slouch_seconds": record.severe_slouch_seconds,
            "total_tracked_seconds": record.total_tracked_seconds,
            "good_posture_count": record.good_posture_count,
            "mild_slouch_count": record.mild_slouch_count,
            "severe_slouch_count": record.severe_slouch_count
        }
