import pytest
from fastapi.testclient import TestClient
import os
from main import app

client = TestClient(app)

# Save original environment
original_api_key = os.environ.get("API_KEY")

def setup_module(module):
    """Setup for all tests in this module"""
    # Set test API key
    os.environ["API_KEY"] = "test_api_key"

def teardown_module(module):
    """Teardown after all tests in this module"""
    # Restore original API key
    if original_api_key:
        os.environ["API_KEY"] = original_api_key
    else:
        del os.environ["API_KEY"]

def test_missing_api_key():
    """Test that requests without API key are rejected"""
    response = client.get("/health")
    assert response.status_code == 401
    assert "API key is required" in response.json()["error"]

def test_invalid_api_key():
    """Test that requests with invalid API key are rejected"""
    response = client.get("/health", headers={"Authorization": "Bearer invalid_key"})
    assert response.status_code == 401
    assert "Invalid API key" in response.json()["error"]

def test_valid_api_key():
    """Test that requests with valid API key are accepted"""
    response = client.get("/health", headers={"Authorization": "Bearer test_api_key"})
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_non_bearer_auth():
    """Test that non-Bearer auth is rejected"""
    response = client.get("/health", headers={"Authorization": "Basic test_api_key"})
    assert response.status_code == 401
    assert "Invalid API key" in response.json()["error"]

def test_root_endpoint():
    """Test root endpoint with valid API key"""
    response = client.get("/", headers={"Authorization": "Bearer test_api_key"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "SecureKey Workspace Agent"
    assert data["status"] == "online"
    assert "version" in data
