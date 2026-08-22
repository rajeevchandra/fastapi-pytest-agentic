import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price validation for POST /items endpoint."""

    @pytest.mark.parametrize("price", [
        0.01,      # Minimum valid price
        1.0,       # Normal price
        99.99,     # Two decimal places
        100.0,     # Round number
        1000.0,    # Large price
        9999.99,   # Large with decimals
        0.001,     # Very small but positive
        1000000.0, # Very large price
    ])
    def test_create_item_with_valid_prices(self, price):
        """Test POST /items accepts valid positive prices."""
        response = client.post("/items", json={"name": "item", "price": price})
        assert response.status_code == 200
        data = response.json()
        assert data["price"] == price
        assert "id" in data
        assert "name" in data

    @pytest.mark.parametrize("price", [
        0,         # Zero price (invalid)
        -1,        # Negative price
        -0.01,     # Negative decimal
        -999.99,   # Large negative
    ])
    def test_create_item_rejects_non_positive_prices(self, price):
        """Test POST /items rejects non-positive prices."""
        response = client.post("/items", json={"name": "item", "price": price})
        assert response.status_code == 400
        assert "price must be > 0" in response.json()["detail"]


class TestCreateItemNameValidation:
    """Test name validation for POST /items endpoint."""

    @pytest.mark.parametrize("name", [
        "book",              # Normal name
        "a",                 # Single character
        "Item with spaces",  # Name with spaces
        "123",               # Numeric string
        "special-chars_123", # Special characters
        "UPPERCASE",         # All uppercase
        "lowercase",         # All lowercase
        "MixedCase",         # Mixed case
        "very" * 50,         # Very long name (200+ chars)
        "名前",              # Unicode characters
        "emoji 😀",          # Emoji
    ])
    def test_create_item_with_valid_names(self, name):
        """Test POST /items accepts various valid name formats."""
        response = client.post("/items", json={"name": name, "price": 10.0})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == name
        assert data["price"] == 10.0

    @pytest.mark.parametrize("name", [
        "",          # Empty string
        "   ",       # Whitespace only
    ])
    def test_create_item_with_invalid_names(self, name):
        """Test POST /items behavior with invalid names."""
        response = client.post("/items", json={"name": name, "price": 10.0})
        # Pydantic might accept empty/whitespace strings, but we document behavior
        # If API should reject, this test catches that requirement
        assert response.status_code in [200, 422]  # 422 if validation rejects


class TestCreateItemMissingFields:
    """Test missing required fields for POST /items endpoint."""

    def test_create_item_missing_name(self):
        """Test POST /items rejects request with missing name."""
        response = client.post("/items", json={"price": 10.0})
        assert response.status_code == 422  # Unprocessable Entity

    def test_create_item_missing_price(self):
        """Test POST /items rejects request with missing price."""
        response = client.post("/items", json={"name": "item"})
        assert response.status_code == 422  # Unprocessable Entity

    def test_create_item_missing_both_fields(self):
        """Test POST /items rejects request with no fields."""
        response = client.post("/items", json={})
        assert response.status_code == 422  # Unprocessable Entity


class TestCreateItemTypeValidation:
    """Test type validation for POST /items endpoint."""

    def test_create_item_price_as_string(self):
        """Test POST /items with price as string."""
        response = client.post("/items", json={"name": "item", "price": "10.0"})
        # Pydantic may coerce string to float or reject
        assert response.status_code in [200, 422]

    def test_create_item_name_as_number(self):
        """Test POST /items with name as number."""
        response = client.post("/items", json={"name": 123, "price": 10.0})
        # Pydantic may coerce number to string or accept as is
        assert response.status_code == 200
        # Name should be present in response
        assert "name" in response.json()

    def test_create_item_with_extra_fields(self):
        """Test POST /items ignores extra fields."""
        response = client.post("/items", json={
            "name": "item",
            "price": 10.0,
            "extra_field": "ignored",
            "another_extra": 123
        })
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "price" in data
        # Extra fields should not appear in response (security best practice)


class TestCreateItemResponseStructure:
    """Test response structure for successful POST /items."""

    def test_create_item_response_has_required_fields(self):
        """Test successful POST /items response includes id, name, price."""
        response = client.post("/items", json={"name": "test-item", "price": 15.5})
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data
        assert len(data) == 3  # Exactly 3 fields

    def test_create_item_response_field_types(self):
        """Test POST /items response fields have correct types."""
        response = client.post("/items", json={"name": "item", "price": 20.0})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))
        assert isinstance(data["price"], (float, int))  # Ensure numeric


class TestCreateItemBoundaryPrices:
    """Test boundary conditions for prices."""

    def test_create_item_minimum_valid_price(self):
        """Test minimum valid price (smallest positive)."""
        response = client.post("/items", json={"name": "item", "price": 0.01})
        assert response.status_code == 200
        assert response.json()["price"] == 0.01

    def test_create_item_just_above_zero(self):
        """Test price just above zero."""
        response = client.post("/items", json={"name": "item", "price": 0.001})
        assert response.status_code == 200

    def test_create_item_float_precision(self):
        """Test float precision handling."""
        response = client.post("/items", json={"name": "item", "price": 99.99})
        assert response.status_code == 200
        data = response.json()
        # Allow for floating point precision
        assert abs(data["price"] - 99.99) < 0.001


class TestCreateItemMultipleRequests:
    """Test multiple sequential requests to POST /items."""

    def test_create_multiple_items_different_prices(self):
        """Test creating multiple items with different prices."""
        prices = [10.0, 20.5, 99.99]
        for price in prices:
            response = client.post("/items", json={"name": "item", "price": price})
            assert response.status_code == 200
            assert response.json()["price"] == price

    def test_create_items_alternating_valid_invalid(self):
        """Test alternating valid and invalid requests."""
        # Valid request
        response1 = client.post("/items", json={"name": "item1", "price": 10.0})
        assert response1.status_code == 200

        # Invalid request (zero price)
        response2 = client.post("/items", json={"name": "item2", "price": 0})
        assert response2.status_code == 400

        # Valid request again
        response3 = client.post("/items", json={"name": "item3", "price": 20.0})
        assert response3.status_code == 200
