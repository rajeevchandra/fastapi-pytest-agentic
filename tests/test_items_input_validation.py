"""
Input Validation & Boundary Testing for POST /items endpoint.

Tests comprehensive price and name validation, missing fields,
type validation, and edge cases to improve test quality and confidence.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price field validation and boundary conditions."""

    @pytest.mark.parametrize("price,should_fail", [
        (0, True),           # Zero price must be rejected
        (-1, True),          # Negative price must be rejected
        (-100.50, True),     # Large negative price must be rejected
        (0.001, False),      # Very small positive price should work
        (0.01, False),       # Small positive price should work
        (1, False),          # Small integer price should work
        (10.5, False),       # Regular decimal price should work
        (100, False),        # Larger price should work
        (999999.99, False),  # Very large price should work
    ])
    def test_create_item_price_validation(self, price, should_fail):
        """Test various price values to verify validation logic."""
        response = client.post("/items", json={"name": "test", "price": price})
        if should_fail:
            assert response.status_code == 400, f"Price {price} should be rejected"
            assert "price must be > 0" in response.json()["detail"]
        else:
            assert response.status_code == 200, f"Price {price} should be accepted"
            data = response.json()
            assert data["price"] == price


class TestCreateItemNameValidation:
    """Test name field validation and edge cases."""

    @pytest.mark.parametrize("name", [
        "A",                                    # Single character
        "ab",                                   # Two characters
        "test item",                            # Space in name
        "item-name",                            # Hyphen in name
        "item_name",                            # Underscore in name
        "item.name",                            # Dot in name
        "Item123",                              # Mixed case with numbers
        "café",                                 # Unicode characters
        "™©®",                                  # Special unicode symbols
        "a" * 100,                              # Very long name
        "a" * 500,                              # Extremely long name
    ])
    def test_create_item_name_accepts_valid_names(self, name):
        """Test that various valid names are accepted."""
        response = client.post("/items", json={"name": name, "price": 10.5})
        assert response.status_code == 200, f"Name '{name}' should be accepted"
        data = response.json()
        assert data["name"] == name


class TestCreateItemMissingFields:
    """Test validation when required fields are missing."""

    def test_create_item_missing_name(self):
        """Test that missing name field returns validation error."""
        response = client.post("/items", json={"price": 10.5})
        assert response.status_code == 422, "Missing name should return 422"
        assert "validation error" in response.json()["detail"][0]["type"].lower()

    def test_create_item_missing_price(self):
        """Test that missing price field returns validation error."""
        response = client.post("/items", json={"name": "test"})
        assert response.status_code == 422, "Missing price should return 422"
        assert "validation error" in response.json()["detail"][0]["type"].lower()

    def test_create_item_missing_both_fields(self):
        """Test that missing both fields returns validation errors."""
        response = client.post("/items", json={})
        assert response.status_code == 422, "Missing both fields should return 422"
        errors = response.json()["detail"]
        assert len(errors) >= 2, "Should have multiple validation errors"


class TestCreateItemInvalidTypes:
    """Test type validation for required fields."""

    def test_create_item_price_as_string_valid_number(self):
        """Test that price as numeric string is auto-coerced to float."""
        response = client.post("/items", json={"name": "test", "price": "10.5"})
        assert response.status_code == 200, "Numeric string price should be coerced"
        assert response.json()["price"] == 10.5

    def test_create_item_price_as_string_invalid(self):
        """Test that price as non-numeric string fails validation."""
        response = client.post("/items", json={"name": "test", "price": "invalid"})
        assert response.status_code == 422, "Non-numeric price string should fail"

    def test_create_item_price_as_null(self):
        """Test that null price fails validation."""
        response = client.post("/items", json={"name": "test", "price": None})
        assert response.status_code == 422, "Null price should fail validation"

    def test_create_item_name_as_number(self):
        """Test that numeric name is accepted and coerced to string."""
        response = client.post("/items", json={"name": 123, "price": 10.5})
        assert response.status_code == 200, "Numeric name should be coerced to string"

    def test_create_item_name_as_null(self):
        """Test that null name fails validation."""
        response = client.post("/items", json={"name": None, "price": 10.5})
        assert response.status_code == 422, "Null name should fail validation"

    def test_create_item_price_as_bool(self):
        """Test that boolean price is accepted (Python bool is subclass of int)."""
        response = client.post("/items", json={"name": "test", "price": True})
        assert response.status_code == 200, "Boolean price True should be accepted (=1)"
        assert response.json()["price"] == 1

    def test_create_item_price_as_bool_false(self):
        """Test that boolean False price is rejected (False=0)."""
        response = client.post("/items", json={"name": "test", "price": False})
        assert response.status_code == 400, "Boolean False price should be rejected (=0)"


class TestCreateItemResponseStructure:
    """Test response structure and field validation."""

    def test_create_item_response_has_required_fields(self):
        """Test that response contains all required fields."""
        response = client.post("/items", json={"name": "book", "price": 12.5})
        assert response.status_code == 200
        data = response.json()
        assert "id" in data, "Response should have 'id' field"
        assert "name" in data, "Response should have 'name' field"
        assert "price" in data, "Response should have 'price' field"

    def test_create_item_response_id_is_integer(self):
        """Test that response id is an integer."""
        response = client.post("/items", json={"name": "test", "price": 10.0})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["id"], int), "ID should be integer"
        assert data["id"] == 1

    def test_create_item_response_name_matches_input(self):
        """Test that response name matches input name."""
        test_name = "unique-test-item"
        response = client.post("/items", json={"name": test_name, "price": 25.0})
        assert response.status_code == 200
        assert response.json()["name"] == test_name

    def test_create_item_response_price_matches_input(self):
        """Test that response price matches input price."""
        test_price = 33.33
        response = client.post("/items", json={"name": "test", "price": test_price})
        assert response.status_code == 200
        assert response.json()["price"] == test_price

    def test_create_item_response_has_no_extra_fields(self):
        """Test that response only contains expected fields."""
        response = client.post("/items", json={"name": "test", "price": 10.0})
        assert response.status_code == 200
        data = response.json()
        expected_fields = {"id", "name", "price"}
        actual_fields = set(data.keys())
        assert actual_fields == expected_fields, f"Unexpected fields in response"


class TestCreateItemErrorHandling:
    """Test error handling and edge cases."""

    def test_create_item_with_extra_fields(self):
        """Test that extra fields in request don't cause errors."""
        response = client.post("/items", json={
            "name": "test",
            "price": 10.5,
            "extra_field": "ignored"
        })
        assert response.status_code == 200, "Extra fields should be ignored"

    def test_create_item_negative_zero(self):
        """Test that negative zero is treated as zero and rejected."""
        response = client.post("/items", json={"name": "test", "price": -0.0})
        assert response.status_code == 400, "Negative zero should be rejected"

    def test_create_item_very_large_price(self):
        """Test that very large prices are accepted."""
        response = client.post("/items", json={"name": "expensive", "price": 1e10})
        assert response.status_code == 200, "Very large price should be accepted"
        assert response.json()["price"] == 1e10

    def test_create_item_very_small_price(self):
        """Test that very small positive prices are accepted."""
        response = client.post("/items", json={"name": "cheap", "price": 1e-10})
        assert response.status_code == 200, "Very small positive price should be accepted"
        assert response.json()["price"] == 1e-10
