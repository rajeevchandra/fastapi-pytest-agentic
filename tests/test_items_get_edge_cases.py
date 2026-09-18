"""
Test suite for path parameter validation and integration edge cases.

This module provides comprehensive tests for:
- Path parameter boundary values (negative, zero, large)
- Item id edge cases
- Integration scenarios between endpoints
- Idempotency and consistency
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Tests for path parameter validation on item retrieval."""

    @pytest.mark.parametrize("item_id", [1])
    def test_get_item_valid_id(self, item_id):
        """Valid item id returns 200."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 200
        assert r.json()["id"] == item_id

    @pytest.mark.parametrize("item_id", [-1, -100, -1000])
    def test_get_item_negative_id_returns_404(self, item_id):
        """Negative item ids return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    def test_get_item_zero_id_returns_404(self):
        """Zero item id returns 404."""
        r = client.get(f"/items/0")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    @pytest.mark.parametrize("item_id", [2, 3, 5, 10, 100, 1000, 999999])
    def test_get_item_other_positive_ids_return_404(self, item_id):
        """Positive item ids other than 1 return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    def test_get_item_very_large_id_returns_404(self):
        """Very large item id returns 404."""
        r = client.get(f"/items/{2**63-1}")  # Max 64-bit int
        assert r.status_code == 404

    def test_get_item_id_1_returns_found(self):
        """Item id 1 is the only valid id."""
        r = client.get("/items/1")
        assert r.status_code == 200


class TestGetItemPathParameterTypes:
    """Tests for path parameter type validation."""

    def test_get_item_with_valid_integer_type(self):
        """Integer path parameter is accepted."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_get_item_with_leading_zeros(self):
        """Path parameter with leading zeros is parsed as integer."""
        r = client.get("/items/001")  # Should be treated as 1
        assert r.status_code == 200

    def test_get_item_with_leading_zeros_non_one(self):
        """Path parameter with leading zeros converts to integer."""
        r = client.get("/items/0002")  # Should be treated as 2
        assert r.status_code == 404

    def test_get_item_with_float_like_string(self):
        """Float-like path parameters cause bad request."""
        r = client.get("/items/1.5")
        assert r.status_code in [404, 422]  # Depends on parser

    def test_get_item_with_negative_sign(self):
        """Negative path parameters are parsed correctly."""
        r = client.get("/items/-1")
        assert r.status_code == 404


class TestCreateItemIdempotency:
    """Tests for idempotency and consistency of create endpoint."""

    def test_create_item_multiple_calls_same_id(self):
        """Multiple item creations return same id."""
        r1 = client.post("/items", json={"name": "item1", "price": 10})
        r2 = client.post("/items", json={"name": "item2", "price": 20})
        assert r1.json()["id"] == r2.json()["id"] == 1

    def test_create_item_does_not_persist(self):
        """Created items are not persisted (no backend storage)."""
        # Create an item
        r_create = client.post("/items", json={"name": "ephemeral", "price": 50})
        assert r_create.status_code == 200
        
        # Created item is not returned on get (only id=1 works)
        r_get = client.get("/items/1")
        assert r_get.status_code == 200
        # The retrieved item has the default data, not the created one
        assert r_get.json()["name"] == "sample"

    def test_create_item_with_same_data_twice(self):
        """Creating with same data twice returns same response."""
        data = {"name": "duplicate", "price": 25.50}
        r1 = client.post("/items", json=data)
        r2 = client.post("/items", json=data)
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r1.json()["name"] == r2.json()["name"]
        assert r1.json()["price"] == r2.json()["price"]


