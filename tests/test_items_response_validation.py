"""Comprehensive response validation and HTTP status code tests."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemResponseStructure:
    """Validate response structure for item creation."""
    
    def test_success_response_has_required_fields(self):
        """Test that success response contains all required fields."""
        response = client.post("/items", json={"name": "book", "price": 12.5})
        assert response.status_code == 200
        data = response.json()
        assert "id" in data, "Response missing 'id' field"
        assert "name" in data, "Response missing 'name' field"
        assert "price" in data, "Response missing 'price' field"


    def test_success_response_field_types(self):
        """Test that response fields have correct types."""
        response = client.post("/items", json={"name": "book", "price": 12.5})
        data = response.json()
        assert isinstance(data["id"], int), "id should be integer"
        assert isinstance(data["name"], str), "name should be string"
        assert isinstance(data["price"], (int, float)), "price should be number"


    def test_success_response_id_value(self):
        """Test that response id value matches expectations."""
        response = client.post("/items", json={"name": "test", "price": 5.0})
        data = response.json()
        assert data["id"] == 1, "id should always be 1"


    def test_success_response_preserves_input_values(self):
        """Test that response preserves submitted name and price."""
        test_name = "Test Product"
        test_price = 99.99
        response = client.post("/items", json={"name": test_name, "price": test_price})
        data = response.json()
        assert data["name"] == test_name
        assert data["price"] == test_price


    def test_error_response_has_detail_field(self):
        """Test that error response contains detail field."""
        response = client.post("/items", json={"name": "bad", "price": 0})
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data, "Error response missing 'detail' field"


    def test_error_response_detail_is_string(self):
        """Test that error detail is a string."""
        response = client.post("/items", json={"name": "bad", "price": -1})
        data = response.json()
        assert isinstance(data["detail"], str), "detail should be a string"


class TestGetItemResponseStructure:
    """Validate response structure for item retrieval."""
    
    def test_get_item_found_response_structure(self):
        """Test response structure when item is found."""
        response = client.get("/items/1")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data


    def test_get_item_found_field_types(self):
        """Test that found item response has correct field types."""
        response = client.get("/items/1")
        data = response.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))


    def test_get_item_not_found_response_structure(self):
        """Test response structure when item not found."""
        response = client.get("/items/999")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data


    def test_get_item_not_found_detail_is_string(self):
        """Test that 404 detail is a string."""
        response = client.get("/items/999")
        data = response.json()
        assert isinstance(data["detail"], str)


class TestHTTPStatusCodes:
    """Test HTTP status code consistency."""
    
    @pytest.mark.parametrize("endpoint,method,json_data,expected_status", [
        ("/items", "POST", {"name": "test", "price": 10.0}, 200),
        ("/items", "POST", {"name": "test", "price": 0}, 400),
        ("/items", "POST", {"name": "test", "price": -5}, 400),
        ("/items/1", "GET", None, 200),
        ("/items/2", "GET", None, 404),
        ("/items/999", "GET", None, 404),
    ])
    def test_status_codes(self, endpoint, method, json_data, expected_status):
        """Test that endpoints return correct status codes."""
        if method == "POST":
            response = client.post(endpoint, json=json_data)
        else:
            response = client.get(endpoint)
        assert response.status_code == expected_status


class TestResponseConsistency:
    """Test response consistency across multiple requests."""
    
    def test_same_input_produces_same_output(self):
        """Test that identical requests produce identical responses."""
        data = {"name": "consistent", "price": 15.5}
        response1 = client.post("/items", json=data)
        response2 = client.post("/items", json=data)
        assert response1.json() == response2.json()


    def test_get_item_always_returns_same_data(self):
        """Test that getting item 1 always returns same data."""
        response1 = client.get("/items/1")
        response2 = client.get("/items/1")
        assert response1.json() == response2.json()


class TestHeaderAndContentType:
    """Test response headers and content type."""
    
    def test_create_item_response_content_type(self):
        """Test that response has correct content type."""
        response = client.post("/items", json={"name": "test", "price": 10.0})
        assert "application/json" in response.headers.get("content-type", "")


    def test_get_item_response_content_type(self):
        """Test that GET response has correct content type."""
        response = client.get("/items/1")
        assert "application/json" in response.headers.get("content-type", "")


    def test_error_response_content_type(self):
        """Test that error response has correct content type."""
        response = client.post("/items", json={"name": "test", "price": 0})
        assert "application/json" in response.headers.get("content-type", "")
