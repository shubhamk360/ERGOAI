"""Open the default webcam and show the live video stream.

This is a minimal OpenCV demo that can serve as the starting point for the
posture monitoring pipeline.
"""
# pyright: reportMissingImports=false
# pyright: reportPossiblyUnboundVariable=false

from datetime import datetime, timezone
from pathlib import Path
import sys
import time
from types import SimpleNamespace
import urllib.request

import cv2  # type: ignore
import mediapipe as mp  # type: ignore


# Add the source directory to the import path so the reusable helper can be used.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# ruff: noqa: E402
from posture_detector.pose.landmarks import extract_landmark_coordinates  # type: ignore
from posture_detector.alerts import update_break_reminder, update_posture_alert  # type: ignore
from posture_detector.calibration import load_baseline, save_baseline  # type: ignore
from posture_detector.classification import classify_posture, classify_posture_with_baseline  # type: ignore
from posture_detector.geometry import calculate_back_angle, calculate_neck_angle  # type: ignore
from posture_detector.metrics import PostureStatisticsTracker  # type: ignore
from posture_detector.storage import write_daily_posture_summary, write_live_session_snapshot  # type: ignore


USE_TASKS_API = not hasattr(mp, "solutions")

# Create MediaPipe helper objects once so they can be reused for every frame.
if not USE_TASKS_API:
    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils
else:
    from mediapipe import tasks  # type: ignore
    from mediapipe.tasks.python import vision  # type: ignore

    POSE_CONNECTIONS = [
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 7),
        (0, 4),
        (4, 5),
        (5, 6),
        (6, 8),
        (9, 10),
        (11, 12),
        (11, 13),
        (13, 15),
        (15, 17),
        (15, 19),
        (15, 21),
        (17, 19),
        (12, 14),
        (14, 16),
        (16, 18),
        (16, 20),
        (16, 22),
        (18, 20),
        (11, 23),
        (12, 24),
        (23, 24),
        (23, 25),
        (25, 27),
        (27, 29),
        (29, 31),
        (24, 26),
        (26, 28),
        (28, 30),
        (30, 32),
        (27, 31),
        (28, 32),
    ]


def ensure_pose_model(model_path: Path) -> None:
    # Download the MediaPipe pose landmark model if it is missing.
    if model_path.exists():
        return

    model_path.parent.mkdir(parents=True, exist_ok=True)
    model_url = (
        "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
        "pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
    )
    urllib.request.urlretrieve(model_url, model_path)


def draw_pose_skeleton(frame: cv2.typing.MatLike, landmarks: list, connections: list[tuple[int, int]]) -> None:
    # Draw pose connections and landmark points on the frame.
    height, width = frame.shape[:2]
    for start_index, end_index in connections:
        start = landmarks[start_index]
        end = landmarks[end_index]
        start_point = (int(start.x * width), int(start.y * height))
        end_point = (int(end.x * width), int(end.y * height))
        cv2.line(frame, start_point, end_point, (0, 255, 0), 2)

    for landmark in landmarks:
        point = (int(landmark.x * width), int(landmark.y * height))
        cv2.circle(frame, point, 3, (255, 255, 255), -1)


class _FrameContext:
    """Mutable state that is shared across frames in the main loop.

    Grouping these fields avoids passing dozens of individual variables
    between the frame-processing helpers and the main loop.
    """

    def __init__(self, baseline_path: Path) -> None:
        self.bad_posture_start_time: float | None = None
        self.sitting_start_time: float | None = None
        self.posture_stats = PostureStatisticsTracker()
        self.last_live_write: float = 0.0
        self.live_session_path = PROJECT_ROOT / "data" / "exports" / "live_session.json"
        self.baseline_path = baseline_path
        self.baseline = load_baseline(baseline_path)
        self.calibration_active: bool = False
        self.calibration_start_time: float | None = None
        self.calibration_neck_sum: float = 0.0
        self.calibration_back_sum: float = 0.0
        self.calibration_count: int = 0
        self.calibration_duration: float = 10.0


def _classify_frame(
    landmark_coordinates: dict,
    baseline: dict | None,
) -> tuple[str, float | None, float | None]:
    """Return (posture_label, neck_angle, back_angle) for one frame."""

    neck_angle = calculate_neck_angle(landmark_coordinates)
    back_angle = calculate_back_angle(landmark_coordinates)

    posture_label = "No pose detected"
    if neck_angle is not None and back_angle is not None:
        if baseline and "neck_angle" in baseline and "back_angle" in baseline:
            posture_label = classify_posture_with_baseline(
                neck_angle,
                back_angle,
                baseline["neck_angle"],
                baseline["back_angle"],
            )
        else:
            posture_label = classify_posture(neck_angle, back_angle)

    return posture_label, neck_angle, back_angle


