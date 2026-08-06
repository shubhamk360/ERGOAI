"""Posture monitoring session engine.

:class:`PostureSession` owns the complete per-frame pipeline::

    camera → detect pose → extract landmarks → classify → alert →
    track stats → write snapshot

Both the webcam preview script and the Streamlit dashboard delegate
to this class rather than re-implementing the pipeline themselves.
"""
# pyright: reportMissingImports=false

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cv2  # type: ignore
import numpy as np

from posture_detector.alerts import update_break_reminder, update_posture_alert
from posture_detector.calibration import load_baseline, save_baseline
from posture_detector.classification import classify_posture, classify_posture_with_baseline
from posture_detector.config import PostureConfig
from posture_detector.geometry import calculate_back_angle, calculate_neck_angle
from posture_detector.metrics import PostureStatisticsTracker, FatigueDetector
from posture_detector.pose.detector import PoseDetector
from posture_detector.storage import write_daily_posture_summary, write_live_session_snapshot


# ---------------------------------------------------------------------------
# Public data structures
# ---------------------------------------------------------------------------


@dataclass
class FrameResult:
    """Everything a UI layer needs to render a single processed frame."""

    frame: np.ndarray
    """BGR frame with the pose skeleton already drawn."""

    posture_label: str
    neck_angle: float | None
    back_angle: float | None

    show_warning: bool
    warning_message: str | None

    show_break: bool
    break_message: str | None

    show_fatigue: bool
    fatigue_message: str | None

    calibration_message: str | None


# ---------------------------------------------------------------------------
# HUD helper (shared by all consumers)
# ---------------------------------------------------------------------------


