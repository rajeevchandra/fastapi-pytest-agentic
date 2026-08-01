"""Path parameter edge cases and integration testing."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test GET /items/{item_id} with various path parameter values."""

    @pytest.mark.parametrize("item_id,should_exist", [
        (1, True),        # Valid - item exists
        (0, False),       # Zero - not found
        (-1, False),      # Negative - not found
        (2, False),       # Different ID - not found
        (999999, False),  # Very large ID - not found
    ])
    def test_get_item_by_id_boundaries(self, item_id, should_exist):
        """Test GET endpoint with various ID boundary values."""
        r = client.get(f"/items/{item_id}")
        if should_exist:
            assert r.status_code == 200
            data = r.json()
            assert data["id"] == item_id
        else:
            assert r.status_code == 404
            data = r.json()
            assert data["detail"] == "not found"


class TestHealthEndpoint:
    """Test health endpoint."""

    def test_health_returns_ok(self):
        """Test that health endpoint returns ok status."""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"

    def test_health_response_type(self):
        """Test health response has correct type."""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["status"], str)


class TestEndToEndIntegration:
    """Test multi-step integration scenarios."""

    def test_create_then_get(self):
        """Test creating an item then retrieving it."""
        # Create an item
        create_r = client.post("/items", json={"name": "widget", "price": 25.0})
        assert create_r.status_code == 200
        created_data = create_r.json()
        created_id = created_data["id"]
        
        # Retrieve the created item
        get_r = client.get(f"/items/{created_id}")
        assert get_r.status_code == 200
        retrieved_data = get_r.json()
        assert retrieved_data["id"] == created_id

    def test_multiple_creates_then_gets(self):
        """Test creating multiple items and retrieving them."""
        for i in range(3):
            r = client.post("/items", json={"name": f"item_{i}", "price": 10.0 + i})
            assert r.status_code == 200

    def test_valid_then_invalid_create(self):
        """Test valid creation followed by invalid creation."""
        # Valid create
        valid_r = client.post("/items", json={"name": "good", "price": 10.0})
        assert valid_r.status_code == 200
        
        # Invalid create (bad price)
        invalid_r = client.post("/items", json={"name": "bad", "price": -1})
        assert invalid_r.status_code == 400

    def test_health_then_items(self):
        """Test checking health then accessing items."""
        # Check health
        health_r = client.get("/health")
        assert health_r.status_code == 200
        
        # Create item
        create_r = client.post("/items", json={"name": "test", "price": 5.0})
        assert create_r.status_code == 200


class TestBoundaryValuePairings:
    """Test combinations of boundary values."""

    @pytest.mark.parametrize("name,price", [
        ("a", 0.01),           # Minimal values
        ("x" * 100, 999999.99), # Maximal values
        ("test", 1.0),          # Common values
        ("special!@#", 100.5),  # Special characters
        ("123", 0.1),           # Numeric name
    ])
    def test_boundary_value_combinations(self, name, price):
        """Test various boundary value combinations."""
        r = client.post("/items", json={"name": name, "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name
        assert data["price"] == price


class TestResponseConsistency:
    """Test that responses are consistent."""

    def test_same_request_same_response(self):
        """Test that identical requests produce identical responses."""
        request_data = {"name": "test", "price": 10.0}
        
        r1 = client.post("/items", json=request_data)
        r2 = client.post("/items", json=request_data)
        
        assert r1.status_code == r2.status_code
        assert r1.json()["name"] == r2.json()["name"]
        assert r1.json()["price"] == r2.json()["price"]

    def test_get_item_1_consistency(self):
        """Test that getting item 1 returns consistent data."""
        r1 = client.get("/items/1")
        r2 = client.get("/items/1")
        
        assert r1.status_code == r2.status_code
        data1 = r1.json()
        data2 = r2.json()
        assert data1 == data2

    def test_error_consistency(self):
        """Test that errors for same request are consistent."""
        request_data = {"name": "test", "price": -1}
        
        r1 = client.post("/items", json=request_data)
        r2 = client.post("/items", json=request_data)
        
        assert r1.status_code == r2.status_code
        assert r1.json() == r2.json()


class TestErrorRecovery:
    """Test API behavior after errors."""

    def test_valid_request_after_invalid_price(self):
        """Test that valid request works after invalid price error."""
        # Invalid request
        bad_r = client.post("/items", json={"name": "test", "price": -1})
        assert bad_r.status_code == 400
        
        # Valid request should still work
        good_r = client.post("/items", json={"name": "test", "price": 10.0})
        assert good_r.status_code == 200

    def test_valid_request_after_missing_field(self):
        """Test that valid request works after missing field error."""
        # Invalid request (missing price)
        bad_r = client.post("/items", json={"name": "test"})
        assert bad_r.status_code == 422
        
        # Valid request should still work
        good_r = client.post("/items", json={"name": "test", "price": 10.0})
        assert good_r.status_code == 200

    def test_valid_request_after_not_found(self):
        """Test that valid request works after 404 error."""
        # Get non-existent item
        not_found_r = client.get("/items/999")
        assert not_found_r.status_code == 404
        
        # Valid create should still work
        create_r = client.post("/items", json={"name": "test", "price": 10.0})
        assert create_r.status_code == 200
