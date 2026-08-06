import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from posture_detector.api import schemas, dependencies

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])

DEFAULT_EXPORT_DIR = Path(__file__).resolve().parents[4] / "data" / "exports"
DEFAULT_LIVE_SESSION = DEFAULT_EXPORT_DIR / "live_session.json"

from posture_detector.storage.queries import get_live_snapshot

@router.get("/live", response_model=schemas.LiveSessionSnapshot)
async def get_live_session(
    current_user: schemas.UserResponse = Depends(dependencies.get_current_user)
):
    try:
        data = get_live_snapshot(current_user.id)
        if not data:
            raise HTTPException(status_code=404, detail="Live session snapshot not found.")
        return schemas.LiveSessionSnapshot(**data)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error reading snapshot: {str(e)}")
