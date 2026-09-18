"""
Test suite for response structure validation and error handling.

This module provides comprehensive tests for:
- Response field types and structure validation
- Error response format consistency
- All HTTP status codes
- Error message content validation
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemHTTPStatusCodes:
    """Tests for HTTP status codes in item creation responses."""

    def test_create_item_success_status_is_200(self):
        """Successful item creation returns 200 OK."""
        r = client.post("/items", json={"name": "book", "price": 12.5})
        assert r.status_code == 200

    def test_create_item_negative_price_status_is_400(self):
        """Invalid price returns 400 Bad Request."""
        r = client.post("/items", json={"name": "item", "price": -5})
        assert r.status_code == 400

    def test_create_item_zero_price_status_is_400(self):
        """Zero price returns 400 Bad Request."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.status_code == 400

    def test_create_item_missing_field_status_is_422(self):
        """Missing required field returns 422 Unprocessable Entity."""
        r = client.post("/items", json={"name": "item"})
        assert r.status_code == 422

    def test_create_item_invalid_type_status_is_422(self):
        """Invalid field type returns 422 Unprocessable Entity."""
        r = client.post("/items", json={"name": ["list"], "price": 10})
        assert r.status_code == 422


class TestGetItemHTTPStatusCodes:
    """Tests for HTTP status codes in item retrieval."""

    @pytest.mark.parametrize("item_id", [1])
    def test_get_item_found_status_is_200(self, item_id):
        """Existing item returns 200 OK."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 200

    @pytest.mark.parametrize("item_id", [0, -1, 2, 999, 1000000])
    def test_get_item_not_found_status_is_404(self, item_id):
        """Non-existent item returns 404 Not Found."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404


class TestCreateItemResponseStructure:
    """Tests for response structure validation on item creation."""

    def test_create_item_response_is_json_dict(self):
        """Response should be a JSON object (dict)."""
        r = client.post("/items", json={"name": "test", "price": 10})
        assert r.status_code == 200
        assert isinstance(r.json(), dict)

    def test_create_item_response_not_list(self):
        """Response should not be a list."""
        r = client.post("/items", json={"name": "test", "price": 10})
        assert r.status_code == 200
        assert not isinstance(r.json(), list)

    def test_create_item_response_exact_fields(self):
        """Response should contain exactly id, name, and price."""
        r = client.post("/items", json={"name": "test", "price": 10})
        assert r.status_code == 200
        data = r.json()
        assert set(data.keys()) == {"id", "name", "price"}

    def test_create_item_no_extra_fields(self):
        """Response should not contain extra fields."""
        r = client.post("/items", json={"name": "test", "price": 10})
        assert r.status_code == 200
        data = r.json()
        forbidden_fields = ["description", "category", "stock", "created_at"]
        for field in forbidden_fields:
            assert field not in data

    def test_create_item_id_type(self):
        """Response id should be an integer."""
        r = client.post("/items", json={"name": "test", "price": 10})
        assert r.status_code == 200
        assert isinstance(r.json()["id"], int)

    def test_create_item_name_type(self):
        """Response name should be a string."""
        r = client.post("/items", json={"name": "test", "price": 10})
        assert r.status_code == 200
        assert isinstance(r.json()["name"], str)

    def test_create_item_price_type(self):
        """Response price should be a number (float or int)."""
        r = client.post("/items", json={"name": "test", "price": 10})
        assert r.status_code == 200
        price = r.json()["price"]
        assert isinstance(price, (int, float))

    def test_create_item_id_positive(self):
        """Response id should be positive."""
        r = client.post("/items", json={"name": "test", "price": 10})
        assert r.status_code == 200
        assert r.json()["id"] > 0

    def test_create_item_id_consistent(self):
        """Response id should be consistent across requests (always 1)."""
        r1 = client.post("/items", json={"name": "item1", "price": 10})
        r2 = client.post("/items", json={"name": "item2", "price": 20})
        assert r1.json()["id"] == 1
        assert r2.json()["id"] == 1


class TestGetItemResponseStructure:
    """Tests for response structure validation on item retrieval."""

    def test_get_item_response_is_json_dict(self):
        """Response should be a JSON object."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert isinstance(r.json(), dict)

    def test_get_item_response_exact_fields(self):
        """Response should contain exactly id, name, and price."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert set(data.keys()) == {"id", "name", "price"}

    def test_get_item_id_type(self):
        """Response id should be an integer."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert isinstance(r.json()["id"], int)

    def test_get_item_name_type(self):
        """Response name should be a string."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert isinstance(r.json()["name"], str)

    def test_get_item_price_type(self):
        """Response price should be a number."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert isinstance(r.json()["price"], (int, float))

    def test_get_item_response_consistent(self):
        """Item 1 should always return the same data."""
        r1 = client.get("/items/1")
        r2 = client.get("/items/1")
        assert r1.json() == r2.json()

    def test_get_item_id_matches_requested_id(self):
        """Response id should match the requested item_id."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["id"] == 1


