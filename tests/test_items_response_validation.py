"""
Response structure and error handling validation for API endpoints.

Tests cover:
- Response field types and structure consistency
- HTTP status code verification
- Error response format consistency
- Edge cases for both success and error paths
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemHTTPStatusCodes:
    """Test HTTP status code responses for get_item endpoint."""

    @pytest.mark.parametrize("item_id", [1])
    def test_found_item_status_200(self, item_id):
        """Existing item should return 200."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 200

    @pytest.mark.parametrize("item_id", [2, 3, 100, 999, 0, -1])
    def test_missing_item_status_404(self, item_id):
        """Missing items should return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    def test_get_item_with_large_id(self):
        """Large item IDs should return 404 (not found)."""
        r = client.get(f"/items/{2**31 - 1}")
        assert r.status_code == 404


class TestGetItemResponseStructure:
    """Test response structure from get_item endpoint."""

    def test_success_response_has_required_fields(self):
        """Successful response should have id, name, price."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_success_response_no_extra_fields(self):
        """Successful response should only have expected fields."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        # Check no unexpected fields
        assert len(data) == 3
        assert set(data.keys()) == {"id", "name", "price"}

    def test_success_response_field_types(self):
        """Response fields should have correct types."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_success_response_values(self):
        """Success response should have consistent values."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1
        assert isinstance(data["name"], str)
        assert len(data["name"]) > 0
        assert data["price"] > 0


class TestGetItemErrorResponse:
    """Test error response format and content."""

    def test_not_found_returns_json(self):
        """Not found response should be valid JSON."""
        r = client.get("/items/999")
        assert r.status_code == 404
        assert r.headers.get("content-type") == "application/json"
        data = r.json()
        assert isinstance(data, dict)

    def test_not_found_has_detail_field(self):
        """Not found response should have detail field."""
        r = client.get("/items/999")
        assert r.status_code == 404
        data = r.json()
        assert "detail" in data

    def test_not_found_detail_message(self):
        """Not found detail message should be meaningful."""
        r = client.get("/items/999")
        assert r.status_code == 404
        detail = r.json()["detail"]
        assert isinstance(detail, str)
        assert len(detail) > 0

    def test_error_response_consistency(self):
        """Error response format should be consistent."""
        r1 = client.get("/items/2")
        r2 = client.get("/items/3")
        assert r1.status_code == r2.status_code == 404
        assert set(r1.json().keys()) == set(r2.json().keys())


class TestCreateItemHTTPStatusCodes:
    """Test HTTP status codes for create_item endpoint."""

    def test_success_status_200(self):
        """Valid creation should return 200."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200

    def test_price_validation_error_status_400(self):
        """Price validation error should return 400."""
        r = client.post("/items", json={"name": "test", "price": -1})
        assert r.status_code == 400

    def test_missing_required_field_status_422(self):
        """Missing required field should return 422."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422

    def test_invalid_json_status_422(self):
        """Invalid JSON should return 422."""
        r = client.post("/items", data="invalid", headers={"Content-Type": "application/json"})
        assert r.status_code == 422

    @pytest.mark.parametrize("price", [0, -0.5, -1000])
    def test_invalid_price_status_400(self, price):
        """Various invalid prices should return 400."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400


class TestCreateItemErrorResponse:
    """Test error response format for create_item."""

    def test_price_error_returns_json(self):
        """Price validation error should return JSON."""
        r = client.post("/items", json={"name": "test", "price": -5})
        assert r.status_code == 400
        assert r.headers.get("content-type") == "application/json"

    def test_price_error_has_detail(self):
        """Price error should have detail field."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400
        data = r.json()
        assert "detail" in data

    def test_price_error_message_content(self):
        """Price error message should mention price."""
        r = client.post("/items", json={"name": "test", "price": -10})
        assert r.status_code == 400
        detail = r.json()["detail"]
        assert "price" in detail.lower()

    def test_validation_error_has_detail(self):
        """Validation error (422) should have detail field."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data

    def test_validation_error_detail_is_list_or_string(self):
        """Validation error detail should be list or string."""
        r = client.post("/items", json={})
        assert r.status_code == 422
        detail = r.json()["detail"]
        assert isinstance(detail, (list, str))


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_status_200(self):
        """Health endpoint should return 200."""
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_response_structure(self):
        """Health response should have status field."""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert "status" in data

    def test_health_response_value(self):
        """Health status should be ok."""
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_health_response_content_type(self):
        """Health response should be JSON."""
        r = client.get("/health")
        assert r.headers.get("content-type") == "application/json"


class TestContentTypeHeaders:
    """Test Content-Type headers in responses."""

    def test_create_item_returns_json(self):
        """Create item response should have JSON content type."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        assert r.headers.get("content-type") == "application/json"

    def test_get_item_returns_json(self):
        """Get item response should have JSON content type."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.headers.get("content-type") == "application/json"

    def test_error_responses_return_json(self):
        """Error responses should have JSON content type."""
        test_cases = [
            (client.get("/items/999"), 404),
            (client.post("/items", json={"price": 10.0}), 422),
            (client.post("/items", json={"name": "test", "price": -1}), 400),
        ]
        for r, expected_status in test_cases:
            assert r.status_code == expected_status
            assert r.headers.get("content-type") == "application/json"


class TestResponseConsistency:
    """Test consistency across multiple requests."""

    def test_multiple_get_item_requests_consistent(self):
        """Multiple requests for same item should return same data."""
        responses = [client.get("/items/1") for _ in range(3)]
        data_list = [r.json() for r in responses]
        assert all(d == data_list[0] for d in data_list)

    def test_multiple_create_requests_same_response(self):
        """Creating items returns consistent structure."""
        r1 = client.post("/items", json={"name": "item1", "price": 10.0})
        r2 = client.post("/items", json={"name": "item2", "price": 20.0})
        assert r1.status_code == r2.status_code == 200
        assert set(r1.json().keys()) == set(r2.json().keys())

    def test_error_responses_consistent(self):
        """Error responses should have consistent format."""
        errors = [
            client.get("/items/2"),
            client.get("/items/3"),
            client.get("/items/100"),
        ]
        for r in errors:
            assert r.status_code == 404
            assert "detail" in r.json()
            assert len(r.json()) == 1
