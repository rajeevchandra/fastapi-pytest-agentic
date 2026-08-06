"""Response structure and HTTP status code validation."""
from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)


class TestCreateItemResponseStructure:
    """Test response structure for POST /items endpoint."""

    def test_create_item_response_has_required_fields(self):
        """Response should contain id, name, and price fields."""
        response = client.post("/items", json={"name": "test", "price": 10.5})
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data
        assert len(data) == 3  # exactly these 3 fields

    def test_create_item_response_field_types(self):
        """Response fields should have correct types."""
        response = client.post("/items", json={"name": "test", "price": 10.5})
        data = response.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_create_item_response_echoes_input(self):
        """Response name and price should match request."""
        test_name = "Test Product"
        test_price = 25.99
        response = client.post(
            "/items",
            json={"name": test_name, "price": test_price}
        )
        data = response.json()
        assert data["name"] == test_name
        assert data["price"] == test_price

    def test_create_item_response_always_id_1(self):
        """Current implementation always returns id=1."""
        response = client.post("/items", json={"name": "test", "price": 10.0})
        data = response.json()
        assert data["id"] == 1

    def test_create_item_response_content_type(self):
        """Response should be JSON."""
        response = client.post("/items", json={"name": "test", "price": 10.0})
        assert "application/json" in response.headers.get("content-type", "")


class TestCreateItemErrorResponses:
    """Test error response structure for POST /items."""

    def test_create_item_negative_price_error_format(self):
        """Error response should have standard format."""
        response = client.post("/items", json={"name": "test", "price": -5})
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

    def test_create_item_validation_error_format(self):
        """422 validation error should have detail field."""
        response = client.post("/items", json={"name": "test"})
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.parametrize("invalid_payload", [
        {"price": 10.0},                    # missing name
        {"name": "test"},                   # missing price
        {},                                  # empty
        {"name": "test", "price": "abc"},   # invalid type
    ])
    def test_create_item_validation_errors(self, invalid_payload):
        """Validation errors should return 422."""
        response = client.post("/items", json=invalid_payload)
        assert response.status_code == 422


class TestGetItemResponseStructure:
    """Test response structure for GET /items/{item_id}."""

    def test_get_item_response_has_required_fields(self):
        """Response should contain id, name, and price fields."""
        response = client.get("/items/1")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_get_item_response_field_types(self):
        """Response fields should have correct types."""
        response = client.get("/items/1")
        data = response.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_get_item_response_content_type(self):
        """Response should be JSON."""
        response = client.get("/items/1")
        assert "application/json" in response.headers.get("content-type", "")

    def test_get_item_found_returns_sample_data(self):
        """GET /items/1 should return expected sample data."""
        response = client.get("/items/1")
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0


class TestGetItemErrorResponses:
    """Test error response structure for GET /items/{item_id}."""

    def test_get_item_not_found_error_format(self):
        """404 response should have detail field."""
        response = client.get("/items/999")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "not found"

    def test_get_item_error_response_type(self):
        """Error detail should be a string."""
        response = client.get("/items/999")
        data = response.json()
        assert isinstance(data["detail"], str)


class TestHTTPStatusCodes:
    """Test HTTP status codes across endpoints."""

    @pytest.mark.parametrize("endpoint,method,status", [
        ("/health", "get", 200),
        ("/items", "post", 200),
        ("/items/1", "get", 200),
        ("/items/999", "get", 404),
    ])
    def test_http_status_codes(self, endpoint, method, status):
        """Verify HTTP status codes for various endpoints."""
        if method == "get":
            response = client.get(endpoint)
        elif method == "post":
            response = client.post(endpoint, json={"name": "test", "price": 10.0})
        assert response.status_code == status

    def test_invalid_price_returns_400(self):
        """Invalid price should return 400 Bad Request."""
        response = client.post("/items", json={"name": "test", "price": 0})
        assert response.status_code == 400

    def test_invalid_price_detail_message(self):
        """400 error should have specific detail about price."""
        response = client.post("/items", json={"name": "test", "price": -1})
        assert response.status_code == 400
        assert "price" in response.json()["detail"].lower()

    def test_missing_fields_returns_422(self):
        """Missing fields should return 422 Unprocessable Entity."""
        response = client.post("/items", json={"name": "test"})
        assert response.status_code == 422
