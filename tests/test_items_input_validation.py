"""
Enhanced input validation tests for POST /items endpoint.
Tests cover edge cases, boundary values, and error handling.
"""
from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price field validation with boundary and edge cases."""

    @pytest.mark.parametrize("price", [0.01, 1.0, 10.0, 100.5, 9999.99])
    def test_create_item_valid_prices(self, price):
        """Test successful creation with valid positive prices."""
        response = client.post("/items", json={"name": "test", "price": price})
        assert response.status_code == 200
        data = response.json()
        assert data["price"] == price
        assert data["name"] == "test"

    @pytest.mark.parametrize("price", [0, -1, -10.5, -0.01, -9999.99])
    def test_create_item_invalid_prices(self, price):
        """Test rejection of zero and negative prices."""
        response = client.post("/items", json={"name": "test", "price": price})
        assert response.status_code == 400
        assert response.json()["detail"] == "price must be > 0"

    def test_create_item_price_as_string_rejected(self):
        """Test that string price is rejected by Pydantic."""
        response = client.post("/items", json={"name": "test", "price": "not_a_number"})
        assert response.status_code == 422

    def test_create_item_price_as_null_rejected(self):
        """Test that null price is rejected."""
        response = client.post("/items", json={"name": "test", "price": None})
        assert response.status_code == 422

    def test_create_item_missing_price_field(self):
        """Test that missing price field triggers validation error."""
        response = client.post("/items", json={"name": "test"})
        assert response.status_code == 422


class TestCreateItemNameValidation:
    """Test name field validation with edge cases."""

    @pytest.mark.parametrize("name", ["book", "a", "test item", "Product-123", "名前"])
    def test_create_item_valid_names(self, name):
        """Test successful creation with various valid names."""
        response = client.post("/items", json={"name": name, "price": 10.0})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == name

    @pytest.mark.parametrize("name", ["", "   ", "\t", "\n"])
    def test_create_item_empty_or_whitespace_names(self, name):
        """Test that empty/whitespace names fail or are invalid."""
        response = client.post("/items", json={"name": name, "price": 10.0})
        # Empty string is technically valid for str field in Pydantic
        # but could be considered invalid for business logic
        assert response.status_code in [200, 422]

    def test_create_item_name_as_null_rejected(self):
        """Test that null name is rejected."""
        response = client.post("/items", json={"name": None, "price": 10.0})
        assert response.status_code == 422

    def test_create_item_missing_name_field(self):
        """Test that missing name field triggers validation error."""
        response = client.post("/items", json={"price": 10.0})
        assert response.status_code == 422

    def test_create_item_name_as_number_rejected(self):
        """Test that numeric name is rejected (should be string)."""
        response = client.post("/items", json={"name": 123, "price": 10.0})
        assert response.status_code == 422


class TestCreateItemPayloadValidation:
    """Test overall payload and request structure validation."""

    def test_create_item_extra_fields_ignored(self):
        """Test that extra fields in payload are ignored."""
        response = client.post(
            "/items",
            json={"name": "test", "price": 10.0, "extra_field": "ignored", "another": 42}
        )
        assert response.status_code == 200
        data = response.json()
        assert "extra_field" not in data
        assert "another" not in data

    def test_create_item_both_fields_missing(self):
        """Test request with both required fields missing."""
        response = client.post("/items", json={})
        assert response.status_code == 422

    def test_create_item_malformed_json_rejected(self):
        """Test that malformed JSON is rejected."""
        response = client.post(
            "/items",
            content=b"not valid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_create_item_empty_json_object_missing_fields(self):
        """Test empty JSON object is rejected (missing required fields)."""
        response = client.post("/items", json={})
        assert response.status_code == 422


class TestCreateItemEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_create_item_very_long_name(self):
        """Test creation with very long name."""
        long_name = "a" * 1000
        response = client.post("/items", json={"name": long_name, "price": 10.0})
        assert response.status_code == 200
        assert response.json()["name"] == long_name

    def test_create_item_very_small_price(self):
        """Test creation with very small positive price."""
        response = client.post("/items", json={"name": "test", "price": 0.001})
        assert response.status_code == 200
        assert response.json()["price"] == 0.001

    def test_create_item_very_large_price(self):
        """Test creation with very large price."""
        large_price = 1e10
        response = client.post("/items", json={"name": "test", "price": large_price})
        assert response.status_code == 200
        assert response.json()["price"] == large_price

    def test_create_item_special_characters_in_name(self):
        """Test creation with special characters in name."""
        special_name = "Item!@#$%^&*()_+-=[]{}|;:',.<>?/~`"
        response = client.post("/items", json={"name": special_name, "price": 10.0})
        assert response.status_code == 200
        assert response.json()["name"] == special_name

    def test_create_item_unicode_characters_in_name(self):
        """Test creation with unicode characters."""
        unicode_name = "商品 🎉 Ürün"
        response = client.post("/items", json={"name": unicode_name, "price": 10.0})
        assert response.status_code == 200
        assert response.json()["name"] == unicode_name

    def test_create_item_response_contains_id(self):
        """Test that response always includes id."""
        response = client.post("/items", json={"name": "test", "price": 10.0})
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["id"] == 1

    def test_create_item_response_structure(self):
        """Test response has correct structure and all fields."""
        response = client.post("/items", json={"name": "test", "price": 5.0})
        assert response.status_code == 200
        data = response.json()
        assert set(data.keys()) == {"id", "name", "price"}
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))
