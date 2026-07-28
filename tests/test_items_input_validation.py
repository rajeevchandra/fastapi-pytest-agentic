from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price validation with boundary values."""
    
    @pytest.mark.parametrize("price,should_pass", [
        (0.01, True),      # minimum valid price
        (0.1, True),
        (1.0, True),
        (100.0, True),
        (999999.99, True), # very large price
        (-0.01, False),    # negative
        (-1.0, False),
        (-100.0, False),
        (-999999.99, False),
        (0, False),        # zero not allowed
    ])
    def test_price_boundary_values(self, price, should_pass):
        """Test create item with various price boundary values."""
        response = client.post("/items", json={"name": "test", "price": price})
        if should_pass:
            assert response.status_code == 200
            assert response.json()["price"] == price
        else:
            assert response.status_code == 400
            assert "price must be > 0" in response.json()["detail"]


class TestCreateItemNameValidation:
    """Test name field validation with various formats."""
    
    @pytest.mark.parametrize("name", [
        "a",                           # single char
        "Book",                        # uppercase
        "my_book",                     # underscores
        "my-book",                     # dashes
        "book with spaces",            # spaces
        "book!@#$%",                   # special chars
        "A" * 100,                     # very long name
        "Café",                        # unicode
        "123",                         # numbers as name
    ])
    def test_name_variations(self, name):
        """Test create item with various name formats."""
        response = client.post("/items", json={"name": name, "price": 10.0})
        assert response.status_code == 200
        assert response.json()["name"] == name


class TestCreateItemMissingFields:
    """Test validation of required fields."""
    
    def test_missing_name(self):
        """Test create item without name field."""
        response = client.post("/items", json={"price": 10.0})
        assert response.status_code == 422  # Validation error
    
    def test_missing_price(self):
        """Test create item without price field."""
        response = client.post("/items", json={"name": "test"})
        assert response.status_code == 422  # Validation error
    
    def test_empty_payload(self):
        """Test create item with empty payload."""
        response = client.post("/items", json={})
        assert response.status_code == 422  # Validation error
    
    def test_null_name(self):
        """Test create item with null name."""
        response = client.post("/items", json={"name": None, "price": 10.0})
        assert response.status_code == 422  # Validation error
    
    def test_null_price(self):
        """Test create item with null price."""
        response = client.post("/items", json={"name": "test", "price": None})
        assert response.status_code == 422  # Validation error


class TestCreateItemTypeValidation:
    """Test type validation and coercion."""
    
    def test_string_price_coercion(self):
        """Test create item with string price that can be coerced to float."""
        response = client.post("/items", json={"name": "test", "price": "10.5"})
        assert response.status_code == 200
        assert response.json()["price"] == 10.5
    
    def test_integer_price_coercion(self):
        """Test create item with integer price."""
        response = client.post("/items", json={"name": "test", "price": 10})
        assert response.status_code == 200
        assert response.json()["price"] == 10.0
    
    def test_non_numeric_string_price(self):
        """Test create item with non-numeric string price."""
        response = client.post("/items", json={"name": "test", "price": "abc"})
        assert response.status_code == 422  # Validation error
    
    def test_extra_fields(self):
        """Test create item with extra fields (should be ignored)."""
        response = client.post("/items", json={
            "name": "test",
            "price": 10.0,
            "extra_field": "value",
            "another": 123
        })
        assert response.status_code == 200
        assert response.json()["name"] == "test"
        assert response.json()["price"] == 10.0
    
    def test_price_as_string_non_numeric(self):
        """Test price validation with completely invalid string."""
        response = client.post("/items", json={"name": "test", "price": "not_a_number"})
        assert response.status_code == 422


class TestCreateItemEdgeCases:
    """Test edge case scenarios."""
    
    def test_very_small_price(self):
        """Test create item with very small valid price."""
        response = client.post("/items", json={"name": "test", "price": 0.001})
        assert response.status_code == 200
        assert response.json()["price"] == 0.001
    
    def test_very_large_price(self):
        """Test create item with very large price."""
        response = client.post("/items", json={"name": "test", "price": 9999999.99})
        assert response.status_code == 200
        assert response.json()["price"] == 9999999.99
    
    def test_emoji_in_name(self):
        """Test create item with emoji in name."""
        response = client.post("/items", json={"name": "Book 📚", "price": 10.0})
        assert response.status_code == 200
        assert "📚" in response.json()["name"]
    
    def test_multiple_sequential_creates(self):
        """Test creating multiple items sequentially."""
        for i in range(5):
            response = client.post("/items", json={"name": f"item_{i}", "price": 10.0 * (i + 1)})
            assert response.status_code == 200
            assert response.json()["name"] == f"item_{i}"
    
    def test_name_with_newlines(self):
        """Test create item with name containing newlines."""
        name_with_newline = "line1\nline2"
        response = client.post("/items", json={"name": name_with_newline, "price": 10.0})
        assert response.status_code == 200
        assert response.json()["name"] == name_with_newline