def _process_frame(
    ctx: _FrameContext,
    posture_label: str,
    neck_angle: float | None,
    back_angle: float | None,
) -> tuple[str, bool, str | None, bool, str | None, str | None]:
    """Run calibration, alerts, stats tracking, and live snapshot writing.

    Returns (posture_label, show_warning, warning_message,
             show_break, break_message, calibration_message).
    """

    frame_time = time.monotonic()

    # --- Calibration ---
    calibration_message = None
    if ctx.calibration_active:
        if ctx.calibration_start_time is None:
            ctx.calibration_start_time = frame_time

        if neck_angle is not None and back_angle is not None:
            ctx.calibration_neck_sum += neck_angle
            ctx.calibration_back_sum += back_angle
            ctx.calibration_count += 1

        elapsed_time = frame_time - ctx.calibration_start_time
        progress = min(elapsed_time / ctx.calibration_duration, 1.0)
        calibration_message = f"Calibrating... {int(progress * 100)}%"

        if elapsed_time >= ctx.calibration_duration:
            if ctx.calibration_count > 0:
                ctx.baseline = save_baseline(
                    ctx.baseline_path,
                    ctx.calibration_neck_sum / ctx.calibration_count,
                    ctx.calibration_back_sum / ctx.calibration_count,
                )
                calibration_message = "Calibration saved"
            else:
                calibration_message = "Calibration failed: no pose"

            ctx.calibration_active = False
            ctx.calibration_start_time = None
            ctx.calibration_neck_sum = 0.0
            ctx.calibration_back_sum = 0.0
            ctx.calibration_count = 0

    if ctx.calibration_active:
        posture_label = "Calibrating"

    # --- Alerts ---
    show_warning = False
    warning_message = None
    show_break = False
    break_message = None
    if not ctx.calibration_active:
        ctx.sitting_start_time, show_break, break_message = update_break_reminder(
            posture_label,
            ctx.sitting_start_time,
            frame_time,
        )
        ctx.bad_posture_start_time, show_warning, warning_message = update_posture_alert(
            posture_label,
            ctx.bad_posture_start_time,
            frame_time,
        )

        # Track how long each posture label has been held.
        ctx.posture_stats.update(posture_label, frame_time)
    else:
        ctx.sitting_start_time = None

    # --- Live session snapshot ---
    if not ctx.calibration_active and frame_time - ctx.last_live_write >= 1.0:
        _write_live_snapshot(ctx, posture_label, neck_angle, back_angle)
        ctx.last_live_write = frame_time

    return posture_label, show_warning, warning_message, show_break, break_message, calibration_message


def _write_live_snapshot(
    ctx: _FrameContext,
    posture_label: str,
    neck_angle: float | None,
    back_angle: float | None,
) -> None:
    """Build and persist a live session JSON snapshot."""

    summary = ctx.posture_stats.build_daily_summary()
    total_seconds = summary["total_tracked_seconds"]
    bad_seconds = summary["mild_slouch_seconds"] + summary["severe_slouch_seconds"]
    good_percent = (summary["good_posture_seconds"] / total_seconds) * 100 if total_seconds else 0.0
    bad_percent = (bad_seconds / total_seconds) * 100 if total_seconds else 0.0

    summary.update(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "current_posture_label": posture_label,
            "neck_angle": round(neck_angle, 1) if neck_angle is not None else None,
            "back_angle": round(back_angle, 1) if back_angle is not None else None,
            "good_posture_percent": round(good_percent, 2),
            "bad_posture_percent": round(bad_percent, 2),
            "bad_posture_seconds": round(bad_seconds, 2),
        }
    )
    write_live_session_snapshot(ctx.live_session_path, summary)


