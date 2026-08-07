"""
Path parameter edge cases and integration testing for the items API.

This module tests:
- Path parameter boundary values and edge cases
- Integration scenarios with multiple operations
- State consistency across API calls
- Special parameter values (negative, zero, large numbers)
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test path parameter validation for get_item endpoint."""

    @pytest.mark.parametrize("item_id,should_be_found", [
        (1, True),           # Valid: known item
        (2, False),          # Not found
        (0, False),          # Boundary: zero
        (-1, False),         # Negative
        (-100, False),       # Negative large
        (100, False),        # Large number
        (999999, False),     # Very large number
        (int(1e9), False),   # Billion
    ])
    def test_get_item_various_ids(self, item_id, should_be_found):
        """Test various item IDs including boundary values."""
        response = client.get(f"/items/{item_id}")
        
        if should_be_found:
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == item_id
        else:
            assert response.status_code == 404

    def test_get_item_zero_id(self):
        """Test that ID zero returns 404."""
        response = client.get("/items/0")
        assert response.status_code == 404

    def test_get_item_negative_id(self):
        """Test that negative IDs return 404."""
        response = client.get("/items/-1")
        assert response.status_code == 404

    def test_get_item_negative_large_id(self):
        """Test that large negative IDs return 404."""
        response = client.get("/items/-999")
        assert response.status_code == 404

    def test_get_item_very_large_id(self):
        """Test that very large IDs return 404."""
        response = client.get(f"/items/{int(1e15)}")
        assert response.status_code == 404

    def test_get_item_boundary_id_just_above_one(self):
        """Test that ID 2 (just above valid) returns 404."""
        response = client.get("/items/2")
        assert response.status_code == 404

    def test_get_item_boundary_id_just_below_one(self):
        """Test that ID 0 (just below valid) returns 404."""
        response = client.get("/items/0")
        assert response.status_code == 404


class TestGetItemResponseConsistency:
    """Test response consistency for the same item across multiple calls."""

    def test_get_item_repeated_calls_same_response(self):
        """Test that repeated calls for item 1 return identical responses."""
        responses = [client.get("/items/1").json() for _ in range(3)]
        assert all(r == responses[0] for r in responses)

    def test_get_item_one_consistency(self):
        """Test that item 1 has consistent field values."""
        response = client.get("/items/1")
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0

    def test_get_item_multiple_ids_different_responses(self):
        """Test that different valid searches work properly."""
        # Item 1 exists
        response_1 = client.get("/items/1")
        assert response_1.status_code == 200
        
        # Item 2 doesn't exist
        response_2 = client.get("/items/2")
        assert response_2.status_code == 404


class TestCreateThenGetIntegration:
    """Test integration of create and get operations."""

    def test_create_item_returns_id_one(self):
        """Test that created items always get id 1."""
        response = client.post("/items", json={"name": "new_item", "price": 15.0})
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1

    def test_create_and_get_same_item(self):
        """Test creating an item and verifying it can be retrieved."""
        # Create item
        create_response = client.post("/items", json={"name": "book", "price": 12.99})
        assert create_response.status_code == 200
        
        # Get the created item
        get_response = client.get("/items/1")
        assert get_response.status_code == 200
        
        # They should have matching fields
        created = create_response.json()
        retrieved = get_response.json()
        assert created["id"] == retrieved["id"]

    def test_multiple_creates_all_have_id_one(self):
        """Test that each create operation returns id 1."""
        items = [
            {"name": "item1", "price": 10.0},
            {"name": "item2", "price": 20.0},
            {"name": "item3", "price": 30.0},
        ]
        
        for item in items:
            response = client.post("/items", json=item)
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1


class TestAPIEndpointSequences:
    """Test various sequences of API operations."""

    def test_health_then_get_item(self):
        """Test calling health check followed by get item."""
        health_response = client.get("/health")
        assert health_response.status_code == 200
        
        get_response = client.get("/items/1")
        assert get_response.status_code == 200

    def test_health_then_create_item(self):
        """Test calling health check followed by create item."""
        health_response = client.get("/health")
        assert health_response.status_code == 200
        
        create_response = client.post("/items", json={"name": "test", "price": 10.0})
        assert create_response.status_code == 200

    def test_create_item_then_health(self):
        """Test creating item followed by health check."""
        create_response = client.post("/items", json={"name": "test", "price": 10.0})
        assert create_response.status_code == 200
        
        health_response = client.get("/health")
        assert health_response.status_code == 200

    def test_create_multiple_different_items(self):
        """Test creating multiple different items."""
        items = [
            {"name": "widget", "price": 5.99},
            {"name": "gadget", "price": 15.99},
            {"name": "doohickey", "price": 25.99},
        ]
        
        for item in items:
            response = client.post("/items", json=item)
            assert response.status_code == 200
            assert response.json()["name"] == item["name"]
            assert response.json()["price"] == item["price"]


class TestPathParameterBoundaryValues:
    """Comprehensive boundary value testing for path parameters."""

    def test_item_id_one_is_valid(self):
        """Test that ID 1 is valid and exists."""
        response = client.get("/items/1")
        assert response.status_code == 200
        assert response.json()["id"] == 1

    def test_item_id_zero_is_invalid(self):
        """Test that ID 0 is invalid."""
        response = client.get("/items/0")
        assert response.status_code == 404

    def test_item_id_two_is_not_found(self):
        """Test that ID 2 doesn't exist."""
        response = client.get("/items/2")
        assert response.status_code == 404

    def test_item_id_negative_one_is_invalid(self):
        """Test that ID -1 is invalid."""
        response = client.get("/items/-1")
        assert response.status_code == 404

    def test_item_id_max_int_is_invalid(self):
        """Test that maximum integer value returns 404."""
        response = client.get(f"/items/{2**31-1}")
        assert response.status_code == 404


