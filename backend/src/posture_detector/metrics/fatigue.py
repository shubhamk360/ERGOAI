"""Fatigue detection based on posture history and angle variance."""

from __future__ import annotations

import statistics
from collections import deque
from dataclasses import dataclass, field

from posture_detector.classification import GOOD_POSTURE


@dataclass
class FatigueDetector:
    """Detect signs of fatigue from posture data."""

    droop_variance_threshold: float = 25.0
    """Variance threshold for short-term neck angle to detect head drooping/nodding."""
    
    inactivity_variance_threshold: float = 0.5
    """Maximum variance allowed to flag a period as completely inactive."""
    
    instability_variance_threshold: float = 15.0
    """Variance threshold for long-term angles to detect frequent shifting."""
    
    prolonged_slouch_seconds: float = 300.0
    """Continuous seconds in a slouching state before triggering fatigue."""
    
    window_size_seconds: float = 60.0
    """Duration to keep angle history for variance calculations."""

    # Internal state
    _history: deque[tuple[float, float, float]] = field(default_factory=deque)
    _slouch_start_time: float | None = None
    _last_fatigue_time: float = 0.0
    _cooldown_seconds: float = 10.0

    def update(
        self,
        current_timestamp: float,
        posture_label: str,
        neck_angle: float | None,
        back_angle: float | None,
    ) -> tuple[bool, str | None]:
        """Update detector state and return (is_fatigued, message)."""
        
        # 1. Prolonged slouching check (doesn't depend on continuous angles)
        if posture_label != GOOD_POSTURE and posture_label != "No pose detected":
            if self._slouch_start_time is None:
                self._slouch_start_time = current_timestamp
            elif current_timestamp - self._slouch_start_time >= self.prolonged_slouch_seconds:
                return self._trigger(current_timestamp, "Fatigue: Prolonged slouching. Please stand up!")
        else:
            self._slouch_start_time = None

        if neck_angle is None or back_angle is None:
            return False, None

        self._history.append((current_timestamp, neck_angle, back_angle))

        # Evict old history
        while self._history and current_timestamp - self._history[0][0] > self.window_size_seconds:
            self._history.popleft()

        # Cooldown check
        if current_timestamp - self._last_fatigue_time < self._cooldown_seconds:
            return False, None

        # Need at least a few samples to calculate meaningful variance
        if len(self._history) < 15:
            return False, None

        # 2. Head drooping (Short-term high variance in neck angle)
        # Look at the last ~10-15 frames (approx 1-2 seconds)
        recent_history = list(self._history)[-15:]
        recent_neck_angles = [h[1] for h in recent_history]
        recent_neck_var = statistics.variance(recent_neck_angles)
        
        if recent_neck_var > self.droop_variance_threshold:
            return self._trigger(current_timestamp, "Fatigue: Head drooping detected. Stay alert!")

        # 3 & 4. Inactivity & Instability (Long-term variance)
        # Only evaluate if we have filled at least half our window
        window_duration = current_timestamp - self._history[0][0]
        if window_duration >= self.window_size_seconds * 0.5:
            neck_angles = [h[1] for h in self._history]
            back_angles = [h[2] for h in self._history]
            
            neck_var = statistics.variance(neck_angles)
            back_var = statistics.variance(back_angles)

            # Inactivity
            if neck_var < self.inactivity_variance_threshold and back_var < self.inactivity_variance_threshold:
                return self._trigger(current_timestamp, "Fatigue: Prolonged inactivity. Move around!")

            # Instability
            if neck_var > self.instability_variance_threshold or back_var > self.instability_variance_threshold:
                return self._trigger(current_timestamp, "Fatigue: Frequent shifting. Adjust your seating.")

        return False, None

    def _trigger(self, current_timestamp: float, message: str) -> tuple[bool, str]:
        self._last_fatigue_time = current_timestamp
        # Reset history to avoid re-triggering variance alerts continuously
        self._history.clear()
        return True, message
