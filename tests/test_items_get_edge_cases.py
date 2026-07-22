"""
Test suite for path parameter edge cases and integration scenarios.
Covers item_id boundary values, multiple operations, and end-to-end workflows.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Parametrized tests for path parameter boundary conditions."""

    @pytest.mark.parametrize(
        "item_id,expected_status",
        [
            # Valid item (only 1 exists)
            (1, 200),
            # Non-existent items
            (0, 404),
            (-1, 404),
            (-100, 404),
            (2, 404),
            (3, 404),
            (100, 404),
            (999999, 404),
            (2147483647, 404),  # MAX_INT (2^31 - 1)
        ],
    )
    def test_get_item_various_ids(self, item_id, expected_status):
        """Test GET /items/{item_id} with various ID values."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == expected_status


class TestGetItemBoundaryValues:
    """Test boundary values for item_id parameter."""

    def test_get_item_zero(self):
        """Test getting item with id=0."""
        response = client.get("/items/0")
        assert response.status_code == 404

    def test_get_item_negative_one(self):
        """Test getting item with id=-1."""
        response = client.get("/items/-1")
        assert response.status_code == 404

    def test_get_item_large_positive(self):
        """Test getting item with very large positive id."""
        response = client.get("/items/999999999")
        assert response.status_code == 404

    def test_get_item_negative_large(self):
        """Test getting item with very large negative id."""
        response = client.get("/items/-999999999")
        assert response.status_code == 404

    def test_get_item_sequential_ids(self):
        """Test that only id=1 is found, others 404."""
        for item_id in [1, 2, 3, 4, 5]:
            response = client.get(f"/items/{item_id}")
            if item_id == 1:
                assert response.status_code == 200
            else:
                assert response.status_code == 404


class TestItemCreationSequences:
    """Test multiple item operations in sequence."""

    def test_create_and_retrieve_item(self):
        """Test create item then retrieve it."""
        # Create item
        create_response = client.post(
            "/items",
            json={"name": "integration-test", "price": 25.99},
        )
        assert create_response.status_code == 200
        created = create_response.json()
        assert created["id"] == 1

        # Retrieve the created item
        get_response = client.get("/items/1")
        assert get_response.status_code == 200
        retrieved = get_response.json()
        # Retrieved item always has the sample data
        assert retrieved["id"] == 1
        assert retrieved["name"] == "sample"
        assert retrieved["price"] == 10.0

    def test_create_multiple_items(self):
        """Test creating multiple items in sequence."""
        ids = []
        for i in range(3):
            response = client.post(
                "/items",
                json={"name": f"item-{i}", "price": 10.0 + i},
            )
            assert response.status_code == 200
            # All return id=1
            ids.append(response.json()["id"])

        # All should have id=1
        assert all(id == 1 for id in ids)

    def test_create_item_then_get_wrong_id(self):
        """Test that creating item doesn't affect other GET requests."""
        # Create item
        create_response = client.post(
            "/items",
            json={"name": "test", "price": 15.0},
        )
        assert create_response.status_code == 200

        # Try to get non-existent item
        response = client.get("/items/2")
        assert response.status_code == 404

    def test_multiple_create_and_get_operations(self):
        """Test interleaved create and get operations."""
        # Create first item
        client.post("/items", json={"name": "first", "price": 10.0})

        # Get existing item
        response = client.get("/items/1")
        assert response.status_code == 200

        # Create another
        client.post("/items", json={"name": "second", "price": 20.0})

        # Get should still work
        response = client.get("/items/1")
        assert response.status_code == 200

        # Non-existent still 404
        response = client.get("/items/2")
        assert response.status_code == 404


class TestAPIEndpointIntegration:
    """Test integration of all API endpoints."""

    def test_health_check_always_works(self):
        """Test health endpoint works independently."""
        # Health should work regardless of item operations
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

        # Create item
        client.post("/items", json={"name": "test", "price": 10.0})

        # Health should still work
        response = client.get("/health")
        assert response.status_code == 200

    def test_invalid_item_creation_does_not_affect_existing(self):
        """Test that invalid creation doesn't affect subsequent operations."""
        # Try invalid creation
        response = client.post("/items", json={"name": "test", "price": 0})
        assert response.status_code == 400

        # Valid item should still work
        response = client.post("/items", json={"name": "valid", "price": 10.0})
        assert response.status_code == 200

        # Valid get should still work
        response = client.get("/items/1")
        assert response.status_code == 200

    def test_error_recovery(self):
        """Test that errors don't break subsequent operations."""
        # Invalid price
        response = client.post("/items", json={"name": "test", "price": -1})
        assert response.status_code == 400

        # Missing field
        response = client.post("/items", json={"name": "test"})
        assert response.status_code == 422

        # Valid operation should work
        response = client.post("/items", json={"name": "recovery", "price": 10.0})
        assert response.status_code == 200
        assert response.json()["name"] == "recovery"

    def test_get_404_does_not_break_subsequent_operations(self):
        """Test that 404 responses don't affect subsequent operations."""
        # Get non-existent
        response = client.get("/items/999")
        assert response.status_code == 404

        # Next operation should work
        response = client.post("/items", json={"name": "after-404", "price": 10.0})
        assert response.status_code == 200

        # Another get should work
        response = client.get("/items/1")
        assert response.status_code == 200


