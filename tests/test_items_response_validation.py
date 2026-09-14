"""Test response structure and error handling for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemHTTPStatusCodes:
    """Test HTTP status codes for POST /items endpoint."""

    def test_create_item_success_status_200(self):
        """Successful item creation returns 200."""
        response = client.post("/items", json={"name": "item", "price": 10.0})
        assert response.status_code == 200

    def test_create_item_price_validation_status_400(self):
        """Price validation error returns 400."""
        response = client.post("/items", json={"name": "item", "price": -1})
        assert response.status_code == 400

    def test_create_item_missing_field_status_422(self):
        """Missing required field returns 422."""
        response = client.post("/items", json={"name": "item"})
        assert response.status_code == 422

    def test_create_item_null_field_status_422(self):
        """Null required field returns 422."""
        response = client.post("/items", json={"name": None, "price": 10.0})
        assert response.status_code == 422


class TestCreateItemErrorResponse:
    """Test error response structure for POST /items."""

    def test_create_item_price_error_has_detail(self):
        """400 error response should have 'detail' field."""
        response = client.post("/items", json={"name": "item", "price": 0})
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    def test_create_item_price_error_message_correct(self):
        """400 error should have correct detail message."""
        response = client.post("/items", json={"name": "item", "price": -5})
        data = response.json()
        assert data["detail"] == "price must be > 0"

    def test_create_item_validation_error_structure(self):
        """422 validation error should have expected structure."""
        response = client.post("/items", json={"price": 10.0})
        assert response.status_code == 422
        data = response.json()
        assert isinstance(data, dict)
        # FastAPI validation errors include 'detail' field
        assert "detail" in data

    @pytest.mark.parametrize("price", [-100, -1, -0.01, 0])
    def test_create_item_all_invalid_prices_same_error(self, price):
        """All non-positive prices should return same error detail."""
        response = client.post("/items", json={"name": "item", "price": price})
        assert response.status_code == 400
        assert response.json()["detail"] == "price must be > 0"


class TestGetItemHTTPStatusCodes:
    """Test HTTP status codes for GET /items/{item_id}."""

    def test_get_item_found_status_200(self):
        """Existing item returns 200."""
        response = client.get("/items/1")
        assert response.status_code == 200

    def test_get_item_not_found_status_404(self):
        """Non-existent item returns 404."""
        response = client.get("/items/2")
        assert response.status_code == 404

    @pytest.mark.parametrize("item_id", [99, 100, 999, 10000])
    def test_get_item_various_ids_not_found(self, item_id):
        """Any item_id != 1 returns 404."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == 404


class TestGetItemErrorResponse:
    """Test error response structure for GET /items/{item_id}."""

    def test_get_item_not_found_has_detail(self):
        """404 response should have 'detail' field."""
        response = client.get("/items/2")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_get_item_not_found_detail_message(self):
        """404 should have 'not found' detail message."""
        response = client.get("/items/99")
        data = response.json()
        assert data["detail"] == "not found"

    @pytest.mark.parametrize("item_id", [2, 10, 100, 999999])
    def test_get_item_all_invalid_ids_same_error(self, item_id):
        """All item_id != 1 should return same error message."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == 404
        assert response.json()["detail"] == "not found"


class TestCreateItemResponseContent:
    """Test response content and structure for POST /items."""

    def test_create_item_response_is_json(self):
        """Response content-type should be JSON."""
        response = client.post("/items", json={"name": "item", "price": 10.0})
        assert response.headers["content-type"].startswith("application/json")

    def test_create_item_response_all_fields_present(self):
        """Response must include id, name, and price."""
        response = client.post("/items", json={"name": "book", "price": 15.0})
        data = response.json()
        assert set(data.keys()) >= {"id", "name", "price"}

    def test_create_item_response_field_types(self):
        """Response fields must have correct types."""
        response = client.post("/items", json={"name": "book", "price": 15.0})
        data = response.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_create_item_response_price_matches_input(self):
        """Response price should match input price exactly."""
        price = 25.99
        response = client.post("/items", json={"name": "item", "price": price})
        assert response.json()["price"] == price

    def test_create_item_response_name_matches_input(self):
        """Response name should match input name exactly."""
        name = "test-product"
        response = client.post("/items", json={"name": name, "price": 10.0})
        assert response.json()["name"] == name


class TestGetItemResponseContent:
    """Test response content and structure for GET /items/{item_id}."""

    def test_get_item_response_is_json(self):
        """Response content-type should be JSON."""
        response = client.get("/items/1")
        assert response.headers["content-type"].startswith("application/json")

    def test_get_item_response_all_fields_present(self):
        """Response must include id, name, and price."""
        response = client.get("/items/1")
        data = response.json()
        assert set(data.keys()) >= {"id", "name", "price"}

    def test_get_item_response_field_types(self):
        """Response fields must have correct types."""
        response = client.get("/items/1")
        data = response.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_get_item_response_data_consistency(self):
        """Response should have consistent data (item 1)."""
        response = client.get("/items/1")
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0


class TestHealthEndpoint:
    """Test /health endpoint responses."""

    def test_health_status_200(self):
        """Health check returns 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_structure(self):
        """Health response should have 'status' field."""
        response = client.get("/health")
        data = response.json()
        assert "status" in data

    def test_health_response_status_value(self):
        """Health status value should be 'ok'."""
        response = client.get("/health")
        assert response.json()["status"] == "ok"

    def test_health_response_is_json(self):
        """Health response content-type should be JSON."""
        response = client.get("/health")
        assert response.headers["content-type"].startswith("application/json")
