"""
Integration tests and response validation for the FastAPI items API.
Tests end-to-end scenarios, response structures, and API interaction patterns.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# ============================================================================
# Fixtures for reusable test data
# ============================================================================

@pytest.fixture
def sample_item_data():
    """Standard item data for testing."""
    return {"name": "test-item", "price": 15.99}


@pytest.fixture
def valid_prices():
    """Collection of valid prices for boundary testing."""
    return [0.01, 0.1, 1.0, 10.0, 100.0, 1000.0, 9999.99]


@pytest.fixture
def invalid_prices():
    """Collection of invalid prices for validation testing."""
    return [0, -1, -10.5, -0.01]


# ============================================================================
# Integration Tests - API Interaction Patterns
# ============================================================================

class TestCreateAndRetrieveItem:
    """Test creating an item and then retrieving it."""

    def test_create_item_and_get_same_id(self):
        """Create an item and verify it can be retrieved."""
        # Create
        create_resp = client.post("/items", json={"name": "integration-test", "price": 20.0})
        assert create_resp.status_code == 200
        created_item = create_resp.json()
        
        # Retrieve
        get_resp = client.get(f"/items/{created_item['id']}")
        assert get_resp.status_code == 200
        retrieved_item = get_resp.json()
        
        # Verify
        assert retrieved_item["id"] == created_item["id"]
        assert retrieved_item["name"] == "sample"  # API returns fixed data for ID 1

    def test_create_item_returns_expected_id(self):
        """Created item should have ID 1."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1

    def test_created_item_has_all_fields(self, sample_item_data):
        """Created item response should include all request fields."""
        r = client.post("/items", json=sample_item_data)
        assert r.status_code == 200
        data = r.json()
        
        assert "id" in data
        assert "name" in data
        assert "price" in data
        assert data["name"] == sample_item_data["name"]
        assert data["price"] == sample_item_data["price"]

    def test_multiple_create_attempts_same_response(self):
        """Multiple create requests should return consistent response structure."""
        items = [
            {"name": "item1", "price": 10.0},
            {"name": "item2", "price": 20.0},
        ]
        
        responses = []
        for item in items:
            r = client.post("/items", json=item)
            assert r.status_code == 200
            responses.append(r.json())
        
        # All should have same fields
        for resp in responses:
            assert "id" in resp
            assert "name" in resp
            assert "price" in resp


# ============================================================================
# Response Structure and Content Type Tests
# ============================================================================

class TestResponseStructure:
    """Test response structures and content types."""

    def test_health_endpoint_response(self):
        """Health endpoint should return status."""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert "status" in data
        assert data["status"] == "ok"

    def test_create_item_response_headers(self):
        """Create response should have JSON content-type."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert "application/json" in r.headers.get("content-type", "")

    def test_get_item_response_headers(self):
        """Get response should have JSON content-type."""
        r = client.get("/items/1")
        assert "application/json" in r.headers.get("content-type", "")

    def test_error_response_has_detail_field(self):
        """Error responses should include detail field."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400
        data = r.json()
        assert "detail" in data

    def test_validation_error_response_structure(self):
        """Validation error (422) should have error details."""
        r = client.post("/items", json={"name": "test"})  # Missing price
        assert r.status_code == 422
        data = r.json()
        assert "detail" in data


# ============================================================================
# Data Validation and Type Testing
# ============================================================================

class TestDataValidation:
    """Test data validation throughout the API."""

    @pytest.mark.parametrize("price", [0.01, 1.0, 100.0, 9999.99])
    def test_various_valid_prices_accepted(self, price):
        """API should accept various valid prices."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    @pytest.mark.parametrize("price", [0, -1, -100.5])
    def test_invalid_prices_rejected(self, price):
        """API should reject non-positive prices."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400

    @pytest.mark.parametrize("name", ["A", "test", "A" * 100, "item-123-abc"])
    def test_various_valid_names_accepted(self, name):
        """API should accept various valid names."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_response_data_types_correct(self):
        """Response should have correct data types."""
        r = client.post("/items", json={"name": "test", "price": 10.5})
        assert r.status_code == 200
        data = r.json()
        
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_get_response_data_types_correct(self):
        """GET response should have correct data types."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))


# ============================================================================
# Edge Case Integration Tests
# ============================================================================

