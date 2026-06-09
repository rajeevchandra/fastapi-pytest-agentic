"""
Enhanced edge case tests for the GET /items/{item_id} endpoint.

These tests cover boundary values and error scenarios.
"""
from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)


class TestGetItemBoundaryValues:
    """Test boundary values for item_id parameter."""

    def test_get_item_id_zero(self):
        """Test GET with item_id = 0."""
        r = client.get("/items/0")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_id_negative(self):
        """Test GET with negative item_id."""
        r = client.get("/items/-1")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_id_large_negative(self):
        """Test GET with large negative item_id."""
        r = client.get("/items/-999999")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_id_large_positive(self):
        """Test GET with large positive item_id."""
        r = client.get("/items/999999999")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_id_max_int(self):
        """Test GET with maximum integer value."""
        r = client.get(f"/items/{2**31-1}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"


class TestGetItemParametrized:
    """Parametrized tests for various item_ids."""

    @pytest.mark.parametrize("item_id,expected_status", [
        (1, 200),
        (2, 404),
        (0, 404),
        (-1, 404),
        (999, 404),
    ])
    def test_get_item_parametrized(self, item_id, expected_status):
        """Parametrized test for different item_id values."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == expected_status


class TestGetItemValidSuccess:
    """Test successful GET requests."""

    def test_get_item_found_structure(self):
        """Test that found item has correct response structure."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data
        assert data["id"] == 1

    def test_get_item_found_data_types(self):
        """Test that returned data has correct types."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], float)

    def test_get_item_found_values(self):
        """Test specific values of found item."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "sample"
        assert data["price"] == 10.0

    def test_get_item_response_content_type(self):
        """Test response has correct content type."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")


class TestGetItemNotFoundErrors:
    """Test not found error handling."""

    def test_get_item_not_found_structure(self):
        """Test that 404 response has correct structure."""
        r = client.get("/items/2")
        assert r.status_code == 404
        data = r.json()
        assert "detail" in data
        assert data["detail"] == "not found"

    def test_get_item_not_found_multiple_ids(self):
        """Test not found for multiple different ids."""
        for item_id in [2, 3, 100, 999, 10000]:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404
            assert r.json()["detail"] == "not found"


class TestGetItemInvalidPathTypes:
    """Test invalid path parameter types."""

    def test_get_item_non_numeric_path(self):
        """Test GET with non-numeric path parameter."""
        r = client.get("/items/abc")
        assert r.status_code == 422

    def test_get_item_float_path(self):
        """Test GET with float path parameter."""
        r = client.get("/items/1.5")
        assert r.status_code == 422

    def test_get_item_special_chars_path(self):
        """Test GET with special characters in path."""
        r = client.get("/items/1;drop")
        assert r.status_code == 422

    def test_get_item_empty_path(self):
        """Test GET with empty path parameter."""
        r = client.get("/items/")
        assert r.status_code == 404

    def test_get_item_uuid_path(self):
        """Test GET with UUID-like path parameter."""
        r = client.get("/items/550e8400-e29b-41d4-a716-446655440000")
        assert r.status_code == 422


class TestGetItemResponseConsistency:
    """Test response consistency for successful requests."""

    def test_get_item_consistent_results(self):
        """Test that repeated requests return consistent results."""
        r1 = client.get("/items/1")
        r2 = client.get("/items/1")
        assert r1.json() == r2.json()

    def test_get_item_found_always_id_1(self):
        """Test that only item_id=1 is found."""
        # Test the success case
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["id"] == 1
        
        # Test that any other ID returns 404
        for item_id in range(2, 10):
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404
