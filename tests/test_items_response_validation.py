"""
Test suite for response structure validation and error handling.
Covers response field types, structure validation, and HTTP status codes.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemResponseStructure:
    """Test response structure and field types for POST /items."""

    def test_create_item_response_has_required_fields(self):
        """Test that create_item response contains all required fields."""
        response = client.post("/items", json={"name": "test", "price": 10.0})
        assert response.status_code == 200
        data = response.json()
        # Check all required fields are present
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_create_item_response_field_types(self):
        """Test that response fields have correct types."""
        response = client.post("/items", json={"name": "test", "price": 10.5})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], float)

    def test_create_item_response_id_is_one(self):
        """Test that created items always have id=1."""
        response = client.post("/items", json={"name": "first", "price": 10.0})
        assert response.json()["id"] == 1

    def test_create_item_response_preserves_name(self):
        """Test that response name matches request."""
        test_name = "My Special Item"
        response = client.post("/items", json={"name": test_name, "price": 10.0})
        assert response.json()["name"] == test_name

    def test_create_item_response_preserves_price(self):
        """Test that response price matches request."""
        test_price = 99.99
        response = client.post("/items", json={"name": "test", "price": test_price})
        assert response.json()["price"] == test_price

    def test_create_item_response_no_extra_fields(self):
        """Test that response only contains expected fields."""
        response = client.post("/items", json={"name": "test", "price": 10.0})
        data = response.json()
        expected_fields = {"id", "name", "price"}
        assert set(data.keys()) == expected_fields

    def test_create_item_content_type(self):
        """Test that response has correct content type."""
        response = client.post("/items", json={"name": "test", "price": 10.0})
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")


class TestErrorResponseFormat:
    """Test error response format consistency."""

    def test_error_response_has_detail_field(self):
        """Test that error responses include detail field."""
        response = client.post("/items", json={"name": "test", "price": 0})
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    def test_price_validation_error_message(self):
        """Test specific error message for price validation."""
        response = client.post("/items", json={"name": "test", "price": -1})
        assert response.status_code == 400
        assert response.json()["detail"] == "price must be > 0"

    def test_missing_field_error_includes_detail(self):
        """Test that validation errors include detail."""
        response = client.post("/items", json={"name": "test"})
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_error_response_is_json(self):
        """Test that error responses are valid JSON."""
        response = client.post("/items", json={"price": 0})
        assert response.status_code in (400, 422)
        # Should not raise an exception
        data = response.json()
        assert isinstance(data, dict)

    def test_validation_error_has_array_detail(self):
        """Test that FastAPI validation errors include detail array."""
        response = client.post("/items", json={})
        assert response.status_code == 422
        data = response.json()
        # FastAPI returns detail as array for validation errors
        assert "detail" in data
        if isinstance(data["detail"], list):
            assert len(data["detail"]) > 0

    def test_error_response_content_type(self):
        """Test error responses have correct content type."""
        response = client.post("/items", json={"name": "test", "price": 0})
        assert response.status_code == 400
        assert "application/json" in response.headers.get("content-type", "")


class TestGetItemResponseStructure:
    """Test response structure and field types for GET /items/{item_id}."""

    def test_get_item_response_has_required_fields(self):
        """Test that get_item response contains all required fields."""
        response = client.get("/items/1")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_get_item_response_field_types(self):
        """Test that response fields have correct types."""
        response = client.get("/items/1")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], float)

    def test_get_item_response_no_extra_fields(self):
        """Test that response only contains expected fields."""
        response = client.get("/items/1")
        data = response.json()
        expected_fields = {"id", "name", "price"}
        assert set(data.keys()) == expected_fields

    def test_get_item_response_data_consistency(self):
        """Test that get_item returns consistent data."""
        response = client.get("/items/1")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0

    def test_get_item_content_type(self):
        """Test that response has correct content type."""
        response = client.get("/items/1")
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")


class TestHTTPStatusCodes:
    """Test HTTP status codes for various scenarios."""

    def test_create_item_success_returns_200(self):
        """Test successful create returns 200 OK."""
        response = client.post("/items", json={"name": "test", "price": 10.0})
        assert response.status_code == 200

    def test_create_item_invalid_price_returns_400(self):
        """Test invalid price returns 400 Bad Request."""
        response = client.post("/items", json={"name": "test", "price": 0})
        assert response.status_code == 400

    def test_create_item_negative_price_returns_400(self):
        """Test negative price returns 400 Bad Request."""
        response = client.post("/items", json={"name": "test", "price": -10.0})
        assert response.status_code == 400

    def test_create_item_missing_field_returns_422(self):
        """Test missing field returns 422 Unprocessable Entity."""
        response = client.post("/items", json={"name": "test"})
        assert response.status_code == 422

    def test_get_item_found_returns_200(self):
        """Test getting existing item returns 200 OK."""
        response = client.get("/items/1")
        assert response.status_code == 200

    def test_get_item_not_found_returns_404(self):
        """Test getting non-existent item returns 404 Not Found."""
        response = client.get("/items/2")
        assert response.status_code == 404

    def test_get_item_not_found_message(self):
        """Test 404 response includes appropriate message."""
        response = client.get("/items/2")
        assert response.status_code == 404
        assert response.json()["detail"] == "not found"

    def test_get_nonexistent_items_various_ids_returns_404(self):
        """Test that various non-1 IDs return 404."""
        for item_id in [2, 3, 100, 999999]:
            response = client.get(f"/items/{item_id}")
            assert response.status_code == 404

    def test_post_with_float_price_in_string_returns_200(self):
        """Test that numeric string price coerces to float."""
        response = client.post("/items", json={"name": "test", "price": "15.5"})
        assert response.status_code == 200

    def test_post_with_int_price_returns_200(self):
        """Test that int price is accepted."""
        response = client.post("/items", json={"name": "test", "price": 15})
        assert response.status_code == 200


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_endpoint_returns_200(self):
        """Test health endpoint returns 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_endpoint_response_structure(self):
        """Test health endpoint returns expected response."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"

    def test_health_endpoint_response_type(self):
        """Test health endpoint returns object with string status."""
        response = client.get("/health")
        data = response.json()
        assert isinstance(data, dict)
        assert isinstance(data["status"], str)

    def test_health_endpoint_content_type(self):
        """Test health endpoint has correct content type."""
        response = client.get("/health")
        assert "application/json" in response.headers.get("content-type", "")
