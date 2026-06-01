"""Shoulder imbalance calculations."""

from __future__ import annotations

import math


def calculate_shoulder_imbalance(
    left_shoulder: tuple[int, int] | None,
    right_shoulder: tuple[int, int] | None,
) -> float | None:
    """Return the shoulder line angle from horizontal in degrees."""

    if left_shoulder is None or right_shoulder is None:
        return None

    delta_x = right_shoulder[0] - left_shoulder[0]
    delta_y = right_shoulder[1] - left_shoulder[1]

    if delta_x == 0:
        return 90.0

    return abs(math.degrees(math.atan2(delta_y, delta_x)))
