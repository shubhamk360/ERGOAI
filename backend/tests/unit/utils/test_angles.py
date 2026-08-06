import pytest
from posture_detector.utils.angles import calculate_angle

def test_calculate_angle_90_degrees():
    # A right angle
    a = (0.0, 1.0)
    b = (0.0, 0.0)
    c = (1.0, 0.0)
    assert calculate_angle(a, b, c) == pytest.approx(90.0)

def test_calculate_angle_180_degrees():
    # A straight line
    a = (-1.0, 0.0)
    b = (0.0, 0.0)
    c = (1.0, 0.0)
    assert calculate_angle(a, b, c) == pytest.approx(180.0)

def test_calculate_angle_0_degrees():
    # Overlapping vectors
    a = (1.0, 0.0)
    b = (0.0, 0.0)
    c = (2.0, 0.0)
    assert calculate_angle(a, b, c) == pytest.approx(0.0)

def test_calculate_angle_overlapping_points():
    a = (0.0, 0.0)
    b = (0.0, 0.0)
    c = (1.0, 0.0)
    with pytest.raises(ValueError):
        calculate_angle(a, b, c)
