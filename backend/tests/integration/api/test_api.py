import io
import numpy as np
import cv2
import pytest
from fastapi.testclient import TestClient
from posture_detector.api.main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_user():
    # Register the user if not exists
    response = client.post(
        "/api/v1/auth/signup",
        json={"username": "user", "password": "password"}
    )
    # 201 Created or 400 Already Registered are both fine for tests
    assert response.status_code in [201, 400]

def get_auth_token():
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "user", "password": "password"}
    )
    return response.json()["access_token"]

def test_login_success():
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "user", "password": "password"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_failure():
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "user", "password": "wrongpassword"}
    )
    assert response.status_code == 401

def test_unauthorized_access():
    response = client.get("/api/v1/calibration/")
    assert response.status_code == 401

def test_calibration_endpoints():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get calibration without baseline should return 404
    response = client.get("/api/v1/calibration/", headers=headers)
    assert response.status_code == 404
    
    # Start calibration
    response = client.post("/api/v1/calibration/start", headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Calibration started."

def test_analysis_endpoint():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a dummy image
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    _, buffer = cv2.imencode('.jpg', img)
    io_buf = io.BytesIO(buffer)
    
    response = client.post(
        "/api/v1/analysis/frame",
        headers=headers,
        files={"file": ("dummy.jpg", io_buf, "image/jpeg")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "posture_label" in data
    assert data["posture_label"] in ["No pose detected", "Calibrating"]
