"""Edge cases and integration tests for items endpoints.

Tests cover path parameter boundaries, multiple operations, and integration scenarios.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemIdBoundaries:
    """Tests for item_id boundary values in get_item."""

    @pytest.mark.parametrize("item_id", [2, 0, -1, -100, 3, 10, 100, 1000, 999999])
    def test_get_item_non_one_ids_not_found(self, item_id):
        """Test get_item returns 404 for all non-1 item_ids."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_id_zero_not_found(self):
        """Test get_item returns 404 for item_id=0."""
        r = client.get("/items/0")
        assert r.status_code == 404

    def test_get_item_id_negative_not_found(self):
        """Test get_item returns 404 for negative item_id."""
        r = client.get("/items/-1")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_id_large_not_found(self):
        """Test get_item returns 404 for large item_id."""
        r = client.get("/items/999999999")
        assert r.status_code == 404

    def test_get_item_id_one_found(self):
        """Test get_item returns item for item_id=1."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["id"] == 1


class TestGetItemPathParameterEdgeCases:
    """Tests for path parameter edge cases."""

    def test_get_item_with_valid_id_sequence(self):
        """Test get_item with sequence of valid IDs."""
        for item_id in [1]:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 200

    def test_get_item_with_invalid_id_sequence(self):
        """Test get_item with sequence of invalid IDs."""
        for item_id in [2, 3, 4, 5]:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404

    def test_get_item_alternating_ids(self):
        """Test get_item with alternating valid/invalid IDs."""
        r1 = client.get("/items/1")
        assert r1.status_code == 200

        r2 = client.get("/items/2")
        assert r2.status_code == 404

        r3 = client.get("/items/1")
        assert r3.status_code == 200


class TestCreateItemInputEdgeCases:
    """Tests for create_item input edge cases."""

    def test_create_item_with_minimum_price(self):
        """Test create_item with very small but valid price."""
        r = client.post("/items", json={"name": "test", "price": 0.001})
        assert r.status_code == 200
        assert r.json()["price"] == 0.001

    def test_create_item_with_maximum_price(self):
        """Test create_item with very large price."""
        r = client.post("/items", json={"name": "test", "price": 1e10})
        assert r.status_code == 200
        assert r.json()["price"] == 1e10

    def test_create_item_near_zero_boundary(self):
        """Test create_item with prices near zero boundary."""
        # Just above zero should work
        r = client.post("/items", json={"name": "test", "price": 0.0001})
        assert r.status_code == 200

        # Exactly zero should fail
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400

    def test_create_item_price_boundary_positive(self):
        """Test create_item at positive boundary."""
        r = client.post("/items", json={"name": "test", "price": 0.01})
        assert r.status_code == 200
        assert r.json()["price"] == 0.01

    def test_create_item_price_boundary_negative(self):
        """Test create_item at negative boundary."""
        r = client.post("/items", json={"name": "test", "price": -0.01})
        assert r.status_code == 400

    def test_create_item_price_scientific_notation(self):
        """Test create_item accepts scientific notation."""
        r = client.post("/items", json={"name": "test", "price": 1e5})
        assert r.status_code == 200


class TestIntegrationSequences:
    """Tests for integration scenarios with multiple operations."""

    def test_create_then_get_same_id(self):
        """Test create_item then get_item returns consistent data."""
        # Note: create_item always returns id=1, get_item for id=1 returns fixed data
        create_r = client.post("/items", json={"name": "created", "price": 25.0})
        assert create_r.status_code == 200
        created_data = create_r.json()

        get_r = client.get("/items/1")
        assert get_r.status_code == 200
        get_data = get_r.json()

        # Both should have id=1
        assert created_data["id"] == get_data["id"]

    def test_multiple_creates_then_get(self):
        """Test multiple create operations followed by get."""
        for i in range(3):
            r = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            assert r.status_code == 200
            assert r.json()["id"] == 1

        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_create_with_various_prices_then_verify(self):
        """Test create_item with various prices and verify."""
        test_cases = [
            {"name": "cheap", "price": 1.0},
            {"name": "medium", "price": 10.0},
            {"name": "expensive", "price": 100.0},
        ]

        for case in test_cases:
            r = client.post("/items", json=case)
            assert r.status_code == 200
            data = r.json()
            assert data["name"] == case["name"]
            assert data["price"] == case["price"]

    def test_get_nonexistent_then_get_existing(self):
        """Test get_item for non-existent followed by existing."""
        r1 = client.get("/items/2")
        assert r1.status_code == 404

        r2 = client.get("/items/1")
        assert r2.status_code == 200

    def test_error_recovery_scenario(self):
        """Test recovery from error conditions."""
        # Try to create with invalid price
        r1 = client.post("/items", json={"name": "bad", "price": -1})
        assert r1.status_code == 400

        # Should still be able to create valid item
        r2 = client.post("/items", json={"name": "good", "price": 10.0})
        assert r2.status_code == 200

        # Should still be able to get
        r3 = client.get("/items/1")
        assert r3.status_code == 200


class TestHealthEndpointIntegration:
    """Tests for health endpoint in integration scenarios."""

    def test_health_check_before_operations(self):
        """Test health check before API operations."""
        r1 = client.get("/health")
        assert r1.status_code == 200
        assert r1.json()["status"] == "ok"

        r2 = client.post("/items", json={"name": "test", "price": 10.0})
        assert r2.status_code == 200

    def test_health_check_after_operations(self):
        """Test health check after API operations."""
        r1 = client.post("/items", json={"name": "test", "price": 10.0})
        assert r1.status_code == 200

        r2 = client.get("/health")
        assert r2.status_code == 200
        assert r2.json()["status"] == "ok"

    def test_health_check_after_errors(self):
        """Test health check remains OK after errors."""
        r1 = client.post("/items", json={"name": "test", "price": -1})
        assert r1.status_code == 400

        r2 = client.get("/health")
        assert r2.status_code == 200
        assert r2.json()["status"] == "ok"

    def test_health_multiple_checks(self):
        """Test multiple health checks."""
        for _ in range(5):
            r = client.get("/health")
            assert r.status_code == 200
            assert r.json()["status"] == "ok"


class TestErrorHandlingPatterns:
    """Tests for error handling patterns and recovery."""

    def test_create_error_doesnt_affect_get(self):
        """Test that create errors don't affect get operations."""
        # Try bad create
        r1 = client.post("/items", json={"name": "test", "price": 0})
        assert r1.status_code == 400

        # Get should still work
        r2 = client.get("/items/1")
        assert r2.status_code == 200

    def test_get_error_doesnt_affect_create(self):
        """Test that get errors don't affect create operations."""
        # Try bad get
        r1 = client.get("/items/999")
        assert r1.status_code == 404

        # Create should still work
        r2 = client.post("/items", json={"name": "test", "price": 10.0})
        assert r2.status_code == 200

    def test_multiple_errors_in_sequence(self):
        """Test multiple errors in sequence don't break API."""
        error_count = 0
        success_count = 0

        for i in range(10):
            if i % 2 == 0:
                # Try to create with negative price
                r = client.post("/items", json={"name": "test", "price": -1})
                if r.status_code == 400:
                    error_count += 1
            else:
                # Try to get non-existent item
                r = client.get(f"/items/{i+10}")
                if r.status_code == 404:
                    error_count += 1
            
            # Verify API still responsive
            r = client.get("/health")
            if r.status_code == 200:
                success_count += 1

        assert error_count >= 5
        assert success_count == 10


