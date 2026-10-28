"""
Input validation tests for ItemIn model and create_item endpoint.

Tests cover:
- Price boundary values (negative, zero, extreme values)
- Name field validation (empty, unicode, special characters)
- Missing/malformed JSON
- Type validation
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemValidPrice:
    """Test create_item with valid price values."""

    @pytest.mark.parametrize("price", [
        0.01,      # minimum positive
        1.0,       # unit
        10.5,      # decimal
        100.0,     # round large
        999.99,    # practical max
        1000.0,    # round thousand
        0.001,     # very small positive
        1e6,       # large exponent
    ])
    def test_create_item_accepts_valid_prices(self, price):
        """Should accept any positive price value."""
        r = client.post("/items", json={"name": "widget", "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == price
        assert data["name"] == "widget"
        assert data["id"] == 1


class TestCreateItemInvalidPrice:
    """Test create_item rejects invalid price values."""

    @pytest.mark.parametrize("price", [
        0,         # exactly zero
        -0.01,     # small negative
        -1,        # unit negative
        -100.5,    # larger negative
        -1000,     # large negative
        -1e6,      # very large negative
    ])
    def test_create_item_rejects_non_positive_prices(self, price):
        """Should reject zero and negative prices."""
        r = client.post("/items", json={"name": "widget", "price": price})
        assert r.status_code == 400
        data = r.json()
        assert data["detail"] == "price must be > 0"


class TestCreateItemValidName:
    """Test create_item with valid name values."""

    @pytest.mark.parametrize("name", [
        "book",           # simple
        "Widget Pro",     # with space
        "item-123",       # with hyphen
        "special_char",   # with underscore
        "123numeric",     # starts with digit
        "a",              # single character
        "very long name with multiple words here",  # long
        "Café",           # unicode
        "日本語",          # non-latin
        "emoji🎉test",    # emoji
    ])
    def test_create_item_accepts_various_names(self, name):
        """Should accept diverse name formats."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name
        assert data["price"] == 10.0


class TestCreateItemInvalidName:
    """Test create_item validation of empty names."""

    def test_create_item_rejects_empty_name(self):
        """Should reject empty string for name."""
        r = client.post("/items", json={"name": "", "price": 10.0})
        # FastAPI validates empty strings differently - checking for validation error
        assert r.status_code == 422  # Unprocessable entity


class TestCreateItemMissingFields:
    """Test create_item with missing required fields."""

    def test_create_item_missing_price(self):
        """Should reject request missing price field."""
        r = client.post("/items", json={"name": "widget"})
        assert r.status_code == 422

    def test_create_item_missing_name(self):
        """Should reject request missing name field."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422

    def test_create_item_empty_payload(self):
        """Should reject empty JSON payload."""
        r = client.post("/items", json={})
        assert r.status_code == 422


class TestCreateItemTypeValidation:
    """Test create_item type validation for fields."""

    def test_create_item_price_as_string(self):
        """Should reject string value for price."""
        r = client.post("/items", json={"name": "widget", "price": "10.0"})
        assert r.status_code == 422

    def test_create_item_name_as_number(self):
        """Should handle numeric name (may be coerced to string)."""
        r = client.post("/items", json={"name": 123, "price": 10.0})
        # Pydantic coerces to string for str fields
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "123"

    def test_create_item_null_price(self):
        """Should reject null price."""
        r = client.post("/items", json={"name": "widget", "price": None})
        assert r.status_code == 422

    def test_create_item_null_name(self):
        """Should reject null name."""
        r = client.post("/items", json={"name": None, "price": 10.0})
        assert r.status_code == 422


class TestCreateItemEdgeCases:
    """Test create_item edge cases and boundary conditions."""

    def test_create_item_extra_fields_ignored(self):
        """Should ignore extra fields in request."""
        r = client.post("/items", json={
            "name": "widget",
            "price": 10.0,
            "extra_field": "ignored",
            "another": 123
        })
        assert r.status_code == 200
        data = r.json()
        assert "extra_field" not in data

    def test_create_item_very_large_price(self):
        """Should accept very large price values."""
        large_price = 1e10
        r = client.post("/items", json={"name": "expensive", "price": large_price})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == large_price

    def test_create_item_precision_price(self):
        """Should preserve decimal precision."""
        price = 19.99
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == price

    def test_create_item_response_structure(self):
        """Should return consistent response structure."""
        r = client.post("/items", json={"name": "test", "price": 5.0})
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data
        assert len(data) == 3  # Only these 3 fields

    def test_create_item_multiple_calls(self):
        """Should handle multiple sequential create requests."""
        for i in range(5):
            r = client.post("/items", json={"name": f"item{i}", "price": float(i+1)})
            assert r.status_code == 200
            data = r.json()
            assert data["name"] == f"item{i}"
            assert data["price"] == float(i+1)
