"""
Test suite for path parameter edge cases and integration scenarios.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Comprehensive path parameter validation for get item endpoint."""

    @pytest.mark.parametrize("item_id,expected_status", [
        # Valid IDs
        (1, 200),              # Expected valid ID
        # Invalid IDs that should return 404
        (0, 404),              # Zero ID
        (-1, 404),             # Negative ID
        (2, 404),              # Non-existent positive ID
        (999, 404),            # Large non-existent ID
        (999999, 404),         # Very large ID
    ])
    def test_item_id_boundary_values(self, item_id, expected_status):
        """Test get item with various ID values."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == expected_status

    def test_item_id_found_returns_correct_data(self):
        """Test that valid ID returns correct item data."""
        response = client.get("/items/1")
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == 1
        assert "name" in data
        assert "price" in data

    def test_item_id_not_found_returns_error(self):
        """Test that non-existent ID returns not found error."""
        response = client.get("/items/999")
        assert response.status_code == 404
        data = response.json()
        
        assert "detail" in data
        assert "not found" in data["detail"].lower()


class TestGetItemWithVariousIDs:
    """Test get endpoint with different ID scenarios."""

    def test_get_item_boundary_low(self):
        """Test with lowest boundary ID values."""
        # Test ID 1 (should exist)
        response = client.get("/items/1")
        assert response.status_code == 200
        
        # Test ID 0 (should not exist)
        response = client.get("/items/0")
        assert response.status_code == 404

    def test_get_item_boundary_high(self):
        """Test with very high ID values."""
        test_ids = [100, 1000, 10000, 999999]
        for item_id in test_ids:
            response = client.get(f"/items/{item_id}")
            assert response.status_code == 404

    def test_get_item_negative_id(self):
        """Test that negative IDs return 404."""
        test_ids = [-1, -10, -100, -999999]
        for item_id in test_ids:
            response = client.get(f"/items/{item_id}")
            assert response.status_code == 404


class TestEndToEndIntegration:
    """Test end-to-end scenarios combining multiple operations."""

    def test_create_then_get_item(self):
        """Test creating an item and then retrieving it."""
        # Note: Current implementation always returns ID=1
        # This test validates the behavior
        
        # Create item
        create_response = client.post("/items", json={"name": "test_item", "price": 99.99})
        assert create_response.status_code == 200
        created_data = create_response.json()
        created_id = created_data["id"]
        
        # Get item by ID
        get_response = client.get(f"/items/{created_id}")
        assert get_response.status_code == 200
        retrieved_data = get_response.json()
        
        # Verify response structure
        assert retrieved_data["id"] == created_id
        assert "name" in retrieved_data
        assert "price" in retrieved_data

    def test_multiple_create_operations(self):
        """Test multiple sequential create operations."""
        for i in range(5):
            response = client.post("/items", json={
                "name": f"item_{i}",
                "price": 10.0 + i
            })
            assert response.status_code == 200
            data = response.json()
            
            # Each should have valid structure
            assert "id" in data
            assert "name" in data
            assert "price" in data

    def test_multiple_get_operations(self):
        """Test multiple sequential get operations."""
        for _ in range(5):
            response = client.get("/items/1")
            assert response.status_code == 200
            data = response.json()
            
            # All should return same structure
            assert data["id"] == 1
            assert isinstance(data["name"], str)
            assert isinstance(data["price"], (int, float))

    def test_error_recovery(self):
        """Test that API recovers gracefully from errors."""
        # Attempt invalid create
        invalid_response = client.post("/items", json={"name": "test", "price": -1})
        assert invalid_response.status_code == 400
        
        # Next valid request should still work
        valid_response = client.post("/items", json={"name": "test", "price": 9.99})
        assert valid_response.status_code == 200


class TestAPIHealthAndConsistency:
    """Test API health, consistency, and resilience."""

    def test_health_endpoint_status(self):
        """Test that health endpoint is responsive."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_health_endpoint_multiple_calls(self):
        """Test that health endpoint is consistent across multiple calls."""
        for _ in range(5):
            response = client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "ok"

    def test_api_endpoints_are_isolated(self):
        """Test that operations on one endpoint don't affect others."""
        # Get health before items operation
        health_before = client.get("/health")
        assert health_before.status_code == 200
        
        # Perform items operation
        items_response = client.post("/items", json={"name": "test", "price": 9.99})
        assert items_response.status_code == 200
        
        # Health should still work
        health_after = client.get("/health")
        assert health_after.status_code == 200
        assert health_after.json()["status"] == "ok"

    def test_sequential_operations_maintain_state(self):
        """Test that sequential operations maintain consistent state."""
        # Get item that should exist
        response1 = client.get("/items/1")
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Perform other operations
        client.post("/items", json={"name": "other", "price": 15.0})
        client.get("/health")
        
        # Get same item again
        response2 = client.get("/items/1")
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Should have same structure
        assert set(data1.keys()) == set(data2.keys())


class TestBoundaryValueCombinations:
    """Test combinations of boundary values."""

    def test_create_with_boundary_price_then_get(self):
        """Test creating items with boundary prices and retrieving."""
        boundary_prices = [0.01, 99.99, 999999.99]
        
        for price in boundary_prices:
            create_response = client.post("/items", json={
                "name": f"boundary_item",
                "price": price
            })
            assert create_response.status_code == 200
            created_data = create_response.json()
            
            # Get the created item
            get_response = client.get(f"/items/{created_data['id']}")
            assert get_response.status_code == 200

    def test_invalid_price_rejected_before_get(self):
        """Test that invalid prices are rejected before attempting to store."""
        invalid_prices = [0, -1, -999.99]
        
        for price in invalid_prices:
            response = client.post("/items", json={
                "name": "should_fail",
                "price": price
            })
            assert response.status_code == 400
            
            # API should still be functional
            health = client.get("/health")
            assert health.status_code == 200


class TestResponseValidationEdgeCases:
    """Test edge cases in response validation."""

    def test_get_nonexistent_error_message_quality(self):
        """Test that 404 error messages are helpful."""
        response = client.get("/items/9999")
        assert response.status_code == 404
        detail = response.json()["detail"]
        
        # Should be clear what went wrong
        assert isinstance(detail, str)
        assert len(detail) > 0

    def test_price_validation_error_specificity(self):
        """Test that price validation errors are specific."""
        response = client.post("/items", json={"name": "test", "price": 0})
        assert response.status_code == 400
        detail = response.json()["detail"]
        
        # Should specifically mention price
        assert "price" in detail.lower()

    def test_consecutive_invalid_then_valid_requests(self):
        """Test behavior when invalid request is followed by valid one."""
        # Invalid request
        invalid = client.post("/items", json={"name": "test", "price": -10})
        assert invalid.status_code == 400
        
        # Valid request
        valid = client.post("/items", json={"name": "test", "price": 10.0})
        assert valid.status_code == 200
        
        # Get should still work
        get_resp = client.get("/items/1")
        assert get_resp.status_code == 200
