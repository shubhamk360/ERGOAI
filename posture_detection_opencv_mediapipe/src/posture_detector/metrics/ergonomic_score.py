"""Ergonomic score calculation."""

from __future__ import annotations


def _linear_score(value: float, good_threshold: float, bad_threshold: float) -> float:
    # Map a value to a 0-1 score using linear thresholds.
    if bad_threshold <= good_threshold:
        raise ValueError("Bad threshold must be greater than good threshold.")

    if value <= good_threshold:
        return 1.0
    if value >= bad_threshold:
        return 0.0

    return 1.0 - ((value - good_threshold) / (bad_threshold - good_threshold))


def calculate_ergonomic_score(
    neck_angle: float | None,
    shoulder_imbalance: float | None,
    sitting_duration_seconds: float | None,
    neck_good_threshold: float = 15.0,
    neck_bad_threshold: float = 45.0,
    shoulder_good_threshold: float = 2.0,
    shoulder_bad_threshold: float = 12.0,
    sitting_good_seconds: float = 1200.0,
    sitting_bad_seconds: float = 3600.0,
    weights: tuple[float, float, float] = (0.5, 0.3, 0.2),
) -> float:
    """Return a 0-100 ergonomic score from neck, shoulder, and duration inputs."""

    scores: list[tuple[float, float]] = []

    if neck_angle is not None:
        scores.append(
            (
                _linear_score(neck_angle, neck_good_threshold, neck_bad_threshold),
                weights[0],
            )
        )

    if shoulder_imbalance is not None:
        scores.append(
            (
                _linear_score(shoulder_imbalance, shoulder_good_threshold, shoulder_bad_threshold),
                weights[1],
            )
        )

    if sitting_duration_seconds is not None:
        scores.append(
            (
                _linear_score(sitting_duration_seconds, sitting_good_seconds, sitting_bad_seconds),
                weights[2],
            )
        )

    if not scores:
        return 0.0

    total_weight = sum(weight for _, weight in scores)
    if total_weight == 0:
        return 0.0

    weighted_score = sum(score * weight for score, weight in scores) / total_weight
    return round(weighted_score * 100.0, 2)