class TestDataValidationBoundaries:
    """Tests for data validation at various boundaries."""

    @pytest.mark.parametrize(
        "price,should_succeed",
        [
            (0.001, True),
            (0.01, True),
            (1.0, True),
            (100.0, True),
            (0, False),
            (-0.001, False),
            (-1.0, False),
        ],
    )
    def test_price_validation_boundaries(self, price, should_succeed):
        """Test price validation at various boundaries."""
        r = client.post("/items", json={"name": "test", "price": price})
        if should_succeed:
            assert r.status_code == 200
        else:
            assert r.status_code == 400

    @pytest.mark.parametrize("item_id", [1, 2, 0, -1, 100, 999999])
    def test_get_item_id_validation(self, item_id):
        """Test get_item_id validation."""
        r = client.get(f"/items/{item_id}")
        if item_id == 1:
            assert r.status_code == 200
        else:
            assert r.status_code == 404


class TestConcurrentScenarios:
    """Tests for scenarios simulating concurrent-like behavior."""

    def test_rapid_sequential_creates(self):
        """Test rapid sequential create operations."""
        results = []
        for i in range(10):
            r = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            results.append(r.status_code)

        # All should succeed
        assert all(code == 200 for code in results)

    def test_rapid_sequential_gets(self):
        """Test rapid sequential get operations."""
        results = []
        for i in range(1, 11):
            r = client.get(f"/items/{i}")
            results.append((i, r.status_code))

        # Only item_id=1 should succeed
        for item_id, status in results:
            if item_id == 1:
                assert status == 200
            else:
                assert status == 404

    def test_mixed_operations_sequence(self):
        """Test mixed operations in sequence."""
        operations = [
            ("create", {"name": "test", "price": 10.0}),
            ("get", 1),
            ("create", {"name": "test2", "price": 20.0}),
            ("get", 2),
            ("get", 1),
        ]

        results = []
        for op_type, param in operations:
            if op_type == "create":
                r = client.post("/items", json=param)
            else:
                r = client.get(f"/items/{param}")
            results.append((op_type, r.status_code))

        # Verify expected outcomes
        assert results[0][1] == 200  # create succeeds
        assert results[1][1] == 200  # get 1 succeeds
        assert results[2][1] == 200  # create succeeds
        assert results[3][1] == 404  # get 2 fails
        assert results[4][1] == 200  # get 1 succeeds


class TestResponseConsistencyOverTime:
    """Tests for response consistency across multiple operations."""

    def test_get_item_1_consistent(self):
        """Test get_item(1) returns consistent data."""
        responses = []
        for _ in range(5):
            r = client.get("/items/1")
            responses.append(r.json())

        # All responses should be identical
        first = responses[0]
        for response in responses[1:]:
            assert response == first

    def test_health_status_consistent(self):
        """Test health endpoint returns consistent status."""
        statuses = []
        for _ in range(5):
            r = client.get("/health")
            statuses.append(r.json()["status"])

        # All should be "ok"
        assert all(status == "ok" for status in statuses)

    def test_error_message_consistency(self):
        """Test error messages are consistent."""
        messages = []
        for _ in range(3):
            r = client.post("/items", json={"name": "test", "price": 0})
            messages.append(r.json()["detail"])

        # All should be same message
        assert all(msg == messages[0] for msg in messages)
