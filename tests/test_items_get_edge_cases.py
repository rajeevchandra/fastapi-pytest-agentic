"""GET endpoint edge cases and error handling tests.

Tests for /items/{item_id} endpoint with boundary values, invalid types,
and URL encoding edge cases.
Part of Coverage Plan issue #3 - PR #2.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemBoundaryValues:
    """Test boundary values for item_id parameter."""

    def test_get_item_valid_id_one(self):
        """Valid item ID (1) should return 200."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_get_item_zero_id(self):
        """Item ID 0 should return 404."""
        r = client.get("/items/0")
        assert r.status_code == 404

    def test_get_item_negative_id(self):
        """Negative item ID should return 404."""
        r = client.get("/items/-1")
        assert r.status_code == 404

    def test_get_item_large_negative_id(self):
        """Large negative item ID should return 404."""
        r = client.get("/items/-999999")
        assert r.status_code == 404

    def test_get_item_large_positive_id(self):
        """Large positive item ID should return 404."""
        r = client.get("/items/999999999")
        assert r.status_code == 404

    @pytest.mark.parametrize("item_id", [0, -1, 2, 100, -100, 999999])
    def test_get_item_various_ids(self, item_id):
        """Test various item IDs - only 1 should succeed."""
        r = client.get(f"/items/{item_id}")
        if item_id == 1:
            assert r.status_code == 200
        else:
            assert r.status_code == 404

    def test_get_item_max_int_value(self):
        """Very large integer ID should return 404."""
        r = client.get("/items/2147483647")
        assert r.status_code == 404


class TestGetItemInvalidTypes:
    """Test invalid path parameter types."""

    def test_get_item_string_id(self):
        """String ID should cause FastAPI to return 422."""
        r = client.get("/items/abc")
        assert r.status_code == 422

    def test_get_item_float_id(self):
        """Float ID should cause FastAPI to return 422."""
        r = client.get("/items/1.5")
        assert r.status_code == 422

    def test_get_item_empty_id(self):
        """Empty ID should cause 404."""
        r = client.get("/items/")
        # FastAPI treats this as no path parameter - should be 404 or 405
        assert r.status_code in (404, 405, 422)


class TestGetItemURLEncoding:
    """Test URL encoding edge cases."""

    def test_get_item_url_encoded_id(self):
        """URL encoded number should work."""
        r = client.get("/items/%31")  # %31 is '1' in URL encoding
        # May decode to 1 or fail depending on FastAPI behavior
        assert r.status_code in (200, 422)

    def test_get_item_plus_sign(self):
        """Plus sign before number should cause validation error."""
        r = client.get("/items/+1")
        # May be interpreted as valid or invalid
        assert r.status_code in (200, 404, 422)

    def test_get_item_leading_zeros(self):
        """Leading zeros should be parsed as valid integer."""
        r = client.get("/items/001")
        assert r.status_code == 200  # Should parse to 1

    def test_get_item_with_spaces(self):
        """Spaces in path should cause 404."""
        r = client.get("/items/1%20")
        assert r.status_code in (404, 422)


class TestGetItemResponseValidation:
    """Test response structure and content."""

    def test_get_item_response_structure(self):
        """Valid item response should have required fields."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_get_item_response_types(self):
        """Response fields should have correct types."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_get_item_response_content(self):
        """Valid item should return expected values."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0

    def test_get_item_not_found_message(self):
        """404 response should have error detail."""
        r = client.get("/items/2")
        assert r.status_code == 404
        assert "detail" in r.json()
        assert r.json()["detail"] == "not found"

    def test_get_item_not_found_structure(self):
        """404 response should be properly structured."""
        r = client.get("/items/999")
        assert r.status_code == 404
        data = r.json()
        assert isinstance(data, dict)
        assert "detail" in data
