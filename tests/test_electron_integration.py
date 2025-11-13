"""
Integration tests for Electron desktop app backend endpoints.
Verifies 6 backend endpoints used by Electron app.
"""

import pytest
import httpx
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestElectronIntegration:
    """Test backend endpoints for Electron integration."""
    
    def test_health_endpoint(self):
        """Test /health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "playwright" in data
    
    def test_run_endpoint_navigation(self):
        """Test /run endpoint for navigation (Phase 1)."""
        response = client.post(
            "/run",
            json={
                "url": "https://example.com",
                "goals": ["Navigate to the page"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "status" in data
        assert data["status"] == "running"
    
    def test_run_endpoint_summarization(self):
        """Test /run endpoint for summarization (Phase 2)."""
        response = client.post(
            "/run",
            json={
                "url": "https://example.com",
                "goals": [
                    "Navigate to the page",
                    "Summarize the main content and purpose of this page"
                ]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "status" in data
    
    def test_run_endpoint_task(self):
        """Test /run endpoint for task execution (Phase 3)."""
        response = client.post(
            "/run",
            json={
                "url": "https://example.com",
                "goals": ["Click on the first link"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "status" in data
    
    def test_status_endpoint(self):
        """Test /status/{session_id} endpoint."""
        # First create a session
        run_response = client.post(
            "/run",
            json={
                "url": "https://example.com",
                "goals": ["Navigate to the page"]
            }
        )
        session_id = run_response.json()["session_id"]
        
        # Then check status
        response = client.get(f"/status/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "status" in data
    
    def test_session_full_endpoint(self):
        """Test /api/session/{session_id}/full endpoint."""
        # First create a session
        run_response = client.post(
            "/run",
            json={
                "url": "https://example.com",
                "goals": ["Navigate to the page"]
            }
        )
        session_id = run_response.json()["session_id"]
        
        # Then get full session data
        response = client.get(f"/api/session/{session_id}/full")
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "status" in data
        assert "steps" in data
        assert "current_url" in data
    
    def test_stop_endpoint(self):
        """Test /stop/{session_id} endpoint."""
        # First create a session
        run_response = client.post(
            "/run",
            json={
                "url": "https://example.com",
                "goals": ["Navigate to the page"]
            }
        )
        session_id = run_response.json()["session_id"]
        
        # Then stop it
        response = client.post(f"/stop/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
    
    def test_sessions_endpoint(self):
        """Test /sessions endpoint."""
        response = client.get("/sessions")
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert isinstance(data["sessions"], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

