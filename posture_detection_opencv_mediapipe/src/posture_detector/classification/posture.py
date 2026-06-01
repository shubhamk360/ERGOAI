"""Rule-based posture classification using neck and back angles."""

from __future__ import annotations


GOOD_POSTURE = "Good posture"
MILD_SLOUCH = "Mild slouch"
SEVERE_SLOUCH = "Severe slouch"


def classify_posture(
    neck_angle: float,
    back_angle: float,
    neck_good_threshold: float = 20.0,
    neck_severe_threshold: float = 40.0,
    back_good_threshold: float = 8.0,
    back_severe_threshold: float = 18.0,
) -> str:
    """Return a posture label from neck and back angles.

    Lower angles indicate a more upright posture. Larger angles indicate a
    stronger forward head tilt or back slouch.
    """

    # Mark posture as severe when either angle is clearly outside the healthy range.
    if neck_angle >= neck_severe_threshold or back_angle >= back_severe_threshold:
        return SEVERE_SLOUCH

    # Mark posture as good only when both angles stay within the healthy range.
    if neck_angle <= neck_good_threshold and back_angle <= back_good_threshold:
        return GOOD_POSTURE

    # Everything between good and severe is treated as a mild slouch.
    return MILD_SLOUCH


def classify_posture_with_baseline(
    neck_angle: float,
    back_angle: float,
    baseline_neck: float,
    baseline_back: float,
    neck_good_delta: float = 5.0,
    neck_severe_delta: float = 15.0,
    back_good_delta: float = 4.0,
    back_severe_delta: float = 10.0,
) -> str:
    """Return a posture label using deltas from a calibrated baseline."""

    neck_delta = max(0.0, neck_angle - baseline_neck)
    back_delta = max(0.0, back_angle - baseline_back)

    return classify_posture(
        neck_delta,
        back_delta,
        neck_good_threshold=neck_good_delta,
        neck_severe_threshold=neck_severe_delta,
        back_good_threshold=back_good_delta,
        back_severe_threshold=back_severe_delta,
    )
