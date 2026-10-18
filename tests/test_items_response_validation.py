"""Comprehensive response validation tests for all endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemResponseStructure:
    """Test the structure and types of create_item response."""

    def test_create_item_response_has_required_fields(self):
        """Test that response has all required fields."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data
        assert len(data) == 3  # exactly 3 fields

    def test_create_item_response_field_types(self):
        """Test that response fields have correct types."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_create_item_response_id_value(self):
        """Test that id is always 1 in mock endpoint."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_create_item_response_name_matches_request(self):
        """Test that response name matches request."""
        test_name = "specific-item"
        r = client.post("/items", json={"name": test_name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == test_name

    def test_create_item_response_price_matches_request(self):
        """Test that response price matches request."""
        test_price = 42.99
        r = client.post("/items", json={"name": "test", "price": test_price})
        assert r.status_code == 200
        assert r.json()["price"] == test_price

    @pytest.mark.parametrize("name,price", [
        ("book", 19.99),
        ("pen", 0.99),
        ("desk", 199.99),
        ("chair", 89.50),
    ])
    def test_create_item_response_consistency(self, name, price):
        """Test response consistency across various inputs."""
        r = client.post("/items", json={"name": name, "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name
        assert data["price"] == price
        assert data["id"] == 1


class TestCreateItemErrorResponse:
    """Test error response structure and messages."""

    def test_invalid_price_error_structure(self):
        """Test that error response has correct structure."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400
        data = r.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

    def test_invalid_price_error_message_content(self):
        """Test that error message is informative."""
        r = client.post("/items", json={"name": "test", "price": -5})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]

    def test_missing_field_error_status_code(self):
        """Test that missing field returns 422 status code."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422

    def test_missing_field_error_has_detail(self):
        """Test that validation error has detail field."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422
        assert "detail" in r.json()

    def test_wrong_type_error_status_code(self):
        """Test that wrong type returns 422 status code."""
        r = client.post("/items", json={"name": "test", "price": "invalid"})
        assert r.status_code == 422

    @pytest.mark.parametrize("price", [0, -1, -10.5])
    def test_negative_price_error_consistency(self, price):
        """Test that price validation error is consistent."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"


class TestGetItemResponseStructure:
    """Test the structure and types of get_item response."""

    def test_get_item_response_has_required_fields(self):
        """Test that response has all required fields."""
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
        assert isinstance(data["price"], (int, float))

    def test_get_item_response_id_value(self):
        """Test that get_item returns correct id."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_get_item_response_name_value(self):
        """Test that get_item returns expected name."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["name"] == "sample"

    def test_get_item_response_price_value(self):
        """Test that get_item returns expected price."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["price"] == 10.0

    def test_get_item_response_consistent_structure(self):
        """Test that response structure is consistent on repeated calls."""
        r1 = client.get("/items/1")
        r2 = client.get("/items/1")
        assert r1.json() == r2.json()
        assert r1.status_code == r2.status_code == 200


class TestGetItemNotFoundResponse:
    """Test error response for not found items."""

    def test_not_found_error_status_code(self):
        """Test that not found returns 404 status code."""
        r = client.get("/items/2")
        assert r.status_code == 404

    def test_not_found_error_has_detail(self):
        """Test that not found error has detail field."""
        r = client.get("/items/2")
        assert "detail" in r.json()

    def test_not_found_error_message(self):
        """Test not found error message."""
        r = client.get("/items/2")
        assert r.json()["detail"] == "not found"

    @pytest.mark.parametrize("item_id", [2, 3, 999, -1])
    def test_not_found_various_ids(self, item_id):
        """Test not found error for various item IDs."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"


class TestHealthEndpoint:
    """Test health check endpoint response."""

    def test_health_status_code(self):
        """Test that health endpoint returns 200."""
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_response_structure(self):
        """Test that health response has status field."""
        r = client.get("/health")
        data = r.json()
        assert "status" in data

    def test_health_response_value(self):
        """Test that health status is 'ok'."""
        r = client.get("/health")
        assert r.json()["status"] == "ok"

    def test_health_response_type(self):
        """Test that health response is dict."""
        r = client.get("/health")
        assert isinstance(r.json(), dict)

    def test_health_repeated_calls_consistent(self):
        """Test that health check is consistent."""
        responses = [client.get("/health").json() for _ in range(3)]
        assert all(r == responses[0] for r in responses)


class TestContentTypeHeaders:
    """Test response content type headers."""

    def test_create_item_content_type(self):
        """Test that create_item returns JSON content type."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert "application/json" in r.headers.get("content-type", "")

    def test_get_item_content_type(self):
        """Test that get_item returns JSON content type."""
        r = client.get("/items/1")
        assert "application/json" in r.headers.get("content-type", "")

    def test_health_content_type(self):
        """Test that health endpoint returns JSON content type."""
        r = client.get("/health")
        assert "application/json" in r.headers.get("content-type", "")

    def test_error_response_content_type(self):
        """Test that error responses return JSON content type."""
        r = client.post("/items", json={"name": "test", "price": -1})
        assert "application/json" in r.headers.get("content-type", "")


class TestResponseRobustness:
    """Test response behavior edge cases."""

    def test_get_item_with_string_looking_id(self):
        """Test that invalid item_id format is handled."""
        r = client.get("/items/abc")
        # FastAPI will return 422 for invalid path parameter type
        assert r.status_code in [404, 422]

    def test_create_item_large_name_accepted(self):
        """Test that large names are accepted."""
        large_name = "x" * 1000
        r = client.post("/items", json={"name": large_name, "price": 10.0})
        assert r.status_code == 200
        assert len(r.json()["name"]) == 1000

    def test_create_item_whitespace_preserved_in_name(self):
        """Test that whitespace in names is preserved."""
        name_with_spaces = "  test  item  "
        r = client.post("/items", json={"name": name_with_spaces, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name_with_spaces
