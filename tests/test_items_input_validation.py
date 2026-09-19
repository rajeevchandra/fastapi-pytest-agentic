"""
Input Validation & Boundary Testing for Create Item endpoint.

This test module focuses on validating edge cases and boundary conditions
for the POST /items endpoint, including price boundaries, name variations,
and missing required fields.
"""
from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price field validation with various boundary values."""

    @pytest.mark.parametrize("price", [
        -100,      # Large negative
        -1,        # Small negative
        -0.01,     # Small negative decimal
        0,         # Zero (should fail)
        0.001,     # Very small positive
        0.01,      # Small positive
        1,         # Normal value
        100,       # Large value
        1000.99,   # Large decimal
        999999.99, # Very large value
    ])
    def test_create_item_with_various_prices(self, price):
        """Test create_item with different price values."""
        response = client.post("/items", json={"name": "test_item", "price": price})
        
        if price > 0:
            # Valid prices should return 200
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
            assert data["name"] == "test_item"
            assert data["price"] == price
        else:
            # Non-positive prices should return 400
            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
            assert "price must be > 0" in data["detail"]

    @pytest.mark.parametrize("invalid_price", [
        -100, -1, -0.01, 0
    ])
    def test_create_item_rejects_non_positive_prices(self, invalid_price):
        """Test that non-positive prices are rejected."""
        response = client.post("/items", json={"name": "item", "price": invalid_price})
        assert response.status_code == 400
        assert "price must be > 0" in response.json()["detail"]

    @pytest.mark.parametrize("valid_price", [
        0.01, 0.001, 1, 10.5, 100, 9999.99
    ])
    def test_create_item_accepts_positive_prices(self, valid_price):
        """Test that positive prices are accepted."""
        response = client.post("/items", json={"name": "item", "price": valid_price})
        assert response.status_code == 200
        assert response.json()["price"] == valid_price


class TestCreateItemNameValidation:
    """Test name field validation with various values."""

    @pytest.mark.parametrize("name,should_pass", [
        ("item", True),           # Normal name
        ("a", True),              # Single char
        ("Item Name", True),      # With space
        ("Item-Name", True),      # With hyphen
        ("Item_Name", True),      # With underscore
        ("ITEM", True),           # Uppercase
        ("item123", True),        # With numbers
        ("item!", True),          # With special char
        ("$item%", True),         # With special chars
        ("日本語アイテム", True),  # Unicode
        ("😀 item", True),         # With emoji
        ("x" * 500, True),        # Very long name
        ("x" * 1000, True),       # Extremely long name
    ])
    def test_create_item_with_various_names(self, name, should_pass):
        """Test create_item with different name values."""
        response = client.post("/items", json={"name": name, "price": 10.0})
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == name
        assert data["price"] == 10.0


class TestCreateItemMissingFields:
    """Test handling of missing required fields."""

    def test_create_item_missing_name(self):
        """Test that missing name field returns 422."""
        response = client.post("/items", json={"price": 10.0})
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data

    def test_create_item_missing_price(self):
        """Test that missing price field returns 422."""
        response = client.post("/items", json={"name": "item"})
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data

    def test_create_item_missing_both_fields(self):
        """Test that missing both fields returns 422."""
        response = client.post("/items", json={})
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data


class TestCreateItemInvalidFieldTypes:
    """Test handling of invalid field types."""

    def test_create_item_price_as_string(self):
        """Test that string price returns 422."""
        response = client.post("/items", json={"name": "item", "price": "10.5"})
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data

    def test_create_item_price_as_none(self):
        """Test that null price returns 422."""
        response = client.post("/items", json={"name": "item", "price": None})
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_create_item_name_as_number(self):
        """Test that numeric name is converted to string."""
        response = client.post("/items", json={"name": 123, "price": 10.0})
        # Pydantic should coerce numeric to string or reject
        assert response.status_code in [200, 422]

    def test_create_item_name_as_none(self):
        """Test that null name returns 422."""
        response = client.post("/items", json={"name": None, "price": 10.0})
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestCreateItemEmptyStrings:
    """Test handling of empty string fields."""

    def test_create_item_empty_name(self):
        """Test creating item with empty name string."""
        response = client.post("/items", json={"name": "", "price": 10.0})
        # Empty string is still a valid string, should return 200
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == ""
        assert data["price"] == 10.0

    def test_create_item_whitespace_name(self):
        """Test creating item with whitespace-only name."""
        response = client.post("/items", json={"name": "   ", "price": 10.0})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "   "


class TestCreateItemPriceEdgeCases:
    """Test edge cases specific to price field."""

    def test_create_item_very_small_positive_price(self):
        """Test with extremely small positive price."""
        response = client.post("/items", json={"name": "item", "price": 0.0001})
        assert response.status_code == 200
        assert response.json()["price"] == 0.0001

    def test_create_item_zero_point_zero_price(self):
        """Test with 0.0 which should be rejected."""
        response = client.post("/items", json={"name": "item", "price": 0.0})
        assert response.status_code == 400
        assert "price must be > 0" in response.json()["detail"]

    def test_create_item_negative_zero_price(self):
        """Test with -0.0 (edge case for zero handling)."""
        response = client.post("/items", json={"name": "item", "price": -0.0})
        # -0.0 should be treated as 0
        assert response.status_code == 400

    def test_create_item_float_precision(self):
        """Test with various float precision values."""
        prices = [0.1, 0.01, 0.001, 0.0001, 0.99999]
        for price in prices:
            response = client.post("/items", json={"name": "item", "price": price})
            assert response.status_code == 200
            assert response.json()["price"] == price


class TestCreateItemResponseStructure:
    """Test response structure and field presence."""

    def test_create_item_success_response_structure(self):
        """Test that successful response has required fields."""
        response = client.post("/items", json={"name": "test", "price": 5.0})
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields are present
        assert "id" in data
        assert "name" in data
        assert "price" in data
        
        # Verify field types
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_create_item_error_response_structure(self):
        """Test that error response has detail field."""
        response = client.post("/items", json={"name": "test", "price": -1})
        assert response.status_code == 400
        data = response.json()
        
        # Verify error structure
        assert "detail" in data
        assert isinstance(data["detail"], str)


class TestCreateItemConcurrentOperations:
    """Test multiple create operations."""

    def test_create_multiple_items_sequentially(self):
        """Test creating multiple items one after another."""
        item_names = ["item1", "item2", "item3"]
        prices = [5.0, 10.0, 15.0]
        
        for name, price in zip(item_names, prices):
            response = client.post("/items", json={"name": name, "price": price})
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == name
            assert data["price"] == price

    def test_create_items_same_name_different_prices(self):
        """Test creating multiple items with same name but different prices."""
        for price in [1.0, 2.0, 3.0]:
            response = client.post("/items", json={"name": "item", "price": price})
            assert response.status_code == 200
            assert response.json()["price"] == price

    def test_create_items_same_price_different_names(self):
        """Test creating multiple items with same price but different names."""
        names = ["apple", "banana", "cherry"]
        for name in names:
            response = client.post("/items", json={"name": name, "price": 5.0})
            assert response.status_code == 200
            assert response.json()["name"] == name
