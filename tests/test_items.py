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
# Test negative price values
def test_create_item_negative_price():
    r = client.post("/items", json={"name": "item", "price": -1})
    assert r.status_code == 400
    assert r.json()["detail"] == "price must be > 0"


def test_create_item_large_negative_price():
    r = client.post("/items", json={"name": "item", "price": -100.50})
    assert r.status_code == 400
    assert r.json()["detail"] == "price must be > 0"


# Test missing required fields
def test_create_item_missing_name():
    r = client.post("/items", json={"price": 10.0})
    assert r.status_code == 422
    assert "field required" in str(r.json()).lower() or "missing" in str(r.json()).lower()


def test_create_item_missing_price():
    r = client.post("/items", json={"name": "item"})
    assert r.status_code == 422
    assert "field required" in str(r.json()).lower() or "missing" in str(r.json()).lower()


def test_create_item_missing_both_fields():
    r = client.post("/items", json={})
    assert r.status_code == 422


# Test invalid data types
def test_create_item_string_price():
    r = client.post("/items", json={"name": "item", "price": "not-a-number"})
    assert r.status_code == 422


def test_create_item_null_name():
    r = client.post("/items", json={"name": None, "price": 10.0})
    assert r.status_code == 422


def test_create_item_null_price():
    r = client.post("/items", json={"name": "item", "price": None})
    assert r.status_code == 422


# Test empty/whitespace strings for name
def test_create_item_empty_name():
    r = client.post("/items", json={"name": "", "price": 10.0})
    assert r.status_code == 200
    assert r.json()["name"] == ""


def test_create_item_whitespace_name():
    r = client.post("/items", json={"name": "   ", "price": 10.0})
    assert r.status_code == 200
    assert r.json()["name"] == "   "


# Test extreme values
def test_create_item_very_large_price():
    r = client.post("/items", json={"name": "expensive", "price": 999999999.99})
    assert r.status_code == 200
    assert r.json()["price"] == 999999999.99


def test_create_item_very_long_name():
    long_name = "x" * 10000
    r = client.post("/items", json={"name": long_name, "price": 10.0})
    assert r.status_code == 200
    assert r.json()["name"] == long_name


def test_create_item_special_characters_name():
    special_name = "Item with émojis 🚀 and symbols @#$%"
    r = client.post("/items", json={"name": special_name, "price": 10.0})
    assert r.status_code == 200
    assert r.json()["name"] == special_name


# Test malformed JSON
def test_create_item_malformed_json():
    r = client.post(
        "/items",
        data="this is not json",
        headers={"Content-Type": "application/json"}
    )
    assert r.status_code == 422
