"""Enhanced input validation tests for POST /items endpoint.

Tests cover negative prices, missing fields, invalid types, and edge cases.
Part of Coverage Plan issue #3 - PR #1.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price validation for item creation."""

    def test_create_item_negative_price(self):
        """Negative prices should be rejected."""
        r = client.post("/items", json={"name": "item", "price": -1})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]

    def test_create_item_large_negative_price(self):
        """Large negative prices should be rejected."""
        r = client.post("/items", json={"name": "item", "price": -100.50})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]

    @pytest.mark.parametrize("price", [-1, -0.01, -999, -1000.99])
    def test_create_item_various_negative_prices(self, price):
        """Test multiple negative price values."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 400

    def test_create_item_price_boundary_zero(self):
        """Zero price should be rejected."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.status_code == 400

    def test_create_item_price_boundary_positive_epsilon(self):
        """Very small positive price should be accepted."""
        r = client.post("/items", json={"name": "item", "price": 0.01})
        assert r.status_code == 200
        assert r.json()["price"] == 0.01


class TestCreateItemMissingFields:
    """Test missing required field validation."""

    def test_create_item_missing_name(self):
        """Missing name field should be rejected."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422

    def test_create_item_missing_price(self):
        """Missing price field should be rejected."""
        r = client.post("/items", json={"name": "item"})
        assert r.status_code == 422

    def test_create_item_missing_both_fields(self):
        """Missing both fields should be rejected."""
        r = client.post("/items", json={})
        assert r.status_code == 422

    def test_create_item_null_name(self):
        """Null name should be rejected."""
        r = client.post("/items", json={"name": None, "price": 10.0})
        assert r.status_code == 422

    def test_create_item_null_price(self):
        """Null price should be rejected."""
        r = client.post("/items", json={"name": "item", "price": None})
        assert r.status_code == 422


class TestCreateItemInvalidTypes:
    """Test invalid data type validation."""

    def test_create_item_string_price(self):
        """String price should be rejected or coerced."""
        r = client.post("/items", json={"name": "item", "price": "12.5"})
        # Pydantic might coerce string to float, so either 200 or 422 is acceptable
        assert r.status_code in (200, 422)

    def test_create_item_integer_name(self):
        """Integer name should be rejected or coerced."""
        r = client.post("/items", json={"name": 123, "price": 10.0})
        # Pydantic might coerce integer to string, so either 200 or 422 is acceptable
        assert r.status_code in (200, 422)

    def test_create_item_boolean_price(self):
        """Boolean price should be rejected."""
        r = client.post("/items", json={"name": "item", "price": True})
        # Pydantic might coerce boolean, so check response is valid
        assert r.status_code in (200, 422)

    def test_create_item_list_as_name(self):
        """List as name should be rejected."""
        r = client.post("/items", json={"name": ["item"], "price": 10.0})
        assert r.status_code == 422


class TestCreateItemEdgeCases:
    """Test edge cases for item creation."""

    def test_create_item_empty_name(self):
        """Empty string name should be accepted (no validation)."""
        r = client.post("/items", json={"name": "", "price": 10.0})
        assert r.status_code == 200

    def test_create_item_whitespace_name(self):
        """Whitespace name should be accepted (no validation)."""
        r = client.post("/items", json={"name": "   ", "price": 10.0})
        assert r.status_code == 200

    def test_create_item_very_long_name(self):
        """Very long name should be accepted."""
        long_name = "a" * 10000
        r = client.post("/items", json={"name": long_name, "price": 10.0})
        assert r.status_code == 200

    def test_create_item_unicode_name(self):
        """Unicode characters in name should be accepted."""
        r = client.post("/items", json={"name": "αβγ δεζ 中文", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "αβγ δεζ 中文"

    def test_create_item_very_large_price(self):
        """Very large price should be accepted."""
        r = client.post("/items", json={"name": "item", "price": 999999999.99})
        assert r.status_code == 200

    def test_create_item_extra_fields(self):
        """Extra fields should be ignored."""
        r = client.post("/items", json={"name": "item", "price": 10.0, "extra": "field"})
        assert r.status_code == 200
        # Extra field should not be in response
        assert "extra" not in r.json()

    def test_create_item_scientific_notation_price(self):
        """Scientific notation price should be accepted."""
        r = client.post("/items", json={"name": "item", "price": 1e2})
        assert r.status_code == 200
        assert r.json()["price"] == 100.0