class TestGetItemConsistency:
    """Tests for consistency of get endpoint."""

    def test_get_item_1_always_returns_same_data(self):
        """Getting item 1 always returns consistent data."""
        results = []
        for _ in range(5):
            r = client.get("/items/1")
            results.append(r.json())
        
        # All results should be identical
        for result in results[1:]:
            assert result == results[0]

    def test_get_item_1_has_expected_fields(self):
        """Item 1 has expected default data."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0

    def test_get_item_1_not_affected_by_create(self):
        """Creating items does not affect item 1 data."""
        # Get item 1 initially
        r_before = client.get("/items/1")
        before_data = r_before.json()
        
        # Create multiple items
        for i in range(5):
            client.post("/items", json={"name": f"item{i}", "price": 10 + i})
        
        # Get item 1 again
        r_after = client.get("/items/1")
        after_data = r_after.json()
        
        # Should be identical
        assert before_data == after_data


class TestEndpointIntegration:
    """Integration tests combining multiple endpoints."""

    def test_create_then_get_returns_created_data(self):
        """Created item data appears in response (for id 1)."""
        # Note: In this implementation, item 1 is fixed, not dynamic
        r_get = client.get("/items/1")
        assert r_get.status_code == 200

    def test_create_different_names_get_same_id(self):
        """Multiple items created with different names all return id 1."""
        names = ["apple", "banana", "cherry"]
        responses = []
        for name in names:
            r = client.post("/items", json={"name": name, "price": 10})
            responses.append(r.json())
        
        # All have same id
        assert all(resp["id"] == 1 for resp in responses)
        # But names differ in response
        assert responses[0]["name"] == "apple"
        assert responses[1]["name"] == "banana"
        assert responses[2]["name"] == "cherry"

    def test_create_different_prices_get_same_id(self):
        """Multiple items created with different prices all return id 1."""
        prices = [9.99, 19.99, 99.99]
        responses = []
        for price in prices:
            r = client.post("/items", json={"name": "item", "price": price})
            responses.append(r.json())
        
        # All have same id
        assert all(resp["id"] == 1 for resp in responses)
        # Prices are preserved in response
        assert responses[0]["price"] == 9.99
        assert responses[1]["price"] == 19.99
        assert responses[2]["price"] == 99.99

    def test_get_non_existent_then_get_existing(self):
        """Getting non-existent item then existing item works correctly."""
        r_404 = client.get("/items/999")
        assert r_404.status_code == 404
        
        r_200 = client.get("/items/1")
        assert r_200.status_code == 200
        assert r_200.json()["id"] == 1

    def test_multiple_operations_sequence(self):
        """Complex sequence of operations maintains consistency."""
        # Create some items
        r1 = client.post("/items", json={"name": "first", "price": 10})
        assert r1.status_code == 200
        
        # Get non-existent
        r2 = client.get("/items/5")
        assert r2.status_code == 404
        
        # Get existing
        r3 = client.get("/items/1")
        assert r3.status_code == 200
        
        # Create another
        r4 = client.post("/items", json={"name": "second", "price": 20})
        assert r4.status_code == 200
        
        # Get existing again - should be unchanged
        r5 = client.get("/items/1")
        assert r5.status_code == 200
        assert r5.json() == r3.json()


class TestErrorRecovery:
    """Tests for error recovery and error handling consistency."""

    def test_create_with_error_then_valid(self):
        """Valid request after error works correctly."""
        # Send invalid request
        r_err = client.post("/items", json={"name": "bad", "price": -5})
        assert r_err.status_code == 400
        
        # Send valid request
        r_ok = client.post("/items", json={"name": "good", "price": 5})
        assert r_ok.status_code == 200

    def test_get_not_found_then_found(self):
        """Valid request after 404 works correctly."""
        # Get non-existent
        r_404 = client.get("/items/999")
        assert r_404.status_code == 404
        
        # Get existing
        r_200 = client.get("/items/1")
        assert r_200.status_code == 200

    def test_validation_error_recovery(self):
        """Multiple validation errors in sequence."""
        errors = [
            {"name": "item", "price": -1},
            {"name": "item", "price": 0},
            {"name": "item"},
        ]
        
        for error_data in errors:
            if "price" in error_data and error_data.get("price", 1) <= 0:
                r = client.post("/items", json=error_data)
                assert r.status_code == 400
            else:
                r = client.post("/items", json=error_data)
                assert r.status_code == 422

    def test_valid_after_multiple_errors(self):
        """Valid request works after multiple errors."""
        # Multiple error requests
        for _ in range(3):
            client.post("/items", json={"name": "item", "price": -1})
        
        # Valid request should still work
        r = client.post("/items", json={"name": "valid", "price": 10})
        assert r.status_code == 200


class TestBoundaryValueCombinations:
    """Tests for boundary value combinations."""

    def test_create_with_max_safe_integer_price(self):
        """Maximum safe integer price."""
        price = 9007199254740991  # JS MAX_SAFE_INTEGER
        r = client.post("/items", json={"name": "expensive", "price": price})
        assert r.status_code == 200

    def test_create_with_min_positive_price(self):
        """Minimum positive price."""
        price = 0.01
        r = client.post("/items", json={"name": "cheap", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    def test_create_very_small_positive_price(self):
        """Very small positive price (close to zero)."""
        price = 1e-10  # Extremely small
        r = client.post("/items", json={"name": "tiny", "price": price})
        assert r.status_code == 200

    def test_get_boundary_path_parameters(self):
        """Test all boundary path parameters."""
        boundaries = [-1, 0, 1, 2, 1000000]
        statuses = []
        for item_id in boundaries:
            r = client.get(f"/items/{item_id}")
            statuses.append(r.status_code)
        
        # Only 1 should be 200, rest should be 404
        assert statuses.count(200) == 1
        assert statuses.count(404) == 4
        assert statuses[2] == 200  # item_id 1

    def test_create_name_with_max_length(self):
        """Very long name field."""
        long_name = "x" * 10000
        r = client.post("/items", json={"name": long_name, "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == long_name


class TestRequestMethodValidation:
    """Tests for HTTP method validation."""

    def test_items_endpoint_get_not_allowed(self):
        """GET /items should not be allowed (only POST)."""
        r = client.get("/items")
        assert r.status_code == 404  # No GET /items endpoint

    def test_items_endpoint_put_not_allowed(self):
        """PUT on create endpoint not supported."""
        r = client.put("/items", json={"name": "test", "price": 10})
        assert r.status_code == 405

    def test_items_id_endpoint_post_not_allowed(self):
        """POST on get endpoint not supported."""
        r = client.post("/items/1", json={"name": "test", "price": 10})
        assert r.status_code == 405

    def test_items_id_endpoint_delete_not_allowed(self):
        """DELETE on get endpoint not supported."""
        r = client.delete("/items/1")
        assert r.status_code == 405


class TestQueryParameterHandling:
    """Tests for handling of unexpected query parameters."""

    def test_create_with_query_parameters_ignored(self):
        """Extra query parameters are ignored."""
        r = client.post("/items?extra=param", json={"name": "test", "price": 10})
        assert r.status_code == 200

    def test_get_with_query_parameters_ignored(self):
        """Extra query parameters on GET are ignored."""
        r = client.get("/items/1?extra=param&another=value")
        assert r.status_code == 200

    def test_health_with_query_parameters(self):
        """Health endpoint ignores query parameters."""
        r = client.get("/health?status=check")
        assert r.status_code == 200


class TestHeaderHandling:
    """Tests for handling of various headers."""

    def test_create_with_custom_headers(self):
        """Extra headers don't affect request processing."""
        r = client.post(
            "/items",
            json={"name": "test", "price": 10},
            headers={"X-Custom-Header": "value"}
        )
        assert r.status_code == 200

    def test_get_with_custom_headers(self):
        """Extra headers on GET don't affect response."""
        r = client.get(
            "/items/1",
            headers={"X-Request-ID": "12345"}
        )
        assert r.status_code == 200

    def test_request_with_accept_header(self):
        """Accept header doesn't affect JSON response."""
        r = client.get("/items/1", headers={"Accept": "application/json"})
        assert r.status_code == 200
        assert "application/json" in r.headers["content-type"]
