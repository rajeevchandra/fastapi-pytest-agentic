"""
Response structure and error handling tests for /items endpoints.

Tests cover:
- Complete response structure validation for all endpoints
- HTTP status codes and error responses
- Response headers and content types
- Error message consistency
- All HTTP methods validation
- Response field presence and types
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemResponseValidation:
    """Test /items POST response structure and validation."""

    def test_success_response_has_all_fields(self):
        """Verify successful response includes all required fields."""
        response = client.post("/items", json={"name": "book", "price": 10.0})
        assert response.status_code == 200
        data = response.json()
        
        # Check all fields exist
        required_fields = {"id", "name", "price"}
        assert required_fields.issubset(set(data.keys()))
        
        # Check no unexpected fields
        assert len(data) == 3

    def test_success_response_field_types(self):
        """Verify response field types are correct."""
        response = client.post("/items", json={"name": "test", "price": 15.5})
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        # Price could be int or float
        assert isinstance(data["price"], (int, float))

    def test_response_id_is_positive_integer(self):
        """Verify response id is a positive integer."""
        response = client.post("/items", json={"name": "test", "price": 10.0})
        data = response.json()
        
        assert data["id"] > 0
        assert isinstance(data["id"], int)

    def test_response_preserves_exact_input_values(self):
        """Verify response values match input exactly."""
        test_cases = [
            ("apple", 0.99),
            ("Special Book!", 49.95),
            ("Item #123", 199.99),
            ("名前", 9.99),
        ]
        
        for name, price in test_cases:
            response = client.post("/items", json={"name": name, "price": price})
            data = response.json()
            assert data["name"] == name
            assert data["price"] == price

    def test_response_json_format_valid(self):
        """Verify response is valid JSON."""
        response = client.post("/items", json={"name": "test", "price": 10.0})
        assert response.status_code == 200
        
        # If json() succeeds, the response is valid JSON
        data = response.json()
        assert data is not None
        assert isinstance(data, dict)

    @pytest.mark.parametrize("price", [1.0, 10.5, 100.99, 999.99])
    def test_success_response_with_various_prices(self, price):
        """Test response structure with various price values."""
        response = client.post("/items", json={"name": "item", "price": price})
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "item"
        assert data["price"] == price

    def test_multiple_creations_response_consistency(self):
        """Verify response structure is consistent across multiple requests."""
        for i in range(3):
            response = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            assert response.status_code == 200
            
            data = response.json()
            assert "id" in data
            assert "name" in data
            assert "price" in data
            assert len(data) == 3


class TestErrorResponse:
    """Test error response structure and messages."""

    def test_error_response_is_json(self):
        """Verify error responses are valid JSON."""
        response = client.post("/items", json={"name": "test", "price": 0})
        assert response.status_code == 400
        
        # Should be valid JSON
        data = response.json()
        assert isinstance(data, dict)

    def test_error_response_has_detail_field(self):
        """Verify error responses include detail field."""
        response = client.post("/items", json={"name": "test", "price": -1})
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data

    def test_error_message_clarity(self):
        """Verify error messages are clear and specific."""
        response = client.post("/items", json={"name": "test", "price": 0})
        data = response.json()
        
        # Message should explain the problem
        assert "price" in data["detail"].lower()
        assert "0" in data["detail"] or "positive" in data["detail"].lower()

    @pytest.mark.parametrize("price", [0, -1, -100])
    def test_error_message_consistency(self, price):
        """Verify error message is consistent for all invalid prices."""
        response = client.post("/items", json={"name": "test", "price": price})
        assert response.status_code == 400
        
        data = response.json()
        # Should be the same message for all price <= 0
        assert data["detail"] == "price must be > 0"

    def test_validation_error_422_status_code(self):
        """Test that validation errors return 422."""
        # Missing required field
        response = client.post("/items", json={"price": 10.0})
        assert response.status_code == 422

    def test_validation_error_includes_error_details(self):
        """Test validation error response structure."""
        response = client.post("/items", json={"price": 10.0})
        assert response.status_code == 422
        
        data = response.json()
        # FastAPI returns detail array for validation errors
        assert "detail" in data

    def test_multiple_validation_errors_response(self):
        """Test response when multiple fields are invalid."""
        response = client.post("/items", json={})
        assert response.status_code == 422
        
        data = response.json()
        assert "detail" in data

    def test_type_error_response_structure(self):
        """Test response for type validation errors."""
        response = client.post("/items", json={"name": "test", "price": "invalid"})
        assert response.status_code == 422
        
        data = response.json()
        assert "detail" in data


class TestHTTPStatusCodes:
    """Test correct HTTP status codes for different scenarios."""

    def test_successful_post_returns_200(self):
        """Verify successful POST returns 200 OK."""
        response = client.post("/items", json={"name": "test", "price": 10.0})
        assert response.status_code == 200

    def test_invalid_price_returns_400(self):
        """Verify business logic errors return 400."""
        response = client.post("/items", json={"name": "test", "price": 0})
        assert response.status_code == 400

    def test_missing_required_field_returns_422(self):
        """Verify validation errors return 422."""
        response = client.post("/items", json={"name": "test"})
        assert response.status_code == 422

    def test_type_mismatch_returns_422(self):
        """Verify type validation errors return 422."""
        response = client.post("/items", json={"name": "test", "price": "not-a-number"})
        assert response.status_code == 422

    def test_get_existing_item_returns_200(self):
        """Verify GET for existing item returns 200."""
        response = client.get("/items/1")
        assert response.status_code == 200

    def test_get_nonexistent_item_returns_404(self):
        """Verify GET for non-existent item returns 404."""
        response = client.get("/items/999")
        assert response.status_code == 404

    def test_health_check_returns_200(self):
        """Verify health endpoint returns 200."""
        response = client.get("/health")
        assert response.status_code == 200


class TestGetItemResponseValidation:
    """Test /items/{item_id} GET response structure."""

    def test_get_item_success_response_has_all_fields(self):
        """Verify successful GET includes all fields."""
        response = client.get("/items/1")
        assert response.status_code == 200
        
        data = response.json()
        required_fields = {"id", "name", "price"}
        assert required_fields.issubset(set(data.keys()))

    def test_get_item_success_response_field_types(self):
        """Verify GET response field types."""
        response = client.get("/items/1")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_get_item_known_values(self):
        """Verify GET returns expected hardcoded values."""
        response = client.get("/items/1")
        data = response.json()
        
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0

    def test_get_item_response_is_json(self):
        """Verify GET response is valid JSON."""
        response = client.get("/items/1")
        assert response.status_code == 200
        
        # json() succeeds means valid JSON
        data = response.json()
        assert isinstance(data, dict)

    def test_get_item_404_error_response(self):
        """Test GET 404 error response structure."""
        response = client.get("/items/2")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "not found"

    def test_get_item_404_message_clarity(self):
        """Verify 404 error message is clear."""
        response = client.get("/items/999")
        data = response.json()
        
        assert "not found" in data["detail"].lower()

    @pytest.mark.parametrize("item_id", [1, 2, 100, 999])
    def test_get_item_various_ids(self, item_id):
        """Test GET with various item IDs."""
        response = client.get(f"/items/{item_id}")
        
        if item_id == 1:
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
        else:
            assert response.status_code == 404
            data = response.json()
            assert data["detail"] == "not found"


class TestHealthEndpointResponse:
    """Test /health endpoint response."""

    def test_health_response_structure(self):
        """Verify health endpoint response structure."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data

    def test_health_response_value(self):
        """Verify health endpoint returns correct status."""
        response = client.get("/health")
        data = response.json()
        
        assert data["status"] == "ok"

    def test_health_response_type(self):
        """Verify health response field types."""
        response = client.get("/health")
        data = response.json()
        
        assert isinstance(data["status"], str)

    def test_health_endpoint_consistency(self):
        """Verify health endpoint is consistent across calls."""
        for _ in range(3):
            response = client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "ok"


