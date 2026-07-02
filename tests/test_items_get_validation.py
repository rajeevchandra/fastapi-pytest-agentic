import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemParametrized:
    """Parametrized tests for GET /items/{item_id} endpoint."""

    @pytest.mark.parametrize("item_id", [1])
    def test_get_existing_item(self, item_id):
        """Item with id=1 should be found."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == item_id
        assert "name" in data
        assert "price" in data

    @pytest.mark.parametrize("item_id", [0, -1, 2, 100, 999])
    def test_get_non_existing_items(self, item_id):
        """Items with id other than 1 should return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"


class TestGetItemBoundaryValues:
    """Test boundary values for item_id parameter."""

    def test_zero_item_id(self):
        """Zero item_id should return 404."""
        r = client.get("/items/0")
        assert r.status_code == 404

    def test_negative_item_id(self):
        """Negative item_id should return 404."""
        r = client.get("/items/-1")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_very_large_item_id(self):
        """Very large item_id should return 404."""
        r = client.get("/items/999999999")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_max_int_item_id(self):
        """Max integer item_id should return 404."""
        r = client.get(f"/items/{2**31 - 1}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"


class TestGetItemResponseValidation:
    """Test response structure and content for GET /items/{item_id}."""

    def test_response_has_required_fields(self):
        """Response should have id, name, price fields."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_response_field_types(self):
        """Response fields should have correct types."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_response_values_consistent(self):
        """Multiple calls to same endpoint should return consistent data."""
        r1 = client.get("/items/1")
        r2 = client.get("/items/1")
        assert r1.json() == r2.json()

    def test_error_response_structure(self):
        """Error response should have detail field."""
        r = client.get("/items/2")
        assert r.status_code == 404
        data = r.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)


class TestGetItemContentType:
    """Test content type headers for GET endpoint."""

    def test_success_content_type(self):
        """Successful response should have JSON content type."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")

    def test_error_content_type(self):
        """Error response should have JSON content type."""
        r = client.get("/items/2")
        assert r.status_code == 404
        assert "application/json" in r.headers.get("content-type", "")
