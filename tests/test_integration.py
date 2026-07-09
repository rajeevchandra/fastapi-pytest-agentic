"""Integration and response validation tests."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestIntegrationScenarios:
    """Test complete end-to-end scenarios."""

    def test_create_and_retrieve_workflow(self):
        """Test creating and then retrieving an item."""
        # Create item
        create_r = client.post("/items", json={"name": "workflow_test", "price": 25.5})
        assert create_r.status_code == 200
        created_item = create_r.json()

        # Retrieve item
        get_r = client.get(f"/items/{created_item['id']}")
        # Note: The implementation always returns id=1, so this tests that behavior
        assert get_r.status_code == 200
        retrieved_item = get_r.json()

        # Verify id matches
        assert retrieved_item["id"] == created_item["id"] == 1

    def test_multiple_create_requests_same_id(self):
        """Test that multiple creates still return same ID (API behavior)."""
        r1 = client.post("/items", json={"name": "item1", "price": 10.0})
        r2 = client.post("/items", json={"name": "item2", "price": 20.0})

        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r1.json()["id"] == r2.json()["id"] == 1

    def test_health_check_always_ok(self):
        """Test that health check always returns ok."""
        for _ in range(3):
            r = client.get("/health")
            assert r.status_code == 200
            assert r.json() == {"status": "ok"}

    def test_workflow_with_health_checks(self):
        """Test workflow interspersed with health checks."""
        # Health check
        r = client.get("/health")
        assert r.status_code == 200

        # Create item
        r = client.post("/items", json={"name": "test", "price": 15.0})
        assert r.status_code == 200

        # Health check
        r = client.get("/health")
        assert r.status_code == 200

        # Get item
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_invalid_then_valid_request_sequence(self):
        """Test recovery after invalid request."""
        # Invalid request
        invalid_r = client.post("/items", json={"name": "test", "price": -5})
        assert invalid_r.status_code == 400

        # Valid request after invalid
        valid_r = client.post("/items", json={"name": "test", "price": 10.0})
        assert valid_r.status_code == 200

    def test_404_then_valid_request_sequence(self):
        """Test recovery after 404."""
        # 404 request
        r404 = client.get("/items/999")
        assert r404.status_code == 404

        # Valid request after 404
        valid_r = client.get("/items/1")
        assert valid_r.status_code == 200


class TestResponseHeaderValidation:
    """Test response headers."""

    def test_response_has_content_type_header(self):
        """Test that all responses have content-type header."""
        endpoints = [
            ("/health", "GET"),
            ("/items/1", "GET"),
            ("/items", "POST"),
        ]

        for endpoint, method in endpoints[:-1]:
            r = client.request(method, endpoint)
            assert "content-type" in r.headers

        # POST request
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert "content-type" in r.headers

    def test_response_content_type_is_json(self):
        """Test that successful responses are JSON."""
        r = client.get("/health")
        assert "application/json" in r.headers.get("content-type", "")

        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert "application/json" in r.headers.get("content-type", "")

        r = client.get("/items/1")
        assert "application/json" in r.headers.get("content-type", "")

    def test_error_response_content_type_is_json(self):
        """Test that error responses are JSON."""
        r = client.post("/items", json={"name": "test", "price": -1})
        assert "application/json" in r.headers.get("content-type", "")

        r = client.get("/items/999")
        assert "application/json" in r.headers.get("content-type", "")


class TestParametrizedIntegration:
    """Parametrized integration tests for comprehensive coverage."""

    @pytest.mark.parametrize("price", [1.0, 5.5, 100.0, 0.01])
    def test_create_with_various_prices_and_retrieve(self, price):
        """Test create and retrieve with various prices."""
        create_r = client.post("/items", json={"name": "test", "price": price})
        assert create_r.status_code == 200
        assert create_r.json()["price"] == price

        get_r = client.get("/items/1")
        assert get_r.status_code == 200

    @pytest.mark.parametrize("invalid_price", [-1, 0, -100.5, -0.01])
    def test_create_with_invalid_prices_fails(self, invalid_price):
        """Test that invalid prices fail validation."""
        r = client.post("/items", json={"name": "test", "price": invalid_price})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]

    @pytest.mark.parametrize("item_id", [1, 2, 3, 10, 100, 999])
    def test_get_various_ids(self, item_id):
        """Test GET with various IDs."""
        r = client.get(f"/items/{item_id}")
        if item_id == 1:
            assert r.status_code == 200
        else:
            assert r.status_code == 404


class TestStatusCodes:
    """Test HTTP status codes."""

    def test_health_returns_200(self):
        """Test that health endpoint returns 200."""
        r = client.get("/health")
        assert r.status_code == 200

    def test_create_success_returns_200(self):
        """Test that successful create returns 200."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200

    def test_create_invalid_price_returns_400(self):
        """Test that invalid price returns 400."""
        r = client.post("/items", json={"name": "test", "price": -1})
        assert r.status_code == 400

    def test_create_missing_field_returns_422(self):
        """Test that missing required field returns 422."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422

    def test_get_found_returns_200(self):
        """Test that found item returns 200."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_get_not_found_returns_404(self):
        """Test that not found item returns 404."""
        r = client.get("/items/999")
        assert r.status_code == 404

    def test_get_invalid_type_may_return_422(self):
        """Test that invalid path parameter type returns 422."""
        # This depends on FastAPI's path parameter validation
        r = client.get("/items/abc")
        assert r.status_code in [422, 404]


class TestCompleteResponseStructure:
    """Test complete response structures."""

    def test_health_response_complete_structure(self):
        """Test health response complete structure."""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data["status"] == "ok"

    def test_create_response_complete_structure(self):
        """Test create response complete structure."""
        r = client.post("/items", json={"name": "book", "price": 12.99})
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 3
        assert data["id"] == 1
        assert data["name"] == "book"
        assert data["price"] == 12.99

    def test_get_response_complete_structure(self):
        """Test get response complete structure."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 3
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0

    def test_error_response_structure(self):
        """Test error response structure."""
        r = client.post("/items", json={"name": "bad", "price": -5})
        assert r.status_code == 400
        data = r.json()
        assert "detail" in data


class TestStressScenarios:
    """Test stress scenarios and boundary conditions."""

    def test_rapid_consecutive_requests(self):
        """Test rapid consecutive requests."""
        for _ in range(10):
            r = client.get("/health")
            assert r.status_code == 200

    def test_mixed_rapid_requests(self):
        """Test mixed rapid requests."""
        for i in range(5):
            r1 = client.get("/health")
            assert r1.status_code == 200

            r2 = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            assert r2.status_code == 200

            r3 = client.get("/items/1")
            assert r3.status_code == 200

    def test_long_running_name_field(self):
        """Test very long name field."""
        long_name = "x" * 10000
        r = client.post("/items", json={"name": long_name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == long_name
