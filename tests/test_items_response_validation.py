import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemHTTPStatusCodes:
    """Test HTTP status codes for POST /items endpoint."""

    @pytest.mark.parametrize(
        "payload",
        [
            {"name": "book", "price": 10.0},
            {"name": "pen", "price": 1.5},
            {"name": "notebook", "price": 5.99},
        ],
    )
    def test_create_item_success_returns_200(self, payload):
        """Test that valid items return 200 status."""
        r = client.post("/items", json=payload)
        assert r.status_code == 200

    @pytest.mark.parametrize(
        "payload",
        [
            {"name": "book", "price": 0},
            {"name": "pen", "price": -1},
            {"name": "notebook", "price": -99.99},
        ],
    )
    def test_create_item_invalid_price_returns_400(self, payload):
        """Test that non-positive prices return 400 status."""
        r = client.post("/items", json=payload)
        assert r.status_code == 400

    @pytest.mark.parametrize(
        "payload",
        [
            {"price": 10.0},
            {"name": "book"},
            {},
        ],
    )
    def test_create_item_missing_fields_returns_422(self, payload):
        """Test that missing fields return 422 status."""
        r = client.post("/items", json=payload)
        assert r.status_code == 422


class TestGetItemHTTPStatusCodes:
    """Test HTTP status codes for GET /items/{item_id} endpoint."""

    def test_get_existing_item_returns_200(self):
        """Test that getting an existing item returns 200 status."""
        r = client.get("/items/1")
        assert r.status_code == 200

    @pytest.mark.parametrize(
        "item_id",
        [2, 3, 100, -1, 999999],
    )
    def test_get_nonexistent_item_returns_404(self, item_id):
        """Test that getting a non-existent item returns 404 status."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404


class TestCreateItemResponseValidation:
    """Test response structure and content for POST /items endpoint."""

    def test_response_contains_exact_fields(self):
        """Test that response contains only id, name, and price."""
        r = client.post("/items", json={"name": "test", "price": 15.0})
        assert r.status_code == 200
        data = r.json()
        assert set(data.keys()) == {"id", "name", "price"}

    def test_response_echoes_input_values(self):
        """Test that response echoes the input name and price."""
        r = client.post("/items", json={"name": "widget", "price": 42.5})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "widget"
        assert data["price"] == 42.5

    def test_response_content_type(self):
        """Test that response content type is JSON."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")


class TestGetItemResponseValidation:
    """Test response structure and content for GET /items/{item_id} endpoint."""

    def test_response_contains_required_fields(self):
        """Test that GET response contains id, name, and price."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_response_values_for_item_1(self):
        """Test that item 1 has expected values."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0

    def test_response_field_types(self):
        """Test that response field types are correct."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))


class TestErrorResponseStructure:
    """Test error response structure and format."""

    def test_bad_price_error_has_detail_field(self):
        """Test that custom error has detail field."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400
        data = r.json()
        assert "detail" in data

    def test_not_found_error_has_detail_field(self):
        """Test that 404 error has detail field."""
        r = client.get("/items/999")
        assert r.status_code == 404
        data = r.json()
        assert "detail" in data
        assert data["detail"] == "not found"

    def test_validation_error_has_detail_field(self):
        """Test that validation error has detail field."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data

    def test_error_detail_is_descriptive(self):
        """Test that error messages are descriptive."""
        r = client.post("/items", json={"name": "test", "price": -5})
        assert r.status_code == 400
        detail = r.json()["detail"]
        assert len(detail) > 0


class TestHealthEndpoint:
    """Test health check endpoint response."""

    def test_health_status_ok(self):
        """Test that health check returns status ok."""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data == {"status": "ok"}

    def test_health_response_structure(self):
        """Test that health response has correct structure."""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert "status" in data
        assert isinstance(data["status"], str)

    def test_health_endpoint_consistency(self):
        """Test that health endpoint returns consistent responses."""
        for _ in range(3):
            r = client.get("/health")
            assert r.status_code == 200
            assert r.json()["status"] == "ok"
