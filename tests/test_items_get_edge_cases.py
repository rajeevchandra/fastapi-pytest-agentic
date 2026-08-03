"""
GET endpoint edge cases and integration tests.
Tests path parameter validation, boundary values, and end-to-end scenarios.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Parametrized tests for item_id path parameter validation."""
    
    @pytest.mark.parametrize("item_id,expected_status", [
        (1, 200),           # Valid item_id
        (2, 404),           # Non-existent item
        (0, 404),           # Zero is invalid
        (-1, 404),          # Negative item_id
        (999, 404),         # Large non-existent item_id
        (100000, 404),      # Very large item_id
    ])
    def test_get_item_id_boundary_values(self, item_id, expected_status):
        """Test GET /items/{item_id} with various boundary values."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == expected_status


class TestGetItemBoundaryValues:
    """Tests for boundary conditions in get_item."""
    
    def test_get_item_found_returns_valid_data(self):
        """Test item 1 is found and returns valid data."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0
    
    def test_get_item_not_found_returns_error(self):
        """Test non-existent items return 404."""
        r = client.get("/items/2")
        assert r.status_code == 404
    
    def test_get_item_zero_returns_not_found(self):
        """Test item_id=0 returns 404."""
        r = client.get("/items/0")
        assert r.status_code == 404
    
    def test_get_item_negative_returns_not_found(self):
        """Test negative item_id returns 404."""
        r = client.get("/items/-5")
        assert r.status_code == 404


class TestIntegrationScenarios:
    """End-to-end integration tests combining multiple endpoints."""
    
    def test_create_then_retrieve_item(self):
        """Test creating an item then retrieving it."""
        # Create item
        r_post = client.post("/items", json={"name": "integration-test", "price": 99.99})
        assert r_post.status_code == 200
        post_data = r_post.json()
        
        # Retrieve item
        r_get = client.get(f"/items/{post_data['id']}")
        assert r_get.status_code == 200
        get_data = r_get.json()
        
        # Verify response structure
        assert get_data["id"] == post_data["id"]
    
    def test_health_endpoint_always_works(self):
        """Test /health endpoint is always accessible."""
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}
    
    def test_multiple_requests_sequence(self):
        """Test sequence of different requests."""
        # Check health
        r1 = client.get("/health")
        assert r1.status_code == 200
        
        # Create item with valid price
        r2 = client.post("/items", json={"name": "seq1", "price": 50.0})
        assert r2.status_code == 200
        
        # Try create item with invalid price
        r3 = client.post("/items", json={"name": "seq2", "price": -10})
        assert r3.status_code == 400
        
        # Try get non-existent item
        r4 = client.get("/items/999")
        assert r4.status_code == 404
        
        # Get existing item
        r5 = client.get("/items/1")
        assert r5.status_code == 200


class TestEndToEndValidation:
    """Comprehensive end-to-end validation tests."""
    
    def test_valid_workflow(self):
        """Test complete valid workflow."""
        # Health check
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"
        
        # Create item
        item = client.post("/items", json={"name": "Complete Test", "price": 42.5})
        assert item.status_code == 200
        created_id = item.json()["id"]
        
        # Get created item
        retrieved = client.get(f"/items/{created_id}")
        assert retrieved.status_code == 200
        retrieved_data = retrieved.json()
        assert retrieved_data["id"] == created_id
    
    def test_error_cases_sequence(self):
        """Test sequence of various error cases."""
        # Invalid price (zero)
        r1 = client.post("/items", json={"name": "test", "price": 0})
        assert r1.status_code == 400
        
        # Invalid price (negative)
        r2 = client.post("/items", json={"name": "test", "price": -99})
        assert r2.status_code == 400
        
        # Missing field
        r3 = client.post("/items", json={"price": 10})
        assert r3.status_code == 422
        
        # Non-existent item
        r4 = client.get("/items/7777")
        assert r4.status_code == 404
    
    def test_mixed_operations(self):
        """Test mixed valid and invalid operations."""
        results = []
        
        # Valid create
        r = client.post("/items", json={"name": "test1", "price": 10.0})
        results.append(r.status_code == 200)
        
        # Invalid create
        r = client.post("/items", json={"name": "test2", "price": -5})
        results.append(r.status_code == 400)
        
        # Valid get
        r = client.get("/items/1")
        results.append(r.status_code == 200)
        
        # Invalid get
        r = client.get("/items/999")
        results.append(r.status_code == 404)
        
        # All operations executed
        assert all(results)
