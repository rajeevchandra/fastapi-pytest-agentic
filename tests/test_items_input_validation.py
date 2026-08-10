"""Input validation and boundary testing for items endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price field validation and boundary conditions."""

    @pytest.mark.parametrize("price,expected_status", [
        (0, 400),          # Zero price
        (-1, 400),         # Negative price
        (-0.01, 400),      # Small negative
        (-999.99, 400),    # Large negative
        (0.001, 200),      # Very small positive
        (0.01, 200),       # Small positive
        (1, 200),          # Integer positive
        (999999.99, 200),  # Large positive
        (1e10, 200),       # Very large number
    ])
    def test_create_item_price_boundaries(self, price, expected_status):
        """Test various price boundary values."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == expected_status
        if expected_status == 200:
            assert r.json()["price"] == price
        else:
            assert r.json()["detail"] == "price must be > 0"

    def test_create_item_zero_price_error(self):
        """Explicit test for zero price rejection."""
        r = client.post("/items", json={"name": "zero_test", "price": 0})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]

    def test_create_item_negative_price_error(self):
        """Explicit test for negative price rejection."""
        r = client.post("/items", json={"name": "neg_test", "price": -5.0})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]


class TestCreateItemNameValidation:
    """Test name field validation and edge cases."""

    @pytest.mark.parametrize("name,expected_status", [
        ("book", 200),                          # Simple string
        ("A", 200),                             # Single character
        ("a" * 100, 200),                       # Long string
        ("with spaces", 200),                   # String with spaces
        ("with-dashes", 200),                   # String with dashes
        ("with_underscores", 200),              # String with underscores
        ("123", 200),                           # Numeric string
        ("UPPERCASE", 200),                     # Uppercase letters
        ("MixedCase123", 200),                  # Mixed case with numbers
        ("item (special)", 200),                # String with parentheses
        ("item/product", 200),                  # String with slash
    ])
    def test_create_item_name_variations(self, name, expected_status):
        """Test various name field values."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == expected_status
        if expected_status == 200:
            assert r.json()["name"] == name

    def test_create_item_empty_name(self):
        """Test that empty name is accepted (no validation in current API)."""
        r = client.post("/items", json={"name": "", "price": 10.0})
        # Current API doesn't validate empty name, so it should succeed
        assert r.status_code == 200
        assert r.json()["name"] == ""

    def test_create_item_whitespace_name(self):
        """Test whitespace-only name."""
        r = client.post("/items", json={"name": "   ", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "   "

    def test_create_item_special_characters_in_name(self):
        """Test special characters in name."""
        special_name = "item!@#$%^&*()"
        r = client.post("/items", json={"name": special_name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == special_name

    def test_create_item_unicode_name(self):
        """Test unicode characters in name."""
        unicode_name = "café ☕ 北京"
        r = client.post("/items", json={"name": unicode_name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == unicode_name


class TestCreateItemMissingFields:
    """Test behavior with missing required fields."""

    def test_create_item_missing_name(self):
        """Test creating item without name field."""
        r = client.post("/items", json={"price": 10.0})
        # Pydantic validation should reject
        assert r.status_code == 422
        assert "detail" in r.json()

    def test_create_item_missing_price(self):
        """Test creating item without price field."""
        r = client.post("/items", json={"name": "test"})
        # Pydantic validation should reject
        assert r.status_code == 422
        assert "detail" in r.json()

    def test_create_item_empty_body(self):
        """Test creating item with empty JSON body."""
        r = client.post("/items", json={})
        # Pydantic validation should reject both fields
        assert r.status_code == 422
        assert "detail" in r.json()

    def test_create_item_null_name(self):
        """Test creating item with null name."""
        r = client.post("/items", json={"name": None, "price": 10.0})
        # Pydantic validation should reject null name
        assert r.status_code == 422

    def test_create_item_null_price(self):
        """Test creating item with null price."""
        r = client.post("/items", json={"name": "test", "price": None})
        # Pydantic validation should reject null price
        assert r.status_code == 422


class TestCreateItemTypeValidation:
    """Test type validation for input fields."""

    def test_create_item_name_as_number(self):
        """Test providing numeric type for name field."""
        r = client.post("/items", json={"name": 123, "price": 10.0})
        # FastAPI/Pydantic coerces or validates types
        # Number should be coerced to string "123"
        assert r.status_code == 200
        assert r.json()["name"] == "123"

    def test_create_item_price_as_string(self):
        """Test providing string numeric value for price."""
        r = client.post("/items", json={"name": "test", "price": "10.5"})
        # Pydantic should coerce valid numeric string
        assert r.status_code == 200
        assert r.json()["price"] == 10.5

    def test_create_item_price_as_invalid_string(self):
        """Test providing non-numeric string for price."""
        r = client.post("/items", json={"name": "test", "price": "invalid"})
        # Pydantic validation should reject
        assert r.status_code == 422

    def test_create_item_price_as_list(self):
        """Test providing list for price."""
        r = client.post("/items", json={"name": "test", "price": [10.0]})
        # Pydantic validation should reject
        assert r.status_code == 422

    def test_create_item_name_as_dict(self):
        """Test providing dict for name."""
        r = client.post("/items", json={"name": {"value": "test"}, "price": 10.0})
        # Pydantic validation should reject
        assert r.status_code == 422


class TestCreateItemResponseStructure:
    """Test response structure for valid create requests."""

    def test_create_item_response_has_required_fields(self):
        """Test that response contains all required fields."""
        r = client.post("/items", json={"name": "book", "price": 12.5})
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_create_item_response_field_types(self):
        """Test response field types."""
        r = client.post("/items", json={"name": "book", "price": 12.5})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_create_item_preserves_price_value(self):
        """Test that price value is preserved in response."""
        test_price = 25.75
        r = client.post("/items", json={"name": "item", "price": test_price})
        assert r.status_code == 200
        assert r.json()["price"] == test_price

    def test_create_item_preserves_name_value(self):
        """Test that name value is preserved in response."""
        test_name = "special-item_123"
        r = client.post("/items", json={"name": test_name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == test_name


class TestCreateItemEdgeCases:
    """Test edge cases and unusual scenarios."""

    def test_create_item_extra_fields_ignored(self):
        """Test that extra fields in request are ignored."""
        r = client.post("/items", json={
            "name": "book",
            "price": 10.0,
            "extra_field": "ignored",
            "another_extra": 123
        })
        # Should succeed and ignore extra fields
        assert r.status_code == 200
        assert r.json()["name"] == "book"

    def test_create_item_float_as_price(self):
        """Test various float formats for price."""
        test_cases = [
            1.0, 1.1, 1.01, 1.001, 0.1, 0.01, 0.001,
            999.999, 1000000.0
        ]
        for price in test_cases:
            r = client.post("/items", json={"name": "test", "price": price})
            assert r.status_code == 200

    def test_create_item_scientific_notation_price(self):
        """Test scientific notation for price."""
        r = client.post("/items", json={"name": "test", "price": 1e5})
        assert r.status_code == 200
        assert r.json()["price"] == 100000.0

    def test_create_item_very_large_string_name(self):
        """Test very large name string."""
        large_name = "x" * 10000
        r = client.post("/items", json={"name": large_name, "price": 10.0})
        assert r.status_code == 200
        assert len(r.json()["name"]) == 10000

    def test_create_item_boundary_price_just_above_zero(self):
        """Test price just barely above zero (smallest positive float)."""
        r = client.post("/items", json={"name": "test", "price": 1e-10})
        assert r.status_code == 200
        assert r.json()["price"] > 0
