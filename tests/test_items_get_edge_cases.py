"""Path parameter, edge case, and integration tests."""
from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test path parameter validation for get_item."""

    @pytest.mark.parametrize("item_id", [-1000, -100, -1])
    def test_negative_item_id_not_found(self, item_id):
        """Negative item IDs return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_zero_item_id_not_found(self):
        """Item ID 0 returns 404."""
        r = client.get("/items/0")
        assert r.status_code == 404

    @pytest.mark.parametrize("item_id", [1e10, 999999, 9999])
    def test_large_item_id_not_found(self, item_id):
        """Very large item IDs return 404."""
        r = client.get(f"/items/{int(item_id)}")
        assert r.status_code == 404

    def test_only_item_1_exists(self):
        """Only item ID 1 is available."""
        r = client.get("/items/1")
        assert r.status_code == 200
        
        # All other IDs should return 404
        for item_id in [0, 2, 3, 100, -1]:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404


class TestPathParameterTypeCoercion:
    """Test path parameter type handling."""

    def test_numeric_path_parameter(self):
        """Path parameter must be numeric."""
        # FastAPI should reject non-numeric path parameters at routing level
        # This would result in 404 (no matching route) rather than getting to handler
        r = client.get("/items/abc")
        assert r.status_code == 404  # FastAPI can't route to handler

    def test_float_path_parameter_coerced_to_int(self):
        """Float in path is coerced to int (or rejected by FastAPI)."""
        # FastAPI path parameters with int type should reject floats
        r = client.get("/items/1.5")
        assert r.status_code == 404  # Route not found


class TestCreateItemSequenceAndOrder:
    """Test create_item endpoint behavior across multiple requests."""

    def test_multiple_creates_same_response(self):
        """Multiple create requests all return id=1."""
        for i in range(3):
            r = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            assert r.status_code == 200
            assert r.json()["id"] == 1

    def test_creates_with_different_data(self):
        """Multiple creates with different data all succeed."""
        items = [
            {"name": "apple", "price": 1.5},
            {"name": "book", "price": 9.99},
            {"name": "pencil", "price": 0.50},
        ]
        for item in items:
            r = client.post("/items", json=item)
            assert r.status_code == 200
            data = r.json()
            assert data["name"] == item["name"]
            assert data["price"] == item["price"]


class TestGetItemConsistency:
    """Test get_item consistency across requests."""

    def test_get_item_1_consistent(self):
        """Getting item 1 multiple times returns same data."""
        results = []
        for _ in range(3):
            r = client.get("/items/1")
            results.append(r.json())
        
        # All should be identical
        assert all(item == results[0] for item in results)

    def test_get_item_1_always_has_correct_data(self):
        """Item 1 always has id=1, name=sample, price=10.0."""
        r = client.get("/items/1")
        data = r.json()
        assert data == {"id": 1, "name": "sample", "price": 10.0}


class TestHealthEndpointConsistency:
    """Test health endpoint consistency."""

    def test_health_always_returns_same(self):
        """Health endpoint always returns same response."""
        responses = []
        for _ in range(5):
            r = client.get("/health")
            responses.append(r.json())
        
        assert all(resp == responses[0] for resp in responses)
        assert responses[0] == {"status": "ok"}


class TestErrorHandlingIntegration:
    """Test error handling across endpoints."""

    def test_invalid_price_consistent_error(self):
        """Invalid prices produce consistent error responses."""
        invalid_prices = [-1, 0, -100]
        
        for price in invalid_prices:
            r = client.post("/items", json={"name": "test", "price": price})
            assert r.status_code == 400
            assert r.json()["detail"] == "price must be > 0"

    def test_missing_fields_produces_422(self):
        """Various missing field scenarios all produce 422."""
        invalid_requests = [
            {"price": 10.0},  # missing name
            {"name": "test"},  # missing price
            {},  # empty
        ]
        
        for req in invalid_requests:
            r = client.post("/items", json=req)
            assert r.status_code == 422


class TestBoundaryConditions:
    """Test boundary conditions and edge cases."""

    def test_very_small_positive_price(self):
        """Smallest positive price is accepted."""
        prices = [0.01, 0.001, 0.0001, 1e-10]
        for price in prices:
            r = client.post("/items", json={"name": "test", "price": price})
            assert r.status_code == 200
            assert r.json()["price"] == price

    def test_price_exactly_zero_rejected(self):
        """Price exactly 0 is rejected."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400

    def test_price_just_above_zero_accepted(self):
        """Price just above 0 is accepted."""
        r = client.post("/items", json={"name": "test", "price": 1e-100})
        assert r.status_code == 200

    def test_very_large_price(self):
        """Very large prices are accepted."""
        r = client.post("/items", json={"name": "test", "price": 1e100})
        assert r.status_code == 200

    def test_name_with_newlines(self):
        """Names with newlines are accepted."""
        r = client.post("/items", json={"name": "line1\nline2", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "line1\nline2"

    def test_name_with_tabs(self):
        """Names with tabs are accepted."""
        r = client.post("/items", json={"name": "col1\tcol2", "price": 10.0})
        assert r.status_code == 200


class TestAPIRouting:
    """Test API endpoint routing and existence."""

    def test_health_endpoint_exists(self):
        """Health endpoint is accessible."""
        r = client.get("/health")
        assert r.status_code == 200

    def test_create_items_endpoint_exists(self):
        """POST /items endpoint is accessible."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200

    def test_get_item_endpoint_exists(self):
        """GET /items/{id} endpoint is accessible."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_nonexistent_endpoint_returns_404(self):
        """Non-existent endpoints return 404."""
        r = client.get("/nonexistent")
        assert r.status_code == 404

    def test_wrong_method_returns_405(self):
        """Wrong HTTP method returns 405."""
        r = client.get("/items")  # Should be POST
        # Depending on routing, could be 404 or 405
        assert r.status_code in [404, 405]


class TestResponseContentValidation:
    """Test response content is valid and expected."""

    def test_item_response_valid_json(self):
        """Item response is valid JSON."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        # Should not raise
        data = r.json()
        assert isinstance(data, dict)

    def test_error_response_valid_json(self):
        """Error response is valid JSON."""
        r = client.post("/items", json={"name": "test", "price": 0})
        # Should not raise
        data = r.json()
        assert isinstance(data, dict)
        assert "detail" in data

    def test_health_response_valid_json(self):
        """Health response is valid JSON."""
        r = client.get("/health")
        # Should not raise
        data = r.json()
        assert isinstance(data, dict)


class TestConcurrentOperations:
    """Test behavior with multiple operations."""

    def test_interleaved_creates_and_gets(self):
        """Interleaving creates and gets works correctly."""
        # Create item
        r1 = client.post("/items", json={"name": "first", "price": 5.0})
        assert r1.status_code == 200
        
        # Get item 1
        r2 = client.get("/items/1")
        assert r2.status_code == 200
        assert r2.json()["id"] == 1
        
        # Create another
        r3 = client.post("/items", json={"name": "second", "price": 15.0})
        assert r3.status_code == 200
        
        # Get item 1 again
        r4 = client.get("/items/1")
        assert r4.status_code == 200
        assert r4.json()["id"] == 1

    def test_health_between_operations(self):
        """Health check works between other operations."""
        r1 = client.get("/health")
        assert r1.status_code == 200
        
        r2 = client.post("/items", json={"name": "test", "price": 10.0})
        assert r2.status_code == 200
        
        r3 = client.get("/health")
        assert r3.status_code == 200
        assert r3.json() == {"status": "ok"}
