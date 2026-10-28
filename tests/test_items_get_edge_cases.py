"""
Edge case and integration tests for API endpoints.

Tests cover:
- Path parameter boundary values (negative, zero, large)
- Integration patterns between endpoints
- Combined endpoint behaviors
- Stress testing with various input combinations
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathIdBoundaries:
    """Test GET /items/{item_id} with boundary value item_ids."""

    def test_get_item_id_zero(self):
        """Should return 404 for item_id=0."""
        r = client.get("/items/0")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_id_negative_one(self):
        """Should return 404 for item_id=-1."""
        r = client.get("/items/-1")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_id_very_large(self):
        """Should return 404 for very large item_id."""
        r = client.get("/items/999999999")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_id_max_int(self):
        """Should handle maximum integer value."""
        r = client.get("/items/2147483647")
        assert r.status_code == 404

    def test_get_item_id_one_specific(self):
        """Item_id=1 should return success."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_get_item_id_one_plus_one(self):
        """Item_id=2 (one above valid) should 404."""
        r = client.get("/items/2")
        assert r.status_code == 404

    def test_get_item_id_negative_large(self):
        """Should handle large negative item_id."""
        r = client.get("/items/-999999")
        assert r.status_code == 404


class TestCreateItemPriceBoundaryIntegration:
    """Test create_item with boundary prices in various contexts."""

    def test_create_item_boundary_just_above_zero(self):
        """Smallest positive price should succeed."""
        r = client.post("/items", json={"name": "minimal", "price": 0.0001})
        assert r.status_code == 200

    def test_create_item_boundary_exactly_zero_fails(self):
        """Price exactly 0 should fail."""
        r = client.post("/items", json={"name": "zero", "price": 0})
        assert r.status_code == 400

    def test_create_item_boundary_just_below_zero(self):
        """Negative price just below zero should fail."""
        r = client.post("/items", json={"name": "negative", "price": -0.0001})
        assert r.status_code == 400

    def test_create_item_extreme_price_low_boundary(self):
        """Extreme low boundary (very small positive)."""
        r = client.post("/items", json={"name": "tiny", "price": 1e-10})
        assert r.status_code == 200
        assert r.json()["price"] == 1e-10

    def test_create_item_extreme_price_high_boundary(self):
        """Extreme high boundary (very large)."""
        r = client.post("/items", json={"name": "expensive", "price": 1e15})
        assert r.status_code == 200
        assert r.json()["price"] == 1e15


class TestCreateItemNameBoundaryIntegration:
    """Test create_item with boundary name values."""

    def test_create_item_name_single_char(self):
        """Single character name should work."""
        r = client.post("/items", json={"name": "A", "price": 1.0})
        assert r.status_code == 200
        assert r.json()["name"] == "A"

    def test_create_item_name_very_long(self):
        """Very long name should be accepted."""
        long_name = "x" * 1000
        r = client.post("/items", json={"name": long_name, "price": 1.0})
        assert r.status_code == 200
        assert r.json()["name"] == long_name
        assert len(r.json()["name"]) == 1000

    def test_create_item_name_whitespace_only(self):
        """Name with only whitespace might be accepted by model."""
        r = client.post("/items", json={"name": "   ", "price": 1.0})
        # Pydantic doesn't validate whitespace-only strings by default
        assert r.status_code == 200
        assert r.json()["name"] == "   "

    def test_create_item_name_special_characters(self):
        """Name with special characters should work."""
        special_name = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        r = client.post("/items", json={"name": special_name, "price": 1.0})
        assert r.status_code == 200
        assert r.json()["name"] == special_name

    def test_create_item_name_newlines(self):
        """Name with newlines should be accepted."""
        multiline_name = "line1\nline2\nline3"
        r = client.post("/items", json={"name": multiline_name, "price": 1.0})
        assert r.status_code == 200
        assert r.json()["name"] == multiline_name


