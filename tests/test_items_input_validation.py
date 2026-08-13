"""
Comprehensive input validation and boundary testing for /items POST endpoint.

Tests cover:
- Price boundary conditions (negative, zero, large values)
- Name field variations (empty, special chars, long strings)
- Missing required fields
- Data type validation
- Edge cases for input sanitization
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price field validation for item creation."""

    @pytest.mark.parametrize("price,should_pass", [
        (0, False),           # Zero not allowed
        (-1, False),          # Negative not allowed
        (-100.50, False),     # Large negative not allowed
        (0.01, True),         # Minimum positive value
        (0.001, True),        # Very small positive value
        (1, True),            # Integer positive value
        (999999.99, True),    # Very large price
        (1234567890.12, True),# Huge price value
    ])
    def test_create_item_price_boundaries(self, price, should_pass):
        """Test various price values to ensure proper validation."""
        response = client.post("/items", json={"name": "test", "price": price})
        
        if should_pass:
            assert response.status_code == 200, f"Expected success for price={price}"
            assert response.json()["price"] == price
        else:
            assert response.status_code == 400, f"Expected failure for price={price}"
            assert "price must be > 0" in response.json()["detail"]

    def test_create_item_zero_price_rejected(self):
        """Verify zero price is explicitly rejected."""
        response = client.post("/items", json={"name": "book", "price": 0})
        assert response.status_code == 400
        assert response.json()["detail"] == "price must be > 0"

    def test_create_item_negative_price_rejected(self):
        """Verify negative prices are rejected."""
        response = client.post("/items", json={"name": "book", "price": -5.99})
        assert response.status_code == 400
        assert response.json()["detail"] == "price must be > 0"

    def test_create_item_very_large_price_accepted(self):
        """Verify very large prices are accepted when positive."""
        response = client.post("/items", json={"name": "diamond", "price": 999999999.99})
        assert response.status_code == 200
        assert response.json()["price"] == 999999999.99


class TestCreateItemNameValidation:
    """Test name field validation for item creation."""

    @pytest.mark.parametrize("name,should_pass", [
        ("", False),                    # Empty string
        (" ", True),                    # Space is valid string
        ("a", True),                    # Single character
        ("test", True),                 # Normal name
        ("Test Item #123", True),       # With special chars
        ("名前", True),                   # Unicode characters
        ("a" * 500, True),              # Very long name
        ("name\nwith\nnewlines", True), # Newlines in string
        ("tab\tname", True),            # Tab character
        ("@#$%^&*()", True),            # Special characters
    ])
    def test_create_item_name_variations(self, name, should_pass):
        """Test various name values for item creation."""
        response = client.post("/items", json={"name": name, "price": 10.0})
        
        if should_pass:
            assert response.status_code == 200, f"Expected success for name={repr(name)}"
            assert response.json()["name"] == name
        else:
            assert response.status_code != 200, f"Expected failure for name={repr(name)}"

    def test_create_item_empty_name_rejected(self):
        """Verify empty string for name is rejected (FastAPI validation)."""
        response = client.post("/items", json={"name": "", "price": 10.0})
        # FastAPI rejects empty strings by default
        assert response.status_code == 422

    def test_create_item_normal_name_accepted(self):
        """Verify normal names are accepted."""
        response = client.post("/items", json={"name": "Book", "price": 15.99})
        assert response.status_code == 200
        assert response.json()["name"] == "Book"

    def test_create_item_long_name_accepted(self):
        """Verify very long names are accepted."""
        long_name = "x" * 1000
        response = client.post("/items", json={"name": long_name, "price": 9.99})
        assert response.status_code == 200
        assert response.json()["name"] == long_name

    def test_create_item_special_chars_in_name(self):
        """Verify names with special characters are accepted."""
        special_name = "Item #1 @ 50%"
        response = client.post("/items", json={"name": special_name, "price": 10.0})
        assert response.status_code == 200
        assert response.json()["name"] == special_name

    def test_create_item_unicode_name(self):
        """Verify unicode names are accepted."""
        unicode_name = "商品"
        response = client.post("/items", json={"name": unicode_name, "price": 10.0})
        assert response.status_code == 200
        assert response.json()["name"] == unicode_name


class TestCreateItemMissingFields:
    """Test handling of missing required fields."""

    def test_create_item_missing_name(self):
        """Verify request is rejected when name field is missing."""
        response = client.post("/items", json={"price": 10.0})
        assert response.status_code == 422
        error = response.json()
        assert "detail" in error

    def test_create_item_missing_price(self):
        """Verify request is rejected when price field is missing."""
        response = client.post("/items", json={"name": "test"})
        assert response.status_code == 422
        error = response.json()
        assert "detail" in error

    def test_create_item_both_fields_missing(self):
        """Verify request is rejected when both fields are missing."""
        response = client.post("/items", json={})
        assert response.status_code == 422
        error = response.json()
        assert "detail" in error


class TestCreateItemDataTypeValidation:
    """Test data type validation for item fields."""

    def test_create_item_price_as_string_rejected(self):
        """Verify string value for price is rejected or coerced."""
        response = client.post("/items", json={"name": "test", "price": "10.0"})
        # FastAPI attempts type coercion, should succeed with string "10.0"
        assert response.status_code == 200
        assert response.json()["price"] == 10.0

    def test_create_item_price_invalid_string_rejected(self):
        """Verify non-numeric string for price is rejected."""
        response = client.post("/items", json={"name": "test", "price": "abc"})
        assert response.status_code == 422
        error = response.json()
        assert "detail" in error

    def test_create_item_name_as_number(self):
        """Verify number for name field is coerced to string."""
        response = client.post("/items", json={"name": 123, "price": 10.0})
        assert response.status_code == 200

    def test_create_item_null_name_rejected(self):
        """Verify null value for name is rejected."""
        response = client.post("/items", json={"name": None, "price": 10.0})
        assert response.status_code == 422

    def test_create_item_null_price_rejected(self):
        """Verify null value for price is rejected."""
        response = client.post("/items", json={"name": "test", "price": None})
        assert response.status_code == 422


class TestCreateItemExtraFields:
    """Test handling of extra/unknown fields."""

    def test_create_item_with_extra_fields(self):
        """Verify extra fields don't break item creation."""
        response = client.post("/items", json={
            "name": "test",
            "price": 10.0,
            "description": "extra field",
            "category": "book"
        })
        # FastAPI should accept and ignore extra fields
        assert response.status_code == 200
        assert response.json()["name"] == "test"
        assert response.json()["price"] == 10.0

    def test_create_item_response_has_correct_fields(self):
        """Verify response contains required fields and correct structure."""
        response = client.post("/items", json={"name": "test", "price": 9.99})
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data
        assert data["id"] == 1
        assert data["name"] == "test"
        assert data["price"] == 9.99

    def test_create_item_response_format(self):
        """Verify response has correct field types."""
        response = client.post("/items", json={"name": "widget", "price": 25.50})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))


class TestCreateItemIntegration:
    """Integration tests for item creation."""

    def test_create_multiple_items_with_various_prices(self):
        """Verify multiple items can be created with different prices."""
        prices = [0.99, 10.0, 100.50, 9999.99]
        for i, price in enumerate(prices):
            response = client.post("/items", json={"name": f"item{i}", "price": price})
            assert response.status_code == 200
            assert response.json()["price"] == price

    def test_create_item_then_verify_response(self):
        """Create an item and verify all response fields."""
        response = client.post("/items", json={"name": "book", "price": 15.99})
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "book"
        assert data["price"] == 15.99
        assert len(data) == 3  # Should have exactly 3 fields
