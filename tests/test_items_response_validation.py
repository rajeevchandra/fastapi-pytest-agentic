"""Response structure and HTTP status code validation."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemHTTPStatusCodes:
    """Test HTTP status codes for item creation."""

    def test_create_item_success_returns_200(self):
        """Successful item creation should return 200."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200

    def test_create_item_invalid_price_returns_400(self):
        """Invalid price should return 400 Bad Request."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400

    def test_create_item_missing_field_returns_422(self):
        """Missing required field should return 422 Unprocessable Entity."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422

    def test_create_item_invalid_type_returns_422(self):
        """Invalid type should return 422."""
        r = client.post("/items", json={"name": "test", "price": "invalid"})
        assert r.status_code == 422


class TestGetItemHTTPStatusCodes:
    """Test HTTP status codes for item retrieval."""

    def test_get_item_found_returns_200(self):
        """Getting existing item should return 200."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_get_item_not_found_returns_404(self):
        """Getting non-existent item should return 404."""
        r = client.get("/items/2")
        assert r.status_code == 404

    @pytest.mark.parametrize("item_id", [2, 3, 10, 100, 999])
    def test_get_item_not_found_for_various_ids(self, item_id):
        """Only item_id=1 exists; others return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404


class TestCreateItemResponseHeaders:
    """Test response headers for consistency."""

    def test_create_item_response_has_content_type(self):
        """Response should have proper content type."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert "content-type" in r.headers
        assert "application/json" in r.headers["content-type"]

    def test_get_item_response_has_content_type(self):
        """GET response should have proper content type."""
        r = client.get("/items/1")
        assert "content-type" in r.headers
        assert "application/json" in r.headers["content-type"]


class TestGetItemResponseStructure:
    """Test response structure for item retrieval."""

    def test_get_item_response_has_required_fields(self):
        """GET response should include id, name, price."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_get_item_response_field_types(self):
        """GET response fields should have correct types."""
        r = client.get("/items/1")
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], float)

    def test_get_item_response_values(self):
        """GET response should return hardcoded sample item."""
        r = client.get("/items/1")
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0


class TestErrorResponseFormat:
    """Test error response consistency and format."""

    def test_error_response_has_detail_field(self):
        """All error responses should have detail field."""
        r = client.post("/items", json={"name": "test", "price": -1})
        assert r.status_code == 400
        assert "detail" in r.json()

    def test_not_found_error_detail(self):
        """404 error should have proper detail message."""
        r = client.get("/items/999")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_validation_error_detail_is_list(self):
        """422 validation errors should have list of issues."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data

    def test_business_logic_error_detail_is_string(self):
        """400 business logic errors should have string detail."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400
        detail = r.json()["detail"]
        assert isinstance(detail, str)


class TestGetItemErrorHandling:
    """Test error handling for GET requests."""

    def test_get_item_invalid_id_type(self):
        """Invalid item_id type should raise error."""
        r = client.get("/items/not_a_number")
        assert r.status_code == 422

    def test_get_item_negative_id_not_found(self):
        """Negative item_id should return 404."""
        r = client.get("/items/-1")
        assert r.status_code == 404

    def test_get_item_zero_id_not_found(self):
        """Zero item_id should return 404."""
        r = client.get("/items/0")
        assert r.status_code == 404


class TestContentNegotiation:
    """Test that responses are always JSON."""

    def test_create_item_response_is_json(self):
        """Success response should be valid JSON."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        # Should not raise an exception
        data = r.json()
        assert isinstance(data, dict)

    def test_get_item_response_is_json(self):
        """GET response should be valid JSON."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)

    def test_error_response_is_json(self):
        """Error responses should be valid JSON."""
        r = client.post("/items", json={"name": "test", "price": -1})
        assert r.status_code == 400
        data = r.json()
        assert isinstance(data, dict)


class TestResponseConsistency:
    """Test consistency across multiple requests."""

    def test_multiple_get_requests_return_same_data(self):
        """Multiple GET requests should return same data."""
        r1 = client.get("/items/1")
        r2 = client.get("/items/1")
        assert r1.json() == r2.json()

    def test_multiple_creates_return_same_id(self):
        """Multiple creates return same hardcoded id."""
        r1 = client.post("/items", json={"name": "item1", "price": 5.0})
        r2 = client.post("/items", json={"name": "item2", "price": 15.0})
        assert r1.json()["id"] == r2.json()["id"] == 1

    def test_create_and_get_have_compatible_structure(self):
        """Created item and retrieved item have same structure."""
        created = client.post("/items", json={"name": "test", "price": 10.0})
        retrieved = client.get("/items/1")
        
        created_keys = set(created.json().keys())
        retrieved_keys = set(retrieved.json().keys())
        assert created_keys == retrieved_keys
