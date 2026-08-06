import pandas as pd
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from posture_detector.api import schemas, dependencies

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

DEFAULT_EXPORT_DIR = Path(__file__).resolve().parents[4] / "data" / "exports"

from posture_detector.storage.queries import get_daily_history

def load_daily_history(user_id: int) -> List[schemas.DailySummary]:
    return get_daily_history(user_id)

@router.get("/daily", response_model=List[schemas.DailySummary])
async def get_daily_analytics(
    current_user: schemas.UserResponse = Depends(dependencies.get_current_user)
):
    try:
        return load_daily_history(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading analytics: {str(e)}")

@router.get("/report", response_model=schemas.ReportResponse)
async def generate_report(
    days: int = 7,
    current_user: schemas.UserResponse = Depends(dependencies.get_current_user)
):
    try:
        history = load_daily_history(current_user.id)
        # Filter to last `days` days, history is returned sorted by date
        history = history[-days:] if len(history) > days else history

        if not history:
            return schemas.ReportResponse(
                ergonomic_score=0.0,
                posture_summary="No data available for the selected timeframe.",
                recommendations=["Start a live session to begin tracking your posture."]
            )

        total_tracked = sum(d.total_tracked_seconds for d in history)
        total_good = sum(d.good_posture_seconds for d in history)
        total_severe = sum(d.severe_slouch_seconds for d in history)
        total_fatigue_alerts = sum(d.fatigue_alerts_count for d in history)
        
        ergonomic_score = (total_good / total_tracked) * 100 if total_tracked > 0 else 0.0

        posture_summary = f"Over the last {len(history)} tracked days, you spent {round(ergonomic_score, 1)}% of your time in good posture."

        recommendations = []
        
        # 1. Posture History & Score
        if ergonomic_score > 85:
            recommendations.append("Excellent work! Your posture history indicates you are consistently maintaining healthy posture.")
        elif ergonomic_score > 60:
            recommendations.append("Good effort, but there is room for improvement. Try to focus on keeping your back straight during long sessions.")
        else:
            recommendations.append("Your posture needs attention. Your low ergonomic score suggests you may be straining your back.")

        if total_tracked > 0 and (total_severe / total_tracked) > 0.15:
            recommendations.append("You have a high amount of severe slouching. Consider adopting a stretching routine for your lower back.")

        # 2. Fatigue Detection
        if total_fatigue_alerts > 0:
            freq_msg = "several" if total_fatigue_alerts > 5 else "a few"
            recommendations.append(f"You triggered {total_fatigue_alerts} fatigue alerts this period. Implement the 20-20-20 rule to reduce stiffness and prevent head drooping.")

        # 3. Calibration vs History
        avg_necks = [d.avg_neck_angle for d in history if d.avg_neck_angle is not None]
        overall_avg_neck = sum(avg_necks) / len(avg_necks) if avg_necks else None
        
        from posture_detector.calibration import load_baseline
        baseline = load_baseline(current_user.id)
        
        if baseline and overall_avg_neck is not None:
            baseline_neck = baseline.get("neck_angle")
            if baseline_neck is not None:
                delta = overall_avg_neck - baseline_neck
                if delta > 5.0:
                    recommendations.append(f"Your average neck angle ({overall_avg_neck:.1f}°) has drifted {delta:.1f}° worse than your calibrated baseline ({baseline_neck:.1f}°). Please re-adjust your monitor height to match your initial setup.")
                elif delta < -5.0:
                    recommendations.append(f"Your average neck angle has improved significantly compared to your baseline. Keep up the good work!")
        elif overall_avg_neck is not None and overall_avg_neck > 20:
            recommendations.append("Your average neck angle is quite high. Make sure your screen is at eye level to prevent looking down.")

        return schemas.ReportResponse(
            ergonomic_score=round(ergonomic_score, 1),
            posture_summary=posture_summary,
            recommendations=recommendations
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")
