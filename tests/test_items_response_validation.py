"""Test response structure and error handling for endpoints."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemHTTPStatusCodes:
    """Test HTTP status codes for get_item endpoint."""

    @pytest.mark.parametrize("item_id", [1])
    def test_get_item_found_returns_200(self, item_id):
        """Test that existing item returns 200."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == 200

    @pytest.mark.parametrize("item_id", [2, 0, -1, 999, 100000])
    def test_get_item_not_found_returns_404(self, item_id):
        """Test that non-existent items return 404."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == 404

    def test_get_item_returns_json_content_type(self):
        """Test that response has JSON content type."""
        response = client.get("/items/1")
        assert response.headers["content-type"] == "application/json"

    def test_get_item_404_returns_json_error(self):
        """Test that 404 response contains JSON error."""
        response = client.get("/items/999")
        assert response.status_code == 404
        assert response.headers["content-type"] == "application/json"


class TestGetItemResponseStructure:
    """Test response structure for successful get_item."""

    def test_get_item_response_has_required_fields(self):
        """Test that response contains all expected fields."""
        response = client.get("/items/1")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_get_item_response_field_types(self):
        """Test that response fields have correct types."""
        response = client.get("/items/1")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_get_item_response_no_extra_fields(self):
        """Test that response contains only expected fields."""
        response = client.get("/items/1")
        assert response.status_code == 200
        data = response.json()
        assert set(data.keys()) == {"id", "name", "price"}

    def test_get_item_response_is_dict_not_list(self):
        """Test that response is a dictionary, not a list."""
        response = client.get("/items/1")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


class TestGetItemSuccessResponse:
    """Test success response content for get_item."""

    def test_get_item_returns_correct_id(self):
        """Test that retrieved item has correct id."""
        response = client.get("/items/1")
        assert response.status_code == 200
        assert response.json()["id"] == 1

    def test_get_item_returns_correct_name(self):
        """Test that retrieved item has correct name."""
        response = client.get("/items/1")
        assert response.status_code == 200
        assert response.json()["name"] == "sample"

    def test_get_item_returns_correct_price(self):
        """Test that retrieved item has correct price."""
        response = client.get("/items/1")
        assert response.status_code == 200
        assert response.json()["price"] == 10.0

    def test_get_item_price_is_float(self):
        """Test that price is returned as float."""
        response = client.get("/items/1")
        assert response.status_code == 200
        price = response.json()["price"]
        assert isinstance(price, float)
        assert price == 10.0

    def test_get_item_name_is_string(self):
        """Test that name is returned as string."""
        response = client.get("/items/1")
        assert response.status_code == 200
        name = response.json()["name"]
        assert isinstance(name, str)
        assert name == "sample"


class TestErrorResponseFormat:
    """Test error response format consistency."""

    def test_error_response_has_detail_field(self):
        """Test that error responses have detail field."""
        # Test 404 error
        response = client.get("/items/999")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_error_response_detail_is_string(self):
        """Test that error detail is a string."""
        response = client.get("/items/999")
        assert response.status_code == 404
        detail = response.json()["detail"]
        assert isinstance(detail, str)

    def test_price_validation_error_has_detail(self):
        """Test that price validation errors have detail field."""
        response = client.post("/items", json={"name": "item", "price": 0})
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

    def test_missing_field_error_has_detail(self):
        """Test that validation errors for missing fields have detail."""
        response = client.post("/items", json={"price": 10})
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_error_response_consistent_format(self):
        """Test that all error responses follow same structure."""
        # 404 error
        response_404 = client.get("/items/999")
        assert response_404.status_code == 404
        assert isinstance(response_404.json(), dict)
        assert "detail" in response_404.json()

        # 400 error
        response_400 = client.post("/items", json={"name": "bad", "price": -5})
        assert response_400.status_code == 400
        assert isinstance(response_400.json(), dict)
        assert "detail" in response_400.json()


class TestGetItemNotFoundErrorMessage:
    """Test specific error messages for not found scenarios."""

    def test_get_item_404_error_message(self):
        """Test that 404 error has correct message."""
        response = client.get("/items/2")
        assert response.status_code == 404
        assert response.json()["detail"] == "not found"

    def test_get_item_large_id_404_error(self):
        """Test 404 for large item ID."""
        response = client.get("/items/999999")
        assert response.status_code == 404
        assert response.json()["detail"] == "not found"

    def test_get_item_zero_id_404_error(self):
        """Test 404 for item ID 0."""
        response = client.get("/items/0")
        assert response.status_code == 404
        assert response.json()["detail"] == "not found"

    def test_get_item_negative_id_404_error(self):
        """Test 404 for negative item ID."""
        response = client.get("/items/-1")
        assert response.status_code == 404
        assert response.json()["detail"] == "not found"


class TestCreateItemErrorMessages:
    """Test specific error messages for create_item validation errors."""

    def test_price_validation_error_message(self):
        """Test that price validation error has correct message."""
        response = client.post("/items", json={"name": "book", "price": 0})
        assert response.status_code == 400
        assert response.json()["detail"] == "price must be > 0"

    def test_negative_price_error_message(self):
        """Test error message for negative price."""
        response = client.post("/items", json={"name": "item", "price": -10})
        assert response.status_code == 400
        assert response.json()["detail"] == "price must be > 0"

    def test_zero_price_error_message(self):
        """Test error message specifically for zero price."""
        response = client.post("/items", json={"name": "free", "price": 0})
        assert response.status_code == 400
        assert "price must be > 0" in response.json()["detail"]


class TestHealthEndpointResponse:
    """Test health check endpoint response structure."""

    def test_health_endpoint_returns_200(self):
        """Test that health endpoint returns 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_endpoint_returns_json(self):
        """Test that health endpoint returns JSON."""
        response = client.get("/health")
        assert response.headers["content-type"] == "application/json"

    def test_health_endpoint_response_structure(self):
        """Test health endpoint response structure."""
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert isinstance(data["status"], str)

    def test_health_endpoint_response_value(self):
        """Test health endpoint returns correct status."""
        response = client.get("/health")
        assert response.json() == {"status": "ok"}

    def test_health_endpoint_status_is_ok(self):
        """Test that health status is 'ok'."""
        response = client.get("/health")
        assert response.json()["status"] == "ok"


