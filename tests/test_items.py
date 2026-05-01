from fastapi.testclient import TestClient
from app.main import app
import pytest

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


# ===== New Tests for PR #1: Enhanced Input Validation =====

def test_create_item_negative_price():
    """Test that negative prices are rejected"""
    r = client.post("/items", json={"name": "item", "price": -1.0})
    assert r.status_code == 400
    assert r.json()["detail"] == "price must be > 0"


def test_create_item_large_negative_price():
    """Test that large negative prices are rejected"""
    r = client.post("/items", json={"name": "item", "price": -999.99})
    assert r.status_code == 400
    assert r.json()["detail"] == "price must be > 0"


def test_create_item_missing_name():
    """Test that missing name field returns 422 validation error"""
    r = client.post("/items", json={"price": 10.0})
    assert r.status_code == 422
    errors = r.json()["detail"]
    assert any(err["loc"] == ["body", "name"] for err in errors)


def test_create_item_missing_price():
    """Test that missing price field returns 422 validation error"""
    r = client.post("/items", json={"name": "book"})
    assert r.status_code == 422
    errors = r.json()["detail"]
    assert any(err["loc"] == ["body", "price"] for err in errors)


def test_create_item_invalid_price_type_string():
    """Test that string price returns 422 validation error"""
    r = client.post("/items", json={"name": "book", "price": "expensive"})
    assert r.status_code == 422
    errors = r.json()["detail"]
    assert any(err["loc"] == ["body", "price"] for err in errors)


def test_create_item_invalid_name_type_number():
    """Test that numeric name returns 422 validation error"""
    r = client.post("/items", json={"name": 12345, "price": 10.0})
    assert r.status_code == 422
    errors = r.json()["detail"]
    assert any(err["loc"] == ["body", "name"] for err in errors)


def test_create_item_null_name():
    """Test that null name returns 422 validation error"""
    r = client.post("/items", json={"name": None, "price": 10.0})
    assert r.status_code == 422
    errors = r.json()["detail"]
    assert any(err["loc"] == ["body", "name"] for err in errors)


def test_create_item_null_price():
    """Test that null price returns 422 validation error"""
    r = client.post("/items", json={"name": "book", "price": None})
    assert r.status_code == 422
    errors = r.json()["detail"]
    assert any(err["loc"] == ["body", "price"] for err in errors)


def test_create_item_empty_string_name():
    """Test that empty string name is accepted (validation at app level if needed)"""
    r = client.post("/items", json={"name": "", "price": 10.0})
    # FastAPI accepts empty strings, app logic should handle if needed
    assert r.status_code == 200
    assert r.json()["name"] == ""


def test_create_item_whitespace_name():
    """Test that whitespace-only name is accepted"""
    r = client.post("/items", json={"name": "   ", "price": 10.0})
    assert r.status_code == 200
    assert r.json()["name"] == "   "


def test_create_item_very_long_name():
    """Test that very long names are accepted"""
    long_name = "x" * 1000
    r = client.post("/items", json={"name": long_name, "price": 10.0})
    assert r.status_code == 200
    assert r.json()["name"] == long_name


def test_create_item_very_large_price():
    """Test that very large prices are accepted"""
    r = client.post("/items", json={"name": "expensive", "price": 999999999.99})
    assert r.status_code == 200
    assert r.json()["price"] == 999999999.99


def test_create_item_minimal_positive_price():
    """Test that minimal positive price (just above zero) works"""
    r = client.post("/items", json={"name": "cheap", "price": 0.01})
    assert r.status_code == 200
    assert r.json()["price"] == 0.01


def test_create_item_malformed_json():
    """Test that malformed JSON returns 422 error"""
    r = client.post(
        "/items",
        data="{name: book, price: 10}",  # Invalid JSON (unquoted keys)
        headers={"Content-Type": "application/json"}
    )
    assert r.status_code == 422


def test_create_item_extra_fields_ignored():
    """Test that extra fields in request are ignored by Pydantic"""
    r = client.post("/items", json={
        "name": "book",
        "price": 10.0,
        "extra_field": "should be ignored",
        "another": 123
    })
    assert r.status_code == 200
    # Pydantic ignores extra fields by default
    assert "extra_field" not in r.json()
    assert "another" not in r.json()
