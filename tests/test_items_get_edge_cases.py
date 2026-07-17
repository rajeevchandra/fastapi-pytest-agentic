"""
Comprehensive edge case tests for the GET /items/{item_id} endpoint.
Tests boundary values, error handling, and various item_id scenarios.
"""
from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)


class TestGetItemSuccess:
    """Test successful GET requests for items."""

    def test_get_item_found_returns_correct_data(self):
        """Getting existing item (id=1) should return correct data."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0

    def test_get_item_found_has_required_fields(self):
        """Response should contain id, name, and price fields."""
        r = client.get("/items/1")
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_get_item_found_response_content_type(self):
        """Response should have JSON content type."""
        r = client.get("/items/1")
        assert "application/json" in r.headers.get("content-type", "")


class TestGetItemNotFound:
    """Test 404 responses for non-existent items."""

    @pytest.mark.parametrize("item_id", [2, 3, 10, 100, 999])
    def test_get_item_not_found(self, item_id):
        """Getting non-existent items should return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert "not found" in r.json()["detail"]

    def test_get_item_zero_not_found(self):
        """Getting item with id=0 should return 404."""
        r = client.get("/items/0")
        assert r.status_code == 404

    def test_get_item_negative_id_not_found(self):
        """Getting item with negative id should return 404."""
        r = client.get("/items/-1")
        assert r.status_code == 404

    def test_get_item_large_id_not_found(self):
        """Getting item with very large id should return 404."""
        r = client.get("/items/999999999")
        assert r.status_code == 404

    def test_get_item_max_int_not_found(self):
        """Getting item with max int value should return 404."""
        r = client.get("/items/2147483647")
        assert r.status_code == 404


class TestGetItemBoundaryValues:
    """Test boundary values for item_id parameter."""

    @pytest.mark.parametrize("item_id", [0, -1, -10, -999])
    def test_get_item_non_positive_ids(self, item_id):
        """Non-positive item_ids should return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    def test_get_item_sequential_ids(self):
        """Test accessing items with sequential ids (all should be 404 except 1)."""
        for item_id in range(1, 6):
            r = client.get(f"/items/{item_id}")
            if item_id == 1:
                assert r.status_code == 200
            else:
                assert r.status_code == 404

    def test_get_item_decimal_like_id(self):
        """Item id as string should be parsed as integer."""
        r = client.get("/items/001")
        # Should be interpreted as id=1
        assert r.status_code == 200

    def test_get_item_with_trailing_slash(self):
        """Request with trailing slash might be different."""
        # Note: FastAPI typically doesn't match trailing slashes by default
        r = client.get("/items/1/")
        # May return 404 or 200 depending on FastAPI configuration
        assert r.status_code in [200, 404]


class TestGetItemPathVariations:
    """Test various path parameter formats."""

    def test_get_item_id_one(self):
        """Item with id 1 should be found."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_get_item_exact_integer_path(self):
        """Path parameter should be exact integer."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_get_item_leading_zeros(self):
        """Item id with leading zeros (e.g., 001) should be parsed correctly."""
        r = client.get("/items/001")
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_get_item_large_number_string(self):
        """Very large number in path should be handled."""
        r = client.get("/items/99999999999999999999")
        # Will likely be parsed as large integer and not found
        assert r.status_code == 404


class TestGetItemErrorMessages:
    """Test error message content and structure."""

    def test_get_item_not_found_has_detail_field(self):
        """404 response should include detail field."""
        r = client.get("/items/999")
        assert "detail" in r.json()

    def test_get_item_not_found_detail_is_string(self):
        """detail field should be a string."""
        r = client.get("/items/999")
        assert isinstance(r.json()["detail"], str)

    def test_get_item_not_found_detail_message(self):
        """detail message should be descriptive."""
        r = client.get("/items/999")
        assert "not found" in r.json()["detail"].lower()


class TestGetItemMultipleCalls:
    """Test multiple consecutive GET requests."""

    def test_get_item_multiple_times_consistent(self):
        """Multiple requests for same item should return same data."""
        r1 = client.get("/items/1")
        r2 = client.get("/items/1")
        assert r1.json() == r2.json()

    def test_get_item_alternating_ids(self):
        """Alternating between existing and non-existing items should work."""
        r1 = client.get("/items/1")
        assert r1.status_code == 200
        r2 = client.get("/items/2")
        assert r2.status_code == 404
        r3 = client.get("/items/1")
        assert r3.status_code == 200
        assert r1.json() == r3.json()
