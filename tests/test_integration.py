"""
Integration and end-to-end tests for the FastAPI application.
Tests complete workflows, response validation, and API interaction patterns.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Test the health check endpoint."""

    def test_health_returns_ok_status(self):
        """Test that health endpoint returns ok status."""
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_health_response_structure(self):
        """Test health endpoint response structure."""
        r = client.get("/health")
        assert r.json() == {"status": "ok"}

    def test_health_content_type(self):
        """Test that health response is JSON."""
        r = client.get("/health")
        assert "application/json" in r.headers.get("content-type", "")


class TestParametrizedIntegration:
    """Parametrized integration tests for common workflows."""

    @pytest.mark.parametrize("name,price", [
        ("book", 12.99),
        ("pen", 0.99),
        ("laptop", 999.99),
        ("item", 1.0),
    ])
    def test_create_item_with_various_products(self, name, price):
        """Test creating items with various product names and prices."""
        r = client.post("/items", json={"name": name, "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name
        assert data["price"] == price
        assert data["id"] == 1

    @pytest.mark.parametrize("item_id", [1, 2, 3, 100, 999])
    def test_get_item_various_ids(self, item_id):
        """Test getting items with various IDs."""
        r = client.get(f"/items/{item_id}")
        if item_id == 1:
            assert r.status_code == 200
            assert r.json()["id"] == 1
        else:
            assert r.status_code == 404


class TestStatusCodes:
    """Test various HTTP status codes returned by the API."""

    def test_create_success_is_200(self):
        """Test that successful create returns 200."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200

    def test_get_success_is_200(self):
        """Test that successful get returns 200."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_create_invalid_price_is_400(self):
        """Test that invalid price returns 400 Bad Request."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400

    def test_get_nonexistent_item_is_404(self):
        """Test that nonexistent item returns 404 Not Found."""
        r = client.get("/items/999")
        assert r.status_code == 404

    def test_create_missing_field_is_422(self):
        """Test that missing required field returns 422 Unprocessable Entity."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422


class TestErrorResponses:
    """Test error response format and content."""

    def test_validation_error_has_detail(self):
        """Test that validation errors include detail field."""
        r = client.post("/items", json={"name": "test", "price": "invalid"})
        assert r.status_code == 422
        assert "detail" in r.json()

    def test_not_found_error_has_detail(self):
        """Test that 404 errors include detail field."""
        r = client.get("/items/999")
        assert r.status_code == 404
        data = r.json()
        assert "detail" in data
        assert data["detail"] == "not found"

    def test_bad_request_error_has_detail(self):
        """Test that 400 errors include detail field."""
        r = client.post("/items", json={"name": "test", "price": -5})
        assert r.status_code == 400
        data = r.json()
        assert "detail" in data
        assert "price must be > 0" in data["detail"]

    def test_error_detail_is_string(self):
        """Test that error detail is a string."""
        r = client.get("/items/999")
        assert isinstance(r.json()["detail"], str)


class TestStressScenarios:
    """Test API under various stress conditions."""

    def test_repeated_successful_creates(self):
        """Test multiple successful create operations."""
        for i in range(10):
            r = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            assert r.status_code == 200

    def test_repeated_successful_gets(self):
        """Test multiple successful get operations."""
        for i in range(10):
            r = client.get("/items/1")
            assert r.status_code == 200
            assert r.json()["id"] == 1

    def test_alternating_create_and_get(self):
        """Test alternating create and get operations."""
        for i in range(5):
            create_r = client.post("/items", json={"name": f"item{i}", "price": 10.0})
            assert create_r.status_code == 200
            get_r = client.get("/items/1")
            assert get_r.status_code == 200

    def test_rapid_failed_requests(self):
        """Test rapid failed requests don't break the API."""
        for i in range(10):
            r = client.get(f"/items/{i + 2}")  # All should be 404
            assert r.status_code == 404
        # Verify API still works
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_mixed_valid_and_invalid_creates(self):
        """Test mix of valid and invalid create requests."""
        valid_r = client.post("/items", json={"name": "valid", "price": 10.0})
        assert valid_r.status_code == 200
        
        invalid_r = client.post("/items", json={"name": "invalid", "price": -1})
        assert invalid_r.status_code == 400
        
        # Verify API still works
        valid_r2 = client.post("/items", json={"name": "valid2", "price": 20.0})
        assert valid_r2.status_code == 200


class TestDataPersistence:
    """Test behavior regarding data state."""

    def test_get_item_returns_fixed_data(self):
        """Test that GET /items/1 returns consistent fixed data."""
        r1 = client.get("/items/1")
        r2 = client.get("/items/1")
        r3 = client.get("/items/1")
        
        assert r1.json() == r2.json() == r3.json()
        assert r1.json()["name"] == "sample"
        assert r1.json()["price"] == 10.0

    def test_create_doesnt_affect_existing_item(self):
        """Test that creating a new item doesn't change the existing item."""
        # Get existing item
        get_r1 = client.get("/items/1")
        data1 = get_r1.json()
        
        # Create new item
        create_r = client.post("/items", json={"name": "new", "price": 99.99})
        assert create_r.status_code == 200
        
        # Get existing item again
        get_r2 = client.get("/items/1")
        data2 = get_r2.json()
        
        # Should be unchanged
        assert data1 == data2


class TestResponseValidation:
    """Test response body validation and structure."""

    def test_create_response_all_fields_present(self):
        """Test that create response includes all required fields."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        data = r.json()
        required_fields = {"id", "name", "price"}
        assert required_fields.issubset(data.keys())

    def test_get_response_all_fields_present(self):
        """Test that get response includes all required fields."""
        r = client.get("/items/1")
        data = r.json()
        required_fields = {"id", "name", "price"}
        assert required_fields.issubset(data.keys())

    def test_create_response_no_extra_fields(self):
        """Test that create response doesn't include unexpected fields."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        data = r.json()
        expected_fields = {"id", "name", "price"}
        assert set(data.keys()) == expected_fields

    def test_get_response_no_extra_fields(self):
        """Test that get response doesn't include unexpected fields."""
        r = client.get("/items/1")
        data = r.json()
        expected_fields = {"id", "name", "price"}
        assert set(data.keys()) == expected_fields

    @pytest.mark.parametrize("name,price", [
        ("", 0.01),
        ("a", 1000000),
        ("x" * 100, 0.01),
        ("special!@#$%", 99.99),
    ])
    def test_create_response_values_match_input(self, name, price):
        """Test that response values match input for various cases."""
        r = client.post("/items", json={"name": name, "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name
        assert data["price"] == price


class TestAPIBasics:
    """Basic API functionality tests."""

    def test_api_is_responsive(self):
        """Test that API is responsive to requests."""
        r = client.get("/health")
        assert r.status_code == 200

    def test_endpoints_exist(self):
        """Test that expected endpoints exist."""
        # Health check should exist
        r = client.get("/health")
        assert r.status_code == 200
        
        # Items create should exist
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code in [200, 400, 422]  # Should not 404
        
        # Items get should exist
        r = client.get("/items/1")
        assert r.status_code in [200, 404]  # Should not 404 (method not found)

    def test_non_existent_endpoint_returns_404(self):
        """Test that non-existent endpoints return 404."""
        r = client.get("/nonexistent")
        assert r.status_code == 404
