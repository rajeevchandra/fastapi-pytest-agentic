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
    """Negative prices should be rejected with 400."""
    r = client.post("/items", json={"name": "invalid", "price": -1})
    assert r.status_code == 400
    assert r.json()["detail"] == "price must be > 0"


def test_create_item_large_negative_price():
    """Large negative prices should be rejected with 400."""
    r = client.post("/items", json={"name": "invalid", "price": -100.50})
    assert r.status_code == 400
    assert r.json()["detail"] == "price must be > 0"


def test_create_item_missing_name():
    """Missing required field 'name' should return 422."""
    r = client.post("/items", json={"price": 10.0})
    assert r.status_code == 422
    data = r.json()
    assert "detail" in data


def test_create_item_missing_price():
    """Missing required field 'price' should return 422."""
    r = client.post("/items", json={"name": "test"})
    assert r.status_code == 422
    data = r.json()
    assert "detail" in data


def test_create_item_missing_both_fields():
    """Missing both required fields should return 422."""
    r = client.post("/items", json={})
    assert r.status_code == 422
    data = r.json()
    assert "detail" in data


def test_create_item_string_price():
    """String value for price should return 422."""
    r = client.post("/items", json={"name": "test", "price": "invalid"})
    assert r.status_code == 422
    data = r.json()
    assert "detail" in data


def test_create_item_number_name():
    """Pydantic coerces numbers to strings for name field."""
    r = client.post("/items", json={"name": 123, "price": 10.0})
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "123"


def test_create_item_null_name():
    """Null value for name should return 422."""
    r = client.post("/items", json={"name": None, "price": 10.0})
    assert r.status_code == 422
    data = r.json()
    assert "detail" in data


def test_create_item_null_price():
    """Null value for price should return 422."""
    r = client.post("/items", json={"name": "test", "price": None})
    assert r.status_code == 422
    data = r.json()
    assert "detail" in data


def test_create_item_empty_string_name():
    """Empty string is valid for name field."""
    r = client.post("/items", json={"name": "", "price": 5.0})
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == ""


def test_create_item_whitespace_name():
    """Whitespace-only string is valid for name field."""
    r = client.post("/items", json={"name": "   ", "price": 5.0})
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "   "


def test_create_item_very_long_name():
    """Very long names should be accepted."""
    long_name = "a" * 1000
    r = client.post("/items", json={"name": long_name, "price": 5.0})
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == long_name


def test_create_item_very_large_price():
    """Very large prices should be accepted."""
    r = client.post("/items", json={"name": "expensive", "price": 999999999.99})
    assert r.status_code == 200
    data = r.json()
    assert data["price"] == 999999999.99


def test_create_item_very_small_positive_price():
    """Very small positive prices should be accepted."""
    r = client.post("/items", json={"name": "cheap", "price": 0.01})
    assert r.status_code == 200
    data = r.json()
    assert data["price"] == 0.01


def test_create_item_malformed_json():
    """Malformed JSON should return 422."""
    r = client.post(
        "/items",
        data='{"name": "test", "price":',
        headers={"Content-Type": "application/json"}
    )
    assert r.status_code == 422


def test_create_item_extra_fields():
    """Extra fields should be ignored by Pydantic."""
    r = client.post(
        "/items",
        json={"name": "test", "price": 10.0, "extra": "ignored", "another": 123}
    )
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "test"
    assert data["price"] == 10.0
    assert "extra" not in data
    assert "another" not in data
