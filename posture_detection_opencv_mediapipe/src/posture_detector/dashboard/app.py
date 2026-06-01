"""Streamlit dashboard for posture monitoring statistics."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any
import sys
import time
import threading

import numpy as np
import pandas as pd
import streamlit as st
import cv2
import mediapipe as mp


# Add the source directory to the import path so the dashboard can run directly.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# ruff: noqa: E402
from posture_detector.pose.landmarks import extract_landmark_coordinates
from posture_detector.alerts import update_break_reminder, update_posture_alert
from posture_detector.storage.csv_export import write_daily_posture_summary
from posture_detector.calibration import load_baseline
from posture_detector.classification import classify_posture, classify_posture_with_baseline
from posture_detector.geometry import calculate_back_angle, calculate_neck_angle
from posture_detector.metrics import PostureStatisticsTracker
from posture_detector.storage import write_live_session_snapshot


DEFAULT_EXPORT_DIR = PROJECT_ROOT / "data" / "exports"
DEFAULT_LIVE_SESSION = DEFAULT_EXPORT_DIR / "live_session.json"

# Detect whether the legacy mp.solutions API is available.
_USE_TASKS_API = not hasattr(mp, "solutions")

if _USE_TASKS_API:
    from mediapipe import tasks
    from mediapipe.tasks.python import vision
    import urllib.request

    _POSE_CONNECTIONS = [
        (0, 1), (1, 2), (2, 3), (3, 7), (0, 4), (4, 5), (5, 6), (6, 8),
        (9, 10), (11, 12), (11, 13), (13, 15), (15, 17), (15, 19), (15, 21),
        (17, 19), (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20),
        (11, 23), (12, 24), (23, 24), (23, 25), (25, 27), (27, 29), (29, 31),
        (24, 26), (26, 28), (28, 30), (30, 32), (27, 31), (28, 32),
    ]


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
    frame: np.ndarray, landmarks: list, connections: list[tuple[int, int]]
) -> None:
    """Draw pose connections and landmark points on the frame."""
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


@st.cache_data(show_spinner=False)
def load_daily_history(export_dir: str) -> pd.DataFrame:
    """Load all daily posture CSV files and aggregate them by date."""

    path = Path(export_dir)
    csv_files = sorted(path.glob("posture_daily_stats_*.csv"))

    if not csv_files:
        return pd.DataFrame(
            columns=[
                "date",
                "good_posture_seconds",
                "mild_slouch_seconds",
                "severe_slouch_seconds",
                "total_tracked_seconds",
                "good_posture_count",
                "mild_slouch_count",
                "severe_slouch_count",
                "good_posture_percent",
                "bad_posture_percent",
                "bad_posture_seconds",
            ]
        )

    frames = []
    for csv_file in csv_files:
        frame = pd.read_csv(csv_file)
        if not frame.empty:
            frames.append(frame)

    if not frames:
        return pd.DataFrame()

    history = pd.concat(frames, ignore_index=True)
    history["date"] = pd.to_datetime(history["date"])

    aggregated = (
        history.groupby("date", as_index=False)[
            [
                "good_posture_seconds",
                "mild_slouch_seconds",
                "severe_slouch_seconds",
                "total_tracked_seconds",
                "good_posture_count",
                "mild_slouch_count",
                "severe_slouch_count",
            ]
        ]
        .sum()
        .sort_values("date")
    )

    aggregated["good_posture_percent"] = aggregated.apply(
        lambda row: round((row["good_posture_seconds"] / row["total_tracked_seconds"]) * 100, 2)
        if row["total_tracked_seconds"]
        else 0.0,
        axis=1,
    )
    aggregated["bad_posture_seconds"] = aggregated["mild_slouch_seconds"] + aggregated["severe_slouch_seconds"]
    aggregated["bad_posture_percent"] = aggregated.apply(
        lambda row: round((row["bad_posture_seconds"] / row["total_tracked_seconds"]) * 100, 2)
        if row["total_tracked_seconds"]
        else 0.0,
        axis=1,
    )
    aggregated["date_label"] = aggregated["date"].dt.strftime("%Y-%m-%d")

    return aggregated


def list_daily_exports(export_dir: str) -> list[Path]:
    """Return matching daily export files for debugging and discovery."""

    path = Path(export_dir)
    if not path.exists():
        return []
    return sorted(path.glob("posture_daily_stats_*.csv"))


def _render_metric_card(title: str, value: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">{title}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def load_live_session_snapshot(snapshot_path: str) -> dict | None:
    """Load the latest live session snapshot from JSON."""

    path = Path(snapshot_path)
    if not path.exists():
        return None

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


# ---------------------------------------------------------------------------
# Thread-safe camera worker with integrated pose detection
# ---------------------------------------------------------------------------

# Shared state between the camera worker thread and the Streamlit main thread.
@st.cache_resource
def get_camera_state() -> tuple[dict[str, Any], threading.Lock]:
    """Persist camera state and lock across Streamlit reruns."""
    return {
        "running": False,
        "frame": None,
        "error": None,
        "posture_label": None,
        "neck_angle": None,
        "back_angle": None,
    }, threading.Lock()


def _camera_worker() -> None:
    """Capture frames, run pose detection, and classify posture in background.

    Writes results to the module-level ``_camera_shared`` dict which is
    guarded by ``_camera_lock``.  The main Streamlit thread reads from
    this dict on every render cycle.
    """

    _camera_shared, _camera_lock = get_camera_state()

    print("[Worker] Starting camera worker thread...")
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        print("[Worker] Failed to open camera!")
        with _camera_lock:
            _camera_shared["error"] = "Could not open webcam. Check camera permissions."
            _camera_shared["running"] = False
        return

    with _camera_lock:
        _camera_shared["error"] = None

    # Load calibration baseline once at start.
    baseline_path = PROJECT_ROOT / "data" / "exports" / "calibration_baseline.json"
    baseline = load_baseline(baseline_path)

    # Set up posture tracking state.
    posture_stats = PostureStatisticsTracker()
    bad_posture_start_time: float | None = None
    sitting_start_time: float | None = None
    last_live_write: float = 0.0
    live_session_path = DEFAULT_LIVE_SESSION

    # Generate a unique ID for this specific webcam session so it doesn't overwrite earlier sessions today
    session_id = datetime.now(timezone.utc).strftime("%H%M%S")

    # Set up MediaPipe pose detector.
    pose_ctx = None
    pose_landmarker = None

    if not _USE_TASKS_API:
        mp_pose = mp.solutions.pose
        mp_drawing = mp.solutions.drawing_utils
        pose_ctx = mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
    else:
        model_path = PROJECT_ROOT / "models" / "mediapipe" / "pose_landmarker_lite.task"
        if not model_path.exists():
            with _camera_lock:
                _camera_shared["error"] = f"Model missing: {model_path}"
                _camera_shared["running"] = False
            return

        base_options = tasks.BaseOptions(model_asset_path=str(model_path))
        options = vision.PoseLandmarkerOptions(base_options=base_options, num_poses=1)
        pose_landmarker = vision.PoseLandmarker.create_from_options(options)

    # --- Main camera loop ---
    try:
        while True:
            with _camera_lock:
                if not _camera_shared["running"]:
                    break

            success, frame = camera.read()
            if not success:
                with _camera_lock:
                    _camera_shared["error"] = "Failed to read from webcam."
                break

            frame_time = time.monotonic()
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # --- Detect Pose ---
            pose_landmarks = None
            posture_label = "No pose detected"
            neck_angle = None
            back_angle = None

            if not _USE_TASKS_API and pose_ctx is not None:
                results = pose_ctx.process(rgb_frame)
                if results.pose_landmarks:
                    pose_landmarks = results.pose_landmarks

                    landmark_coordinates = extract_landmark_coordinates(
                        results, frame.shape[1], frame.shape[0]
                    )

                    neck_angle = calculate_neck_angle(landmark_coordinates)
                    back_angle = calculate_back_angle(landmark_coordinates)

                    if neck_angle is not None and back_angle is not None:
                        if baseline and "neck_angle" in baseline and "back_angle" in baseline:
                            posture_label = classify_posture_with_baseline(
                                neck_angle, back_angle,
                                baseline["neck_angle"], baseline["back_angle"],
                            )
                        else:
                            posture_label = classify_posture(neck_angle, back_angle)

                    mp_drawing.draw_landmarks(
                        frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS
                    )

            elif _USE_TASKS_API and pose_landmarker is not None:
                image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                result = pose_landmarker.detect(image)

                pose_landmarks = result.pose_landmarks[0] if result.pose_landmarks else None
                fake_results = SimpleNamespace(
                    pose_landmarks=SimpleNamespace(landmark=pose_landmarks)
                    if pose_landmarks else None
                )

                landmark_coordinates = extract_landmark_coordinates(
                    fake_results, frame.shape[1], frame.shape[0]
                )

                neck_angle = calculate_neck_angle(landmark_coordinates)
                back_angle = calculate_back_angle(landmark_coordinates)

                if neck_angle is not None and back_angle is not None:
                    if baseline and "neck_angle" in baseline and "back_angle" in baseline:
                        posture_label = classify_posture_with_baseline(
                            neck_angle, back_angle,
                            baseline["neck_angle"], baseline["back_angle"],
                        )
                    else:
                        posture_label = classify_posture(neck_angle, back_angle)

                if pose_landmarks:
                    _draw_pose_skeleton(frame, pose_landmarks, _POSE_CONNECTIONS)

            # --- Draw HUD text overlay ---
            cv2.putText(
                frame, f"Posture: {posture_label}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2,
            )
            if neck_angle is not None:
                cv2.putText(
                    frame, f"Neck angle: {neck_angle:.1f}", (20, 75),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2,
                )
            if back_angle is not None:
                cv2.putText(
                    frame, f"Back angle: {back_angle:.1f}", (20, 105),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2,
                )

            # --- Alerts ---
            sitting_start_time, show_break, break_message = update_break_reminder(
                posture_label, sitting_start_time, frame_time,
            )
            bad_posture_start_time, show_warning, warning_message = update_posture_alert(
                posture_label, bad_posture_start_time, frame_time,
            )

            if show_warning and warning_message:
                cv2.putText(
                    frame, warning_message, (20, 145),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2,
                )
            if show_break and break_message:
                cv2.putText(
                    frame, break_message, (20, 175),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 140, 255), 2,
                )

            # --- Track posture statistics ---
            posture_stats.update(posture_label, frame_time)

            # Convert annotated BGR frame to RGB for display.
            annotated_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Resize frame to save bandwidth/CPU
            h, w = annotated_rgb.shape[:2]
            if w > 640:
                scale = 640 / w
                annotated_rgb = cv2.resize(annotated_rgb, (640, int(h * scale)))

            # Compress to JPEG in background thread so Streamlit doesn't have to PNG encode it
            success_enc, buffer = cv2.imencode(".jpg", cv2.cvtColor(annotated_rgb, cv2.COLOR_RGB2BGR))
            jpeg_bytes = buffer.tobytes() if success_enc else None

            # --- Write shared state ---
            with _camera_lock:
                _camera_shared["frame"] = jpeg_bytes
                _camera_shared["posture_label"] = posture_label
                _camera_shared["neck_angle"] = neck_angle
                _camera_shared["back_angle"] = back_angle

            # --- Write live session snapshot every 1 second ---
            if frame_time - last_live_write >= 1.0:
                try:
                    summary = posture_stats.build_daily_summary()
                    total_seconds = summary["total_tracked_seconds"]
                    bad_seconds = summary["mild_slouch_seconds"] + summary["severe_slouch_seconds"]
                    good_pct = (summary["good_posture_seconds"] / total_seconds * 100) if total_seconds else 0.0
                    bad_pct = (bad_seconds / total_seconds * 100) if total_seconds else 0.0

                    summary.update({
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "current_posture_label": posture_label,
                        "neck_angle": round(neck_angle, 1) if neck_angle is not None else None,
                        "back_angle": round(back_angle, 1) if back_angle is not None else None,
                        "good_posture_percent": round(good_pct, 2),
                        "bad_posture_percent": round(bad_pct, 2),
                        "bad_posture_seconds": round(bad_seconds, 2),
                    })
                    write_live_session_snapshot(live_session_path, summary)

                    # Also update the daily CSV export (using session_id to avoid overwriting earlier sessions)
                    csv_path = PROJECT_ROOT / "data" / "exports" / f"posture_daily_stats_{posture_stats.day.isoformat()}_{session_id}.csv"
                    write_daily_posture_summary(csv_path, summary)
                except Exception:
                    pass  # Don't crash the worker if snapshot writing fails.
                last_live_write = frame_time

            # Cap capture rate to ~30 fps.
            time.sleep(0.033)

    finally:
        print("[Worker] Stopping camera worker...")
        try:
            # Write final data point before exiting
            posture_stats.finalize(time.monotonic())
            final_summary = posture_stats.build_daily_summary()
            csv_path = PROJECT_ROOT / "data" / "exports" / f"posture_daily_stats_{posture_stats.day.isoformat()}_{session_id}.csv"
            write_daily_posture_summary(csv_path, final_summary)
        except Exception:
            pass
        camera.release()
        if pose_ctx is not None:
            pose_ctx.close()
        with _camera_lock:
            _camera_shared["running"] = False
        print("[Worker] Camera released cleanly.")


def _start_camera() -> None:
    """Start the webcam worker thread if it is not already running."""
    _camera_shared, _camera_lock = get_camera_state()

    with _camera_lock:
        if _camera_shared["running"]:
            return
        print("[Main] Issuing START to camera worker.")
        _camera_shared["running"] = True
        _camera_shared["frame"] = None
        _camera_shared["error"] = None
        _camera_shared["posture_label"] = None
        _camera_shared["neck_angle"] = None
        _camera_shared["back_angle"] = None

    thread = threading.Thread(target=_camera_worker, daemon=True)
    thread.start()


def _stop_camera() -> None:
    """Signal the camera worker to stop."""
    _camera_shared, _camera_lock = get_camera_state()

    with _camera_lock:
        if _camera_shared["running"]:
            print("[Main] Issuing STOP to camera worker.")
        _camera_shared["running"] = False
        _camera_shared["frame"] = None


def _read_camera_state() -> dict:
    """Return a snapshot of the camera worker state."""
    _camera_shared, _camera_lock = get_camera_state()

    with _camera_lock:
        return {
            "running": _camera_shared["running"],
            "frame": _camera_shared["frame"],
            "error": _camera_shared["error"],
            "posture_label": _camera_shared["posture_label"],
            "neck_angle": _camera_shared["neck_angle"],
            "back_angle": _camera_shared["back_angle"],
        }


# ---------------------------------------------------------------------------
# Streamlit dashboard
# ---------------------------------------------------------------------------


def main() -> None:
    """Render the Streamlit dashboard."""

    st.set_page_config(page_title="Posture Dashboard", page_icon="🧍", layout="wide")

    # Initialise session state keys used to track button toggles.
    if "cam_active" not in st.session_state:
        st.session_state["cam_active"] = False

    st.markdown(
        """
        <style>
        .metric-card {
            background: linear-gradient(135deg, rgba(20, 20, 35, 0.95), rgba(33, 43, 70, 0.95));
            border: 1px solid rgba(255, 255, 255, 0.10);
            border-radius: 18px;
            padding: 1.25rem;
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.25);
        }
        .metric-title {
            color: #b8c0d9;
            font-size: 0.9rem;
            margin-bottom: 0.35rem;
        }
        .metric-value {
            color: #ffffff;
            font-size: 2.2rem;
            font-weight: 700;
            line-height: 1.1;
        }
        .metric-subtitle {
            color: #8f9bbd;
            font-size: 0.85rem;
            margin-top: 0.35rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("Posture Monitoring Dashboard")
    st.caption("Track posture quality, daily history, and trends from exported webcam sessions.")

    # --- Sidebar ---
    st.sidebar.subheader("Webcam")

    # Use a robust toggle for the webcam to prevent lost clicks.
    cam_active = st.sidebar.toggle("🎥 Webcam Power", value=st.session_state.get("cam_active", False))
    st.session_state["cam_active"] = cam_active

    if cam_active:
        _start_camera()
    else:
        _stop_camera()

    st.sidebar.subheader("Live session")
    live_enabled = st.sidebar.checkbox("Show live metrics", value=True)
    live_path = st.sidebar.text_input("Live session file", value=str(DEFAULT_LIVE_SESSION))
    
    st.sidebar.subheader("Data Controls")
    if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    export_dir = st.sidebar.text_input("Export folder", value=str(DEFAULT_EXPORT_DIR))
    history = load_daily_history(export_dir)
    export_files = list_daily_exports(export_dir)
    st.sidebar.caption(f"Daily CSV files: {len(export_files)}")
    if export_files:
        st.sidebar.caption(f"Latest: {export_files[-1].name}")

    # --- Webcam feed section (uses @st.fragment for independent refresh) ---
    cam_state = _read_camera_state()
    cam_running = cam_state["running"]

    if cam_running:
        _render_webcam_section()
    elif cam_state["error"]:
        st.error(cam_state["error"])

    # --- Live session metrics (uses @st.fragment for independent refresh) ---
    if live_enabled:
        _render_live_session_section(live_path)

    # --- Daily history ---
    if history.empty:
        st.info("No daily CSV exports found yet. Run the webcam monitor to generate posture_daily_stats_YYYY-MM-DD.csv files in data/exports.")
    else:
        latest_day = history.iloc[-1]
        latest_date = latest_day["date_label"]

        metric_col_1, metric_col_2 = st.columns(2)
        with metric_col_1:
            _render_metric_card(
                "Good posture %",
                f"{latest_day['good_posture_percent']:.1f}%",
                f"Latest day: {latest_date}",
            )
        with metric_col_2:
            _render_metric_card(
                "Bad posture %",
                f"{latest_day['bad_posture_percent']:.1f}%",
                f"Latest day: {latest_date}",
            )

        st.write("")
        history_col, trend_col = st.columns([1.15, 1])

        with history_col:
            st.subheader("Daily history")
            display_columns = [
                "date_label",
                "good_posture_percent",
                "bad_posture_percent",
                "good_posture_seconds",
                "mild_slouch_seconds",
                "severe_slouch_seconds",
                "total_tracked_seconds",
            ]
            st.dataframe(
                history[display_columns].rename(
                    columns={
                        "date_label": "date",
                        "good_posture_percent": "good_posture_%",
                        "bad_posture_percent": "bad_posture_%",
                    }
                ),
                width="stretch",
                hide_index=True,
            )

        with trend_col:
            st.subheader("Trend graph")
            trend_frame = history.set_index("date")[["good_posture_percent", "bad_posture_percent"]]
            st.line_chart(trend_frame, height=360)




@st.fragment(run_every=0.5)
def _render_webcam_section() -> None:
    """Render the webcam feed + live posture indicators as an auto-refreshing fragment.

    Using ``@st.fragment(run_every=0.5)`` means only this function re-runs
    every 500ms — the rest of the dashboard is NOT re-executed, avoiding
    the rerun-storm that previously froze the UI.
    """

    cam_state = _read_camera_state()

    st.subheader("Webcam feed")

    if cam_state["error"]:
        st.error(cam_state["error"])
        return

    if cam_state["frame"] is not None:
        st.image(cam_state["frame"], width="stretch", output_format="JPEG")

        # Show real-time posture metrics below the feed.
        p_col1, p_col2, p_col3 = st.columns(3)
        p_col1.metric("Status", str(cam_state["posture_label"]))
        p_col2.metric("Neck", f"{cam_state['neck_angle']:.1f}°" if cam_state["neck_angle"] else "n/a")
        p_col3.metric("Back", f"{cam_state['back_angle']:.1f}°" if cam_state["back_angle"] else "n/a")
    else:
        st.info("Waiting for the first webcam frame...")


@st.fragment(run_every=2.0)
def _render_live_session_section(live_path: str) -> None:
    """Render the live session metrics as an auto-refreshing fragment."""
    st.subheader("Live session")
    snapshot = load_live_session_snapshot(live_path)

    if snapshot is None:
        st.info("No live session snapshot found yet. Start the webcam monitor to generate data/exports/live_session.json.")
        return

    live_col_1, live_col_2, live_col_3 = st.columns(3)
    with live_col_1:
        _render_metric_card(
            "Good posture %",
            f"{snapshot.get('good_posture_percent', 0.0):.1f}%",
            "Current session",
        )
    with live_col_2:
        _render_metric_card(
            "Bad posture %",
            f"{snapshot.get('bad_posture_percent', 0.0):.1f}%",
            "Current session",
        )
    with live_col_3:
        _render_metric_card(
            "Current posture",
            str(snapshot.get("current_posture_label", "Unknown")),
            f"Last update: {snapshot.get('timestamp', 'n/a')}",
        )

    st.write("")
    detail_col_1, detail_col_2, detail_col_3 = st.columns(3)
    with detail_col_1:
        st.metric("Neck angle", f"{snapshot.get('neck_angle', 'n/a')}")
    with detail_col_2:
        st.metric("Back angle", f"{snapshot.get('back_angle', 'n/a')}")
    with detail_col_3:
        st.metric("Tracked seconds", f"{snapshot.get('total_tracked_seconds', 0.0)}")

    st.divider()


if __name__ == "__main__":
    main()
