"""
Edge case tests for GET /items/{item_id} endpoint.
Tests boundary values, invalid types, and URL parameter validation.
"""
from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)


class TestGetItemBoundaryValues:
    """Test boundary values for GET /items/{item_id} endpoint."""

    def test_get_existing_item(self):
        """Get existing item (id=1)."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0

    def test_get_item_with_zero_id(self):
        """Get item with id=0 (should not exist)."""
        r = client.get("/items/0")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_with_negative_id(self):
        """Get item with negative id (should not exist)."""
        r = client.get("/items/-1")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_with_large_negative_id(self):
        """Get item with large negative id."""
        r = client.get("/items/-999999999")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_with_large_positive_id(self):
        """Get item with very large positive id."""
        r = client.get("/items/999999999")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_with_max_int(self):
        """Get item with maximum integer value."""
        r = client.get("/items/2147483647")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    @pytest.mark.parametrize("item_id", [0, -1, 2, 3, 999, -100])
    def test_get_nonexistent_items(self, item_id):
        """Parametrized test for all non-existent item ids."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"


class TestGetItemInvalidTypes:
    """Test invalid path parameter types for GET /items/{item_id}."""

    def test_get_item_with_string_id(self):
        """Get item with string instead of integer."""
        r = client.get("/items/abc")
        assert r.status_code == 422

    def test_get_item_with_float_id(self):
        """Get item with float value."""
        r = client.get("/items/1.5")
        assert r.status_code == 422

    def test_get_item_with_special_characters(self):
        """Get item with special characters in id."""
        r = client.get("/items/1!@#$")
        assert r.status_code == 422

    def test_get_item_with_empty_id(self):
        """Get item with missing id (no path parameter)."""
        r = client.get("/items/")
        assert r.status_code == 404 or r.status_code == 405

    def test_get_item_with_multiple_path_segments(self):
        """Get item with extra path segments."""
        r = client.get("/items/1/extra")
        assert r.status_code == 404

    def test_get_item_with_url_encoded_id(self):
        """Get item with URL-encoded id."""
        r = client.get("/items/%31")  # %31 is URL encoding for '1'
        assert r.status_code == 200

    def test_get_item_response_structure(self):
        """Verify complete response structure for valid item."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_get_item_with_leading_zeros(self):
        """Get item with leading zeros in id."""
        r = client.get("/items/001")
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_get_item_response_contains_required_fields(self):
        """Verify response has all required fields."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data
        assert data["id"] == 1
        assert len(data["name"]) > 0
        assert data["price"] > 0