def draw_hud(frame: np.ndarray, result: FrameResult) -> None:
    """Overlay posture information text onto a BGR video frame.

    This is a convenience function so that every consumer (webcam preview,
    dashboard, future REST API) draws a consistent heads-up display.
    """

    cv2.putText(
        frame, f"Posture: {result.posture_label}",
        (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2,
    )
    if result.neck_angle is not None:
        cv2.putText(
            frame, f"Neck angle: {result.neck_angle:.1f}",
            (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2,
        )
    if result.back_angle is not None:
        cv2.putText(
            frame, f"Back angle: {result.back_angle:.1f}",
            (20, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2,
        )
    if result.show_warning and result.warning_message:
        cv2.putText(
            frame, result.warning_message,
            (20, 145), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2,
        )
    if result.show_break and result.break_message:
        cv2.putText(
            frame, result.break_message,
            (20, 175), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 140, 255), 2,
        )
    if result.show_fatigue and result.fatigue_message:
        cv2.putText(
            frame, result.fatigue_message,
            (20, 205), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 0, 255), 2,
        )
    if result.calibration_message:
        # Move calibration message down if fatigue is showing
        y_pos = 235 if result.show_fatigue else 205
        cv2.putText(
            frame, result.calibration_message,
            (20, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2,
        )


# ---------------------------------------------------------------------------
# Session engine
# ---------------------------------------------------------------------------


class PostureSession:
    """Owns the full posture-monitoring pipeline from camera to export.

    Usage::

        with PostureSession(PostureConfig(), baseline_path, export_dir) as s:
            s.open()
            while True:
                result = s.process_frame()
                if result is None:
                    break
                draw_hud(result.frame, result)
                cv2.imshow("Webcam", result.frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    """

    def __init__(
        self,
        config: PostureConfig | None = None,
        baseline_path: Path | str | None = None,
        export_dir: Path | str | None = None,
        model_dir: Path | None = None,
    ) -> None:
        self._config = config or PostureConfig()
        self._model_dir = model_dir
        self._user_id: int | None = None

        # Paths ---------------------------------------------------------
        self._baseline_path: Path | None = Path(baseline_path) if baseline_path is not None else None
        self._export_dir: Path | None = Path(export_dir) if export_dir is not None else None

        # Runtime state -------------------------------------------------
        self._camera: cv2.VideoCapture | None = None
        self._detector: PoseDetector | None = None
        self._baseline: dict[str, Any] | None = None
        self._posture_stats = PostureStatisticsTracker()
        self._fatigue_detector = FatigueDetector()

        # Alert timers
        self._bad_posture_start_time: float | None = None
        self._sitting_start_time: float | None = None

        # Live snapshot throttle
        self._last_live_write: float = 0.0

        # Calibration
        self._calibration_active: bool = False
        self._calibration_start_time: float | None = None
        self._calibration_neck_sum: float = 0.0
        self._calibration_back_sum: float = 0.0
        self._calibration_count: int = 0

    # ----- read-only properties -----

    @property
    def baseline(self) -> dict[str, Any] | None:
        """The currently loaded calibration baseline, if any."""
        if self._baseline is None and self._user_id is not None:
            self._baseline = load_baseline(self._user_id)
        return self._baseline

    @property
    def posture_stats(self) -> PostureStatisticsTracker:
        """Live statistics tracker (useful for dashboards)."""
        return self._posture_stats

    @property
    def is_open(self) -> bool:
        """``True`` when the camera has been opened successfully."""
        return self._camera is not None and self._camera.isOpened()

    # ----- lifecycle -----

    def open(self, camera_index: int | None = 0) -> bool:
        """Open the webcam and initialise the pose detector.

        If camera_index is None, bypasses camera initialization (useful for API backends).
        Returns ``True`` if the camera or detector opened successfully.
        """

        if camera_index is not None:
            self._camera = cv2.VideoCapture(camera_index)
            if not self._camera.isOpened():
                self._camera = None
                return False
            # Force 640x480 resolution to save CPU before MediaPipe processing.
            self._camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self._camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        self._detector = PoseDetector(model_dir=self._model_dir)
        return True

    def close(self) -> None:
        """Release all resources and write final exports."""

        if self._detector is not None:
            self._detector.close()
            self._detector = None

        if self._camera is not None:
            self._camera.release()
            self._camera = None

        # Finalise statistics
        self._posture_stats.finalize(time.monotonic())

        if self._user_id is not None:
            write_daily_posture_summary(self._user_id, self._posture_stats.build_daily_summary())
            self._write_final_snapshot()

    def __enter__(self) -> PostureSession:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # ----- per-frame processing -----

    def process_frame(self, frame: np.ndarray | None = None, draw_skeleton: bool = True) -> FrameResult | None:
        """Read one frame, run the full pipeline, and return the result.

        If a frame is not provided, it will read from the opened camera.
        Returns ``None`` when a frame cannot be read (camera disconnected).
        """

        if frame is None:
            if self._camera is None:
                return None
            success, frame = self._camera.read()
            if not success:
                return None

        if self._detector is None:
            return None

        frame_time = time.monotonic()

        # --- Detect pose ---
        pose_result = self._detector.detect(frame)

        # --- Classify ---
        neck_angle = calculate_neck_angle(pose_result.landmark_coordinates)
        back_angle = calculate_back_angle(pose_result.landmark_coordinates)

        posture_label = "No pose detected"
        if neck_angle is not None and back_angle is not None:
            if (
                self._baseline
                and "neck_angle" in self._baseline
                and "back_angle" in self._baseline
            ):
                posture_label = classify_posture_with_baseline(
                    neck_angle,
                    back_angle,
                    self._baseline["neck_angle"],
                    self._baseline["back_angle"],
                    neck_good_delta=self._baseline.get("neck_good_delta", self._config.neck_good_delta),
                    neck_severe_delta=self._baseline.get("neck_severe_delta", self._config.neck_severe_delta),
                    back_good_delta=self._baseline.get("back_good_delta", self._config.back_good_delta),
                    back_severe_delta=self._baseline.get("back_severe_delta", self._config.back_severe_delta),
                )
            else:
                posture_label = classify_posture(
                    neck_angle,
                    back_angle,
                    neck_good_threshold=self._config.neck_good_threshold,
                    neck_severe_threshold=self._config.neck_severe_threshold,
                    back_good_threshold=self._config.back_good_threshold,
                    back_severe_threshold=self._config.back_severe_threshold,
                )

        # --- Calibration ---
        calibration_message = None
        if self._calibration_active:
            calibration_message = self._process_calibration(
                frame_time, neck_angle, back_angle,
            )
            if self._calibration_active:
                posture_label = "Calibrating"

        # --- Alerts ---
        show_warning = False
        warning_message = None
        show_break = False
        break_message = None
        show_fatigue = False
        fatigue_message = None

        if not self._calibration_active:
            self._sitting_start_time, show_break, break_message = update_break_reminder(
                posture_label,
                self._sitting_start_time,
                frame_time,
                break_delay_seconds=self._config.break_reminder_seconds,
            )
            self._bad_posture_start_time, show_warning, warning_message = update_posture_alert(
                posture_label,
                self._bad_posture_start_time,
                frame_time,
                alert_delay_seconds=self._config.bad_posture_alert_seconds,
            )
            self._posture_stats.update(posture_label, frame_time, neck_angle, back_angle)
            
            show_fatigue, fatigue_message = self._fatigue_detector.update(
                frame_time, posture_label, neck_angle, back_angle
            )
            if show_fatigue:
                self._posture_stats.fatigue_alerts_count += 1
        else:
            self._sitting_start_time = None

        # --- Draw skeleton ---
        if draw_skeleton and pose_result.detected:
            self._detector.draw_skeleton(frame)

        # --- Live snapshot ---
        if (
            not self._calibration_active
            and self._export_dir is not None
            and frame_time - self._last_live_write >= self._config.live_snapshot_interval
        ):
            self._write_live_snapshot(posture_label, neck_angle, back_angle)
            self._last_live_write = frame_time

        return FrameResult(
            frame=frame,
            posture_label=posture_label,
            neck_angle=neck_angle,
            back_angle=back_angle,
            show_warning=show_warning,
            warning_message=warning_message,
            show_break=show_break,
            break_message=break_message,
            show_fatigue=show_fatigue,
            fatigue_message=fatigue_message,
            calibration_message=calibration_message,
        )

    # ----- calibration -----

    def start_calibration(self) -> None:
        """Begin a new calibration sequence."""

        self._calibration_active = True
        self._calibration_start_time = None
        self._calibration_neck_history: list[float] = []
        self._calibration_back_history: list[float] = []
        self._sitting_start_time = None

    # ----- private helpers -----

    def _process_calibration(
        self,
        frame_time: float,
        neck_angle: float | None,
        back_angle: float | None,
    ) -> str:
        """Update calibration state and return a status message."""

        if self._calibration_start_time is None:
            self._calibration_start_time = frame_time

        if neck_angle is not None and back_angle is not None:
            if not hasattr(self, "_calibration_neck_history"):
                self._calibration_neck_history = []
                self._calibration_back_history = []
            self._calibration_neck_history.append(neck_angle)
            self._calibration_back_history.append(back_angle)

        elapsed = frame_time - self._calibration_start_time
        progress = min(elapsed / self._config.calibration_duration, 1.0)
        message = f"Calibrating... {int(progress * 100)}%"

        if elapsed >= self._config.calibration_duration:
            neck_history = getattr(self, "_calibration_neck_history", [])
            back_history = getattr(self, "_calibration_back_history", [])
            if len(neck_history) > 0 and self._user_id is not None:
                import statistics
                avg_neck = statistics.mean(neck_history)
                avg_back = statistics.mean(back_history)

                neck_std = statistics.stdev(neck_history) if len(neck_history) > 1 else 1.0
                back_std = statistics.stdev(back_history) if len(back_history) > 1 else 1.0

                neck_good_delta = max(3.0, round(2.0 * neck_std, 2))
                neck_severe_delta = max(10.0, round(4.0 * neck_std, 2))
                back_good_delta = max(2.5, round(2.0 * back_std, 2))
                back_severe_delta = max(8.0, round(4.0 * back_std, 2))

                self._baseline = save_baseline(
                    self._user_id,
                    avg_neck,
                    avg_back,
                    neck_good_delta=neck_good_delta,
                    neck_severe_delta=neck_severe_delta,
                    back_good_delta=back_good_delta,
                    back_severe_delta=back_severe_delta,
                )
                message = "Calibration saved"
            else:
                message = "Calibration failed: no pose"

            self._calibration_active = False
            self._calibration_start_time = None
            self._calibration_neck_history = []
            self._calibration_back_history = []

        return message

    def _build_snapshot_summary(
        self,
        posture_label: str,
        neck_angle: float | None,
        back_angle: float | None,
    ) -> dict[str, Any]:
        """Build the summary dict used for live and final snapshots."""

        summary = self._posture_stats.build_daily_summary()
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
            "fatigue_alerts_count": summary.get("fatigue_alerts_count", 0),
        })
        return summary

    def _write_live_snapshot(
        self,
        posture_label: str,
        neck_angle: float | None,
        back_angle: float | None,
    ) -> None:
        """Write a live session snapshot to JSON."""

        if self._user_id is None:
            return
        summary = self._build_snapshot_summary(posture_label, neck_angle, back_angle)
        write_live_session_snapshot(self._user_id, summary)
        
        # Continuously update the daily summary so data isn't lost if the websocket disconnects unexpectedly
        daily_summary = self._posture_stats.build_daily_summary()
        from posture_detector.storage import write_daily_posture_summary
        write_daily_posture_summary(self._user_id, daily_summary)

    def _write_final_snapshot(self) -> None:
        """Write the final session-ended snapshot."""

        if self._user_id is None:
            return
        summary = self._build_snapshot_summary("Session Ended", None, None)
        write_live_session_snapshot(self._user_id, summary)
