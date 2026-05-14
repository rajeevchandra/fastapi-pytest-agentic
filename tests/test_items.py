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

# Negative Price Values
def test_create_item_negative_price():
    r = client.post("/items", json={"name": "negative", "price": -1})
    assert r.status_code == 400
    assert r.json()["detail"] == "price must be > 0"


def test_create_item_large_negative_price():
    r = client.post("/items", json={"name": "large_negative", "price": -100.50})
    assert r.status_code == 400
    assert r.json()["detail"] == "price must be > 0"


# Missing Required Fields
def test_create_item_missing_name():
    r = client.post("/items", json={"price": 10.0})
    assert r.status_code == 422


def test_create_item_missing_price():
    r = client.post("/items", json={"name": "item"})
    assert r.status_code == 422


def test_create_item_missing_all_fields():
    r = client.post("/items", json={})
    assert r.status_code == 422


# Invalid Data Types
def test_create_item_string_price():
    r = client.post("/items", json={"name": "item", "price": "not_a_number"})
    assert r.status_code == 422


def test_create_item_number_name():
    r = client.post("/items", json={"name": 123, "price": 10.0})
    assert r.status_code == 422


def test_create_item_null_price():
    r = client.post("/items", json={"name": "item", "price": None})
    assert r.status_code == 422


def test_create_item_null_name():
    r = client.post("/items", json={"name": None, "price": 10.0})
    assert r.status_code == 422


# Empty/Whitespace Strings
def test_create_item_empty_name():
    r = client.post("/items", json={"name": "", "price": 10.0})
    assert r.status_code == 200
    assert r.json()["name"] == ""


def test_create_item_whitespace_name():
    r = client.post("/items", json={"name": "   ", "price": 10.0})
    assert r.status_code == 200
    assert r.json()["name"] == "   "


# Extreme Values
def test_create_item_very_large_price():
    r = client.post("/items", json={"name": "expensive", "price": 999999999.99})
    assert r.status_code == 200
    assert r.json()["price"] == 999999999.99


def test_create_item_very_long_name():
    long_name = "x" * 10000
    r = client.post("/items", json={"name": long_name, "price": 10.0})
    assert r.status_code == 200
    assert r.json()["name"] == long_name


def test_create_item_tiny_price():
    r = client.post("/items", json={"name": "tiny", "price": 0.0001})
    assert r.status_code == 200
    assert r.json()["price"] == 0.0001


# Malformed JSON
def test_create_item_invalid_json():
    r = client.post("/items", data="not json", headers={"Content-Type": "application/json"})
    assert r.status_code == 422


# Extra Fields
def test_create_item_extra_fields():
    r = client.post("/items", json={"name": "item", "price": 10.0, "extra": "field", "another": 123})
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "item"
    assert data["price"] == 10.0
