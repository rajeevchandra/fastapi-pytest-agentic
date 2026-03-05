"""
Enhanced input validation tests for /items endpoint.
Tests edge cases, invalid inputs, and error handling.
"""
from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)


# ============================================================================
# Negative Price Tests
# ============================================================================

def test_create_item_negative_price():
    """Test that negative prices are rejected"""
    r = client.post("/items", json={"name": "book", "price": -1})
    assert r.status_code == 400
    assert "price must be > 0" in r.json()["detail"]


def test_create_item_large_negative_price():
    """Test that large negative prices are rejected"""
    r = client.post("/items", json={"name": "book", "price": -100.50})
    assert r.status_code == 400
    assert "price must be > 0" in r.json()["detail"]


# ============================================================================
# Missing Required Fields Tests
# ============================================================================

def test_create_item_missing_name():
    """Test that missing name field is rejected"""
    r = client.post("/items", json={"price": 10.0})
    assert r.status_code == 422
    assert r.json()["detail"][0]["loc"] == ["body", "name"]
    assert r.json()["detail"][0]["type"] == "missing"


def test_create_item_missing_price():
    """Test that missing price field is rejected"""
    r = client.post("/items", json={"name": "book"})
    assert r.status_code == 422
    assert r.json()["detail"][0]["loc"] == ["body", "price"]
    assert r.json()["detail"][0]["type"] == "missing"


def test_create_item_empty_body():
    """Test that empty request body is rejected"""
    r = client.post("/items", json={})
    assert r.status_code == 422
    # Should have 2 validation errors (missing name and price)
    assert len(r.json()["detail"]) == 2


# ============================================================================
# Invalid Data Type Tests
# ============================================================================

def test_create_item_string_price():
    """Test that string price is rejected"""
    r = client.post("/items", json={"name": "book", "price": "ten"})
    assert r.status_code == 422
    detail = r.json()["detail"][0]
    assert detail["loc"] == ["body", "price"]
    assert detail["type"] in ["float_parsing", "float_type"]


def test_create_item_numeric_name():
    """Test that numeric name is coerced to string"""
    r = client.post("/items", json={"name": 123, "price": 10.0})
    # Pydantic will coerce numeric to string
    assert r.status_code == 200
    assert r.json()["name"] == "123"


def test_create_item_null_name():
    """Test that null name is rejected"""
    r = client.post("/items", json={"name": None, "price": 10.0})
    assert r.status_code == 422
    detail = r.json()["detail"][0]
    assert detail["loc"] == ["body", "name"]


def test_create_item_null_price():
    """Test that null price is rejected"""
    r = client.post("/items", json={"name": "book", "price": None})
    assert r.status_code == 422
    detail = r.json()["detail"][0]
    assert detail["loc"] == ["body", "price"]


# ============================================================================
# Edge Case String Values
# ============================================================================

def test_create_item_empty_name():
    """Test that empty string name is accepted (validation may vary)"""
    r = client.post("/items", json={"name": "", "price": 10.0})
    # Empty string is technically valid for str type
    assert r.status_code == 200
    assert r.json()["name"] == ""


def test_create_item_whitespace_name():
    """Test that whitespace-only name is accepted"""
    r = client.post("/items", json={"name": "   ", "price": 10.0})
    assert r.status_code == 200
    assert r.json()["name"] == "   "


def test_create_item_very_long_name():
    """Test that very long names are accepted"""
    long_name = "a" * 10000
    r = client.post("/items", json={"name": long_name, "price": 10.0})
    assert r.status_code == 200
    assert r.json()["name"] == long_name


def test_create_item_unicode_name():
    """Test that unicode characters in name are handled"""
    r = client.post("/items", json={"name": "📚 Book émoji", "price": 10.0})
    assert r.status_code == 200
    assert r.json()["name"] == "📚 Book émoji"


# ============================================================================
# Extreme Price Values
# ============================================================================

def test_create_item_very_small_positive_price():
    """Test that very small positive prices are accepted"""
    r = client.post("/items", json={"name": "book", "price": 0.01})
    assert r.status_code == 200
    assert r.json()["price"] == 0.01


def test_create_item_very_large_price():
    """Test that very large prices are accepted"""
    r = client.post("/items", json={"name": "book", "price": 999999999.99})
    assert r.status_code == 200
    assert r.json()["price"] == 999999999.99


def test_create_item_float_precision():
    """Test float precision handling"""
    r = client.post("/items", json={"name": "book", "price": 12.3456789})
    assert r.status_code == 200
    # Just verify it's accepted, precision may vary


# ============================================================================
# Malformed JSON Tests
# ============================================================================

def test_create_item_invalid_json():
    """Test that malformed JSON is rejected"""
    r = client.post(
        "/items",
        data="{invalid json}",
        headers={"Content-Type": "application/json"}
    )
    assert r.status_code == 422


def test_create_item_extra_fields():
    """Test that extra fields are ignored"""
    r = client.post("/items", json={
        "name": "book",
        "price": 10.0,
        "extra_field": "should be ignored"
    })
    assert r.status_code == 200
    # Pydantic ignores extra fields by default
    assert "extra_field" not in r.json()


# ============================================================================
# Content-Type Tests
# ============================================================================

def test_create_item_wrong_content_type():
    """Test that non-JSON content-type is handled"""
    r = client.post(
        "/items",
        data="name=book&price=10",
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert r.status_code == 422
