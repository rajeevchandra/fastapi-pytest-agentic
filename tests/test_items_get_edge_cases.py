"""Test edge cases and boundary values for GET /items/{item_id} endpoint."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemBoundaryValues:
    """Test boundary values for item_id parameter."""

    @pytest.mark.parametrize(
        "item_id,expected_status",
        [
            (1, 200),  # Valid
            (0, 404),  # Boundary - less than valid
            (-1, 404),  # Negative
            (2, 404),  # Greater than valid
            (100, 404),  # Large value
            (999999, 404),  # Very large value
        ],
    )
    def test_get_item_boundary_values(self, item_id, expected_status):
        """Test various boundary values for item_id."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == expected_status

    def test_get_item_zero(self):
        """Test that item_id 0 returns 404."""
        r = client.get("/items/0")
        assert r.status_code == 404
        assert "not found" in r.json()["detail"]

    def test_get_item_negative_one(self):
        """Test that negative item_id returns 404."""
        r = client.get("/items/-1")
        assert r.status_code == 404
        assert "not found" in r.json()["detail"]

    def test_get_item_large_value(self):
        """Test that large item_id returns 404."""
        r = client.get("/items/999999")
        assert r.status_code == 404
        assert "not found" in r.json()["detail"]


class TestGetItemNotFoundResponse:
    """Test 404 response structure and content."""

    def test_get_item_not_found_status(self):
        """Test that 404 status is returned for non-existent item."""
        r = client.get("/items/99")
        assert r.status_code == 404

    def test_get_item_not_found_detail_field(self):
        """Test that detail field is present in 404 response."""
        r = client.get("/items/99")
        data = r.json()
        assert "detail" in data

    def test_get_item_not_found_detail_message(self):
        """Test that error message is correct."""
        r = client.get("/items/99")
        data = r.json()
        assert data["detail"] == "not found"


class TestGetItemSuccessResponse:
    """Test successful response structure."""

    def test_get_item_success_fields(self):
        """Test that response contains all expected fields."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_get_item_success_values(self):
        """Test that response values are correct."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0

    def test_get_item_response_id_type(self):
        """Test that response id is integer."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)

    def test_get_item_response_name_type(self):
        """Test that response name is string."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["name"], str)

    def test_get_item_response_price_type(self):
        """Test that response price is number."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["price"], (int, float))


class TestGetItemIntegration:
    """Integration tests for GET endpoint."""

    def test_get_existing_item_returns_data(self):
        """Test that existing item can be retrieved."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1

    def test_get_nonexistent_item_returns_not_found(self):
        """Test that non-existent item returns 404."""
        r = client.get("/items/2")
        assert r.status_code == 404

    def test_get_item_consistency(self):
        """Test that same item_id always returns same data."""
        r1 = client.get("/items/1")
        r2 = client.get("/items/1")
        assert r1.json() == r2.json()
