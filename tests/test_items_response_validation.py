import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemResponseStructure:
    """Test response structure and field types for create_item endpoint."""

    def test_create_item_response_fields(self):
        """Test that create_item response has correct fields."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        
        # Verify all required fields are present
        assert "id" in data
        assert "name" in data
        assert "price" in data
        assert len(data) == 3  # Only these three fields

    def test_create_item_response_field_types(self):
        """Test that response fields have correct types."""
        r = client.post("/items", json={"name": "book", "price": 12.99})
        assert r.status_code == 200
        data = r.json()
        
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_create_item_response_values_match_request(self):
        """Test that response values match the request."""
        request_data = {"name": "unique_item_name", "price": 25.50}
        r = client.post("/items", json=request_data)
        assert r.status_code == 200
        data = r.json()
        
        assert data["name"] == request_data["name"]
        assert data["price"] == request_data["price"]


class TestGetItemResponseStructure:
    """Test response structure for get_item endpoint."""

    def test_get_item_response_fields(self):
        """Test that get_item response has correct fields."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_get_item_response_field_types(self):
        """Test that response fields have correct types."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_get_item_found_response_consistency(self):
        """Test that found item response is consistent."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0


class TestErrorResponseStructure:
    """Test error response format consistency."""

    def test_invalid_price_error_response(self):
        """Test error response for invalid price."""
        r = client.post("/items", json={"name": "test", "price": -5})
        assert r.status_code == 400
        data = r.json()
        
        assert "detail" in data
        assert isinstance(data["detail"], str)
        assert len(data["detail"]) > 0

    def test_item_not_found_error_response(self):
        """Test error response for not found."""
        r = client.get("/items/999")
        assert r.status_code == 404
        data = r.json()
        
        assert "detail" in data
        assert isinstance(data["detail"], str)
        assert len(data["detail"]) > 0

    def test_validation_error_response(self):
        """Test error response for validation error."""
        r = client.post("/items", json={"name": "test"})  # Missing price
        assert r.status_code == 422
        data = r.json()
        
        assert "detail" in data


class TestHTTPStatusCodes:
    """Test HTTP status codes across endpoints."""

    @pytest.mark.parametrize(
        "method,endpoint,data,expected_status",
        [
            ("GET", "/health", None, 200),
            ("POST", "/items", {"name": "item", "price": 10.0}, 200),
            ("POST", "/items", {"name": "item", "price": 0}, 400),
            ("POST", "/items", {"name": "item", "price": -5}, 400),
            ("POST", "/items", {"name": "item"}, 422),
            ("GET", "/items/1", None, 200),
            ("GET", "/items/2", None, 404),
            ("GET", "/items/999", None, 404),
        ],
    )
    def test_all_status_codes(self, method, endpoint, data, expected_status):
        """Test all expected status codes."""
        if method == "GET":
            r = client.get(endpoint)
        else:  # POST
            r = client.post(endpoint, json=data)
        
        assert r.status_code == expected_status

    def test_successful_response_always_200_or_404(self):
        """Test that successful operations return 200."""
        r = client.post("/items", json={"name": "success", "price": 15.0})
        assert r.status_code == 200
        assert r.status_code != 201  # Not 201 for create

    def test_error_status_codes_not_2xx(self):
        """Test that errors don't return 2xx codes."""
        error_cases = [
            ("POST", "/items", {"name": "item", "price": -1}),  # 400
            ("POST", "/items", {"price": 10}),  # 422
            ("GET", "/items/0"),  # 404
        ]
        
        for case in error_cases:
            if len(case) == 3 and case[0] == "GET":
                r = client.get(case[1])
            else:
                r = client.post(case[1], json=case[2])
            
            assert r.status_code >= 400


class TestErrorMessages:
    """Test error message content."""

    def test_price_validation_error_message(self):
        """Test specific error message for price validation."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.status_code == 400
        data = r.json()
        
        assert "price must be > 0" in data["detail"]

    def test_not_found_error_message(self):
        """Test specific error message for not found."""
        r = client.get("/items/100")
        assert r.status_code == 404
        data = r.json()
        
        assert "not found" in data["detail"].lower()

    def test_validation_error_has_detail(self):
        """Test that validation errors have detail field."""
        r = client.post("/items", json={})
        assert r.status_code == 422
        data = r.json()
        
        assert "detail" in data


class TestContentTypeHeaders:
    """Test response content type headers."""

    def test_create_item_json_response(self):
        """Test that create_item returns JSON."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")
        assert r.json() is not None

    def test_get_item_json_response(self):
        """Test that get_item returns JSON."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")
        assert r.json() is not None

    def test_error_response_json_response(self):
        """Test that error responses return JSON."""
        r = client.post("/items", json={"name": "item", "price": -1})
        assert r.status_code == 400
        assert "application/json" in r.headers.get("content-type", "")
        assert r.json() is not None