class TestIntegrationCreateThenGet:
    """Test integration of create and get operations."""

    def test_create_then_get_same_item(self):
        """Create an item, then retrieve it (always returns id=1)."""
        # Create with specific values
        create_r = client.post("/items", json={"name": "created_item", "price": 25.5})
        assert create_r.status_code == 200
        created_data = create_r.json()
        
        # Get the created item (id=1)
        get_r = client.get(f"/items/{created_data['id']}")
        assert get_r.status_code == 200
        retrieved_data = get_r.json()
        
        # Due to hardcoded implementation, get returns fixed data
        assert retrieved_data["id"] == 1
        assert retrieved_data["name"] == "sample"
        assert retrieved_data["price"] == 10.0

    def test_multiple_creates_sequential(self):
        """Multiple creates should all return consistent structure."""
        test_items = [
            {"name": "item1", "price": 10.0},
            {"name": "item2", "price": 20.0},
            {"name": "item3", "price": 30.0},
        ]
        
        for item_data in test_items:
            r = client.post("/items", json=item_data)
            assert r.status_code == 200
            data = r.json()
            assert data["id"] == 1  # Always 1
            assert data["name"] == item_data["name"]
            assert data["price"] == item_data["price"]

    def test_create_get_error_get(self):
        """Sequence: create success, get success, get error."""
        # Create
        create_r = client.post("/items", json={"name": "test", "price": 5.0})
        assert create_r.status_code == 200
        
        # Get valid
        get_r = client.get("/items/1")
        assert get_r.status_code == 200
        
        # Get invalid
        get_r_err = client.get("/items/2")
        assert get_r_err.status_code == 404


class TestEndpointInteractions:
    """Test interactions and dependencies between endpoints."""

    def test_health_before_operations(self):
        """Health check should work before any operations."""
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_health_between_operations(self):
        """Health check should work between create and get."""
        client.post("/items", json={"name": "test", "price": 1.0})
        
        r = client.get("/health")
        assert r.status_code == 200
        
        client.get("/items/1")

    def test_health_after_operations(self):
        """Health check should work after failed operations."""
        client.post("/items", json={"name": "bad", "price": -1})  # Error
        client.get("/items/999")  # Error
        
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_operations_dont_affect_health(self):
        """Operations should not affect health endpoint."""
        health_before = client.get("/health").json()
        
        # Various operations
        client.post("/items", json={"name": "test", "price": 10.0})
        client.get("/items/1")
        client.post("/items", json={"name": "bad", "price": 0})
        client.get("/items/999")
        
        health_after = client.get("/health").json()
        
        assert health_before == health_after


class TestConcurrentOperations:
    """Test behavior with rapid sequential operations."""

    def test_rapid_creates(self):
        """Multiple creates in quick succession."""
        for i in range(10):
            r = client.post("/items", json={"name": f"item_{i}", "price": float(i+1)})
            assert r.status_code == 200
            assert r.json()["id"] == 1

    def test_rapid_gets_valid(self):
        """Multiple gets for valid id."""
        for _ in range(10):
            r = client.get("/items/1")
            assert r.status_code == 200
            assert r.json()["id"] == 1

    def test_rapid_gets_invalid(self):
        """Multiple gets for invalid ids."""
        for item_id in range(2, 12):
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404

    def test_alternating_success_failure(self):
        """Alternating successful and failed operations."""
        for i in range(5):
            # Success
            r = client.post("/items", json={"name": f"ok_{i}", "price": 1.0})
            assert r.status_code == 200
            
            # Failure
            r = client.post("/items", json={"name": f"bad_{i}", "price": -1.0})
            assert r.status_code == 400


class TestErrorRecovery:
    """Test that errors don't break subsequent operations."""

    def test_create_error_then_success(self):
        """Failed create should not prevent successful create."""
        # Failed create
        r1 = client.post("/items", json={"name": "bad", "price": -10})
        assert r1.status_code == 400
        
        # Successful create
        r2 = client.post("/items", json={"name": "good", "price": 10})
        assert r2.status_code == 200

    def test_get_error_then_success(self):
        """Failed get should not prevent successful get."""
        # Failed get
        r1 = client.get("/items/999")
        assert r1.status_code == 404
        
        # Successful get
        r2 = client.get("/items/1")
        assert r2.status_code == 200

    def test_validation_error_then_success(self):
        """Validation error should not prevent next request."""
        # Validation error (missing field)
        r1 = client.post("/items", json={"name": "only_name"})
        assert r1.status_code == 422
        
        # Successful request
        r2 = client.post("/items", json={"name": "complete", "price": 5.0})
        assert r2.status_code == 200


class TestResponseDataIntegrity:
    """Test that response data maintains integrity across operations."""

    def test_get_item_always_same_data(self):
        """GET /items/1 should always return same data."""
        first_response = client.get("/items/1").json()
        
        # Do various other operations
        client.post("/items", json={"name": "changed", "price": 999.0})
        client.post("/items", json={"name": "bad", "price": -1})
        
        second_response = client.get("/items/1").json()
        
        assert first_response == second_response
        assert first_response["name"] == "sample"
        assert first_response["price"] == 10.0

    def test_create_response_matches_request(self):
        """Create response should echo request data (except id)."""
        payload = {"name": "echo_test", "price": 33.33}
        response = client.post("/items", json=payload).json()
        
        assert response["name"] == payload["name"]
        assert response["price"] == payload["price"]
        assert "id" in response  # But id is added
