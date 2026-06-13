"""
Integration and response validation tests.
Tests end-to-end scenarios, response structure, and API interaction patterns.
"""
from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_returns_ok_status(self):
        """Test that health endpoint returns ok status."""
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_health_response_structure(self):
        """Test that health response has correct structure."""
        r = client.get("/health")
        data = r.json()
        assert isinstance(data, dict)
        assert "status" in data
        assert isinstance(data["status"], str)

    def test_health_response_content_type(self):
        """Test that health response has correct content type."""
        r = client.get("/health")
        assert "application/json" in r.headers.get("content-type", "")

    @pytest.mark.parametrize("method", ["GET", "HEAD"])
    def test_health_http_methods(self, method):
        """Test health endpoint with different HTTP methods."""
        if method == "GET":
            r = client.get("/health")
            assert r.status_code == 200
        elif method == "HEAD":
            # HEAD requests might not be supported
            r = client.head("/health")
            assert r.status_code in (200, 405)


class TestCreateItemResponseValidation:
    """Tests for /items POST response structure and validation."""

    def test_create_item_response_structure(self):
        """Test that create item response has correct structure."""
        r = client.post("/items", json={"name": "book", "price": 10})
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_create_item_response_field_types(self):
        """Test that response fields have correct types."""
        r = client.post("/items", json={"name": "book", "price": 10})
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_create_item_returns_correct_id(self):
        """Test that create item returns id of 1."""
        r = client.post("/items", json={"name": "book", "price": 10})
        assert r.json()["id"] == 1

    def test_create_item_echoes_name_and_price(self):
        """Test that create item echoes back name and price."""
        name = "test book"
        price = 25.50
        r = client.post("/items", json={"name": name, "price": price})
        data = r.json()
        assert data["name"] == name
        assert data["price"] == price

    def test_create_item_error_response_structure(self):
        """Test that error response has correct structure."""
        r = client.post("/items", json={"name": "book", "price": -1})
        assert r.status_code == 400
        data = r.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

    def test_create_item_validation_error_structure(self):
        """Test that validation error response has correct structure."""
        r = client.post("/items", json={"name": "book"})
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)


class TestIntegrationScenarios:
    """Integration tests for multi-step API interactions."""

    def test_create_and_retrieve_item(self):
        """Test creating an item and retrieving it."""
        # Create item
        create_r = client.post("/items", json={"name": "novel", "price": 15.99})
        assert create_r.status_code == 200
        created = create_r.json()
        
        # Retrieve item
        get_r = client.get(f"/items/{created['id']}")
        assert get_r.status_code == 200
        retrieved = get_r.json()
        
        # Verify fields match (note: the GET endpoint returns fixed data)
        assert retrieved["id"] == 1

    def test_health_check_then_create_item(self):
        """Test health check followed by item creation."""
        # Check health
        health_r = client.get("/health")
        assert health_r.status_code == 200
        
        # Create item
        create_r = client.post("/items", json={"name": "pen", "price": 1.5})
        assert create_r.status_code == 200

    def test_multiple_create_requests(self):
        """Test multiple create requests return consistent results."""
        results = []
        for i in range(3):
            r = client.post(
                "/items",
                json={"name": f"item{i}", "price": 10 + i}
            )
            assert r.status_code == 200
            results.append(r.json())
        
        # All should have the same ID (1) since endpoint is stateless
        for result in results:
            assert result["id"] == 1


class TestResponseTypeValidation:
    """Tests for response type validation and consistency."""

    @pytest.mark.parametrize("endpoint,method", [
        ("/health", "GET"),
        ("/items/1", "GET"),
    ])
    def test_response_content_type_json(self, endpoint, method):
        """Test that GET endpoints return JSON content type."""
        if method == "GET":
            r = client.get(endpoint)
            assert r.status_code in (200, 404)
            assert "application/json" in r.headers.get("content-type", "")

    def test_create_item_response_is_json(self):
        """Test that POST response is JSON."""
        r = client.post("/items", json={"name": "book", "price": 10})
        assert "application/json" in r.headers.get("content-type", "")

    def test_error_response_is_json(self):
        """Test that error responses are JSON."""
        r = client.post("/items", json={"name": "book", "price": -1})
        assert "application/json" in r.headers.get("content-type", "")


class TestRequestResponseCycle:
    """Tests for complete request-response cycles."""

    def test_create_with_various_prices(self):
        """Test creating items with various valid prices."""
        prices = [0.01, 1, 10, 100.50, 999.99]
        for price in prices:
            r = client.post(
                "/items",
                json={"name": "item", "price": price}
            )
            assert r.status_code == 200
            assert r.json()["price"] == price

    def test_get_various_ids_consistency(self):
        """Test getting various item IDs with consistent error handling."""
        ids_not_found = [0, 2, 3, 100, -1, 999999]
        for item_id in ids_not_found:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404
            assert r.json()["detail"] == "not found"

    def test_only_item_id_one_exists(self):
        """Test that only item ID 1 returns success."""
        # Test ID 1
        r1 = client.get("/items/1")
        assert r1.status_code == 200
        
        # Test other IDs
        for item_id in [0, 2, 3, 100]:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404


class TestParametrizedIntegration:
    """Comprehensive parametrized integration tests."""

    @pytest.mark.parametrize("name,price", [
        ("item1", 10),
        ("item2", 0.5),
        ("item3", 999.99),
        ("item with spaces", 15),
        ("item-with-dash", 20),
    ])
    def test_create_with_various_inputs(self, name, price):
        """Test creating items with various valid inputs."""
        r = client.post("/items", json={"name": name, "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name
        assert data["price"] == price
        assert data["id"] == 1

    @pytest.mark.parametrize("price", [-100, -1, -0.01, 0])
    def test_create_rejects_invalid_prices(self, price):
        """Parametrized test for rejected prices."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    @pytest.mark.parametrize("item_id", [1, 2, 3, 0, -1, 100, 999999])
    def test_get_consistency(self, item_id):
        """Parametrized test for consistent GET behavior."""
        r = client.get(f"/items/{item_id}")
        if item_id == 1:
            assert r.status_code == 200
            data = r.json()
            assert data["id"] == 1
            assert data["name"] == "sample"
            assert data["price"] == 10.0
        else:
            assert r.status_code == 404
            assert r.json()["detail"] == "not found"
