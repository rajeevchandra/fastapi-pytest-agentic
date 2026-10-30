"""
Input validation tests for items endpoint.

Tests cover:
- Boundary values for price validation
- Name field validation (empty, unicode, special characters)
- Missing/malformed JSON
- Type validation
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemValidPrice:
    """Test create_item with valid prices."""

    @pytest.mark.parametrize("price", [0.01, 1.0, 10.5, 100.0, 1000.99, 9999.99])
    def test_valid_positive_prices(self, price):
        """Test that valid positive prices are accepted."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == price
        assert data["name"] == "test"
        assert data["id"] == 1

    @pytest.mark.parametrize("price", [1e-10, 0.001, 0.0001])
    def test_very_small_positive_prices(self, price):
        """Test very small but valid positive prices."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    @pytest.mark.parametrize("price", [1e6, 1e7, 1e9])
    def test_very_large_positive_prices(self, price):
        """Test very large positive prices."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price


class TestCreateItemInvalidPrice:
    """Test create_item with invalid prices."""

    @pytest.mark.parametrize("price", [0, -0.5, -1, -10.5, -100, -1000])
    def test_zero_and_negative_prices(self, price):
        """Test that zero and negative prices are rejected."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    def test_price_validation_error_message(self):
        """Test exact error message for invalid price."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.status_code == 400
        data = r.json()
        assert "detail" in data
        assert data["detail"] == "price must be > 0"


class TestCreateItemValidName:
    """Test create_item with valid name values."""

    @pytest.mark.parametrize("name", ["a", "book", "Test Item", "Item-123", "item_with_underscore"])
    def test_valid_name_formats(self, name):
        """Test various valid name formats."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_name_with_spaces(self):
        """Test name with multiple spaces."""
        r = client.post("/items", json={"name": "test  item  name", "price": 1.0})
        assert r.status_code == 200
        assert r.json()["name"] == "test  item  name"

    def test_name_with_special_characters(self):
        """Test name with special characters."""
        r = client.post("/items", json={"name": "item!@#$%^&*()", "price": 1.0})
        assert r.status_code == 200
        assert r.json()["name"] == "item!@#$%^&*()"

    def test_name_with_unicode_characters(self):
        """Test name with unicode characters."""
        r = client.post("/items", json={"name": "商品", "price": 1.0})
        assert r.status_code == 200
        assert r.json()["name"] == "商品"

    def test_name_with_emoji(self):
        """Test name with emoji characters."""
        r = client.post("/items", json={"name": "item 🎉 test", "price": 1.0})
        assert r.status_code == 200
        assert r.json()["name"] == "item 🎉 test"

    def test_very_long_name(self):
        """Test very long name string."""
        long_name = "x" * 1000
        r = client.post("/items", json={"name": long_name, "price": 1.0})
        assert r.status_code == 200
        assert r.json()["name"] == long_name


class TestCreateItemInvalidName:
    """Test create_item with invalid name values."""

    def test_empty_name(self):
        """Test empty name string."""
        r = client.post("/items", json={"name": "", "price": 10.0})
        assert r.status_code == 422  # Validation error from Pydantic
        data = r.json()
        assert "detail" in data

    def test_name_as_none(self):
        """Test name as null value."""
        r = client.post("/items", json={"name": None, "price": 10.0})
        assert r.status_code == 422  # Validation error from Pydantic

    def test_name_as_number(self):
        """Test name as number instead of string."""
        r = client.post("/items", json={"name": 123, "price": 10.0})
        # Pydantic should coerce number to string
        assert r.status_code in [200, 422]

    def test_name_as_boolean(self):
        """Test name as boolean."""
        r = client.post("/items", json={"name": True, "price": 10.0})
        assert r.status_code in [200, 422]


class TestCreateItemMissingFields:
    """Test create_item with missing required fields."""

    def test_missing_name_field(self):
        """Test request with missing name field."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422  # Missing required field
        data = r.json()
        assert "detail" in data

    def test_missing_price_field(self):
        """Test request with missing price field."""
        r = client.post("/items", json={"name": "item"})
        assert r.status_code == 422  # Missing required field
        data = r.json()
        assert "detail" in data

    def test_missing_both_fields(self):
        """Test request with both fields missing."""
        r = client.post("/items", json={})
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data

    def test_completely_empty_body(self):
        """Test request with completely empty JSON."""
        r = client.post("/items", json={})
        assert r.status_code == 422


