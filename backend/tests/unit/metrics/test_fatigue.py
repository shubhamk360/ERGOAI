import pytest
from posture_detector.metrics import FatigueDetector
from posture_detector.classification import GOOD_POSTURE, MILD_SLOUCH, SEVERE_SLOUCH

def test_no_fatigue_initially():
    detector = FatigueDetector(_cooldown_seconds=0)
    # Supply a few good frames
    for i in range(20):
        is_fatigued, msg = detector.update(float(i), GOOD_POSTURE, 15.0, 5.0)
        assert not is_fatigued

def test_head_drooping():
    detector = FatigueDetector(_cooldown_seconds=0, droop_variance_threshold=10.0)
    # Supply erratic neck angles
    angles = [15.0, 30.0, 10.0, 40.0, 15.0, 35.0, 10.0, 45.0, 15.0, 30.0, 10.0, 40.0, 15.0, 35.0, 10.0, 45.0]
    fatigued = False
    for i, angle in enumerate(angles):
        is_fatigued, msg = detector.update(float(i), GOOD_POSTURE, angle, 5.0)
        if is_fatigued:
            fatigued = True
            assert "Head drooping" in msg
            break
            
    assert fatigued

def test_prolonged_slouching():
    detector = FatigueDetector(_cooldown_seconds=0, prolonged_slouch_seconds=10.0)
    fatigued = False
    # Slouch for 11 seconds
    for i in range(12):
        is_fatigued, msg = detector.update(float(i), MILD_SLOUCH, 25.0, 15.0)
        if is_fatigued:
            fatigued = True
            assert "Prolonged slouching" in msg
            
    assert fatigued

def test_inactivity():
    # Set a very short window so we can test it quickly
    detector = FatigueDetector(_cooldown_seconds=0, window_size_seconds=10.0, inactivity_variance_threshold=0.5)
    fatigued = False
    # Supply the exact same angles
    for i in range(30):
        is_fatigued, msg = detector.update(float(i) * 0.5, GOOD_POSTURE, 15.0, 5.0)
        if is_fatigued:
            fatigued = True
            assert "inactivity" in msg
            break
            
    assert fatigued

def test_instability():
    detector = FatigueDetector(_cooldown_seconds=0, window_size_seconds=10.0, instability_variance_threshold=10.0)
    fatigued = False
    # Supply shifting angles
    angles = [15.0, 25.0] * 15
    for i, angle in enumerate(angles):
        is_fatigued, msg = detector.update(float(i) * 0.5, GOOD_POSTURE, 15.0, angle)
        if is_fatigued:
            fatigued = True
            assert "shifting" in msg
            break
            
    assert fatigued
