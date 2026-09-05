"""
Response Structure & Error Handling validation for all endpoints.

Tests comprehensive HTTP status codes, response formats, error consistency,
and complete response structure validation across all endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemHTTPStatusCodes:
    """Test HTTP status codes for POST /items endpoint."""

    def test_create_item_success_returns_200(self):
        """Test that successful creation returns 200 OK."""
        response = client.post("/items", json={"name": "test", "price": 10.0})
        assert response.status_code == 200

    def test_create_item_invalid_price_returns_400(self):
        """Test that zero price returns 400 Bad Request."""
        response = client.post("/items", json={"name": "test", "price": 0})
        assert response.status_code == 400

    @pytest.mark.parametrize("price", [-1, -100.5, -0.01])
    def test_create_item_negative_price_returns_400(self, price):
        """Test that negative prices return 400 Bad Request."""
        response = client.post("/items", json={"name": "test", "price": price})
        assert response.status_code == 400

    def test_create_item_missing_fields_returns_422(self):
        """Test that missing required fields returns 422 Unprocessable Entity."""
        response = client.post("/items", json={})
        assert response.status_code == 422

    def test_create_item_invalid_type_returns_422(self):
        """Test that invalid types return 422 Unprocessable Entity."""
        response = client.post("/items", json={"name": "test", "price": "invalid"})
        assert response.status_code == 422


class TestGetItemHTTPStatusCodes:
    """Test HTTP status codes for GET /items/{item_id} endpoint."""

    def test_get_item_found_returns_200(self):
        """Test that getting existing item returns 200 OK."""
        response = client.get("/items/1")
        assert response.status_code == 200

    def test_get_item_not_found_returns_404(self):
        """Test that getting non-existent item returns 404 Not Found."""
        response = client.get("/items/2")
        assert response.status_code == 404

    @pytest.mark.parametrize("item_id", [2, 3, 100, 999, 10000])
    def test_get_item_various_ids_not_found_returns_404(self, item_id):
        """Test that various non-existent IDs return 404."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == 404

    @pytest.mark.parametrize("item_id", [-1, -100])
    def test_get_item_negative_id_not_found_returns_404(self, item_id):
        """Test that negative IDs return 404 Not Found."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == 404


class TestErrorResponseStructure:
    """Test error response format and consistency."""

    def test_price_validation_error_has_detail(self):
        """Test that price validation error includes detail message."""
        response = client.post("/items", json={"name": "test", "price": 0})
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data, "Error response should have 'detail' field"

    def test_price_validation_error_message_is_string(self):
        """Test that error detail is a string."""
        response = client.post("/items", json={"name": "test", "price": 0})
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert isinstance(detail, str), "Error detail should be a string"

    def test_price_validation_error_message_content(self):
        """Test that error message contains helpful information."""
        response = client.post("/items", json={"name": "test", "price": 0})
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert "price" in detail.lower(), "Error should mention 'price'"
        assert "0" in detail or "positive" in detail.lower(), "Error should explain the constraint"

    def test_not_found_error_has_detail(self):
        """Test that 404 error includes detail message."""
        response = client.get("/items/999")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data, "Error response should have 'detail' field"

    def test_not_found_error_message_content(self):
        """Test that 404 error message mentions not found."""
        response = client.get("/items/999")
        assert response.status_code == 404
        detail = response.json()["detail"]
        assert "not found" in detail.lower(), "Error message should indicate item not found"

    def test_validation_error_has_detail_array(self):
        """Test that validation errors include detail as array."""
        response = client.post("/items", json={})
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data, "Validation error should have 'detail' field"
        # FastAPI returns list of validation errors
        detail = data["detail"]
        assert isinstance(detail, (list, str)), "Detail should be list or string"

    def test_validation_error_specifies_fields(self):
        """Test that validation errors indicate which field failed."""
        response = client.post("/items", json={"price": 10.0})  # missing name
        assert response.status_code == 422
        # Response should provide info about which field is missing
        response_text = str(response.json())
        assert "name" in response_text.lower(), "Should indicate 'name' field is missing"


class TestCreateItemResponseContentTypes:
    """Test response content type headers and JSON structure."""

    def test_create_item_response_content_type(self):
        """Test that response has correct content type."""
        response = client.post("/items", json={"name": "test", "price": 10.0})
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    def test_create_item_response_is_valid_json(self):
        """Test that response body is valid JSON."""
        response = client.post("/items", json={"name": "test", "price": 10.0})
        assert response.status_code == 200
        # If this doesn't raise an exception, JSON is valid
        data = response.json()
        assert data is not None

    def test_error_response_content_type(self):
        """Test that error responses also have correct content type."""
        response = client.post("/items", json={"name": "test", "price": 0})
        assert response.status_code == 400
        assert "application/json" in response.headers.get("content-type", "")

    def test_get_item_response_content_type(self):
        """Test that GET response has correct content type."""
        response = client.get("/items/1")
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")


class TestGetItemResponseStructure:
    """Test complete response structure for GET /items/{item_id}."""

    def test_get_item_response_has_required_fields(self):
        """Test that successful response contains all required fields."""
        response = client.get("/items/1")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data, "Response should have 'id' field"
        assert "name" in data, "Response should have 'name' field"
        assert "price" in data, "Response should have 'price' field"

    def test_get_item_response_field_types(self):
        """Test that response fields have correct types."""
        response = client.get("/items/1")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["id"], int), "id should be integer"
        assert isinstance(data["name"], str), "name should be string"
        assert isinstance(data["price"], (int, float)), "price should be numeric"

    def test_get_item_response_field_values(self):
        """Test that response contains expected values."""
        response = client.get("/items/1")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1, "id should be 1"
        assert data["name"] == "sample", "name should be 'sample'"
        assert data["price"] == 10.0, "price should be 10.0"

    def test_get_item_response_no_extra_fields(self):
        """Test that response has only expected fields."""
        response = client.get("/items/1")
        assert response.status_code == 200
        data = response.json()
        expected_fields = {"id", "name", "price"}
        actual_fields = set(data.keys())
        assert actual_fields == expected_fields, "Response should only have expected fields"


class TestMultipleCreateOperations:
    """Test multiple create operations and response consistency."""

    def test_multiple_create_operations_return_same_id(self):
        """Test that multiple create operations return the same id."""
        response1 = client.post("/items", json={"name": "item1", "price": 10.0})
        response2 = client.post("/items", json={"name": "item2", "price": 20.0})
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        id1 = response1.json()["id"]
        id2 = response2.json()["id"]
        # API currently returns id=1 for all creates
        assert id1 == id2, "Current API returns same ID for all creates"

    def test_multiple_create_operations_preserve_names(self):
        """Test that multiple creates return correct names."""
        response1 = client.post("/items", json={"name": "alpha", "price": 15.0})
        response2 = client.post("/items", json={"name": "beta", "price": 25.0})
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        assert response1.json()["name"] == "alpha"
        assert response2.json()["name"] == "beta"

    def test_multiple_create_operations_preserve_prices(self):
        """Test that multiple creates return correct prices."""
        test_prices = [10.5, 20.75, 30.99]
        
        for price in test_prices:
            response = client.post("/items", json={"name": "test", "price": price})
            assert response.status_code == 200
            assert response.json()["price"] == price


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check_returns_200(self):
        """Test that health endpoint returns 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_check_returns_ok_status(self):
        """Test that health endpoint returns status='ok'."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data, "Health response should have 'status' field"
        assert data["status"] == "ok", "Health status should be 'ok'"

    def test_health_check_is_json(self):
        """Test that health endpoint returns JSON."""
        response = client.get("/health")
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")
        data = response.json()
        assert data is not None


class TestErrorConsistency:
    """Test consistency of error handling across endpoints."""

    def test_all_errors_have_json_response(self):
        """Test that all error responses are valid JSON."""
        error_responses = [
            client.post("/items", json={"name": "test", "price": 0}),  # 400
            client.post("/items", json={}),  # 422
            client.get("/items/999"),  # 404
        ]
        
        for response in error_responses:
            assert response.status_code >= 400
            data = response.json()  # Should not raise
            assert data is not None

    def test_all_errors_have_detail_field(self):
        """Test that all error responses include detail field."""
        error_responses = [
            client.post("/items", json={"name": "test", "price": 0}),  # 400
            client.get("/items/999"),  # 404
        ]
        
        for response in error_responses:
            data = response.json()
            assert "detail" in data, f"Error {response.status_code} should have 'detail' field"
