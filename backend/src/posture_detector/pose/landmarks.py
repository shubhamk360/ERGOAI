"""Reusable MediaPipe Pose landmark extraction helpers."""

from __future__ import annotations

from typing import Any


def _to_pixel_coordinates(landmark: Any, image_width: int, image_height: int) -> tuple[int, int]:
    # Convert normalized landmark coordinates into pixel coordinates.
    x_coordinate = int(landmark.x * image_width)
    y_coordinate = int(landmark.y * image_height)
    return x_coordinate, y_coordinate


def _extract_pair(
    landmarks: Any,
    left_index: int,
    right_index: int,
    image_width: int,
    image_height: int,
) -> dict[str, tuple[int, int] | None]:
    # Return both left and right points for a paired landmark group.
    left_landmark = landmarks[left_index] if landmarks and len(landmarks) > left_index else None
    right_landmark = landmarks[right_index] if landmarks and len(landmarks) > right_index else None

    return {
        "left": _to_pixel_coordinates(left_landmark, image_width, image_height) if left_landmark else None,
        "right": _to_pixel_coordinates(right_landmark, image_width, image_height) if right_landmark else None,
    }


def extract_landmark_coordinates(results: Any, image_width: int, image_height: int) -> dict[str, Any]:
    # Build a reusable dictionary of the key upper-body landmarks.
    extracted_landmarks: dict[str, Any] = {
        "nose": None,
        "ears": {"left": None, "right": None},
        "shoulders": {"left": None, "right": None},
        "hips": {"left": None, "right": None},
    }

    # Skip extraction when no pose landmarks are available.
    if not getattr(results, "pose_landmarks", None):
        return extracted_landmarks

    # Read the MediaPipe landmark list once for all coordinate lookups.
    landmarks = results.pose_landmarks.landmark

    # Extract the nose coordinate.
    nose_landmark = landmarks[0]
    extracted_landmarks["nose"] = _to_pixel_coordinates(nose_landmark, image_width, image_height)

    # Extract both ears, shoulders, and hips as grouped coordinates.
    extracted_landmarks["ears"] = _extract_pair(landmarks, 7, 8, image_width, image_height)
    extracted_landmarks["shoulders"] = _extract_pair(landmarks, 11, 12, image_width, image_height)
    extracted_landmarks["hips"] = _extract_pair(landmarks, 23, 24, image_width, image_height)

    return extracted_landmarks
