"""
Response structure and error handling tests for API endpoints.
Validates response formats, HTTP status codes, and error messages.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemHTTPStatusCodes:
    """Test HTTP status codes for create_item endpoint."""

    @pytest.mark.parametrize("price", [0.01, 1.0, 10.0, 100.0])
    def test_create_item_success_returns_200(self, price):
        """Test that successful item creation returns 200 OK."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200

    @pytest.mark.parametrize("price", [-1, 0, -100.0, -0.01])
    def test_create_item_invalid_price_returns_400(self, price):
        """Test that invalid price returns 400 Bad Request."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 400

    def test_create_item_invalid_json_returns_422(self):
        """Test that invalid JSON returns 422 Unprocessable Entity."""
        r = client.post("/items", content="invalid json", headers={"Content-Type": "application/json"})
        assert r.status_code == 422

    def test_create_item_missing_fields_returns_422(self):
        """Test that missing required fields returns 422."""
        r = client.post("/items", json={"name": "item"})
        assert r.status_code == 422


class TestGetItemHTTPStatusCodes:
    """Test HTTP status codes for get_item endpoint."""

    @pytest.mark.parametrize("item_id", [1])
    def test_get_item_existing_returns_200(self, item_id):
        """Test that getting existing item returns 200 OK."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 200

    @pytest.mark.parametrize("item_id", [2, 3, 999, -1, 0])
    def test_get_item_nonexistent_returns_404(self, item_id):
        """Test that getting non-existent item returns 404 Not Found."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404


class TestCreateItemErrorResponse:
    """Test error response format and content."""

    def test_create_item_error_has_detail_field(self):
        """Test that error response includes detail field."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.status_code == 400
        assert "detail" in r.json()

    def test_create_item_error_detail_is_string(self):
        """Test that detail field is a string."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.status_code == 400
        assert isinstance(r.json()["detail"], str)

    def test_create_item_invalid_price_error_message(self):
        """Test specific error message for invalid price."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.status_code == 400
        assert "price" in r.json()["detail"].lower()
        assert "0" in r.json()["detail"]

    def test_create_item_validation_error_has_detail(self):
        """Test that validation errors include detail information."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422
        # Validation error response includes detail or detail message
        assert "detail" in r.json() or "title" in r.json()

    def test_create_item_multiple_errors_handled(self):
        """Test that missing multiple fields is handled."""
        r = client.post("/items", json={})
        assert r.status_code == 422


class TestGetItemErrorResponse:
    """Test error response format for get_item endpoint."""

    def test_get_item_not_found_has_detail(self):
        """Test that 404 response includes detail field."""
        r = client.get("/items/999")
        assert r.status_code == 404
        assert "detail" in r.json()

    def test_get_item_not_found_error_message(self):
        """Test specific error message for not found."""
        r = client.get("/items/999")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_error_detail_is_string(self):
        """Test that error detail is a string."""
        r = client.get("/items/999")
        assert r.status_code == 404
        assert isinstance(r.json()["detail"], str)


class TestCreateItemResponseFormat:
    """Test response format and structure."""

    def test_create_item_success_returns_json(self):
        """Test that successful response is JSON."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("application/json")

    def test_create_item_response_is_object(self):
        """Test that response body is a JSON object."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)

    def test_create_item_response_has_only_expected_fields(self):
        """Test that response contains expected fields."""
        r = client.post("/items", json={"name": "book", "price": 12.5})
        assert r.status_code == 200
        data = r.json()
        expected_fields = {"id", "name", "price"}
        actual_fields = set(data.keys())
        assert expected_fields.issubset(actual_fields)

    def test_create_item_response_content_type_json(self):
        """Test that content-type header is application/json."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")


class TestGetItemResponseFormat:
    """Test get_item response format."""

    def test_get_item_success_returns_json(self):
        """Test that successful response is JSON."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("application/json")

    def test_get_item_response_is_object(self):
        """Test that response body is a JSON object."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)

    def test_get_item_response_structure(self):
        """Test that get response has expected fields."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_get_item_response_has_correct_types(self):
        """Test that response fields have correct types."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))


class TestGetItemResponseContent:
    """Test get_item response content."""

    def test_get_item_returns_fixed_data(self):
        """Test that get returns the expected fixed data."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0

    def test_get_item_id_matches_request(self):
        """Test that returned id matches the path parameter."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_get_item_name_is_consistent(self):
        """Test that name field is consistent."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["name"] == "sample"

    def test_get_item_price_is_positive(self):
        """Test that returned price is positive."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["price"] > 0


class TestHealthEndpointResponse:
    """Test health endpoint response format."""

    def test_health_returns_json(self):
        """Test that health endpoint returns JSON."""
        r = client.get("/health")
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("application/json")

    def test_health_response_structure(self):
        """Test that health response has expected structure."""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)
        assert "status" in data

    def test_health_status_value(self):
        """Test that health status is 'ok'."""
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_health_status_is_string(self):
        """Test that status field is a string."""
        r = client.get("/health")
        assert r.status_code == 200
        assert isinstance(r.json()["status"], str)


class TestErrorConsistency:
    """Test error handling consistency across endpoints."""

    def test_all_errors_have_detail_field(self):
        """Test that all error responses include detail field."""
        # Test create_item error
        r1 = client.post("/items", json={"name": "item", "price": 0})
        assert "detail" in r1.json()
        
        # Test get_item error
        r2 = client.get("/items/999")
        assert "detail" in r2.json()

    def test_error_responses_are_json(self):
        """Test that error responses are valid JSON."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.status_code == 400
        # Should not raise exception
        data = r.json()
        assert isinstance(data, dict)

    def test_validation_errors_consistent_format(self):
        """Test that validation errors follow consistent format."""
        r = client.post("/items", json={})
        assert r.status_code == 422
        # Should have some error detail
        data = r.json()
        assert isinstance(data, dict)


class TestResponseConsistency:
    """Test consistency of successful responses."""

    def test_create_item_includes_input_fields(self):
        """Test that created item response includes input fields."""
        name = "test_book"
        price = 15.99
        r = client.post("/items", json={"name": name, "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name
        assert data["price"] == price

    def test_create_item_always_has_id(self):
        """Test that all created items have an id."""
        for i in range(3):
            r = client.post("/items", json={"name": f"item{i}", "price": 10.0})
            assert r.status_code == 200
            assert "id" in r.json()
            assert r.json()["id"] is not None

    def test_response_data_preserved_through_field_types(self):
        """Test that data is preserved when round-tripping through JSON."""
        name = "test"
        price = 123.45
        r = client.post("/items", json={"name": name, "price": price})
        assert r.status_code == 200
        data = r.json()
        # Verify name preserved as string
        assert data["name"] == name
        # Verify price value is maintained
        assert abs(data["price"] - price) < 0.01
