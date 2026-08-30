"""
Response structure and error handling tests for the items API.
Tests HTTP status codes, response formats, error consistency, and headers.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemHTTPStatusCodes:
    """Test HTTP status codes for POST /items endpoint."""

    def test_create_item_success_returns_200(self):
        """Successful item creation returns 200 OK."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert r.status_code == 200

    def test_create_item_price_error_returns_400(self):
        """Price validation error returns 400 Bad Request."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.status_code == 400

    def test_create_item_negative_price_returns_400(self):
        """Negative price returns 400 Bad Request."""
        r = client.post("/items", json={"name": "item", "price": -5.0})
        assert r.status_code == 400

    def test_create_item_missing_field_returns_422(self):
        """Missing required field returns 422 Unprocessable Entity."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422

    def test_create_item_invalid_type_returns_422(self):
        """Invalid field type returns 422 Unprocessable Entity."""
        r = client.post("/items", json={"name": "item", "price": "invalid"})
        assert r.status_code == 422


class TestGetItemHTTPStatusCodes:
    """Test HTTP status codes for GET /items/{item_id} endpoint."""

    def test_get_item_success_returns_200(self):
        """Getting existing item returns 200 OK."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_get_item_not_found_returns_404(self):
        """Getting non-existent item returns 404 Not Found."""
        r = client.get("/items/2")
        assert r.status_code == 404

    def test_get_item_negative_id_returns_404(self):
        """Getting item with negative ID returns 404."""
        r = client.get("/items/-1")
        assert r.status_code == 404

    def test_get_item_large_id_returns_404(self):
        """Getting item with large ID returns 404."""
        r = client.get("/items/9999")
        assert r.status_code == 404

    def test_get_item_zero_id_returns_404(self):
        """Getting item with ID 0 returns 404."""
        r = client.get("/items/0")
        assert r.status_code == 404


class TestCreateItemResponseFormat:
    """Test response JSON format for POST /items endpoint."""

    def test_create_item_response_is_json(self):
        """Response body is valid JSON."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/json"
        data = r.json()
        assert isinstance(data, dict)

    def test_create_item_response_contains_id(self):
        """Response includes 'id' field."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert r.status_code == 200
        assert "id" in r.json()

    def test_create_item_response_id_is_integer(self):
        """Response 'id' field is integer."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert r.status_code == 200
        assert isinstance(r.json()["id"], int)

    def test_create_item_response_name_matches_request(self):
        """Response name field matches request name."""
        name = "test-product"
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_create_item_response_price_matches_request(self):
        """Response price field matches request price."""
        price = 15.75
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    @pytest.mark.parametrize("name,price", [
        ("book", 9.99),
        ("pen", 1.50),
        ("notebook", 5.0),
    ])
    def test_create_item_response_fields_match_input(self, name, price):
        """Response fields match input values."""
        r = client.post("/items", json={"name": name, "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name
        assert data["price"] == price


class TestGetItemResponseFormat:
    """Test response JSON format for GET /items/{item_id} endpoint."""

    def test_get_item_response_is_json(self):
        """Response body is valid JSON."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/json"
        data = r.json()
        assert isinstance(data, dict)

    def test_get_item_response_contains_id(self):
        """Response includes 'id' field."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert "id" in r.json()

    def test_get_item_response_contains_name(self):
        """Response includes 'name' field."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert "name" in r.json()

    def test_get_item_response_contains_price(self):
        """Response includes 'price' field."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert "price" in r.json()

    def test_get_item_response_fields_are_correct_types(self):
        """Response fields have correct types."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))


class TestErrorResponseFormat:
    """Test error response format consistency."""

    def test_price_error_contains_detail_field(self):
        """400 error response contains 'detail' field."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.status_code == 400
        assert "detail" in r.json()

    def test_validation_error_contains_detail_field(self):
        """422 error response contains 'detail' field."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422
        assert "detail" in r.json()

    def test_not_found_error_contains_detail_field(self):
        """404 error response contains 'detail' field."""
        r = client.get("/items/999")
        assert r.status_code == 404
        assert "detail" in r.json()

    def test_price_error_detail_is_string(self):
        """Error detail field is a string."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.status_code == 400
        assert isinstance(r.json()["detail"], str)

    def test_not_found_error_message_content(self):
        """404 error message indicates 'not found'."""
        r = client.get("/items/999")
        assert r.status_code == 404
        detail = r.json()["detail"]
        assert "not found" in detail.lower()

    def test_price_error_message_mentions_price(self):
        """400 error message mentions 'price'."""
        r = client.post("/items", json={"name": "item", "price": -1})
        assert r.status_code == 400
        detail = r.json()["detail"]
        assert "price" in detail.lower()


class TestContentType:
    """Test content-type headers."""

    def test_create_item_response_content_type(self):
        """POST response has application/json content type."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.headers["content-type"] == "application/json"

    def test_get_item_response_content_type(self):
        """GET response has application/json content type."""
        r = client.get("/items/1")
        assert r.headers["content-type"] == "application/json"

    def test_error_response_content_type(self):
        """Error response has application/json content type."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.headers["content-type"] == "application/json"


class TestResponseConsistency:
    """Test response consistency across multiple requests."""

    def test_repeated_get_same_item_same_response(self):
        """Repeated GET requests for same item return consistent data."""
        r1 = client.get("/items/1")
        r2 = client.get("/items/1")
        assert r1.json() == r2.json()

    def test_multiple_404s_consistent(self):
        """Multiple 404 responses are consistent."""
        r1 = client.get("/items/999")
        r2 = client.get("/items/999")
        assert r1.status_code == r2.status_code == 404
        assert r1.json()["detail"] == r2.json()["detail"]

    def test_price_validation_error_consistent(self):
        """Price validation error is consistent across calls."""
        r1 = client.post("/items", json={"name": "item", "price": 0})
        r2 = client.post("/items", json={"name": "item", "price": 0})
        assert r1.status_code == r2.status_code == 400
        assert r1.json()["detail"] == r2.json()["detail"]

    @pytest.mark.parametrize("invalid_price", [-1, -100, 0])
    def test_negative_price_error_consistent(self, invalid_price):
        """Negative/zero price errors are consistent."""
        r1 = client.post("/items", json={"name": "item", "price": invalid_price})
        r2 = client.post("/items", json={"name": "item", "price": invalid_price})
        assert r1.status_code == r2.status_code == 400
        assert r1.json() == r2.json()


class TestHTTPHeaders:
    """Test HTTP response headers."""

    def test_response_has_content_length(self):
        """Response includes content-length header."""
        r = client.get("/items/1")
        assert "content-length" in r.headers or r.status_code in [204, 304]

    def test_success_response_is_200_or_2xx(self):
        """Success responses are in 2xx range."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert 200 <= r.status_code < 300

    def test_error_response_is_4xx_or_5xx(self):
        """Error responses are in 4xx or 5xx range."""
        r = client.get("/items/999")
        assert 400 <= r.status_code < 600
