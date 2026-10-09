"""Response validation and HTTP status code testing."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemHTTPStatusCodes:
    """Test HTTP status codes for create_item endpoint."""

    def test_create_item_success_returns_200(self):
        """Test successful creation returns 200."""
        response = client.post(
            "/items",
            json={"name": "test", "price": 10.0}
        )
        assert response.status_code == 200

    @pytest.mark.parametrize(
        "price",
        [-1, 0, -100, -0.01]
    )
    def test_create_item_invalid_price_returns_400(self, price):
        """Test invalid price returns 400 Bad Request."""
        response = client.post(
            "/items",
            json={"name": "test", "price": price}
        )
        assert response.status_code == 400

    def test_create_item_missing_field_returns_422(self):
        """Test missing required field returns 422 Unprocessable Entity."""
        response = client.post(
            "/items",
            json={"name": "test"}
        )
        assert response.status_code == 422

    def test_create_item_invalid_type_returns_422(self):
        """Test invalid type returns 422 Unprocessable Entity."""
        response = client.post(
            "/items",
            json={"name": "test", "price": "invalid"}
        )
        assert response.status_code == 422


class TestCreateItemErrorResponse:
    """Test error response format and content."""

    def test_error_response_contains_detail_field(self):
        """Test error response includes detail field."""
        response = client.post(
            "/items",
            json={"name": "test", "price": 0}
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    def test_error_response_detail_message(self):
        """Test error detail message is correct."""
        response = client.post(
            "/items",
            json={"name": "test", "price": 0}
        )
        data = response.json()
        assert data["detail"] == "price must be > 0"

    def test_validation_error_response_structure(self):
        """Test validation error response structure."""
        response = client.post(
            "/items",
            json={"name": "test"}
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data or "detail" in str(data)

    def test_error_response_content_type(self):
        """Test error responses have correct content type."""
        response = client.post(
            "/items",
            json={"name": "test", "price": 0}
        )
        assert response.headers["content-type"] == "application/json"


class TestGetItemHTTPStatusCodes:
    """Test HTTP status codes for get_item endpoint."""

    @pytest.mark.parametrize(
        "item_id,expected_status",
        [
            (1, 200),  # Found
            (2, 404),  # Not found
            (0, 404),  # Not found
            (-1, 404),  # Not found
            (999, 404),  # Not found
        ],
    )
    def test_get_item_status_codes(self, item_id, expected_status):
        """Test status codes for various item IDs."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == expected_status

    def test_get_item_found_returns_200(self):
        """Test getting existing item returns 200."""
        response = client.get("/items/1")
        assert response.status_code == 200

    def test_get_item_not_found_returns_404(self):
        """Test getting non-existent item returns 404."""
        response = client.get("/items/2")
        assert response.status_code == 404


class TestGetItemErrorResponse:
    """Test get_item error response format."""

    def test_not_found_error_contains_detail(self):
        """Test 404 response contains detail field."""
        response = client.get("/items/2")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_not_found_detail_message(self):
        """Test 404 detail message content."""
        response = client.get("/items/2")
        data = response.json()
        assert data["detail"] == "not found"

    def test_not_found_error_content_type(self):
        """Test 404 response has correct content type."""
        response = client.get("/items/2")
        assert response.headers["content-type"] == "application/json"

    def test_not_found_no_extra_fields(self):
        """Test 404 response only has detail field."""
        response = client.get("/items/2")
        data = response.json()
        assert data == {"detail": "not found"}


class TestGetItemSuccessResponse:
    """Test get_item success response format."""

    def test_get_item_response_has_all_fields(self):
        """Test response contains all required fields."""
        response = client.get("/items/1")
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_get_item_response_field_count(self):
        """Test response has exactly 3 fields."""
        response = client.get("/items/1")
        data = response.json()
        assert len(data) == 3

    def test_get_item_response_field_types(self):
        """Test response field types are correct."""
        response = client.get("/items/1")
        data = response.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_get_item_response_id_value(self):
        """Test response id value for item 1."""
        response = client.get("/items/1")
        data = response.json()
        assert data["id"] == 1

    def test_get_item_response_name_value(self):
        """Test response name value for item 1."""
        response = client.get("/items/1")
        data = response.json()
        assert data["name"] == "sample"

    def test_get_item_response_price_value(self):
        """Test response price value for item 1."""
        response = client.get("/items/1")
        data = response.json()
        assert data["price"] == 10.0

    def test_get_item_response_price_is_float(self):
        """Test that price is returned as float."""
        response = client.get("/items/1")
        data = response.json()
        assert isinstance(data["price"], (int, float))
        # Verify it can be treated as float
        assert data["price"] > 0


class TestHealthEndpointResponse:
    """Test health endpoint response format."""

    def test_health_endpoint_returns_200(self):
        """Test health endpoint returns 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_endpoint_response_format(self):
        """Test health endpoint response format."""
        response = client.get("/health")
        data = response.json()
        assert "status" in data

    def test_health_endpoint_response_value(self):
        """Test health endpoint returns correct status."""
        response = client.get("/health")
        assert response.json() == {"status": "ok"}

    def test_health_endpoint_response_exact_structure(self):
        """Test health endpoint response exact structure."""
        response = client.get("/health")
        data = response.json()
        assert len(data) == 1
        assert data["status"] == "ok"

    def test_health_endpoint_content_type(self):
        """Test health endpoint content type."""
        response = client.get("/health")
        assert response.headers["content-type"] == "application/json"


class TestResponseConsistency:
    """Test response consistency across calls."""

    def test_create_and_get_item_consistency(self):
        """Test that created and retrieved items have consistent structure."""
        create_response = client.post(
            "/items",
            json={"name": "consistency_test", "price": 15.0}
        )
        create_data = create_response.json()

        get_response = client.get(f"/items/{create_data['id']}")
        # Note: item_id must be 1 to exist, so we test with 1
        get_response = client.get("/items/1")
        get_data = get_response.json()

        # Both should have same fields
        assert set(create_data.keys()) == set(get_data.keys())

    def test_response_json_serializable(self):
        """Test all responses are proper JSON."""
        endpoints = [
            ("GET", "/health", None),
            ("GET", "/items/1", None),
            ("POST", "/items", {"name": "test", "price": 10.0}),
        ]
        for method, endpoint, body in endpoints:
            if method == "GET":
                response = client.get(endpoint)
            else:
                response = client.post(endpoint, json=body)
            # If this doesn't raise, JSON is valid
            assert response.json()


class TestHTTPMethods:
    """Test HTTP method support."""

    def test_create_item_requires_post(self):
        """Test that create_item only accepts POST."""
        response = client.get("/items")
        # Might be 404 or 405 depending on router config
        assert response.status_code in [404, 405]

    def test_get_item_requires_get(self):
        """Test that get_item only accepts GET."""
        response = client.post("/items/1", json={})
        assert response.status_code in [404, 405]

    def test_health_requires_get(self):
        """Test that health endpoint only accepts GET."""
        response = client.post("/health", json={})
        assert response.status_code in [404, 405]