class TestCreateItemErrorResponse:
    """Tests for error response format consistency on item creation."""

    def test_create_item_error_response_is_dict(self):
        """Error response should be a JSON object."""
        r = client.post("/items", json={"name": "item", "price": -5})
        assert r.status_code == 400
        assert isinstance(r.json(), dict)

    def test_create_item_error_has_detail_field(self):
        """Error response should have 'detail' field."""
        r = client.post("/items", json={"name": "item", "price": -5})
        assert r.status_code == 400
        assert "detail" in r.json()

    def test_create_item_error_detail_is_string(self):
        """Error detail should be a string."""
        r = client.post("/items", json={"name": "item", "price": -5})
        assert r.status_code == 400
        detail = r.json()["detail"]
        assert isinstance(detail, str)

    def test_create_item_error_message_not_empty(self):
        """Error message should not be empty."""
        r = client.post("/items", json={"name": "item", "price": -5})
        assert r.status_code == 400
        detail = r.json()["detail"]
        assert len(detail) > 0

    def test_create_item_validation_error_format(self):
        """Validation error should have 'detail' field with error list or string."""
        r = client.post("/items", json={"name": "item"})
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data


class TestGetItemErrorResponse:
    """Tests for error response format consistency on item retrieval."""

    def test_get_item_error_response_is_dict(self):
        """Error response should be a JSON object."""
        r = client.get("/items/999")
        assert r.status_code == 404
        assert isinstance(r.json(), dict)

    def test_get_item_error_has_detail_field(self):
        """Error response should have 'detail' field."""
        r = client.get("/items/999")
        assert r.status_code == 404
        assert "detail" in r.json()

    def test_get_item_error_detail_is_string(self):
        """Error detail should be a string."""
        r = client.get("/items/999")
        assert r.status_code == 404
        detail = r.json()["detail"]
        assert isinstance(detail, str)

    def test_get_item_not_found_error_message(self):
        """Not found error should have meaningful message."""
        r = client.get("/items/999")
        assert r.status_code == 404
        detail = r.json()["detail"]
        assert len(detail) > 0
        assert detail == "not found"

    def test_get_item_multiple_not_found_ids(self):
        """Multiple non-existent IDs should return 404 with same format."""
        for item_id in [0, -1, 2, 999]:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404
            assert "detail" in r.json()


class TestHealthEndpointResponse:
    """Tests for health endpoint response structure."""

    def test_health_status_is_200(self):
        """Health check should return 200 OK."""
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_response_is_dict(self):
        """Health response should be a JSON object."""
        r = client.get("/health")
        assert r.status_code == 200
        assert isinstance(r.json(), dict)

    def test_health_response_has_status_field(self):
        """Health response should have 'status' field."""
        r = client.get("/health")
        assert r.status_code == 200
        assert "status" in r.json()

    def test_health_response_status_is_ok(self):
        """Health status should be 'ok'."""
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_health_response_consistent(self):
        """Health response should be consistent."""
        r1 = client.get("/health")
        r2 = client.get("/health")
        assert r1.json() == r2.json()


class TestContentTypeHeaders:
    """Tests for response content type headers."""

    def test_create_item_content_type_json(self):
        """Create item response should have JSON content type."""
        r = client.post("/items", json={"name": "test", "price": 10})
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")

    def test_get_item_content_type_json(self):
        """Get item response should have JSON content type."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")

    def test_health_content_type_json(self):
        """Health response should have JSON content type."""
        r = client.get("/health")
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")

    def test_error_response_content_type_json(self):
        """Error response should have JSON content type."""
        r = client.get("/items/999")
        assert r.status_code == 404
        assert "application/json" in r.headers.get("content-type", "")


class TestResponseEncodingAndFormat:
    """Tests for response encoding and format consistency."""

    def test_create_item_response_utf8(self):
        """Response should be valid UTF-8."""
        r = client.post("/items", json={"name": "café", "price": 10})
        assert r.status_code == 200
        # If we can decode and access, it's valid UTF-8
        assert r.json()["name"] == "café"

    def test_create_item_with_special_chars_preserved(self):
        """Special characters in names should be preserved."""
        special_name = "测试商品"
        r = client.post("/items", json={"name": special_name, "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == special_name

    def test_price_precision_in_response(self):
        """Price precision should be maintained in response."""
        r = client.post("/items", json={"name": "test", "price": 10.99})
        assert r.status_code == 200
        price = r.json()["price"]
        assert abs(price - 10.99) < 0.01


class TestErrorMessageConsistency:
    """Tests for error message consistency and clarity."""

    def test_negative_price_error_message(self):
        """Negative price error should mention price and requirement."""
        r = client.post("/items", json={"name": "item", "price": -10})
        assert r.status_code == 400
        assert "price" in r.json()["detail"].lower()
        assert ">" in r.json()["detail"] or "positive" in r.json()["detail"].lower()

    def test_zero_price_error_message(self):
        """Zero price error should be same as negative price error."""
        r1 = client.post("/items", json={"name": "item", "price": -1})
        r2 = client.post("/items", json={"name": "item", "price": 0})
        assert r1.status_code == 400
        assert r2.status_code == 400
        assert r1.json()["detail"] == r2.json()["detail"]

    def test_not_found_error_consistent_format(self):
        """Not found errors should have consistent format."""
        errors = []
        for item_id in [2, 0, -1, 999]:
            r = client.get(f"/items/{item_id}")
            errors.append(r.json()["detail"])
        # All not found errors should be identical
        assert len(set(errors)) == 1