class TestResponseContentType:
    """Test response content-type headers."""

    def test_post_response_content_type_json(self):
        """Verify POST response has JSON content-type."""
        response = client.post("/items", json={"name": "test", "price": 10.0})
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type

    def test_get_response_content_type_json(self):
        """Verify GET response has JSON content-type."""
        response = client.get("/items/1")
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type

    def test_health_response_content_type_json(self):
        """Verify health response has JSON content-type."""
        response = client.get("/health")
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type

    def test_error_response_content_type_json(self):
        """Verify error responses have JSON content-type."""
        response = client.post("/items", json={"name": "test", "price": 0})
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type

    def test_validation_error_content_type_json(self):
        """Verify validation error responses have JSON content-type."""
        response = client.post("/items", json={"price": 10.0})
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type


class TestHTTPMethods:
    """Test that endpoints only accept correct HTTP methods."""

    def test_health_post_not_allowed(self):
        """Verify POST to /health is not allowed."""
        # FastAPI by default returns 405 or 422 depending on config
        response = client.post("/health")
        assert response.status_code in [405, 422]

    def test_health_put_not_allowed(self):
        """Verify PUT to /health is not allowed."""
        response = client.put("/health")
        assert response.status_code in [405, 422]

    def test_health_delete_not_allowed(self):
        """Verify DELETE to /health is not allowed."""
        response = client.delete("/health")
        assert response.status_code in [405, 422]

    def test_items_post_get_not_allowed(self):
        """Verify GET to /items (collection) is not allowed."""
        # The endpoint only defines POST
        response = client.get("/items")
        assert response.status_code in [405, 404, 422]

    def test_items_post_delete_not_allowed(self):
        """Verify DELETE to /items is not allowed."""
        response = client.delete("/items")
        assert response.status_code in [405, 404, 422]

    def test_items_id_post_not_allowed(self):
        """Verify POST to /items/{id} is not allowed."""
        response = client.post("/items/1")
        assert response.status_code in [405, 404, 422]

    def test_items_id_put_not_allowed(self):
        """Verify PUT to /items/{id} is not allowed."""
        response = client.put("/items/1")
        assert response.status_code in [405, 404, 422]

    def test_items_id_delete_not_allowed(self):
        """Verify DELETE to /items/{id} is not allowed."""
        response = client.delete("/items/1")
        assert response.status_code in [405, 404, 422]


