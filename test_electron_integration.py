#!/usr/bin/env python3
"""
Integration test script to verify the Electron app can communicate with the backend.
This script tests the backend endpoints that the Electron app uses.
"""

import sys
import requests
import time
from typing import Dict, Any

BACKEND_URL = "http://localhost:8000"

def print_test(name: str):
    """Print test name."""
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print('='*60)

def print_success(message: str):
    """Print success message."""
    print(f"✓ {message}")

def print_error(message: str):
    """Print error message."""
    print(f"✗ {message}")

def test_health_endpoint() -> bool:
    """Test /health endpoint."""
    print_test("Health Check")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Backend is healthy: {data}")
            return True
        else:
            print_error(f"Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Cannot connect to backend: {e}")
        return False

def test_api_info() -> bool:
    """Test /api endpoint."""
    print_test("API Info")
    try:
        response = requests.get(f"{BACKEND_URL}/api", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"API info: {data}")
            return True
        else:
            print_error(f"API info failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"API info request failed: {e}")
        return False

def test_session_creation() -> Dict[str, Any]:
    """Test POST /run endpoint (navigation)."""
    print_test("Session Creation (Navigation)")
    try:
        payload = {
            "url": "https://example.com",
            "goals": ["Navigate to the page"],
            "max_steps": 1
        }
        response = requests.post(
            f"{BACKEND_URL}/run",
            json=payload,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            session_id = data.get("session_id")
            print_success(f"Session created: {session_id}")
            return data
        else:
            print_error(f"Session creation failed: {response.status_code}")
            return {}
    except Exception as e:
        print_error(f"Session creation request failed: {e}")
        return {}

def test_session_status(session_id: str) -> bool:
    """Test GET /status/{session_id} endpoint."""
    print_test(f"Session Status (ID: {session_id})")
    try:
        # Wait a bit for the session to start
        time.sleep(2)
        
        response = requests.get(f"{BACKEND_URL}/status/{session_id}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Status: {data.get('state')}, Steps: {data.get('steps_done')}")
            return True
        else:
            print_error(f"Status check failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Status check request failed: {e}")
        return False

def test_session_full_data(session_id: str) -> bool:
    """Test GET /api/session/{session_id}/full endpoint."""
    print_test(f"Full Session Data (ID: {session_id})")
    try:
        # Wait for session to complete
        max_attempts = 10
        for attempt in range(max_attempts):
            response = requests.get(f"{BACKEND_URL}/status/{session_id}", timeout=5)
            if response.status_code == 200:
                status = response.json().get('state')
                if status in ['completed', 'failed', 'stopped']:
                    break
            time.sleep(1)
        
        response = requests.get(
            f"{BACKEND_URL}/api/session/{session_id}/full",
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            steps = data.get('steps', [])
            print_success(f"Retrieved full data: {len(steps)} steps")
            if steps:
                print_success(f"  First step: {steps[0].get('reasoning', 'N/A')}")
            return True
        else:
            print_error(f"Full data retrieval failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Full data request failed: {e}")
        return False

def test_list_sessions() -> bool:
    """Test GET /sessions endpoint."""
    print_test("List Sessions")
    try:
        response = requests.get(f"{BACKEND_URL}/sessions", timeout=5)
        if response.status_code == 200:
            data = response.json()
            sessions = data.get('sessions', [])
            print_success(f"Found {len(sessions)} session(s)")
            return True
        else:
            print_error(f"List sessions failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"List sessions request failed: {e}")
        return False

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("ELECTRON APP BACKEND INTEGRATION TEST")
    print("="*60)
    print("\nThis script tests the backend endpoints used by the Electron app.")
    print(f"Backend URL: {BACKEND_URL}")
    
    results = []
    
    # Test 1: Health check
    results.append(("Health Check", test_health_endpoint()))
    
    if not results[-1][1]:
        print("\n" + "="*60)
        print("FATAL: Backend is not running!")
        print("="*60)
        print("\nPlease start the backend first:")
        print("  uvicorn app.main:app --host 0.0.0.0 --port 8000")
        sys.exit(1)
    
    # Test 2: API info
    results.append(("API Info", test_api_info()))
    
    # Test 3: Create session (navigation)
    session_data = test_session_creation()
    session_id = session_data.get("session_id")
    results.append(("Session Creation", bool(session_id)))
    
    if session_id:
        # Test 4: Check session status
        results.append(("Session Status", test_session_status(session_id)))
        
        # Test 5: Get full session data
        results.append(("Full Session Data", test_session_full_data(session_id)))
    
    # Test 6: List sessions
    results.append(("List Sessions", test_list_sessions()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print("\n" + "="*60)
    print(f"Results: {passed}/{total} tests passed")
    print("="*60)
    
    if passed == total:
        print("\n🎉 All tests passed! The Electron app backend integration is working.")
        print("\nYou can now test the Electron desktop app:")
        print("  npm start")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the backend configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
