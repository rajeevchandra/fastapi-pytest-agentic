"""
Edge Cases and Integration Tests for /items endpoints.
Tests path parameter validation, boundary conditions, sequential operations, and integration scenarios.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test path parameter validation for get_item endpoint."""

    @pytest.mark.parametrize("item_id,expected_status", [
        (1, 200),           # Valid
        (2, 404),           # Not found
        (0, 404),           # Zero
        (-1, 404),          # Negative
        (-100, 404),        # Large negative
        (999, 404),         # Large positive
        (2147483647, 404),  # Max 32-bit int
    ])
    def test_get_item_path_parameter_validation(self, item_id, expected_status):
        """Test various path parameter values."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == expected_status


class TestPriceEdgeCases:
    """Test extreme price values and edge cases."""

    @pytest.mark.parametrize("price,should_succeed", [
        (0.0001, True),           # Very small positive
        (0.001, True),            # Minimal reasonable price
        (0.01, True),             # Smallest common price
        (0.1, True),              # Tenth
        (1, True),                # One unit
        (99.99, True),            # Common price
        (999.99, True),           # Larger price
        (9999.99, True),          # Large price
        (99999.99, True),         # Very large price
        (1000000, True),          # Million
        (1e6, True),              # Scientific notation
        (1e10, True),             # Very large
        (0, False),               # Zero rejected
        (-0, False),              # Negative zero
        (-0.0001, False),         # Small negative
        (-0.01, False),           # Negative cent
        (-1, False),              # Negative one
        (-999, False),            # Large negative
    ])
    def test_price_boundary_conditions(self, price, should_succeed):
        """Test extreme price boundary values."""
        response = client.post("/items", json={"name": "test", "price": price})
        if should_succeed:
            assert response.status_code == 200, f"Price {price} should succeed"
        else:
            assert response.status_code == 400, f"Price {price} should fail"


class TestNameEdgeCases:
    """Test extreme name values and edge cases."""

    @pytest.mark.parametrize("name", [
        "A",                    # Single character
        "AB",                   # Two characters
        "a",                    # Lowercase single
        "1",                    # Number
        "名前",                  # Japanese (if supported)
        "Ñoño",                 # Accented characters
        "Test Item #1",         # With spaces and punctuation
        "item-with-dashes",     # Dashes
        "item_with_underscores",# Underscores
        "UPPERCASE",            # All caps
        "lowercase",            # All lower
        "MixedCase",            # Mixed case
        "item.with.dots",       # Dots
        "item/with/slashes",    # Slashes
        "item@domain",          # @ symbol
        "item$value",           # Dollar sign
        "item%percent",         # Percent
        "item&and",             # Ampersand
        "item*asterisk",        # Asterisk
        "item(parens)",         # Parentheses
        "item[brackets]",       # Brackets
        "item{braces}",         # Braces
        "item'quote'",          # Single quotes
        'item"double"',         # Double quotes
        "item`backtick`",       # Backticks
        "item\\backslash",      # Backslash
        "  spaces  ",           # Leading/trailing spaces
        "multiple   spaces",    # Multiple spaces
        "tab\there",            # Tab character
        "newline\nhere",        # Newline (if allowed)
        "very " * 50 + "long",  # Very long name
    ])
    def test_name_variations(self, name):
        """Test various name formats."""
        response = client.post("/items", json={"name": name, "price": 10.0})
        # Most should succeed, some may fail validation
        assert response.status_code in [200, 422]

    def test_empty_string_name(self):
        """Test that empty string name is rejected."""
        response = client.post("/items", json={"name": "", "price": 10.0})
        assert response.status_code == 422

    def test_whitespace_only_name(self):
        """Test whitespace-only name handling."""
        response = client.post("/items", json={"name": "   ", "price": 10.0})
        # May be accepted or rejected depending on validation
        assert response.status_code in [200, 422]


class TestNumericPrecision:
    """Test numeric precision handling."""

    @pytest.mark.parametrize("price", [
        1.1,
        1.11,
        1.111,
        1.1111,
        1.11111,
        1.111111,
        3.14159,
        2.71828,
        0.99999,
        0.33333,
    ])
    def test_decimal_precision(self, price):
        """Test various decimal precisions."""
        response = client.post("/items", json={"name": "test", "price": price})
        assert response.status_code == 200
        returned_price = response.json()["price"]
        # Allow for small floating point errors
        assert abs(returned_price - price) < 1e-5

    def test_integer_price_converted_to_float(self):
        """Test that integer price is converted to float."""
        response = client.post("/items", json={"name": "test", "price": 10})
        data = response.json()
        assert isinstance(data["price"], float)
        assert data["price"] == 10.0

    def test_string_price_conversion(self):
        """Test string price conversion."""
        response = client.post("/items", json={"name": "test", "price": "15.5"})
        assert response.status_code == 200
        assert response.json()["price"] == 15.5

    def test_string_integer_price_conversion(self):
        """Test string integer price conversion."""
        response = client.post("/items", json={"name": "test", "price": "20"})
        assert response.status_code == 200
        assert response.json()["price"] == 20.0


class TestSequentialOperations:
    """Test sequential create and get operations."""

    def test_create_then_get_same_item(self):
        """Test creating an item and then retrieving it."""
        create_resp = client.post("/items", json={"name": "sequential_test", "price": 25.0})
        assert create_resp.status_code == 200
        
        get_resp = client.get("/items/1")
        assert get_resp.status_code == 200
        
        # Values should be consistent
        assert get_resp.json()["id"] == 1

    def test_multiple_create_operations(self):
        """Test multiple sequential create operations."""
        for i in range(5):
            response = client.post("/items", json={"name": f"item_{i}", "price": float(i + 1)})
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1  # API always returns id=1
            assert data["name"] == f"item_{i}"
            assert data["price"] == float(i + 1)

    def test_create_different_items_then_get(self):
        """Test creating different items and getting the same one."""
        items_to_create = [
            {"name": "book", "price": 15.99},
            {"name": "pen", "price": 1.50},
            {"name": "notebook", "price": 5.00},
        ]
        
        for item_data in items_to_create:
            response = client.post("/items", json=item_data)
            assert response.status_code == 200
        
        # Get should return the fixed item
        get_resp = client.get("/items/1")
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == 1


class TestValidationErrorDetailed:
    """Test detailed validation error scenarios."""

    def test_type_coercion_string_to_float(self):
        """Test type coercion from string to float."""
        response = client.post("/items", json={"name": "test", "price": "99.99"})
        assert response.status_code == 200
        assert response.json()["price"] == 99.99

    def test_type_coercion_int_to_float(self):
        """Test type coercion from int to float."""
        response = client.post("/items", json={"name": "test", "price": 50})
        assert response.status_code == 200
        assert isinstance(response.json()["price"], float)

    def test_invalid_number_string(self):
        """Test invalid number string fails validation."""
        response = client.post("/items", json={"name": "test", "price": "not_a_number"})
        assert response.status_code == 422

    def test_boolean_price_fails(self):
        """Test that boolean price fails validation."""
        response = client.post("/items", json={"name": "test", "price": True})
        # Should either coerce to 1.0 or fail - implementation dependent
        # Most strict validators would fail this
        assert response.status_code in [200, 422]

    def test_null_name_fails(self):
        """Test that null name fails validation."""
        response = client.post("/items", json={"name": None, "price": 10.0})
        assert response.status_code == 422

    def test_array_name_fails(self):
        """Test that array name fails validation."""
        response = client.post("/items", json={"name": ["item"], "price": 10.0})
        assert response.status_code == 422

    def test_object_price_fails(self):
        """Test that object price fails validation."""
        response = client.post("/items", json={"name": "test", "price": {"value": 10}})
        assert response.status_code == 422


class TestGetItemEdgeCases:
    """Test edge cases for get_item endpoint."""

    def test_get_item_with_valid_id_returns_fixed_item(self):
        """Test that get_item/1 always returns the same fixed item."""
        response = client.get("/items/1")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0

    def test_get_multiple_different_ids_same_result(self):
        """Test getting different IDs when only 1 exists."""
        valid_response = client.get("/items/1")
        invalid_responses = [
            client.get("/items/0"),
            client.get("/items/2"),
            client.get("/items/3"),
            client.get("/items/999"),
        ]
        
        assert valid_response.status_code == 200
        for resp in invalid_responses:
            assert resp.status_code == 404

    def test_get_item_response_consistency(self):
        """Test that repeated gets return consistent results."""
        responses = [client.get("/items/1") for _ in range(3)]
        
        jsons = [r.json() for r in responses]
        assert all(j == jsons[0] for j in jsons)


class TestRequestDataTypes:
    """Test different request data types."""

    def test_json_payload_float_price(self):
        """Test JSON payload with float price."""
        response = client.post("/items", json={"name": "test", "price": 10.5})
        assert response.status_code == 200

    def test_json_payload_int_price(self):
        """Test JSON payload with integer price."""
        response = client.post("/items", json={"name": "test", "price": 10})
        assert response.status_code == 200

    def test_json_payload_string_price(self):
        """Test JSON payload with string price (type coercion)."""
        response = client.post("/items", json={"name": "test", "price": "10"})
        assert response.status_code == 200

    def test_json_payload_scientific_notation(self):
        """Test JSON payload with scientific notation."""
        response = client.post("/items", json={"name": "test", "price": 1e2})
        assert response.status_code == 200
        assert response.json()["price"] == 100.0


class TestResponseDataTypes:
    """Test response data types are correct."""

    def test_response_all_fields_present_create(self):
        """Test that all expected fields are in create response."""
        response = client.post("/items", json={"name": "test", "price": 10.0})
        data = response.json()
        assert set(data.keys()) == {"id", "name", "price"}

    def test_response_all_fields_present_get(self):
        """Test that all expected fields are in get response."""
        response = client.get("/items/1")
        data = response.json()
        assert set(data.keys()) == {"id", "name", "price"}

    def test_response_field_types(self):
        """Test response field types."""
        response = client.post("/items", json={"name": "test", "price": 10.5})
        data = response.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], float)

    def test_response_price_never_integer(self):
        """Test that price is always float, not int."""
        response = client.post("/items", json={"name": "test", "price": 10})
        data = response.json()
        assert isinstance(data["price"], float)
        assert data["price"] == 10.0


class TestBoundaryBetweenSuccessAndFailure:
    """Test exact boundary between success and failure."""

    def test_smallest_valid_price(self):
        """Test the smallest valid price."""
        # Test very small positive values
        response = client.post("/items", json={"name": "test", "price": 0.00001})
        assert response.status_code == 200

    def test_largest_invalid_price_before_success(self):
        """Test largest invalid price."""
        response = client.post("/items", json={"name": "test", "price": 0})
        assert response.status_code == 400

    def test_boundary_between_zero_and_positive(self):
        """Test the exact boundary between zero and positive."""
        # 0 should fail
        response_zero = client.post("/items", json={"name": "test", "price": 0})
        assert response_zero.status_code == 400
        
        # Any positive should succeed
        response_positive = client.post("/items", json={"name": "test", "price": 0.000001})
        assert response_positive.status_code == 200


class TestErrorRecovery:
    """Test behavior after errors."""

    def test_create_after_validation_error(self):
        """Test that valid create works after validation error."""
        # First, trigger validation error
        error_resp = client.post("/items", json={"name": "test", "price": 0})
        assert error_resp.status_code == 400
        
        # Then, valid request should work
        success_resp = client.post("/items", json={"name": "test", "price": 10.0})
        assert success_resp.status_code == 200

    def test_create_after_missing_field_error(self):
        """Test that valid create works after missing field error."""
        # First, missing field error
        error_resp = client.post("/items", json={"price": 10.0})
        assert error_resp.status_code == 422
        
        # Then, valid request should work
        success_resp = client.post("/items", json={"name": "test", "price": 10.0})
        assert success_resp.status_code == 200

    def test_get_after_404(self):
        """Test that valid get works after 404."""
        # First, 404
        not_found = client.get("/items/999")
        assert not_found.status_code == 404
        
        # Then, valid get should work
        found = client.get("/items/1")
        assert found.status_code == 200
