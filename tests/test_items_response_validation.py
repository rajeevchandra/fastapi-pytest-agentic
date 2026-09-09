"""
Response structure and error handling validation tests.
Tests response field validation, error formats, and HTTP status codes.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemHTTPStatusCodes:
    """Test HTTP status code responses for POST /items."""

    def test_create_item_success_status_200(self):
        """Successful item creation returns 200."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert r.status_code == 200

    def test_create_item_invalid_price_status_400(self):
        """Invalid price returns 400."""
        r = client.post("/items", json={"name": "book", "price": 0})
        assert r.status_code == 400

    def test_create_item_missing_field_status_422(self):
        """Missing required field returns 422."""
        r = client.post("/items", json={"name": "book"})
        assert r.status_code == 422

    def test_create_item_invalid_type_status_422(self):
        """Invalid field type returns 422."""
        r = client.post("/items", json={"name": "book", "price": "invalid"})
        assert r.status_code == 422


class TestCreateItemErrorResponse:
    """Test error response format for POST /items."""

    def test_create_item_error_has_detail_field(self):
        """Error responses should have a 'detail' field."""
        r = client.post("/items", json={"name": "book", "price": 0})
        assert "detail" in r.json()

    def test_create_item_price_error_message(self):
        """Price validation error has correct message."""
        r = client.post("/items", json={"name": "book", "price": 0})
        assert r.json()["detail"] == "price must be > 0"

    def test_create_item_validation_error_format(self):
        """Pydantic validation errors have standard format."""
        r = client.post("/items", json={"name": "book"})
        data = r.json()
        assert "detail" in data

    @pytest.mark.parametrize("price", [-1, -100, 0])
    def test_create_item_non_positive_error_message(self, price):
        """All non-positive prices produce same error message."""
        r = client.post("/items", json={"name": "book", "price": price})
        assert r.json()["detail"] == "price must be > 0"


class TestGetItemHTTPStatusCodes:
    """Test HTTP status code responses for GET /items/{item_id}."""

    def test_get_item_found_status_200(self):
        """Getting existing item returns 200."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_get_item_not_found_status_404(self):
        """Getting non-existent item returns 404."""
        r = client.get("/items/2")
        assert r.status_code == 404

    @pytest.mark.parametrize("item_id", [2, 3, 4, 5, 100])
    def test_get_item_various_not_found_ids(self, item_id):
        """All IDs except 1 return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404


class TestGetItemErrorResponse:
    """Test error response format for GET /items/{item_id}."""

    def test_get_item_not_found_has_detail(self):
        """404 response should have 'detail' field."""
        r = client.get("/items/2")
        assert "detail" in r.json()

    def test_get_item_not_found_message(self):
        """404 error has correct message."""
        r = client.get("/items/2")
        assert r.json()["detail"] == "not found"

    def test_get_item_error_is_consistent(self):
        """Error message is consistent across different missing IDs."""
        for item_id in [2, 3, 100]:
            r = client.get(f"/items/{item_id}")
            assert r.json()["detail"] == "not found"


class TestCreateItemResponseFields:
    """Test response field presence and correctness for POST /items."""

    def test_create_item_has_all_fields(self):
        """Response has id, name, and price fields."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        data = r.json()
        assert set(data.keys()) >= {"id", "name", "price"}

    def test_create_item_id_is_integer(self):
        """Response id field is an integer."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert isinstance(r.json()["id"], int)

    def test_create_item_name_is_string(self):
        """Response name field is a string."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert isinstance(r.json()["name"], str)

    def test_create_item_price_is_number(self):
        """Response price field is numeric."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        price = r.json()["price"]
        assert isinstance(price, (int, float))

    def test_create_item_name_preserved(self):
        """Response name matches request name."""
        name = "my special book"
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.json()["name"] == name

    def test_create_item_price_preserved(self):
        """Response price matches request price."""
        price = 25.50
        r = client.post("/items", json={"name": "book", "price": price})
        assert r.json()["price"] == price


class TestGetItemResponseFields:
    """Test response field presence and correctness for GET /items/{item_id}."""

    def test_get_item_has_all_fields(self):
        """Response has id, name, and price fields."""
        r = client.get("/items/1")
        data = r.json()
        assert set(data.keys()) >= {"id", "name", "price"}

    def test_get_item_id_is_integer(self):
        """Response id field is an integer."""
        r = client.get("/items/1")
        assert isinstance(r.json()["id"], int)

    def test_get_item_name_is_string(self):
        """Response name field is a string."""
        r = client.get("/items/1")
        assert isinstance(r.json()["name"], str)

    def test_get_item_price_is_number(self):
        """Response price field is numeric."""
        r = client.get("/items/1")
        price = r.json()["price"]
        assert isinstance(price, (int, float))

    def test_get_item_has_expected_data(self):
        """Item 1 returns expected data."""
        r = client.get("/items/1")
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0


class TestResponseContentType:
    """Test response content-type headers."""

    def test_create_item_json_content_type(self):
        """POST response has JSON content type."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert "application/json" in r.headers.get("content-type", "")

    def test_get_item_json_content_type(self):
        """GET response has JSON content type."""
        r = client.get("/items/1")
        assert "application/json" in r.headers.get("content-type", "")

    def test_error_response_json_content_type(self):
        """Error response has JSON content type."""
        r = client.get("/items/2")
        assert "application/json" in r.headers.get("content-type", "")


class TestHTTPMethods:
    """Test HTTP method validation."""

    def test_post_items_accepts_post(self):
        """POST /items accepts POST method."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert r.status_code in [200, 400, 422]

    def test_get_items_accepts_get(self):
        """GET /items/{id} accepts GET method."""
        r = client.get("/items/1")
        assert r.status_code in [200, 404]

    def test_get_items_rejects_post(self):
        """GET /items/{id} rejects POST method."""
        r = client.post("/items/1")
        assert r.status_code == 405


class TestHealthEndpoint:
    """Test /health endpoint response."""

    def test_health_status_200(self):
        """Health endpoint returns 200."""
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_response_structure(self):
        """Health response has status field."""
        r = client.get("/health")
        assert "status" in r.json()

    def test_health_response_ok(self):
        """Health status is 'ok'."""
        r = client.get("/health")
        assert r.json()["status"] == "ok"

    def test_health_json_content_type(self):
        """Health response is JSON."""
        r = client.get("/health")
        assert "application/json" in r.headers.get("content-type", "")
