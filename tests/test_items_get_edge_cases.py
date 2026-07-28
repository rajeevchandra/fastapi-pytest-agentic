from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test path parameter validation for get item endpoint."""
    
    @pytest.mark.parametrize("item_id,should_exist", [
        (1, True),          # valid item exists
        (0, False),         # zero id doesn't exist
        (-1, False),        # negative id doesn't exist
        (2, False),         # other valid-looking id doesn't exist
        (999999, False),    # very large id doesn't exist
    ])
    def test_get_item_with_various_ids(self, item_id, should_exist):
        """Test get item with various id values."""
        response = client.get(f"/items/{item_id}")
        if should_exist:
            assert response.status_code == 200
            assert response.json()["id"] == item_id
        else:
            assert response.status_code == 404


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_status_ok(self):
        """Test health endpoint returns status ok."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    
    def test_health_response_type(self):
        """Test health endpoint response type."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "status" in data


class TestEndToEndIntegration:
    """Test end-to-end integration scenarios."""
    
    def test_create_then_get_item(self):
        """Test creating an item and then retrieving it."""
        # Create item
        create_response = client.post("/items", json={"name": "integration_test", "price": 25.0})
        assert create_response.status_code == 200
        created_id = create_response.json()["id"]
        
        # Get the created item
        get_response = client.get(f"/items/{created_id}")
        assert get_response.status_code == 200
        assert get_response.json()["id"] == created_id
    
    def test_invalid_then_valid_requests(self):
        """Test recovery from invalid request to valid request."""
        # Invalid request
        invalid_response = client.post("/items", json={"name": "test", "price": -10})
        assert invalid_response.status_code == 400
        
        # Valid request should succeed
        valid_response = client.post("/items", json={"name": "test", "price": 10})
        assert valid_response.status_code == 200
    
    def test_multiple_items_sequential_access(self):
        """Test accessing multiple items in sequence."""
        # Create multiple items
        for i in range(3):
            response = client.post("/items", json={"name": f"item_{i}", "price": 10.0 * (i + 1)})
            assert response.status_code == 200
        
        # Access item 1 multiple times
        for _ in range(3):
            response = client.get("/items/1")
            assert response.status_code == 200
            assert response.json()["id"] == 1


class TestBoundaryValuePairings:
    """Test pairings of boundary conditions."""
    
    @pytest.mark.parametrize("price,name", [
        (0.01, "a"),                          # minimal valid values
        (999999.99, "x" * 100),              # maximal values
        (0.1, ""),                           # price ok, but edge case name (if empty allowed)
        (1.0, "special!@#"),                 # normal price, special chars
        (100.0, "Café"),                     # normal price, unicode
    ])
    def test_price_name_pairings(self, price, name):
        """Test various pairings of price and name boundary values."""
        if name == "":
            # Empty name may not be valid
            response = client.post("/items", json={"name": name, "price": price})
            # Should either accept or reject, but be consistent
            assert response.status_code in [200, 422]
        else:
            response = client.post("/items", json={"name": name, "price": price})
            assert response.status_code == 200
            assert response.json()["name"] == name
            assert response.json()["price"] == price


class TestResponseConsistency:
    """Test consistency of responses across different scenarios."""
    
    def test_multiple_successful_creates_return_same_id(self):
        """Test that multiple creates return consistent structure."""
        responses = []
        for _ in range(3):
            response = client.post("/items", json={"name": "test", "price": 10.0})
            assert response.status_code == 200
            responses.append(response.json())
        
        # All responses should have same fields
        for data in responses:
            assert "id" in data
            assert "name" in data
            assert "price" in data
    
    def test_get_item_always_returns_same_structure(self):
        """Test that get endpoint always returns consistent structure."""
        for _ in range(3):
            response = client.get("/items/1")
            assert response.status_code == 200
            data = response.json()
            assert set(data.keys()) == {"id", "name", "price"}
    
    def test_error_responses_have_consistent_structure(self):
        """Test error responses have consistent detail field."""
        # Trigger different errors
        responses = [
            client.post("/items", json={"name": "test", "price": 0}),      # price error
            client.get("/items/999"),                                        # not found
            client.post("/items", json={"name": "test"}),                   # missing field
        ]
        
        for response in responses:
            assert response.status_code in [400, 404, 422]
            assert "detail" in response.json()


class TestErrorRecovery:
    """Test API behavior in error scenarios and recovery."""
    
    def test_api_works_after_validation_error(self):
        """Test API is usable after validation error."""
        # Trigger validation error
        error_response = client.post("/items", json={"name": "test", "price": "invalid"})
        assert error_response.status_code == 422
        
        # API should still work
        success_response = client.post("/items", json={"name": "test", "price": 10.0})
        assert success_response.status_code == 200
    
    def test_api_works_after_not_found_error(self):
        """Test API is usable after not found error."""
        # Trigger not found
        error_response = client.get("/items/999")
        assert error_response.status_code == 404
        
        # API should still work
        success_response = client.get("/items/1")
        assert success_response.status_code == 200
    
    def test_health_endpoint_after_errors(self):
        """Test health endpoint works after various errors."""
        # Trigger multiple errors
        client.post("/items", json={"price": 10.0})
        client.post("/items", json={"name": "test", "price": 0})
        client.get("/items/999")
        
        # Health check should still work
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
