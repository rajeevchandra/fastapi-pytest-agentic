"""
Response structure and error handling tests.
Validates HTTP status codes, response formats, and error messages.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemResponseValidation:
    """Tests for POST /items response validation."""
    
    def test_create_item_success_response_status(self):
        """Test successful item creation returns 200."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
    
    def test_create_item_error_response_status(self):
        """Test invalid price returns 400."""
        r = client.post("/items", json={"name": "test", "price": -5})
        assert r.status_code == 400
    
    def test_create_item_validation_error_status(self):
        """Test missing fields return 422."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422


class TestHTTPStatusCodes:
    """Tests for HTTP status codes across all endpoints."""
    
    @pytest.mark.parametrize("method,endpoint,body,expected_status", [
        ("POST", "/items", {"name": "valid", "price": 10.0}, 200),
        ("POST", "/items", {"name": "invalid", "price": 0}, 400),
        ("POST", "/items", {"name": "test"}, 422),
        ("GET", "/items/1", None, 200),
        ("GET", "/items/2", None, 404),
        ("GET", "/items/999", None, 404),
        ("GET", "/health", None, 200),
    ])
    def test_http_status_codes(self, method, endpoint, body, expected_status):
        """Test HTTP status codes for various endpoints and inputs."""
        if method == "POST":
            r = client.post(endpoint, json=body)
        else:
            r = client.get(endpoint)
        assert r.status_code == expected_status


class TestErrorResponseFormat:
    """Tests for error response structure and format."""
    
    def test_price_error_has_detail_field(self):
        """Test price error response includes detail field."""
        r = client.post("/items", json={"name": "test", "price": -1})
        assert r.status_code == 400
        data = r.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)
    
    def test_price_error_message_content(self):
        """Test price error message is clear and specific."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"
    
    def test_not_found_error_has_detail_field(self):
        """Test 404 error response includes detail field."""
        r = client.get("/items/999")
        assert r.status_code == 404
        data = r.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)
    
    def test_not_found_error_message_content(self):
        """Test 404 error message is clear."""
        r = client.get("/items/2")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"
    
    def test_validation_error_response_format(self):
        """Test 422 validation error has proper format."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data


class TestResponseContentType:
    """Tests for response content types."""
    
    def test_post_items_response_is_json(self):
        """Test POST /items returns JSON content."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("application/json")
    
    def test_get_items_response_is_json(self):
        """Test GET /items/{id} returns JSON content."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("application/json")
    
    def test_health_response_is_json(self):
        """Test GET /health returns JSON content."""
        r = client.get("/health")
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("application/json")
    
    def test_error_response_is_json(self):
        """Test error responses are JSON."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400
        assert r.headers["content-type"].startswith("application/json")


class TestGetItemResponseStructure:
    """Tests for GET /items/{item_id} response structure."""
    
    def test_get_item_found_response_fields(self):
        """Test successful GET /items/1 returns all fields."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data
        assert data["id"] == 1
    
    def test_get_item_found_field_types(self):
        """Test GET /items/1 response field types."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))
    
    def test_get_item_not_found_response_has_detail(self):
        """Test GET /items/404 returns detail in error."""
        r = client.get("/items/404")
        assert r.status_code == 404
        data = r.json()
        assert "detail" in data
