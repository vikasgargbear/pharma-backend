"""
Test main application endpoints and middleware
"""
import pytest
from fastapi.testclient import TestClient


def test_root_endpoint(client):
    """Test the root endpoint returns system information"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "system_info" in data
    assert data["system_info"]["database_type"] in ["sqlite", "postgresql"]


def test_health_endpoint(client):
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "database_status" in data


def test_info_endpoint(client):
    """Test the system info endpoint"""
    response = client.get("/info")
    assert response.status_code == 200
    data = response.json()
    assert "app_name" in data
    assert "version" in data
    assert "database" in data


def test_security_headers(client):
    """Test that security headers are present"""
    response = client.get("/")
    headers = response.headers
    
    # Check for security headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert "Strict-Transport-Security" in headers
    assert "Referrer-Policy" in headers
    assert "Permissions-Policy" in headers


def test_cors_headers(client):
    """Test CORS headers are properly configured"""
    response = client.options("/", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
    

def test_rate_limiting_basic(client):
    """Test basic rate limiting functionality"""
    # Make several requests rapidly
    responses = []
    for i in range(5):
        response = client.get("/health")
        responses.append(response.status_code)
    
    # All should succeed for small number of requests
    assert all(status == 200 for status in responses)


def test_invalid_endpoint(client):
    """Test handling of invalid endpoints"""
    response = client.get("/nonexistent")
    assert response.status_code == 404


def test_request_validation_error(client):
    """Test request validation error handling"""
    # Send invalid JSON to an endpoint that expects valid data
    response = client.post("/customers/", json={"invalid": "data"})
    assert response.status_code == 422  # Unprocessable Entity