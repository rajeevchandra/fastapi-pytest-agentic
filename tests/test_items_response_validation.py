from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)


class TestCreateItemResponseStructure:
    """Test response structure and field types for create item."""
    
    def test_response_has_id_field(self):
        """Test that response includes id field."""
        response = client.post("/items", json={"name": "test", "price": 10.0})
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert isinstance(data["id"], int)
    
    def test_response_has_name_field(self):
        """Test that response includes name field."""
        response = client.post("/items", json={"name": "test", "price": 10.0})
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert isinstance(data["name"], str)
    
    def test_response_has_price_field(self):
        """Test that response includes price field."""
        response = client.post("/items", json={"name": "test", "price": 10.0})
        assert response.status_code == 200
        data = response.json()
        assert "price" in data
        assert isinstance(data["price"], (int, float))


class TestGetItemResponseStructure:
    """Test response structure for get item endpoint."""
    
    def test_get_response_has_all_fields(self):
        """Test that get item response has all required fields."""
        response = client.get("/items/1")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data
    
    def test_get_response_field_types(self):
        """Test field types in get item response."""
        response = client.get("/items/1")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))
    
    def test_get_response_no_extra_fields(self):
        """Test that get response doesn't have unexpected fields."""
        response = client.get("/items/1")
        assert response.status_code == 200
        data = response.json()
        expected_keys = {"id", "name", "price"}
        assert set(data.keys()) == expected_keys


class TestErrorResponseStructure:
    """Test error response format and consistency."""
    
    def test_bad_price_error_has_detail(self):
        """Test that price validation error has detail field."""
        response = client.post("/items", json={"name": "test", "price": 0})
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)
    
    def test_not_found_error_has_detail(self):
        """Test that not found error has detail field."""
        response = client.get("/items/999")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    def test_missing_field_error_format(self):
        """Test error format for missing required field."""
        response = client.post("/items", json={"name": "test"})
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_type_error_format(self):
        """Test error format for type validation failure."""
        response = client.post("/items", json={"name": "test", "price": "invalid"})
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_validation_error_is_list_or_dict(self):
        """Test validation error detail is properly formatted."""
        response = client.post("/items", json={"price": 10.0})
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        # FastAPI returns detail as list of error objects


class TestHTTPStatusCodes:
    """Test HTTP status codes for various scenarios."""
    
    @pytest.mark.parametrize("endpoint,method,data,expected_status", [
        ("/items", "POST", {"name": "test", "price": 10.0}, 200),           # success
        ("/items", "POST", {"name": "test", "price": 0}, 400),              # bad request
        ("/items", "POST", {"name": "test", "price": -1}, 400),             # bad request
        ("/items/1", "GET", None, 200),                                     # found
        ("/items/999", "GET", None, 404),                                   # not found
        ("/items", "POST", {"name": "test"}, 422),                          # missing field
        ("/items", "POST", {"price": 10.0}, 422),                           # missing field
    ])
    def test_status_codes(self, endpoint, method, data, expected_status):
        """Test HTTP status codes for various requests."""
        if method == "POST":
            response = client.post(endpoint, json=data)
        else:
            response = client.get(endpoint)
        assert response.status_code == expected_status


class TestContentTypeHeaders:
    """Test content-type headers in responses."""
    
    def test_create_response_content_type(self):
        """Test create item response has correct content-type."""
        response = client.post("/items", json={"name": "test", "price": 10.0})
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")
    
    def test_get_response_content_type(self):
        """Test get item response has correct content-type."""
        response = client.get("/items/1")
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")
    
    def test_error_response_content_type(self):
        """Test error response has correct content-type."""
        response = client.post("/items", json={"name": "test", "price": 0})
        assert response.status_code == 400
        assert "application/json" in response.headers.get("content-type", "")
