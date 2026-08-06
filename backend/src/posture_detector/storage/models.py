from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from posture_detector.storage.database import Base
from datetime import datetime, timezone

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)  # Nullable for Google Auth users
    auth_provider = Column(String, default="local", nullable=False) # 'local' or 'google'


class DailyPostureSummary(Base):
    __tablename__ = "daily_posture_summary"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    date = Column(Date, index=True, nullable=False)
    good_posture_seconds = Column(Float, default=0.0)
    mild_slouch_seconds = Column(Float, default=0.0)
    severe_slouch_seconds = Column(Float, default=0.0)
    total_tracked_seconds = Column(Float, default=0.0)
    good_posture_count = Column(Integer, default=0)
    mild_slouch_count = Column(Integer, default=0)
    severe_slouch_count = Column(Integer, default=0)
    avg_neck_angle = Column(Float, nullable=True)
    avg_back_angle = Column(Float, nullable=True)
    fatigue_alerts_count = Column(Integer, default=0)


class LiveSessionSnapshot(Base):
    __tablename__ = "live_session_snapshot"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, index=True, nullable=False)
    timestamp = Column(String, nullable=False)
    current_posture_label = Column(String, nullable=False)
    neck_angle = Column(Float, nullable=True)
    back_angle = Column(Float, nullable=True)
    good_posture_percent = Column(Float, default=0.0)
    bad_posture_percent = Column(Float, default=0.0)
    bad_posture_seconds = Column(Float, default=0.0)
    good_posture_seconds = Column(Float, default=0.0)
    mild_slouch_seconds = Column(Float, default=0.0)
    severe_slouch_seconds = Column(Float, default=0.0)
    total_tracked_seconds = Column(Float, default=0.0)
    good_posture_count = Column(Integer, default=0)
    mild_slouch_count = Column(Integer, default=0)
    severe_slouch_count = Column(Integer, default=0)
    fatigue_alerts_count = Column(Integer, default=0)


class CalibrationBaseline(Base):
    __tablename__ = "calibration_baseline"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, index=True, nullable=False)
    timestamp = Column(String, nullable=False)
    neck_angle = Column(Float, nullable=False)
    back_angle = Column(Float, nullable=False)
    neck_good_delta = Column(Float, nullable=True, default=5.0)
    neck_severe_delta = Column(Float, nullable=True, default=15.0)
    back_good_delta = Column(Float, nullable=True, default=4.0)
    back_severe_delta = Column(Float, nullable=True, default=10.0)

