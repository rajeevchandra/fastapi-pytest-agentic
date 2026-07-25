"""
Path parameter edge cases and integration tests.
Tests item_id boundary values and end-to-end scenarios.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test various item_id path parameter values."""

    @pytest.mark.parametrize("item_id,should_succeed", [
        (1, True),
        (0, False),
        (-1, False),
        (2, False),
        (999, False),
        (2147483647, False),  # MAX_INT
    ])
    def test_item_id_boundaries(self, item_id, should_succeed):
        """Test item_id boundary conditions."""
        response = client.get(f"/items/{item_id}")
        if should_succeed:
            assert response.status_code == 200
        else:
            assert response.status_code == 404


class TestGetItemEdgeCases:
    """Test edge cases for get_item endpoint."""

    def test_get_nonexistent_item(self):
        """Test getting non-existent item."""
        response = client.get("/items/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "not found"

    def test_get_zero_id(self):
        """Test getting item with id 0."""
        response = client.get("/items/0")
        assert response.status_code == 404

    def test_get_negative_id(self):
        """Test getting item with negative id."""
        response = client.get("/items/-1")
        assert response.status_code == 404

    def test_get_large_id(self):
        """Test getting item with very large id."""
        response = client.get("/items/999999999")
        assert response.status_code == 404

    def test_get_valid_item_response_complete(self):
        """Test that valid item response is complete."""
        response = client.get("/items/1")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0


class TestIntegrationScenarios:
    """Test end-to-end integration scenarios."""

    def test_create_then_get_item(self):
        """Test creating an item, then getting it."""
        # Create item
        create_response = client.post("/items", json={"name": "integration", "price": 25.0})
        assert create_response.status_code == 200
        created_data = create_response.json()
        assert created_data["id"] == 1
        
        # Get the created item
        get_response = client.get("/items/1")
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["id"] == 1

    def test_create_invalid_then_get_valid(self):
        """Test creating invalid item doesn't affect getting valid items."""
        # Try to create invalid item
        invalid_response = client.post("/items", json={"name": "test", "price": -10})
        assert invalid_response.status_code == 400
        
        # Should still be able to get the valid item
        get_response = client.get("/items/1")
        assert get_response.status_code == 200

    def test_get_invalid_then_get_valid(self):
        """Test getting invalid item doesn't affect subsequent valid requests."""
        # Try to get invalid item
        invalid_response = client.get("/items/999")
        assert invalid_response.status_code == 404
        
        # Should still be able to get valid item
        valid_response = client.get("/items/1")
        assert valid_response.status_code == 200

    def test_multiple_creates(self):
        """Test multiple item creations."""
        for i in range(5):
            response = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            assert response.status_code == 200
            assert response.json()["id"] == 1

    def test_error_recovery(self):
        """Test that system recovers after errors."""
        # Create error
        error_response = client.post("/items", json={"name": "test", "price": 0})
        assert error_response.status_code == 400
        
        # System should still work
        success_response = client.post("/items", json={"name": "success", "price": 10.0})
        assert success_response.status_code == 200


class TestBoundaryValueCombinations:
    """Test combinations of boundary conditions."""

    def test_create_with_boundary_price_get_with_valid_id(self):
        """Test valid boundary price with valid item ID retrieval."""
        # Create with boundary price
        create_response = client.post("/items", json={"name": "boundary", "price": 0.01})
        assert create_response.status_code == 200
        
        # Get with valid ID
        get_response = client.get("/items/1")
        assert get_response.status_code == 200

    def test_create_with_max_price_get_valid(self):
        """Test max price creation with valid retrieval."""
        create_response = client.post("/items", json={"name": "expensive", "price": 999999.99})
        assert create_response.status_code == 200
        
        get_response = client.get("/items/1")
        assert get_response.status_code == 200

    def test_get_boundary_ids(self):
        """Test multiple boundary ID scenarios."""
        test_ids = [0, -1, 1, 2, 999999]
        responses = []
        for test_id in test_ids:
            response = client.get(f"/items/{test_id}")
            responses.append(response.status_code)
        
        # Only id=1 should succeed
        assert responses == [404, 404, 200, 404, 404]


class TestSequentialAccess:
    """Test sequential access patterns."""

    def test_repeated_get_same_item(self):
        """Test repeated retrieval of same item."""
        for _ in range(3):
            response = client.get("/items/1")
            assert response.status_code == 200
            assert response.json()["id"] == 1

    def test_repeated_failed_then_success(self):
        """Test pattern of failed then successful requests."""
        # Failed attempts
        for attempt in range(3):
            response = client.get(f"/items/{attempt + 2}")
            assert response.status_code == 404
        
        # Successful attempt
        response = client.get("/items/1")
        assert response.status_code == 200

    def test_alternating_create_and_get(self):
        """Test alternating between create and get operations."""
        for i in range(3):
            # Create
            create_response = client.post("/items", json={"name": f"item{i}", "price": 10.0})
            assert create_response.status_code == 200
            
            # Get
            get_response = client.get("/items/1")
            assert get_response.status_code == 200


class TestErrorHandling:
    """Test proper error handling in various scenarios."""

    def test_create_then_error_then_create(self):
        """Test pattern of successful create, error, then another create."""
        # First create
        r1 = client.post("/items", json={"name": "first", "price": 10.0})
        assert r1.status_code == 200
        
        # Error
        r2 = client.post("/items", json={"name": "bad", "price": -5})
        assert r2.status_code == 400
        
        # Second create
        r3 = client.post("/items", json={"name": "second", "price": 20.0})
        assert r3.status_code == 200

    def test_get_error_consistency(self):
        """Test that 404 errors are consistent."""
        for test_id in [2, 3, 100, 999]:
            response = client.get(f"/items/{test_id}")
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()
