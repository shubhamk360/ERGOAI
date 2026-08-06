import pytest
from posture_detector.geometry.posture_angles import calculate_neck_angle, calculate_back_angle

def test_calculate_neck_angle_valid():
    coords = {
        "ears": {"left": (10, 10), "right": (10, 10)}, # Midpoint (10, 10)
        "shoulders": {"left": (10, 30), "right": (10, 30)}, # Midpoint (10, 30)
    }
    # Vertical line, should be 0 degrees
    angle = calculate_neck_angle(coords)
    assert angle == pytest.approx(0.0)

def test_calculate_neck_angle_missing():
    coords = {
        "nose": None,
        "ears": {"left": None, "right": None},
        "shoulders": {"left": (10, 30), "right": (10, 30)},
    }
    assert calculate_neck_angle(coords) is None

def test_calculate_back_angle_valid():
    coords = {
        "shoulders": {"left": (10, 30), "right": (10, 30)}, # Midpoint (10, 30)
        "hips": {"left": (10, 70), "right": (10, 70)}, # Midpoint (10, 70)
    }
    # Vertical line, should be 0 degrees
    angle = calculate_back_angle(coords)
    assert angle == pytest.approx(0.0)

def test_calculate_back_angle_missing():
    coords = {
        "shoulders": {"left": (10, 30), "right": (10, 30)},
        "hips": {"left": None, "right": None},
    }
    assert calculate_back_angle(coords) is None
