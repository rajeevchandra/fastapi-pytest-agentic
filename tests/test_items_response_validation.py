"""
Comprehensive response structure and error handling tests for items endpoints.
Tests focus on validating response format, field types, and error consistency.
"""
from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)


class TestCreateItemResponseStructure:
    """Validate response structure for create item endpoint."""

    def test_create_item_response_has_all_required_fields(self):
        """Response should contain id, name, price fields."""
        r = client.post("/items", json={"name": "book", "price": 12.5})
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_create_item_response_field_types(self):
        """Response fields should have correct types."""
        r = client.post("/items", json={"name": "book", "price": 12.5})
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (float, int))

    def test_create_item_response_no_extra_fields(self):
        """Response should only contain id, name, price."""
        r = client.post("/items", json={"name": "book", "price": 12.5})
        data = r.json()
        assert set(data.keys()) == {"id", "name", "price"}

    def test_create_item_response_values_match_request(self):
        """Response name and price should match request."""
        r = client.post("/items", json={"name": "widget", "price": 9.99})
        data = r.json()
        assert data["name"] == "widget"
        assert data["price"] == 9.99

    def test_create_item_response_id_is_positive_integer(self):
        """Response id should be positive integer."""
        r = client.post("/items", json={"name": "test", "price": 1.0})
        data = r.json()
        assert data["id"] > 0
        assert isinstance(data["id"], int)


class TestCreateItemErrorResponses:
    """Validate error response format and content."""

    def test_error_response_has_detail_field(self):
        """Error responses should contain detail field."""
        r = client.post("/items", json={"name": "bad", "price": 0})
        data = r.json()
        assert "detail" in data

    def test_invalid_price_error_is_400(self):
        """Non-positive price should return 400."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.status_code == 400

    def test_invalid_price_error_message_contains_price(self):
        """Error detail should mention price."""
        r = client.post("/items", json={"name": "item", "price": 0})
        detail = r.json()["detail"].lower()
        assert "price" in detail

    def test_negative_price_error_is_400(self):
        """Negative price should return 400."""
        r = client.post("/items", json={"name": "item", "price": -1.0})
        assert r.status_code == 400

    def test_missing_name_field_returns_422(self):
        """Missing name field should return 422 validation error."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422

    def test_missing_price_field_returns_422(self):
        """Missing price field should return 422 validation error."""
        r = client.post("/items", json={"name": "item"})
        assert r.status_code == 422

    def test_invalid_json_returns_422(self):
        """Malformed JSON should return 422."""
        r = client.post("/items", content="{invalid json")
        assert r.status_code == 422

    def test_422_error_has_detail(self):
        """422 errors should have detail field."""
        r = client.post("/items", json={"price": 10.0})
        assert "detail" in r.json()


class TestGetItemResponseStructure:
    """Validate response structure for get item endpoint."""

    def test_get_item_response_has_all_required_fields(self):
        """GET response should contain id, name, price."""
        r = client.get("/items/1")
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_get_item_response_field_types(self):
        """GET response fields should have correct types."""
        r = client.get("/items/1")
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (float, int))

    def test_get_item_response_no_extra_fields(self):
        """GET response should only contain id, name, price."""
        r = client.get("/items/1")
        data = r.json()
        assert set(data.keys()) == {"id", "name", "price"}

    def test_get_item_response_id_matches_param(self):
        """Response id should match the requested item_id."""
        r = client.get("/items/1")
        assert r.json()["id"] == 1

    def test_get_item_success_returns_200(self):
        """Valid item_id should return 200."""
        r = client.get("/items/1")
        assert r.status_code == 200


class TestGetItemErrorResponses:
    """Validate error handling for get item endpoint."""

    def test_item_not_found_returns_404(self):
        """Non-existent item should return 404."""
        r = client.get("/items/2")
        assert r.status_code == 404

    def test_item_not_found_has_detail(self):
        """404 response should have detail field."""
        r = client.get("/items/2")
        assert "detail" in r.json()

    def test_item_not_found_detail_message(self):
        """404 detail should indicate not found."""
        r = client.get("/items/2")
        detail = r.json()["detail"].lower()
        assert "not found" in detail or "404" in detail

    def test_invalid_item_id_type_returns_error(self):
        """Non-integer item_id in path should return error."""
        r = client.get("/items/abc")
        assert r.status_code in [400, 422]

    def test_large_item_id_not_found(self):
        """Very large item_id should return 404."""
        r = client.get("/items/999999")
        assert r.status_code == 404

    def test_negative_item_id_not_found(self):
        """Negative item_id should return 404 (if accepted by parser)."""
        r = client.get("/items/-1")
        assert r.status_code == 404


