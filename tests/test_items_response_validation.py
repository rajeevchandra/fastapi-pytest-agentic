"""
Response validation and HTTP status code tests for all endpoints.
Ensures correct response structure, status codes, and error handling.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemResponseStructure:
    """Validate response structure for POST /items."""

    def test_successful_response_structure(self):
        """Successful POST should return item with id, name, price."""
        r = client.post("/items", json={"name": "widget", "price": 25.0})
        data = r.json()
        assert set(data.keys()) >= {"id", "name", "price"}
        assert data["id"] is not None
        assert data["name"] == "widget"
        assert data["price"] == 25.0

    def test_error_response_structure(self):
        """Error response should have detail field."""
        r = client.post("/items", json={"name": "bad", "price": 0})
        data = r.json()
        assert "detail" in data


class TestHealthEndpoint:
    """Test the health check endpoint."""

    def test_health_returns_200(self):
        """GET /health should return 200."""
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_returns_status_ok(self):
        """GET /health should return status: ok."""
        r = client.get("/health")
        data = r.json()
        assert data.get("status") == "ok"


class TestCreateItemHTTPStatusCodes:
    """Test HTTP status codes for POST /items."""

    @pytest.mark.parametrize("name,price,expected_status", [
        ("valid item", 10.0, 200),
        ("another item", 99.99, 200),
        ("test", 0.01, 200),
        ("zero price", 0, 400),
        ("negative price", -5.0, 400),
    ])
    def test_post_status_codes(self, name, price, expected_status):
        """POST should return correct status codes."""
        r = client.post("/items", json={"name": name, "price": price})
        assert r.status_code == expected_status


class TestGetItemHTTPStatusCodes:
    """Test HTTP status codes for GET /items/{item_id}."""

    @pytest.mark.parametrize("item_id,expected_status", [
        (1, 200),
        (2, 404),
        (0, 404),
        (999, 404),
    ])
    def test_get_status_codes(self, item_id, expected_status):
        """GET should return correct status codes."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == expected_status


class TestGetItemResponseStructure:
    """Validate response structure for GET /items/{item_id}."""

    def test_found_response_structure(self):
        """Successful GET should return item with id, name, price."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_not_found_response_structure(self):
        """404 GET should have error detail."""
        r = client.get("/items/2")
        assert r.status_code == 404
        data = r.json()
        assert "detail" in data
        assert "not found" in data["detail"]


class TestContentType:
    """Test response content types."""

    def test_post_returns_json(self):
        """POST response should be JSON."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert "application/json" in r.headers.get("content-type", "")

    def test_get_returns_json(self):
        """GET response should be JSON."""
        r = client.get("/items/1")
        assert "application/json" in r.headers.get("content-type", "")

    def test_health_returns_json(self):
        """Health response should be JSON."""
        r = client.get("/health")
        assert "application/json" in r.headers.get("content-type", "")


class TestErrorMessages:
    """Validate error message content and consistency."""

    def test_price_validation_error_message(self):
        """Price validation error should have clear message."""
        r = client.post("/items", json={"name": "test", "price": -1})
        data = r.json()
        assert "price" in data["detail"].lower()
        assert "0" in data["detail"]

    def test_item_not_found_error_message(self):
        """Not found error should indicate item not found."""
        r = client.get("/items/999")
        data = r.json()
        assert "not found" in data["detail"].lower()


class TestPydanticValidationErrors:
    """Test Pydantic validation error responses (422)."""

    def test_invalid_json_type_price(self):
        """Non-numeric price should return 422."""
        r = client.post("/items", json={"name": "test", "price": "abc"})
        assert r.status_code == 422

    def test_missing_required_field_name(self):
        """Missing name should return 422."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422

    def test_missing_required_field_price(self):
        """Missing price should return 422."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422

    def test_null_required_field(self):
        """Null price should return 422."""
        r = client.post("/items", json={"name": "test", "price": None})
        assert r.status_code == 422


class TestResponseConsistency:
    """Ensure response consistency across requests."""

    def test_multiple_valid_posts_have_consistent_structure(self):
        """Multiple valid POSTs should have consistent response structure."""
        r1 = client.post("/items", json={"name": "item1", "price": 10.0})
        r2 = client.post("/items", json={"name": "item2", "price": 20.0})
        
        keys1 = set(r1.json().keys())
        keys2 = set(r2.json().keys())
        assert keys1 == keys2

    def test_get_response_consistent_with_post(self):
        """GET response should have same structure as POST response."""
        post_r = client.post("/items", json={"name": "test", "price": 10.0})
        get_r = client.get("/items/1")
        
        post_keys = set(post_r.json().keys())
        get_keys = set(get_r.json().keys())
        assert post_keys == get_keys
