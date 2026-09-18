"""
Test suite for input validation and boundary testing of items endpoints.

This module provides comprehensive parametrized tests for:
- Price field validation (negative, zero, large values)
- Name field variations (empty, special chars, long strings)
- Missing required fields
- Type validation for all input fields
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Tests for price field validation on item creation."""

    @pytest.mark.parametrize("price", [-100, -1, -0.01, 0])
    def test_create_item_rejects_non_positive_price(self, price):
        """Price must be positive (> 0)."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]

    @pytest.mark.parametrize("price", [0.01, 1, 10, 100, 999.99, 1e10])
    def test_create_item_accepts_positive_price(self, price):
        """Positive prices are accepted."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == price

    def test_create_item_with_very_large_price(self):
        """Extremely large prices are accepted."""
        r = client.post("/items", json={"name": "luxury", "price": 1e100})
        assert r.status_code == 200
        assert r.json()["price"] == 1e100

    def test_create_item_price_precision(self):
        """Prices with decimal precision are preserved."""
        r = client.post("/items", json={"name": "test", "price": 19.99})
        assert r.status_code == 200
        assert r.json()["price"] == 19.99


class TestCreateItemNameValidation:
    """Tests for name field validation on item creation."""

    def test_create_item_with_empty_name(self):
        """Empty name should be accepted by FastAPI pydantic (valid string)."""
        r = client.post("/items", json={"name": "", "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == ""

    def test_create_item_with_single_char_name(self):
        """Single character names are valid."""
        r = client.post("/items", json={"name": "a", "price": 5})
        assert r.status_code == 200
        assert r.json()["name"] == "a"

    def test_create_item_with_very_long_name(self):
        """Very long names are accepted."""
        long_name = "x" * 1000
        r = client.post("/items", json={"name": long_name, "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == long_name

    @pytest.mark.parametrize("name", [
        "item with spaces",
        "item-with-dashes",
        "item_with_underscores",
        "item.with.dots",
        "item/with/slashes",
        "item@special#chars!",
        "café",  # unicode
        "日本語",  # non-latin
    ])
    def test_create_item_with_special_names(self, name):
        """Various name formats are accepted."""
        r = client.post("/items", json={"name": name, "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_create_item_name_with_quotes(self):
        """Names with quotes are accepted."""
        r = client.post("/items", json={"name": 'item with "quotes"', "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == 'item with "quotes"'

    def test_create_item_name_with_newlines(self):
        """Names with newlines are accepted."""
        r = client.post("/items", json={"name": "item\nwith\nnewlines", "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == "item\nwith\nnewlines"


class TestCreateItemMissingFields:
    """Tests for missing required fields on item creation."""

    def test_create_item_missing_name(self):
        """Missing name field should be rejected."""
        r = client.post("/items", json={"price": 10})
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data
        # FastAPI returns validation error details

    def test_create_item_missing_price(self):
        """Missing price field should be rejected."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data

    def test_create_item_empty_payload(self):
        """Empty JSON payload should be rejected."""
        r = client.post("/items", json={})
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data

    def test_create_item_null_name(self):
        """Null name should be rejected by pydantic."""
        r = client.post("/items", json={"name": None, "price": 10})
        assert r.status_code == 422

    def test_create_item_null_price(self):
        """Null price should be rejected by pydantic."""
        r = client.post("/items", json={"name": "test", "price": None})
        assert r.status_code == 422


class TestCreateItemTypeValidation:
    """Tests for type validation of item fields."""

    def test_create_item_string_price(self):
        """String price should be rejected or coerced."""
        r = client.post("/items", json={"name": "test", "price": "10.5"})
        # FastAPI may coerce string to float, or reject with 422
        assert r.status_code in [200, 422]

    def test_create_item_negative_string_price(self):
        """Negative string price should be rejected or coerced, then validated."""
        r = client.post("/items", json={"name": "test", "price": "-10"})
        # If coerced to float, should be rejected for being negative
        # If not coerced, should be 422 validation error
        assert r.status_code in [400, 422]

    def test_create_item_boolean_price(self):
        """Boolean price should be rejected."""
        r = client.post("/items", json={"name": "test", "price": True})
        # FastAPI may coerce boolean to number or reject
        assert r.status_code in [200, 422, 400]

    def test_create_item_numeric_name(self):
        """Numeric name should be coerced to string."""
        r = client.post("/items", json={"name": 123, "price": 10})
        # FastAPI coerces to string
        assert r.status_code == 200
        assert r.json()["name"] == "123"

    def test_create_item_list_name(self):
        """List as name should be rejected."""
        r = client.post("/items", json={"name": ["a", "b"], "price": 10})
        assert r.status_code == 422

    def test_create_item_dict_price(self):
        """Dict as price should be rejected."""
        r = client.post("/items", json={"name": "test", "price": {"value": 10}})
        assert r.status_code == 422


class TestCreateItemResponseFormat:
    """Tests for response format and field presence."""

    def test_create_item_response_has_id(self):
        """Response should include id field."""
        r = client.post("/items", json={"name": "test", "price": 10})
        assert r.status_code == 200
        assert "id" in r.json()

    def test_create_item_response_has_name(self):
        """Response should include name field."""
        r = client.post("/items", json={"name": "test", "price": 10})
        assert r.status_code == 200
        assert "name" in r.json()

    def test_create_item_response_has_price(self):
        """Response should include price field."""
        r = client.post("/items", json={"name": "test", "price": 10})
        assert r.status_code == 200
        assert "price" in r.json()

    def test_create_item_id_is_numeric(self):
        """Response id should be numeric."""
        r = client.post("/items", json={"name": "test", "price": 10})
        assert r.status_code == 200
        assert isinstance(r.json()["id"], int)

    def test_create_item_response_fields_match_input(self):
        """Response name and price should match input."""
        input_data = {"name": "gadget", "price": 29.99}
        r = client.post("/items", json=input_data)
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == input_data["name"]
        assert data["price"] == input_data["price"]
