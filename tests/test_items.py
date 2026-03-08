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


def test_create_item_negative_price():
    """Negative prices should be rejected"""
    r = client.post("/items", json={"name": "book", "price": -1})
    assert r.status_code == 400
    assert r.json()["detail"] == "price must be > 0"


def test_create_item_large_negative_price():
    """Large negative prices should be rejected"""
    r = client.post("/items", json={"name": "item", "price": -100.50})
    assert r.status_code == 400
    assert r.json()["detail"] == "price must be > 0"


def test_create_item_missing_name():
    """Missing name field should return 422 validation error"""
    r = client.post("/items", json={"price": 10.0})
    assert r.status_code == 422
    errors = r.json()["detail"]
    assert any(e["loc"] == ["body", "name"] for e in errors)


def test_create_item_missing_price():
    """Missing price field should return 422 validation error"""
    r = client.post("/items", json={"name": "book"})
    assert r.status_code == 422
    errors = r.json()["detail"]
    assert any(e["loc"] == ["body", "price"] for e in errors)


def test_create_item_both_fields_missing():
    """Missing both fields should return 422 validation error"""
    r = client.post("/items", json={})
    assert r.status_code == 422
    errors = r.json()["detail"]
    assert len(errors) == 2


def test_create_item_invalid_price_type():
    """String value for price should return 422 validation error"""
    r = client.post("/items", json={"name": "book", "price": "invalid"})
    assert r.status_code == 422
    errors = r.json()["detail"]
    assert any(e["loc"] == ["body", "price"] for e in errors)


def test_create_item_invalid_name_type():
    """Number value for name should be accepted and converted to string"""
    r = client.post("/items", json={"name": 123, "price": 10.0})
    assert r.status_code == 200
    assert r.json()["name"] == "123"


def test_create_item_empty_string_name():
    """Empty string name should be accepted (no validation constraint)"""
    r = client.post("/items", json={"name": "", "price": 10.0})
    assert r.status_code == 200
    assert r.json()["name"] == ""


def test_create_item_whitespace_name():
    """Whitespace-only name should be accepted"""
    r = client.post("/items", json={"name": "   ", "price": 10.0})
    assert r.status_code == 200
    assert r.json()["name"] == "   "


def test_create_item_very_large_price():
    """Very large prices should be accepted"""
    r = client.post("/items", json={"name": "expensive", "price": 999999999.99})
    assert r.status_code == 200
    assert r.json()["price"] == 999999999.99


def test_create_item_very_long_name():
    """Very long names should be accepted"""
    long_name = "a" * 10000
    r = client.post("/items", json={"name": long_name, "price": 10.0})
    assert r.status_code == 200
    assert r.json()["name"] == long_name


def test_create_item_malformed_json():
    """Malformed JSON should return 422 error"""
    r = client.post(
        "/items",
        data="{invalid json}",
        headers={"Content-Type": "application/json"}
    )
    assert r.status_code == 422


def test_create_item_null_name():
    """Null value for name should return 422 validation error"""
    r = client.post("/items", json={"name": None, "price": 10.0})
    assert r.status_code == 422


def test_create_item_null_price():
    """Null value for price should return 422 validation error"""
    r = client.post("/items", json={"name": "book", "price": None})
    assert r.status_code == 422


def test_create_item_extra_fields():
    """Extra fields should be ignored by Pydantic"""
    r = client.post("/items", json={
        "name": "book",
        "price": 10.0,
        "extra_field": "ignored"
    })
    assert r.status_code == 200
    data = r.json()
    assert "extra_field" not in data
