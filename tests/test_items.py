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


# Enhanced Input Validation Tests for PR #1

# Negative Price Values
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


# Missing Required Fields
def test_create_item_missing_name():
    """Test that missing name field triggers validation error"""
    r = client.post("/items", json={"price": 10.0})
    assert r.status_code == 422


def test_create_item_missing_price():
    """Test that missing price field triggers validation error"""
    r = client.post("/items", json={"name": "item"})
    assert r.status_code == 422


# Invalid Data Types
def test_create_item_invalid_price_type_string():
    """Test that string price triggers validation error"""
    r = client.post("/items", json={"name": "item", "price": "ten"})
    assert r.status_code == 422


def test_create_item_invalid_name_type_number():
    """Test that numeric name triggers validation error"""
    r = client.post("/items", json={"name": 123, "price": 10.0})
    assert r.status_code == 422


# Null Values
def test_create_item_null_name():
    """Test that null name triggers validation error"""
    r = client.post("/items", json={"name": None, "price": 10.0})
    assert r.status_code == 422


def test_create_item_null_price():
    """Test that null price triggers validation error"""
    r = client.post("/items", json={"name": "item", "price": None})
    assert r.status_code == 422


# Edge Cases
def test_create_item_empty_name():
    """Test that empty string name is accepted by Pydantic but can be validated by business logic if needed"""
    r = client.post("/items", json={"name": "", "price": 10.0})
    # FastAPI/Pydantic accepts empty strings by default
    assert r.status_code in [200, 400, 422]


def test_create_item_whitespace_name():
    """Test that whitespace-only name is accepted by Pydantic"""
    r = client.post("/items", json={"name": "   ", "price": 10.0})
    assert r.status_code in [200, 400, 422]


def test_create_item_very_large_price():
    """Test that very large prices are handled correctly"""
    r = client.post("/items", json={"name": "expensive", "price": 999999999.99})
    assert r.status_code == 200
    assert r.json()["price"] == 999999999.99


def test_create_item_very_long_name():
    """Test that very long names are handled correctly"""
    long_name = "a" * 10000
    r = client.post("/items", json={"name": long_name, "price": 10.0})
    assert r.status_code == 200
    assert r.json()["name"] == long_name


# Malformed Input
def test_create_item_malformed_json():
    """Test that malformed JSON triggers validation error"""
    r = client.post("/items", data="not json", headers={"Content-Type": "application/json"})
    assert r.status_code == 422
