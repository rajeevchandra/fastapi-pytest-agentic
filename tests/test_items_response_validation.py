"""Response structure and validation testing."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemResponseStructure:
    """Test response structure for POST /items."""

    def test_response_has_required_fields(self):
        """Test that response includes all required fields."""
        r = client.post("/items", json={"name": "book", "price": 15.5})
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_response_field_types(self):
        """Test that response fields have correct types."""
        r = client.post("/items", json={"name": "book", "price": 15.5})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], float)

    def test_response_no_extra_fields(self):
        """Test that response doesn't have unexpected extra fields."""
        r = client.post("/items", json={"name": "book", "price": 15.5})
        assert r.status_code == 200
        data = r.json()
        # Should only have id, name, price
        assert set(data.keys()) == {"id", "name", "price"}


class TestGetItemResponseStructure:
    """Test response structure for GET /items/{item_id}."""

    def test_get_item_response_has_required_fields(self):
        """Test that GET response includes required fields."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_get_item_response_field_types(self):
        """Test that GET response fields have correct types."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], float)

    def test_get_item_response_no_extra_fields(self):
        """Test that GET response has only expected fields."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert set(data.keys()) == {"id", "name", "price"}


class TestErrorResponseStructure:
    """Test error response format consistency."""

    def test_400_error_has_detail_field(self):
        """Test that 400 errors include detail field."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400
        data = r.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

    def test_404_error_has_detail_field(self):
        """Test that 404 errors include detail field."""
        r = client.get("/items/999")
        assert r.status_code == 404
        data = r.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

    def test_422_error_structure(self):
        """Test that 422 validation errors have proper structure."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422
        data = r.json()
        # Pydantic returns detail array with error objects
        assert "detail" in data

    def test_error_messages_descriptive(self):
        """Test that error messages are descriptive."""
        r = client.post("/items", json={"name": "test", "price": -5})
        assert r.status_code == 400
        data = r.json()
        assert "price" in data["detail"].lower()


class TestHTTPStatusCodes:
    """Test HTTP status codes for various scenarios."""

    @pytest.mark.parametrize("scenario,expected_status", [
        ("valid_create", 200),
        ("negative_price", 400),
        ("zero_price", 400),
        ("missing_name", 422),
        ("get_existing", 200),
        ("get_missing", 404),
    ])
    def test_http_status_codes(self, scenario, expected_status):
        """Test correct HTTP status codes for various scenarios."""
        if scenario == "valid_create":
            r = client.post("/items", json={"name": "test", "price": 10.0})
        elif scenario == "negative_price":
            r = client.post("/items", json={"name": "test", "price": -1.0})
        elif scenario == "zero_price":
            r = client.post("/items", json={"name": "test", "price": 0})
        elif scenario == "missing_name":
            r = client.post("/items", json={"price": 10.0})
        elif scenario == "get_existing":
            r = client.get("/items/1")
        elif scenario == "get_missing":
            r = client.get("/items/999")
        
        assert r.status_code == expected_status


class TestContentTypeHeaders:
    """Test Content-Type header in responses."""

    def test_post_response_content_type(self):
        """Test that POST response has correct Content-Type."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")

    def test_get_response_content_type(self):
        """Test that GET response has correct Content-Type."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")

    def test_error_response_content_type(self):
        """Test that error responses have correct Content-Type."""
        r = client.post("/items", json={"name": "test", "price": -1.0})
        assert r.status_code == 400
        assert "application/json" in r.headers.get("content-type", "")
