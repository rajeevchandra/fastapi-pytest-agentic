"""Response structure and error handling validation for /items endpoint."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemResponseStructure:
    """Test response structure for successful create operations."""

    def test_create_item_response_has_required_fields(self):
        """Test that response has all required fields."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        
        # Verify all expected fields are present
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_create_item_response_field_types(self):
        """Test that response fields have correct types."""
        r = client.post("/items", json={"name": "test", "price": 10.5})
        assert r.status_code == 200
        data = r.json()
        
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_create_item_response_no_extra_fields(self):
        """Test that response doesn't include unexpected fields."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        
        # Response should only have id, name, price
        expected_fields = {"id", "name", "price"}
        assert set(data.keys()) == expected_fields

    def test_create_item_response_id_is_consistent(self):
        """Test that id is consistently returned."""
        for _ in range(3):
            r = client.post("/items", json={"name": "test", "price": 10.0})
            assert r.status_code == 200
            assert r.json()["id"] == 1


class TestCreateItemErrorResponse:
    """Test error response format for invalid requests."""

    def test_create_item_error_response_has_detail(self):
        """Test that error response includes detail field."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400
        data = r.json()
        assert "detail" in data

    def test_create_item_error_response_detail_is_string(self):
        """Test that error detail is a string."""
        r = client.post("/items", json={"name": "test", "price": -1})
        assert r.status_code == 400
        assert isinstance(r.json()["detail"], str)

    def test_create_item_error_detail_message(self):
        """Test error message content."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]

    def test_validation_error_response_structure(self):
        """Test that validation errors have proper structure."""
        r = client.post("/items", json={"price": 10.0})  # Missing name
        assert r.status_code == 422
        data = r.json()
        
        # FastAPI validation errors include detail field
        assert "detail" in data


class TestCreateItemStatusCodes:
    """Test HTTP status codes for various scenarios."""

    def test_create_item_success_status_200(self):
        """Test successful creation returns 200."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200

    def test_create_item_invalid_price_status_400(self):
        """Test invalid price returns 400 Bad Request."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.status_code == 400

    def test_create_item_missing_field_status_422(self):
        """Test missing required field returns 422 Unprocessable Entity."""
        r = client.post("/items", json={"name": "item"})
        assert r.status_code == 422

    def test_create_item_malformed_json_status(self):
        """Test malformed JSON handling."""
        r = client.post("/items", data="not valid json", 
                       headers={"Content-Type": "application/json"})
        assert r.status_code in [400, 422]


class TestGetItemResponseStructure:
    """Test response structure for GET operations."""

    def test_get_item_response_has_required_fields(self):
        """Test that response has all required fields."""
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

    def test_get_item_response_no_extra_fields(self):
        """Test that response doesn't include unexpected fields."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        
        expected_fields = {"id", "name", "price"}
        assert set(data.keys()) == expected_fields

    def test_get_item_found_returns_expected_data(self):
        """Test that found item returns correct data."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0


class TestGetItemErrorResponse:
    """Test error response format for GET operations."""

    def test_get_item_not_found_has_detail(self):
        """Test that 404 response includes detail field."""
        r = client.get("/items/999")
        assert r.status_code == 404
        assert "detail" in r.json()

    def test_get_item_not_found_detail_message(self):
        """Test 404 error message."""
        r = client.get("/items/2")
        assert r.status_code == 404
        assert "not found" in r.json()["detail"]

    def test_get_item_not_found_detail_is_string(self):
        """Test that error detail is a string."""
        r = client.get("/items/999")
        assert r.status_code == 404
        assert isinstance(r.json()["detail"], str)


class TestGetItemStatusCodes:
    """Test HTTP status codes for GET operations."""

    def test_get_item_found_status_200(self):
        """Test found item returns 200."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_get_item_not_found_status_404(self):
        """Test missing item returns 404."""
        r = client.get("/items/2")
        assert r.status_code == 404

    def test_get_item_other_ids_status_404(self):
        """Test that only item_id=1 is found."""
        for item_id in [0, 3, 100, 999]:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404


class TestHealthEndpointResponse:
    """Test health endpoint response structure."""

    def test_health_response_has_status_field(self):
        """Test that health endpoint returns status field."""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert "status" in data

    def test_health_response_status_value(self):
        """Test health status value."""
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_health_response_is_200(self):
        """Test health endpoint returns 200."""
        r = client.get("/health")
        assert r.status_code == 200


class TestContentTypeHeaders:
    """Test response content type headers."""

    def test_json_content_type_on_success(self):
        """Test that successful responses have JSON content type."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert "application/json" in r.headers.get("content-type", "")

    def test_json_content_type_on_error(self):
        """Test that error responses have JSON content type."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert "application/json" in r.headers.get("content-type", "")

    def test_json_content_type_on_get_found(self):
        """Test that GET found responses have JSON content type."""
        r = client.get("/items/1")
        assert "application/json" in r.headers.get("content-type", "")

    def test_json_content_type_on_get_not_found(self):
        """Test that GET not found responses have JSON content type."""
        r = client.get("/items/999")
        assert "application/json" in r.headers.get("content-type", "")


class TestErrorMessageConsistency:
    """Test error message consistency across endpoints."""

    def test_error_responses_always_have_detail(self):
        """Test that all error responses include detail field."""
        test_cases = [
            ("POST", "/items", 400, {"name": "item", "price": 0}),
            ("POST", "/items", 422, {"price": 10.0}),
            ("GET", "/items/999", 404, None),
        ]
        
        for method, path, expected_status, json_data in test_cases:
            if method == "POST":
                r = client.post(path, json=json_data)
            else:
                r = client.get(path)
            
            assert r.status_code == expected_status
            assert "detail" in r.json()
