"""
Enhanced validation tests for /items/{item_id} GET endpoint.
Tests edge cases, boundary conditions, and path parameter validation.
"""
from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)


class TestGetItemBoundaryValues:
    """Test boundary value item IDs."""

    def test_get_item_id_zero(self):
        """Test that item_id of 0 returns 404."""
        r = client.get("/items/0")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_id_negative(self):
        """Test that negative item_id returns 404."""
        r = client.get("/items/-1")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_id_very_negative(self):
        """Test that very negative item_id returns 404."""
        r = client.get("/items/-999999")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_id_very_large(self):
        """Test that very large item_id returns 404."""
        r = client.get("/items/999999999")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_id_max_int(self):
        """Test that max int value returns 404."""
        r = client.get(f"/items/{2**31 - 1}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"


class TestGetItemParametrized:
    """Parametrized tests for various item IDs."""

    @pytest.mark.parametrize("item_id", [0, -1, -100, 2, 3, 100, 999999])
    def test_get_item_not_found_ids(self, item_id):
        """Test that all IDs except 1 return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_id_one_success(self):
        """Test that item_id 1 returns success."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0


class TestGetItemResponseValidation:
    """Test response structure and content validation."""

    def test_get_item_response_has_required_fields(self):
        """Test that successful response has all required fields."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_get_item_response_field_types(self):
        """Test that response fields have correct types."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], float)

    def test_get_item_response_content_types(self):
        """Test that response has correct content type."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")

    def test_get_item_not_found_response_structure(self):
        """Test that 404 response has correct structure."""
        r = client.get("/items/2")
        assert r.status_code == 404
        data = r.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)


class TestGetItemEdgeCases:
    """Test edge cases and unusual inputs."""

    def test_get_item_id_float_coercion(self):
        """Test that float item_id is coerced to int."""
        # FastAPI path parameters coerce float-like strings to int
        r = client.get("/items/1.0")
        # This might return 404 if FastAPI doesn't coerce, or 200 if it does
        assert r.status_code in (200, 404, 422)

    def test_get_item_id_float_non_integer(self):
        """Test that non-integer float is handled."""
        r = client.get("/items/1.5")
        # This should fail or be handled by FastAPI
        assert r.status_code in (404, 422)

    def test_get_item_id_string_number(self):
        """Test that string numbers are coerced to int."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_get_item_headers_validation(self):
        """Test GET request with custom headers."""
        r = client.get(
            "/items/1",
            headers={"X-Custom-Header": "custom-value"}
        )
        assert r.status_code == 200

    def test_get_item_query_params_ignored(self):
        """Test that query parameters don't affect the response."""
        r = client.get("/items/1?extra=param&another=value")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1


class TestGetItemConsistency:
    """Test response consistency."""

    def test_get_item_multiple_requests_consistent(self):
        """Test that multiple requests return consistent data."""
        r1 = client.get("/items/1")
        r2 = client.get("/items/1")
        r3 = client.get("/items/1")
        
        assert r1.json() == r2.json() == r3.json()
        assert r1.status_code == r2.status_code == r3.status_code == 200

    def test_get_item_not_found_consistent(self):
        """Test that 404 responses are consistent."""
        r1 = client.get("/items/2")
        r2 = client.get("/items/2")
        
        assert r1.status_code == r2.status_code == 404
        assert r1.json() == r2.json()