class TestIntegrationEdgeCases:
    """Test integration scenarios with edge cases."""

    def test_create_with_minimum_valid_price(self):
        """Creating with very small valid price should work."""
        r = client.post("/items", json={"name": "cheap", "price": 0.01})
        assert r.status_code == 200
        assert r.json()["price"] == 0.01

    def test_create_with_very_large_price(self):
        """Creating with very large price should work."""
        r = client.post("/items", json={"name": "expensive", "price": 999999.99})
        assert r.status_code == 200
        assert r.json()["price"] == 999999.99

    def test_create_with_long_name(self):
        """Creating with long name should work."""
        long_name = "x" * 500
        r = client.post("/items", json={"name": long_name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == long_name

    def test_create_with_special_characters_in_name(self):
        """Creating with special characters in name should work."""
        special_names = [
            "item-123",
            "item_456",
            "item.789",
            "café",
            "日本",
        ]
        for name in special_names:
            r = client.post("/items", json={"name": name, "price": 10.0})
            assert r.status_code == 200
            assert r.json()["name"] == name

    def test_get_with_edge_case_ids(self):
        """GET with various edge case IDs should handle correctly."""
        edge_ids = [0, -1, 2, 999, 1000000]
        for item_id in edge_ids:
            r = client.get(f"/items/{item_id}")
            if item_id == 1:
                assert r.status_code == 200
            else:
                assert r.status_code == 404


# ============================================================================
# Error Handling and Status Code Tests
# ============================================================================

class TestErrorHandling:
    """Test error handling and HTTP status codes."""

    def test_missing_required_field_returns_422(self):
        """Missing required field should return 422."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422

    def test_invalid_price_type_returns_422(self):
        """Invalid price type should return 422."""
        r = client.post("/items", json={"name": "test", "price": "invalid"})
        assert r.status_code == 422

    def test_negative_price_returns_400(self):
        """Negative price should return 400."""
        r = client.post("/items", json={"name": "test", "price": -10})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    def test_zero_price_returns_400(self):
        """Zero price should return 400."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    def test_invalid_item_id_returns_404(self):
        """Invalid item ID should return 404."""
        r = client.get("/items/999")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    @pytest.mark.parametrize("item_id", [0, -1, 2, 100])
    def test_various_invalid_ids_return_404(self, item_id):
        """Various invalid item IDs should all return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404


# ============================================================================
# Health Check and API Status Tests
# ============================================================================

class TestHealthAndStatus:
    """Test health check and API status endpoints."""

    def test_health_endpoint_exists(self):
        """Health endpoint should be accessible."""
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_endpoint_returns_ok_status(self):
        """Health endpoint should return ok status."""
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_health_endpoint_response_type(self):
        """Health endpoint should return JSON."""
        r = client.get("/health")
        assert "application/json" in r.headers.get("content-type", "")

    def test_health_endpoint_has_required_fields(self):
        """Health response should have status field."""
        r = client.get("/health")
        data = r.json()
        assert "status" in data


# ============================================================================
# Parametrized Comprehensive Tests
# ============================================================================

class TestParametrizedComprehensive:
    """Comprehensive parametrized tests for API coverage."""

    @pytest.mark.parametrize("price", [0.01, 1.0, 10.0, 100.0, 1000.0, 9999.99])
    def test_create_with_boundary_prices(self, price):
        """Create items with various valid prices."""
        r = client.post("/items", json={"name": f"item_{price}", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    @pytest.mark.parametrize("price", [0, -1, -0.01, -100.5])
    def test_create_with_invalid_prices(self, price):
        """Create with invalid prices should fail."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400

    @pytest.mark.parametrize("item_id", [1, 2, 3, 0, -1, 999])
    def test_get_various_item_ids(self, item_id):
        """Get requests with various IDs."""
        r = client.get(f"/items/{item_id}")
        if item_id == 1:
            assert r.status_code == 200
            assert r.json()["id"] == 1
        else:
            assert r.status_code == 404

    @pytest.mark.parametrize("name,price", [
        ("item1", 10.0),
        ("item2", 20.5),
        ("item3", 0.01),
        ("item4", 999.99),
    ])
    def test_create_multiple_items_combination(self, name, price):
        """Create items with various name/price combinations."""
        r = client.post("/items", json={"name": name, "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name
        assert data["price"] == price
