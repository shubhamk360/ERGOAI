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

    def update(self, posture_label: str, current_timestamp: float) -> None:
        """Accumulate elapsed time for the current posture label."""

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
        """Return a dictionary ready for CSV export."""

        total_seconds = sum(self.posture_durations.values())
        return {
            "date": self.day.isoformat(),
            "good_posture_seconds": round(self.posture_durations[GOOD_POSTURE], 2),
            "mild_slouch_seconds": round(self.posture_durations[MILD_SLOUCH], 2),
            "severe_slouch_seconds": round(self.posture_durations[SEVERE_SLOUCH], 2),
            "total_tracked_seconds": round(total_seconds, 2),
            "good_posture_count": self.posture_counts[GOOD_POSTURE],
            "mild_slouch_count": self.posture_counts[MILD_SLOUCH],
            "severe_slouch_count": self.posture_counts[SEVERE_SLOUCH],
        }
