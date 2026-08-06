"""Angle helpers for landmark-based posture analysis."""

from __future__ import annotations

import numpy as np


def calculate_angle(point_a: tuple[float, float], point_b: tuple[float, float], point_c: tuple[float, float]) -> float:
    """Return the angle in degrees formed by three points with point_b as the vertex.

    The angle is measured between the vectors point_b -> point_a and point_b -> point_c.
    """

    # Convert the input points to numpy arrays so vector math stays compact and readable.
    point_a_array = np.array(point_a, dtype=float)
    point_b_array = np.array(point_b, dtype=float)
    point_c_array = np.array(point_c, dtype=float)

    # Build the two vectors that meet at the middle point.
    vector_ba = point_a_array - point_b_array
    vector_bc = point_c_array - point_b_array

    # Compute vector magnitudes and guard against degenerate points.
    magnitude_ba = np.linalg.norm(vector_ba)
    magnitude_bc = np.linalg.norm(vector_bc)
    if magnitude_ba == 0 or magnitude_bc == 0:
        raise ValueError("Angle cannot be calculated with overlapping points.")

    # Use the dot product to get the cosine of the angle at the middle point.
    cosine_angle = np.dot(vector_ba, vector_bc) / (magnitude_ba * magnitude_bc)

    # Clamp the cosine to the valid numeric range so floating-point noise cannot break arccos.
    cosine_angle = np.clip(cosine_angle, -1.0, 1.0)

    # Convert the angle from radians to degrees for easier posture interpretation.
    angle_radians = np.arccos(cosine_angle)
    return float(np.degrees(angle_radians))
