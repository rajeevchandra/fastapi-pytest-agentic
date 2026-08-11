"""
Edge case and integration tests for all endpoints.
Tests boundary values, path parameters, and end-to-end scenarios.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test path parameter validation for GET /items/{item_id}."""

    @pytest.mark.parametrize("item_id", [
        1,           # Valid existing item
        2,           # Valid non-existing item
        0,           # Zero
        -1,          # Negative
        999999,      # Large positive
        -999999,     # Large negative
    ])
    def test_various_item_ids(self, item_id):
        """Various item_id values should be accepted by FastAPI."""
        r = client.get(f"/items/{item_id}")
        # All numeric IDs are valid for FastAPI; only ID=1 returns 200
        assert r.status_code in (200, 404)

    def test_item_id_1_found(self):
        """Item ID 1 should always be found."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_item_id_not_1_not_found(self):
        """Any item ID other than 1 should return 404."""
        for item_id in [0, 2, 3, 100, 999]:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404


class TestCreateItemBoundaryPrices:
    """Test extreme price boundary conditions."""

    @pytest.mark.parametrize("price", [
        0.001,           # Very small valid
        0.01,            # Typical minimum
        999999999.99,    # Very large
        1.0,             # Unity
        0.5,             # Half
    ])
    def test_extreme_valid_prices(self, price):
        """Extreme but valid prices should be accepted."""
        r = client.post("/items", json={"name": "extreme", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    @pytest.mark.parametrize("price", [
        -0.001,      # Very small negative
        -0.01,       # Small negative
        -999999.99,  # Large negative
    ])
    def test_negative_prices_boundary(self, price):
        """All negative prices should be rejected."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400


class TestCreateItemWithExtraFields:
    """Test how the API handles extra fields in request."""

    def test_extra_field_ignored(self):
        """Extra fields should not cause errors."""
        r = client.post("/items", json={
            "name": "test",
            "price": 10.0,
            "description": "extra field",
            "quantity": 5,
        })
        # FastAPI/Pydantic ignores extra fields by default
        assert r.status_code == 200

    def test_extra_field_not_in_response(self):
        """Extra fields should not appear in response."""
        r = client.post("/items", json={
            "name": "test",
            "price": 10.0,
            "extra": "field",
        })
        assert "extra" not in r.json()


class TestResponseDataTypes:
    """Verify response data types are correct."""

    def test_get_item_id_is_integer(self):
        """Item ID in response should be integer."""
        r = client.get("/items/1")
        assert isinstance(r.json()["id"], int)

    def test_get_item_name_is_string(self):
        """Item name in response should be string."""
        r = client.get("/items/1")
        assert isinstance(r.json()["name"], str)

    def test_get_item_price_is_numeric(self):
        """Item price in response should be numeric."""
        r = client.get("/items/1")
        price = r.json()["price"]
        assert isinstance(price, (int, float))
        assert price > 0

    def test_post_response_types(self):
        """POST response should have correct types."""
        r = client.post("/items", json={"name": "test", "price": 10.50})
        data = r.json()
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], (int, float))


class TestEndToEndScenarios:
    """Test realistic end-to-end usage scenarios."""

    def test_create_item_then_get_it(self):
        """Create item then retrieve it."""
        post_r = client.post("/items", json={"name": "created", "price": 15.0})
        assert post_r.status_code == 200
        created_id = post_r.json()["id"]
        
        get_r = client.get(f"/items/{created_id}")
        assert get_r.status_code == 200
        assert get_r.json()["name"] == "created"

    def test_multiple_create_operations(self):
        """Multiple create operations should work."""
        prices = [10.0, 20.0, 30.0, 40.0]
        for price in prices:
            r = client.post("/items", json={"name": f"item", "price": price})
            assert r.status_code == 200

    def test_error_recovery(self):
        """API should recover from error requests."""
        # First: invalid request
        r1 = client.post("/items", json={"name": "test", "price": 0})
        assert r1.status_code == 400
        
        # Second: valid request should still work
        r2 = client.post("/items", json={"name": "test", "price": 10.0})
        assert r2.status_code == 200


class TestNameFieldEdgeCases:
    """Test edge cases for name field."""

    @pytest.mark.parametrize("name", [
        "",
        " ",
        "   ",
        "a",
        "A" * 500,
        "123",
        "!@#$%^&*()",
        "name with spaces",
        "name\twith\ttabs",
        "Café",
        "日本語",
        "😀",
    ])
    def test_various_name_strings(self, name):
        """Various name strings should be accepted."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name


class TestAPIAvailability:
    """Test API endpoints are available and responsive."""

    def test_all_endpoints_available(self):
        """All endpoints should be accessible."""
        # Health endpoint
        r1 = client.get("/health")
        assert r1.status_code == 200
        
        # Get item endpoint
        r2 = client.get("/items/1")
        assert r2.status_code in (200, 404)  # Either found or not found is OK
        
        # Create item endpoint
        r3 = client.post("/items", json={"name": "test", "price": 10.0})
        assert r3.status_code in (200, 400, 422)

    def test_method_not_allowed_on_create_endpoint(self):
        """GET on create endpoint should be method not allowed."""
        r = client.get("/items")
        assert r.status_code == 405  # Method Not Allowed

    def test_invalid_endpoint_returns_404(self):
        """Invalid endpoint should return 404."""
        r = client.get("/nonexistent")
        assert r.status_code == 404


class TestPriceEdgeCases:
    """Test edge cases for price field."""

    def test_price_precision_preserved(self):
        """Price precision should be preserved in response."""
        test_prices = [10.01, 99.99, 0.01, 123.456]
        for price in test_prices:
            r = client.post("/items", json={"name": "test", "price": price})
            assert r.json()["price"] == price

    def test_float_price_converted_properly(self):
        """Float prices should be converted properly."""
        r = client.post("/items", json={"name": "test", "price": 10})
        assert r.status_code == 200
        # JSON might represent 10 as int or 10.0, both are valid
        price = r.json()["price"]
        assert price == 10 or price == 10.0

    def test_scientific_notation_price(self):
        """Very small prices in scientific notation should work."""
        r = client.post("/items", json={"name": "test", "price": 0.0001})
        assert r.status_code == 200
        assert r.json()["price"] == 0.0001


class TestConcurrentBehavior:
    """Test behavior under rapid requests."""

    def test_rapid_create_requests(self):
        """Multiple rapid create requests should work."""
        for i in range(10):
            r = client.post("/items", json={"name": f"item_{i}", "price": float(i + 1)})
            assert r.status_code == 200

    def test_rapid_get_requests(self):
        """Multiple rapid get requests should work."""
        for _ in range(10):
            r = client.get("/items/1")
            assert r.status_code == 200

    def test_mixed_rapid_requests(self):
        """Rapid mixed requests should work."""
        for i in range(5):
            r1 = client.post("/items", json={"name": f"test_{i}", "price": 10.0})
            assert r1.status_code == 200
            
            r2 = client.get("/items/1")
            assert r2.status_code == 200
            
            r3 = client.get("/health")
            assert r3.status_code == 200
