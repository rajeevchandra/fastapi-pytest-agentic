"""Integration and comprehensive response validation tests."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestResponseTypeValidation:
    """Test response type validation across endpoints."""

    def test_health_response_type(self):
        """Health check should return JSON with status."""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)
        assert "status" in data

    def test_create_item_response_type(self):
        """Create item response should have all required fields."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        data = r.json()
        required_fields = {"id", "name", "price"}
        assert required_fields.issubset(set(data.keys()))

    def test_get_item_response_type(self):
        """Get item response should have all required fields."""
        r = client.get("/items/1")
        data = r.json()
        required_fields = {"id", "name", "price"}
        assert required_fields.issubset(set(data.keys()))


class TestResponseHeaders:
    """Test HTTP response headers."""

    def test_create_item_headers(self):
        """Create item should return correct headers."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        assert "content-type" in r.headers
        assert "application/json" in r.headers["content-type"]

    def test_get_item_headers(self):
        """Get item should return correct headers."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert "content-type" in r.headers
        assert "application/json" in r.headers["content-type"]

    def test_error_response_headers(self):
        """Error responses should be JSON."""
        r = client.get("/items/999")
        assert r.status_code == 404
        assert "content-type" in r.headers
        assert "application/json" in r.headers["content-type"]


class TestIntegrationWorkflows:
    """Test complete workflows combining multiple endpoints."""

    def test_create_then_retrieve_workflow(self):
        """Create an item and verify it can be retrieved."""
        # Create item
        create_r = client.post("/items", json={"name": "workflow-test", "price": 25.0})
        assert create_r.status_code == 200
        created = create_r.json()
        
        # The API returns id=1 always, so retrieve it
        get_r = client.get(f"/items/{created['id']}")
        assert get_r.status_code == 200
        retrieved = get_r.json()
        
        # Verify id matches
        assert retrieved["id"] == created["id"]

    def test_health_check_workflow(self):
        """Health check should be accessible and return ok status."""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data.get("status") == "ok"

    def test_multiple_items_workflow(self):
        """Create multiple items and verify they all have id=1."""
        items = [
            {"name": "book1", "price": 10.0},
            {"name": "book2", "price": 15.0},
            {"name": "book3", "price": 20.0},
        ]
        
        for item in items:
            r = client.post("/items", json=item)
            assert r.status_code == 200
            data = r.json()
            assert data["id"] == 1
            assert data["name"] == item["name"]
            assert data["price"] == item["price"]


class TestResponseConsistency:
    """Test consistency of responses."""

    def test_item_response_format_consistency(self):
        """All successful item responses should have consistent format."""
        prices = [5.0, 10.0, 99.99]
        responses = []
        
        for price in prices:
            r = client.post("/items", json={"name": f"test-{price}", "price": price})
            responses.append(r.json())
        
        # All should have the same keys
        keys = set(responses[0].keys())
        for resp in responses:
            assert set(resp.keys()) == keys

    def test_error_response_format_consistency(self):
        """All error responses should have consistent format."""
        invalid_ids = [999, -1, 0, 100]
        responses = []
        
        for item_id in invalid_ids:
            r = client.get(f"/items/{item_id}")
            responses.append(r.json())
        
        # All should have detail field
        for resp in responses:
            assert "detail" in resp


class TestParametrizedIntegration:
    """Parametrized integration tests."""

    @pytest.mark.parametrize("price", [1.0, 5.0, 10.0, 50.0, 100.0])
    def test_create_items_various_prices(self, price):
        """Create items with various prices."""
        r = client.post("/items", json={"name": f"item-{price}", "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == price
        assert data["id"] == 1

    @pytest.mark.parametrize("name", ["book", "pen", "notebook", "desk", "chair"])
    def test_create_items_various_names(self, name):
        """Create items with various names."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name
        assert data["id"] == 1

    @pytest.mark.parametrize("item_id", [1])
    def test_retrieve_existing_item(self, item_id):
        """Retrieve existing item."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == item_id


class TestErrorHandling:
    """Test error handling and error messages."""

    def test_price_validation_error_message(self):
        """Price validation error should have clear message."""
        r = client.post("/items", json={"name": "test", "price": -5.0})
        assert r.status_code == 400
        data = r.json()
        assert "price" in data["detail"].lower()
        assert "0" in data["detail"]

    def test_not_found_error_message(self):
        """Not found error should have clear message."""
        r = client.get("/items/999")
        assert r.status_code == 404
        data = r.json()
        assert "not found" in data["detail"].lower()

    def test_missing_field_error(self):
        """Missing required field should return 422."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422
        # Should have detail field
        data = r.json()
        assert "detail" in data

    def test_invalid_type_error(self):
        """Invalid type should return 422."""
        r = client.post("/items", json={"name": 123, "price": "invalid"})
        assert r.status_code == 422


class TestStatusCodeProgression:
    """Test expected status code sequences."""

    def test_success_status_codes(self):
        """Successful operations should return 2xx."""
        success_operations = [
            ("GET", "/health"),
            ("POST", "/items", {"name": "test", "price": 10.0}),
            ("GET", "/items/1"),
        ]
        
        for op in success_operations:
            if op[0] == "GET":
                r = client.get(op[1])
            else:
                r = client.post(op[1], json=op[2])
            assert 200 <= r.status_code < 300

    def test_error_status_codes(self):
        """Error operations should return 4xx or 5xx."""
        error_operations = [
            ("GET", "/items/999"),
            ("POST", "/items", {"name": "test", "price": -1}),
            ("POST", "/items", {"name": "test"}),
        ]
        
        for op in error_operations:
            if op[0] == "GET":
                r = client.get(op[1])
            else:
                r = client.post(op[1], json=op[2])
            assert r.status_code >= 400
