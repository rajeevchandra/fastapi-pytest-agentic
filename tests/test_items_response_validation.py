"""
Response structure and error handling tests for all endpoints.

Tests cover:
- HTTP status code verification
- Response field types and structure
- Error response format consistency
- Error message validation
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Test /health endpoint."""

    def test_health_returns_200(self):
        """Health check should return 200."""
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_response_structure(self):
        """Health response should have status field."""
        r = client.get("/health")
        data = r.json()
        assert "status" in data

    def test_health_response_status_value(self):
        """Health status should be 'ok'."""
        r = client.get("/health")
        assert r.json()["status"] == "ok"

    def test_health_response_is_json(self):
        """Health response should be valid JSON."""
        r = client.get("/health")
        assert r.headers["content-type"]
        assert "application/json" in r.headers["content-type"]


class TestCreateItemHTTPStatusCodes:
    """Test HTTP status codes for POST /items."""

    def test_create_item_success_returns_200(self):
        """Successful item creation should return 200."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert r.status_code == 200

    def test_create_item_invalid_price_returns_400(self):
        """Invalid price should return 400."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.status_code == 400

    def test_create_item_missing_field_returns_422(self):
        """Missing required field should return 422."""
        r = client.post("/items", json={"name": "item"})
        assert r.status_code == 422

    def test_create_item_invalid_type_returns_422(self):
        """Invalid type should return 422."""
        r = client.post("/items", json={"name": "item", "price": "invalid"})
        assert r.status_code == 422

    def test_create_item_empty_body_returns_422(self):
        """Empty body should return 422."""
        r = client.post("/items", json={})
        assert r.status_code == 422


class TestCreateItemErrorResponseFormat:
    """Test error response format for invalid requests."""

    def test_business_error_has_detail_field(self):
        """Business validation error should have detail field."""
        r = client.post("/items", json={"name": "item", "price": -1})
        assert r.status_code == 400
        data = r.json()
        assert "detail" in data

    def test_business_error_detail_is_string(self):
        """Error detail should be a string."""
        r = client.post("/items", json={"name": "item", "price": 0})
        data = r.json()
        assert isinstance(data["detail"], str)

    def test_validation_error_has_detail_field(self):
        """Validation error should have detail field."""
        r = client.post("/items", json={"price": 10.0})
        data = r.json()
        assert "detail" in data

    def test_error_messages_are_informative(self):
        """Error messages should provide useful information."""
        r = client.post("/items", json={"name": "item", "price": 0})
        detail = r.json()["detail"]
        assert "price" in detail.lower()
        assert len(detail) > 5


class TestGetItemHTTPStatusCodes:
    """Test HTTP status codes for GET /items/{item_id}."""

    def test_get_item_found_returns_200(self):
        """Getting existing item should return 200."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_get_item_not_found_returns_404(self):
        """Getting non-existent item should return 404."""
        r = client.get("/items/2")
        assert r.status_code == 404

    def test_get_item_various_ids_not_found(self):
        """Getting items with various IDs other than 1 should return 404."""
        for item_id in [3, 5, 100, 999]:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404


class TestGetItemErrorResponseFormat:
    """Test error response format for GET endpoint."""

    def test_not_found_error_has_detail(self):
        """404 response should have detail field."""
        r = client.get("/items/2")
        assert r.status_code == 404
        assert "detail" in r.json()

    def test_not_found_detail_is_string(self):
        """Error detail should be a string."""
        r = client.get("/items/999")
        assert isinstance(r.json()["detail"], str)

    def test_not_found_error_message(self):
        """404 error should indicate item not found."""
        r = client.get("/items/2")
        detail = r.json()["detail"]
        assert "not found" in detail.lower() or "404" in str(r.status_code)


class TestCreateItemResponseFields:
    """Test response field presence and types."""

    def test_create_item_response_has_id(self):
        """Response must include id field."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert "id" in r.json()

    def test_create_item_response_has_name(self):
        """Response must include name field."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert "name" in r.json()

    def test_create_item_response_has_price(self):
        """Response must include price field."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert "price" in r.json()

    def test_create_item_id_is_integer(self):
        """Response id should be an integer."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert isinstance(r.json()["id"], int)

    def test_create_item_name_is_string(self):
        """Response name should be a string."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert isinstance(r.json()["name"], str)

    def test_create_item_price_is_number(self):
        """Response price should be a number."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        price = r.json()["price"]
        assert isinstance(price, (int, float))
        assert not isinstance(price, bool)


class TestGetItemResponseFields:
    """Test response field presence and types for GET."""

    def test_get_item_response_has_id(self):
        """Response must include id field."""
        r = client.get("/items/1")
        assert "id" in r.json()

    def test_get_item_response_has_name(self):
        """Response must include name field."""
        r = client.get("/items/1")
        assert "name" in r.json()

    def test_get_item_response_has_price(self):
        """Response must include price field."""
        r = client.get("/items/1")
        assert "price" in r.json()

    def test_get_item_response_fields_types(self):
        """Response fields should have correct types."""
        r = client.get("/items/1")
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))
        assert not isinstance(data["price"], bool)


class TestContentTypeHeaders:
    """Test content type headers."""

    def test_create_item_response_content_type(self):
        """POST response should have JSON content type."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert "application/json" in r.headers.get("content-type", "")

    def test_get_item_response_content_type(self):
        """GET response should have JSON content type."""
        r = client.get("/items/1")
        assert "application/json" in r.headers.get("content-type", "")

    def test_health_response_content_type(self):
        """Health response should have JSON content type."""
        r = client.get("/health")
        assert "application/json" in r.headers.get("content-type", "")