class TestDataIntegrity:
    """Test data integrity across operations."""

    def test_get_item_returns_consistent_data(self):
        """Test that get item returns consistent data."""
        response1 = client.get("/items/1")
        response2 = client.get("/items/1")

        assert response1.json() == response2.json()

    def test_get_item_data_unchanged_after_create(self):
        """Test that creating new items doesn't change existing item data."""
        before = client.get("/items/1").json()

        # Create new items
        client.post("/items", json={"name": "test1", "price": 10.0})
        client.post("/items", json={"name": "test2", "price": 20.0})

        after = client.get("/items/1").json()

        assert before == after

    def test_create_item_returns_requested_data(self):
        """Test that created item response contains requested values."""
        test_cases = [
            {"name": "item-a", "price": 15.5},
            {"name": "item-b", "price": 99.99},
            {"name": "item-c", "price": 0.01},
        ]

        for item in test_cases:
            response = client.post("/items", json=item)
            data = response.json()
            assert data["name"] == item["name"]
            assert data["price"] == item["price"]


class TestEdgeCaseSequences:
    """Test edge case scenarios with multiple operations."""

    def test_create_with_zero_price_then_valid(self):
        """Test invalid then valid creation."""
        # Invalid
        response = client.post("/items", json={"name": "invalid", "price": 0})
        assert response.status_code == 400

        # Valid after
        response = client.post("/items", json={"name": "valid", "price": 0.01})
        assert response.status_code == 200
        assert response.json()["price"] == 0.01

    def test_get_with_negative_then_valid_id(self):
        """Test invalid then valid get requests."""
        # Invalid
        response = client.get("/items/-1")
        assert response.status_code == 404

        # Valid after
        response = client.get("/items/1")
        assert response.status_code == 200

    def test_mixed_valid_invalid_operations(self):
        """Test alternating valid and invalid operations."""
        operations = [
            ("get", 1, 200),  # valid
            ("get", 999, 404),  # invalid
            ("create", None, 200),  # valid
            ("get", 2, 404),  # invalid
            ("create", None, 200),  # valid
            ("get", 1, 200),  # valid
        ]

        for op_type, param, expected_status in operations:
            if op_type == "get":
                response = client.get(f"/items/{param}")
            else:
                response = client.post(
                    "/items",
                    json={"name": "test", "price": 10.0},
                )
            assert response.status_code == expected_status

    def test_repeated_get_same_id(self):
        """Test repeated GET requests for same item."""
        responses = [client.get("/items/1") for _ in range(5)]
        assert all(r.status_code == 200 for r in responses)
        assert all(r.json() == responses[0].json() for r in responses)

    def test_repeated_invalid_get_same_id(self):
        """Test repeated GET requests for non-existent item."""
        responses = [client.get("/items/999") for _ in range(5)]
        assert all(r.status_code == 404 for r in responses)


class TestResponseConsistency:
    """Test response consistency across different scenarios."""

    def test_error_response_format_consistency(self):
        """Test that all error responses have consistent format."""
        error_scenarios = [
            client.post("/items", json={"name": "test", "price": 0}),
            client.post("/items", json={"name": "test"}),
            client.get("/items/999"),
        ]

        for response in error_scenarios:
            assert response.status_code in (400, 404, 422)
            data = response.json()
            assert isinstance(data, dict)
            assert "detail" in data

    def test_success_response_format_consistency(self):
        """Test that all success responses have consistent format."""
        responses = [
            client.get("/health"),
            client.post("/items", json={"name": "test", "price": 10.0}),
            client.get("/items/1"),
        ]

        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, dict)
            assert "application/json" in response.headers.get("content-type", "")
