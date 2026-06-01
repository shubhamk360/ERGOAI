# Posture Detection with OpenCV + MediaPipe Pose

Modular Python project for real-time posture analysis using OpenCV for capture/rendering and MediaPipe Pose for landmark detection.

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
