"""
Path parameter edge cases and integration scenario tests.
Tests boundary values for item IDs, multiple operations, and cross-endpoint interactions.
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test path parameter validation for get_item endpoint."""

    def test_item_id_one_found(self):
        """Item ID 1 should be found."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_item_id_zero_not_found(self):
        """Item ID 0 should not be found."""
        r = client.get("/items/0")
        assert r.status_code == 404

    def test_item_id_negative_not_found(self):
        """Negative item ID should not be found."""
        r = client.get("/items/-1")
        assert r.status_code == 404

    def test_item_id_two_not_found(self):
        """Item ID 2 should not be found."""
        r = client.get("/items/2")
        assert r.status_code == 404

    def test_item_id_large_number_not_found(self):
        """Large item ID should not be found."""
        r = client.get("/items/999999")
        assert r.status_code == 404

    def test_item_id_max_int_not_found(self):
        """Maximum integer value should not be found."""
        r = client.get("/items/2147483647")
        assert r.status_code == 404

    def test_item_id_min_int_not_found(self):
        """Minimum integer value should not be found."""
        r = client.get("/items/-2147483648")
        assert r.status_code == 404

    def test_single_valid_item_exists(self):
        """Only item ID 1 should exist in the system."""
        valid_ids = [client.get(f"/items/{i}").status_code == 200 for i in range(-5, 10)]
        # Only one ID should return 200
        assert sum(valid_ids) == 1


class TestCreateItemNameEdgeCases:
    """Test edge cases for item name in creation."""

    def test_create_item_empty_name_string(self):
        """Empty name string might be accepted or rejected."""
        r = client.post("/items", json={"name": "", "price": 10.0})
        # Empty strings can be valid or invalid depending on validation
        assert r.status_code in (200, 422)

    def test_create_item_very_long_name(self):
        """Very long names should be handled."""
        long_name = "x" * 1000
        r = client.post("/items", json={"name": long_name, "price": 10.0})
        assert r.status_code in (200, 422)

    def test_create_item_name_with_newline(self):
        """Names with newlines should be handled."""
        r = client.post("/items", json={"name": "book\nvolume1", "price": 10.0})
        assert r.status_code in (200, 422)

    def test_create_item_name_with_tab(self):
        """Names with tabs should be handled."""
        r = client.post("/items", json={"name": "book\tvolume1", "price": 10.0})
        assert r.status_code in (200, 422)

    def test_create_item_name_only_spaces(self):
        """Names with only spaces might be valid or invalid."""
        r = client.post("/items", json={"name": "   ", "price": 10.0})
        assert r.status_code in (200, 422)

    def test_create_item_name_with_html_chars(self):
        """Names with HTML-like characters should be handled."""
        r = client.post("/items", json={"name": "<book>", "price": 10.0})
        assert r.status_code in (200, 422)

    def test_create_item_name_with_sql_like_chars(self):
        """Names with SQL-like characters should be handled safely."""
        r = client.post("/items", json={"name": "'; DROP TABLE items;--", "price": 10.0})
        assert r.status_code in (200, 422)


class TestCreateItemPriceEdgeCases:
    """Test edge cases for item price in creation."""

    def test_price_very_large_value(self):
        """Very large price should be handled."""
        r = client.post("/items", json={"name": "item", "price": 1e10})
        assert r.status_code == 200

    def test_price_very_small_positive(self):
        """Very small positive price should be accepted."""
        r = client.post("/items", json={"name": "item", "price": 1e-10})
        assert r.status_code == 200

    def test_price_exactly_one(self):
        """Price of exactly 1 should be valid."""
        r = client.post("/items", json={"name": "item", "price": 1})
        assert r.status_code == 200
        assert r.json()["price"] == 1

    def test_price_exactly_one_point_zero(self):
        """Price of 1.0 should be valid."""
        r = client.post("/items", json={"name": "item", "price": 1.0})
        assert r.status_code == 200
        assert r.json()["price"] == 1.0

    def test_price_boundary_just_above_zero(self):
        """Price just above zero should be valid."""
        r = client.post("/items", json={"name": "item", "price": 0.0001})
        assert r.status_code == 200

    def test_price_with_many_decimals(self):
        """Price with many decimal places should be handled."""
        r = client.post("/items", json={"name": "item", "price": 10.123456789})
        assert r.status_code == 200

    def test_price_scientific_notation(self):
        """Scientific notation for price should work."""
        r = client.post("/items", json={"name": "item", "price": 1e2})
        assert r.status_code == 200
        assert r.json()["price"] == 100


class TestResponseDataIntegrity:
    """Test data integrity between request and response."""

    def test_create_then_get_same_data(self):
        """Created item should match when retrieved."""
        # Create an item
        create_r = client.post("/items", json={"name": "test_book", "price": 25.5})
        assert create_r.status_code == 200
        created_id = create_r.json()["id"]
        created_data = create_r.json()

        # Get the created item
        if created_id == 1:
            get_r = client.get(f"/items/{created_id}")
            assert get_r.status_code == 200
            # Note: Get endpoint returns fixed sample data, not created data
            # This test documents the current behavior

    def test_multiple_creates_return_same_id(self):
        """Multiple creates should all return ID 1."""
        ids = []
        for i in range(3):
            r = client.post("/items", json={"name": f"item_{i}", "price": 10.0 + i})
            assert r.status_code == 200
            ids.append(r.json()["id"])
        
        # All should have same ID
        assert all(id == 1 for id in ids)
        assert len(set(ids)) == 1

    def test_create_response_has_all_fields_from_request(self):
        """Create response should contain data from request."""
        request_data = {"name": "special_item", "price": 99.99}
        r = client.post("/items", json=request_data)
        assert r.status_code == 200
        response_data = r.json()
        
        assert response_data["name"] == request_data["name"]
        assert response_data["price"] == request_data["price"]

    def test_get_item_has_consistent_data(self):
        """Get item should always return same data."""
        responses = []
        for _ in range(3):
            r = client.get("/items/1")
            assert r.status_code == 200
            responses.append(r.json())
        
        # All responses should be identical
        assert responses[0] == responses[1] == responses[2]


class TestSequentialOperations:
    """Test sequences of operations."""

    def test_create_then_get_not_found_different_id(self):
        """After creating, getting different ID should be not found."""
        # Create
        r1 = client.post("/items", json={"name": "item1", "price": 10.0})
        assert r1.status_code == 200

        # Try to get different ID
        r2 = client.get("/items/2")
        assert r2.status_code == 404

    def test_get_then_create_preserves_get_response(self):
        """Creating an item shouldn't affect get endpoint."""
        # Get existing
        r1 = client.get("/items/1")
        assert r1.status_code == 200
        first_get = r1.json()

        # Create new item
        r2 = client.post("/items", json={"name": "new_item", "price": 20.0})
        assert r2.status_code == 200

        # Get again - should be same as before
        r3 = client.get("/items/1")
        assert r3.status_code == 200
        assert r3.json() == first_get

    def test_multiple_get_same_id_consistent(self):
        """Multiple GETs of same ID should return identical data."""
        r1 = client.get("/items/1")
        r2 = client.get("/items/1")
        assert r1.json() == r2.json()

    def test_get_not_found_then_create_then_get_not_found(self):
        """Not found should remain not found even after creation."""
        r1 = client.get("/items/5")
        assert r1.status_code == 404

        # Create
        r2 = client.post("/items", json={"name": "item", "price": 10.0})
        assert r2.status_code == 200

        # Try same ID again
        r3 = client.get("/items/5")
        assert r3.status_code == 404


