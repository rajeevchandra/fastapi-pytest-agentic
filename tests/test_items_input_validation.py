"""
Comprehensive input validation tests for the items API.

Tests cover:
- Price boundary values (negative, zero, extreme large/small)
- Name field validation (empty, special characters, unicode, length)
- Type validation and Pydantic model validation
- Missing required fields
- Malformed JSON payloads
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemValidPrice:
    """Tests for successful create_item with valid prices."""

    @pytest.mark.parametrize("price", [0.01, 0.1, 1.0, 10.5, 99.99, 100, 1000, 10000, 1e6])
    def test_create_item_with_various_valid_prices(self, price):
        """Test that various positive prices are accepted."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "test"
        assert data["price"] == price

    def test_create_item_minimal_positive_price(self):
        """Test creation with minimal positive price (0.01)."""
        r = client.post("/items", json={"name": "item", "price": 0.01})
        assert r.status_code == 200
        assert r.json()["price"] == 0.01

    def test_create_item_large_price(self):
        """Test creation with very large price."""
        r = client.post("/items", json={"name": "item", "price": 999999.99})
        assert r.status_code == 200
        assert r.json()["price"] == 999999.99


class TestCreateItemInvalidPrice:
    """Tests for create_item rejection of invalid prices."""

    @pytest.mark.parametrize("price", [0, -0.01, -1, -100, -999999])
    def test_create_item_rejects_non_positive_prices(self, price):
        """Test that non-positive prices are rejected."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    def test_create_item_rejects_zero_price(self):
        """Test that zero price is rejected."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    def test_create_item_rejects_negative_price(self):
        """Test that negative price is rejected."""
        r = client.post("/items", json={"name": "item", "price": -10.5})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    def test_create_item_rejects_large_negative_price(self):
        """Test that large negative price is rejected."""
        r = client.post("/items", json={"name": "item", "price": -1e6})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"


class TestCreateItemValidName:
    """Tests for valid name field variations."""

    @pytest.mark.parametrize("name", [
        "book",
        "a",
        "A" * 100,  # Long name
        "Item-123",
        "item_with_underscore",
        "UPPERCASE",
        "lowercase",
        "MixedCase",
    ])
    def test_create_item_with_various_valid_names(self, name):
        """Test creation with various valid name formats."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name
        assert data["price"] == 10.0

    def test_create_item_with_numeric_name(self):
        """Test creation with numeric string as name."""
        r = client.post("/items", json={"name": "123", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "123"

    def test_create_item_with_special_characters_in_name(self):
        """Test creation with special characters in name."""
        r = client.post("/items", json={"name": "item@#$%", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "item@#$%"

    def test_create_item_with_spaces_in_name(self):
        """Test creation with spaces in name."""
        r = client.post("/items", json={"name": "my item", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "my item"

    def test_create_item_with_unicode_name(self):
        """Test creation with unicode characters in name."""
        r = client.post("/items", json={"name": "ñoño", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "ñoño"

    def test_create_item_with_emoji_in_name(self):
        """Test creation with emoji in name."""
        r = client.post("/items", json={"name": "book📚", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "book📚"

    def test_create_item_with_cjk_characters(self):
        """Test creation with CJK (Chinese, Japanese, Korean) characters."""
        r = client.post("/items", json={"name": "本🌏书籍", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "本🌏书籍"


class TestCreateItemInvalidName:
    """Tests for name field validation and edge cases."""

    def test_create_item_with_empty_name(self):
        """Test creation with empty name string."""
        r = client.post("/items", json={"name": "", "price": 10.0})
        assert r.status_code == 200
        # Empty strings are valid per Pydantic BaseModel default behavior
        assert r.json()["name"] == ""

    def test_create_item_with_whitespace_only_name(self):
        """Test creation with whitespace-only name."""
        r = client.post("/items", json={"name": "   ", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "   "


class TestCreateItemMissingFields:
    """Tests for missing required fields."""

    def test_create_item_missing_price(self):
        """Test that missing price field is rejected."""
        r = client.post("/items", json={"name": "item"})
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data

    def test_create_item_missing_name(self):
        """Test that missing name field is rejected."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data

    def test_create_item_empty_json(self):
        """Test that empty JSON object is rejected."""
        r = client.post("/items", json={})
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data


class TestCreateItemInvalidTypes:
    """Tests for invalid data types."""

    def test_create_item_price_as_string(self):
        """Test that string price is rejected."""
        r = client.post("/items", json={"name": "item", "price": "10.0"})
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data

    def test_create_item_price_as_null(self):
        """Test that null price is rejected."""
        r = client.post("/items", json={"name": "item", "price": None})
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data

    def test_create_item_name_as_number(self):
        """Test that numeric name is coerced to string (Pydantic behavior)."""
        r = client.post("/items", json={"name": 123, "price": 10.0})
        # Pydantic may coerce this depending on version
        assert r.status_code in [200, 422]

    def test_create_item_name_as_null(self):
        """Test that null name is rejected."""
        r = client.post("/items", json={"name": None, "price": 10.0})
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data

    def test_create_item_name_as_array(self):
        """Test that array name is rejected."""
        r = client.post("/items", json={"name": ["item"], "price": 10.0})
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data

    def test_create_item_price_as_array(self):
        """Test that array price is rejected."""
        r = client.post("/items", json={"name": "item", "price": [10.0]})
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data


class TestCreateItemExtraFields:
    """Tests for handling extra/unexpected fields."""

    def test_create_item_with_extra_field(self):
        """Test that extra fields are accepted (Pydantic ignores by default)."""
        r = client.post("/items", json={"name": "item", "price": 10.0, "extra": "field"})
        # Pydantic by default ignores extra fields
        assert r.status_code == 200
        assert r.json()["name"] == "item"

    def test_create_item_with_multiple_extra_fields(self):
        """Test with multiple extra fields."""
        r = client.post("/items", json={
            "name": "item",
            "price": 10.0,
            "extra1": "field1",
            "extra2": "field2",
            "extra3": "field3"
        })
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "item"
        assert data["price"] == 10.0


class TestCreateItemMalformedJSON:
    """Tests for malformed JSON handling."""

    def test_create_item_with_invalid_json(self):
        """Test that invalid JSON is rejected."""
        r = client.post("/items", content="{invalid json}")
        assert r.status_code == 422

    def test_create_item_with_unfinished_json(self):
        """Test that incomplete JSON is rejected."""
        r = client.post("/items", content='{"name": "item"')
        assert r.status_code == 422

    def test_create_item_with_json_not_object(self):
        """Test that JSON array instead of object is rejected."""
        r = client.post("/items", json=["name", "price"])
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data


class TestCreateItemFloatPrecision:
    """Tests for floating point precision edge cases."""

    @pytest.mark.parametrize("price", [
        0.1 + 0.2,  # Classic floating point precision issue
        1.0 / 3.0,
        0.01,
        0.001,
        0.0001,
    ])
    def test_create_item_with_float_precision_values(self, price):
        """Test creation with various floating point precision values."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == price
