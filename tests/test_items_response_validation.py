import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemResponseStructure:
    """Test response structure and field types."""

    def test_create_item_response_structure(self):
        """Response should have correct structure."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)
        assert set(data.keys()) == {"id", "name", "price"}

    def test_create_item_response_field_types(self):
        """Response fields should have correct types."""
        r = client.post("/items", json={"name": "book", "price": 10.5})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], float)

    def test_create_item_response_id_always_one(self):
        """ID in response should always be 1 (hardcoded)."""
        r = client.post("/items", json={"name": "book", "price": 5.0})
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_create_item_response_name_matches_input(self):
        """Response name should match input."""
        r = client.post("/items", json={"name": "test-book", "price": 5.0})
        assert r.status_code == 200
        assert r.json()["name"] == "test-book"

    def test_create_item_response_price_matches_input(self):
        """Response price should match input."""
        r = client.post("/items", json={"name": "book", "price": 15.75})
        assert r.status_code == 200
        assert r.json()["price"] == 15.75


class TestCreateItemHTTPStatusCodes:
    """Test HTTP status codes for create_item endpoint."""

    def test_create_item_success_returns_200(self):
        """Successful create should return 200."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert r.status_code == 200

    def test_create_item_invalid_price_returns_400(self):
        """Invalid price should return 400 Bad Request."""
        r = client.post("/items", json={"name": "book", "price": 0})
        assert r.status_code == 400

    def test_create_item_missing_field_returns_422(self):
        """Missing required field should return 422 Unprocessable Entity."""
        r = client.post("/items", json={"name": "book"})
        assert r.status_code == 422

    def test_create_item_invalid_type_returns_422(self):
        """Invalid field type should return 422."""
        r = client.post("/items", json={"name": "book", "price": "invalid"})
        assert r.status_code == 422


class TestCreateItemErrorResponses:
    """Test error response format and content."""

    def test_create_item_error_response_has_detail(self):
        """Error responses should have detail field."""
        r = client.post("/items", json={"name": "book", "price": -1})
        assert r.status_code == 400
        assert "detail" in r.json()

    def test_create_item_price_error_message_content(self):
        """Price error should have specific message."""
        r = client.post("/items", json={"name": "book", "price": 0})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    def test_create_item_validation_error_structure(self):
        """Validation error should have detail field."""
        r = client.post("/items", json={"name": "book"})
        assert r.status_code == 422
        assert "detail" in r.json()

    @pytest.mark.parametrize("negative_price", [-1, -0.5, -100])
    def test_create_item_all_negative_prices_rejected(self, negative_price):
        """All negative prices should be rejected."""
        r = client.post("/items", json={"name": "book", "price": negative_price})
        assert r.status_code == 400


class TestGetItemResponseStructure:
    """Test GET /items/{item_id} response structure."""

    def test_get_item_found_response_structure(self):
        """Response should have correct structure when item found."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert set(data.keys()) == {"id", "name", "price"}

    def test_get_item_found_response_types(self):
        """Response fields should have correct types."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], float)

    def test_get_item_found_response_content(self):
        """Response should contain expected values."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0


class TestGetItemHTTPStatusCodes:
    """Test HTTP status codes for GET /items/{item_id}."""

    def test_get_item_found_returns_200(self):
        """Getting existing item should return 200."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_get_item_not_found_returns_404(self):
        """Getting non-existent item should return 404."""
        r = client.get("/items/2")
        assert r.status_code == 404

    @pytest.mark.parametrize("item_id", [2, 3, 100, 999])
    def test_get_item_any_id_except_1_returns_404(self, item_id):
        """Any item_id other than 1 should return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404


class TestGetItemErrorResponses:
    """Test error response format."""

    def test_get_item_not_found_error_has_detail(self):
        """Not found error should have detail field."""
        r = client.get("/items/2")
        assert r.status_code == 404
        assert "detail" in r.json()

    def test_get_item_not_found_error_message(self):
        """Not found error should have specific message."""
        r = client.get("/items/2")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"


class TestHealthCheckResponse:
    """Test health check endpoint response."""

    def test_health_check_returns_200(self):
        """Health check should return 200."""
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_check_response_structure(self):
        """Health check should return expected structure."""
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}

    def test_health_check_response_type(self):
        """Health check response should be a dict."""
        r = client.get("/health")
        assert isinstance(r.json(), dict)

    def test_health_check_contains_status_field(self):
        """Health check should have status field."""
        r = client.get("/health")
        assert "status" in r.json()

    def test_health_check_status_value_is_ok(self):
        """Health check status should be 'ok'."""
        r = client.get("/health")
        assert r.json()["status"] == "ok"


class TestResponseContentType:
    """Test response content type headers."""

    def test_create_item_response_content_type(self):
        """Response should have JSON content type."""
        r = client.post("/items", json={"name": "book", "price": 10.0})
        assert "application/json" in r.headers.get("content-type", "")

    def test_get_item_response_content_type(self):
        """Response should have JSON content type."""
        r = client.get("/items/1")
        assert "application/json" in r.headers.get("content-type", "")

    def test_health_check_response_content_type(self):
        """Response should have JSON content type."""
        r = client.get("/health")
        assert "application/json" in r.headers.get("content-type", "")
