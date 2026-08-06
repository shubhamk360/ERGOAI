"""Random Forest and rule-based posture classification using neck and back angles."""

from __future__ import annotations
from pathlib import Path
from typing import Any, Optional
import joblib

GOOD_POSTURE = "Good posture"
MILD_SLOUCH = "Mild slouch"
SEVERE_SLOUCH = "Severe slouch"

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MODEL_PATH = PROJECT_ROOT / "models" / "ml" / "rf_posture_model.pkl"


class ModelRegistry:
    """Registry responsible for loading, caching, and managing ML model instances."""

    def __init__(self, model_path: Path | str | None = None) -> None:
        self.model_path = Path(model_path) if model_path else DEFAULT_MODEL_PATH
        self._model: Any = None
        self._loaded: bool = False

    def get_model(self) -> Any | None:
        """Lazily load and return the Random Forest classifier model."""
        if not self._loaded:
            self._loaded = True
            try:
                if self.model_path.exists():
                    self._model = joblib.load(self.model_path)
            except Exception:
                self._model = None
        return self._model

    def set_model(self, model: Any) -> None:
        """Inject a custom or mock model instance (useful for testing or A/B testing)."""
        self._model = model
        self._loaded = True


# Global default registry instance
default_registry = ModelRegistry()


def classify_posture(
    neck_angle: float,
    back_angle: float,
    neck_good_threshold: float = 20.0,
    neck_severe_threshold: float = 40.0,
    back_good_threshold: float = 8.0,
    back_severe_threshold: float = 18.0,
    registry: Optional[ModelRegistry] = None,
) -> str:
    """Return a posture label from neck and back angles.

    Uses Random Forest model if available from the registry, otherwise falls back to rule-based logic.
    """
    model_registry = registry or default_registry
    model = model_registry.get_model()

    if model is not None:
        try:
            features = [[
                neck_angle / max(0.1, neck_good_threshold),
                neck_angle / max(0.1, neck_severe_threshold),
                back_angle / max(0.1, back_good_threshold),
                back_angle / max(0.1, back_severe_threshold),
            ]]
            prediction = model.predict(features)[0]
            return str(prediction)
        except Exception:
            pass  # Fall back to rule-based detection on error

    # Rule-based fallback:
    if neck_angle >= neck_severe_threshold or back_angle >= back_severe_threshold:
        return SEVERE_SLOUCH

    if neck_angle <= neck_good_threshold and back_angle <= back_good_threshold:
        return GOOD_POSTURE

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
    registry: Optional[ModelRegistry] = None,
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
        registry=registry,
    )
