"""
Integration tests and response structure validation.

Tests cover:
- End-to-end workflows (create then retrieve)
- Complete response structure validation
- Fixture-based test organization
- Health check integration
- Response schema validation
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.fixture
def test_item_data():
    """Fixture providing test item data."""
    return {
        "name": "Integration Test Item",
        "price": 29.99
    }


@pytest.fixture
def created_item(test_item_data):
    """Fixture that creates an item and returns the response data."""
    r = client.post("/items", json=test_item_data)
    assert r.status_code == 200
    return r.json()


@pytest.fixture
def app_client():
    """Fixture providing the test client."""
    return client


class TestIntegrationCreateAndRetrieve:
    """Integration tests for create and retrieve workflows."""

    def test_create_item_then_get_by_id(self, test_item_data):
        """Create an item, then retrieve it by ID."""
        # Create
        create_r = client.post("/items", json=test_item_data)
        assert create_r.status_code == 200
        created = create_r.json()
        item_id = created["id"]
        
        # Retrieve
        get_r = client.get(f"/items/{item_id}")
        assert get_r.status_code == 200
        retrieved = get_r.json()
        
        # Verify the retrieved item matches expected data structure
        assert retrieved["id"] == item_id
        assert "name" in retrieved
        assert "price" in retrieved
        assert isinstance(retrieved["price"], (int, float))

    def test_create_multiple_items_same_id(self, test_item_data):
        """Multiple creates return the same ID (hardcoded to 1)."""
        r1 = client.post("/items", json=test_item_data)
        r2 = client.post("/items", json={**test_item_data, "name": "Different"})
        
        assert r1.json()["id"] == r2.json()["id"] == 1

    def test_create_and_verify_item_data_preserved(self):
        """Created item data should be preserved correctly."""
        test_data = {
            "name": "Test Book",
            "price": 15.99
        }
        
        r = client.post("/items", json=test_data)
        created = r.json()
        
        # Verify data is preserved (except for id which is hardcoded)
        assert created["name"] == test_data["name"]
        assert created["price"] == test_data["price"]

    def test_create_with_special_characters_preserved(self):
        """Special characters in name should be preserved through create."""
        test_data = {
            "name": "Book & Coffee ☕: A Study (2024) [Premium Edition]",
            "price": 35.00
        }
        
        r = client.post("/items", json=test_data)
        assert r.status_code == 200
        assert r.json()["name"] == test_data["name"]

    def test_workflow_create_then_get_not_found_different_id(self, test_item_data):
        """Create returns id=1, but getting id=2 should return 404."""
        # Create item (always returns id=1)
        create_r = client.post("/items", json=test_item_data)
        assert create_r.status_code == 200
        assert create_r.json()["id"] == 1
        
        # Try to get non-existent id=2
        get_r = client.get("/items/2")
        assert get_r.status_code == 404


class TestResponseStructureValidation:
    """Comprehensive response structure validation."""

    def test_create_item_response_has_all_fields(self, test_item_data):
        """POST response should have all required fields."""
        r = client.post("/items", json=test_item_data)
        data = r.json()
        
        required_fields = ["id", "name", "price"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"

    def test_create_item_response_has_no_extra_fields(self, test_item_data):
        """POST response should have exactly 3 fields (no extra fields)."""
        r = client.post("/items", json=test_item_data)
        data = r.json()
        
        expected_fields = {"id", "name", "price"}
        actual_fields = set(data.keys())
        assert actual_fields == expected_fields, f"Extra fields: {actual_fields - expected_fields}"

    def test_get_item_response_has_all_fields(self):
        """GET response should have all required fields."""
        r = client.get("/items/1")
        data = r.json()
        
        required_fields = ["id", "name", "price"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"

    def test_get_item_response_has_no_extra_fields(self):
        """GET response should have exactly 3 fields (no extra fields)."""
        r = client.get("/items/1")
        data = r.json()
        
        expected_fields = {"id", "name", "price"}
        actual_fields = set(data.keys())
        assert actual_fields == expected_fields

    def test_create_error_response_structure(self):
        """Error response should only have 'detail' field."""
        r = client.post("/items", json={"name": "test", "price": -1})
        assert r.status_code == 400
        data = r.json()
        
        # Error response from HTTPException should have 'detail'
        assert "detail" in data
        assert isinstance(data["detail"], str)

    def test_get_error_response_structure(self):
        """404 error response should only have 'detail' field."""
        r = client.get("/items/999")
        assert r.status_code == 404
        data = r.json()
        
        assert "detail" in data
        assert data["detail"] == "not found"


class TestHealthCheckIntegration:
    """Test health check endpoint and API integration."""

    def test_health_endpoint_available(self):
        """Health check endpoint should be available."""
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_response_structure(self):
        """Health check response should have correct structure."""
        r = client.get("/health")
        data = r.json()
        
        assert "status" in data
        assert data["status"] == "ok"

    def test_health_response_has_no_extra_fields(self):
        """Health response should only have 'status' field."""
        r = client.get("/health")
        data = r.json()
        
        expected_fields = {"status"}
        actual_fields = set(data.keys())
        assert actual_fields == expected_fields


class TestFixtureBased:
    """Test using fixtures for cleaner, more maintainable tests."""

    def test_with_test_item_fixture(self, created_item):
        """Test using created_item fixture."""
        assert created_item["id"] == 1
        assert "name" in created_item
        assert "price" in created_item

    def test_fixture_data_consistency(self, test_item_data, created_item):
        """Test that fixture data is used correctly."""
        assert created_item["name"] == test_item_data["name"]
        assert created_item["price"] == test_item_data["price"]

    def test_multiple_fixtures(self, app_client, test_item_data):
        """Test using multiple fixtures."""
        r = app_client.post("/items", json=test_item_data)
        assert r.status_code == 200


class TestCompleteWorkflow:
    """End-to-end workflow tests."""

    def test_workflow_health_check_create_get(self):
        """Complete workflow: health → create → get."""
        # Health check
        health_r = client.get("/health")
        assert health_r.status_code == 200
        assert health_r.json()["status"] == "ok"
        
        # Create item
        create_r = client.post("/items", json={"name": "test", "price": 10.0})
        assert create_r.status_code == 200
        item_id = create_r.json()["id"]
        
        # Get item
        get_r = client.get(f"/items/{item_id}")
        assert get_r.status_code == 200
        assert get_r.json()["id"] == item_id

    def test_workflow_multiple_creates(self):
        """Multiple creates should work (all return id=1)."""
        items_data = [
            {"name": "Item 1", "price": 10.0},
            {"name": "Item 2", "price": 20.0},
            {"name": "Item 3", "price": 30.0},
        ]
        
        responses = []
        for item_data in items_data:
            r = client.post("/items", json=item_data)
            assert r.status_code == 200
            responses.append(r.json())
        
        # All should have same id (hardcoded to 1)
        ids = [resp["id"] for resp in responses]
        assert all(id == 1 for id in ids)

    def test_workflow_invalid_then_valid_create(self):
        """Invalid create followed by valid create should work."""
        # Invalid create (negative price)
        invalid_r = client.post("/items", json={"name": "test", "price": -10})
        assert invalid_r.status_code == 400
        
        # Valid create should still work
        valid_r = client.post("/items", json={"name": "test", "price": 10})
        assert valid_r.status_code == 200
        assert valid_r.json()["price"] == 10.0


class TestResponseTypeValidation:
    """Detailed type validation for responses."""

    def test_item_id_is_integer(self, created_item):
        """Item ID should be an integer."""
        assert isinstance(created_item["id"], int)
        assert created_item["id"] == 1

    def test_item_name_is_string(self, created_item):
        """Item name should be a string."""
        assert isinstance(created_item["name"], str)

    def test_item_price_is_float_or_int(self, created_item):
        """Item price should be numeric (float or int)."""
        assert isinstance(created_item["price"], (int, float))
        # Should not be a boolean (which is technically a subclass of int)
        assert not isinstance(created_item["price"], bool)

    def test_error_detail_is_string(self):
        """Error detail should be a string."""
        r = client.post("/items", json={"name": "test", "price": -1})
        data = r.json()
        assert isinstance(data["detail"], str)

    @pytest.mark.parametrize("price_value", [0.01, 1.0, 10.5, 99.99, 1000.00])
    def test_various_prices_stored_correctly(self, price_value):
        """Various price values should be stored and returned correctly."""
        r = client.post("/items", json={"name": "test", "price": price_value})
        assert r.status_code == 200
        assert r.json()["price"] == price_value


class TestResponseConsistency:
    """Consistency validation across multiple operations."""

    def test_same_item_retrieved_consistently(self):
        """Getting the same item multiple times should return same data."""
        results = [client.get("/items/1").json() for _ in range(5)]
        
        # All should be identical
        for i in range(1, len(results)):
            assert results[i] == results[0]

    def test_success_response_consistent(self):
        """Successful item creation should return consistent response format."""
        responses = []
        for i in range(3):
            r = client.post("/items", json={"name": f"Item {i}", "price": 10.0 + i})
            responses.append(r.json())
        
        # All responses should have same structure
        keys = set(responses[0].keys())
        for resp in responses[1:]:
            assert set(resp.keys()) == keys

    def test_error_response_consistent(self):
        """Error responses should have consistent structure."""
        # Test multiple error cases
        error_responses = [
            client.post("/items", json={"name": "test", "price": -1}),  # Invalid price
            client.get("/items/999"),  # Not found
            client.post("/items", json={"price": 10}),  # Missing name
        ]
        
        # All should return JSON with error info
        for r in error_responses:
            assert r.status_code >= 400
            data = r.json()
            assert "detail" in data
            assert isinstance(data["detail"], str)
