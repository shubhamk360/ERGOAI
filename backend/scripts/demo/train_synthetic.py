import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
from pathlib import Path
import os

def create_synthetic_dataset(n_samples=5000):
    """
    Generate a realistic synthetic dataset for posture angles.
    We create three clusters: Good, Mild, Severe.
    """
    np.random.seed(42)
    
    # 1. Good posture (low neck and back angles)
    # Neck ~10 deg, Back ~3 deg
    good_neck = np.random.normal(loc=10.0, scale=4.0, size=int(n_samples * 0.4))
    good_back = np.random.normal(loc=3.0, scale=2.0, size=int(n_samples * 0.4))
    good_labels = ["Good posture"] * len(good_neck)
    
    # 2. Mild slouch (medium neck and back angles)
    # Neck ~25 deg, Back ~12 deg
    mild_neck = np.random.normal(loc=25.0, scale=6.0, size=int(n_samples * 0.4))
    mild_back = np.random.normal(loc=12.0, scale=4.0, size=int(n_samples * 0.4))
    mild_labels = ["Mild slouch"] * len(mild_neck)
    
    # 3. Severe slouch (high neck and back angles)
    # Neck ~45 deg, Back ~22 deg
    severe_neck = np.random.normal(loc=45.0, scale=8.0, size=int(n_samples * 0.2))
    severe_back = np.random.normal(loc=22.0, scale=5.0, size=int(n_samples * 0.2))
    severe_labels = ["Severe slouch"] * len(severe_neck)
    
    # Combine everything
    neck = np.concatenate([good_neck, mild_neck, severe_neck])
    back = np.concatenate([good_back, mild_back, severe_back])
    labels = np.concatenate([good_labels, mild_labels, severe_labels])
    
    # Ensure no negative angles (bound to 0)
    neck = np.clip(neck, 0, None)
    back = np.clip(back, 0, None)
    
    df = pd.DataFrame({
        "neck_angle": neck,
        "back_angle": back,
        "label": labels
    })
    
    # Shuffle
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    return df

def extract_features(df, neck_good=20.0, neck_severe=40.0, back_good=8.0, back_severe=18.0):
    """
    Apply the exact same normalization logic the API uses before feeding to the model.
    """
    f1 = df['neck_angle'] / max(0.1, neck_good)
    f2 = df['neck_angle'] / max(0.1, neck_severe)
    f3 = df['back_angle'] / max(0.1, back_good)
    f4 = df['back_angle'] / max(0.1, back_severe)
    
    X = pd.DataFrame({
        'f1': f1, 'f2': f2, 'f3': f3, 'f4': f4
    })
    return X.values

def main():
    print("Generating synthetic dataset...")
    df = create_synthetic_dataset(n_samples=5000)
    print(f"Dataset generated with {len(df)} samples.")
    print(df['label'].value_counts())
    
    X = extract_features(df)
    y = df['label'].values
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("\nTraining Random Forest model...")
    clf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    clf.fit(X_train, y_train)
    
    print("\nEvaluating model on test set...")
    y_pred = clf.predict(X_test)
    print(classification_report(y_test, y_pred))
    
    # Save the model
    project_root = Path(__file__).resolve().parents[3]
    model_dir = project_root / "models" / "ml"
    model_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = model_dir / "rf_posture_model.pkl"
    joblib.dump(clf, model_path)
    print(f"\nModel successfully saved to {model_path}")

if __name__ == "__main__":
    main()
