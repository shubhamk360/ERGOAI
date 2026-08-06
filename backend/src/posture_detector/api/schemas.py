from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class GoogleToken(BaseModel):
    token: str

class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True

class UserInDB(UserResponse):
    hashed_password: str

class CalibrationResponse(BaseModel):
    neck_angle: float
    back_angle: float
    neck_good_delta: Optional[float] = 5.0
    neck_severe_delta: Optional[float] = 15.0
    back_good_delta: Optional[float] = 4.0
    back_severe_delta: Optional[float] = 10.0

class FrameAnalysisResponse(BaseModel):
    posture_label: str
    neck_angle: Optional[float] = None
    back_angle: Optional[float] = None
    show_warning: bool
    warning_message: Optional[str] = None
    show_break: bool
    break_message: Optional[str] = None
    show_fatigue: bool = False
    fatigue_message: Optional[str] = None
    calibration_message: Optional[str] = None

class DailySummary(BaseModel):
    date: str
    good_posture_seconds: float
    mild_slouch_seconds: float
    severe_slouch_seconds: float
    total_tracked_seconds: float
    good_posture_count: int
    mild_slouch_count: int
    severe_slouch_count: int
    good_posture_percent: float
    bad_posture_percent: float
    bad_posture_seconds: float
    avg_neck_angle: Optional[float] = None
    avg_back_angle: Optional[float] = None
    fatigue_alerts_count: int = 0

class LiveSessionSnapshot(BaseModel):
    timestamp: str
    current_posture_label: str
    neck_angle: Optional[float] = None
    back_angle: Optional[float] = None
    good_posture_percent: float
    bad_posture_percent: float
    bad_posture_seconds: float
    good_posture_seconds: float
    mild_slouch_seconds: float
    severe_slouch_seconds: float
    total_tracked_seconds: float
    good_posture_count: int
    mild_slouch_count: int
    severe_slouch_count: int
    fatigue_alerts_count: int = 0

class ReportResponse(BaseModel):
    ergonomic_score: float
    posture_summary: str
    recommendations: List[str]
