import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Parametrized tests for GET /items/{item_id} path parameter edge cases."""

    @pytest.mark.parametrize("item_id", [1])
    def test_get_item_valid_id(self, item_id):
        """Test GET /items/{item_id} with valid item_id."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 200
        assert r.json()["id"] == item_id

    @pytest.mark.parametrize("item_id", [2, 3, 5, 100, 999])
    def test_get_item_invalid_ids_not_found(self, item_id):
        """Test GET /items/{item_id} with non-existent item_ids."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    @pytest.mark.parametrize("item_id", [0, -1, -100])
    def test_get_item_negative_or_zero_ids(self, item_id):
        """Test GET /items/{item_id} with negative or zero item_ids."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    @pytest.mark.parametrize("item_id", [999999, 2147483647, 1000000000])
    def test_get_item_very_large_ids(self, item_id):
        """Test GET /items/{item_id} with very large item_ids."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404


class TestGetItemBoundaryValues:
    """Tests for GET /items/{item_id} boundary value analysis."""

    def test_get_item_boundary_zero(self):
        """Test item_id = 0 (boundary below valid range)."""
        r = client.get("/items/0")
        assert r.status_code == 404

    def test_get_item_boundary_one(self):
        """Test item_id = 1 (valid single item)."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_get_item_boundary_two(self):
        """Test item_id = 2 (boundary above valid range)."""
        r = client.get("/items/2")
        assert r.status_code == 404

    def test_get_item_boundary_negative_one(self):
        """Test item_id = -1 (negative boundary)."""
        r = client.get("/items/-1")
        assert r.status_code == 404

    def test_get_item_int_max(self):
        """Test item_id near integer max value."""
        r = client.get("/items/2147483647")
        assert r.status_code == 404

    def test_get_item_sequential_ids(self):
        """Test sequential item_id lookups."""
        for item_id in range(1, 11):
            r = client.get(f"/items/{item_id}")
            if item_id == 1:
                assert r.status_code == 200
            else:
                assert r.status_code == 404


class TestEndToEndIntegration:
    """End-to-end integration tests."""

    def test_create_then_get_item(self):
        """Test creating an item then retrieving it."""
        # Create item
        create_r = client.post("/items", json={"name": "book", "price": 15.0})
        assert create_r.status_code == 200
        created_id = create_r.json()["id"]
        
        # Get item
        get_r = client.get(f"/items/{created_id}")
        assert get_r.status_code == 200
        assert get_r.json()["id"] == created_id

    def test_health_check_always_available(self):
        """Test health endpoint is always available."""
        for _ in range(5):
            r = client.get("/health")
            assert r.status_code == 200
            assert r.json()["status"] == "ok"

    def test_error_does_not_affect_health(self):
        """Test that errors don't affect health endpoint."""
        # Trigger an error
        r = client.post("/items", json={"name": "item", "price": -1})
        assert r.status_code == 400
        
        # Health should still work
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_validation_error_does_not_affect_health(self):
        """Test that validation errors don't affect health endpoint."""
        # Trigger a validation error
        r = client.post("/items", json={"price": 10})
        assert r.status_code == 422
        
        # Health should still work
        r = client.get("/health")
        assert r.status_code == 200

    def test_sequential_mixed_operations(self):
        """Test sequence of mixed valid and invalid operations."""
        operations = [
            ("POST", "/items", {"name": "book", "price": 10.0}, 200),
            ("GET", "/items/1", None, 200),
            ("POST", "/items", {"name": "pen", "price": -1}, 400),
            ("GET", "/items/1", None, 200),
            ("GET", "/items/999", None, 404),
            ("GET", "/health", None, 200),
        ]
        
        for method, path, json_data, expected_status in operations:
            if method == "GET":
                r = client.get(path)
            elif method == "POST":
                r = client.post(path, json=json_data)
            assert r.status_code == expected_status


class TestItemResponseConsistency:
    """Tests for consistency of item data across operations."""

    def test_get_item_one_returns_sample(self):
        """Verify GET /items/1 always returns the same sample item."""
        r = client.get("/items/1")
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0

    def test_get_item_one_idempotent(self):
        """Test that GET /items/1 is idempotent."""
        responses = []
        for _ in range(3):
            r = client.get("/items/1")
            responses.append(r.json())
        
        # All responses should be identical
        assert responses[0] == responses[1] == responses[2]

    def test_health_response_consistent(self):
        """Test health response is consistent."""
        responses = []
        for _ in range(5):
            r = client.get("/health")
            responses.append(r.json())
        
        # All responses should be identical
        assert all(resp == {"status": "ok"} for resp in responses)


class TestErrorRecovery:
    """Tests for system stability after errors."""

    def test_system_recovers_after_validation_error(self):
        """Test system works correctly after validation error."""
        # Cause error
        r = client.post("/items", json={"invalid": "payload"})
        assert r.status_code == 422
        
        # System should still work
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200

    def test_system_recovers_after_business_error(self):
        """Test system works correctly after business error."""
        # Cause error
        r = client.post("/items", json={"name": "item", "price": -1})
        assert r.status_code == 400
        
        # System should still work
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200

    def test_system_recovers_after_not_found_error(self):
        """Test system works correctly after 404 error."""
        # Cause error
        r = client.get("/items/999")
        assert r.status_code == 404
        
        # System should still work
        r = client.get("/items/1")
        assert r.status_code == 200


class TestCreateItemMultipleScenarios:
    """Additional scenarios for item creation."""

    def test_create_item_with_float_price(self):
        """Test creating item with float price."""
        r = client.post("/items", json={"name": "item", "price": 9.99})
        assert r.status_code == 200
        assert r.json()["price"] == 9.99

    def test_create_item_with_integer_price(self):
        """Test creating item with integer price."""
        r = client.post("/items", json={"name": "item", "price": 10})
        assert r.status_code == 200
        assert r.json()["price"] == 10

    def test_create_multiple_items_different_prices(self):
        """Test creating multiple items with different prices."""
        prices = [1.0, 5.5, 10.99, 100.0, 999.99]
        for i, price in enumerate(prices):
            r = client.post("/items", json={"name": f"item{i}", "price": price})
            assert r.status_code == 200
            assert r.json()["price"] == price

    def test_create_item_boundary_price_0_01(self):
        """Test creating item with minimum positive price."""
        r = client.post("/items", json={"name": "item", "price": 0.01})
        assert r.status_code == 200
        assert r.json()["price"] == 0.01

    def test_create_item_large_price(self):
        """Test creating item with large price."""
        r = client.post("/items", json={"name": "item", "price": 999999.99})
        assert r.status_code == 200
        assert r.json()["price"] == 999999.99


class TestPathParameterTypes:
    """Tests for path parameter type handling."""

    def test_get_item_with_string_digits(self):
        """Test path parameter parsed as integer from string."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_get_item_string_representation_matches(self):
        """Test that string '1' in path is correctly parsed."""
        r = client.get("/items/1")
        data = r.json()
        assert data["id"] == 1
        assert isinstance(data["id"], int)

    def test_get_item_with_different_valid_numbers(self):
        """Test various numeric path values."""
        test_values = [1, 2, 3, 5, 10, 50, 100]
        
        for val in test_values:
            r = client.get(f"/items/{val}")
            # Only id=1 should return 200, others 404
            if val == 1:
                assert r.status_code == 200
            else:
                assert r.status_code == 404
