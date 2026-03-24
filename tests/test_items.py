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


# ============================================================================
# PR #1: Enhanced Input Validation Tests
# Testing edge cases for POST /items endpoint
# ============================================================================

# --- Negative Price Values ---
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


# --- Missing Required Fields ---
def test_create_item_missing_name():
    """Test that missing name field returns 422 validation error"""
    r = client.post("/items", json={"price": 10.0})
    assert r.status_code == 422
    errors = r.json()["detail"]
    assert any(e["loc"] == ["body", "name"] for e in errors)


def test_create_item_missing_price():
    """Test that missing price field returns 422 validation error"""
    r = client.post("/items", json={"name": "item"})
    assert r.status_code == 422
    errors = r.json()["detail"]
    assert any(e["loc"] == ["body", "price"] for e in errors)


# --- Invalid Data Types ---
def test_create_item_string_price():
    """Test that string price value returns 422 validation error"""
    r = client.post("/items", json={"name": "item", "price": "not-a-number"})
    assert r.status_code == 422
    errors = r.json()["detail"]
    assert any(e["loc"] == ["body", "price"] for e in errors)


def test_create_item_number_name():
    """Test that numeric name value is coerced to string"""
    r = client.post("/items", json={"name": 123, "price": 10.0})
    assert r.status_code == 200
    assert r.json()["name"] == "123"


# --- Empty/Whitespace Strings ---
def test_create_item_empty_name():
    """Test that empty string name is accepted (no validation rule against it)"""
    r = client.post("/items", json={"name": "", "price": 10.0})
    assert r.status_code == 200
    assert r.json()["name"] == ""


def test_create_item_whitespace_name():
    """Test that whitespace-only name is accepted"""
    r = client.post("/items", json={"name": "   ", "price": 10.0})
    assert r.status_code == 200
    assert r.json()["name"] == "   "


# --- Extreme Values ---
def test_create_item_very_large_price():
    """Test that very large price values are accepted"""
    r = client.post("/items", json={"name": "expensive", "price": 999999999.99})
    assert r.status_code == 200
    assert r.json()["price"] == 999999999.99


def test_create_item_very_long_name():
    """Test that very long names are accepted"""
    long_name = "a" * 10000
    r = client.post("/items", json={"name": long_name, "price": 10.0})
    assert r.status_code == 200
    assert r.json()["name"] == long_name


# --- Malformed/Invalid JSON ---
def test_create_item_malformed_json():
    """Test that malformed JSON returns 422"""
    r = client.post(
        "/items",
        data="{invalid json}",
        headers={"Content-Type": "application/json"}
    )
    assert r.status_code == 422


def test_create_item_empty_body():
    """Test that empty request body returns 422"""
    r = client.post("/items", json={})
    assert r.status_code == 422


# --- Extra Fields ---
def test_create_item_extra_fields_ignored():
    """Test that extra fields are ignored by default Pydantic behavior"""
    r = client.post("/items", json={
        "name": "item",
        "price": 10.0,
        "extra": "field",
        "another": 123
    })
    assert r.status_code == 200
    response_data = r.json()
    assert response_data["name"] == "item"
    assert response_data["price"] == 10.0
