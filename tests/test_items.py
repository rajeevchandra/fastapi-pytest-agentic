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
# Negative price values
def test_create_item_negative_price():
    r = client.post("/items", json={"name": "book", "price": -1})
    assert r.status_code == 400
    assert r.json()["detail"] == "price must be > 0"


def test_create_item_large_negative_price():
    r = client.post("/items", json={"name": "book", "price": -100.50})
    assert r.status_code == 400
    assert r.json()["detail"] == "price must be > 0"


# Missing required fields
def test_create_item_missing_name():
    r = client.post("/items", json={"price": 12.5})
    assert r.status_code == 422
    data = r.json()
    assert "detail" in data


def test_create_item_missing_price():
    r = client.post("/items", json={"name": "book"})
    assert r.status_code == 422
    data = r.json()
    assert "detail" in data


# Invalid data types
def test_create_item_invalid_price_type_string():
    r = client.post("/items", json={"name": "book", "price": "not-a-number"})
    assert r.status_code == 422
    data = r.json()
    assert "detail" in data


def test_create_item_invalid_name_type_number():
    r = client.post("/items", json={"name": 123, "price": 12.5})
    assert r.status_code == 422
    data = r.json()
    assert "detail" in data


# Null values
def test_create_item_null_name():
    r = client.post("/items", json={"name": None, "price": 12.5})
    assert r.status_code == 422
    data = r.json()
    assert "detail" in data


def test_create_item_null_price():
    r = client.post("/items", json={"name": "book", "price": None})
    assert r.status_code == 422
    data = r.json()
    assert "detail" in data


# Empty/whitespace strings
def test_create_item_empty_name():
    r = client.post("/items", json={"name": "", "price": 12.5})
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == ""


def test_create_item_whitespace_name():
    r = client.post("/items", json={"name": "   ", "price": 12.5})
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "   "


# Extreme values
def test_create_item_very_large_price():
    r = client.post("/items", json={"name": "expensive", "price": 999999999.99})
    assert r.status_code == 200
    data = r.json()
    assert data["price"] == 999999999.99


def test_create_item_very_long_name():
    long_name = "a" * 10000
    r = client.post("/items", json={"name": long_name, "price": 12.5})
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == long_name


def test_create_item_very_small_positive_price():
    r = client.post("/items", json={"name": "cheap", "price": 0.01})
    assert r.status_code == 200
    data = r.json()
    assert data["price"] == 0.01


# Malformed JSON
def test_create_item_malformed_json():
    r = client.post("/items", data="not json", headers={"Content-Type": "application/json"})
    assert r.status_code == 422


# Extra fields
def test_create_item_extra_fields():
    r = client.post("/items", json={"name": "book", "price": 12.5, "extra": "field"})
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "book"
    assert data["price"] == 12.5
