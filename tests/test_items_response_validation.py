import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemHTTPStatusCodes:
    """Test HTTP status codes from create_item endpoint."""

    def test_create_item_success_returns_200(self):
        """Successful item creation should return 200."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200

    @pytest.mark.parametrize("price", [-1, 0, -100])
    def test_create_item_invalid_price_returns_400(self, price):
        """Invalid price should return 400."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400

    def test_create_item_missing_field_returns_422(self):
        """Missing required field should return 422."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422


class TestCreateItemErrorResponse:
    """Test error response format from create_item endpoint."""

    def test_create_item_invalid_price_has_detail_message(self):
        """Error response should have detail message."""
        r = client.post("/items", json={"name": "test", "price": -1})
        assert r.status_code == 400
        data = r.json()
        assert "detail" in data
        assert data["detail"] == "price must be > 0"

    def test_create_item_invalid_price_detail_message_format(self):
        """Error message should be descriptive."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400
        data = r.json()
        assert isinstance(data["detail"], str)
        assert len(data["detail"]) > 0

    def test_create_item_missing_field_error_response_structure(self):
        """422 response should have error details."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422
        data = r.json()
        assert isinstance(data, dict)


class TestCreateItemContentType:
    """Test content type of create_item responses."""

    def test_create_item_response_content_type_json(self):
        """Response content type should be JSON."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")

    def test_create_item_error_response_content_type_json(self):
        """Error response content type should be JSON."""
        r = client.post("/items", json={"name": "test", "price": -1})
        assert r.status_code == 400
        assert "application/json" in r.headers.get("content-type", "")


class TestGetItemHTTPStatusCodes:
    """Test HTTP status codes from get_item endpoint."""

    def test_get_item_found_returns_200(self):
        """Getting existing item should return 200."""
        r = client.get("/items/1")
        assert r.status_code == 200

    @pytest.mark.parametrize("item_id", [2, 3, 100, 999])
    def test_get_item_not_found_returns_404(self, item_id):
        """Getting non-existent item should return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    def test_get_item_negative_id_returns_404(self):
        """Getting item with negative ID should return 404."""
        r = client.get("/items/-1")
        assert r.status_code == 404

    def test_get_item_zero_id_returns_404(self):
        """Getting item with ID 0 should return 404."""
        r = client.get("/items/0")
        assert r.status_code == 404


class TestGetItemErrorResponse:
    """Test error response format from get_item endpoint."""

    def test_get_item_not_found_has_detail_message(self):
        """404 response should have detail message."""
        r = client.get("/items/999")
        assert r.status_code == 404
        data = r.json()
        assert "detail" in data
        assert data["detail"] == "not found"

    def test_get_item_not_found_detail_message_format(self):
        """Error message should be descriptive."""
        r = client.get("/items/2")
        assert r.status_code == 404
        data = r.json()
        assert isinstance(data["detail"], str)
        assert len(data["detail"]) > 0


class TestGetItemResponseStructure:
    """Test response structure from get_item endpoint."""

    def test_get_item_response_has_required_fields(self):
        """Response should contain id, name, and price."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_get_item_response_id_type(self):
        """Response id should be an integer."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert isinstance(r.json()["id"], int)

    def test_get_item_response_name_type(self):
        """Response name should be a string."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert isinstance(r.json()["name"], str)

    def test_get_item_response_price_type(self):
        """Response price should be a number."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert isinstance(r.json()["price"], (int, float))

    def test_get_item_response_values_not_empty(self):
        """Response fields should have meaningful values."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1
        assert len(data["name"]) > 0
        assert data["price"] > 0


class TestGetItemContentType:
    """Test content type of get_item responses."""

    def test_get_item_response_content_type_json(self):
        """Response content type should be JSON."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")

    def test_get_item_not_found_response_content_type_json(self):
        """404 response content type should be JSON."""
        r = client.get("/items/999")
        assert r.status_code == 404
        assert "application/json" in r.headers.get("content-type", "")


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_returns_200(self):
        """Health check should return 200."""
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_response_has_status_field(self):
        """Health response should have status field."""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert "status" in data

    def test_health_response_status_is_ok(self):
        """Health response status should be 'ok'."""
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_health_response_content_type_json(self):
        """Health response content type should be JSON."""
        r = client.get("/health")
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")


class TestResponseConsistency:
    """Test consistency of responses across endpoints."""

    def test_all_success_responses_are_json(self):
        """All successful responses should be JSON."""
        endpoints = [
            ("GET", "/health"),
            ("GET", "/items/1"),
            ("POST", "/items", {"name": "test", "price": 10.0}),
        ]
        for method, path, *json_body in endpoints:
            if method == "GET":
                r = client.get(path)
            else:
                r = client.post(path, json=json_body[0] if json_body else None)
            if r.status_code == 200:
                assert "application/json" in r.headers.get("content-type", "")
                # Should be valid JSON
                assert isinstance(r.json(), dict)

    def test_all_error_responses_have_detail_field(self):
        """All error responses should have detail field."""
        error_cases = [
            ("POST", "/items", {"name": "test", "price": -1}, 400),
            ("GET", "/items/999", None, 404),
        ]
        for method, path, json_body, expected_status in error_cases:
            if method == "GET":
                r = client.get(path)
            else:
                r = client.post(path, json=json_body)
            assert r.status_code == expected_status
            assert "detail" in r.json()