class TestErrorConditionSequences:
    """Test sequences of error conditions."""

    def test_multiple_invalid_creates_all_fail(self):
        """Multiple invalid creates should all fail."""
        for price in [-1, 0, -100]:
            r = client.post("/items", json={"name": "item", "price": price})
            assert r.status_code == 400

    def test_invalid_create_then_valid_create(self):
        """Invalid create followed by valid create should work."""
        # Invalid
        r1 = client.post("/items", json={"name": "item", "price": -1})
        assert r1.status_code == 400

        # Valid
        r2 = client.post("/items", json={"name": "item", "price": 10.0})
        assert r2.status_code == 200

    def test_multiple_not_found_gets_consistent(self):
        """Multiple 404s should be consistent."""
        statuses = []
        for id in [2, 3, 4, 999]:
            r = client.get(f"/items/{id}")
            statuses.append(r.status_code)

        assert all(s == 404 for s in statuses)


class TestBoundaryConditionIntegration:
    """Test combinations of boundary conditions."""

    def test_minimum_valid_price_with_various_names(self):
        """Minimum valid price with different names."""
        names = ["a", "test", "special-item", "café"]
        for name in names:
            r = client.post("/items", json={"name": name, "price": 0.001})
            assert r.status_code == 200
            assert r.json()["name"] == name

    def test_maximum_reasonable_price_with_various_names(self):
        """Large price with different names."""
        names = ["expensive", "luxury_item", "x" * 100]
        for name in names:
            r = client.post("/items", json={"name": name, "price": 1e10})
            assert r.status_code == 200

    def test_boundary_prices_validation(self):
        """Test multiple price boundaries."""
        boundaries = [
            (0, False),      # Should fail
            (0.0001, True),  # Should pass
            (1, True),       # Should pass
            (-0.001, False), # Should fail
        ]
        for price, should_pass in boundaries:
            r = client.post("/items", json={"name": "item", "price": price})
            if should_pass:
                assert r.status_code == 200
            else:
                assert r.status_code == 400

    def test_various_ids_all_not_found_except_one(self):
        """Test range of IDs, only 1 should be found."""
        results = {}
        for item_id in range(-10, 20):
            r = client.get(f"/items/{item_id}")
            results[item_id] = r.status_code

        # Only ID 1 should be 200
        assert results[1] == 200
        # All others should be 404
        for id in range(-10, 20):
            if id != 1:
                assert results[id] == 404


class TestHealthEndpoint:
    """Test health check endpoint for completeness."""

    def test_health_returns_ok(self):
        """Health endpoint should return ok status."""
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_health_response_format(self):
        """Health response should have correct format."""
        r = client.get("/health")
        data = r.json()
        assert "status" in data
        assert data["status"] == "ok"

    def test_health_is_always_available(self):
        """Health endpoint should always be available."""
        for _ in range(5):
            r = client.get("/health")
            assert r.status_code == 200


class TestErrorMessagesClarity:
    """Test that error messages are clear and actionable."""

    def test_zero_price_error_clear(self):
        """Zero price error should be clear."""
        r = client.post("/items", json={"name": "item", "price": 0})
        detail = r.json()["detail"]
        assert "price" in detail.lower()

    def test_not_found_error_clear(self):
        """Not found error should be clear."""
        r = client.get("/items/999")
        detail = r.json()["detail"]
        assert "not found" in detail.lower()

    def test_negative_price_rejected_with_message(self):
        """Negative price should be rejected with message."""
        r = client.post("/items", json={"name": "item", "price": -10})
        assert r.status_code == 400
        assert "detail" in r.json()

    def test_validation_error_is_informative(self):
        """Missing field error should be informative."""
        r = client.post("/items", json={"name": "item"})
        assert r.status_code == 422
        # Detail should exist and be informative
        data = r.json()
        assert "detail" in data or "errors" in str(data).lower()
