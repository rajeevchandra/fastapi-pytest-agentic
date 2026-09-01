"""
Test suite for response validation on the /items endpoint.
Tests cover response structure, status codes, and error formats.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemHTTPStatusCodes:
    """Tests for HTTP status codes returned by POST /items."""

    def test_create_item_success_returns_200(self):
        """Valid item creation should return 200."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200

    @pytest.mark.parametrize("price", [0, -1, -100])
    def test_create_item_invalid_price_returns_400(self, price):
        """Invalid price should return 400 Bad Request."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400

    def test_create_item_missing_field_returns_422(self):
        """Missing required field should return 422."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422

    def test_create_item_invalid_type_returns_422(self):
        """Invalid field type should return 422."""
        r = client.post("/items", json={"name": "test", "price": "not_a_number"})
        assert r.status_code == 422

    def test_create_item_empty_json_returns_422(self):
        """Empty JSON object should return 422."""
        r = client.post("/items", json={})
        assert r.status_code == 422


class TestGetItemHTTPStatusCodes:
    """Tests for HTTP status codes returned by GET /items/{item_id}."""

    def test_get_item_found_returns_200(self):
        """Getting existing item should return 200."""
        r = client.get("/items/1")
        assert r.status_code == 200

    @pytest.mark.parametrize("item_id", [2, 3, 99, 999])
    def test_get_item_not_found_returns_404(self, item_id):
        """Getting non-existent item should return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    def test_get_item_negative_id_returns_404(self):
        """Negative item ID should return 404."""
        r = client.get("/items/-1")
        assert r.status_code == 404

    def test_get_item_zero_id_returns_404(self):
        """Zero item ID should return 404."""
        r = client.get("/items/0")
        assert r.status_code == 404


class TestCreateItemErrorResponseFormat:
    """Tests for error response format from POST /items."""

    def test_create_item_price_error_has_detail_field(self):
        """Price validation error should have detail field."""
        r = client.post("/items", json={"name": "test", "price": -1})
        data = r.json()
        assert "detail" in data

    def test_create_item_price_error_detail_message(self):
        """Price error should have specific error message."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.json()["detail"] == "price must be > 0"

    def test_create_item_validation_error_is_dict(self):
        """Validation error response should be a dict."""
        r = client.post("/items", json={"name": "test"})
        data = r.json()
        assert isinstance(data, dict)

    def test_create_item_validation_error_has_detail(self):
        """Validation error should have detail information."""
        r = client.post("/items", json={})
        data = r.json()
        assert "detail" in data or "errors" in data or "msg" in data


class TestGetItemErrorResponseFormat:
    """Tests for error response format from GET /items/{item_id}."""

    def test_get_item_not_found_has_detail_field(self):
        """404 response should have detail field."""
        r = client.get("/items/99")
        data = r.json()
        assert "detail" in data

    def test_get_item_not_found_detail_message(self):
        """404 detail should have 'not found' message."""
        r = client.get("/items/999")
        assert r.json()["detail"] == "not found"

    def test_get_item_error_is_dict(self):
        """Error response should be a dict."""
        r = client.get("/items/2")
        assert isinstance(r.json(), dict)


class TestCreateItemResponseFields:
    """Tests for response field presence and types in POST /items."""

    def test_create_item_response_has_id(self):
        """Response must have id field."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert "id" in r.json()

    def test_create_item_response_has_name(self):
        """Response must have name field."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert "name" in r.json()

    def test_create_item_response_has_price(self):
        """Response must have price field."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert "price" in r.json()

    def test_create_item_response_id_is_integer(self):
        """Response id must be an integer."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        data = r.json()
        assert isinstance(data["id"], int)

    def test_create_item_response_name_is_string(self):
        """Response name must be a string."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        data = r.json()
        assert isinstance(data["name"], str)

    def test_create_item_response_price_is_number(self):
        """Response price must be a number."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        data = r.json()
        assert isinstance(data["price"], (int, float))


class TestGetItemResponseFields:
    """Tests for response field presence and types in GET /items/{item_id}."""

    def test_get_item_response_has_id(self):
        """Response must have id field."""
        r = client.get("/items/1")
        assert "id" in r.json()

    def test_get_item_response_has_name(self):
        """Response must have name field."""
        r = client.get("/items/1")
        assert "name" in r.json()

    def test_get_item_response_has_price(self):
        """Response must have price field."""
        r = client.get("/items/1")
        assert "price" in r.json()

    def test_get_item_response_id_is_integer(self):
        """Response id must be an integer."""
        r = client.get("/items/1")
        data = r.json()
        assert isinstance(data["id"], int)

    def test_get_item_response_name_is_string(self):
        """Response name must be a string."""
        r = client.get("/items/1")
        data = r.json()
        assert isinstance(data["name"], str)

    def test_get_item_response_price_is_number(self):
        """Response price must be a number."""
        r = client.get("/items/1")
        data = r.json()
        assert isinstance(data["price"], (int, float))

    def test_get_item_response_values_are_consistent(self):
        """GET /items/1 should always return same data."""
        r1 = client.get("/items/1")
        r2 = client.get("/items/1")
        assert r1.json() == r2.json()


class TestContentTypeHeaders:
    """Tests for response content-type headers."""

    def test_create_item_response_content_type(self):
        """POST /items response should be JSON."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert "application/json" in r.headers.get("content-type", "")

    def test_get_item_response_content_type(self):
        """GET /items/{item_id} response should be JSON."""
        r = client.get("/items/1")
        assert "application/json" in r.headers.get("content-type", "")

    def test_get_item_not_found_response_content_type(self):
        """404 response should be JSON."""
        r = client.get("/items/999")
        assert "application/json" in r.headers.get("content-type", "")

    def test_create_item_error_response_content_type(self):
        """Error response should be JSON."""
        r = client.post("/items", json={"name": "test", "price": -1})
        assert "application/json" in r.headers.get("content-type", "")


class TestResponseConsistency:
    """Tests for consistency of responses."""

    def test_create_item_success_response_complete(self):
        """Successful response should have all fields."""
        r = client.post("/items", json={"name": "complete", "price": 5.5})
        data = r.json()
        assert len(data) >= 3
        assert all(k in data for k in ["id", "name", "price"])

    def test_get_item_success_response_complete(self):
        """GET success response should have all fields."""
        r = client.get("/items/1")
        data = r.json()
        assert len(data) >= 3
        assert all(k in data for k in ["id", "name", "price"])

    def test_create_item_price_error_response_only_detail(self):
        """Price error should have detail field."""
        r = client.post("/items", json={"name": "test", "price": 0})
        data = r.json()
        assert isinstance(data, dict)
        assert "detail" in data

    def test_get_item_not_found_response_only_detail(self):
        """404 error should have detail field."""
        r = client.get("/items/999")
        data = r.json()
        assert isinstance(data, dict)
        assert "detail" in data
