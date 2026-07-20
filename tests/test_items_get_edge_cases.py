"""
GET /items/{item_id} endpoint edge cases and boundary value tests.
"""
from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)


class TestGetItemBoundaryValues:
    """Test GET endpoint with boundary values for item_id."""

    @pytest.mark.parametrize("item_id", [1, -1, 0, 2, 999999])
    def test_get_item_various_ids(self, item_id):
        """Test GET with various item_id values."""
        response = client.get(f"/items/{item_id}")
        if item_id == 1:
            assert response.status_code == 200
            assert response.json()["id"] == 1
        else:
            assert response.status_code == 404
            assert response.json()["detail"] == "not found"

    def test_get_item_found_has_correct_structure(self):
        """Test that found item has correct response structure."""
        response = client.get("/items/1")
        assert response.status_code == 200
        data = response.json()
        assert set(data.keys()) == {"id", "name", "price"}
        assert data["id"] == 1
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_get_item_found_values(self):
        """Test that found item returns expected values."""
        response = client.get("/items/1")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0

    @pytest.mark.parametrize("item_id", [0, -1, 2, 100, 9999])
    def test_get_item_not_found_ids(self, item_id):
        """Test that non-existent item_ids return 404."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == 404
        assert response.json()["detail"] == "not found"

    def test_get_item_not_found_response_structure(self):
        """Test 404 response has detail field."""
        response = client.get("/items/999")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "not found"


class TestGetItemPathParameters:
    """Test path parameter handling and type validation."""

    def test_get_item_with_string_id_type_error(self):
        """Test that string item_id in path causes validation error."""
        response = client.get("/items/abc")
        assert response.status_code == 422

    def test_get_item_with_float_id_type_error(self):
        """Test that float item_id in path causes validation error."""
        response = client.get("/items/1.5")
        assert response.status_code == 422

    def test_get_item_with_special_chars_type_error(self):
        """Test that special characters in path cause validation error."""
        response = client.get("/items/@#$")
        assert response.status_code == 422

    def test_get_item_large_integer_id(self):
        """Test with very large integer ID."""
        large_id = 2147483647  # Max 32-bit int
        response = client.get(f"/items/{large_id}")
        assert response.status_code == 404

    def test_get_item_large_negative_integer_id(self):
        """Test with very large negative integer ID."""
        large_negative_id = -2147483648  # Min 32-bit int
        response = client.get(f"/items/{large_negative_id}")
        assert response.status_code == 404


class TestGetItemResponseDetails:
    """Test response details and headers for GET requests."""

    def test_get_item_content_type_header(self):
        """Test that response has correct content-type."""
        response = client.get("/items/1")
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]

    def test_get_item_found_no_cache_considerations(self):
        """Test successful GET response."""
        response = client.get("/items/1")
        assert response.status_code == 200
        assert response.headers["content-type"]

    def test_get_item_not_found_content_type_header(self):
        """Test that 404 response also has correct content-type."""
        response = client.get("/items/999")
        assert response.status_code == 404
        assert "application/json" in response.headers["content-type"]
