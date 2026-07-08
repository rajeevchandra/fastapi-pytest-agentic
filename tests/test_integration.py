"""
Integration and response validation tests.
Tests end-to-end scenarios, response structure, and API interaction patterns.
"""
from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)


@pytest.fixture
def valid_item_payload():
    """Fixture providing a valid item payload."""
    return {"name": "fixture_item", "price": 25.0}


class TestResponseStructure:
    """Test response structure and content-type validation."""

    def test_create_item_response_headers(self):
        """Verify response headers for item creation."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        assert "content-type" in r.headers
        assert "application/json" in r.headers["content-type"]

    def test_get_item_response_headers(self):
        """Verify response headers for item retrieval."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert "content-type" in r.headers
        assert "application/json" in r.headers["content-type"]

    def test_health_response_structure(self):
        """Verify health endpoint response structure."""
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}

    def test_error_response_structure(self):
        """Verify error response has detail field."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.status_code == 400
        data = r.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)


class TestStatusCodes:
    """Test HTTP status codes for various scenarios."""

    def test_create_item_returns_200(self):
        """POST /items returns 200 for valid input."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200

    def test_create_item_invalid_price_returns_400(self):
        """POST /items returns 400 for invalid price."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.status_code == 400

    def test_create_item_missing_field_returns_422(self):
        """POST /items returns 422 for missing required field."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422

    def test_get_existing_item_returns_200(self):
        """GET /items/1 returns 200."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_get_nonexistent_item_returns_404(self):
        """GET /items/{other} returns 404."""
        r = client.get("/items/999")
        assert r.status_code == 404

    def test_get_invalid_item_id_returns_422(self):
        """GET /items/{invalid} returns 422."""
        r = client.get("/items/not-a-number")
        assert r.status_code == 422

    def test_health_endpoint_returns_200(self):
        """GET /health returns 200."""
        r = client.get("/health")
        assert r.status_code == 200


class TestParametrizedIntegration:
    """Parametrized integration tests for comprehensive coverage."""

    @pytest.mark.parametrize("name,price", [
        ("item1", 10.0),
        ("item2", 99.99),
        ("item3", 0.01),
        ("特殊商品", 150.0),
        ("🎉 Special Item 🎉", 5.0),
    ])
    def test_create_various_valid_items(self, name, price):
        """Test creating items with various valid names and prices."""
        r = client.post("/items", json={"name": name, "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name
        assert data["price"] == price

    @pytest.mark.parametrize("price", [0.001, 1.0, 10.5, 100.0, 999.99])
    def test_create_items_various_prices(self, price):
        """Test creating items with various positive prices."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    @pytest.mark.parametrize("name", ["a", "ab", "test item", "a" * 100])
    def test_create_items_various_name_lengths(self, name):
        """Test creating items with various name lengths."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name


class TestErrorHandling:
    """Test error handling and error messages."""

    def test_price_validation_error_detail(self):
        """Verify error detail message for price validation."""
        r = client.post("/items", json={"name": "item", "price": -5})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]

    def test_item_not_found_error_detail(self):
        """Verify error detail message for item not found."""
        r = client.get("/items/999")
        assert r.status_code == 404
        assert "not found" in r.json()["detail"]

    def test_validation_error_includes_field_info(self):
        """Verify validation errors include field information."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422
        # Pydantic validation error should have detail array
        assert "detail" in r.json()


class TestDataTypeHandling:
    """Test how the API handles various data types."""

    def test_price_float_precision(self):
        """Verify price float precision is maintained."""
        r = client.post("/items", json={"name": "item", "price": 10.99})
        assert r.status_code == 200
        price = r.json()["price"]
        assert abs(price - 10.99) < 0.001

    def test_item_id_is_integer(self):
        """Verify item id is returned as integer."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        item_id = r.json()["id"]
        assert isinstance(item_id, int)

    def test_item_name_is_string(self):
        """Verify item name is returned as string."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        name = r.json()["name"]
        assert isinstance(name, str)


class TestStressScenarios:
    """Test API behavior under various stress scenarios."""

    def test_create_multiple_items_rapidly(self):
        """Create multiple items in rapid succession."""
        for i in range(5):
            r = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            assert r.status_code == 200
            assert r.json()["id"] == 1  # API always returns id=1

    def test_get_item_multiple_times(self):
        """Retrieve the same item multiple times."""
        for _ in range(5):
            r = client.get("/items/1")
            assert r.status_code == 200
            assert r.json()["id"] == 1

    def test_mixed_create_and_get_operations(self):
        """Interleave create and get operations."""
        for i in range(3):
            # Create
            r = client.post("/items", json={"name": f"item{i}", "price": 10.0})
            assert r.status_code == 200
            
            # Get existing
            r = client.get("/items/1")
            assert r.status_code == 200
            
            # Get non-existing
            r = client.get("/items/999")
            assert r.status_code == 404

    def test_very_long_name_handling(self):
        """Test handling of very long item names."""
        long_name = "a" * 50000
        r = client.post("/items", json={"name": long_name, "price": 10.0})
        assert r.status_code == 200
        assert len(r.json()["name"]) == 50000


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_endpoint_structure(self):
        """Verify health endpoint response structure."""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data == {"status": "ok"}

    def test_health_endpoint_multiple_calls(self):
        """Health endpoint should return consistent results."""
        for _ in range(3):
            r = client.get("/health")
            assert r.status_code == 200
            assert r.json() == {"status": "ok"}

    def test_health_response_type(self):
        """Verify health response is valid JSON."""
        r = client.get("/health")
        assert r.status_code == 200
        assert isinstance(r.json(), dict)
