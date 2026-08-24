# Posture Detection with OpenCV + MediaPipe Pose

Modular Python project for real-time posture analysis using OpenCV for capture/rendering and MediaPipe Pose for landmark detection.

## Local Setup & Initialization

To get the backend running locally, follow these steps to initialize your virtual environment and local database. **Note:** You must have a PostgreSQL instance running locally or hosted remotely, and provide its connection string.

1. **Install Dependencies**
   ```bash
   # From the root of the project
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e ./backend
   ```

2. **Initialize the Database**
   We use Alembic for database migrations. To generate the correct schema on your PostgreSQL instance, set your `DATABASE_URL` (e.g. in a `.env` file) and run:
   ```bash
   cd backend
   export DATABASE_URL="postgresql://localhost/ergoai"
   alembic upgrade head
   ```

3. **Start the Development Server**
   ```bash
   # Run the FastAPI server
   python3 -m uvicorn posture_detector.api.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## Core Features

- Posture classification
- Neck angle calculation
- Shoulder imbalance detection
- Alert system
- Statistics dashboard

## Project Structure

```text
posture_detection_opencv_mediapipe/
├── assets/
│   ├── images/
│   ├── fonts/
│   └── icons/
├── data/
│   ├── exports/
│   ├── processed/
│   ├── raw/
│   ├── recordings/
│   ├── reference_images/
│   └── sample_videos/
├── docs/
│   ├── api/
│   ├── architecture/
│   └── reports/
├── experiments/
├── logs/
├── models/
│   ├── checkpoints/
│   ├── exported/
│   └── metrics/
├── notebooks/
├── scripts/
│   ├── demo/
│   ├── evaluate/
│   ├── infer/
│   └── train/
├── src/
│   └── posture_detector/
│       ├── alerts/
│       ├── capture/
│       ├── classification/
│       ├── config/
│       ├── dashboard/
│       ├── geometry/
│       ├── metrics/
│       ├── pose/
│       ├── preprocessing/
│       ├── storage/
│       ├── tracking/
│       ├── ui/
│       └── utils/
└── tests/
    ├── e2e/
    ├── integration/
    │   ├── alerts/
    │   └── pipeline/
    └── unit/
        ├── alerts/
        ├── classification/
        ├── geometry/
        └── pose/
```

## Module Responsibilities

- `capture`: camera/video input and frame preprocessing
- `pose`: MediaPipe Pose landmark extraction and pose tracking
- `geometry`: neck angle, shoulder slope, and other posture metrics
- `classification`: rules or ML logic for posture state labeling
- `alerts`: thresholding, cooldowns, and user notifications
- `dashboard`: statistics, trends, and session summaries
- `config`: constants, thresholds, and runtime settings
- `utils`: shared helpers and visualization primitives

## Intended Flow

1. Capture a frame from webcam or video.
2. Extract pose landmarks with MediaPipe Pose.
3. Compute neck angle and shoulder imbalance metrics.
4. Classify posture state.
5. Trigger alerts when thresholds are exceeded.
6. Update statistics for the dashboard.
