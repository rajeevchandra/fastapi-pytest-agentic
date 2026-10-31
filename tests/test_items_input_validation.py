"""
Part 1: Input Validation Testing - Parametrized tests for ItemIn model validation,
price boundary value testing, name field validation, and malformed JSON handling.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemValidPrice:
    """Test cases for valid price values."""

    @pytest.mark.parametrize("price", [0.01, 1, 10, 100, 1000, 9999.99, 1e6, 1e9])
    def test_create_item_with_valid_prices(self, price):
        """Test item creation with various valid price values."""
        r = client.post("/items", json={"name": "test_item", "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == price
        assert data["name"] == "test_item"

    def test_create_item_min_positive_price(self):
        """Test item creation with minimum positive price."""
        r = client.post("/items", json={"name": "item", "price": 0.01})
        assert r.status_code == 200
        assert r.json()["price"] == 0.01

    def test_create_item_large_price(self):
        """Test item creation with very large price."""
        r = client.post("/items", json={"name": "expensive", "price": 1e10})
        assert r.status_code == 200
        assert r.json()["price"] == 1e10


class TestCreateItemInvalidPrice:
    """Test cases for invalid price values that should be rejected."""

    @pytest.mark.parametrize("price", [0, -1, -0.01, -100, -1000])
    def test_create_item_with_invalid_prices(self, price):
        """Test item creation is rejected with non-positive prices."""
        r = client.post("/items", json={"name": "bad_item", "price": price})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    def test_create_item_zero_price(self):
        """Test item creation is rejected when price is zero."""
        r = client.post("/items", json={"name": "free", "price": 0})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    def test_create_item_negative_price(self):
        """Test item creation is rejected when price is negative."""
        r = client.post("/items", json={"name": "invalid", "price": -50})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    def test_create_item_very_negative_price(self):
        """Test item creation is rejected with very negative price."""
        r = client.post("/items", json={"name": "extreme", "price": -1e10})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"


class TestCreateItemNameValidation:
    """Test cases for name field validation."""

    @pytest.mark.parametrize("name", ["", " ", "  "])
    def test_create_item_with_empty_name(self, name):
        """Test that empty or whitespace-only names are handled."""
        r = client.post("/items", json={"name": name, "price": 10})
        # FastAPI will accept these; they pass model validation
        # Our focus is on what the API actually does, not what it should do
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name

    def test_create_item_with_long_name(self):
        """Test item creation with very long name."""
        long_name = "a" * 1000
        r = client.post("/items", json={"name": long_name, "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == long_name

    @pytest.mark.parametrize("name", [
        "simple",
        "with spaces",
        "with-dashes",
        "with_underscores",
        "with.dots",
        "CamelCase",
        "UPPERCASE",
    ])
    def test_create_item_with_valid_names(self, name):
        """Test item creation with various valid name formats."""
        r = client.post("/items", json={"name": name, "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == name

    @pytest.mark.parametrize("name", [
        "café",
        "日本語",
        "Ελληνικά",
        "العربية",
        "🎉",
        "emoji_🚀_text",
    ])
    def test_create_item_with_unicode_names(self, name):
        """Test item creation with unicode and emoji names."""
        r = client.post("/items", json={"name": name, "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == name

    @pytest.mark.parametrize("name", [
        "special!chars",
        "with@symbol",
        "with#hash",
        "with$dollar",
        "with%percent",
        "with&ampersand",
        "with*asterisk",
        "with/slash",
        "with\\backslash",
        "with|pipe",
        "with<bracket",
        "with>bracket",
    ])
    def test_create_item_with_special_char_names(self, name):
        """Test item creation with special characters in name."""
        r = client.post("/items", json={"name": name, "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == name


class TestCreateItemMalformedJson:
    """Test cases for malformed JSON and missing fields."""

    def test_create_item_missing_name(self):
        """Test that request without name field is rejected."""
        r = client.post("/items", json={"price": 10})
        assert r.status_code == 422

    def test_create_item_missing_price(self):
        """Test that request without price field is rejected."""
        r = client.post("/items", json={"name": "no_price"})
        assert r.status_code == 422

    def test_create_item_empty_json(self):
        """Test that empty JSON object is rejected."""
        r = client.post("/items", json={})
        assert r.status_code == 422

    def test_create_item_null_name(self):
        """Test that null name is rejected."""
        r = client.post("/items", json={"name": None, "price": 10})
        assert r.status_code == 422

    def test_create_item_null_price(self):
        """Test that null price is rejected."""
        r = client.post("/items", json={"name": "test", "price": None})
        assert r.status_code == 422

    def test_create_item_wrong_type_price_string(self):
        """Test that string price is rejected."""
        r = client.post("/items", json={"name": "test", "price": "not_a_number"})
        assert r.status_code == 422

    def test_create_item_wrong_type_name_number(self):
        """Test that numeric name might be coerced or rejected."""
        r = client.post("/items", json={"name": 123, "price": 10})
        # FastAPI will attempt to coerce to string
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "123"

    def test_create_item_extra_fields_ignored(self):
        """Test that extra fields in JSON are ignored."""
        r = client.post("/items", json={
            "name": "test",
            "price": 10,
            "extra_field": "ignored",
            "another": 123
        })
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "test"
        assert data["price"] == 10


class TestCreateItemPriceBoundaries:
    """Test critical price boundaries and edge cases."""

    def test_create_item_just_above_zero(self):
        """Test the boundary just above zero."""
        r = client.post("/items", json={"name": "boundary", "price": 0.001})
        assert r.status_code == 200
        assert r.json()["price"] == 0.001

    def test_create_item_just_at_zero(self):
        """Test the boundary at zero."""
        r = client.post("/items", json={"name": "zero", "price": 0})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    def test_create_item_just_below_zero(self):
        """Test the boundary just below zero."""
        r = client.post("/items", json={"name": "negative", "price": -0.001})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    @pytest.mark.parametrize("price", [1, 1.5, 2, 5, 10, 100, 1000])
    def test_create_item_round_prices(self, price):
        """Test item creation with round numbers."""
        r = client.post("/items", json={"name": "round", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    @pytest.mark.parametrize("price", [1.11, 2.22, 3.33, 9.99, 99.99])
    def test_create_item_decimal_prices(self, price):
        """Test item creation with decimal prices."""
        r = client.post("/items", json={"name": "decimal", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price


class TestCreateItemResponseStructure:
    """Test response structure and field types."""

    def test_create_item_response_has_id(self):
        """Test that response includes id field."""
        r = client.post("/items", json={"name": "test", "price": 10})
        assert r.status_code == 200
        data = r.json()
        assert "id" in data

    def test_create_item_response_has_name(self):
        """Test that response includes name field."""
        r = client.post("/items", json={"name": "test", "price": 10})
        assert r.status_code == 200
        data = r.json()
        assert "name" in data

    def test_create_item_response_has_price(self):
        """Test that response includes price field."""
        r = client.post("/items", json={"name": "test", "price": 10})
        assert r.status_code == 200
        data = r.json()
        assert "price" in data

    def test_create_item_response_id_type(self):
        """Test that id field is an integer."""
        r = client.post("/items", json={"name": "test", "price": 10})
        data = r.json()
        assert isinstance(data["id"], int)

    def test_create_item_response_name_type(self):
        """Test that name field is a string."""
        r = client.post("/items", json={"name": "test", "price": 10})
        data = r.json()
        assert isinstance(data["name"], str)

    def test_create_item_response_price_type(self):
        """Test that price field is a number."""
        r = client.post("/items", json={"name": "test", "price": 10})
        data = r.json()
        assert isinstance(data["price"], (int, float))

    def test_create_item_preserves_input_name(self):
        """Test that response name matches input."""
        input_name = "my_special_item"
        r = client.post("/items", json={"name": input_name, "price": 10})
        assert r.json()["name"] == input_name

    def test_create_item_preserves_input_price(self):
        """Test that response price matches input."""
        input_price = 123.45
        r = client.post("/items", json={"name": "test", "price": input_price})
        assert r.json()["price"] == input_price
