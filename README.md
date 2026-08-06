# ERGOAI

ERGOAI is a real-time, AI-powered ergonomic posture tracking web application. It uses a webcam to monitor your posture continuously, alerting you when you slouch, and tracking your daily ergonomic health.

The project is split into a modern React frontend and a FastAPI backend powered by OpenCV and MediaPipe.

## Project Structure

- `/frontend` - The Vite + React 19 web application.
- `/backend` - The FastAPI + Python computer vision and telemetry server.

## Quick Start

To run ERGOAI locally, you need to start both the backend server and the frontend development server.

### 1. Backend Setup

The backend handles the video processing, user authentication, and data storage.

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# Initialize the empty database
alembic upgrade head

# Start the server
python3 -m uvicorn posture_detector.api.main:app --host 0.0.0.0 --port 8000 --reload
```
*Note: A local SQLite database is generated at `backend/data/posture.db`. This file is ignored by Git to protect user data.*

### 2. Frontend Setup

The frontend provides the user interface and captures the webcam feed.

```bash
# Open a new terminal window
cd frontend
npm install

# Start the development server
npm run dev
```

Visit `http://localhost:5173` in your browser to access the application.

## Technologies Used

- **Frontend:** React 19, TypeScript, Vite, TailwindCSS, Recharts.
- **Backend:** Python 3.13, FastAPI, SQLAlchemy, Alembic.
- **Computer Vision:** OpenCV, MediaPipe Pose Estimation, Scikit-Learn (Random Forest Classification).
- **Authentication:** JWT (JSON Web Tokens) and Google OAuth2.

## Key Features

- **Real-Time Tracking:** High-frequency WebSocket telemetry (~6.6 FPS) for instantaneous posture feedback.
- **Dynamic Calibration:** Establish a personal neutral posture baseline before starting a session.
- **Smart Notifications:** Native desktop notifications and Web Audio API sound alerts with customizable throttling to prevent alert fatigue.
- **Analytics Dashboard:** Daily, weekly, and monthly tracking of ergonomic health and improvement scores.

## Contributing

1. Ensure the backend tests pass by running `pytest` in the `/backend` directory.
2. Please do not commit any `.env` files or the `posture.db` database.
