from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from posture_detector.api.routes import auth, calibration, analysis, sessions, analytics

app = FastAPI(
    title="ERGOAI Posture API",
    description="FastAPI backend for ERGOAI posture monitoring and analytics.",
    version="0.1.0",
)

# Configure CORS for frontend integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev, restrict in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(calibration.router)
app.include_router(analysis.router)
app.include_router(sessions.router)
app.include_router(analytics.router)

@app.get("/")
async def root():
    return {"message": "Welcome to ERGOAI Posture API. Visit /docs for documentation."}
