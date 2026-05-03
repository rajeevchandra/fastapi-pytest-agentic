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


# ========================================
# PR #1: Enhanced Input Validation Tests
# ========================================

# Negative price values
def test_create_item_negative_price():
    """Test that negative prices are rejected"""
    r = client.post("/items", json={"name": "item", "price": -1})
    assert r.status_code == 400
    assert r.json()["detail"] == "price must be > 0"


def test_create_item_large_negative_price():
    """Test that large negative prices are rejected"""
    r = client.post("/items", json={"name": "item", "price": -100.50})
    assert r.status_code == 400
    assert r.json()["detail"] == "price must be > 0"


# Missing required fields - FastAPI/Pydantic validation
def test_create_item_missing_name():
    """Test that missing name field returns 422 validation error"""
    r = client.post("/items", json={"price": 10.0})
    assert r.status_code == 422
    data = r.json()
    assert "detail" in data


def test_create_item_missing_price():
    """Test that missing price field returns 422 validation error"""
    r = client.post("/items", json={"name": "item"})
    assert r.status_code == 422
    data = r.json()
    assert "detail" in data


def test_create_item_missing_all_fields():
    """Test that missing all fields returns 422 validation error"""
    r = client.post("/items", json={})
    assert r.status_code == 422
    data = r.json()
    assert "detail" in data


# Invalid data types - FastAPI/Pydantic validation
def test_create_item_string_price():
    """Test that string price returns 422 validation error"""
    r = client.post("/items", json={"name": "item", "price": "ten"})
    assert r.status_code == 422
    data = r.json()
    assert "detail" in data


def test_create_item_null_name():
    """Test that null name returns 422 validation error"""
    r = client.post("/items", json={"name": None, "price": 10.0})
    assert r.status_code == 422
    data = r.json()
    assert "detail" in data


def test_create_item_null_price():
    """Test that null price returns 422 validation error"""
    r = client.post("/items", json={"name": "item", "price": None})
    assert r.status_code == 422
    data = r.json()
    assert "detail" in data


# Edge cases for string values
def test_create_item_empty_name():
    """Test that empty string name is accepted by Pydantic but processed"""
    r = client.post("/items", json={"name": "", "price": 10.0})
    # Empty string is valid for str type, but our API accepts it
    assert r.status_code == 200


def test_create_item_whitespace_name():
    """Test that whitespace name is accepted"""
    r = client.post("/items", json={"name": "   ", "price": 10.0})
    assert r.status_code == 200


# Extreme values
def test_create_item_very_large_price():
    """Test that very large prices are handled"""
    r = client.post("/items", json={"name": "expensive", "price": 999999999.99})
    assert r.status_code == 200
    assert r.json()["price"] == 999999999.99


def test_create_item_very_long_name():
    """Test that very long names are handled"""
    long_name = "a" * 10000
    r = client.post("/items", json={"name": long_name, "price": 10.0})
    assert r.status_code == 200
    assert r.json()["name"] == long_name


def test_create_item_special_characters_in_name():
    """Test that special characters in name are handled"""
    r = client.post("/items", json={"name": "item<>\"'&", "price": 10.0})
    assert r.status_code == 200
    assert r.json()["name"] == "item<>\"'&"


# Malformed JSON - handled by FastAPI
def test_create_item_invalid_json():
    """Test that malformed JSON returns 422"""
    r = client.post("/items", data="{invalid json}", headers={"Content-Type": "application/json"})
    assert r.status_code == 422


# Extra fields - Pydantic ignores by default
def test_create_item_extra_fields():
    """Test that extra fields are ignored by Pydantic"""
    r = client.post("/items", json={"name": "item", "price": 10.0, "extra": "ignored"})
    assert r.status_code == 200
    data = r.json()
    assert "extra" not in data
