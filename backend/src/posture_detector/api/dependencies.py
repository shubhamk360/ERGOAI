import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
import bcrypt
from pydantic import ValidationError

from posture_detector.api import schemas
from posture_detector.session import PostureSession
from posture_detector.config import PostureConfig

SECRET_KEY = os.getenv("SECRET_KEY", "development_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str | None) -> bool:
    if not hashed_password:
        return False
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

from posture_detector.storage.database import SessionLocal
from posture_detector.storage.models import User

# In-memory storage of active PostureSessions per user
active_sessions: Dict[int, PostureSession] = {}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_user(db, username: str):
    return db.query(User).filter(User.username == username).first()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme)) -> schemas.UserResponse:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except jwt.InvalidTokenError:
        raise credentials_exception
    except ValidationError:
        raise credentials_exception
        
    db = SessionLocal()
    try:
        user = get_user(db, username=token_data.username)
        if user is None:
            raise credentials_exception
        return schemas.UserResponse.model_validate(user)
    finally:
        db.close()

def get_current_user_from_token(token: str) -> Optional[schemas.UserResponse]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        token_data = schemas.TokenData(username=username)
    except Exception:
        return None
        
    db = SessionLocal()
    try:
        user = get_user(db, username=token_data.username)
        if user is None:
            return None
        return schemas.UserResponse.model_validate(user)
    finally:
        db.close()

from pathlib import Path
DEFAULT_EXPORT_DIR = Path(__file__).resolve().parents[4] / "data" / "exports"

def get_active_session_by_id(user_id: int) -> PostureSession:
    """Retrieve or create the active PostureSession for a user ID."""
    if user_id not in active_sessions:
        config = PostureConfig()
        session = PostureSession(config=config, export_dir=DEFAULT_EXPORT_DIR)
        session._user_id = user_id
        
        # Hydrate the session's PostureStatisticsTracker with today's existing DB data
        from posture_detector.storage.database import SessionLocal
        from posture_detector.storage.models import DailyPostureSummary
        with SessionLocal() as db:
            today_record = db.query(DailyPostureSummary).filter(
                DailyPostureSummary.user_id == user_id,
                DailyPostureSummary.date == datetime.now(timezone.utc).date()
            ).first()
            if today_record:
                session.posture_stats.posture_durations["Good posture"] = today_record.good_posture_seconds or 0.0
                session.posture_stats.posture_durations["Mild slouch"] = today_record.mild_slouch_seconds or 0.0
                session.posture_stats.posture_durations["Severe slouch"] = today_record.severe_slouch_seconds or 0.0
                session.posture_stats.posture_counts["Good posture"] = today_record.good_posture_count or 0
                session.posture_stats.posture_counts["Mild slouch"] = today_record.mild_slouch_count or 0
                session.posture_stats.posture_counts["Severe slouch"] = today_record.severe_slouch_count or 0
                session.posture_stats.fatigue_alerts_count = today_record.fatigue_alerts_count or 0

        session.open(camera_index=None)
        active_sessions[user_id] = session
    return active_sessions[user_id]

def get_active_session(current_user: schemas.UserResponse = Depends(get_current_user)) -> PostureSession:
    """Dependency to retrieve or create the active PostureSession for the user."""
    return get_active_session_by_id(current_user.id)

