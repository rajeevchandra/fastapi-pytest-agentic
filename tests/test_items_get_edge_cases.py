"""Edge cases, path parameters, and integration scenarios."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameters:
    """Test get_item endpoint with various path parameter values."""

    def test_get_item_valid_positive_integer(self):
        """Test get_item with valid positive integer ID."""
        response = client.get("/items/1")
        assert response.status_code == 200

    @pytest.mark.parametrize("item_id", [2, 3, 10, 100, 1000, 999999])
    def test_get_item_different_positive_ids(self, item_id):
        """Test get_item with various positive IDs returns 404."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == 404

    @pytest.mark.parametrize("item_id", [0, -1, -10, -100, -999])
    def test_get_item_zero_and_negative_ids(self, item_id):
        """Test get_item with zero and negative IDs returns 404."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == 404

    def test_get_item_id_zero_returns_404(self):
        """Test that ID 0 returns 404."""
        response = client.get("/items/0")
        assert response.status_code == 404

    def test_get_item_id_negative_one_returns_404(self):
        """Test that ID -1 returns 404."""
        response = client.get("/items/-1")
        assert response.status_code == 404

    def test_get_item_very_large_id(self):
        """Test get_item with very large ID."""
        response = client.get(f"/items/{2**31 - 1}")
        assert response.status_code == 404

    def test_get_item_id_one_is_special(self):
        """Test that only ID 1 returns the special item."""
        # ID 1 should succeed
        response = client.get("/items/1")
        assert response.status_code == 200
        assert response.json()["id"] == 1
        
        # ID 0, 2, -1 should fail
        for item_id in [0, 2, -1]:
            response = client.get(f"/items/{item_id}")
            assert response.status_code == 404


class TestCreateItemPriceEdgeCases:
    """Test create_item with extreme price values."""

    def test_create_item_price_boundary_zero_point_zero_one(self):
        """Test minimum positive price 0.01."""
        response = client.post("/items", json={"name": "test", "price": 0.01})
        assert response.status_code == 200
        assert response.json()["price"] == 0.01

    def test_create_item_price_boundary_just_below_zero(self):
        """Test price just below zero is rejected."""
        response = client.post("/items", json={"name": "test", "price": -0.001})
        assert response.status_code == 400

    def test_create_item_price_very_large_value(self):
        """Test very large price value."""
        large_price = 1e15
        response = client.post("/items", json={"name": "test", "price": large_price})
        assert response.status_code == 200
        assert response.json()["price"] == large_price

    def test_create_item_price_max_float(self):
        """Test maximum float value."""
        max_price = 1e308
        response = client.post("/items", json={"name": "test", "price": max_price})
        assert response.status_code == 200

    def test_create_item_price_repeating_decimal(self):
        """Test price with repeating decimal pattern."""
        price = 0.33333333
        response = client.post("/items", json={"name": "test", "price": price})
        assert response.status_code == 200
        assert response.json()["price"] == price

    def test_create_item_price_scientific_notation(self):
        """Test price in scientific notation."""
        price = 1e5
        response = client.post("/items", json={"name": "test", "price": price})
        assert response.status_code == 200
        assert response.json()["price"] == price

    def test_create_item_integer_price(self):
        """Test integer price value."""
        response = client.post("/items", json={"name": "test", "price": 10})
        assert response.status_code == 200
        assert response.json()["price"] == 10


class TestCreateItemNameEdgeCases:
    """Test create_item with extreme name values."""

    def test_create_item_single_character_name(self):
        """Test single character name."""
        response = client.post("/items", json={"name": "a", "price": 10.0})
        assert response.status_code == 200
        assert response.json()["name"] == "a"

    def test_create_item_very_long_name(self):
        """Test very long name (10000 characters)."""
        long_name = "x" * 10000
        response = client.post("/items", json={"name": long_name, "price": 10.0})
        assert response.status_code == 200
        assert response.json()["name"] == long_name

    def test_create_item_whitespace_only_name(self):
        """Test name with only whitespace."""
        response = client.post("/items", json={"name": "   ", "price": 10.0})
        assert response.status_code == 200
        assert response.json()["name"] == "   "

    def test_create_item_newline_in_name(self):
        """Test name containing newline characters."""
        response = client.post("/items", json={"name": "line1\nline2", "price": 10.0})
        assert response.status_code == 200
        assert "line1\nline2" in response.json()["name"]

    def test_create_item_tab_in_name(self):
        """Test name containing tab characters."""
        response = client.post("/items", json={"name": "col1\tcol2", "price": 10.0})
        assert response.status_code == 200
        assert "col1\tcol2" in response.json()["name"]

    def test_create_item_name_with_null_byte(self):
        """Test name with null byte character."""
        response = client.post("/items", json={"name": "test\x00null", "price": 10.0})
        assert response.status_code == 200

    def test_create_item_name_all_special_chars(self):
        """Test name with all special characters."""
        special_name = "!@#$%^&*()_+-=[]{}|;:',.<>?/~`"
        response = client.post("/items", json={"name": special_name, "price": 10.0})
        assert response.status_code == 200
        assert response.json()["name"] == special_name


class TestCreateItemSequentialRequests:
    """Test create_item with sequential requests."""

    def test_create_multiple_items_sequentially(self):
        """Test creating multiple items in sequence."""
        responses = []
        for i in range(5):
            response = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            responses.append(response)
            assert response.status_code == 200

    def test_create_multiple_items_returns_same_id(self):
        """Test that multiple create requests return same ID."""
        ids = []
        for i in range(3):
            response = client.post("/items", json={"name": f"item{i}", "price": 10.0})
            ids.append(response.json()["id"])
        
        # All should have id = 1
        assert all(id == 1 for id in ids)

    def test_create_and_get_item_sequence(self):
        """Test creating and then getting an item."""
        # Create an item
        create_response = client.post("/items", json={"name": "created", "price": 15.0})
        assert create_response.status_code == 200
        created_id = create_response.json()["id"]
        
        # Get the item
        get_response = client.get(f"/items/{created_id}")
        assert get_response.status_code == 200
        assert get_response.json()["id"] == created_id

    def test_create_item_with_various_prices_sequentially(self):
        """Test creating items with different prices in sequence."""
        prices = [0.01, 1.0, 100.0, 999.99, 10000.0]
        for price in prices:
            response = client.post("/items", json={"name": "test", "price": price})
            assert response.status_code == 200
            assert response.json()["price"] == price

    def test_create_items_then_get_all_scenarios(self):
        """Test creating multiple items and getting various IDs."""
        # Create several items
        for i in range(3):
            response = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            assert response.status_code == 200
        
        # Try getting ID 1 (should exist)
        response = client.get("/items/1")
        assert response.status_code == 200
        
        # Try getting other IDs (should not exist)
        for item_id in [2, 3, 999]:
            response = client.get(f"/items/{item_id}")
            assert response.status_code == 404


class TestMultipleEndpointsIntegration:
    """Test integration scenarios across multiple endpoints."""

    def test_health_then_create_then_get(self):
        """Test complete flow: health check, create item, get item."""
        # Check health
        health_response = client.get("/health")
        assert health_response.status_code == 200
        
        # Create item
        create_response = client.post("/items", json={"name": "integration_test", "price": 50.0})
        assert create_response.status_code == 200
        created_id = create_response.json()["id"]
        
        # Get item
        get_response = client.get(f"/items/{created_id}")
        assert get_response.status_code == 200
        assert get_response.json()["id"] == created_id

    def test_create_item_invalid_then_valid(self):
        """Test creating item with invalid data then valid data."""
        # Try invalid
        response = client.post("/items", json={"name": "bad", "price": -10})
        assert response.status_code == 400
        
        # Then valid
        response = client.post("/items", json={"name": "good", "price": 10.0})
        assert response.status_code == 200

    def test_get_nonexistent_then_existent(self):
        """Test getting non-existent then existent item."""
        # Try non-existent
        response = client.get("/items/999")
        assert response.status_code == 404
        
        # Then existent
        response = client.get("/items/1")
        assert response.status_code == 200

    def test_interleaved_get_and_create(self):
        """Test interleaved get and create operations."""
        # Get item 1
        response = client.get("/items/1")
        assert response.status_code == 200
        
        # Create new item
        response = client.post("/items", json={"name": "new", "price": 20.0})
        assert response.status_code == 200
        
        # Get item 1 again
        response = client.get("/items/1")
        assert response.status_code == 200

    def test_create_with_error_response_validation(self):
        """Test error response from create_item is properly formatted."""
        response = client.post("/items", json={"name": "test", "price": 0})
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

    def test_get_nonexistent_error_response_validation(self):
        """Test error response from get_item is properly formatted."""
        response = client.get("/items/2")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)
        assert data["detail"] == "not found"


class TestResponseConsistency:
    """Test consistency of responses across different operations."""

    def test_create_response_structure_consistency(self):
        """Test that multiple create requests have consistent response structure."""
        responses = []
        for i in range(3):
            response = client.post("/items", json={"name": f"item{i}", "price": 10.0})
            responses.append(response.json())
        
        # All should have same keys
        expected_keys = {"id", "name", "price"}
        for data in responses:
            assert set(data.keys()) == expected_keys

    def test_get_response_structure_consistency(self):
        """Test that multiple get requests return consistent response structure."""
        for _ in range(3):
            response = client.get("/items/1")
            data = response.json()
            expected_keys = {"id", "name", "price"}
            assert set(data.keys()) == expected_keys

    def test_error_response_structure_consistency(self):
        """Test that error responses have consistent structure."""
        # Test 400 error
        response1 = client.post("/items", json={"name": "test", "price": 0})
        assert "detail" in response1.json()
        
        # Test 400 error with different value
        response2 = client.post("/items", json={"name": "test", "price": -5})
        assert "detail" in response2.json()
        
        # Test 404 error
        response3 = client.get("/items/999")
        assert "detail" in response3.json()

    def test_price_value_preservation(self):
        """Test that price values are preserved accurately across operations."""
        test_prices = [0.01, 1.5, 99.99, 100.0, 1000.0]
        for price in test_prices:
            response = client.post("/items", json={"name": "test", "price": price})
            returned_price = response.json()["price"]
            assert returned_price == price

    def test_name_value_preservation(self):
        """Test that name values are preserved accurately across operations."""
        test_names = ["simple", "with spaces", "with-hyphens", "123numeric", "café", ""]
        for name in test_names:
            response = client.post("/items", json={"name": name, "price": 10.0})
            returned_name = response.json()["name"]
            assert returned_name == name


class TestDataIntegrity:
    """Test data integrity across multiple operations."""

    def test_create_item_data_not_corrupted(self):
        """Test that created item data is not corrupted."""
        original_data = {"name": "test_item", "price": 42.5}
        response = client.post("/items", json=original_data)
        returned_data = response.json()
        
        assert returned_data["name"] == original_data["name"]
        assert returned_data["price"] == original_data["price"]

    def test_get_item_data_not_modified(self):
        """Test that getting item doesn't modify it."""
        # Get item multiple times
        responses = [client.get("/items/1") for _ in range(5)]
        
        # All responses should be identical
        first_data = responses[0].json()
        for response in responses[1:]:
            assert response.json() == first_data

    def test_special_characters_preserved(self):
        """Test that special characters in name are preserved."""
        special_names = [
            "name with 'quotes'",
            'name with "double quotes"',
            "name with \\backslash",
            "name with /forward/slash",
            "name with |pipe|",
        ]
        for name in special_names:
            response = client.post("/items", json={"name": name, "price": 10.0})
            assert response.json()["name"] == name

    def test_unicode_characters_preserved(self):
        """Test that unicode characters are preserved."""
        unicode_names = ["café", "naïve", "Москва", "北京", "🎉🎊"]
        for name in unicode_names:
            response = client.post("/items", json={"name": name, "price": 10.0})
            assert response.json()["name"] == name
