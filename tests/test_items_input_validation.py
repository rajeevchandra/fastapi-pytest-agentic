"""
Comprehensive input validation tests for the POST /items endpoint.
Tests edge cases, boundary values, error handling, and data validation.
"""
from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price validation for create item endpoint."""

    def test_create_item_positive_price(self):
        """Valid positive price should succeed."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["price"] == 10.0

    def test_create_item_small_positive_price(self):
        """Small positive price (0.01) should succeed."""
        r = client.post("/items", json={"name": "item", "price": 0.01})
        assert r.status_code == 200
        assert r.json()["price"] == 0.01

    def test_create_item_large_price(self):
        """Large price value should succeed."""
        r = client.post("/items", json={"name": "expensive", "price": 999999.99})
        assert r.status_code == 200
        assert r.json()["price"] == 999999.99

    @pytest.mark.parametrize("invalid_price", [0, -1, -0.01, -100, -999999.99])
    def test_create_item_invalid_price(self, invalid_price):
        """Zero and negative prices should be rejected."""
        r = client.post("/items", json={"name": "item", "price": invalid_price})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]

    @pytest.mark.parametrize("price_type", [
        "10.5",  # string instead of number
        None,    # null value
        True,    # boolean
    ])
    def test_create_item_invalid_price_type(self, price_type):
        """Invalid price types should be rejected with 422 validation error."""
        r = client.post("/items", json={"name": "item", "price": price_type})
        assert r.status_code == 422


class TestCreateItemNameValidation:
    """Test name validation for create item endpoint."""

    def test_create_item_valid_name(self):
        """Standard name should succeed."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "book"

    def test_create_item_single_char_name(self):
        """Single character name should succeed."""
        r = client.post("/items", json={"name": "a", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "a"

    def test_create_item_long_name(self):
        """Long name should succeed."""
        long_name = "a" * 255
        r = client.post("/items", json={"name": long_name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == long_name

    def test_create_item_name_with_spaces(self):
        """Name with spaces should succeed."""
        r = client.post("/items", json={"name": "my book", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "my book"

    def test_create_item_name_with_special_chars(self):
        """Name with special characters should succeed."""
        r = client.post("/items", json={"name": "book-v2.0 ($99)", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "book-v2.0 ($99)"

    @pytest.mark.parametrize("invalid_name", [
        "",              # empty string
        "   ",          # whitespace only
        None,           # null value
    ])
    def test_create_item_invalid_name(self, invalid_name):
        """Empty, whitespace-only, and null names should be rejected."""
        r = client.post("/items", json={"name": invalid_name, "price": 10.0})
        assert r.status_code == 422

    @pytest.mark.parametrize("name_type", [
        10,        # number instead of string
        10.5,      # float instead of string
        True,      # boolean
        [],        # list
        {},        # dict
    ])
    def test_create_item_invalid_name_type(self, name_type):
        """Invalid name types should be rejected with 422 validation error."""
        r = client.post("/items", json={"name": name_type, "price": 10.0})
        assert r.status_code == 422


class TestCreateItemMissingFields:
    """Test handling of missing required fields."""

    def test_create_item_missing_name(self):
        """Missing name field should be rejected."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422

    def test_create_item_missing_price(self):
        """Missing price field should be rejected."""
        r = client.post("/items", json={"name": "book"})
        assert r.status_code == 422

    def test_create_item_missing_both_fields(self):
        """Missing both fields should be rejected."""
        r = client.post("/items", json={})
        assert r.status_code == 422


class TestCreateItemExtraFields:
    """Test handling of extra fields in request."""

    def test_create_item_with_extra_field(self):
        """Extra fields should be accepted and ignored by Pydantic."""
        r = client.post("/items", json={
            "name": "book",
            "price": 10.0,
            "extra_field": "should_be_ignored"
        })
        assert r.status_code == 200
        data = r.json()
        assert "extra_field" not in data
        assert data["name"] == "book"
        assert data["price"] == 10.0

    def test_create_item_with_multiple_extra_fields(self):
        """Multiple extra fields should be accepted and ignored."""
        r = client.post("/items", json={
            "name": "book",
            "price": 10.0,
            "description": "test",
            "quantity": 5,
            "category": "fiction"
        })
        assert r.status_code == 200
        data = r.json()
        assert "description" not in data
        assert "quantity" not in data
        assert "category" not in data


class TestCreateItemRequestFormat:
    """Test handling of various request formats and malformed JSON."""

    def test_create_item_valid_json(self):
        """Well-formed JSON should succeed."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert r.status_code == 200

    def test_create_item_empty_json(self):
        """Empty JSON object should fail validation."""
        r = client.post("/items", json={})
        assert r.status_code == 422

    def test_create_item_with_unicode_name(self):
        """Unicode characters in name should be handled correctly."""
        r = client.post("/items", json={"name": "café", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "café"

    def test_create_item_with_emoji_name(self):
        """Emoji in name should be handled correctly."""
        r = client.post("/items", json={"name": "book 📚", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "book 📚"


class TestCreateItemResponseStructure:
    """Test the structure and content of successful responses."""

    def test_create_item_response_has_required_fields(self):
        """Response should contain id, name, and price fields."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_create_item_response_id_is_valid(self):
        """Response id should be a positive integer."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        data = r.json()
        assert isinstance(data["id"], int)
        assert data["id"] > 0

    def test_create_item_response_preserves_input_values(self):
        """Response should preserve the input name and price values."""
        test_name = "test_book_v2.0"
        test_price = 19.99
        r = client.post("/items", json={"name": test_name, "price": test_price})
        data = r.json()
        assert data["name"] == test_name
        assert data["price"] == test_price

    def test_create_item_response_content_type(self):
        """Response should have JSON content type."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert "application/json" in r.headers.get("content-type", "")
