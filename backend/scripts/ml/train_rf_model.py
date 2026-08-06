"""Script to train and save a baseline Random Forest posture classification model using normalized features."""

from pathlib import Path
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = PROJECT_ROOT / "models" / "ml"
MODEL_PATH = MODEL_DIR / "rf_posture_model.pkl"

GOOD_POSTURE = "Good posture"
MILD_SLOUCH = "Mild slouch"
SEVERE_SLOUCH = "Severe slouch"

def generate_synthetic_normalized_data(num_samples: int = 3000):
    np.random.seed(42)
    # Generate normalized ratios where:
    # neck_good_ratio <= 1.0 AND back_good_ratio <= 1.0 -> Good
    # neck_severe_ratio >= 1.0 OR back_severe_ratio >= 1.0 -> Severe
    # Else -> Mild
    
    # Generate random neck angles and thresholds
    neck_angles = np.random.uniform(0, 60, num_samples)
    back_angles = np.random.uniform(0, 30, num_samples)
    
    # Mix of raw thresholds (20/40, 8/18) and delta thresholds (5/15, 4/10)
    X = []
    labels = []
    
    for _ in range(num_samples):
        is_delta = np.random.rand() > 0.5
        if is_delta:
            ng_th, ns_th = 5.0, 15.0
            bg_th, bs_th = 4.0, 10.0
            neck = np.random.uniform(0, 30)
            back = np.random.uniform(0, 20)
        else:
            ng_th, ns_th = 20.0, 40.0
            bg_th, bs_th = 8.0, 18.0
            neck = np.random.uniform(0, 60)
            back = np.random.uniform(0, 30)
            
        if neck >= ns_th or back >= bs_th:
            label = SEVERE_SLOUCH
        elif neck <= ng_th and back <= bg_th:
            label = GOOD_POSTURE
        else:
            label = MILD_SLOUCH
            
        features = [
            neck / ng_th,
            neck / ns_th,
            back / bg_th,
            back / bs_th,
        ]
        X.append(features)
        labels.append(label)
        
    return np.array(X), np.array(labels)

def train_and_save_model():
    print("Generating normalized synthetic posture dataset...")
    X, y = generate_synthetic_normalized_data()
    
    print("Training RandomForestClassifier...")
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X, y)
    
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(clf, MODEL_PATH)
    print(f"Model successfully saved to {MODEL_PATH}")

if __name__ == "__main__":
    train_and_save_model()
