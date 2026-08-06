"""Posture duration statistics tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from posture_detector.classification import GOOD_POSTURE, MILD_SLOUCH, SEVERE_SLOUCH


@dataclass
class PostureStatisticsTracker:
    """Track how long each posture label is held during a day."""

    day: date = field(default_factory=date.today)
    posture_durations: dict[str, float] = field(
        default_factory=lambda: {
            GOOD_POSTURE: 0.0,
            MILD_SLOUCH: 0.0,
            SEVERE_SLOUCH: 0.0,
        }
    )
    posture_counts: dict[str, int] = field(
        default_factory=lambda: {
            GOOD_POSTURE: 0,
            MILD_SLOUCH: 0,
            SEVERE_SLOUCH: 0,
        }
    )
    current_label: str | None = None
    last_timestamp: float | None = None
    neck_angle_sum: float = 0.0
    back_angle_sum: float = 0.0
    angle_sample_count: int = 0
    fatigue_alerts_count: int = 0

    def update(
        self,
        posture_label: str,
        current_timestamp: float,
        neck_angle: float | None = None,
        back_angle: float | None = None,
    ) -> None:
        """Accumulate elapsed time for the current posture label and update average angles."""

        if neck_angle is not None and back_angle is not None:
            self.neck_angle_sum += neck_angle
            self.back_angle_sum += back_angle
            self.angle_sample_count += 1

        if self.last_timestamp is None:
            self.current_label = posture_label
            self.last_timestamp = current_timestamp
            if posture_label in self.posture_counts:
                self.posture_counts[posture_label] += 1
            return

        elapsed_seconds = current_timestamp - self.last_timestamp
        if self.current_label in self.posture_durations and elapsed_seconds >= 0:
            self.posture_durations[self.current_label] += elapsed_seconds

        if posture_label != self.current_label and posture_label in self.posture_counts:
            self.posture_counts[posture_label] += 1

        self.current_label = posture_label
        self.last_timestamp = current_timestamp

    def finalize(self, current_timestamp: float) -> None:
        """Add the time between the last update and now to the active label."""

        if self.last_timestamp is None or self.current_label not in self.posture_durations:
            return

        elapsed_seconds = current_timestamp - self.last_timestamp
        if elapsed_seconds >= 0:
            self.posture_durations[self.current_label] += elapsed_seconds
        self.last_timestamp = current_timestamp

    def build_daily_summary(self) -> dict[str, Any]:
        """Return a dictionary ready for CSV/DB export."""

        total_seconds = sum(self.posture_durations.values())
        avg_neck = (
            round(self.neck_angle_sum / self.angle_sample_count, 2)
            if self.angle_sample_count > 0
            else None
        )
        avg_back = (
            round(self.back_angle_sum / self.angle_sample_count, 2)
            if self.angle_sample_count > 0
            else None
        )
        return {
            "date": self.day.isoformat(),
            "good_posture_seconds": round(self.posture_durations[GOOD_POSTURE], 2),
            "mild_slouch_seconds": round(self.posture_durations[MILD_SLOUCH], 2),
            "severe_slouch_seconds": round(self.posture_durations[SEVERE_SLOUCH], 2),
            "total_tracked_seconds": round(total_seconds, 2),
            "good_posture_count": self.posture_counts[GOOD_POSTURE],
            "mild_slouch_count": self.posture_counts[MILD_SLOUCH],
            "severe_slouch_count": self.posture_counts[SEVERE_SLOUCH],
            "avg_neck_angle": avg_neck,
            "avg_back_angle": avg_back,
            "fatigue_alerts_count": self.fatigue_alerts_count,
        }