class TestCreateItemPriceIntegration:
    """Integration tests for create item with various prices."""

    @pytest.mark.parametrize("price", [0.01, 1.0, 10.99, 100.0, 9999.99])
    def test_create_items_various_prices(self, price):
        """Test creating items with various valid prices."""
        response = client.post("/items", json={"name": "item", "price": price})
        assert response.status_code == 200
        data = response.json()
        assert data["price"] == price

    @pytest.mark.parametrize("price", [0, -1, -0.01, -100])
    def test_create_items_invalid_prices_rejected(self, price):
        """Test that invalid prices are rejected."""
        response = client.post("/items", json={"name": "item", "price": price})
        assert response.status_code == 400


class TestCreateItemNameIntegration:
    """Integration tests for create item with various names."""

    @pytest.mark.parametrize("name", ["a", "widget", "My Product", "Item-123", "用品"])
    def test_create_items_various_names(self, name):
        """Test creating items with various valid names."""
        response = client.post("/items", json={"name": name, "price": 10.0})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == name

    def test_create_items_empty_name_invalid(self):
        """Test that empty name is invalid."""
        response = client.post("/items", json={"name": "", "price": 10.0})
        assert response.status_code == 422


class TestResponseDataTypes:
    """Test that response data types are consistent across operations."""

    def test_created_item_id_is_int(self):
        """Test that created item ID is integer."""
        response = client.post("/items", json={"name": "test", "price": 10.0})
        data = response.json()
        assert isinstance(data["id"], int)

    def test_retrieved_item_id_is_int(self):
        """Test that retrieved item ID is integer."""
        response = client.get("/items/1")
        data = response.json()
        assert isinstance(data["id"], int)

    def test_created_item_name_is_string(self):
        """Test that created item name is string."""
        response = client.post("/items", json={"name": "test", "price": 10.0})
        data = response.json()
        assert isinstance(data["name"], str)

    def test_created_item_price_is_number(self):
        """Test that created item price is number."""
        response = client.post("/items", json={"name": "test", "price": 10.0})
        data = response.json()
        assert isinstance(data["price"], (int, float))

    def test_retrieved_item_price_is_number(self):
        """Test that retrieved item price is number."""
        response = client.get("/items/1")
        data = response.json()
        assert isinstance(data["price"], (int, float))


class TestErrorStatePersistence:
    """Test that errors don't affect subsequent operations."""

    def test_failed_create_then_successful_create(self):
        """Test that failed create doesn't prevent successful create."""
        # Failed create (invalid price)
        fail_response = client.post("/items", json={"name": "bad", "price": 0})
        assert fail_response.status_code == 400
        
        # Successful create should still work
        success_response = client.post("/items", json={"name": "good", "price": 10.0})
        assert success_response.status_code == 200

    def test_failed_get_then_successful_get(self):
        """Test that failed get doesn't prevent successful get."""
        # Failed get (not found)
        fail_response = client.get("/items/999")
        assert fail_response.status_code == 404
        
        # Successful get should still work
        success_response = client.get("/items/1")
        assert success_response.status_code == 200

    def test_failed_create_doesnt_affect_get_item_one(self):
        """Test that invalid create attempts don't affect item 1."""
        # Try multiple invalid creates
        for price in [0, -1, -100]:
            response = client.post("/items", json={"name": "test", "price": price})
            assert response.status_code == 400
        
        # Item 1 should still be retrievable
        response = client.get("/items/1")
        assert response.status_code == 200
        assert response.json()["id"] == 1


class TestEndToEndScenarios:
    """Test end-to-end realistic scenarios."""

    def test_health_check_flow(self):
        """Test basic health check flow."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_create_and_retrieve_flow(self):
        """Test complete create and retrieve flow."""
        # Create an item
        create_response = client.post(
            "/items",
            json={"name": "laptop", "price": 999.99}
        )
        assert create_response.status_code == 200
        created = create_response.json()
        assert created["name"] == "laptop"
        assert created["price"] == 999.99
        
        # Retrieve the created item
        get_response = client.get(f"/items/{created['id']}")
        assert get_response.status_code == 200
        retrieved = get_response.json()
        
        # Verify consistency
        assert created["id"] == retrieved["id"]
        assert created["name"] == retrieved["name"]
        assert created["price"] == retrieved["price"]

    def test_api_robustness_mixed_operations(self):
        """Test API robustness with mixed valid and invalid operations."""
        # Valid health check
        assert client.get("/health").status_code == 200
        
        # Invalid create
        assert client.post("/items", json={"price": 0}).status_code == 422
        
        # Valid create
        assert client.post("/items", json={"name": "test", "price": 10.0}).status_code == 200
        
        # Invalid get
        assert client.get("/items/999").status_code == 404
        
        # Valid get
        assert client.get("/items/1").status_code == 200
        
        # Invalid create again
        assert client.post("/items", json={"name": "test", "price": -5}).status_code == 400
        
        # Health check still works
        assert client.get("/health").status_code == 200
