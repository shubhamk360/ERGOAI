import pytest
from unittest.mock import MagicMock
from posture_detector.classification.posture import (
    classify_posture,
    classify_posture_with_baseline,
    ModelRegistry,
    GOOD_POSTURE,
    MILD_SLOUCH,
    SEVERE_SLOUCH,
)


@pytest.mark.parametrize(
    "neck_angle,back_angle,expected",
    [
        (0.0, 0.0, GOOD_POSTURE),
        (20.0, 8.0, GOOD_POSTURE),      # Exactly on good boundary
        (21.0, 5.0, MILD_SLOUCH),       # Slightly above good neck boundary
        (10.0, 9.0, MILD_SLOUCH),       # Slightly above good back boundary
        (40.0, 5.0, SEVERE_SLOUCH),     # Exactly on severe neck boundary
        (10.0, 18.0, SEVERE_SLOUCH),    # Exactly on severe back boundary
        (50.0, 25.0, SEVERE_SLOUCH),    # Well above severe boundaries
    ],
)
def test_classify_posture_rule_based_boundaries(neck_angle, back_angle, expected):
    # Pass an empty ModelRegistry so rule-based logic is guaranteed
    empty_registry = ModelRegistry()
    empty_registry.set_model(None)

    result = classify_posture(neck_angle, back_angle, registry=empty_registry)
    assert result == expected


def test_classify_posture_with_mock_model():
    mock_model = MagicMock()
    mock_model.predict.return_value = ["Custom Posture Label"]

    registry = ModelRegistry()
    registry.set_model(mock_model)

    result = classify_posture(15.0, 5.0, registry=registry)
    assert result == "Custom Posture Label"
    assert mock_model.predict.called


def test_classify_posture_with_baseline():
    empty_registry = ModelRegistry()
    empty_registry.set_model(None)

    # Baseline: neck 10, back 5
    # Current: neck 12 (delta 2), back 6 (delta 1) -> Good
    assert classify_posture_with_baseline(12.0, 6.0, 10.0, 5.0, registry=empty_registry) == GOOD_POSTURE

    # Current: neck 30 (delta 20) -> Severe
    assert classify_posture_with_baseline(30.0, 6.0, 10.0, 5.0, registry=empty_registry) == SEVERE_SLOUCH
