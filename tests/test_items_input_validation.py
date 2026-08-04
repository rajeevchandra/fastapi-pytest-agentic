"""Comprehensive input validation tests for item creation."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price field validation with boundary values."""
    
    @pytest.mark.parametrize("price,should_pass", [
        (0.01, True),           # Minimum valid price
        (1.0, True),            # Standard price
        (100.0, True),          # Large price
        (0.001, True),          # Very small but valid
        (999999.99, True),      # Very large price
        (0, False),             # Boundary: zero
        (-1, False),            # Negative price
        (-0.01, False),         # Small negative
        (-999, False),          # Large negative
    ])
    def test_price_boundaries(self, price, should_pass):
        """Test various price boundary conditions."""
        response = client.post("/items", json={"name": "test", "price": price})
        if should_pass:
            assert response.status_code == 200, f"Expected 200 for price {price}"
            assert response.json()["price"] == price
        else:
            assert response.status_code == 400, f"Expected 400 for price {price}"
            assert "price must be > 0" in response.json()["detail"]


class TestCreateItemNameValidation:
    """Test name field validation with various formats."""
    
    @pytest.mark.parametrize("name,should_pass", [
        ("book", True),                         # Simple name
        ("Book Title With Spaces", True),       # Name with spaces
        ("123", True),                          # Numeric string
        ("book-with-dashes", True),             # Name with dashes
        ("book_with_underscores", True),        # Name with underscores
        ("книга", True),                        # Unicode characters
        ("a", True),                            # Single character
        ("x" * 100, True),                      # Long name
        ("name@with#special$chars", True),      # Special characters
        ("name with  double  spaces", True),    # Multiple spaces
    ])
    def test_name_formats(self, name, should_pass):
        """Test various name formats and edge cases."""
        response = client.post("/items", json={"name": name, "price": 10.0})
        if should_pass:
            assert response.status_code == 200, f"Expected success for name '{name}'"
            assert response.json()["name"] == name
        else:
            assert response.status_code == 400


class TestCreateItemMissingFields:
    """Test validation of required fields."""
    
    def test_missing_name_field(self):
        """Test request without name field."""
        response = client.post("/items", json={"price": 10.0})
        assert response.status_code == 422  # Validation error


    def test_missing_price_field(self):
        """Test request without price field."""
        response = client.post("/items", json={"name": "book"})
        assert response.status_code == 422  # Validation error


    def test_empty_request_body(self):
        """Test with empty JSON object."""
        response = client.post("/items", json={})
        assert response.status_code == 422  # Validation error


class TestCreateItemPriceType:
    """Test price field type validation."""
    
    @pytest.mark.parametrize("price_value,should_pass", [
        (10, True),                 # Integer (valid)
        (10.5, True),               # Float (valid)
        ("10.5", False),            # String representation
        (True, False),              # Boolean
        (None, False),              # Null value
        ([], False),                # Empty list
        ({}, False),                # Empty dict
    ])
    def test_price_type_validation(self, price_value, should_pass):
        """Test price field type validation."""
        response = client.post("/items", json={"name": "test", "price": price_value})
        if should_pass:
            assert response.status_code == 200
        else:
            assert response.status_code in (400, 422)  # Either validation or value error


class TestCreateItemNameType:
    """Test name field type validation."""
    
    @pytest.mark.parametrize("name_value,should_pass", [
        ("book", True),             # String (valid)
        (123, False),               # Integer
        (10.5, False),              # Float
        (True, False),              # Boolean
        (None, False),              # Null value
        ([], False),                # List
        ({}, False),                # Dict
    ])
    def test_name_type_validation(self, name_value, should_pass):
        """Test name field type validation."""
        response = client.post("/items", json={"name": name_value, "price": 10.0})
        if should_pass:
            assert response.status_code == 200
        else:
            assert response.status_code in (400, 422)  # Either validation or type error
