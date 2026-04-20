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


# PR #1: Enhanced Input Validation Tests for /items POST endpoint

def test_create_item_negative_price():
    """Test that negative prices are rejected"""
    r = client.post("/items", json={"name": "item", "price": -1})
    assert r.status_code == 400
    assert r.json()["detail"] == "price must be > 0"


def test_create_item_large_negative_price():
    """Test that large negative prices are rejected"""
    r = client.post("/items", json={"name": "item", "price": -100})
    assert r.status_code == 400
    assert r.json()["detail"] == "price must be > 0"


def test_create_item_missing_name():
    """Test that missing name field is rejected by Pydantic"""
    r = client.post("/items", json={"price": 10})
    assert r.status_code == 422
    assert "field required" in str(r.json()).lower() or "missing" in str(r.json()).lower()


def test_create_item_missing_price():
    """Test that missing price field is rejected by Pydantic"""
    r = client.post("/items", json={"name": "book"})
    assert r.status_code == 422
    assert "field required" in str(r.json()).lower() or "missing" in str(r.json()).lower()


def test_create_item_missing_all_fields():
    """Test that empty request body is rejected"""
    r = client.post("/items", json={})
    assert r.status_code == 422


def test_create_item_string_price():
    """Test that string value for price is rejected"""
    r = client.post("/items", json={"name": "item", "price": "ten"})
    assert r.status_code == 422


def test_create_item_number_for_name():
    """Test that numeric value for name is coerced to string or rejected"""
    r = client.post("/items", json={"name": 123, "price": 10})
    # Pydantic may coerce int to string or reject it
    assert r.status_code in [200, 422]


def test_create_item_empty_string_name():
    """Test that empty string name is accepted (no validation in model)"""
    r = client.post("/items", json={"name": "", "price": 10})
    assert r.status_code == 200
    assert r.json()["name"] == ""


def test_create_item_whitespace_name():
    """Test that whitespace-only name is accepted"""
    r = client.post("/items", json={"name": "   ", "price": 10})
    assert r.status_code == 200
    assert r.json()["name"] == "   "


def test_create_item_very_large_price():
    """Test that very large prices are accepted"""
    r = client.post("/items", json={"name": "expensive", "price": 999999999.99})
    assert r.status_code == 200
    assert r.json()["price"] == 999999999.99


def test_create_item_very_long_name():
    """Test that very long names are accepted"""
    long_name = "a" * 10000
    r = client.post("/items", json={"name": long_name, "price": 10})
    assert r.status_code == 200
    assert r.json()["name"] == long_name


def test_create_item_malformed_json():
    """Test that malformed JSON is rejected"""
    r = client.post(
        "/items",
        data="{invalid json}",
        headers={"Content-Type": "application/json"}
    )
    assert r.status_code == 422


def test_create_item_null_name():
    """Test that null value for name is rejected"""
    r = client.post("/items", json={"name": None, "price": 10})
    assert r.status_code == 422


def test_create_item_null_price():
    """Test that null value for price is rejected"""
    r = client.post("/items", json={"name": "item", "price": None})
    assert r.status_code == 422


def test_create_item_extra_fields():
    """Test that extra fields are ignored by Pydantic"""
    r = client.post("/items", json={"name": "item", "price": 10, "extra": "ignored"})
    assert r.status_code == 200
    data = r.json()
    assert "extra" not in data
