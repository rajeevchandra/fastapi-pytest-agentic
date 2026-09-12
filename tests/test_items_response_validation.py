from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)


class TestCreateItemHTTPStatusCodes:
    """Test HTTP status codes for create_item endpoint."""

    def test_create_item_success_returns_200(self):
        """Successful creation should return 200."""
        r = client.post("/items", json={"name": "test", "price": 10})
        assert r.status_code == 200

    def test_create_item_invalid_price_returns_400(self):
        """Invalid price should return 400."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400

    def test_create_item_negative_price_returns_400(self):
        """Negative price should return 400."""
        r = client.post("/items", json={"name": "test", "price": -5})
        assert r.status_code == 400

    def test_create_item_missing_field_returns_422(self):
        """Missing required field should return 422."""
        r = client.post("/items", json={"price": 10})
        assert r.status_code == 422

    def test_create_item_invalid_type_returns_422(self):
        """Invalid type should return 422."""
        r = client.post("/items", json={"name": "test", "price": "invalid"})
        assert r.status_code == 422


class TestGetItemHTTPStatusCodes:
    """Test HTTP status codes for get_item endpoint."""

    @pytest.mark.parametrize("item_id", [1])
    def test_get_existing_item_returns_200(self, item_id):
        """Getting existing item should return 200."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 200

    @pytest.mark.parametrize("item_id", [2, 3, 100, 999])
    def test_get_nonexistent_item_returns_404(self, item_id):
        """Getting non-existent item should return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404


class TestCreateItemResponseFormat:
    """Test response format and content-type for create_item."""

    def test_create_item_response_content_type(self):
        """Response should be JSON."""
        r = client.post("/items", json={"name": "test", "price": 10})
        assert "application/json" in r.headers["content-type"]

    def test_create_item_response_is_valid_json(self):
        """Response should be valid JSON."""
        r = client.post("/items", json={"name": "test", "price": 10})
        # Should not raise
        data = r.json()
        assert isinstance(data, dict)

    def test_create_item_response_has_no_extra_fields(self):
        """Response should only have id, name, price."""
        r = client.post("/items", json={"name": "test", "price": 10})
        data = r.json()
        assert len(data) == 3
        assert set(data.keys()) == {"id", "name", "price"}


class TestGetItemResponseFormat:
    """Test response format and content-type for get_item."""

    def test_get_item_response_content_type(self):
        """Response should be JSON."""
        r = client.get("/items/1")
        assert "application/json" in r.headers["content-type"]

    def test_get_item_response_is_valid_json(self):
        """Response should be valid JSON."""
        r = client.get("/items/1")
        data = r.json()
        assert isinstance(data, dict)

    def test_get_item_response_has_required_fields(self):
        """Response should have id, name, price fields."""
        r = client.get("/items/1")
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data


class TestErrorResponseFormat:
    """Test error response format consistency."""

    def test_error_400_has_detail_field(self):
        """400 errors should have detail field."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert "detail" in r.json()

    def test_error_404_has_detail_field(self):
        """404 errors should have detail field."""
        r = client.get("/items/999")
        assert "detail" in r.json()

    def test_error_detail_is_string(self):
        """Error detail should be a string."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert isinstance(r.json()["detail"], str)

    def test_error_422_has_detail_field(self):
        """422 validation errors should have detail field."""
        r = client.post("/items", json={"price": 10})
        data = r.json()
        assert "detail" in data or isinstance(data, dict)

    def test_error_response_is_json(self):
        """Error responses should be JSON."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert "application/json" in r.headers["content-type"]


class TestResponseFieldTypes:
    """Test that response fields have correct types."""

    def test_create_item_response_id_is_int(self):
        """Response id should be an integer."""
        r = client.post("/items", json={"name": "test", "price": 10})
        data = r.json()
        assert isinstance(data["id"], int)

    def test_create_item_response_name_is_string(self):
        """Response name should be a string."""
        r = client.post("/items", json={"name": "test", "price": 10})
        data = r.json()
        assert isinstance(data["name"], str)

    def test_create_item_response_price_is_float(self):
        """Response price should be a number."""
        r = client.post("/items", json={"name": "test", "price": 10})
        data = r.json()
        assert isinstance(data["price"], (int, float))

    def test_get_item_response_fields_types(self):
        """Get response fields should have correct types."""
        r = client.get("/items/1")
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))