def _draw_hud(
    frame: cv2.typing.MatLike,
    posture_label: str,
    neck_angle: float | None,
    back_angle: float | None,
    show_warning: bool,
    warning_message: str | None,
    show_break: bool,
    break_message: str | None,
    calibration_message: str | None,
) -> None:
    """Overlay posture information text onto the video frame."""

    cv2.putText(frame, f"Posture: {posture_label}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
    if neck_angle is not None:
        cv2.putText(frame, f"Neck angle: {neck_angle:.1f}", (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    if back_angle is not None:
        cv2.putText(frame, f"Back angle: {back_angle:.1f}", (20, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    if show_warning and warning_message:
        cv2.putText(frame, warning_message, (20, 145), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    if show_break and break_message:
        cv2.putText(frame, break_message, (20, 175), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 140, 255), 2)
    if calibration_message:
        cv2.putText(frame, calibration_message, (20, 205), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)


def _handle_key_press(key: int, ctx: _FrameContext, frame_time: float) -> bool:
    """Process a key press. Return True when the loop should exit."""

    if key == ord("q"):
        return True

    if key == ord("c"):
        ctx.calibration_active = True
        ctx.calibration_start_time = frame_time
        ctx.calibration_neck_sum = 0.0
        ctx.calibration_back_sum = 0.0
        ctx.calibration_count = 0
        ctx.sitting_start_time = None

    return False


def _finalize_session(ctx: _FrameContext) -> None:
    """Write the final daily summary and session snapshot after the loop ends."""

    ctx.posture_stats.finalize(time.monotonic())
    write_daily_posture_summary(
        PROJECT_ROOT / "data" / "exports" / f"posture_daily_stats_{ctx.posture_stats.day.isoformat()}.csv",
        ctx.posture_stats.build_daily_summary(),
    )

    final_summary = ctx.posture_stats.build_daily_summary()
    total_seconds = final_summary["total_tracked_seconds"]
    bad_seconds = final_summary["mild_slouch_seconds"] + final_summary["severe_slouch_seconds"]
    final_summary.update(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "current_posture_label": "Session ended",
            "neck_angle": None,
            "back_angle": None,
            "good_posture_percent": round(
                (final_summary["good_posture_seconds"] / total_seconds) * 100 if total_seconds else 0.0,
                2,
            ),
            "bad_posture_percent": round((bad_seconds / total_seconds) * 100 if total_seconds else 0.0, 2),
            "bad_posture_seconds": round(bad_seconds, 2),
        }
    )
    write_live_session_snapshot(ctx.live_session_path, final_summary)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main() -> None:
    # Create a video capture object for the default webcam.
    camera = cv2.VideoCapture(0)
    baseline_path = PROJECT_ROOT / "data" / "exports" / "calibration_baseline.json"
    ctx = _FrameContext(baseline_path)

    # Stop immediately if the webcam cannot be opened.
    if not camera.isOpened():
        print("Error: Could not open webcam.")
        return

    if not USE_TASKS_API:
        # Create a MediaPipe Pose instance that will detect body landmarks.
        with mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        ) as pose:
            while True:
                success, frame = camera.read()
                if not success:
                    print("Error: Could not read frame from webcam.")
                    break

                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = pose.process(rgb_frame)

                landmark_coordinates = extract_landmark_coordinates(results, frame.shape[1], frame.shape[0])
                posture_label, neck_angle, back_angle = _classify_frame(landmark_coordinates, ctx.baseline)
                posture_label, show_warning, warning_message, show_break, break_message, calibration_message = (
                    _process_frame(ctx, posture_label, neck_angle, back_angle)
                )

                # Draw the pose skeleton using the legacy API.
                if results.pose_landmarks:
                    mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

                _draw_hud(frame, posture_label, neck_angle, back_angle, show_warning, warning_message, show_break, break_message, calibration_message)
                cv2.imshow("MediaPipe Pose Webcam", frame)

                key = cv2.waitKey(1) & 0xFF
                if _handle_key_press(key, ctx, time.monotonic()):
                    break
    else:
        model_path = PROJECT_ROOT / "models" / "mediapipe" / "pose_landmarker_lite.task"
        ensure_pose_model(model_path)
        base_options = tasks.BaseOptions(model_asset_path=str(model_path))
        options = vision.PoseLandmarkerOptions(base_options=base_options, num_poses=1)
        pose_landmarker = vision.PoseLandmarker.create_from_options(options)

        while True:
            success, frame = camera.read()
            if not success:
                print("Error: Could not read frame from webcam.")
                break

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            result = pose_landmarker.detect(image)

            # Normalize the tasks result so existing utilities can reuse it.
            pose_landmarks = result.pose_landmarks[0] if result.pose_landmarks else None
            fake_results = SimpleNamespace(
                pose_landmarks=SimpleNamespace(landmark=pose_landmarks) if pose_landmarks else None
            )

            landmark_coordinates = extract_landmark_coordinates(fake_results, frame.shape[1], frame.shape[0])
            posture_label, neck_angle, back_angle = _classify_frame(landmark_coordinates, ctx.baseline)
            posture_label, show_warning, warning_message, show_break, break_message, calibration_message = (
                _process_frame(ctx, posture_label, neck_angle, back_angle)
            )

            # Draw the pose skeleton using the Tasks API fallback.
            if pose_landmarks:
                draw_pose_skeleton(frame, pose_landmarks, POSE_CONNECTIONS)

            _draw_hud(frame, posture_label, neck_angle, back_angle, show_warning, warning_message, show_break, break_message, calibration_message)
            cv2.imshow("MediaPipe Pose Webcam", frame)

            key = cv2.waitKey(1) & 0xFF
            if _handle_key_press(key, ctx, time.monotonic()):
                break

    # Release the webcam so other applications can use it.
    camera.release()

    _finalize_session(ctx)

    # Close all OpenCV windows created by this script.
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()