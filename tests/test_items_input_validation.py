"""
Test suite for input validation on the /items endpoint.
Tests cover price boundaries, name field variations, and missing fields.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Tests for price field validation in POST /items."""

    @pytest.mark.parametrize("price", [0, -1, -100, -0.01])
    def test_create_item_rejects_zero_and_negative_price(self, price):
        """Price must be strictly positive."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    @pytest.mark.parametrize("price", [0.01, 1, 100, 999.99, 1000000])
    def test_create_item_accepts_positive_price(self, price):
        """Positive prices should be accepted."""
        r = client.post("/items", json={"name": "valid", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    def test_create_item_price_very_small_positive(self):
        """Very small positive prices should work."""
        r = client.post("/items", json={"name": "penny", "price": 0.001})
        assert r.status_code == 200
        assert r.json()["price"] == 0.001

    def test_create_item_price_very_large(self):
        """Very large prices should work."""
        r = client.post("/items", json={"name": "expensive", "price": 999999.99})
        assert r.status_code == 200
        assert r.json()["price"] == 999999.99

    def test_create_item_price_string_coercion(self):
        """Pydantic should coerce valid string prices to float."""
        r = client.post("/items", json={"name": "stringprice", "price": "42.5"})
        assert r.status_code == 200
        assert r.json()["price"] == 42.5

    def test_create_item_price_int_coercion(self):
        """Pydantic should coerce int prices to float."""
        r = client.post("/items", json={"name": "intprice", "price": 42})
        assert r.status_code == 200
        assert r.json()["price"] == 42.0


class TestCreateItemNameValidation:
    """Tests for name field validation in POST /items."""

    @pytest.mark.parametrize("name", ["a", "ab", "x" * 100, "valid name", "name-with-dash"])
    def test_create_item_accepts_various_names(self, name):
        """Different name formats should be accepted."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_create_item_name_with_special_chars(self):
        """Special characters in name should be accepted."""
        r = client.post("/items", json={"name": "item@#$%", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "item@#$%"

    def test_create_item_name_with_unicode(self):
        """Unicode characters in name should be accepted."""
        r = client.post("/items", json={"name": "café", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "café"

    def test_create_item_name_with_numbers(self):
        """Names with numbers should be accepted."""
        r = client.post("/items", json={"name": "item123", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "item123"

    def test_create_item_name_with_spaces(self):
        """Names with multiple spaces should be accepted."""
        r = client.post("/items", json={"name": "item  with   spaces", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "item  with   spaces"


class TestCreateItemMissingFields:
    """Tests for missing required fields in POST /items."""

    def test_create_item_missing_name(self):
        """Missing name field should return 422."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422

    def test_create_item_missing_price(self):
        """Missing price field should return 422."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422

    def test_create_item_missing_both_fields(self):
        """Missing both name and price should return 422."""
        r = client.post("/items", json={})
        assert r.status_code == 422

    def test_create_item_extra_fields_accepted(self):
        """Extra fields should be ignored by Pydantic."""
        r = client.post("/items", json={"name": "test", "price": 10.0, "extra": "field"})
        assert r.status_code == 200
        assert r.json()["name"] == "test"


class TestCreateItemInvalidTypes:
    """Tests for invalid field types in POST /items."""

    def test_create_item_price_invalid_string(self):
        """Non-numeric string price should return 422."""
        r = client.post("/items", json={"name": "test", "price": "not_a_number"})
        assert r.status_code == 422

    def test_create_item_price_null(self):
        """Null price should return 422."""
        r = client.post("/items", json={"name": "test", "price": None})
        assert r.status_code == 422

    def test_create_item_name_not_string(self):
        """Non-string name should be coerced or return 422."""
        r = client.post("/items", json={"name": 123, "price": 10.0})
        # Pydantic may coerce to string or reject
        assert r.status_code in [200, 422]

    def test_create_item_name_null(self):
        """Null name should return 422."""
        r = client.post("/items", json={"name": None, "price": 10.0})
        assert r.status_code == 422

    def test_create_item_price_array(self):
        """Array price should return 422."""
        r = client.post("/items", json={"name": "test", "price": [10.0]})
        assert r.status_code == 422

    def test_create_item_name_array(self):
        """Array name should return 422."""
        r = client.post("/items", json={"name": ["test"], "price": 10.0})
        assert r.status_code == 422


class TestCreateItemResponseStructure:
    """Tests for response structure of POST /items."""

    def test_create_item_response_has_required_fields(self):
        """Response should contain id, name, and price."""
        r = client.post("/items", json={"name": "test", "price": 42.5})
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_create_item_response_id_type(self):
        """Response id should be an integer."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        data = r.json()
        assert isinstance(data["id"], int)

    def test_create_item_response_name_matches_input(self):
        """Response name should match request."""
        test_name = "my_custom_item"
        r = client.post("/items", json={"name": test_name, "price": 10.0})
        assert r.json()["name"] == test_name

    def test_create_item_response_price_matches_input(self):
        """Response price should match request."""
        test_price = 99.99
        r = client.post("/items", json={"name": "test", "price": test_price})
        assert r.json()["price"] == test_price


class TestCreateItemErrorHandling:
    """Tests for error handling in POST /items."""

    def test_create_item_invalid_json(self):
        """Invalid JSON should return 422."""
        r = client.post("/items", json="not json object")
        assert r.status_code == 422

    def test_create_item_empty_body(self):
        """Empty body should return 422."""
        r = client.post("/items", json={})
        assert r.status_code == 422

    def test_create_item_wrong_http_method(self):
        """GET to /items should fail."""
        r = client.get("/items")
        assert r.status_code == 404

    def test_create_item_successful_then_retry(self):
        """Multiple successive creates should work."""
        r1 = client.post("/items", json={"name": "first", "price": 1.0})
        r2 = client.post("/items", json={"name": "second", "price": 2.0})
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r1.json()["name"] == "first"
        assert r2.json()["name"] == "second"