class TestHealthEndpointResponseStructure:
    """Validate response structure for health endpoint."""

    def test_health_check_returns_200(self):
        """Health endpoint should return 200."""
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_check_has_status_field(self):
        """Health response should have status field."""
        data = client.get("/health").json()
        assert "status" in data

    def test_health_check_status_is_ok(self):
        """Health status should be ok."""
        data = client.get("/health").json()
        assert data["status"] == "ok"

    def test_health_check_returns_dict(self):
        """Health endpoint should return JSON object."""
        r = client.get("/health")
        assert isinstance(r.json(), dict)


class TestHTTPStatusCodes:
    """Parametrized tests for HTTP status codes."""

    @pytest.mark.parametrize("item_id,expected_status", [
        (1, 200),
        (2, 404),
        (999, 404),
    ])
    def test_get_item_status_codes(self, item_id, expected_status):
        """GET /items/{item_id} should return correct status."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == expected_status

    @pytest.mark.parametrize("name,price,expected_status", [
        ("book", 12.5, 200),
        ("pen", 1.0, 200),
        ("expensive", 999.99, 200),
        ("item", 0, 400),
        ("item", -1.0, 400),
    ])
    def test_create_item_status_codes(self, name, price, expected_status):
        """POST /items should return correct status."""
        r = client.post("/items", json={"name": name, "price": price})
        assert r.status_code == expected_status


class TestResponseContentTypes:
    """Validate response content types."""

    def test_create_item_returns_json(self):
        """POST /items should return JSON."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert r.headers["content-type"] == "application/json"

    def test_get_item_returns_json(self):
        """GET /items/{id} should return JSON."""
        r = client.get("/items/1")
        assert r.headers["content-type"] == "application/json"

    def test_health_check_returns_json(self):
        """GET /health should return JSON."""
        r = client.get("/health")
        assert r.headers["content-type"] == "application/json"

    def test_error_response_returns_json(self):
        """Error responses should return JSON."""
        r = client.get("/items/999")
        assert r.headers["content-type"] == "application/json"


class TestResponseConsistency:
    """Test consistency across multiple requests."""

    def test_multiple_creates_return_same_id(self):
        """Multiple create requests should return consistent id."""
        r1 = client.post("/items", json={"name": "item1", "price": 1.0})
        r2 = client.post("/items", json={"name": "item2", "price": 2.0})
        # Both should return same id (simplified API always returns 1)
        assert r1.json()["id"] == r2.json()["id"] == 1

    def test_get_existing_item_response_consistent(self):
        """Getting same item multiple times should return consistent data."""
        r1 = client.get("/items/1")
        r2 = client.get("/items/1")
        assert r1.json() == r2.json()

    def test_error_response_format_consistent(self):
        """Error responses should have consistent structure."""
        r1 = client.post("/items", json={"name": "item", "price": 0})
        r2 = client.post("/items", json={"name": "item", "price": -5})
        assert set(r1.json().keys()) == set(r2.json().keys())
        assert "detail" in r1.json()
        assert "detail" in r2.json()


class TestEdgeCaseResponses:
    """Test edge cases in response handling."""

    def test_very_small_price_is_valid(self):
        """Very small positive price should be valid."""
        r = client.post("/items", json={"name": "item", "price": 0.01})
        assert r.status_code == 200

    def test_very_large_price_is_valid(self):
        """Very large price should be valid."""
        r = client.post("/items", json={"name": "item", "price": 999999.99})
        assert r.status_code == 200

    def test_item_with_special_chars_name_is_valid(self):
        """Item name with special characters should be valid."""
        r = client.post("/items", json={"name": "item-_123!@#", "price": 1.0})
        assert r.status_code == 200

    def test_item_with_long_name_is_valid(self):
        """Item with very long name should be valid."""
        long_name = "a" * 1000
        r = client.post("/items", json={"name": long_name, "price": 1.0})
        assert r.status_code == 200

    def test_float_conversion_in_response(self):
        """Integer price should be converted to float in response."""
        r = client.post("/items", json={"name": "item", "price": 10})
        price = r.json()["price"]
        assert isinstance(price, (int, float))
        assert price == 10.0
