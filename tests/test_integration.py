"""
Integration tests and response validation for complete API scenarios.
Tests end-to-end workflows, response structure consistency, and parametrized scenarios.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.fixture
def item_data():
    """Fixture providing various test item data."""
    return [
        {"name": "book", "price": 12.5},
        {"name": "pen", "price": 1.0},
        {"name": "desk", "price": 99.99},
        {"name": "laptop", "price": 1299.99},
        {"name": "coffee mug", "price": 5.99},
    ]


class TestParametrizedIntegration:
    """Parametrized tests for various item scenarios."""

    @pytest.mark.parametrize("price", [0.01, 0.99, 1, 10, 100, 999.99, 9999.99])
    def test_create_item_various_prices(self, price):
        """Test item creation with various price points."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    @pytest.mark.parametrize("name", [
        "item",
        "test item",
        "Test Item With Capitals",
        "123-456",
        "item_with_underscore",
        "caffè-latte",
        "日本語アイテム"
    ])
    def test_create_item_various_names(self, name):
        """Test item creation with various name formats."""
        r = client.post("/items", json={"name": name, "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == name


class TestCreateThenRetrieve:
    """Test create-then-retrieve workflows."""

    def test_create_and_verify_structure(self):
        """Create item and verify returned structure."""
        create_r = client.post("/items", json={"name": "widget", "price": 29.99})
        assert create_r.status_code == 200
        created_data = create_r.json()
        
        assert "id" in created_data
        assert "name" in created_data
        assert "price" in created_data
        assert created_data["name"] == "widget"
        assert created_data["price"] == 29.99

    def test_create_and_retrieve_item(self):
        """Full workflow: create item, then retrieve it."""
        # Create an item
        create_r = client.post("/items", json={"name": "phone", "price": 499.99})
        assert create_r.status_code == 200
        created_item = create_r.json()
        
        # Retrieve the same item
        get_r = client.get(f"/items/{created_item['id']}")
        assert get_r.status_code == 200
        retrieved_item = get_r.json()
        
        # Verify retrieval returns consistent data
        assert retrieved_item["id"] == created_item["id"]


class TestResponseTypeValidation:
    """Validate response data types across endpoints."""

    def test_create_item_response_types(self):
        """Verify /items POST response has correct types."""
        r = client.post("/items", json={"name": "item", "price": 15.50})
        assert r.status_code == 200
        data = r.json()
        
        assert isinstance(data, dict)
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_get_item_response_types(self):
        """Verify /items/{id} GET response has correct types."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        
        assert isinstance(data, dict)
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))

    def test_error_response_types(self):
        """Verify error responses have correct structure."""
        r = client.get("/items/999")
        assert r.status_code == 404
        data = r.json()
        
        assert isinstance(data, dict)
        assert "detail" in data
        assert isinstance(data["detail"], str)

    def test_validation_error_response_types(self):
        """Verify validation error responses have correct structure."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422
        data = r.json()
        
        assert isinstance(data, dict)
        assert "detail" in data
        assert isinstance(data["detail"], list)


class TestHealthEndpointIntegration:
    """Test health endpoint as part of integration."""

    def test_health_endpoint_success(self):
        """Verify health endpoint returns success."""
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_health_endpoint_structure(self):
        """Verify health endpoint response structure."""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)
        assert "status" in data
        assert isinstance(data["status"], str)


class TestErrorHandlingConsistency:
    """Test consistency of error responses."""

    def test_all_404_responses_have_detail(self):
        """Verify all 404 responses include detail field."""
        test_ids = [2, 100, 999, 9999]
        for item_id in test_ids:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404
            assert "detail" in r.json()

    def test_all_400_responses_have_detail(self):
        """Verify all 400 responses include detail field."""
        test_prices = [0, -1, -10, -100]
        for price in test_prices:
            r = client.post("/items", json={"name": "test", "price": price})
            assert r.status_code == 400
            assert "detail" in r.json()

    def test_400_error_message_consistency(self):
        """Verify 400 error messages are consistent."""
        r1 = client.post("/items", json={"name": "test", "price": 0})
        r2 = client.post("/items", json={"name": "test", "price": -5})
        
        assert r1.json()["detail"] == r2.json()["detail"]
        assert r1.json()["detail"] == "price must be > 0"


class TestEdgeCaseScenarios:
    """Test realistic edge case scenarios."""

    def test_rapid_sequential_creates(self):
        """Test multiple rapid create operations."""
        for i in range(5):
            r = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            assert r.status_code == 200

    def test_mixed_success_and_failure_operations(self):
        """Test mix of successful and failed operations."""
        # Success
        r1 = client.post("/items", json={"name": "valid", "price": 10})
        assert r1.status_code == 200
        
        # Failure - missing field
        r2 = client.post("/items", json={"name": "invalid"})
        assert r2.status_code == 422
        
        # Success again
        r3 = client.post("/items", json={"name": "valid2", "price": 20})
        assert r3.status_code == 200
        
        # Failure - invalid price
        r4 = client.post("/items", json={"name": "invalid", "price": -5})
        assert r4.status_code == 400
        
        # Success - retrieve
        r5 = client.get("/items/1")
        assert r5.status_code == 200

    def test_retrieve_with_various_valid_ids(self):
        """Test retrieval attempts with various IDs."""
        valid_ids = [1]
        invalid_ids = [0, -1, 2, 100, 999]
        
        for item_id in valid_ids:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 200
        
        for item_id in invalid_ids:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404


class TestContentNegotiation:
    """Test content type and response format."""

    def test_create_item_response_content_type(self):
        """Verify POST response has application/json content type."""
        r = client.post("/items", json={"name": "test", "price": 10})
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")

    def test_get_item_response_content_type(self):
        """Verify GET response has application/json content type."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")

    def test_health_response_content_type(self):
        """Verify health response has application/json content type."""
        r = client.get("/health")
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")


class TestStressScenarios:
    """Test stress scenarios and extreme conditions."""

    def test_create_items_with_extreme_prices(self):
        """Test creation with extreme but valid price values."""
        extreme_prices = [0.01, 0.001, 1000000, 9999999.99]
        for price in extreme_prices:
            r = client.post("/items", json={"name": "test", "price": price})
            assert r.status_code == 200
            assert r.json()["price"] == price

    def test_create_items_with_very_long_names(self):
        """Test creation with very long name strings."""
        long_names = [
            "a" * 100,
            "a" * 1000,
            "a" * 5000,
        ]
        for name in long_names:
            r = client.post("/items", json={"name": name, "price": 10})
            assert r.status_code == 200
            assert r.json()["name"] == name

    def test_retrieve_with_extreme_ids(self):
        """Test retrieval with extreme ID values."""
        extreme_ids = [0, -1, -999999, 2147483647, 9999999999]
        for item_id in extreme_ids:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404
