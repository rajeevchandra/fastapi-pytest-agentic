"""Edge cases and integration scenarios."""
from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test path parameter validation for GET /items/{item_id}."""

    @pytest.mark.parametrize("item_id,expected_status", [
        (1, 200),              # valid
        (2, 404),              # not found
        (999, 404),            # large not found
        (0, 404),              # zero
        (-1, 404),             # negative
    ])
    def test_get_item_various_ids(self, item_id, expected_status):
        """Test various item_id values."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == expected_status


class TestGetItemBoundaryValues:
    """Test boundary conditions for item_id parameter."""

    def test_get_item_very_large_id(self):
        """Very large item_id should return 404."""
        response = client.get("/items/999999999")
        assert response.status_code == 404

    def test_get_item_max_int(self):
        """Maximum integer value should return 404."""
        response = client.get("/items/2147483647")
        assert response.status_code == 404

    def test_get_item_only_id_1_exists(self):
        """Only item_id=1 should return 200."""
        for item_id in [1]:
            response = client.get(f"/items/{item_id}")
            assert response.status_code == 200

    def test_get_item_all_other_ids_not_found(self):
        """All other item_ids should return 404."""
        for item_id in [0, 2, 3, 10, 100, -1, -100]:
            response = client.get(f"/items/{item_id}")
            assert response.status_code == 404


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check_status(self):
        """Health endpoint should return ok status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_health_check_format(self):
        """Health response should have expected format."""
        response = client.get("/health")
        data = response.json()
        assert isinstance(data, dict)
        assert "status" in data
        assert isinstance(data["status"], str)

    def test_health_check_always_ok(self):
        """Health check should always return ok."""
        for _ in range(3):
            response = client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "ok"


class TestIntegrationScenarios:
    """Test end-to-end scenarios across endpoints."""

    def test_create_and_retrieve_item(self):
        """Test creating an item and then retrieving it."""
        create_response = client.post(
            "/items",
            json={"name": "Integration Test Item", "price": 29.99}
        )
        assert create_response.status_code == 200
        created_item = create_response.json()

        # Retrieve the item
        get_response = client.get(f"/items/{created_item['id']}")
        assert get_response.status_code == 200
        retrieved_item = get_response.json()
        assert retrieved_item["id"] == created_item["id"]

    def test_create_item_multiple_times(self):
        """Test creating multiple items returns same id (current behavior)."""
        response1 = client.post("/items", json={"name": "item1", "price": 10.0})
        response2 = client.post("/items", json={"name": "item2", "price": 20.0})

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.json()["id"] == response2.json()["id"]  # both return 1

    def test_retrieve_item_after_failed_creation(self):
        """Failed creation should not affect retrieval."""
        # Try to create with invalid price
        create_response = client.post(
            "/items",
            json={"name": "test", "price": -5}
        )
        assert create_response.status_code == 400

        # Retrieval should still work
        get_response = client.get("/items/1")
        assert get_response.status_code == 200
        assert get_response.json()["id"] == 1


class TestErrorRecovery:
    """Test API behavior after errors."""

    def test_api_recovers_after_validation_error(self):
        """API should accept valid requests after validation error."""
        # Send invalid
        bad_response = client.post("/items", json={"name": "test"})
        assert bad_response.status_code == 422

        # Send valid - should work
        good_response = client.post(
            "/items",
            json={"name": "test", "price": 10.0}
        )
        assert good_response.status_code == 200

    def test_api_recovers_after_business_error(self):
        """API should accept valid requests after business error."""
        # Send business error (negative price)
        bad_response = client.post("/items", json={"name": "test", "price": -5})
        assert bad_response.status_code == 400

        # Send valid - should work
        good_response = client.post(
            "/items",
            json={"name": "test", "price": 10.0}
        )
        assert good_response.status_code == 200


class TestResponseConsistency:
    """Test response consistency across multiple calls."""

    def test_get_item_1_consistent(self):
        """GET /items/1 should return consistent response."""
        responses = [client.get("/items/1") for _ in range(3)]
        
        assert all(r.status_code == 200 for r in responses)
        data_list = [r.json() for r in responses]
        
        # All responses should be identical
        assert all(d == data_list[0] for d in data_list)

    def test_health_endpoint_consistent(self):
        """Health endpoint should return consistent response."""
        responses = [client.get("/health") for _ in range(3)]
        
        assert all(r.status_code == 200 for r in responses)
        data_list = [r.json() for r in responses]
        
        # All responses should be identical
        assert all(d == data_list[0] for d in data_list)


class TestConcurrencySimulation:
    """Simulate concurrent operations."""

    def test_multiple_creates_in_sequence(self):
        """Multiple sequential POST requests should all succeed."""
        responses = []
        for i in range(5):
            response = client.post(
                "/items",
                json={"name": f"item_{i}", "price": 10.0 + i}
            )
            responses.append(response)

        assert all(r.status_code == 200 for r in responses)

    def test_mixed_creates_and_gets_in_sequence(self):
        """Alternating POST and GET should work correctly."""
        # POST
        post_response = client.post(
            "/items",
            json={"name": "test", "price": 10.0}
        )
        assert post_response.status_code == 200

        # GET
        get_response = client.get(f"/items/{post_response.json()['id']}")
        assert get_response.status_code == 200

        # Another POST
        post_response2 = client.post(
            "/items",
            json={"name": "test2", "price": 20.0}
        )
        assert post_response2.status_code == 200

        # Another GET
        get_response2 = client.get(f"/items/{post_response2.json()['id']}")
        assert get_response2.status_code == 200


class TestEndpointAccessibility:
    """Test that endpoints are accessible and respond correctly."""

    def test_all_endpoints_accessible(self):
        """All documented endpoints should be accessible."""
        endpoints = [
            ("/health", "get", {}),
            ("/items", "post", {"json": {"name": "test", "price": 10.0}}),
            ("/items/1", "get", {}),
        ]

        for endpoint, method, kwargs in endpoints:
            if method == "get":
                response = client.get(endpoint, **kwargs)
            elif method == "post":
                response = client.post(endpoint, **kwargs)

            # Should return 2xx or 4xx, not 5xx errors
            assert response.status_code < 500, f"Server error on {endpoint}"
