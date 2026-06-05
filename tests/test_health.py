from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


# Enhanced health endpoint tests

def test_health_response_structure():
    """Test that health response has expected structure"""
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert "status" in data
    assert isinstance(data["status"], str)


def test_health_response_headers():
    """Test that health response has correct content type"""
    r = client.get("/health")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/json"


def test_health_response_value():
    """Test that health status is specifically 'ok'"""
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_health_with_query_params():
    """Test that health endpoint ignores query parameters"""
    r = client.get("/health?extra=param&another=value")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_health_multiple_calls():
    """Test that health endpoint is consistent across multiple calls"""
    for _ in range(5):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


def test_health_case_sensitive():
    """Test that endpoint path is case sensitive"""
    r = client.get("/Health")
    assert r.status_code == 404


def test_health_trailing_slash():
    """Test that trailing slash may cause 404 or redirect"""
    r = client.get("/health/")
    assert r.status_code in [200, 307, 404]

