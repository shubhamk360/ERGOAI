"""Geometry helpers for posture angle calculations."""

from __future__ import annotations

from typing import Any

from posture_detector.utils import calculate_angle


def _midpoint(point_a: tuple[int, int], point_b: tuple[int, int]) -> tuple[int, int]:
    # Compute the center point between two landmarks.
    midpoint_x = int((point_a[0] + point_b[0]) / 2)
    midpoint_y = int((point_a[1] + point_b[1]) / 2)
    return midpoint_x, midpoint_y


def _reference_point_above(point: tuple[int, int], offset: int = 100) -> tuple[int, int]:
    # Build a vertical reference point above the supplied landmark.
    return point[0], point[1] - offset


def _first_available_coordinate(*coordinates: tuple[int, int] | None) -> tuple[int, int] | None:
    # Return the first coordinate that is present.
    for coordinate in coordinates:
        if coordinate is not None:
            return coordinate
    return None


def calculate_neck_angle(landmarks: dict[str, Any]) -> float | None:
    # Prefer the nose, then fall back to an ear midpoint for the head reference.
    nose = landmarks.get("nose")
    ears = landmarks.get("ears", {})
    shoulders = landmarks.get("shoulders", {})

    left_shoulder = shoulders.get("left")
    right_shoulder = shoulders.get("right")
    shoulder_center = _first_available_coordinate(
        _midpoint(left_shoulder, right_shoulder) if left_shoulder and right_shoulder else None,
        left_shoulder,
        right_shoulder,
    )
    if shoulder_center is None:
        return None

    head_point = _first_available_coordinate(
        nose,
        _midpoint(ears["left"], ears["right"]) if ears.get("left") and ears.get("right") else None,
        ears.get("left"),
        ears.get("right"),
    )
    if head_point is None:
        return None

    # Measure the tilt between the head point and a vertical line above the shoulders.
    return calculate_angle(head_point, shoulder_center, _reference_point_above(shoulder_center))


def calculate_back_angle(landmarks: dict[str, Any]) -> float | None:
    # Use the shoulder center and hip center to measure the upper torso tilt.
    shoulders = landmarks.get("shoulders", {})
    hips = landmarks.get("hips", {})

    left_shoulder = shoulders.get("left")
    right_shoulder = shoulders.get("right")
    left_hip = hips.get("left")
    right_hip = hips.get("right")

    shoulder_center = _first_available_coordinate(
        _midpoint(left_shoulder, right_shoulder) if left_shoulder and right_shoulder else None,
        left_shoulder,
        right_shoulder,
    )
    hip_center = _first_available_coordinate(
        _midpoint(left_hip, right_hip) if left_hip and right_hip else None,
        left_hip,
        right_hip,
    )

    if shoulder_center is None or hip_center is None:
        return None

    # Measure the torso tilt between the shoulders and a vertical line above the hips.
    return calculate_angle(shoulder_center, hip_center, _reference_point_above(hip_center))
