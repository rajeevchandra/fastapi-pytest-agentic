import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestResponseTypeValidation:
    """Validate response types and structures across endpoints."""
    
    def test_health_response_structure(self):
        """Test health endpoint response structure."""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)
        assert "status" in data
        assert data["status"] == "ok"
    
    def test_create_item_response_structure(self):
        """Test create_item response structure."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)
        assert "id" in data
        assert "name" in data
        assert "price" in data
    
    def test_get_item_response_structure(self):
        """Test get_item response structure."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)
        assert "id" in data
        assert "name" in data
        assert "price" in data


class TestHTTPHeaders:
    """Test HTTP headers in responses."""
    
    def test_responses_have_content_type_header(self):
        """Test that all responses have content-type header."""
        endpoints = [
            ("GET", "/health"),
            ("POST", "/items"),
            ("GET", "/items/1"),
        ]
        
        for method, path in endpoints:
            if method == "POST":
                r = client.post(path, json={"name": "test", "price": 10.0})
            else:
                r = client.get(path)
            
            assert "content-type" in r.headers
            assert "application/json" in r.headers["content-type"]
    
    def test_success_response_headers(self):
        """Test success response headers."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.headers.get("content-type") is not None
    
    def test_error_response_headers(self):
        """Test error response headers."""
        r = client.get("/items/999")
        assert r.status_code == 404
        assert "content-type" in r.headers
        assert "application/json" in r.headers["content-type"]


class TestParametrizedIntegration:
    """Integration tests with parametrization."""
    
    @pytest.mark.parametrize("name,price", [
        ("apple", 1.99),
        ("book", 15.50),
        ("laptop", 999.99),
    ])
    def test_create_item_and_verify_response(self, name, price):
        """Test creating items with various names and prices."""
        r = client.post("/items", json={"name": name, "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name
        assert data["price"] == price
        assert data["id"] == 1
    
    @pytest.mark.parametrize("item_id,expected_status", [
        (1, 200),
        (2, 404),
        (100, 404),
    ])
    def test_get_item_status_codes(self, item_id, expected_status):
        """Test get_item returns expected status codes."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == expected_status


class TestEndpointInteraction:
    """Test interactions between endpoints."""
    
    def test_health_endpoint_isolation(self):
        """Test that health endpoint is isolated from other operations."""
        # Get health before creating item
        r1 = client.get("/health")
        assert r1.status_code == 200
        
        # Create an item
        r2 = client.post("/items", json={"name": "test", "price": 10.0})
        assert r2.status_code == 200
        
        # Health endpoint should still work
        r3 = client.get("/health")
        assert r3.status_code == 200
        assert r3.json() == r1.json()
    
    def test_error_does_not_affect_health(self):
        """Test that endpoint errors don't affect health endpoint."""
        # Try invalid request to /items
        r1 = client.get("/items/invalid")
        assert r1.status_code == 422
        
        # Health should still be ok
        r2 = client.get("/health")
        assert r2.status_code == 200
        assert r2.json()["status"] == "ok"


class TestContentValidation:
    """Validate response content in detail."""
    
    def test_create_item_returns_all_required_fields(self):
        """Test that create_item response has all required fields."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        data = r.json()
        required_fields = ["id", "name", "price"]
        for field in required_fields:
            assert field in data
            assert data[field] is not None
    
    def test_get_item_returns_all_required_fields(self):
        """Test that get_item response has all required fields."""
        r = client.get("/items/1")
        data = r.json()
        required_fields = ["id", "name", "price"]
        for field in required_fields:
            assert field in data
            assert data[field] is not None
    
    def test_error_response_has_detail_field(self):
        """Test that error responses include detail field."""
        r = client.get("/items/999")
        assert r.status_code == 404
        data = r.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)
    
    def test_validation_error_has_detail_field(self):
        """Test that validation errors include detail field."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400
        data = r.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)


