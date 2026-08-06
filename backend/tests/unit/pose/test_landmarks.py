from types import SimpleNamespace
from posture_detector.pose.landmarks import extract_landmark_coordinates

def test_extract_landmark_coordinates_missing():
    # results with no pose_landmarks
    results = SimpleNamespace(pose_landmarks=None)
    coords = extract_landmark_coordinates(results, 640, 480)
    assert coords["nose"] is None
    assert coords["ears"]["left"] is None
    assert coords["shoulders"]["left"] is None
    assert coords["hips"]["left"] is None

def test_extract_landmark_coordinates_valid():
    # mock landmarks
    class MockLandmark:
        def __init__(self, x, y):
            self.x = x
            self.y = y

    # Create 33 mock landmarks
    landmarks = [MockLandmark(0.5, 0.5) for _ in range(33)]
    
    # Specific landmarks
    landmarks[0] = MockLandmark(0.5, 0.1) # nose
    landmarks[7] = MockLandmark(0.4, 0.1) # left ear
    landmarks[8] = MockLandmark(0.6, 0.1) # right ear
    landmarks[11] = MockLandmark(0.3, 0.3) # left shoulder
    landmarks[12] = MockLandmark(0.7, 0.3) # right shoulder
    landmarks[23] = MockLandmark(0.4, 0.7) # left hip
    landmarks[24] = MockLandmark(0.6, 0.7) # right hip

    results = SimpleNamespace(
        pose_landmarks=SimpleNamespace(landmark=landmarks)
    )

    coords = extract_landmark_coordinates(results, 100, 100)
    
    assert coords["nose"] == (50, 10)
    assert coords["ears"]["left"] == (40, 10)
    assert coords["ears"]["right"] == (60, 10)
    assert coords["shoulders"]["left"] == (30, 30)
    assert coords["shoulders"]["right"] == (70, 30)
    assert coords["hips"]["left"] == (40, 70)
    assert coords["hips"]["right"] == (60, 70)
