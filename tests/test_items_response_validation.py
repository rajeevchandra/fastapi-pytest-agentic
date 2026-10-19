"""
Response validation tests for all endpoints.
Tests verify response structure, data types, and consistency.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestHealthEndpointResponse:
    """Test response structure for health endpoint."""

    def test_health_returns_ok_status(self):
        """Test that health endpoint returns ok status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_health_response_has_status_field(self):
        """Test that response contains status field."""
        response = client.get("/health")
        data = response.json()
        assert "status" in data

    def test_health_response_is_dict(self):
        """Test that response is a dictionary."""
        response = client.get("/health")
        data = response.json()
        assert isinstance(data, dict)

    def test_health_status_is_string(self):
        """Test that status value is a string."""
        response = client.get("/health")
        data = response.json()
        assert isinstance(data["status"], str)


class TestCreateItemSuccessResponse:
    """Test response structure for successful item creation."""

    @pytest.mark.parametrize("name,price", [
        ("apple", 1.5),
        ("book", 25.99),
        ("pen", 0.99),
        ("monitor", 299.0),
    ])
    def test_create_item_response_structure(self, name, price):
        """Test response structure for various valid items."""
        response = client.post(
            "/items",
            json={"name": name, "price": price}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify all required fields present
        assert "id" in data
        assert "name" in data
        assert "price" in data
        
        # Verify no extra fields
        assert len(data) == 3
        
        # Verify field values
        assert data["id"] == 1
        assert data["name"] == name
        assert data["price"] == price

    def test_create_item_response_field_types(self):
        """Test that response fields have correct types."""
        response = client.post(
            "/items",
            json={"name": "test", "price": 10.5}
        )
        data = response.json()
        
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_create_item_name_echoed_correctly(self):
        """Test that name field is echoed correctly in response."""
        test_name = "special_product_123"
        response = client.post(
            "/items",
            json={"name": test_name, "price": 5.0}
        )
        data = response.json()
        assert data["name"] == test_name

    def test_create_item_price_echoed_correctly(self):
        """Test that price field is echoed correctly in response."""
        test_price = 19.99
        response = client.post(
            "/items",
            json={"name": "item", "price": test_price}
        )
        data = response.json()
        assert data["price"] == test_price


class TestCreateItemErrorResponse:
    """Test error response structure for invalid requests."""

    def test_create_item_error_response_structure(self):
        """Test error response has detail field."""
        response = client.post(
            "/items",
            json={"name": "item", "price": 0}
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

    def test_create_item_error_detail_message(self):
        """Test error detail message is correct."""
        response = client.post(
            "/items",
            json={"name": "item", "price": -5}
        )
        data = response.json()
        assert data["detail"] == "price must be > 0"

    def test_create_item_validation_error_response(self):
        """Test validation error response for missing field."""
        response = client.post(
            "/items",
            json={"name": "item"}
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_create_item_validation_error_is_list(self):
        """Test that validation error detail is a list."""
        response = client.post(
            "/items",
            json={"name": "item"}
        )
        data = response.json()
        assert isinstance(data["detail"], list)


class TestGetItemSuccessResponse:
    """Test response structure for successful item retrieval."""

    def test_get_item_response_structure(self):
        """Test response structure for valid item retrieval."""
        response = client.get("/items/1")
        assert response.status_code == 200
        data = response.json()
        
        # Verify all required fields present
        assert "id" in data
        assert "name" in data
        assert "price" in data
        
        # Verify field values
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0

    def test_get_item_response_field_types(self):
        """Test that response fields have correct types."""
        response = client.get("/items/1")
        data = response.json()
        
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_get_item_response_is_dict(self):
        """Test that response is a dictionary."""
        response = client.get("/items/1")
        data = response.json()
        assert isinstance(data, dict)

    def test_get_item_name_is_string(self):
        """Test that name field is a string."""
        response = client.get("/items/1")
        data = response.json()
        assert isinstance(data["name"], str)
        assert len(data["name"]) > 0

    def test_get_item_price_is_positive(self):
        """Test that price is a positive number."""
        response = client.get("/items/1")
        data = response.json()
        assert data["price"] > 0


class TestGetItemNotFoundResponse:
    """Test error response for item not found."""

    def test_get_item_not_found_status(self):
        """Test that 404 is returned for non-existent item."""
        response = client.get("/items/999")
        assert response.status_code == 404

    def test_get_item_not_found_detail_field(self):
        """Test error response has detail field."""
        response = client.get("/items/999")
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "not found"

    def test_get_item_not_found_detail_is_string(self):
        """Test that error detail is a string."""
        response = client.get("/items/2")
        data = response.json()
        assert isinstance(data["detail"], str)

    def test_get_item_not_found_multiple_ids(self):
        """Test 404 for various non-existent item IDs."""
        for item_id in [2, 3, 10, 100, 999]:
            response = client.get(f"/items/{item_id}")
            assert response.status_code == 404
            assert response.json()["detail"] == "not found"


class TestContentTypeHeaders:
    """Test response content type headers."""

    def test_health_content_type(self):
        """Test health endpoint returns JSON content type."""
        response = client.get("/health")
        assert "application/json" in response.headers.get("content-type", "")

    def test_create_item_content_type(self):
        """Test create item endpoint returns JSON content type."""
        response = client.post(
            "/items",
            json={"name": "test", "price": 10.0}
        )
        assert "application/json" in response.headers.get("content-type", "")

    def test_get_item_content_type(self):
        """Test get item endpoint returns JSON content type."""
        response = client.get("/items/1")
        assert "application/json" in response.headers.get("content-type", "")


class TestResponseConsistency:
    """Test response consistency across multiple requests."""

    def test_create_item_consistent_response(self):
        """Test that multiple create requests have consistent response structure."""
        for i in range(3):
            response = client.post(
                "/items",
                json={"name": f"item_{i}", "price": 10.0 + i}
            )
            data = response.json()
            assert "id" in data
            assert "name" in data
            assert "price" in data
            assert len(data) == 3

    def test_get_item_consistent_response(self):
        """Test that get item returns consistent response for same item."""
        response1 = client.get("/items/1")
        response2 = client.get("/items/1")
        
        data1 = response1.json()
        data2 = response2.json()
        
        assert data1 == data2
        assert data1["id"] == 1
        assert data1["name"] == "sample"
        assert data1["price"] == 10.0

    def test_error_response_consistency(self):
        """Test that error responses have consistent structure."""
        for price in [0, -1, -100]:
            response = client.post(
                "/items",
                json={"name": "item", "price": price}
            )
            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
            assert data["detail"] == "price must be > 0"
