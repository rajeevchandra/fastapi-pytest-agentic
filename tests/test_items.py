from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# ============================================================================
# EXISTING TESTS
# ============================================================================

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
# PR #1: ENHANCED INPUT VALIDATION TESTS
# ============================================================================

# Negative Price Values
def test_create_item_negative_price():
    """Test rejection of small negative price"""
    r = client.post("/items", json={"name": "item", "price": -1})
    assert r.status_code == 400
    assert r.json()["detail"] == "price must be > 0"


def test_create_item_large_negative_price():
    """Test rejection of large negative price"""
    r = client.post("/items", json={"name": "item", "price": -100.50})
    assert r.status_code == 400
    assert r.json()["detail"] == "price must be > 0"


# Missing Required Fields
def test_create_item_missing_name():
    """Test rejection when name field is missing"""
    r = client.post("/items", json={"price": 10.0})
    assert r.status_code == 422
    assert "detail" in r.json()


def test_create_item_missing_price():
    """Test rejection when price field is missing"""
    r = client.post("/items", json={"name": "book"})
    assert r.status_code == 422
    assert "detail" in r.json()


def test_create_item_missing_both_fields():
    """Test rejection when both required fields are missing"""
    r = client.post("/items", json={})
    assert r.status_code == 422
    assert "detail" in r.json()


# Invalid Data Types
def test_create_item_string_price():
    """Test rejection of string value for price field"""
    r = client.post("/items", json={"name": "book", "price": "expensive"})
    assert r.status_code == 422
    assert "detail" in r.json()


def test_create_item_numeric_name():
    """Test that numeric values for name are coerced to string"""
    r = client.post("/items", json={"name": 12345, "price": 10.0})
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "12345"


def test_create_item_null_price():
    """Test rejection of null value for price"""
    r = client.post("/items", json={"name": "book", "price": None})
    assert r.status_code == 422
    assert "detail" in r.json()


def test_create_item_null_name():
    """Test rejection of null value for name"""
    r = client.post("/items", json={"name": None, "price": 10.0})
    assert r.status_code == 422
    assert "detail" in r.json()


# Empty/Whitespace Strings
def test_create_item_empty_name():
    """Test acceptance of empty string for name (Pydantic allows this)"""
    r = client.post("/items", json={"name": "", "price": 10.0})
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == ""


def test_create_item_whitespace_name():
    """Test acceptance of whitespace-only name (Pydantic allows this)"""
    r = client.post("/items", json={"name": "   ", "price": 10.0})
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "   "


# Extreme Values
def test_create_item_very_large_price():
    """Test acceptance of very large price values"""
    r = client.post("/items", json={"name": "expensive", "price": 999999999.99})
    assert r.status_code == 200
    data = r.json()
    assert data["price"] == 999999999.99


def test_create_item_very_small_positive_price():
    """Test acceptance of very small positive price"""
    r = client.post("/items", json={"name": "cheap", "price": 0.01})
    assert r.status_code == 200
    data = r.json()
    assert data["price"] == 0.01


def test_create_item_very_long_name():
    """Test acceptance of very long name string"""
    long_name = "a" * 10000
    r = client.post("/items", json={"name": long_name, "price": 10.0})
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == long_name
    assert len(data["name"]) == 10000


# Malformed JSON
def test_create_item_invalid_json():
    """Test rejection of malformed JSON payload"""
    r = client.post(
        "/items",
        data="{invalid json}",
        headers={"Content-Type": "application/json"}
    )
    assert r.status_code == 422
    assert "detail" in r.json()


# Extra Fields
def test_create_item_with_extra_fields():
    """Test that extra fields are ignored (Pydantic default behavior)"""
    r = client.post("/items", json={
        "name": "book",
        "price": 12.5,
        "extra_field": "ignored",
        "another_extra": 123
    })
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "book"
    assert data["price"] == 12.5
    assert "extra_field" not in data
    assert "another_extra" not in data


# Special Characters in Name
def test_create_item_special_characters_name():
    """Test acceptance of special characters in name"""
    r = client.post("/items", json={"name": "Book: The @#$% Adventure!", "price": 15.0})
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Book: The @#$% Adventure!"


def test_create_item_unicode_name():
    """Test acceptance of Unicode characters in name"""
    r = client.post("/items", json={"name": "書籍 📚", "price": 20.0})
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "書籍 📚"
