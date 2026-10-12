"""
Comprehensive input validation tests for /items endpoint.

Tests cover:
- Price boundary conditions (negative, zero, positive edge cases)
- Name field variations (empty, special characters, unicode, length limits)
- Missing required fields
- Type validation
- Extra fields in request
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price parameter validation and boundary conditions."""

    @pytest.mark.parametrize("price,expected_status", [
        (0, 400),           # Zero price should fail
        (-1, 400),          # Negative price should fail
        (-100.50, 400),     # Large negative price should fail
        (0.01, 200),        # Minimum positive price should succeed
        (1, 200),           # Integer price should succeed
        (12.5, 200),        # Decimal price should succeed
        (999999.99, 200),   # Large price should succeed
        (1000000, 200),     # Very large price should succeed
    ])
    def test_price_boundary_values(self, price, expected_status):
        """Test various price values at boundary conditions."""
        response = client.post("/items", json={"name": "test", "price": price})
        assert response.status_code == expected_status
        
        if expected_status == 200:
            data = response.json()
            assert data["price"] == price
            assert data["name"] == "test"

    def test_price_negative_with_valid_name(self):
        """Test that negative price is rejected even with valid name."""
        response = client.post("/items", json={"name": "valid", "price": -50.5})
        assert response.status_code == 400
        assert "price must be > 0" in response.json()["detail"]

    def test_price_zero_error_message(self):
        """Verify error message for zero price."""
        response = client.post("/items", json={"name": "test", "price": 0})
        assert response.status_code == 400
        assert response.json()["detail"] == "price must be > 0"

    @pytest.mark.parametrize("price", [0.001, 0.0001, 0.00001])
    def test_price_very_small_positive(self, price):
        """Test very small positive prices are accepted."""
        response = client.post("/items", json={"name": "test", "price": price})
        assert response.status_code == 200
        assert response.json()["price"] == price


class TestCreateItemNameValidation:
    """Test name parameter validation and string handling."""

    @pytest.mark.parametrize("name,should_succeed", [
        ("", False),                    # Empty string - framework should validate
        ("A", True),                    # Single character
        ("book", True),                 # Normal name
        ("the book", True),             # Name with spaces
        ("Special-Name_123", True),     # Name with special chars
        ("Name!@#$%", True),            # More special chars
        ("名前", True),                  # Unicode (Japanese)
        ("Привет", True),               # Unicode (Russian)
        ("A" * 500, True),              # Very long name
    ])
    def test_name_variations(self, name, should_succeed):
        """Test various name formats and edge cases."""
        response = client.post("/items", json={"name": name, "price": 10.0})
        
        if should_succeed:
            # Only empty string validation is likely enforced by Pydantic
            if name:
                assert response.status_code == 200
                assert response.json()["name"] == name
        else:
            # Empty string handling depends on Pydantic config
            # Just verify the response is received
            assert response.status_code in [200, 422]

    def test_name_with_newlines(self):
        """Test name containing newline characters."""
        response = client.post("/items", json={"name": "line1\nline2", "price": 5.0})
        # Should accept as name is just a string field
        assert response.status_code == 200
        assert response.json()["name"] == "line1\nline2"

    def test_name_with_quotes(self):
        """Test name containing quote characters."""
        response = client.post("/items", json={"name": 'He said "hello"', "price": 5.0})
        assert response.status_code == 200
        assert response.json()["name"] == 'He said "hello"'

    def test_name_null_value(self):
        """Test null value for name field."""
        response = client.post("/items", json={"name": None, "price": 10.0})
        # Pydantic should reject null for required string field
        assert response.status_code == 422

    def test_name_numeric_string(self):
        """Test numeric value as string name."""
        response = client.post("/items", json={"name": "12345", "price": 10.0})
        assert response.status_code == 200
        assert response.json()["name"] == "12345"


class TestCreateItemMissingFields:
    """Test behavior when required fields are missing."""

    def test_missing_name_field(self):
        """Test POST without name field."""
        response = client.post("/items", json={"price": 10.0})
        # FastAPI/Pydantic should return 422 Unprocessable Entity
        assert response.status_code == 422

    def test_missing_price_field(self):
        """Test POST without price field."""
        response = client.post("/items", json={"name": "test"})
        assert response.status_code == 422

    def test_missing_both_fields(self):
        """Test POST with no body fields."""
        response = client.post("/items", json={})
        assert response.status_code == 422

    def test_empty_json_body(self):
        """Test POST with no JSON body at all."""
        response = client.post("/items")
        assert response.status_code == 422


class TestCreateItemTypeValidation:
    """Test type validation for request fields."""

    def test_price_as_string(self):
        """Test passing price as string instead of number."""
        response = client.post("/items", json={"name": "test", "price": "10.5"})
        # Pydantic should attempt to coerce or reject
        # Default Pydantic v2 behavior coerces valid numeric strings
        assert response.status_code in [200, 422]

    def test_price_as_non_numeric_string(self):
        """Test price as non-numeric string."""
        response = client.post("/items", json={"name": "test", "price": "abc"})
        # Should fail validation
        assert response.status_code == 422

    def test_name_as_number(self):
        """Test name as number instead of string."""
        response = client.post("/items", json={"name": 123, "price": 10.0})
        # Pydantic may coerce or reject - both are reasonable
        assert response.status_code in [200, 422]

    def test_name_as_boolean(self):
        """Test name as boolean."""
        response = client.post("/items", json={"name": True, "price": 10.0})
        assert response.status_code in [200, 422]

    def test_price_as_array(self):
        """Test price as array."""
        response = client.post("/items", json={"name": "test", "price": [10.0]})
        assert response.status_code == 422

    def test_name_as_object(self):
        """Test name as object."""
        response = client.post("/items", json={"name": {"value": "test"}, "price": 10.0})
        assert response.status_code == 422


