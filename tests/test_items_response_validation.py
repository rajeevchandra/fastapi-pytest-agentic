"""
Response validation tests for API endpoints.

Tests cover:
- Response structure consistency
- Data type validation for all fields
- HTTP status codes for success and error cases
- Error response format consistency
- Response headers and content-type
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Test /health endpoint responses."""

    def test_health_status_code(self):
        """Should return 200 OK."""
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_response_structure(self):
        """Should return dict with 'status' key."""
        r = client.get("/health")
        data = r.json()
        assert isinstance(data, dict)
        assert "status" in data

    def test_health_response_value(self):
        """Should return status='ok'."""
        r = client.get("/health")
        data = r.json()
        assert data["status"] == "ok"

    def test_health_content_type(self):
        """Should return JSON content-type."""
        r = client.get("/health")
        assert "application/json" in r.headers.get("content-type", "")


class TestCreateItemSuccess:
    """Test successful /items POST responses."""

    def test_create_item_response_fields(self):
        """Should return id, name, and price fields."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_create_item_field_types(self):
        """Response fields should have correct types."""
        r = client.post("/items", json={"name": "widget", "price": 15.5})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_create_item_id_value(self):
        """Should return id=1 (hardcoded in implementation)."""
        r = client.post("/items", json={"name": "book", "price": 20.0})
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1

    def test_create_item_name_echo(self):
        """Response name should match request name."""
        test_name = "Special Product"
        r = client.post("/items", json={"name": test_name, "price": 25.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == test_name

    def test_create_item_price_echo(self):
        """Response price should match request price."""
        test_price = 33.75
        r = client.post("/items", json={"name": "item", "price": test_price})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == test_price

    def test_create_item_response_keys_only(self):
        """Response should contain only id, name, price (no extra fields)."""
        r = client.post("/items", json={"name": "clean", "price": 5.0})
        assert r.status_code == 200
        data = r.json()
        expected_keys = {"id", "name", "price"}
        assert set(data.keys()) == expected_keys


class TestCreateItemErrorResponse:
    """Test error response format for invalid prices."""

    def test_create_item_error_status_code(self):
        """Should return 400 for non-positive price."""
        r = client.post("/items", json={"name": "bad", "price": 0})
        assert r.status_code == 400

    def test_create_item_error_has_detail(self):
        """Error response should have 'detail' field."""
        r = client.post("/items", json={"name": "bad", "price": -1})
        assert r.status_code == 400
        data = r.json()
        assert "detail" in data

    def test_create_item_error_message(self):
        """Error detail should match expected message."""
        r = client.post("/items", json={"name": "bad", "price": -5})
        assert r.status_code == 400
        data = r.json()
        assert data["detail"] == "price must be > 0"

    def test_create_item_zero_price_error(self):
        """Zero price should produce correct error."""
        r = client.post("/items", json={"name": "zero", "price": 0})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    def test_create_item_large_negative_error(self):
        """Large negative price should produce correct error."""
        r = client.post("/items", json={"name": "neg", "price": -999.99})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"


class TestGetItemSuccess:
    """Test successful /items/{item_id} GET responses."""

    def test_get_item_found_status(self):
        """Should return 200 for valid item_id."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_get_item_found_response_fields(self):
        """Response should have id, name, price."""
        r = client.get("/items/1")
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_get_item_found_field_types(self):
        """Response fields should have correct types."""
        r = client.get("/items/1")
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_get_item_found_id_field(self):
        """Response id should be 1 (hardcoded)."""
        r = client.get("/items/1")
        data = r.json()
        assert data["id"] == 1

    def test_get_item_found_name_field(self):
        """Response name should be 'sample' (hardcoded)."""
        r = client.get("/items/1")
        data = r.json()
        assert data["name"] == "sample"

    def test_get_item_found_price_field(self):
        """Response price should be 10.0 (hardcoded)."""
        r = client.get("/items/1")
        data = r.json()
        assert data["price"] == 10.0

    def test_get_item_found_response_keys_only(self):
        """Response should contain only id, name, price."""
        r = client.get("/items/1")
        data = r.json()
        expected_keys = {"id", "name", "price"}
        assert set(data.keys()) == expected_keys


class TestGetItemNotFound:
    """Test not found responses for GET /items/{item_id}."""

    def test_get_item_not_found_status(self):
        """Should return 404 for non-existent item."""
        r = client.get("/items/2")
        assert r.status_code == 404

    def test_get_item_not_found_detail(self):
        """404 response should have detail field."""
        r = client.get("/items/2")
        data = r.json()
        assert "detail" in data

    def test_get_item_not_found_message(self):
        """404 detail should be 'not found'."""
        r = client.get("/items/2")
        data = r.json()
        assert data["detail"] == "not found"

    @pytest.mark.parametrize("item_id", [0, 3, 99, 999, -1, -100])
    def test_get_item_various_not_found_ids(self, item_id):
        """Should return 404 for any id other than 1."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        data = r.json()
        assert data["detail"] == "not found"


class TestResponseConsistency:
    """Test response consistency across multiple calls."""

    def test_get_item_idempotent(self):
        """Multiple calls for same item_id should return same response."""
        r1 = client.get("/items/1")
        r2 = client.get("/items/1")
        r3 = client.get("/items/1")
        
        data1 = r1.json()
        data2 = r2.json()
        data3 = r3.json()
        
        assert data1 == data2 == data3

    def test_create_item_consistent(self):
        """Multiple creates with same data should return same structure."""
        payload = {"name": "consistent", "price": 42.0}
        r1 = client.post("/items", json=payload)
        r2 = client.post("/items", json=payload)
        
        data1 = r1.json()
        data2 = r2.json()
        
        # Should have same structure and values (id is hardcoded to 1)
        assert data1["id"] == data2["id"] == 1
        assert data1["name"] == data2["name"] == "consistent"
        assert data1["price"] == data2["price"] == 42.0


class TestErrorResponseFormat:
    """Test error response format consistency."""

    def test_validation_error_has_detail(self):
        """Validation errors should have 'detail' field."""
        r = client.post("/items", json={})
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data

    def test_business_logic_error_has_detail(self):
        """Business logic errors should have 'detail' field."""
        r = client.post("/items", json={"name": "test", "price": -1})
        assert r.status_code == 400
        data = r.json()
        assert "detail" in data

    def test_not_found_error_has_detail(self):
        """Not found errors should have 'detail' field."""
        r = client.get("/items/999")
        assert r.status_code == 404
        data = r.json()
        assert "detail" in data
