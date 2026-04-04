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

# Negative Price Tests
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


# Missing Required Fields Tests
def test_create_item_missing_name():
    """Test that missing name field returns 422"""
    r = client.post("/items", json={"price": 10.0})
    assert r.status_code == 422


def test_create_item_missing_price():
    """Test that missing price field returns 422"""
    r = client.post("/items", json={"name": "item"})
    assert r.status_code == 422


def test_create_item_missing_both_fields():
    """Test that missing both fields returns 422"""
    r = client.post("/items", json={})
    assert r.status_code == 422


# Invalid Type Tests
def test_create_item_price_as_string():
    """Test that string price is rejected with 422"""
    r = client.post("/items", json={"name": "item", "price": "invalid"})
    assert r.status_code == 422


def test_create_item_name_as_number():
    """Test that numeric name is coerced to string (Pydantic behavior)"""
    r = client.post("/items", json={"name": 123, "price": 10.0})
    assert r.status_code == 200
    assert r.json()["name"] == "123"


def test_create_item_null_name():
    """Test that null name returns 422"""
    r = client.post("/items", json={"name": None, "price": 10.0})
    assert r.status_code == 422


def test_create_item_null_price():
    """Test that null price returns 422"""
    r = client.post("/items", json={"name": "item", "price": None})
    assert r.status_code == 422


# Edge Cases: Empty and Whitespace Strings
def test_create_item_empty_name():
    """Test that empty string name is accepted (no validation on content)"""
    r = client.post("/items", json={"name": "", "price": 10.0})
    assert r.status_code == 200
    assert r.json()["name"] == ""


def test_create_item_whitespace_name():
    """Test that whitespace name is accepted"""
    r = client.post("/items", json={"name": "   ", "price": 10.0})
    assert r.status_code == 200
    assert r.json()["name"] == "   "


def test_create_item_name_with_special_chars():
    """Test that names with special characters are accepted"""
    r = client.post("/items", json={"name": "item-123_test!@#", "price": 10.0})
    assert r.status_code == 200
    assert r.json()["name"] == "item-123_test!@#"


# Extreme Value Tests
def test_create_item_very_large_price():
    """Test that very large prices are accepted"""
    r = client.post("/items", json={"name": "expensive", "price": 999999999.99})
    assert r.status_code == 200
    assert r.json()["price"] == 999999999.99


def test_create_item_very_small_positive_price():
    """Test that very small positive prices are accepted"""
    r = client.post("/items", json={"name": "cheap", "price": 0.01})
    assert r.status_code == 200
    assert r.json()["price"] == 0.01


def test_create_item_very_long_name():
    """Test that very long names are accepted"""
    long_name = "a" * 1000
    r = client.post("/items", json={"name": long_name, "price": 10.0})
    assert r.status_code == 200
    assert r.json()["name"] == long_name


# Malformed JSON Tests
def test_create_item_invalid_json():
    """Test that malformed JSON returns 422"""
    r = client.post("/items", data="not json", headers={"content-type": "application/json"})
    assert r.status_code == 422


def test_create_item_extra_fields():
    """Test that extra fields are ignored (Pydantic default behavior)"""
    r = client.post("/items", json={"name": "item", "price": 10.0, "extra": "field"})
    assert r.status_code == 200
    assert "extra" not in r.json()


def test_create_item_array_instead_of_object():
    """Test that array payload returns 422"""
    r = client.post("/items", json=[{"name": "item", "price": 10.0}])
    assert r.status_code == 422
