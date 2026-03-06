"""
Enhanced input validation tests for POST /items endpoint.
Tests negative prices, missing fields, invalid types, edge cases, and malformed JSON.
"""
from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)


# Negative Price Values
def test_create_item_negative_price():
    """Test rejection of small negative price"""
    r = client.post("/items", json={"name": "book", "price": -1})
    assert r.status_code == 400
    assert r.json()["detail"] == "price must be > 0"


def test_create_item_large_negative_price():
    """Test rejection of large negative price"""
    r = client.post("/items", json={"name": "laptop", "price": -100.50})
    assert r.status_code == 400
    assert r.json()["detail"] == "price must be > 0"


# Missing Required Fields
def test_create_item_missing_name():
    """Test rejection when name field is missing"""
    r = client.post("/items", json={"price": 10.0})
    assert r.status_code == 422
    assert "field required" in str(r.json()).lower() or "missing" in str(r.json()).lower()


def test_create_item_missing_price():
    """Test rejection when price field is missing"""
    r = client.post("/items", json={"name": "book"})
    assert r.status_code == 422
    assert "field required" in str(r.json()).lower() or "missing" in str(r.json()).lower()


def test_create_item_missing_both_fields():
    """Test rejection when both required fields are missing"""
    r = client.post("/items", json={})
    assert r.status_code == 422


# Invalid Data Types
def test_create_item_string_price():
    """Test rejection when price is a string instead of number"""
    r = client.post("/items", json={"name": "book", "price": "ten"})
    assert r.status_code == 422


def test_create_item_number_name():
    """Test rejection when name is a number instead of string"""
    r = client.post("/items", json={"name": 12345, "price": 10.0})
    assert r.status_code == 422


def test_create_item_null_price():
    """Test rejection when price is null"""
    r = client.post("/items", json={"name": "book", "price": None})
    assert r.status_code == 422


def test_create_item_null_name():
    """Test rejection when name is null"""
    r = client.post("/items", json={"name": None, "price": 10.0})
    assert r.status_code == 422


# Empty and Whitespace Strings
def test_create_item_empty_name():
    """Test behavior with empty string for name"""
    r = client.post("/items", json={"name": "", "price": 10.0})
    # Empty strings are technically valid for Pydantic str fields
    # but we're testing the behavior
    assert r.status_code in [200, 400, 422]


def test_create_item_whitespace_name():
    """Test behavior with whitespace-only name"""
    r = client.post("/items", json={"name": "   ", "price": 10.0})
    # Whitespace strings are technically valid for Pydantic str fields
    assert r.status_code in [200, 400, 422]


# Extreme Values
def test_create_item_very_large_price():
    """Test handling of very large price value"""
    r = client.post("/items", json={"name": "yacht", "price": 999999999.99})
    assert r.status_code == 200
    assert r.json()["price"] == 999999999.99


def test_create_item_very_long_name():
    """Test handling of very long name string"""
    long_name = "a" * 10000
    r = client.post("/items", json={"name": long_name, "price": 10.0})
    assert r.status_code == 200
    assert r.json()["name"] == long_name


# Malformed JSON
def test_create_item_malformed_json():
    """Test rejection of malformed JSON payload"""
    r = client.post(
        "/items",
        data="{'name': 'book', 'price': 10}",  # Invalid JSON (single quotes)
        headers={"Content-Type": "application/json"}
    )
    assert r.status_code == 422


def test_create_item_invalid_json_structure():
    """Test rejection of JSON that's not an object"""
    r = client.post(
        "/items",
        data='["name", "price"]',  # Array instead of object
        headers={"Content-Type": "application/json"}
    )
    assert r.status_code == 422


# Extra Fields
def test_create_item_with_extra_fields():
    """Test handling of extra fields in request"""
    r = client.post("/items", json={
        "name": "book",
        "price": 10.0,
        "extra_field": "ignored",
        "another_field": 123
    })
    # Pydantic by default ignores extra fields
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "book"
    assert data["price"] == 10.0


# Boundary Values for Price
def test_create_item_very_small_positive_price():
    """Test smallest positive price value"""
    r = client.post("/items", json={"name": "penny", "price": 0.01})
    assert r.status_code == 200
    assert r.json()["price"] == 0.01


def test_create_item_price_scientific_notation():
    """Test price in scientific notation"""
    r = client.post("/items", json={"name": "atom", "price": 1e-10})
    assert r.status_code == 200
    # Price should be positive even if very small
    assert r.json()["price"] > 0
