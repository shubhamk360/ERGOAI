"""Centralized configuration for posture detection settings."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PostureConfig:
    """All tunable thresholds and settings in one place.

    Every field has a sensible default so that ``PostureConfig()`` works
    out-of-the-box.  Override individual values when constructing the
    config to customise behaviour without touching source code.
    """

    # --- Classification (absolute thresholds) ---
    neck_good_threshold: float = 20.0
    neck_severe_threshold: float = 40.0
    back_good_threshold: float = 8.0
    back_severe_threshold: float = 18.0

    # --- Classification (baseline delta thresholds) ---
    neck_good_delta: float = 5.0
    neck_severe_delta: float = 15.0
    back_good_delta: float = 4.0
    back_severe_delta: float = 10.0

    # --- Alert timing ---
    bad_posture_alert_seconds: float = 10.0
    break_reminder_seconds: float = 2700.0

    # --- Calibration ---
    calibration_duration: float = 10.0

    # --- Live snapshot ---
    live_snapshot_interval: float = 1.0
