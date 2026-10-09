"""Path parameter edge cases and integration testing."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterBoundaries:
    """Test item_id path parameter boundary conditions."""

    @pytest.mark.parametrize(
        "item_id,exists",
        [
            (1, True),
            (0, False),
            (-1, False),
            (-100, False),
            (2, False),
            (100, False),
            (999999, False),
            (9223372036854775807, False),  # Max int64
        ],
    )
    def test_get_item_various_ids(self, item_id, exists):
        """Test get_item with various ID values."""
        response = client.get(f"/items/{item_id}")
        if exists:
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == item_id
        else:
            assert response.status_code == 404
            assert response.json()["detail"] == "not found"

    def test_get_item_id_zero_not_found(self):
        """Test that item_id=0 returns 404."""
        response = client.get("/items/0")
        assert response.status_code == 404

    def test_get_item_negative_id_not_found(self):
        """Test that negative item_ids return 404."""
        for item_id in [-1, -10, -1000]:
            response = client.get(f"/items/{item_id}")
            assert response.status_code == 404
            assert response.json()["detail"] == "not found"

    def test_get_item_large_id_not_found(self):
        """Test that large item_ids return 404."""
        for item_id in [100, 1000, 999999]:
            response = client.get(f"/items/{item_id}")
            assert response.status_code == 404


class TestGetItemPathParameterTypes:
    """Test path parameter type handling."""

    def test_get_item_id_valid_integer(self):
        """Test that valid integer IDs work."""
        response = client.get("/items/1")
        assert response.status_code == 200

    def test_get_item_id_multiple_digits(self):
        """Test multi-digit IDs."""
        response = client.get("/items/123")
        assert response.status_code == 404  # Not found but valid path param
        assert response.json()["detail"] == "not found"


class TestCreateItemIntegration:
    """Test create_item integration scenarios."""

    def test_create_multiple_items_sequential(self):
        """Test creating multiple items sequentially."""
        for i in range(3):
            response = client.post(
                "/items",
                json={"name": f"item_{i}", "price": float(i + 1)}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1  # Always returns same ID
            assert data["name"] == f"item_{i}"
            assert data["price"] == float(i + 1)

    def test_create_item_then_get_item(self):
        """Test creating and then getting the same item."""
        # Create item
        create_response = client.post(
            "/items",
            json={"name": "test_item", "price": 25.0}
        )
        assert create_response.status_code == 200
        created_id = create_response.json()["id"]

        # Get the created item (must be id=1 to exist)
        get_response = client.get(f"/items/{created_id}")
        assert get_response.status_code == 200
        assert get_response.json()["id"] == created_id

    def test_create_item_with_various_prices(self):
        """Test creating items with various valid prices."""
        prices = [0.01, 1.0, 10.5, 100.99, 9999.99]
        for price in prices:
            response = client.post(
                "/items",
                json={"name": "priced_item", "price": price}
            )
            assert response.status_code == 200
            assert response.json()["price"] == price


class TestGetItemIntegration:
    """Test get_item integration scenarios."""

    def test_get_item_multiple_times(self):
        """Test getting the same item multiple times returns same data."""
        responses = []
        for _ in range(3):
            response = client.get("/items/1")
            assert response.status_code == 200
            responses.append(response.json())

        # All responses should be identical
        for i in range(1, len(responses)):
            assert responses[i] == responses[0]

    def test_get_nonexistent_items_all_404(self):
        """Test getting various non-existent items all return 404."""
        for item_id in [2, 3, 10, 100]:
            response = client.get(f"/items/{item_id}")
            assert response.status_code == 404
            assert response.json()["detail"] == "not found"

    def test_get_item_response_consistency(self):
        """Test that item 1 always returns same response."""
        for _ in range(5):
            response = client.get("/items/1")
            data = response.json()
            assert data == {"id": 1, "name": "sample", "price": 10.0}


class TestHealthIntegration:
    """Test health endpoint integration."""

    def test_health_endpoint_multiple_calls(self):
        """Test health endpoint is consistent across calls."""
        for _ in range(3):
            response = client.get("/health")
            assert response.status_code == 200
            assert response.json() == {"status": "ok"}

    def test_health_always_ok(self):
        """Test health endpoint always returns ok status."""
        for _ in range(5):
            response = client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "ok"


class TestAPIFlows:
    """Test complete API flows."""

    def test_flow_health_create_get(self):
        """Test flow: check health -> create item -> get item."""
        # Health check
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"

        # Create item
        create = client.post(
            "/items",
            json={"name": "flow_test", "price": 50.0}
        )
        assert create.status_code == 200
        item_id = create.json()["id"]

        # Get item
        get = client.get(f"/items/{item_id}")
        assert get.status_code == 200
        assert get.json()["id"] == item_id

    def test_flow_create_invalid_then_create_valid(self):
        """Test flow: attempt invalid create -> valid create."""
        # Invalid create (price = 0)
        invalid = client.post(
            "/items",
            json={"name": "bad", "price": 0}
        )
        assert invalid.status_code == 400

        # Valid create
        valid = client.post(
            "/items",
            json={"name": "good", "price": 10.0}
        )
        assert valid.status_code == 200
        assert valid.json()["name"] == "good"

    def test_flow_create_then_query_nonexistent(self):
        """Test flow: create item -> query different ID."""
        # Create
        create = client.post(
            "/items",
            json={"name": "created", "price": 20.0}
        )
        assert create.status_code == 200
        item_id = create.json()["id"]

        # Query non-existent
        get_other = client.get(f"/items/{item_id + 1}")
        assert get_other.status_code == 404


class TestErrorRecovery:
    """Test recovery from errors."""

    def test_error_then_success_create(self):
        """Test successful create after failed create."""
        # First attempt fails
        response1 = client.post(
            "/items",
            json={"name": "test", "price": -10}
        )
        assert response1.status_code == 400

        # Second attempt succeeds
        response2 = client.post(
            "/items",
            json={"name": "test", "price": 10}
        )
        assert response2.status_code == 200

    def test_error_then_success_get(self):
        """Test successful get after failed get."""
        # First attempt fails
        response1 = client.get("/items/999")
        assert response1.status_code == 404

        # Second attempt succeeds
        response2 = client.get("/items/1")
        assert response2.status_code == 200

    def test_validation_error_then_success(self):
        """Test recovery from validation error."""
        # Validation error
        response1 = client.post(
            "/items",
            json={"name": "test"}  # Missing price
        )
        assert response1.status_code == 422

        # Success
        response2 = client.post(
            "/items",
            json={"name": "test", "price": 10.0}
        )
        assert response2.status_code == 200


class TestDataPersistence:
    """Test data persistence patterns (or lack thereof in mock)."""

    def test_item_1_always_same(self):
        """Test that item 1 returns consistent data."""
        first = client.get("/items/1").json()
        second = client.get("/items/1").json()
        assert first == second
        assert first["id"] == 1
        assert first["name"] == "sample"
        assert first["price"] == 10.0

    def test_created_item_id_always_1(self):
        """Test that all created items get id=1."""
        for _ in range(3):
            response = client.post(
                "/items",
                json={"name": "test", "price": 15.0}
            )
            assert response.json()["id"] == 1


class TestBoundaryConditions:
    """Test various boundary conditions."""

    def test_minimum_positive_price(self):
        """Test minimum positive price (0.01)."""
        response = client.post(
            "/items",
            json={"name": "cheap", "price": 0.01}
        )
        assert response.status_code == 200
        assert response.json()["price"] == 0.01

    def test_maximum_price(self):
        """Test very large price."""
        response = client.post(
            "/items",
            json={"name": "expensive", "price": 1e20}
        )
        assert response.status_code == 200

    def test_name_length_extremes(self):
        """Test name length extremes."""
        # Single character
        response1 = client.post(
            "/items",
            json={"name": "a", "price": 1.0}
        )
        assert response1.status_code == 200

        # Very long
        response2 = client.post(
            "/items",
            json={"name": "x" * 5000, "price": 1.0}
        )
        assert response2.status_code == 200

    def test_price_edge_around_zero(self):
        """Test prices at the zero boundary."""
        # Negative
        response1 = client.post(
            "/items",
            json={"name": "test", "price": -0.00001}
        )
        assert response1.status_code == 400

        # Zero
        response2 = client.post(
            "/items",
            json={"name": "test", "price": 0}
        )
        assert response2.status_code == 400

        # Just positive
        response3 = client.post(
            "/items",
            json={"name": "test", "price": 0.00001}
        )
        assert response3.status_code == 200


class TestConcurrentScenarios:
    """Test concurrent/rapid request patterns."""

    def test_rapid_health_checks(self):
        """Test rapid health checks."""
        for _ in range(10):
            response = client.get("/health")
            assert response.status_code == 200

    def test_rapid_get_requests(self):
        """Test rapid sequential get requests."""
        for _ in range(10):
            response = client.get("/items/1")
            assert response.status_code == 200
            assert response.json()["id"] == 1

    def test_rapid_create_requests(self):
        """Test rapid sequential create requests."""
        for i in range(5):
            response = client.post(
                "/items",
                json={"name": f"rapid_{i}", "price": float(i + 1)}
            )
            assert response.status_code == 200
            assert response.json()["id"] == 1

    def test_mixed_rapid_requests(self):
        """Test mixed rapid requests."""
        for i in range(5):
            # Health
            h = client.get("/health")
            assert h.status_code == 200

            # Create
            c = client.post(
                "/items",
                json={"name": f"mixed_{i}", "price": float(i + 1)}
            )
            assert c.status_code == 200

            # Get
            g = client.get("/items/1")
            assert g.status_code == 200
