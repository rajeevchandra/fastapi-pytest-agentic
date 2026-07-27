"""
Path parameter edge cases and integration tests.
Tests ID boundary values, sequential operations, and end-to-end scenarios.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Parametrized tests for item_id path parameter edge cases."""

    @pytest.mark.parametrize("item_id,expected_status", [
        (1, 200),      # Valid found
        (2, 404),      # Valid but not found
        (0, 404),      # Zero (edge case)
        (-1, 404),     # Negative (edge case)
        (999999, 404), # Very large ID
    ])
    def test_get_item_boundary_ids(self, item_id, expected_status):
        """Test GET endpoint with various item_id values."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == expected_status

    def test_get_item_id_not_found_message(self):
        """Test that not found returns correct error message."""
        r = client.get("/items/999")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_id_zero_returns_not_found(self):
        """Test that item_id=0 returns 404."""
        r = client.get("/items/0")
        assert r.status_code == 404

    def test_get_item_id_negative_returns_not_found(self):
        """Test that negative item_id returns 404."""
        r = client.get("/items/-1")
        assert r.status_code == 404


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_endpoint_success(self):
        """Test that health endpoint returns 200 ok."""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"

    def test_health_response_structure(self):
        """Test health endpoint response structure."""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert "status" in data
        assert isinstance(data["status"], str)


class TestEndToEndIntegration:
    """Tests for multi-step integration scenarios."""

    def test_create_then_get_item(self):
        """Test creating an item and retrieving it."""
        # Create an item
        create_r = client.post("/items", json={"name": "notebook", "price": 5.99})
        assert create_r.status_code == 200
        created_item = create_r.json()
        
        # Retrieve the created item (would only work if item_id matched)
        get_r = client.get(f"/items/{created_item['id']}")
        assert get_r.status_code == 200

    def test_failed_create_does_not_affect_retrieval(self):
        """Test that failed creation doesn't impact existing items."""
        # Try to create with invalid price
        r1 = client.post("/items", json={"name": "item", "price": 0})
        assert r1.status_code == 400
        
        # Item 1 should still be retrievable
        r2 = client.get("/items/1")
        assert r2.status_code == 200

    def test_sequential_valid_creates(self):
        """Test creating multiple items in sequence."""
        results = []
        for i in range(3):
            r = client.post("/items", json={"name": f"item_{i}", "price": float(i + 1)})
            assert r.status_code == 200
            results.append(r.json())
        
        # Verify all returned valid responses with items
        assert len(results) == 3
        for result in results:
            assert "id" in result
            assert "name" in result
            assert "price" in result

    def test_mixed_valid_invalid_operations(self):
        """Test sequence of valid and invalid operations."""
        # Valid create
        r1 = client.post("/items", json={"name": "valid", "price": 1.0})
        assert r1.status_code == 200
        
        # Invalid create
        r2 = client.post("/items", json={"name": "invalid", "price": -1})
        assert r2.status_code == 400
        
        # Valid get
        r3 = client.get("/items/1")
        assert r3.status_code == 200
        
        # Invalid get
        r4 = client.get("/items/999")
        assert r4.status_code == 404


class TestBoundaryValuePairings:
    """Tests combining boundary values across parameters."""

    def test_get_boundary_ids_after_creates(self):
        """Test getting items with boundary IDs after creating items."""
        # Create a valid item
        client.post("/items", json={"name": "item", "price": 1.0})
        
        # Test boundary IDs
        test_ids = [-1, 0, 1, 2, 999]
        for item_id in test_ids:
            r = client.get(f"/items/{item_id}")
            expected = 200 if item_id == 1 else 404
            assert r.status_code == expected

    @pytest.mark.parametrize("name,price,should_succeed", [
        ("item", 0.01, True),
        ("", 1.0, False),  # Empty name rejected by Pydantic
        ("item", 0, False),  # Zero price
        ("🎉", 5.5, True),  # Emoji name
        ("a" * 200, 1.0, True),  # Very long name
    ])
    def test_create_with_boundary_combinations(self, name, price, should_succeed):
        """Test various combinations of boundary values."""
        r = client.post("/items", json={"name": name, "price": price})
        if should_succeed:
            assert r.status_code == 200
        else:
            assert r.status_code in [400, 422]


class TestResponseConsistency:
    """Tests for consistency of responses across multiple calls."""

    def test_get_item_consistent_response(self):
        """Test that repeated GET requests return same data."""
        r1 = client.get("/items/1")
        r2 = client.get("/items/1")
        
        assert r1.status_code == r2.status_code
        assert r1.json() == r2.json()

    def test_not_found_consistent_response(self):
        """Test that repeated 404s are consistent."""
        r1 = client.get("/items/999")
        r2 = client.get("/items/999")
        
        assert r1.status_code == r2.status_code == 404
        assert r1.json() == r2.json()

    def test_health_endpoint_consistent(self):
        """Test that health endpoint consistently returns ok."""
        for _ in range(3):
            r = client.get("/health")
            assert r.status_code == 200
            assert r.json()["status"] == "ok"


class TestErrorRecovery:
    """Tests for API behavior after error conditions."""

    def test_recovery_after_validation_error(self):
        """Test that API works normally after a validation error."""
        # Trigger a validation error
        r1 = client.post("/items", json={"name": "item"})  # Missing price
        assert r1.status_code == 422
        
        # API should still work
        r2 = client.post("/items", json={"name": "recovery", "price": 1.0})
        assert r2.status_code == 200

    def test_recovery_after_business_logic_error(self):
        """Test API after a business logic error (negative price)."""
        # Trigger business logic error
        r1 = client.post("/items", json={"name": "item", "price": -1})
        assert r1.status_code == 400
        
        # API should still work
        r2 = client.post("/items", json={"name": "recovery", "price": 1.0})
        assert r2.status_code == 200

    def test_get_after_failed_creates(self):
        """Test GET after multiple failed create attempts."""
        # Multiple failed creates
        for price in [-1, 0, -100]:
            r = client.post("/items", json={"name": "item", "price": price})
            assert r.status_code == 400
        
        # GET should still work
        r = client.get("/items/1")
        assert r.status_code == 200
