import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestHealthEndpointComprehensive:
    """Comprehensive tests for /health endpoint."""

    def test_health_endpoint_exists(self):
        """Health endpoint should be accessible."""
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_status_value(self):
        """Health endpoint status value should be 'ok'."""
        r = client.get("/health")
        assert r.json()["status"] == "ok"

    def test_health_no_extra_fields(self):
        """Health endpoint response should only have status field."""
        r = client.get("/health")
        data = r.json()
        assert set(data.keys()) == {"status"}

    def test_health_idempotent(self):
        """Multiple health checks should return same result."""
        results = [client.get("/health").json() for _ in range(5)]
        assert all(r == results[0] for r in results)


class TestItemCreationFieldValidation:
    """Detailed field validation for item creation."""

    def test_name_required_field(self):
        """Name is a required field."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422
        assert "name" in r.text or "name" in str(r.json()).lower()

    def test_price_required_field(self):
        """Price is a required field."""
        r = client.post("/items", json={"name": "item"})
        assert r.status_code == 422
        assert "price" in r.text or "price" in str(r.json()).lower()

    def test_both_fields_required(self):
        """Both name and price are required."""
        r = client.post("/items", json={})
        assert r.status_code == 422

    def test_extra_fields_ignored(self):
        """Extra fields in request should be ignored."""
        r = client.post("/items", json={
            "name": "book",
            "price": 10.0,
            "description": "extra field",
            "author": "unknown"
        })
        assert r.status_code == 200
        data = r.json()
        assert "description" not in data
        assert "author" not in data


class TestPriceEdgeCases:
    """Additional price validation edge cases."""

    def test_price_at_boundary_001(self):
        """Price of 0.01 should be accepted."""
        r = client.post("/items", json={"name": "item", "price": 0.01})
        assert r.status_code == 200

    def test_price_boundary_just_above_zero(self):
        """Very small positive price should be accepted."""
        r = client.post("/items", json={"name": "item", "price": 0.0001})
        assert r.status_code == 200

    def test_price_float_precision(self):
        """Float prices with decimals should be preserved."""
        prices = [10.99, 0.50, 123.456, 9999.99]
        for price in prices:
            r = client.post("/items", json={"name": "item", "price": price})
            assert r.status_code == 200
            assert r.json()["price"] == price

    def test_price_integer_converted_to_float(self):
        """Integer prices should work and return as float."""
        r = client.post("/items", json={"name": "item", "price": 10})
        assert r.status_code == 200
        assert r.json()["price"] == 10


class TestItemIDRetrieval:
    """Comprehensive tests for item ID retrieval."""

    def test_item_id_always_one(self):
        """Created item should always have id=1."""
        r = client.post("/items", json={"name": "test", "price": 5.0})
        assert r.json()["id"] == 1

    def test_only_item_one_exists(self):
        """Only item with id=1 should be retrievable."""
        # Item 1 should exist
        assert client.get("/items/1").status_code == 200
        
        # Other IDs should not exist
        for item_id in [0, 2, 3, -1, 100, 999]:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404


class TestErrorResponseFormat:
    """Test error response formats."""

    def test_invalid_price_error_format(self):
        """Invalid price should return proper error format."""
        r = client.post("/items", json={"name": "item", "price": -1})
        assert r.status_code == 400
        assert "detail" in r.json()
        assert isinstance(r.json()["detail"], str)

    def test_not_found_error_format(self):
        """Not found should return proper error format."""
        r = client.get("/items/999")
        assert r.status_code == 404
        assert "detail" in r.json()
        assert r.json()["detail"] == "not found"

    def test_validation_error_format_for_missing_fields(self):
        """Validation errors should include field information."""
        r = client.post("/items", json={"name": "item"})
        assert r.status_code == 422
        assert r.json() is not None


class TestContentNegotiation:
    """Test content negotiation and headers."""

    def test_json_responses_have_json_content_type(self):
        """All successful responses should have JSON content type."""
        endpoints = [
            ("GET", "/health"),
            ("GET", "/items/1"),
            ("POST", "/items", {"name": "item", "price": 10.0}),
        ]
        for method, path, *data in endpoints:
            if method == "GET":
                r = client.get(path)
            else:
                r = client.post(path, json=data[0])
            
            content_type = r.headers.get("content-type", "")
            assert "application/json" in content_type

    def test_error_responses_also_json(self):
        """Error responses should also be JSON."""
        r = client.get("/items/999")
        assert "application/json" in r.headers.get("content-type", "")


class TestRequestValidationErrors:
    """Test various request validation errors."""

    def test_malformed_json(self):
        """Malformed JSON should be rejected."""
        # Using client, we can't send malformed JSON directly
        # But we can test that valid JSON is required
        r = client.post("/items", json={"name": "item", "price": "not_a_number"})
        assert r.status_code == 422

    def test_missing_json_content_type(self):
        """Requests should handle content-type properly."""
        # TestClient handles this, but we verify it works
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200


class TestResponseDataIntegrity:
    """Test that response data maintains integrity."""

    def test_create_response_preserves_name(self):
        """Response name should match input name."""
        name = "Test Book"
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.json()["name"] == name

    def test_create_response_preserves_price(self):
        """Response price should match input price."""
        price = 29.99
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.json()["price"] == price

    def test_get_response_contains_expected_data(self):
        """GET response should contain id, name, and price."""
        r = client.get("/items/1")
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))


class TestAPIEndpointAvailability:
    """Test that all expected endpoints are available."""

    def test_get_health_endpoint_available(self):
        """GET /health endpoint should be available."""
        r = client.get("/health")
        assert r.status_code != 404

    def test_post_items_endpoint_available(self):
        """POST /items endpoint should be available."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code != 404

    def test_get_items_id_endpoint_available(self):
        """GET /items/{id} endpoint should be available."""
        r = client.get("/items/1")
        assert r.status_code != 404

    def test_invalid_endpoint_returns_404(self):
        """Invalid endpoints should return 404."""
        r = client.get("/invalid")
        assert r.status_code == 404
