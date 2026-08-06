from fastapi import APIRouter, Depends, HTTPException
from posture_detector.api import schemas, dependencies
from posture_detector.session import PostureSession

router = APIRouter(prefix="/api/v1/calibration", tags=["calibration"])

@router.get("/", response_model=schemas.CalibrationResponse)
async def get_calibration(
    session: PostureSession = Depends(dependencies.get_active_session)
):
    """Get the active baseline from the session (loaded via user_id)."""
    baseline = session.baseline
    if not baseline or "neck_angle" not in baseline:
        raise HTTPException(status_code=404, detail="No calibration found for user")
        
    return schemas.CalibrationResponse(
        neck_angle=baseline["neck_angle"],
        back_angle=baseline["back_angle"],
        neck_good_delta=baseline.get("neck_good_delta", 5.0),
        neck_severe_delta=baseline.get("neck_severe_delta", 15.0),
        back_good_delta=baseline.get("back_good_delta", 4.0),
        back_severe_delta=baseline.get("back_severe_delta", 10.0),
    )

@router.post("/start")
async def start_calibration(
    session: PostureSession = Depends(dependencies.get_active_session)
):
    session.start_calibration()
    return {"message": "Calibration started."}