class TestDataTypes:
    """Test data type consistency across responses."""
    
    def test_create_item_response_types(self):
        """Test create_item response field types."""
        r = client.post("/items", json={"name": "test", "price": 10.5})
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))
    
    def test_get_item_response_types(self):
        """Test get_item response field types."""
        r = client.get("/items/1")
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))
    
    def test_health_response_types(self):
        """Test health response field types."""
        r = client.get("/health")
        data = r.json()
        assert isinstance(data["status"], str)


class TestErrorHandling:
    """Test error handling and error messages."""
    
    def test_invalid_json_format(self):
        """Test response to invalid JSON format."""
        r = client.post("/items", content="invalid json")
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data
    
    def test_missing_required_field_message(self):
        """Test error message for missing required fields."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data
    
    def test_price_validation_error_message(self):
        """Test price validation error message is informative."""
        r = client.post("/items", json={"name": "test", "price": -5})
        assert r.status_code == 400
        data = r.json()
        assert "detail" in data
        assert "price" in data["detail"].lower()
        assert "0" in data["detail"]


class TestStatusCodes:
    """Test that correct status codes are returned."""
    
    @pytest.mark.parametrize("method,path,json_data,expected_status", [
        ("GET", "/health", None, 200),
        ("GET", "/items/1", None, 200),
        ("GET", "/items/999", None, 404),
        ("POST", "/items", {"name": "test", "price": 10.0}, 200),
        ("POST", "/items", {"name": "test", "price": 0}, 400),
        ("POST", "/items", {"price": 10.0}, 422),
        ("GET", "/items/invalid", None, 422),
    ])
    def test_endpoint_status_codes(self, method, path, json_data, expected_status):
        """Test various endpoints return correct status codes."""
        if method == "GET":
            r = client.get(path)
        else:
            r = client.post(path, json=json_data)
        assert r.status_code == expected_status


class TestJSONSerialization:
    """Test JSON serialization of responses."""
    
    def test_create_item_response_is_valid_json(self):
        """Test that create_item response is valid JSON."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        # Should not raise
        data = r.json()
        assert isinstance(data, dict)
    
    def test_get_item_response_is_valid_json(self):
        """Test that get_item response is valid JSON."""
        r = client.get("/items/1")
        assert r.status_code == 200
        # Should not raise
        data = r.json()
        assert isinstance(data, dict)
    
    def test_error_response_is_valid_json(self):
        """Test that error responses are valid JSON."""
        r = client.get("/items/999")
        assert r.status_code == 404
        # Should not raise
        data = r.json()
        assert isinstance(data, dict)


class TestResponseConsistency:
    """Test consistency of responses across multiple calls."""
    
    def test_health_consistency(self):
        """Test health endpoint returns consistent responses."""
        responses = [client.get("/health") for _ in range(5)]
        data_list = [r.json() for r in responses]
        # All responses should be identical
        for data in data_list:
            assert data == {"status": "ok"}
    
    def test_get_item_consistency(self):
        """Test get_item returns consistent data for same ID."""
        responses = [client.get("/items/1") for _ in range(5)]
        data_list = [r.json() for r in responses]
        # All responses should be identical
        first_data = data_list[0]
        for data in data_list[1:]:
            assert data == first_data
    
    def test_create_item_consistency(self):
        """Test create_item returns consistent structure."""
        requests = [
            {"name": "item1", "price": 10.0},
            {"name": "item2", "price": 20.0},
            {"name": "item3", "price": 30.0},
        ]
        responses = [client.post("/items", json=req) for req in requests]
        
        for i, (r, req) in enumerate(zip(responses, requests)):
            assert r.status_code == 200
            data = r.json()
            assert data["name"] == req["name"]
            assert data["price"] == req["price"]
            assert data["id"] == 1  # Always returns id=1


class TestErrorMessageQuality:
    """Test quality and clarity of error messages."""
    
    def test_not_found_error_is_descriptive(self):
        """Test that 404 error message is descriptive."""
        r = client.get("/items/999")
        data = r.json()
        assert "not found" in data["detail"].lower()
    
    def test_price_validation_error_is_descriptive(self):
        """Test that price validation error is descriptive."""
        r = client.post("/items", json={"name": "test", "price": 0})
        data = r.json()
        error_msg = data["detail"].lower()
        assert "price" in error_msg
