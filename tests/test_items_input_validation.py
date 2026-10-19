"""
Input validation tests for item creation endpoint.
Tests cover price boundary values, name validation, and malformed requests.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemValidPrice:
    """Test valid price inputs for item creation."""

    @pytest.mark.parametrize("price", [
        0.01,          # Minimum valid price
        0.1,
        1.0,
        10.0,
        100.0,
        1000.0,
        10000.0,
        float(1e6),    # Very large price
    ])
    def test_create_item_with_valid_price(self, price):
        """Test that items can be created with valid positive prices."""
        response = client.post(
            "/items",
            json={"name": "test_item", "price": price}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["price"] == price
        assert data["name"] == "test_item"
        assert data["id"] == 1


class TestCreateItemInvalidPrice:
    """Test invalid price inputs for item creation."""

    @pytest.mark.parametrize("price", [
        0,             # Exactly zero
        -0.01,         # Negative
        -1,
        -100,
        -1000,
        float('-inf'), # Negative infinity
    ])
    def test_create_item_rejects_non_positive_price(self, price):
        """Test that items cannot be created with zero or negative prices."""
        response = client.post(
            "/items",
            json={"name": "bad_item", "price": price}
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "price must be > 0"


class TestCreateItemValidName:
    """Test valid name inputs for item creation."""

    @pytest.mark.parametrize("name", [
        "apple",
        "book",
        "Product One",
        "item-123",
        "item_456",
        "UPPERCASE",
        "CamelCase",
        "123numbers",
        "name with spaces",
        "unicode_名前",
        "emoji_📚",
        "special!@#$%",
    ])
    def test_create_item_with_valid_name(self, name):
        """Test that items can be created with various name formats."""
        response = client.post(
            "/items",
            json={"name": name, "price": 10.0}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == name
        assert data["price"] == 10.0


class TestCreateItemMissingFields:
    """Test requests with missing required fields."""

    def test_create_item_missing_name(self):
        """Test that request fails when name field is missing."""
        response = client.post(
            "/items",
            json={"price": 10.0}
        )
        assert response.status_code == 422

    def test_create_item_missing_price(self):
        """Test that request fails when price field is missing."""
        response = client.post(
            "/items",
            json={"name": "item"}
        )
        assert response.status_code == 422

    def test_create_item_empty_body(self):
        """Test that request fails with empty JSON body."""
        response = client.post("/items", json={})
        assert response.status_code == 422


class TestCreateItemInvalidTypes:
    """Test requests with invalid field types."""

    def test_create_item_price_as_string(self):
        """Test that string price is rejected."""
        response = client.post(
            "/items",
            json={"name": "item", "price": "not_a_number"}
        )
        assert response.status_code == 422

    def test_create_item_price_as_list(self):
        """Test that list price is rejected."""
        response = client.post(
            "/items",
            json={"name": "item", "price": [10, 20]}
        )
        assert response.status_code == 422

    def test_create_item_name_as_number(self):
        """Test that numeric name is rejected."""
        response = client.post(
            "/items",
            json={"name": 123, "price": 10.0}
        )
        assert response.status_code == 422

    def test_create_item_name_as_list(self):
        """Test that list name is rejected."""
        response = client.post(
            "/items",
            json={"name": ["item1", "item2"], "price": 10.0}
        )
        assert response.status_code == 422


class TestCreateItemEmptyName:
    """Test requests with empty name field."""

    def test_create_item_with_empty_string_name(self):
        """Test that empty string name is accepted (no validation for this)."""
        response = client.post(
            "/items",
            json={"name": "", "price": 10.0}
        )
        # Empty strings are valid in Pydantic by default
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == ""


class TestCreateItemEdgeCasePrices:
    """Test edge case prices."""

    def test_create_item_with_tiny_positive_price(self):
        """Test item creation with very small positive price."""
        response = client.post(
            "/items",
            json={"name": "tiny", "price": 1e-10}
        )
        assert response.status_code == 200
        assert response.json()["price"] == 1e-10

    def test_create_item_with_float_precision(self):
        """Test item creation with precise float values."""
        response = client.post(
            "/items",
            json={"name": "precise", "price": 19.99}
        )
        assert response.status_code == 200
        assert response.json()["price"] == 19.99

    def test_create_item_with_integer_as_price(self):
        """Test that integer prices are accepted."""
        response = client.post(
            "/items",
            json={"name": "item", "price": 5}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["price"] == 5.0
        assert isinstance(data["price"], (int, float))


class TestCreateItemResponseStructure:
    """Test response structure for create item endpoint."""

    def test_create_item_response_has_required_fields(self):
        """Test that response contains all required fields."""
        response = client.post(
            "/items",
            json={"name": "book", "price": 15.99}
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data
        assert len(data) == 3

    def test_create_item_id_is_correct_type(self):
        """Test that id field is an integer."""
        response = client.post(
            "/items",
            json={"name": "book", "price": 15.99}
        )
        data = response.json()
        assert isinstance(data["id"], int)

    def test_create_item_name_is_string(self):
        """Test that name field is a string."""
        response = client.post(
            "/items",
            json={"name": "book", "price": 15.99}
        )
        data = response.json()
        assert isinstance(data["name"], str)

    def test_create_item_price_is_number(self):
        """Test that price field is a number."""
        response = client.post(
            "/items",
            json={"name": "book", "price": 15.99}
        )
        data = response.json()
        assert isinstance(data["price"], (int, float))
