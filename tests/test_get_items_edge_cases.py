"""
Tests for GET /items/{item_id} endpoint edge cases and error handling.

This test module focuses on boundary values, invalid types, and edge cases
for the item retrieval endpoint as outlined in Coverage Plan PR #2.
"""

from fastapi.testclient import TestClient
from app.main import app
import sys

client = TestClient(app)


class TestGetItemBoundaryValues:
    """Test boundary values for item_id parameter."""

    def test_get_item_id_zero(self):
        """Test that item_id=0 is handled correctly (not found)."""
        r = client.get("/items/0")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_id_negative(self):
        """Test that negative item_id is handled correctly."""
        r = client.get("/items/-1")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_id_large_negative(self):
        """Test that large negative item_id is handled correctly."""
        r = client.get("/items/-999999")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_id_max_int(self):
        """Test that maximum integer item_id is handled correctly."""
        max_int = sys.maxsize
        r = client.get(f"/items/{max_int}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_id_very_large(self):
        """Test that very large item_id values are handled correctly."""
        r = client.get("/items/999999999")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"


class TestGetItemInvalidTypes:
    """Test invalid data types for item_id path parameter."""

    def test_get_item_string_id(self):
        """Test that string item_id returns validation error."""
        r = client.get("/items/abc")
        assert r.status_code == 422  # Unprocessable Entity
        detail = r.json()
        assert "detail" in detail
        # FastAPI returns validation error for type mismatch

    def test_get_item_float_id(self):
        """Test that float item_id returns validation error."""
        r = client.get("/items/1.5")
        assert r.status_code == 422
        detail = r.json()
        assert "detail" in detail

    def test_get_item_special_chars(self):
        """Test that special characters in item_id return validation error."""
        r = client.get("/items/@#$")
        assert r.status_code == 422
        detail = r.json()
        assert "detail" in detail

    def test_get_item_empty_id(self):
        """Test that empty item_id is handled correctly."""
        # This should match a different route or return 404
        r = client.get("/items/")
        assert r.status_code in [404, 405]  # Not Found or Method Not Allowed


class TestGetItemResponseStructure:
    """Test response structure and validation for successful GET requests."""

    def test_get_existing_item_response_structure(self):
        """Test that successful GET returns complete response structure."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        
        # Verify all expected fields are present
        assert "id" in data
        assert "name" in data
        assert "price" in data
        
        # Verify data types
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))
        
        # Verify specific values for item_id=1
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0

    def test_get_item_response_headers(self):
        """Test that response has correct content-type header."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")

    def test_get_item_error_response_structure(self):
        """Test that error responses have correct structure."""
        r = client.get("/items/999")
        assert r.status_code == 404
        data = r.json()
        
        # FastAPI error responses have 'detail' field
        assert "detail" in data
        assert isinstance(data["detail"], str)
        assert data["detail"] == "not found"


class TestGetItemURLEncoding:
    """Test URL encoding edge cases for item_id parameter."""

    def test_get_item_url_encoded_number(self):
        """Test that URL-encoded numbers are decoded correctly."""
        # %31 is URL encoding for '1'
        r = client.get("/items/%31")
        # FastAPI/Starlette should decode this to 1
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_get_item_url_encoded_invalid(self):
        """Test that URL-encoded non-numeric values return validation error."""
        # %61%62%63 is URL encoding for 'abc'
        r = client.get("/items/%61%62%63")
        assert r.status_code == 422
        assert "detail" in r.json()

    def test_get_item_percent_encoding_edge_case(self):
        """Test malformed percent encoding in item_id."""
        # Incomplete percent encoding
        r = client.get("/items/%2")
        # This should either be decoded or treated as invalid
        assert r.status_code in [404, 422, 400]
