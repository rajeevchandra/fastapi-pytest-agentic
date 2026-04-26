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


# PR #1: Enhanced Input Validation Tests


# Negative price values
def test_create_item_negative_price():
    r = client.post("/items", json={"name": "item", "price": -1})
    assert r.status_code == 400
    assert r.json()["detail"] == "price must be > 0"


def test_create_item_large_negative_price():
    r = client.post("/items", json={"name": "item", "price": -100.50})
    assert r.status_code == 400
    assert r.json()["detail"] == "price must be > 0"


# Missing required fields
def test_create_item_missing_name():
    r = client.post("/items", json={"price": 10.0})
    assert r.status_code == 422  # FastAPI validation error


def test_create_item_missing_price():
    r = client.post("/items", json={"name": "item"})
    assert r.status_code == 422


def test_create_item_missing_all_fields():
    r = client.post("/items", json={})
    assert r.status_code == 422


# Invalid data types
def test_create_item_string_price():
    r = client.post("/items", json={"name": "item", "price": "invalid"})
    assert r.status_code == 422


def test_create_item_null_price():
    r = client.post("/items", json={"name": "item", "price": None})
    assert r.status_code == 422


def test_create_item_null_name():
    r = client.post("/items", json={"name": None, "price": 10.0})
    assert r.status_code == 422


# Empty/whitespace strings
def test_create_item_empty_name():
    r = client.post("/items", json={"name": "", "price": 10.0})
    assert r.status_code == 200  # Empty string is valid but not ideal


def test_create_item_whitespace_name():
    r = client.post("/items", json={"name": "   ", "price": 10.0})
    assert r.status_code == 200  # Whitespace is valid but not ideal


# Extreme values
def test_create_item_very_large_price():
    r = client.post("/items", json={"name": "expensive", "price": 999999999.99})
    assert r.status_code == 200
    assert r.json()["price"] == 999999999.99


def test_create_item_very_long_name():
    long_name = "a" * 10000
    r = client.post("/items", json={"name": long_name, "price": 10.0})
    assert r.status_code == 200
    assert r.json()["name"] == long_name


def test_create_item_unicode_name():
    r = client.post("/items", json={"name": "книга 📚", "price": 15.0})
    assert r.status_code == 200
    assert r.json()["name"] == "книга 📚"


# Malformed JSON
def test_create_item_malformed_json():
    r = client.post(
        "/items",
        data="{invalid json}",
        headers={"Content-Type": "application/json"}
    )
    assert r.status_code == 422


# Extra fields (Pydantic should ignore by default)
def test_create_item_extra_fields():
    r = client.post("/items", json={
        "name": "item",
        "price": 10.0,
        "extra_field": "ignored"
    })
    assert r.status_code == 200
    data = r.json()
    assert "extra_field" not in data


def test_get_item_found():
    r = client.get("/items/1")
    assert r.status_code == 200
    assert r.json()["id"] == 1


def test_get_item_not_found():
    r = client.get("/items/2")
    assert r.status_code == 404
    assert r.json()["detail"] == "not found"
