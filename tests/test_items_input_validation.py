"""
Input validation tests for the /items endpoint.
Tests price boundary conditions, name variations, and missing fields.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Parametrized tests for price input validation."""
    
    @pytest.mark.parametrize("price,expected_status", [
        (0, 400),           # Zero is invalid
        (-1, 400),          # Negative prices invalid
        (-100.50, 400),     # Negative float invalid
        (0.001, 200),       # Very small positive is valid
        (0.01, 200),        # Small price is valid
        (1.0, 200),         # Normal price is valid
        (999.99, 200),      # Large price is valid
        (10000.00, 200),    # Very large price is valid
        (999999.99, 200),   # Extremely large price is valid
    ])
    def test_create_item_price_boundary(self, price, expected_status):
        """Test price validation with boundary values."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == expected_status
        if expected_status == 400:
            assert "price must be > 0" in r.json()["detail"]


class TestCreateItemNameValidation:
    """Parametrized tests for name input validation."""
    
    @pytest.mark.parametrize("name", [
        "a",                    # Single character
        "Book",                 # Simple name
        "Test Item",            # Name with space
        "Item-with-dash",       # Name with dash
        "Item_with_underscore", # Name with underscore
        "123",                  # Numeric string
        "Item with spaces",     # Multiple spaces
        "Üñíçödé",             # Unicode characters
        "!@#$%^&*()",          # Special characters
    ])
    def test_create_item_valid_names(self, name):
        """Test that various name formats are accepted."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name


class TestCreateItemMissingFields:
    """Tests for missing required fields."""
    
    def test_create_item_missing_price(self):
        """Test POST /items without price field."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422  # Validation error
    
    def test_create_item_missing_name(self):
        """Test POST /items without name field."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422  # Validation error
    
    def test_create_item_missing_both_fields(self):
        """Test POST /items with empty body."""
        r = client.post("/items", json={})
        assert r.status_code == 422  # Validation error


class TestCreateItemTypeValidation:
    """Tests for invalid data types."""
    
    def test_create_item_price_as_string(self):
        """Test POST /items with price as string instead of number."""
        r = client.post("/items", json={"name": "test", "price": "10.0"})
        # Pydantic should coerce string to float if possible
        assert r.status_code == 200
    
    def test_create_item_price_as_null(self):
        """Test POST /items with null price."""
        r = client.post("/items", json={"name": "test", "price": None})
        assert r.status_code == 422  # Validation error
    
    def test_create_item_name_as_number(self):
        """Test POST /items with name as number instead of string."""
        r = client.post("/items", json={"name": 123, "price": 10.0})
        # Pydantic should coerce number to string
        assert r.status_code == 200
    
    def test_create_item_name_as_null(self):
        """Test POST /items with null name."""
        r = client.post("/items", json={"name": None, "price": 10.0})
        assert r.status_code == 422  # Validation error


class TestCreateItemResponseStructure:
    """Tests for response structure and data consistency."""
    
    def test_create_item_response_has_required_fields(self):
        """Test that response includes id, name, and price."""
        r = client.post("/items", json={"name": "test book", "price": 25.5})
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data
        assert data["id"] == 1
        assert data["name"] == "test book"
        assert data["price"] == 25.5
    
    def test_create_item_response_types(self):
        """Test response field types are correct."""
        r = client.post("/items", json={"name": "book", "price": 10.5})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))
