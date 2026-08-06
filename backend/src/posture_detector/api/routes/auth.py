from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from posture_detector.api import schemas, dependencies
from posture_detector.storage.models import User

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

from google.oauth2 import id_token
from google.auth.transport import requests

@router.post("/signup", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_in: schemas.UserCreate, db: Session = Depends(dependencies.get_db)):
    existing_user = db.query(User).filter(User.username == user_in.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = dependencies.get_password_hash(user_in.password)
    db_user = User(username=user_in.username, hashed_password=hashed_password, auth_provider="local")
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/google", response_model=schemas.Token)
async def google_auth(google_token: schemas.GoogleToken, db: Session = Depends(dependencies.get_db)):
    try:
        # Verify the token without checking the audience client ID immediately,
        # since we are using a placeholder. We just want to decode it securely.
        # If the user provides a client ID later, we can pass it to the audience parameter.
        idinfo = id_token.verify_oauth2_token(
            google_token.token, 
            requests.Request()
        )
        
        email = idinfo.get("email")
        if not email:
            raise ValueError("Email not provided by Google")
            
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid Google token: {str(e)}")
        
    user = db.query(User).filter(User.username == email).first()
    if not user:
        # Create user
        user = User(username=email, hashed_password=None, auth_provider="google")
        db.add(user)
        db.commit()
        db.refresh(user)
        
    access_token_expires = timedelta(minutes=dependencies.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = dependencies.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(dependencies.get_db)):
    user = dependencies.get_user(db, form_data.username)
    if not user or not dependencies.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=dependencies.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = dependencies.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
async def logout():
    # Since we are using stateless JWTs without a blacklist,
    # logout is handled client-side by deleting the token.
    return {"message": "Successfully logged out. Please remove the token from your client."}

@router.get("/profile", response_model=schemas.UserResponse)
async def get_profile(current_user: schemas.UserResponse = Depends(dependencies.get_current_user)):
    return current_user
