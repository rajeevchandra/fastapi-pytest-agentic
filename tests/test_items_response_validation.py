"""
Test suite for response structure validation and HTTP status codes.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemResponseStructure:
    """Validate response structure for create item endpoint."""

    def test_success_response_has_required_fields(self):
        """Test that successful response contains all required fields."""
        response = client.post("/items", json={"name": "book", "price": 12.5})
        assert response.status_code == 200
        data = response.json()
        
        # Verify all required fields exist
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_success_response_field_types(self):
        """Test that response fields have correct types."""
        response = client.post("/items", json={"name": "book", "price": 12.5})
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_success_response_values_match_request(self):
        """Test that response values match request values."""
        test_cases = [
            {"name": "item1", "price": 9.99},
            {"name": "special item!", "price": 100.00},
            {"name": "123", "price": 0.01},
        ]
        for test_case in test_cases:
            response = client.post("/items", json=test_case)
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == test_case["name"]
            assert data["price"] == test_case["price"]

    def test_response_has_no_extra_fields(self):
        """Test that response doesn't contain unexpected fields."""
        response = client.post("/items", json={"name": "book", "price": 12.5})
        assert response.status_code == 200
        data = response.json()
        
        # Should only have id, name, price
        expected_keys = {"id", "name", "price"}
        assert set(data.keys()) == expected_keys

    def test_response_content_type(self):
        """Test that response has correct content type."""
        response = client.post("/items", json={"name": "book", "price": 12.5})
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")


class TestGetItemResponseStructure:
    """Validate response structure for get item endpoint."""

    def test_success_response_has_required_fields(self):
        """Test that successful get response contains all required fields."""
        response = client.get("/items/1")
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_success_response_field_types(self):
        """Test that response fields have correct types."""
        response = client.get("/items/1")
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_not_found_response_structure(self):
        """Test that 404 response has correct structure."""
        response = client.get("/items/999")
        assert response.status_code == 404
        data = response.json()
        
        # Should have detail field in error response
        assert "detail" in data

    def test_not_found_response_has_detail_message(self):
        """Test that 404 response contains helpful detail message."""
        response = client.get("/items/999")
        assert response.status_code == 404
        detail = response.json()["detail"]
        
        # Should be a string message
        assert isinstance(detail, str)
        assert len(detail) > 0


class TestHTTPStatusCodes:
    """Comprehensive HTTP status code validation."""

    @pytest.mark.parametrize("status_scenario", [
        # (method, path, json_data, expected_status, description)
        ("POST", "/items", {"name": "test", "price": 9.99}, 200, "Create valid item"),
        ("POST", "/items", {"name": "test", "price": 0}, 400, "Create with zero price"),
        ("POST", "/items", {"name": "test", "price": -1}, 400, "Create with negative price"),
        ("GET", "/items/1", None, 200, "Get existing item"),
        ("GET", "/items/999", None, 404, "Get non-existent item"),
        ("GET", "/health", None, 200, "Health check"),
    ])
    def test_status_codes(self, status_scenario):
        """Test correct status codes for various endpoints."""
        method, path, json_data, expected_status, description = status_scenario
        
        if method == "GET":
            response = client.get(path)
        elif method == "POST":
            response = client.post(path, json=json_data)
        
        assert response.status_code == expected_status, f"Failed: {description}"


class TestErrorResponseFormat:
    """Validate error response format and consistency."""

    def test_validation_error_response(self):
        """Test that validation errors have consistent format."""
        response = client.post("/items", json={"name": "test", "price": 0})
        assert response.status_code == 400
        data = response.json()
        
        # Should have detail field
        assert "detail" in data
        assert isinstance(data["detail"], str)

    def test_not_found_error_response(self):
        """Test that not found errors have consistent format."""
        response = client.get("/items/999")
        assert response.status_code == 404
        data = response.json()
        
        # Should have detail field
        assert "detail" in data
        assert isinstance(data["detail"], str)

    def test_error_messages_are_descriptive(self):
        """Test that error messages are helpful and descriptive."""
        response = client.post("/items", json={"name": "test", "price": -5})
        assert response.status_code == 400
        detail = response.json()["detail"]
        
        # Should mention price in error message
        assert "price" in detail.lower()

    def test_error_response_content_type(self):
        """Test that error responses have correct content type."""
        response = client.post("/items", json={"name": "test", "price": 0})
        assert response.status_code == 400
        assert "application/json" in response.headers.get("content-type", "")


class TestResponseHeaders:
    """Validate response headers."""

    def test_success_response_has_headers(self):
        """Test that responses include expected headers."""
        response = client.post("/items", json={"name": "test", "price": 9.99})
        assert response.status_code == 200
        
        # Should have content type
        assert "content-type" in response.headers

    def test_error_response_has_headers(self):
        """Test that error responses include expected headers."""
        response = client.get("/items/999")
        assert response.status_code == 404
        
        # Should still have content type
        assert "content-type" in response.headers

    def test_response_headers_content_type_json(self):
        """Test that content-type header indicates JSON."""
        response = client.get("/items/1")
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type or "json" in content_type.lower()


class TestResponseConsistency:
    """Test consistency of responses across multiple calls."""

    def test_multiple_create_calls_consistent_structure(self):
        """Test that multiple create calls have consistent response structure."""
        for i in range(3):
            response = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            assert response.status_code == 200
            data = response.json()
            
            # All responses should have same keys
            assert set(data.keys()) == {"id", "name", "price"}

    def test_multiple_get_calls_consistent_structure(self):
        """Test that multiple get calls have consistent response structure."""
        for _ in range(3):
            response = client.get("/items/1")
            assert response.status_code == 200
            data = response.json()
            
            # All responses should have same keys
            assert set(data.keys()) == {"id", "name", "price"}

    def test_error_responses_consistent_format(self):
        """Test that error responses are consistent."""
        test_invalid_prices = [-1, -100, 0]
        
        for price in test_invalid_prices:
            response = client.post("/items", json={"name": "test", "price": price})
            assert response.status_code == 400
            data = response.json()
            
            # All errors should have detail field
            assert "detail" in data
            assert isinstance(data["detail"], str)
