"""Path parameter and integration edge case testing."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test path parameter validation for get_item endpoint."""

    @pytest.mark.parametrize("item_id,expected_status", [
        (1, 200),              # valid item id
        (0, 404),              # zero - not found
        (-1, 404),             # negative - not found
        (2, 404),              # non-existent item
        (999, 404),            # large id - not found
        (999999, 404),         # very large id - not found
    ])
    def test_get_item_boundary_ids(self, item_id, expected_status):
        """Test get_item with various ID values."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == expected_status


class TestGetItemEdgeCases:
    """Test edge cases for get_item endpoint."""

    def test_get_item_id_type_integer(self):
        """Test that item_id is properly interpreted as integer."""
        response = client.get("/items/1")
        assert response.status_code == 200

    def test_get_item_returns_same_item(self):
        """Test that querying existing item returns consistent data."""
        response1 = client.get("/items/1")
        response2 = client.get("/items/1")
        
        assert response1.json() == response2.json()

    def test_get_item_not_found_has_detail(self):
        """Test that 404 response includes detail message."""
        response = client.get("/items/2")
        assert response.status_code == 404
        assert response.json()["detail"] == "not found"


class TestHealthCheckEndpoint:
    """Test health check endpoint."""

    def test_health_check_success(self):
        """Test health check endpoint returns ok status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_health_check_response_structure(self):
        """Test health check response structure."""
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert isinstance(data["status"], str)


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple endpoints."""

    def test_create_and_get_same_item(self):
        """Test creating an item and then retrieving it."""
        # Create item
        create_response = client.post(
            "/items",
            json={"name": "integration test", "price": 20.0}
        )
        assert create_response.status_code == 200
        created_item = create_response.json()
        
        # Retrieve the created item
        get_response = client.get(f"/items/{created_item['id']}")
        assert get_response.status_code == 200
        retrieved_item = get_response.json()
        
        # Both should have same id
        assert created_item["id"] == retrieved_item["id"]

    def test_multiple_get_requests(self):
        """Test multiple GET requests in sequence."""
        responses = []
        for _ in range(3):
            response = client.get("/items/1")
            responses.append(response)
        
        # All should succeed
        assert all(r.status_code == 200 for r in responses)
        # All should return same data
        assert all(r.json() == responses[0].json() for r in responses)

    def test_mixed_valid_invalid_requests(self):
        """Test sequence of valid and invalid requests."""
        # Valid request
        response1 = client.get("/items/1")
        assert response1.status_code == 200
        
        # Invalid request
        response2 = client.get("/items/999")
        assert response2.status_code == 404
        
        # Valid request again
        response3 = client.get("/items/1")
        assert response3.status_code == 200
        
        # Response 1 and 3 should be identical
        assert response1.json() == response3.json()


class TestErrorConditions:
    """Test various error conditions."""

    def test_negative_price_error(self):
        """Test that negative prices are rejected."""
        response = client.post(
            "/items",
            json={"name": "negative", "price": -5.0}
        )
        assert response.status_code == 400
        assert "price" in response.json()["detail"].lower()

    def test_zero_price_error(self):
        """Test that zero price is rejected."""
        response = client.post(
            "/items",
            json={"name": "free", "price": 0}
        )
        assert response.status_code == 400

    def test_missing_required_field_name(self):
        """Test that missing name field causes validation error."""
        response = client.post(
            "/items",
            json={"price": 10.0}
        )
        assert response.status_code == 422

    def test_missing_required_field_price(self):
        """Test that missing price field causes validation error."""
        response = client.post(
            "/items",
            json={"name": "test"}
        )
        assert response.status_code == 422


class TestConcurrentOperations:
    """Test handling of sequential/concurrent-like operations."""

    def test_multiple_creates_sequential(self):
        """Test creating multiple items in sequence."""
        items = []
        for i in range(3):
            response = client.post(
                "/items",
                json={"name": f"item_{i}", "price": 10.0 + i}
            )
            assert response.status_code == 200
            items.append(response.json())
        
        # All should have ids
        assert all("id" in item for item in items)

    def test_create_then_validate_error(self):
        """Test creating valid item followed by invalid attempt."""
        # Valid creation
        response1 = client.post(
            "/items",
            json={"name": "valid", "price": 10.0}
        )
        assert response1.status_code == 200
        
        # Invalid creation
        response2 = client.post(
            "/items",
            json={"name": "invalid", "price": -1}
        )
        assert response2.status_code == 400
