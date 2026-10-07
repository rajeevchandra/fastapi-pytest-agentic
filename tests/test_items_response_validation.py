import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemResponseStructure:
    """Tests for response structure of create_item endpoint."""

    def test_create_item_response_has_all_fields(self):
        """Test that response contains all required fields."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data
        # Should not have extra fields from input validation
        assert len(data) == 3

    def test_create_item_response_field_types(self):
        """Test that response fields have correct types."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_create_item_response_id_always_one(self):
        """Test that create_item always returns id=1 (mock behavior)."""
        r1 = client.post("/items", json={"name": "item1", "price": 5.0})
        r2 = client.post("/items", json={"name": "item2", "price": 15.0})
        assert r1.json()["id"] == 1
        assert r2.json()["id"] == 1

    def test_create_item_response_preserves_name(self):
        """Test that response name matches request."""
        test_names = ["book", "pen", "A", "very long item name" * 10]
        for name in test_names:
            r = client.post("/items", json={"name": name, "price": 10.0})
            assert r.json()["name"] == name

    def test_create_item_response_preserves_price(self):
        """Test that response price matches request."""
        test_prices = [0.01, 1, 100, 9999.99]
        for price in test_prices:
            r = client.post("/items", json={"name": "item", "price": price})
            assert r.json()["price"] == price

    def test_create_item_response_content_type(self):
        """Test that response has correct content type."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.headers["content-type"] == "application/json"


class TestCreateItemErrorResponseStructure:
    """Tests for error response structure."""

    def test_create_item_error_response_has_detail(self):
        """Test that error response has detail field."""
        r = client.post("/items", json={"name": "bad", "price": 0})
        assert r.status_code == 400
        data = r.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

    def test_create_item_error_detail_message(self):
        """Test that error detail contains useful message."""
        r = client.post("/items", json={"name": "bad", "price": 0})
        assert "price" in r.json()["detail"].lower()

    def test_create_item_validation_error_structure(self):
        """Test structure of validation error (422)."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422
        data = r.json()
        # FastAPI validation errors have 'detail' key with error list
        assert "detail" in data
        assert isinstance(data["detail"], list)
        assert len(data["detail"]) > 0

    def test_create_item_validation_error_has_field_info(self):
        """Test that validation errors include field information."""
        r = client.post("/items", json={"name": "test"})
        errors = r.json()["detail"]
        # Should have error info about missing 'price' field
        error_fields = [e.get("loc", []) for e in errors]
        assert any("price" in str(loc) for loc in error_fields)


class TestGetItemResponseStructure:
    """Tests for response structure of get_item endpoint."""

    def test_get_item_response_has_all_fields(self):
        """Test that GET response contains all fields."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_get_item_response_field_types(self):
        """Test that GET response fields have correct types."""
        r = client.get("/items/1")
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_get_item_response_content_type(self):
        """Test that GET response has correct content type."""
        r = client.get("/items/1")
        assert r.headers["content-type"] == "application/json"

    def test_get_item_success_response_consistent(self):
        """Test that GET /items/1 returns consistent data."""
        r1 = client.get("/items/1")
        r2 = client.get("/items/1")
        assert r1.json() == r2.json()

    def test_get_item_response_values(self):
        """Test that GET response has expected values."""
        r = client.get("/items/1")
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0


class TestGetItemErrorResponseStructure:
    """Tests for error response structure in GET endpoint."""

    def test_get_item_not_found_error_has_detail(self):
        """Test that 404 response has detail field."""
        r = client.get("/items/2")
        assert r.status_code == 404
        data = r.json()
        assert "detail" in data

    def test_get_item_not_found_detail_message(self):
        """Test that 404 detail contains useful message."""
        r = client.get("/items/2")
        assert "not found" in r.json()["detail"].lower()

    def test_get_item_error_response_consistent(self):
        """Test that 404 responses are consistent."""
        r1 = client.get("/items/2")
        r2 = client.get("/items/999")
        assert r1.status_code == 404
        assert r2.status_code == 404


class TestHTTPStatusCodes:
    """Tests for HTTP status codes across all endpoints."""

    def test_create_item_success_status(self):
        """Test POST success returns 200."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200

    def test_create_item_validation_error_status(self):
        """Test POST with missing field returns 422."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422

    def test_create_item_business_logic_error_status(self):
        """Test POST with invalid price returns 400."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400

    def test_get_item_found_status(self):
        """Test GET with found item returns 200."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_get_item_not_found_status(self):
        """Test GET with missing item returns 404."""
        r = client.get("/items/2")
        assert r.status_code == 404

    def test_get_item_not_found_various_ids(self):
        """Test GET returns 404 for various non-existent IDs."""
        for item_id in [2, 3, 100, 999]:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404


class TestResponseHeaders:
    """Tests for response headers."""

    def test_create_item_response_has_content_type(self):
        """Test POST response includes content-type header."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert "content-type" in r.headers

    def test_get_item_response_has_content_type(self):
        """Test GET response includes content-type header."""
        r = client.get("/items/1")
        assert "content-type" in r.headers

    def test_error_response_has_content_type(self):
        """Test error response includes content-type header."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert "content-type" in r.headers
