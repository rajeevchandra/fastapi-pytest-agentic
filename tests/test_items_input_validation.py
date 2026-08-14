"""Input validation and boundary testing for items endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price field validation and boundary conditions."""

    @pytest.mark.parametrize(
        "price,should_succeed",
        [
            (0.01, True),  # Minimum valid price
            (1.0, True),  # Standard price
            (100.0, True),  # Large price
            (9999.99, True),  # Very large price
            (0, False),  # Zero (invalid)
            (-1, False),  # Negative (invalid)
            (-0.01, False),  # Negative decimal (invalid)
            (-100.5, False),  # Large negative (invalid)
        ],
    )
    def test_price_boundary_conditions(self, price, should_succeed):
        """Test various price boundary conditions."""
        response = client.post("/items", json={"name": "test item", "price": price})

        if should_succeed:
            assert response.status_code == 200
            data = response.json()
            assert data["price"] == price
        else:
            assert response.status_code == 400
            assert "price must be > 0" in response.json()["detail"]

    def test_price_zero_rejected(self):
        """Test that price of exactly 0 is rejected."""
        response = client.post("/items", json={"name": "test", "price": 0})
        assert response.status_code == 400
        assert response.json()["detail"] == "price must be > 0"

    def test_price_negative_rejected(self):
        """Test that negative prices are rejected."""
        response = client.post("/items", json={"name": "test", "price": -50.0})
        assert response.status_code == 400
        assert response.json()["detail"] == "price must be > 0"


class TestCreateItemNameValidation:
    """Test name field validation and variations."""

    @pytest.mark.parametrize(
        "name",
        [
            "a",  # Single character
            "book",  # Normal name
            "Product Name",  # With space
            "item-123",  # With hyphen
            "Product_Item",  # With underscore
            "UPPERCASE ITEM",  # All caps
            "123",  # Numeric
            "item@special#char",  # Special characters
            "Very Long Product Name " * 5,  # Very long name
        ],
    )
    def test_various_name_formats(self, name):
        """Test that various name formats are accepted."""
        response = client.post("/items", json={"name": name, "price": 10.0})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == name
        assert data["price"] == 10.0

    def test_name_preserved_in_response(self):
        """Test that the provided name is exactly preserved in response."""
        test_name = "Test Item 123"
        response = client.post("/items", json={"name": test_name, "price": 25.5})
        assert response.status_code == 200
        assert response.json()["name"] == test_name


class TestCreateItemMissingFields:
    """Test handling of missing required fields."""

    def test_missing_price_field(self):
        """Test that missing price field is rejected."""
        response = client.post("/items", json={"name": "test"})
        assert response.status_code == 422
        assert "price" in str(response.json())

    def test_missing_name_field(self):
        """Test that missing name field is rejected."""
        response = client.post("/items", json={"price": 10.0})
        assert response.status_code == 422
        assert "name" in str(response.json())

    def test_missing_both_fields(self):
        """Test that missing both fields is rejected."""
        response = client.post("/items", json={})
        assert response.status_code == 422

    def test_null_price_value(self):
        """Test that null price is rejected."""
        response = client.post("/items", json={"name": "test", "price": None})
        assert response.status_code == 422

    def test_null_name_value(self):
        """Test that null name is rejected."""
        response = client.post("/items", json={"name": None, "price": 10.0})
        assert response.status_code == 422


class TestCreateItemInvalidTypes:
    """Test type validation for request fields."""

    def test_price_as_string_rejected(self):
        """Test that string price is rejected or coerced appropriately."""
        response = client.post("/items", json={"name": "test", "price": "10.0"})
        # FastAPI/Pydantic may coerce or reject
        assert response.status_code in [200, 422]

    def test_price_as_list_rejected(self):
        """Test that list price is rejected."""
        response = client.post("/items", json={"name": "test", "price": [10.0]})
        assert response.status_code == 422

    def test_price_as_object_rejected(self):
        """Test that object price is rejected."""
        response = client.post(
            "/items", json={"name": "test", "price": {"amount": 10.0}}
        )
        assert response.status_code == 422

    def test_name_as_number_coerced_or_rejected(self):
        """Test that numeric name is handled."""
        response = client.post("/items", json={"name": 123, "price": 10.0})
        assert response.status_code in [200, 422]

    def test_name_as_list_rejected(self):
        """Test that list name is rejected."""
        response = client.post("/items", json={"name": ["item"], "price": 10.0})
        assert response.status_code == 422


class TestCreateItemResponseStructure:
    """Test response structure validation."""

    def test_response_has_required_fields(self):
        """Test that response contains all required fields."""
        response = client.post("/items", json={"name": "test", "price": 10.0})
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data
        assert len(data) == 3

    def test_response_id_is_numeric(self):
        """Test that response id is numeric."""
        response = client.post("/items", json={"name": "test", "price": 10.0})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["id"], int)

    def test_response_price_is_numeric(self):
        """Test that response price is numeric."""
        response = client.post("/items", json={"name": "test", "price": 10.5})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["price"], (int, float))

    def test_response_name_is_string(self):
        """Test that response name is string."""
        response = client.post("/items", json={"name": "test", "price": 10.0})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["name"], str)


class TestCreateItemEdgeCases:
    """Test edge cases and corner scenarios."""

    def test_very_small_positive_price(self):
        """Test with very small positive price."""
        response = client.post("/items", json={"name": "test", "price": 0.001})
        assert response.status_code == 200
        assert response.json()["price"] == 0.001

    def test_very_large_price(self):
        """Test with very large price value."""
        response = client.post("/items", json={"name": "test", "price": 999999999.99})
        assert response.status_code == 200
        assert response.json()["price"] == 999999999.99

    def test_empty_string_name(self):
        """Test with empty string name."""
        response = client.post("/items", json={"name": "", "price": 10.0})
        assert response.status_code == 200
        assert response.json()["name"] == ""

    def test_whitespace_name(self):
        """Test with whitespace-only name."""
        response = client.post("/items", json={"name": "   ", "price": 10.0})
        assert response.status_code == 200
        assert response.json()["name"] == "   "

    def test_unicode_characters_in_name(self):
        """Test with unicode characters in name."""
        response = client.post("/items", json={"name": "café ☕", "price": 10.0})
        assert response.status_code == 200
        assert response.json()["name"] == "café ☕"

    def test_newline_in_name(self):
        """Test with newline in name."""
        response = client.post("/items", json={"name": "line1\nline2", "price": 10.0})
        assert response.status_code == 200
        assert response.json()["name"] == "line1\nline2"

    def test_price_precision_preserved(self):
        """Test that price decimal precision is preserved."""
        response = client.post("/items", json={"name": "test", "price": 12.34567})
        assert response.status_code == 200
        assert response.json()["price"] == 12.34567

    def test_multiple_sequential_creates(self):
        """Test multiple items can be created sequentially."""
        for i in range(5):
            response = client.post(
                "/items", json={"name": f"item{i}", "price": float(i + 1)}
            )
            assert response.status_code == 200
            assert response.json()["name"] == f"item{i}"
            assert response.json()["price"] == float(i + 1)