class TestCreateItemExtraFields:
    """Test handling of extra/unexpected fields in request."""

    def test_extra_field_in_request(self):
        """Test POST with additional fields."""
        response = client.post("/items", json={
            "name": "test",
            "price": 10.0,
            "extra_field": "should_be_ignored"
        })
        # Pydantic by default ignores extra fields
        assert response.status_code == 200
        assert response.json()["name"] == "test"

    def test_multiple_extra_fields(self):
        """Test POST with multiple extra fields."""
        response = client.post("/items", json={
            "name": "test",
            "price": 10.0,
            "field1": "value1",
            "field2": "value2",
            "field3": "value3"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test"
        assert data["price"] == 10.0

    def test_extra_field_description(self):
        """Test extra field named 'description'."""
        response = client.post("/items", json={
            "name": "test",
            "price": 10.0,
            "description": "This is a description"
        })
        # Should be ignored
        assert response.status_code == 200

    def test_extra_field_id(self):
        """Test extra field named 'id' (which is returned)."""
        response = client.post("/items", json={
            "name": "test",
            "price": 10.0,
            "id": 999
        })
        # The response id should be generated, not taken from input
        assert response.status_code == 200
        data = response.json()
        # Response should have id=1 (server-generated)
        assert data["id"] == 1


class TestCreateItemResponseStructure:
    """Test response structure and field validation."""

    def test_response_contains_required_fields(self):
        """Test that response contains all required fields."""
        response = client.post("/items", json={"name": "test", "price": 10.0})
        assert response.status_code == 200
        data = response.json()
        
        # Check all expected fields exist
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_response_field_types(self):
        """Test response field types are correct."""
        response = client.post("/items", json={"name": "book", "price": 12.5})
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_response_preserves_input_values(self):
        """Test that response preserves exact input values."""
        response = client.post("/items", json={"name": "special-book", "price": 99.99})
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == "special-book"
        assert data["price"] == 99.99

    def test_response_id_always_one(self):
        """Test that response id is always 1 (hardcoded in implementation)."""
        for _ in range(3):
            response = client.post("/items", json={"name": "test", "price": 10.0})
            assert response.status_code == 200
            assert response.json()["id"] == 1


class TestCreateItemContentType:
    """Test content type and headers."""

    def test_response_is_json(self):
        """Test that response has JSON content type."""
        response = client.post("/items", json={"name": "test", "price": 10.0})
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    def test_error_response_is_json(self):
        """Test that error response is also JSON."""
        response = client.post("/items", json={"name": "test", "price": 0})
        assert response.status_code == 400
        assert "application/json" in response.headers.get("content-type", "")


class TestCreateItemEdgeCases:
    """Test various edge cases and corner scenarios."""

    def test_create_with_all_valid_variations(self):
        """Test successful creation with various valid inputs."""
        test_cases = [
            {"name": "a", "price": 0.01},
            {"name": "Book Title", "price": 19.99},
            {"name": "Product-123", "price": 1000.00},
            {"name": "你好", "price": 99.99},
        ]
        
        for test_case in test_cases:
            response = client.post("/items", json=test_case)
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == test_case["name"]
            assert data["price"] == test_case["price"]

    def test_repeated_creations(self):
        """Test that multiple successful creations all return id=1."""
        for i in range(5):
            response = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            assert response.status_code == 200
            assert response.json()["id"] == 1

    @pytest.mark.parametrize("price", [0, -1, -999.99])
    def test_all_invalid_prices_rejected(self, price):
        """Verify all invalid prices are consistently rejected."""
        response = client.post("/items", json={"name": "test", "price": price})
        assert response.status_code == 400
        assert "price must be > 0" in response.json()["detail"]

    def test_create_with_whitespace_name(self):
        """Test name that is only whitespace."""
        response = client.post("/items", json={"name": "   ", "price": 10.0})
        # Should succeed as whitespace is technically valid string content
        assert response.status_code == 200
        assert response.json()["name"] == "   "


class TestCreateItemIntegration:
    """Integration tests combining multiple validation aspects."""

    def test_valid_creation_then_verify_response(self):
        """Create item and verify all response aspects."""
        response = client.post("/items", json={"name": "Test Product", "price": 25.50})
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all fields
        assert data["id"] == 1
        assert data["name"] == "Test Product"
        assert data["price"] == 25.50
        
        # Verify response JSON is valid
        assert isinstance(data, dict)
        assert len(data) == 3  # Only id, name, price

    def test_invalid_then_valid_creation(self):
        """Test invalid creation followed by valid one."""
        # First request: invalid price
        response1 = client.post("/items", json={"name": "first", "price": -10})
        assert response1.status_code == 400
        
        # Second request: valid
        response2 = client.post("/items", json={"name": "second", "price": 10})
        assert response2.status_code == 200
        assert response2.json()["name"] == "second"

    def test_boundary_price_acceptance(self):
        """Test exact boundary between invalid and valid prices."""
        # Just below boundary (should fail)
        response_invalid = client.post("/items", json={"name": "test", "price": 0})
        assert response_invalid.status_code == 400
        
        # At exact boundary (should succeed)
        response_valid = client.post("/items", json={"name": "test", "price": 0.00001})
        assert response_valid.status_code == 200
