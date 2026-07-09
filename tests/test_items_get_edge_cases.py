"""Enhanced edge case tests for GET /items/{item_id} endpoint."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemBoundaryValues:
    """Test boundary values for item_id parameter."""

    @pytest.mark.parametrize("item_id", [
        1,           # Valid ID
        0,           # Zero ID (invalid, should return 404)
        -1,          # Negative ID (invalid, should return 404)
        2,           # ID that doesn't exist
        999999,      # Large ID that doesn't exist
        2147483647,  # MAX_INT (boundary)
    ])
    def test_get_item_various_ids(self, item_id):
        """Test GET with various item IDs."""
        r = client.get(f"/items/{item_id}")
        if item_id == 1:
            assert r.status_code == 200
            assert r.json()["id"] == 1
        else:
            assert r.status_code == 404
            assert "not found" in r.json()["detail"]

    def test_get_item_id_zero(self):
        """Test that item_id=0 returns 404."""
        r = client.get("/items/0")
        assert r.status_code == 404
        assert "not found" in r.json()["detail"]

    def test_get_item_negative_id(self):
        """Test that negative item_id returns 404."""
        r = client.get("/items/-1")
        assert r.status_code == 404
        assert "not found" in r.json()["detail"]

    def test_get_item_id_two(self):
        """Test that item_id=2 returns 404."""
        r = client.get("/items/2")
        assert r.status_code == 404

    def test_get_item_very_large_id(self):
        """Test that very large item_id returns 404."""
        r = client.get("/items/999999999999999")
        assert r.status_code == 404


class TestGetItemResponseValidation:
    """Test response structure and content for valid item."""

    def test_get_item_response_structure(self):
        """Test that response has correct structure."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_get_item_response_values(self):
        """Test that response values are correct."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0

    def test_get_item_response_types(self):
        """Test that response field types are correct."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_get_item_response_content_type(self):
        """Test that response has correct content type."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")


class TestGetItemErrorResponse:
    """Test error response for not found items."""

    def test_get_item_404_response_structure(self):
        """Test that 404 response has detail field."""
        r = client.get("/items/2")
        assert r.status_code == 404
        data = r.json()
        assert "detail" in data

    def test_get_item_404_detail_message(self):
        """Test that 404 detail message is correct."""
        r = client.get("/items/2")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_404_response_content_type(self):
        """Test that 404 response has correct content type."""
        r = client.get("/items/2")
        assert r.status_code == 404
        assert "application/json" in r.headers.get("content-type", "")


class TestGetItemPathParameterHandling:
    """Test path parameter handling and type coercion."""

    def test_get_item_string_id_numeric(self):
        """Test that numeric strings are coerced to int."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_get_item_leading_zeros(self):
        """Test that IDs with leading zeros are handled."""
        r = client.get("/items/01")
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_get_item_large_number_string(self):
        """Test that large numeric strings are handled."""
        r = client.get("/items/999999999999999999999")
        # Either 404 or may cause issues depending on FastAPI version
        assert r.status_code in [404, 422]


class TestGetItemMultipleRequests:
    """Test multiple consecutive requests."""

    def test_get_item_idempotent(self):
        """Test that multiple identical requests return same result."""
        r1 = client.get("/items/1")
        r2 = client.get("/items/1")
        assert r1.status_code == r2.status_code == 200
        assert r1.json() == r2.json()

    def test_get_item_sequence_same_id(self):
        """Test sequence of requests for same ID."""
        for _ in range(3):
            r = client.get("/items/1")
            assert r.status_code == 200
            assert r.json()["id"] == 1

    def test_get_item_sequence_different_ids(self):
        """Test sequence of requests for different IDs."""
        for item_id in [1, 2, 3, 4, 5]:
            r = client.get(f"/items/{item_id}")
            if item_id == 1:
                assert r.status_code == 200
            else:
                assert r.status_code == 404

    def test_get_item_interleaved_valid_invalid(self):
        """Test interleaved valid and invalid requests."""
        r1 = client.get("/items/1")
        assert r1.status_code == 200

        r2 = client.get("/items/2")
        assert r2.status_code == 404

        r3 = client.get("/items/1")
        assert r3.status_code == 200

        assert r1.json() == r3.json()
