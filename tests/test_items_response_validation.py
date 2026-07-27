"""
Response structure and error handling validation tests.
Tests response fields, types, HTTP status codes, and error consistency.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemResponseStructure:
    """Tests for validating response structure and field types."""

    def test_create_item_response_has_all_fields(self):
        """Test that success response includes id, name, and price."""
        r = client.post("/items", json={"name": "book", "price": 10.5})
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data
        assert len(data) == 3  # Exactly these 3 fields

    def test_create_item_response_field_types(self):
        """Test that response fields have correct types."""
        r = client.post("/items", json={"name": "pen", "price": 1.5})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_create_item_returns_same_values(self):
        """Test that response contains the input values."""
        input_name = "test_item"
        input_price = 25.99
        r = client.post("/items", json={"name": input_name, "price": input_price})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == input_name
        assert data["price"] == input_price


class TestGetItemResponseStructure:
    """Tests for GET /items/{item_id} response validation."""

    def test_get_item_found_response_structure(self):
        """Test that successful GET response has correct structure."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data
        assert len(data) == 3

    def test_get_item_found_field_types(self):
        """Test that GET response fields have correct types."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_get_item_found_values_match_hardcoded(self):
        """Test that GET /items/1 returns expected hardcoded values."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0


class TestErrorResponseStructure:
    """Tests for error response format consistency."""

    def test_error_response_has_detail_field(self):
        """Test that error responses include a detail field."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.status_code == 400
        data = r.json()
        assert "detail" in data

    def test_price_error_detail_message(self):
        """Test specific error message for price validation."""
        r = client.post("/items", json={"name": "item", "price": -1})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]

    def test_not_found_error_detail_message(self):
        """Test specific error message for not found."""
        r = client.get("/items/999")
        assert r.status_code == 404
        assert "not found" in r.json()["detail"]

    def test_validation_error_response_format(self):
        """Test that validation errors (422) have proper format."""
        r = client.post("/items", json={"name": "item"})  # Missing price
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data

    def test_malformed_json_error(self):
        """Test handling of malformed JSON."""
        r = client.post("/items", content="{invalid json")
        assert r.status_code == 422


class TestHTTPStatusCodes:
    """Parametrized tests for various HTTP status code scenarios."""

    @pytest.mark.parametrize("scenario,expected_status", [
        ("get_found", 200),
        ("get_not_found", 404),
        ("post_valid", 200),
        ("post_invalid_price", 400),
        ("post_missing_field", 422),
        ("health_check", 200),
    ])
    def test_status_codes(self, scenario, expected_status):
        """Test various scenarios return expected status codes."""
        if scenario == "get_found":
            r = client.get("/items/1")
        elif scenario == "get_not_found":
            r = client.get("/items/2")
        elif scenario == "post_valid":
            r = client.post("/items", json={"name": "item", "price": 1.0})
        elif scenario == "post_invalid_price":
            r = client.post("/items", json={"name": "item", "price": 0})
        elif scenario == "post_missing_field":
            r = client.post("/items", json={"name": "item"})
        elif scenario == "health_check":
            r = client.get("/health")
        
        assert r.status_code == expected_status


class TestContentTypeHeaders:
    """Tests for response content types."""

    def test_json_response_content_type(self):
        """Test that responses have correct content-type header."""
        r = client.get("/items/1")
        assert "application/json" in r.headers.get("content-type", "")

    def test_error_response_content_type(self):
        """Test that error responses have correct content-type."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert "application/json" in r.headers.get("content-type", "")

    def test_health_response_content_type(self):
        """Test health endpoint response content-type."""
        r = client.get("/health")
        assert "application/json" in r.headers.get("content-type", "")
