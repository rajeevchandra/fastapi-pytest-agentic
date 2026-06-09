"""
Integration and response validation tests for the FastAPI application.

These tests validate end-to-end scenarios and response structure.
"""
from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Test the health check endpoint."""

    def test_health_response_status(self):
        """Test health endpoint returns 200."""
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_response_structure(self):
        """Test health endpoint response structure."""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert "status" in data
        assert data["status"] == "ok"

    def test_health_response_type(self):
        """Test health endpoint response is valid JSON."""
        r = client.get("/health")
        assert r.status_code == 200
        assert isinstance(r.json(), dict)

    def test_health_response_content_type(self):
        """Test health endpoint returns JSON content type."""
        r = client.get("/health")
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")


class TestEndToEndWorkflows:
    """Test complete workflows combining multiple endpoints."""

    def test_create_and_retrieve_item(self):
        """Test creating an item and then retrieving it."""
        # Create item
        create_r = client.post("/items", json={"name": "test_item", "price": 25.0})
        assert create_r.status_code == 200
        create_data = create_r.json()
        item_id = create_data["id"]

        # Retrieve the created item
        get_r = client.get(f"/items/{item_id}")
        assert get_r.status_code == 200
        get_data = get_r.json()

        # Verify structure
        assert get_data["id"] == item_id
        assert "name" in get_data
        assert "price" in get_data

    def test_reject_invalid_item_then_valid_item(self):
        """Test that rejecting invalid item doesn't affect subsequent valid requests."""
        # Try invalid item
        invalid_r = client.post("/items", json={"name": "bad", "price": 0})
        assert invalid_r.status_code == 400

        # Valid item should still work
        valid_r = client.post("/items", json={"name": "good", "price": 10.0})
        assert valid_r.status_code == 200
        assert valid_r.json()["price"] == 10.0

    def test_retrieve_valid_item_then_invalid_id(self):
        """Test retrieving valid item followed by invalid item_id."""
        # Get valid item
        valid_r = client.get("/items/1")
        assert valid_r.status_code == 200

        # Try invalid item_id
        invalid_r = client.get("/items/999")
        assert invalid_r.status_code == 404


class TestResponseValidation:
    """Validate response structure and content."""

    def test_successful_create_response_contains_all_fields(self):
        """Test successful POST response contains all expected fields."""
        r = client.post("/items", json={"name": "book", "price": 15.0})
        assert r.status_code == 200
        data = r.json()
        
        # Check all fields are present
        required_fields = ["id", "name", "price"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"

    def test_error_response_contains_detail(self):
        """Test error responses contain detail message."""
        r = client.post("/items", json={"name": "item", "price": -5})
        assert r.status_code == 400
        data = r.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)
        assert len(data["detail"]) > 0

    def test_validation_error_response_structure(self):
        """Test validation error responses have proper structure."""
        r = client.post("/items", json={"name": 123, "price": 10.0})
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data
        assert isinstance(data["detail"], (list, dict, str))

    def test_not_found_response_structure(self):
        """Test 404 response structure."""
        r = client.get("/items/99999")
        assert r.status_code == 404
        data = r.json()
        assert "detail" in data
        assert data["detail"] == "not found"


class TestResponseHeaders:
    """Test HTTP response headers."""

    def test_post_response_headers(self):
        """Test headers in POST response."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200
        assert "content-type" in r.headers
        assert "application/json" in r.headers.get("content-type", "")

    def test_get_response_headers(self):
        """Test headers in GET response."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert "content-type" in r.headers
        assert "application/json" in r.headers.get("content-type", "")

    def test_get_not_found_response_headers(self):
        """Test headers in 404 response."""
        r = client.get("/items/999")
        assert r.status_code == 404
        assert "content-type" in r.headers
        assert "application/json" in r.headers.get("content-type", "")

    def test_health_response_headers(self):
        """Test headers in health response."""
        r = client.get("/health")
        assert r.status_code == 200
        assert "content-type" in r.headers
        assert "application/json" in r.headers.get("content-type", "")


class TestResponseTypeValidation:
    """Validate response data types."""

    @pytest.mark.parametrize("name,price", [
        ("item1", 10.0),
        ("item2", 19.99),
        ("item3", 0.01),
        ("very_long_item_name_with_many_characters", 999.99),
        ("unicode_名前_item", 50.0),
    ])
    def test_response_types_various_inputs(self, name, price):
        """Test response types are consistent across various inputs."""
        r = client.post("/items", json={"name": name, "price": price})
        assert r.status_code == 200
        data = r.json()
        
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_get_response_types(self):
        """Test GET response data types."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))
        assert data["price"] == 10.0


class TestErrorMessages:
    """Test error message content and quality."""

    def test_price_validation_error_message(self):
        """Test that price validation error has clear message."""
        r = client.post("/items", json={"name": "item", "price": -10})
        assert r.status_code == 400
        data = r.json()
        assert "price must be > 0" in data["detail"]

    def test_not_found_error_message(self):
        """Test that not found error has clear message."""
        r = client.get("/items/9999")
        assert r.status_code == 404
        data = r.json()
        assert "not found" in data["detail"]

    def test_validation_error_includes_field_info(self):
        """Test that validation errors provide useful info."""
        r = client.post("/items", json={"price": 10.0})  # Missing name
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data


class TestAPIConsistency:
    """Test API consistency and idempotency where applicable."""

    def test_health_endpoint_consistency(self):
        """Test that health endpoint returns consistent results."""
        results = [client.get("/health").json() for _ in range(3)]
        assert all(r == results[0] for r in results)

    def test_get_specific_item_consistency(self):
        """Test that GET returns consistent results for the same ID."""
        results = [client.get("/items/1").json() for _ in range(3)]
        assert all(r == results[0] for r in results)

    def test_not_found_consistency(self):
        """Test that not found errors are consistent."""
        responses = [client.get("/items/9999") for _ in range(3)]
        assert all(r.status_code == 404 for r in responses)
        assert all(r.json()["detail"] == "not found" for r in responses)


class TestErrorStatusCodes:
    """Test that appropriate status codes are used."""

    def test_created_returns_200(self):
        """Test successful creation returns 200."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200

    def test_found_returns_200(self):
        """Test successful retrieval returns 200."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_not_found_returns_404(self):
        """Test not found returns 404."""
        r = client.get("/items/999")
        assert r.status_code == 404

    def test_business_validation_error_returns_400(self):
        """Test business logic validation error returns 400."""
        r = client.post("/items", json={"name": "item", "price": -1})
        assert r.status_code == 400

    def test_data_validation_error_returns_422(self):
        """Test data validation error returns 422."""
        r = client.post("/items", json={"name": 123, "price": 10.0})
        assert r.status_code == 422