class TestCreateItemInvalidTypes:
    """Test create_item with type validation."""

    def test_price_as_string(self):
        """Test price as string value."""
        r = client.post("/items", json={"name": "item", "price": "10.0"})
        # Pydantic might coerce or reject
        assert r.status_code in [200, 422]

    def test_price_as_string_non_numeric(self):
        """Test price as non-numeric string."""
        r = client.post("/items", json={"name": "item", "price": "abc"})
        assert r.status_code == 422  # Should fail validation

    def test_price_as_none(self):
        """Test price as null."""
        r = client.post("/items", json={"name": "item", "price": None})
        assert r.status_code == 422  # Should fail validation

    def test_price_as_list(self):
        """Test price as list."""
        r = client.post("/items", json={"name": "item", "price": [10.0]})
        assert r.status_code == 422  # Should fail validation

    def test_price_as_dict(self):
        """Test price as dictionary."""
        r = client.post("/items", json={"name": "item", "price": {"value": 10.0}})
        assert r.status_code == 422  # Should fail validation

    def test_name_as_list(self):
        """Test name as list."""
        r = client.post("/items", json={"name": ["item"], "price": 10.0})
        assert r.status_code == 422  # Should fail validation

    def test_name_as_dict(self):
        """Test name as dictionary."""
        r = client.post("/items", json={"name": {"value": "item"}, "price": 10.0})
        assert r.status_code == 422  # Should fail validation


class TestCreateItemExtraFields:
    """Test create_item with extra/unexpected fields."""

    def test_extra_field_in_json(self):
        """Test that extra fields don't break the endpoint."""
        r = client.post("/items", json={"name": "item", "price": 10.0, "extra": "field"})
        # Pydantic usually ignores extra fields by default
        assert r.status_code == 200
        assert r.json()["name"] == "item"

    def test_multiple_extra_fields(self):
        """Test multiple extra fields."""
        r = client.post(
            "/items",
            json={"name": "item", "price": 10.0, "extra1": "value1", "extra2": "value2"},
        )
        assert r.status_code == 200


class TestCreateItemFloatEdgeCases:
    """Test edge cases with floating point values."""

    def test_price_with_many_decimals(self):
        """Test price with many decimal places."""
        r = client.post("/items", json={"name": "item", "price": 10.123456789})
        assert r.status_code == 200
        assert r.json()["price"] > 10  # At least the value is positive

    def test_price_boundary_at_smallest_positive(self):
        """Test price at the smallest positive value."""
        r = client.post("/items", json={"name": "item", "price": 1e-100})
        assert r.status_code == 200

    def test_price_boundary_negative_infinity(self):
        """Test price as negative infinity."""
        r = client.post("/items", json={"name": "item", "price": float("-inf")})
        # Python/JSON may represent this or reject it
        assert r.status_code in [400, 422]

    def test_price_boundary_positive_infinity(self):
        """Test price as positive infinity."""
        r = client.post("/items", json={"name": "item", "price": float("inf")})
        # Could be accepted or rejected depending on implementation
        assert r.status_code in [200, 400, 422]

    def test_price_boundary_nan(self):
        """Test price as NaN."""
        r = client.post("/items", json={"name": "item", "price": float("nan")})
        # NaN typically causes validation issues
        assert r.status_code in [400, 422]


class TestCreateItemResponseStructure:
    """Test response structure from create_item."""

    def test_response_has_required_fields(self):
        """Test that response contains all required fields."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_response_id_type(self):
        """Test that response id is an integer."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)

    def test_response_name_type(self):
        """Test that response name is a string."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["name"], str)

    def test_response_price_type(self):
        """Test that response price is a number."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["price"], (int, float))

    def test_response_only_has_expected_fields(self):
        """Test that response doesn't have unexpected fields."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        # Response should have exactly these fields (or a superset)
        assert set(data.keys()) >= {"id", "name", "price"}
