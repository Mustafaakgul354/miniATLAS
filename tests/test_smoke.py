"""Smoke tests for mini-Atlas."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config import config


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "mini-Atlas"
    assert data["status"] == "running"
    assert "version" in data


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "sessions_active" in data
    assert "sessions_total" in data


def test_run_endpoint_validation(client):
    """Test run endpoint with invalid data."""
    # Missing required fields
    response = client.post("/run", json={})
    assert response.status_code == 422
    
    # Invalid URL
    response = client.post("/run", json={
        "url": "not-a-url",
        "goals": ["Test"]
    })
    assert response.status_code == 422
    
    # Empty goals
    response = client.post("/run", json={
        "url": "https://example.com",
        "goals": []
    })
    assert response.status_code == 422


def test_session_not_found(client):
    """Test status endpoint with non-existent session."""
    response = client.get("/status/non-existent-session")
    assert response.status_code == 404
    assert "Session not found" in response.json()["detail"]


def test_list_sessions(client):
    """Test list sessions endpoint."""
    response = client.get("/sessions")
    assert response.status_code == 200
    data = response.json()
    assert "sessions" in data
    assert isinstance(data["sessions"], list)
