from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_create_item_success():
    r = client.post("/items", json={"name": "book", "price": 12.5})
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == 1
    assert data["name"] == "book"
    assert data["price"] == 12.5


def test_create_item_rejects_non_positive_price():
    r = client.post("/items", json={"name": "bad", "price": 0})
    assert r.status_code == 400
    assert r.json()["detail"] == "price must be > 0"


def test_get_item_found():
    r = client.get("/items/1")
    assert r.status_code == 200
    assert r.json()["id"] == 1


def test_get_item_not_found():
    r = client.get("/items/2")
    assert r.status_code == 404
    assert r.json()["detail"] == "not found"


# PR #1: Enhanced Input Validation Tests
# Focus: Edge cases for POST /items endpoint


# Negative Price Values
def test_create_item_negative_price():
    """Test that negative prices are rejected"""
    r = client.post("/items", json={"name": "book", "price": -1})
    assert r.status_code == 400
    assert r.json()["detail"] == "price must be > 0"


def test_create_item_large_negative_price():
    """Test that large negative prices are rejected"""
    r = client.post("/items", json={"name": "widget", "price": -100.50})
    assert r.status_code == 400
    assert r.json()["detail"] == "price must be > 0"


# Missing Required Fields
def test_create_item_missing_name():
    """Test that missing name field is rejected by Pydantic"""
    r = client.post("/items", json={"price": 10.0})
    assert r.status_code == 422
    detail = r.json()["detail"]
    assert any(err["loc"] == ["body", "name"] for err in detail)


def test_create_item_missing_price():
    """Test that missing price field is rejected by Pydantic"""
    r = client.post("/items", json={"name": "book"})
    assert r.status_code == 422
    detail = r.json()["detail"]
    assert any(err["loc"] == ["body", "price"] for err in detail)


def test_create_item_missing_both_fields():
    """Test that missing both fields is rejected by Pydantic"""
    r = client.post("/items", json={})
    assert r.status_code == 422
    detail = r.json()["detail"]
    assert len(detail) == 2


# Invalid Data Types
def test_create_item_string_price():
    """Test that string price is rejected by Pydantic"""
    r = client.post("/items", json={"name": "book", "price": "expensive"})
    assert r.status_code == 422
    detail = r.json()["detail"]
    assert any(err["loc"] == ["body", "price"] for err in detail)


def test_create_item_number_name():
    """Test that numeric name is coerced to string by Pydantic"""
    r = client.post("/items", json={"name": 12345, "price": 10.0})
    assert r.status_code == 200
    assert r.json()["name"] == "12345"


def test_create_item_null_price():
    """Test that null price is rejected by Pydantic"""
    r = client.post("/items", json={"name": "book", "price": None})
    assert r.status_code == 422
    detail = r.json()["detail"]
    assert any(err["loc"] == ["body", "price"] for err in detail)


# Edge Cases for Strings
def test_create_item_empty_name():
    """Test that empty string name is accepted (Pydantic allows it)"""
    r = client.post("/items", json={"name": "", "price": 5.0})
    assert r.status_code == 200
    assert r.json()["name"] == ""


def test_create_item_whitespace_name():
    """Test that whitespace-only name is accepted"""
    r = client.post("/items", json={"name": "   ", "price": 5.0})
    assert r.status_code == 200
    assert r.json()["name"] == "   "


# Extreme Values
def test_create_item_very_large_price():
    """Test that very large price values are accepted"""
    r = client.post("/items", json={"name": "luxury", "price": 999999999.99})
    assert r.status_code == 200
    assert r.json()["price"] == 999999999.99


def test_create_item_very_small_positive_price():
    """Test that very small positive prices are accepted"""
    r = client.post("/items", json={"name": "cheap", "price": 0.01})
    assert r.status_code == 200
    assert r.json()["price"] == 0.01


def test_create_item_very_long_name():
    """Test that very long names are accepted"""
    long_name = "a" * 10000
    r = client.post("/items", json={"name": long_name, "price": 10.0})
    assert r.status_code == 200
    assert r.json()["name"] == long_name


# Malformed JSON
def test_create_item_malformed_json():
    """Test that malformed JSON is rejected"""
    r = client.post("/items", data="not valid json", headers={"Content-Type": "application/json"})
    assert r.status_code == 422


# Extra Fields
def test_create_item_extra_fields():
    """Test that extra fields are ignored by Pydantic (default behavior)"""
    r = client.post("/items", json={"name": "book", "price": 10.0, "extra": "ignored"})
    assert r.status_code == 200
    result = r.json()
    assert "extra" not in result