class TestResponseConsistency:
    """Test response consistency across multiple calls."""

    def test_repeated_get_item_calls_return_same_response(self):
        """Test that repeated calls return same response."""
        response1 = client.get("/items/1")
        response2 = client.get("/items/1")
        assert response1.json() == response2.json()

    def test_repeated_create_item_calls_return_consistent_id(self):
        """Test that repeated create calls always return id=1."""
        response1 = client.post("/items", json={"name": "item1", "price": 5})
        response2 = client.post("/items", json={"name": "item2", "price": 10})
        # Both should have id=1 (API always returns id=1)
        assert response1.json()["id"] == 1
        assert response2.json()["id"] == 1

    def test_repeated_health_calls_consistent(self):
        """Test that health endpoint returns consistent response."""
        responses = [client.get("/health").json() for _ in range(3)]
        assert all(r == {"status": "ok"} for r in responses)


class TestResponseHeaders:
    """Test response headers for various endpoints."""

    def test_success_response_has_content_type(self):
        """Test that success responses have content type header."""
        response = client.get("/health")
        assert "content-type" in response.headers

    def test_error_response_has_content_type(self):
        """Test that error responses have content type header."""
        response = client.get("/items/999")
        assert "content-type" in response.headers
        assert "application/json" in response.headers["content-type"]

    def test_post_response_has_content_type(self):
        """Test that POST responses have content type header."""
        response = client.post("/items", json={"name": "item", "price": 10})
        assert "content-type" in response.headers
        assert "application/json" in response.headers["content-type"]

    def test_validation_error_has_content_type(self):
        """Test that validation error responses have content type."""
        response = client.post("/items", json={"price": 10})  # Missing name
        assert "content-type" in response.headers
