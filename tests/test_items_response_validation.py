"""Response structure and error handling validation."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemResponseStructure:
    """Test response structure for create_item endpoint."""

    def test_create_item_response_has_required_fields(self):
        """Test that response contains all required fields."""
        response = client.post(
            "/items",
            json={"name": "test item", "price": 15.99}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check all required fields are present
        assert "id" in data
        assert "name" in data
        assert "price" in data
        
        # Check field types
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_create_item_response_field_values(self):
        """Test that response field values are correct."""
        test_name = "book"
        test_price = 25.50
        response = client.post(
            "/items",
            json={"name": test_name, "price": test_price}
        )
        data = response.json()
        
        assert data["name"] == test_name
        assert data["price"] == test_price
        assert data["id"] == 1

    def test_create_item_no_extra_fields(self):
        """Test that response doesn't have unexpected fields."""
        response = client.post(
            "/items",
            json={"name": "test", "price": 10.0}
        )
        data = response.json()
        
        # Should only have id, name, price
        expected_keys = {"id", "name", "price"}
        assert set(data.keys()) == expected_keys


class TestGetItemResponseStructure:
    """Test response structure for get_item endpoint."""

    def test_get_item_response_has_required_fields(self):
        """Test that get_item response contains required fields."""
        response = client.get("/items/1")
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_get_item_response_field_types(self):
        """Test response field types."""
        response = client.get("/items/1")
        data = response.json()
        
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))


class TestErrorResponseStructure:
    """Test error response format consistency."""

    def test_invalid_price_error_response(self):
        """Test error response when price is invalid."""
        response = client.post(
            "/items",
            json={"name": "bad", "price": 0}
        )
        assert response.status_code == 400
        error_data = response.json()
        
        # Should have detail field
        assert "detail" in error_data
        assert isinstance(error_data["detail"], str)
        assert len(error_data["detail"]) > 0

    def test_not_found_error_response(self):
        """Test error response when item not found."""
        response = client.get("/items/999")
        assert response.status_code == 404
        error_data = response.json()
        
        assert "detail" in error_data
        assert isinstance(error_data["detail"], str)

    def test_validation_error_response_structure(self):
        """Test validation error response structure."""
        response = client.post(
            "/items",
            json={"name": "test"}  # missing price
        )
        assert response.status_code == 422
        error_data = response.json()
        
        # Pydantic validation error includes 'detail' field
        assert "detail" in error_data


class TestHTTPStatusCodes:
    """Test that correct HTTP status codes are returned."""

    @pytest.mark.parametrize("endpoint,method,status_code", [
        ("/items", "POST", 200),         # valid creation
        ("/items/1", "GET", 200),        # valid retrieval
        ("/items/999", "GET", 404),      # not found
        ("/health", "GET", 200),         # health check
    ])
    def test_status_codes(self, endpoint, method, status_code):
        """Test various endpoints return correct status codes."""
        if endpoint == "/items" and method == "POST":
            response = client.post(endpoint, json={"name": "test", "price": 10.0})
        else:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint, json={"name": "test", "price": 10.0})
        
        assert response.status_code == status_code
