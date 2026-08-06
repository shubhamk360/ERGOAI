"""Alert helpers for sustained bad posture detection."""

from __future__ import annotations

from posture_detector.classification import GOOD_POSTURE, MILD_SLOUCH, SEVERE_SLOUCH


SITTING_LABELS = {GOOD_POSTURE, MILD_SLOUCH, SEVERE_SLOUCH}


def update_posture_alert(
    posture_label: str,
    bad_posture_start_time: float | None,
    current_time: float,
    alert_delay_seconds: float = 10.0,
) -> tuple[float | None, bool, str | None]:
    """Update alert timing and return the current alert state.

    Returns a tuple of:
    - the updated bad posture start time
    - whether a warning should be shown
    - the warning message, if any
    """

    # Reset the timer whenever posture returns to good or no pose is available.
    if posture_label == GOOD_POSTURE or posture_label not in {MILD_SLOUCH, SEVERE_SLOUCH}:
        return None, False, None

    # Start the timer when bad posture is seen for the first time.
    if bad_posture_start_time is None:
        bad_posture_start_time = current_time

    # Show the warning only after the posture has stayed bad for long enough.
    elapsed_time = current_time - bad_posture_start_time
    if elapsed_time >= alert_delay_seconds:
        return bad_posture_start_time, True, "Warning: Bad posture detected for 10 seconds"

    return bad_posture_start_time, False, None


def update_break_reminder(
    posture_label: str,
    sitting_start_time: float | None,
    current_time: float,
    break_delay_seconds: float = 2700.0,
) -> tuple[float | None, bool, str | None]:
    """Track continuous sitting time and trigger a break reminder."""

    if posture_label not in SITTING_LABELS:
        return None, False, None

    if sitting_start_time is None:
        sitting_start_time = current_time

    elapsed_time = current_time - sitting_start_time
    if elapsed_time >= break_delay_seconds:
        return sitting_start_time, True, "Break reminder: Stand up and stretch"

    return sitting_start_time, False, None
