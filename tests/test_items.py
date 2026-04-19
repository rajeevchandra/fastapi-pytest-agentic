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
# Testing negative price values


def test_create_item_negative_price():
    """Reject items with negative price (-1)"""
    r = client.post("/items", json={"name": "book", "price": -1})
    assert r.status_code == 400
    assert r.json()["detail"] == "price must be > 0"


def test_create_item_large_negative_price():
    """Reject items with large negative price (-100.50)"""
    r = client.post("/items", json={"name": "book", "price": -100.50})
    assert r.status_code == 400
    assert r.json()["detail"] == "price must be > 0"


# Testing missing required fields


def test_create_item_missing_name():
    """Reject request when name field is missing"""
    r = client.post("/items", json={"price": 10.0})
    assert r.status_code == 422
    assert "field required" in str(r.json()).lower()


def test_create_item_missing_price():
    """Reject request when price field is missing"""
    r = client.post("/items", json={"name": "book"})
    assert r.status_code == 422
    assert "field required" in str(r.json()).lower()


def test_create_item_missing_both_fields():
    """Reject request when both name and price are missing"""
    r = client.post("/items", json={})
    assert r.status_code == 422


# Testing invalid data types


def test_create_item_string_price():
    """Reject request when price is a string instead of number"""
    r = client.post("/items", json={"name": "book", "price": "expensive"})
    assert r.status_code == 422


def test_create_item_null_price():
    """Reject request when price is null"""
    r = client.post("/items", json={"name": "book", "price": None})
    assert r.status_code == 422


def test_create_item_null_name():
    """Reject request when name is null"""
    r = client.post("/items", json={"name": None, "price": 10.0})
    assert r.status_code == 422


def test_create_item_number_name():
    """Reject request when name is a number instead of string"""
    r = client.post("/items", json={"name": 123, "price": 10.0})
    assert r.status_code == 422


# Testing edge cases for string values


def test_create_item_empty_name():
    """Reject or accept empty string name (current implementation accepts it)"""
    r = client.post("/items", json={"name": "", "price": 10.0})
    # FastAPI/Pydantic will accept empty strings by default
    # This test documents current behavior
    assert r.status_code in [200, 400]


def test_create_item_whitespace_name():
    """Accept whitespace-only name (Pydantic allows it)"""
    r = client.post("/items", json={"name": "   ", "price": 10.0})
    assert r.status_code == 200


def test_create_item_very_long_name():
    """Accept very long name (no length limit in schema)"""
    long_name = "a" * 10000
    r = client.post("/items", json={"name": long_name, "price": 10.0})
    assert r.status_code == 200
    assert r.json()["name"] == long_name


# Testing extreme price values


def test_create_item_very_large_price():
    """Accept very large price values"""
    r = client.post("/items", json={"name": "expensive", "price": 999999999.99})
    assert r.status_code == 200
    assert r.json()["price"] == 999999999.99


def test_create_item_very_small_positive_price():
    """Accept very small positive price (0.01)"""
    r = client.post("/items", json={"name": "cheap", "price": 0.01})
    assert r.status_code == 200
    assert r.json()["price"] == 0.01


def test_create_item_fractional_price():
    """Accept fractional cents (0.001)"""
    r = client.post("/items", json={"name": "cheap", "price": 0.001})
    assert r.status_code == 200
    assert r.json()["price"] == 0.001


# Testing malformed requests


def test_create_item_malformed_json():
    """Reject malformed JSON payload"""
    r = client.post(
        "/items",
        data="not valid json",
        headers={"Content-Type": "application/json"}
    )
    assert r.status_code == 422


def test_create_item_extra_fields():
    """Accept extra fields (Pydantic ignores them by default)"""
    r = client.post("/items", json={
        "name": "book",
        "price": 10.0,
        "extra_field": "ignored",
        "another": 123
    })
    assert r.status_code == 200
    # Extra fields should not be in response
    data = r.json()
    assert "extra_field" not in data
    assert "another" not in data