class TestErrorResponseConsistency:
    """Test consistency of error responses across scenarios."""

    def test_business_error_vs_validation_error_status_codes(self):
        """Verify different error types have different status codes."""
        # Business logic error (price validation)
        business_error = client.post("/items", json={"name": "test", "price": 0})
        
        # Validation error (missing field)
        validation_error = client.post("/items", json={"name": "test"})
        
        # Should have different status codes
        assert business_error.status_code == 400
        assert validation_error.status_code == 422
        assert business_error.status_code != validation_error.status_code

    def test_error_response_always_has_detail(self):
        """Verify all error responses include detail field."""
        error_responses = [
            client.post("/items", json={"name": "test", "price": 0}),      # 400
            client.post("/items", json={"name": "test"}),                   # 422
            client.get("/items/999"),                                       # 404
        ]
        
        for response in error_responses:
            assert response.status_code >= 400
            data = response.json()
            assert "detail" in data

    def test_success_response_always_has_expected_fields(self):
        """Verify all success responses have expected fields."""
        success_responses = [
            client.post("/items", json={"name": "test", "price": 10.0}),
            client.get("/items/1"),
            client.get("/health"),
        ]
        
        for response in success_responses:
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, dict)
            assert len(data) > 0


class TestResponseIntegration:
    """Integration tests for response behavior."""

    def test_create_then_get_response_consistency(self):
        """Verify created item can be retrieved with response integrity."""
        # Create item
        create_response = client.post("/items", json={"name": "test", "price": 15.0})
        assert create_response.status_code == 200
        create_data = create_response.json()
        
        # Get item with same ID
        get_response = client.get(f"/items/{create_data['id']}")
        assert get_response.status_code == 200
        get_data = get_response.json()
        
        # Both should have same id (1 in this implementation)
        assert create_data["id"] == get_data["id"]

    def test_error_after_success_response_consistency(self):
        """Verify error response after success maintains consistency."""
        # Successful request
        success = client.post("/items", json={"name": "test", "price": 10.0})
        assert success.status_code == 200
        
        # Error request
        error = client.post("/items", json={"name": "test", "price": 0})
        assert error.status_code == 400
        
        # Error response should be properly formatted
        data = error.json()
        assert "detail" in data

    def test_multiple_error_types_response_format(self):
        """Test response format consistency across different error types."""
        # Type error
        response1 = client.post("/items", json={"name": "test", "price": "invalid"})
        
        # Validation error
        response2 = client.post("/items", json={"name": "test"})
        
        # Business logic error
        response3 = client.post("/items", json={"name": "test", "price": 0})
        
        # All should be valid JSON
        for response in [response1, response2, response3]:
            data = response.json()
            assert isinstance(data, dict)
            assert "detail" in data
