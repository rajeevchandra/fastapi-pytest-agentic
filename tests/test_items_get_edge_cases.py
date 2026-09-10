"""Path parameter validation and edge case testing."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test item_id path parameter validation."""

    @pytest.mark.parametrize("item_id", [1])
    def test_get_item_valid_id_found(self, item_id):
        """Valid item_id that exists should return 200."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 200
        assert r.json()["id"] == 1

    @pytest.mark.parametrize("item_id", [2, 3, 10, 100, 1000, 999999])
    def test_get_item_valid_ids_not_found(self, item_id):
        """Valid but non-existent item_ids should return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    @pytest.mark.parametrize("item_id", [-1, -10, -999])
    def test_get_item_negative_ids(self, item_id):
        """Negative item_ids should return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    @pytest.mark.parametrize("item_id", [0])
    def test_get_item_zero_id(self, item_id):
        """Zero item_id should return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    def test_get_item_very_large_id(self):
        """Very large item_id should return 404."""
        r = client.get(f"/items/{2**31}")
        assert r.status_code == 404


class TestGetItemPathParameterTypeCoercion:
    """Test path parameter type handling."""

    def test_get_item_with_float_like_string(self):
        """Float-like string in path should cause validation error."""
        r = client.get("/items/1.5")
        assert r.status_code == 422

    def test_get_item_with_non_numeric_string(self):
        """Non-numeric string in path should cause validation error."""
        r = client.get("/items/abc")
        assert r.status_code == 422

    def test_get_item_with_empty_string(self):
        """Empty path segment should cause error."""
        # This typically results in different behavior
        r = client.get("/items/")
        # Could be 404 (route not found) or 422 depending on framework
        assert r.status_code in [404, 422]


class TestPriceEdgeCases:
    """Test price field edge cases."""

    def test_create_item_very_small_positive_price(self):
        """Very small positive price should be accepted."""
        r = client.post("/items", json={"name": "test", "price": 0.0001})
        assert r.status_code == 200
        assert r.json()["price"] == 0.0001

    def test_create_item_very_large_price(self):
        """Very large price should be accepted."""
        r = client.post("/items", json={"name": "test", "price": 1e15})
        assert r.status_code == 200
        assert r.json()["price"] == 1e15

    def test_create_item_price_with_many_decimals(self):
        """Price with many decimal places should be handled."""
        price = 123.456789
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 200
        # Float precision may vary slightly
        assert abs(r.json()["price"] - price) < 1e-9

    def test_create_item_infinity_price(self):
        """Infinite price should either be accepted or rejected."""
        # JSON doesn't support infinity, so this will fail at JSON level
        # This is implementation dependent
        try:
            import json
            # Python's json module doesn't support infinity by default
            json.dumps({"price": float('inf')})
            # If it somehow works, try the request
            r = client.post("/items", json={"name": "test", "price": float('inf')})
            assert r.status_code in [200, 400, 422]
        except (ValueError, OverflowError):
            # Expected - JSON can't represent infinity
            pass

    def test_create_item_nan_price(self):
        """NaN price should either be accepted or rejected."""
        try:
            import json
            json.dumps({"price": float('nan')})
            r = client.post("/items", json={"name": "test", "price": float('nan')})
            assert r.status_code in [200, 400, 422]
        except (ValueError, OverflowError):
            # Expected - JSON can't represent NaN
            pass


class TestNameEdgeCases:
    """Test name field edge cases."""

    def test_create_item_with_newlines_in_name(self):
        """Name with newlines should be accepted."""
        name = "line1\nline2\nline3"
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_create_item_with_tabs_in_name(self):
        """Name with tabs should be accepted."""
        name = "col1\tcol2\tcol3"
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_create_item_with_quotes_in_name(self):
        """Name with quotes should be accepted."""
        name = 'She said "hello"'
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_create_item_with_backslashes_in_name(self):
        """Name with backslashes should be accepted."""
        name = r"path\to\file"
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_create_item_with_null_bytes_in_name(self):
        """Names with null bytes should be handled."""
        # This is tricky - null bytes in JSON strings are typically escaped
        name = "test\x00name"
        r = client.post("/items", json={"name": name, "price": 10.0})
        # Should succeed since null bytes are valid in JSON
        assert r.status_code == 200


class TestIntegrationEdgeCases:
    """Test integration scenarios."""

    def test_create_then_retrieve_same_item(self):
        """Item created with specific data should be retrievable as id=1."""
        # Create item
        created = client.post("/items", json={"name": "myitem", "price": 25.50})
        assert created.status_code == 200
        
        # Retrieve it
        retrieved = client.get("/items/1")
        assert retrieved.status_code == 200
        
        # They should have same structure but different values
        # (created has user data, retrieved has hardcoded data)
        assert set(created.json().keys()) == set(retrieved.json().keys())

    def test_multiple_creates_and_retrieves(self):
        """Multiple creates should all return id=1."""
        for i in range(5):
            r = client.post("/items", json={"name": f"item{i}", "price": float(i + 1)})
            assert r.status_code == 200
            assert r.json()["id"] == 1

    def test_get_non_existent_after_multiple_creates(self):
        """Non-existent ids should still return 404 after creates."""
        # Create some items
        for i in range(3):
            client.post("/items", json={"name": f"item{i}", "price": 10.0})
        
        # Try to get non-existent
        r = client.get("/items/999")
        assert r.status_code == 404


class TestAPIConsistency:
    """Test consistency of API behavior."""

    def test_same_request_twice_same_response(self):
        """Same request twice should give identical responses."""
        req_data = {"name": "test", "price": 10.0}
        r1 = client.post("/items", json=req_data)
        r2 = client.post("/items", json=req_data)
        assert r1.json() == r2.json()
        assert r1.status_code == r2.status_code

    def test_get_item_1_consistency(self):
        """Getting item 1 should always return same data."""
        results = [client.get("/items/1").json() for _ in range(10)]
        # All results should be identical
        assert all(r == results[0] for r in results)

    def test_error_responses_consistent(self):
        """Same error should produce consistent error response."""
        req_data = {"name": "test", "price": -5}
        r1 = client.post("/items", json=req_data)
        r2 = client.post("/items", json=req_data)
        assert r1.json() == r2.json()
        assert r1.status_code == r2.status_code == 400


class TestRequestMethodValidation:
    """Test that wrong HTTP methods are rejected."""

    def test_post_to_get_endpoint_not_allowed(self):
        """POST to GET endpoint should fail."""
        r = client.post("/items/1")
        assert r.status_code in [405, 422, 400]

    def test_get_to_post_endpoint_not_allowed(self):
        """GET to POST endpoint should fail."""
        r = client.get("/items")
        assert r.status_code in [405, 404]

    def test_put_method_not_supported(self):
        """PUT method should not be supported."""
        r = client.put("/items/1", json={"name": "test", "price": 10.0})
        assert r.status_code in [405, 404]

    def test_delete_method_not_supported(self):
        """DELETE method should not be supported."""
        r = client.delete("/items/1")
        assert r.status_code in [405, 404]
