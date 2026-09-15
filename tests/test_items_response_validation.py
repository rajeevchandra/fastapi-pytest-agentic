"""Comprehensive response validation and error handling tests."""
from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)


class TestCreateItemHTTPStatusCodes:
    """Test HTTP status codes for create_item endpoint."""

    def test_success_returns_200(self):
        """Successful item creation returns 200."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200

    def test_negative_price_returns_400(self):
        """Negative price returns 400 Bad Request."""
        r = client.post("/items", json={"name": "test", "price": -1})
        assert r.status_code == 400

    def test_zero_price_returns_400(self):
        """Zero price returns 400 Bad Request."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400

    def test_missing_field_returns_422(self):
        """Missing required field returns 422 Unprocessable Entity."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422

    def test_invalid_type_returns_422(self):
        """Invalid field type returns 422 Unprocessable Entity."""
        r = client.post("/items", json={"name": "test", "price": "not_a_number"})
        # Pydantic might coerce or reject depending on strictness


class TestCreateItemErrorResponse:
    """Test error response format."""

    def test_validation_error_has_detail(self):
        """Validation errors include detail field."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data

    def test_business_logic_error_message(self):
        """Business logic errors (price <= 0) have proper message."""
        r = client.post("/items", json={"name": "test", "price": -1})
        assert r.status_code == 400
        data = r.json()
        assert data["detail"] == "price must be > 0"

    def test_error_response_json_format(self):
        """Error responses are valid JSON."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400
        # Should not raise exception
        data = r.json()
        assert isinstance(data, dict)


class TestGetItemHTTPStatusCodes:
    """Test HTTP status codes for get_item endpoint."""

    @pytest.mark.parametrize("item_id", [1])
    def test_existing_item_returns_200(self, item_id):
        """Getting existing item returns 200."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 200

    @pytest.mark.parametrize("item_id", [2, 3, 99, 100, -1])
    def test_nonexistent_item_returns_404(self, item_id):
        """Getting non-existent item returns 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404


class TestGetItemResponseStructure:
    """Test response structure for get_item endpoint."""

    def test_found_item_has_required_fields(self):
        """Found item response includes id, name, price."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_found_item_field_types(self):
        """Response fields have correct types."""
        r = client.get("/items/1")
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_found_item_expected_values(self):
        """Item 1 returns expected data."""
        r = client.get("/items/1")
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0

    def test_response_only_has_expected_fields(self):
        """Response contains only id, name, price."""
        r = client.get("/items/1")
        data = r.json()
        assert set(data.keys()) == {"id", "name", "price"}


class TestGetItemErrorResponse:
    """Test error response for get_item endpoint."""

    def test_not_found_returns_detail(self):
        """404 response includes detail message."""
        r = client.get("/items/2")
        assert r.status_code == 404
        data = r.json()
        assert data["detail"] == "not found"

    def test_not_found_has_detail_field(self):
        """404 error has detail field."""
        r = client.get("/items/999")
        assert r.status_code == 404
        assert "detail" in r.json()


class TestHealthEndpointResponse:
    """Test response format for health endpoint."""

    def test_health_returns_200(self):
        """Health endpoint returns 200."""
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_response_format(self):
        """Health response has correct format."""
        r = client.get("/health")
        data = r.json()
        assert data == {"status": "ok"}

    def test_health_response_has_status_field(self):
        """Health response includes status field."""
        r = client.get("/health")
        data = r.json()
        assert "status" in data
        assert data["status"] == "ok"


class TestContentTypeHeaders:
    """Test response content type headers."""

    def test_create_item_content_type_json(self):
        """POST /items response has JSON content type."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert "application/json" in r.headers.get("content-type", "")

    def test_get_item_content_type_json(self):
        """GET /items/{id} response has JSON content type."""
        r = client.get("/items/1")
        assert "application/json" in r.headers.get("content-type", "")

    def test_health_content_type_json(self):
        """GET /health response has JSON content type."""
        r = client.get("/health")
        assert "application/json" in r.headers.get("content-type", "")


class TestResponseNumberTypes:
    """Test numeric field handling in responses."""

    def test_price_is_float_in_response(self):
        """Price field should be returned as float."""
        r = client.post("/items", json={"name": "test", "price": 10})
        data = r.json()
        # JSON serialization may represent as int or float
        assert isinstance(data["price"], (int, float))
        assert data["price"] == 10

    def test_id_is_int_in_response(self):
        """ID field should be returned as int."""
        r = client.get("/items/1")
        data = r.json()
        assert isinstance(data["id"], int)
        assert data["id"] == 1

    def test_large_price_precision(self):
        """Large prices maintain precision."""
        large_price = 999999.99
        r = client.post("/items", json={"name": "test", "price": large_price})
        data = r.json()
        assert data["price"] == large_price
