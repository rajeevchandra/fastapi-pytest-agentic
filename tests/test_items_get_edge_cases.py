"""
Comprehensive edge case tests for /items/{item_id} GET endpoint.
Tests boundary values, invalid path parameters, and error scenarios.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test path parameter type validation for get_item endpoint."""

    def test_get_item_with_string_item_id(self):
        """Verify string item_id causes validation error."""
        r = client.get("/items/abc")
        assert r.status_code == 422

    def test_get_item_with_float_item_id(self):
        """Verify float item_id causes validation error."""
        r = client.get("/items/1.5")
        assert r.status_code == 422

    def test_get_item_with_special_characters(self):
        """Verify special characters in path cause validation error."""
        r = client.get("/items/1@2#3")
        assert r.status_code == 422


class TestGetItemBoundaryValues:
    """Test boundary conditions for item_id parameter."""

    def test_get_item_zero_id(self):
        """Verify item_id=0 returns 404 (not found)."""
        r = client.get("/items/0")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_negative_id(self):
        """Verify negative item_id returns 404."""
        r = client.get("/items/-1")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    @pytest.mark.parametrize("item_id", [2, 3, 100, 999, 999999])
    def test_get_item_non_matching_ids(self, item_id):
        """Verify non-matching item IDs return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_very_large_id(self):
        """Verify very large item_id returns 404."""
        r = client.get(f"/items/{2**31}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"


class TestGetItemSuccessCase:
    """Test successful get_item cases."""

    def test_get_item_found_returns_200(self):
        """Verify item_id=1 returns 200 success."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_get_item_found_returns_correct_data(self):
        """Verify item_id=1 returns expected data structure."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0

    def test_get_item_found_response_type_validation(self):
        """Verify response fields have correct types."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))


class TestGetItemResponseStructure:
    """Test response structure and completeness."""

    def test_get_item_response_has_required_fields(self):
        """Verify response contains all required fields."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data
        assert len(data) == 3

    def test_get_item_response_no_extra_fields(self):
        """Verify response doesn't contain unexpected fields."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        allowed_fields = {"id", "name", "price"}
        assert set(data.keys()) == allowed_fields

    def test_get_item_response_values_not_empty(self):
        """Verify response fields have meaningful values."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] > 0
        assert len(data["name"]) > 0
        assert data["price"] > 0


class TestGetItemErrorResponses:
    """Test error response format and content."""

    def test_get_item_404_has_detail_field(self):
        """Verify 404 responses include detail field."""
        r = client.get("/items/999")
        assert r.status_code == 404
        assert "detail" in r.json()

    def test_get_item_404_detail_message(self):
        """Verify 404 detail message is consistent."""
        r = client.get("/items/999")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_404_response_structure(self):
        """Verify 404 response has expected structure."""
        r = client.get("/items/999")
        assert r.status_code == 404
        data = r.json()
        assert isinstance(data, dict)
        assert "detail" in data


class TestGetItemURLEncoding:
    """Test URL encoding edge cases."""

    def test_get_item_with_plus_sign(self):
        """Verify plus sign in path is handled correctly."""
        r = client.get("/items/+1")
        assert r.status_code in [422, 404]

    def test_get_item_with_url_encoded_characters(self):
        """Verify URL-encoded characters are handled."""
        r = client.get("/items/%31")  # %31 is URL-encoded "1"
        assert r.status_code == 200

    def test_get_item_with_space_encoded(self):
        """Verify space-encoded characters cause validation error."""
        r = client.get("/items/1%20")
        assert r.status_code == 422


class TestGetItemConsistency:
    """Test response consistency across multiple calls."""

    def test_get_item_multiple_calls_same_response(self):
        """Verify multiple requests for same item return identical data."""
        r1 = client.get("/items/1")
        r2 = client.get("/items/1")
        assert r1.json() == r2.json()

    def test_get_item_success_multiple_times(self):
        """Verify repeated successful requests maintain 200 status."""
        for _ in range(3):
            r = client.get("/items/1")
            assert r.status_code == 200

    def test_get_item_not_found_multiple_times(self):
        """Verify repeated 404 requests are consistent."""
        for _ in range(3):
            r = client.get("/items/999")
            assert r.status_code == 404
            assert r.json()["detail"] == "not found"
