"""Unified pose detection abstraction over MediaPipe APIs.

Callers create a :class:`PoseDetector`, call :meth:`detect` per frame, and
optionally call :meth:`draw_skeleton` to annotate the frame.  The class hides
whether the legacy ``mp.solutions.pose`` API or the newer MediaPipe Tasks API
is in use.
"""
# pyright: reportMissingImports=false

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any
import urllib.request

import cv2  # type: ignore
import mediapipe as mp  # type: ignore
import numpy as np

from posture_detector.pose.landmarks import extract_landmark_coordinates


# ---------------------------------------------------------------------------
# MediaPipe API detection
# ---------------------------------------------------------------------------

_USE_TASKS_API: bool = not hasattr(mp, "solutions")

# Connections for drawing the skeleton when using the Tasks API (the legacy
# API ships its own ``POSE_CONNECTIONS`` constant).
_POSE_CONNECTIONS: list[tuple[int, int]] = [
    (0, 1), (1, 2), (2, 3), (3, 7), (0, 4), (4, 5), (5, 6), (6, 8),
    (9, 10), (11, 12), (11, 13), (13, 15), (15, 17), (15, 19), (15, 21),
    (17, 19), (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20),
    (11, 23), (12, 24), (23, 24), (23, 25), (25, 27), (27, 29), (29, 31),
    (24, 26), (26, 28), (28, 30), (30, 32), (27, 31), (28, 32),
]


# ---------------------------------------------------------------------------
# Public data structures
# ---------------------------------------------------------------------------


@dataclass
class PoseResult:
    """Normalised output of a single pose-detection call."""

    landmark_coordinates: dict[str, Any] = field(default_factory=dict)
    detected: bool = False


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------


class PoseDetector:
    """Wraps MediaPipe pose detection behind a unified API.

    Usage::

        with PoseDetector() as det:
            result = det.detect(bgr_frame)
            det.draw_skeleton(bgr_frame)
    """

    def __init__(self, model_dir: Path | None = None) -> None:
        self._use_tasks_api = _USE_TASKS_API

        # Internal handles — exactly one branch is initialised.
        self._pose_ctx: Any | None = None
        self._pose_landmarker: Any | None = None
        self._mp_drawing: Any | None = None
        self._mp_pose: Any | None = None

        # Cached raw results for skeleton drawing.
        self._last_legacy_result: Any | None = None
        self._last_tasks_landmarks: Any | None = None

        if not self._use_tasks_api:
            self._mp_pose = mp.solutions.pose
            self._mp_drawing = mp.solutions.drawing_utils
            self._pose_ctx = self._mp_pose.Pose(
                static_image_mode=False,
                model_complexity=0,
                smooth_landmarks=True,
                enable_segmentation=False,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
        else:
            from mediapipe import tasks  # type: ignore
            from mediapipe.tasks.python import vision  # type: ignore

            if model_dir is None:
                # Default: <project_root>/models/mediapipe
                model_dir = Path(__file__).resolve().parents[3] / "models" / "mediapipe"

            model_path = model_dir / "pose_landmarker_lite.task"
            _ensure_pose_model(model_path)

            base_options = tasks.BaseOptions(model_asset_path=str(model_path))
            options = vision.PoseLandmarkerOptions(
                base_options=base_options, num_poses=1,
            )
            self._pose_landmarker = vision.PoseLandmarker.create_from_options(options)

    # ----- public API -----

    def detect(self, frame: np.ndarray) -> PoseResult:
        """Run pose detection on a **BGR** frame.

        Returns a :class:`PoseResult` with normalised landmark coordinates.
        """

        height, width = frame.shape[:2]
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        if not self._use_tasks_api and self._pose_ctx is not None:
            results = self._pose_ctx.process(rgb_frame)
            self._last_legacy_result = results
            self._last_tasks_landmarks = None

            coordinates = extract_landmark_coordinates(results, width, height)
            return PoseResult(
                landmark_coordinates=coordinates,
                detected=results.pose_landmarks is not None,
            )

        if self._use_tasks_api and self._pose_landmarker is not None:
            image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            result = self._pose_landmarker.detect(image)

            landmarks = result.pose_landmarks[0] if result.pose_landmarks else None
            self._last_legacy_result = None
            self._last_tasks_landmarks = landmarks

            # Build a shim so extract_landmark_coordinates works uniformly.
            shim = SimpleNamespace(
                pose_landmarks=SimpleNamespace(landmark=landmarks) if landmarks else None,
            )
            coordinates = extract_landmark_coordinates(shim, width, height)
            return PoseResult(
                landmark_coordinates=coordinates,
                detected=landmarks is not None,
            )

        # Fallback: detector not initialised.
        empty = extract_landmark_coordinates(
            SimpleNamespace(pose_landmarks=None), width, height,
        )
        return PoseResult(landmark_coordinates=empty, detected=False)

    def draw_skeleton(self, frame: np.ndarray) -> None:
        """Overlay the skeleton from the most recent :meth:`detect` call."""

        if not self._use_tasks_api:
            if (
                self._last_legacy_result is not None
                and self._last_legacy_result.pose_landmarks
            ):
                self._mp_drawing.draw_landmarks(
                    frame,
                    self._last_legacy_result.pose_landmarks,
                    self._mp_pose.POSE_CONNECTIONS,
                )
        else:
            if self._last_tasks_landmarks is not None:
                _draw_pose_skeleton(
                    frame, self._last_tasks_landmarks, _POSE_CONNECTIONS,
                )

    # ----- resource management -----

    def close(self) -> None:
        """Release MediaPipe resources."""

        if self._pose_ctx is not None:
            self._pose_ctx.close()
            self._pose_ctx = None
        if self._pose_landmarker is not None:
            self._pose_landmarker.close()
            self._pose_landmarker = None

    def __enter__(self) -> PoseDetector:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _ensure_pose_model(model_path: Path) -> None:
    """Download the MediaPipe pose landmark model if it is missing."""

    if model_path.exists():
        return

    model_path.parent.mkdir(parents=True, exist_ok=True)
    model_url = (
        "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
        "pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
    )
    urllib.request.urlretrieve(model_url, model_path)


def _draw_pose_skeleton(
    frame: np.ndarray,
    landmarks: list,
    connections: list[tuple[int, int]],
) -> None:
    """Draw pose connections and landmark points on *frame*."""

    height, width = frame.shape[:2]
    for start_idx, end_idx in connections:
        start = landmarks[start_idx]
        end = landmarks[end_idx]
        start_pt = (int(start.x * width), int(start.y * height))
        end_pt = (int(end.x * width), int(end.y * height))
        cv2.line(frame, start_pt, end_pt, (0, 255, 0), 2)

    for lm in landmarks:
        pt = (int(lm.x * width), int(lm.y * height))
        cv2.circle(frame, pt, 3, (255, 255, 255), -1)
