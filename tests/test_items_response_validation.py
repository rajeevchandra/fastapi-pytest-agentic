import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemHTTPStatusCodes:
    """Test HTTP status codes for create_item endpoint."""

    @pytest.mark.parametrize("price", [0.01, 1, 10, 100])
    def test_create_item_success_status(self, price):
        """Test that successful creation returns 200 OK."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 200

    @pytest.mark.parametrize("price", [-1, 0, -100])
    def test_create_item_invalid_price_status(self, price):
        """Test that invalid price returns 400 Bad Request."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400

    def test_create_item_missing_field_status(self):
        """Test that missing required field returns 422 Unprocessable Entity."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422

    def test_create_item_invalid_json_status(self):
        """Test malformed JSON returns 422 or 400."""
        r = client.post("/items", data="not json")
        assert r.status_code in [400, 422]


class TestCreateItemResponseStructure:
    """Test response structure for create_item endpoint."""

    def test_create_item_response_is_json_object(self):
        """Test that response is valid JSON object."""
        r = client.post("/items", json={"name": "test", "price": 10})
        assert r.status_code == 200
        assert isinstance(r.json(), dict)

    def test_create_item_response_has_all_required_fields(self):
        """Test that response contains all required fields."""
        r = client.post("/items", json={"name": "book", "price": 12.5})
        assert r.status_code == 200
        data = r.json()
        required_fields = {"id", "name", "price"}
        assert required_fields.issubset(data.keys())

    def test_create_item_response_field_types(self):
        """Test that response fields have correct types."""
        r = client.post("/items", json={"name": "test", "price": 10})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_create_item_response_preserves_name(self):
        """Test that name in response matches input."""
        test_name = "My Test Item"
        r = client.post("/items", json={"name": test_name, "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == test_name

    def test_create_item_response_preserves_price(self):
        """Test that price in response matches input."""
        test_price = 19.99
        r = client.post("/items", json={"name": "test", "price": test_price})
        assert r.status_code == 200
        assert r.json()["price"] == test_price

    def test_create_item_response_id_value(self):
        """Test that ID is set to 1 for created item."""
        r = client.post("/items", json={"name": "test", "price": 10})
        assert r.status_code == 200
        assert r.json()["id"] == 1


class TestCreateItemErrorResponseStructure:
    """Test error response structure for create_item endpoint."""

    def test_error_response_has_detail_field(self):
        """Test that error response includes detail field."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400
        data = r.json()
        assert "detail" in data

    def test_error_response_for_invalid_price_message(self):
        """Test that error message is descriptive."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]

    def test_error_response_for_invalid_price_negative(self):
        """Test error message for negative price."""
        r = client.post("/items", json={"name": "test", "price": -5})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]

    def test_validation_error_response_structure(self):
        """Test that validation errors have expected structure."""
        r = client.post("/items", json={"price": 10})
        assert r.status_code == 422
        data = r.json()
        # Validation errors should have 'detail' key
        assert "detail" in data


class TestGetItemHTTPStatusCodes:
    """Test HTTP status codes for get_item endpoint."""

    def test_get_item_found_status(self):
        """Test that existing item returns 200 OK."""
        r = client.get("/items/1")
        assert r.status_code == 200

    @pytest.mark.parametrize("item_id", [2, 3, 100, 999])
    def test_get_item_not_found_status(self, item_id):
        """Test that non-existent item returns 404 Not Found."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    def test_get_item_invalid_path_param_status(self):
        """Test that invalid item_id type is handled."""
        r = client.get("/items/notanumber")
        assert r.status_code == 422


class TestGetItemResponseStructure:
    """Test response structure for get_item endpoint."""

    def test_get_item_response_is_json_object(self):
        """Test that response is valid JSON object."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert isinstance(r.json(), dict)

    def test_get_item_response_has_all_required_fields(self):
        """Test that response contains all required fields."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        required_fields = {"id", "name", "price"}
        assert required_fields.issubset(data.keys())

    def test_get_item_response_field_types(self):
        """Test that response fields have correct types."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_get_item_response_values(self):
        """Test that response contains expected values."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0

    def test_get_item_id_consistency(self):
        """Test that returned ID matches requested ID."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["id"] == 1


class TestGetItemErrorResponseStructure:
    """Test error response structure for get_item endpoint."""

    def test_get_item_not_found_has_detail(self):
        """Test that 404 error includes detail field."""
        r = client.get("/items/2")
        assert r.status_code == 404
        data = r.json()
        assert "detail" in data

    def test_get_item_not_found_error_message(self):
        """Test that 404 error message is descriptive."""
        r = client.get("/items/2")
        assert r.status_code == 404
        assert "not found" in r.json()["detail"]

    @pytest.mark.parametrize("item_id", [2, 100, 999, 0, -1])
    def test_get_item_not_found_message_consistency(self, item_id):
        """Test that all not-found responses have consistent message."""
        r = client.get(f"/items/{item_id}")
        if r.status_code == 404:
            assert "not found" in r.json()["detail"]


class TestHealthEndpointResponse:
    """Test health endpoint response structure."""

    def test_health_status_code(self):
        """Test that health endpoint returns 200."""
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_response_structure(self):
        """Test that health response has correct structure."""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)
        assert "status" in data

    def test_health_response_status_value(self):
        """Test that health status value is 'ok'."""
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_health_response_content_type(self):
        """Test that health response has JSON content type."""
        r = client.get("/health")
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")


class TestResponseContentType:
    """Test response content types across endpoints."""

    def test_create_item_response_content_type(self):
        """Test that create_item returns JSON content type."""
        r = client.post("/items", json={"name": "test", "price": 10})
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")

    def test_get_item_response_content_type(self):
        """Test that get_item returns JSON content type."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")

    def test_health_response_content_type(self):
        """Test that health returns JSON content type."""
        r = client.get("/health")
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")

    def test_error_response_content_type(self):
        """Test that errors return JSON content type."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400
        assert "application/json" in r.headers.get("content-type", "")
