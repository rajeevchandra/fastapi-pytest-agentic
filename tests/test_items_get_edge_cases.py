"""
Edge cases and integration testing for FastAPI items endpoint.

Tests focus on boundary conditions, path parameter edge cases,
multiple sequential operations, and integration scenarios.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterBoundaries:
    """Test boundary conditions for item_id path parameter."""

    @pytest.mark.parametrize("item_id", [1])
    def test_get_item_minimum_valid_id(self, item_id):
        """Test minimum valid ID (1) returns success."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 200

    @pytest.mark.parametrize("item_id", [0, -1, -2, -100, -999999])
    def test_get_item_zero_and_negative_ids(self, item_id):
        """Test zero and negative IDs return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    @pytest.mark.parametrize("item_id", [2, 3, 10, 100, 999, 999999])
    def test_get_item_positive_non_matching_ids(self, item_id):
        """Test positive IDs that don't match item_id=1 return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    def test_get_item_id_one_boundary(self):
        """Test item_id=1 is the only valid ID."""
        # ID 1 should work
        r1 = client.get("/items/1")
        assert r1.status_code == 200
        
        # ID 0 should not work
        r0 = client.get("/items/0")
        assert r0.status_code == 404
        
        # ID 2 should not work
        r2 = client.get("/items/2")
        assert r2.status_code == 404

    def test_get_item_large_positive_id(self):
        """Test very large positive ID returns 404."""
        r = client.get(f"/items/{999999999}")
        assert r.status_code == 404

    def test_get_item_max_int_id(self):
        """Test maximum integer ID returns 404."""
        # Most frameworks can handle large ints in paths
        r = client.get(f"/items/{2147483647}")
        assert r.status_code == 404


class TestCreateItemPriceEdgeCases:
    """Test edge cases in price validation."""

    def test_create_item_price_just_above_zero(self):
        """Test price at boundary (0.00001)."""
        r = client.post("/items", json={"name": "test", "price": 0.00001})
        assert r.status_code == 200

    def test_create_item_price_just_below_zero(self):
        """Test price just below zero boundary (-0.00001)."""
        r = client.post("/items", json={"name": "test", "price": -0.00001})
        assert r.status_code == 400

    def test_create_item_price_zero_point_zero_zero_zero_one(self):
        """Test very small positive price (0.0001)."""
        r = client.post("/items", json={"name": "test", "price": 0.0001})
        assert r.status_code == 200

    def test_create_item_price_exact_zero(self):
        """Test exact zero value."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400

    def test_create_item_price_negative_zero(self):
        """Test negative zero (-0.0)."""
        r = client.post("/items", json={"name": "test", "price": -0.0})
        assert r.status_code == 400

    def test_create_item_price_very_small_valid(self):
        """Test very small valid price."""
        r = client.post("/items", json={"name": "test", "price": 1e-10})
        assert r.status_code == 200

    def test_create_item_price_very_large_valid(self):
        """Test very large valid price."""
        r = client.post("/items", json={"name": "test", "price": 1e10})
        assert r.status_code == 200


class TestCreateItemNameEdgeCases:
    """Test edge cases in name validation."""

    def test_create_item_name_single_character(self):
        """Test single character name."""
        r = client.post("/items", json={"name": "a", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "a"

    def test_create_item_name_single_unicode_character(self):
        """Test single unicode character."""
        r = client.post("/items", json={"name": "あ", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "あ"

    def test_create_item_name_spaces_only(self):
        """Test name that is only spaces."""
        r = client.post("/items", json={"name": "     ", "price": 10.0})
        assert r.status_code == 200

    def test_create_item_name_leading_trailing_spaces(self):
        """Test name with leading and trailing spaces."""
        r = client.post("/items", json={"name": "  test  ", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "  test  "  # Spaces should be preserved

    def test_create_item_name_multiple_spaces_between_words(self):
        """Test name with multiple spaces between words."""
        r = client.post("/items", json={"name": "test    item", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "test    item"

    def test_create_item_name_all_digits(self):
        """Test name that is all digits."""
        r = client.post("/items", json={"name": "123456789", "price": 10.0})
        assert r.status_code == 200

    def test_create_item_name_mixed_content(self):
        """Test name with mixed letters, numbers, special chars."""
        r = client.post("/items", json={"name": "Item-v2.0_Pro!", "price": 10.0})
        assert r.status_code == 200


class TestMultipleConsecutiveOperations:
    """Test multiple consecutive API operations."""

    def test_create_and_get_sequence(self):
        """Test creating item and then retrieving it."""
        # Create an item
        create_r = client.post("/items", json={"name": "sequence_test", "price": 25.0})
        assert create_r.status_code == 200
        created = create_r.json()
        
        # Get the item
        get_r = client.get(f"/items/{created['id']}")
        assert get_r.status_code == 200
        retrieved = get_r.json()
        
        # ID should be the same
        assert retrieved["id"] == created["id"]

    def test_multiple_get_requests_consistency(self):
        """Test multiple get requests return consistent results."""
        results = []
        for _ in range(10):
            r = client.get("/items/1")
            assert r.status_code == 200
            results.append(r.json())
        
        # All results should be identical
        for result in results[1:]:
            assert result == results[0]

    def test_multiple_create_requests_same_response(self):
        """Test multiple create requests return same response."""
        responses = []
        for i in range(3):
            r = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            assert r.status_code == 200
            responses.append(r.json())
        
        # All should have id=1
        for response in responses:
            assert response["id"] == 1

    def test_get_nonexistent_then_create_then_get_valid(self):
        """Test sequence of operations with 404 and successful gets."""
        # Try to get non-existent item
        r1 = client.get("/items/999")
        assert r1.status_code == 404
        
        # Create an item
        r2 = client.post("/items", json={"name": "test", "price": 10.0})
        assert r2.status_code == 200
        
        # Get valid item
        r3 = client.get("/items/1")
        assert r3.status_code == 200


class TestErrorRecovery:
    """Test API behavior after error conditions."""

    def test_create_invalid_then_valid_request(self):
        """Test creating with invalid price then valid price."""
        # Invalid request
        r1 = client.post("/items", json={"name": "test", "price": -5})
        assert r1.status_code == 400
        
        # Valid request should still work
        r2 = client.post("/items", json={"name": "test", "price": 10.0})
        assert r2.status_code == 200

    def test_validation_error_then_valid_request(self):
        """Test validation error followed by valid request."""
        # Missing fields
        r1 = client.post("/items", json={"price": 10.0})
        assert r1.status_code == 422
        
        # Valid request should still work
        r2 = client.post("/items", json={"name": "test", "price": 10.0})
        assert r2.status_code == 200

    def test_get_not_found_then_valid_request(self):
        """Test getting non-existent item then valid get."""
        # Invalid item
        r1 = client.get("/items/999")
        assert r1.status_code == 404
        
        # Valid request should still work
        r2 = client.get("/items/1")
        assert r2.status_code == 200

    def test_multiple_errors_then_success(self):
        """Test multiple errors followed by successful request."""
        # Multiple error attempts
        errors = [
            client.post("/items", json={"price": 10.0}),      # Missing name
            client.post("/items", json={"name": "test"}),      # Missing price
            client.post("/items", json={"name": "test", "price": 0}),  # Invalid price
            client.get("/items/999"),                           # Not found
        ]
        
        for r in errors:
            assert r.status_code >= 400
        
        # Success should still work
        r_success = client.post("/items", json={"name": "test", "price": 10.0})
        assert r_success.status_code == 200


class TestAPIHealthAndStability:
    """Test API health and overall stability."""

    def test_health_endpoint_always_available(self):
        """Test health endpoint is always available."""
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}

    def test_health_endpoint_multiple_calls(self):
        """Test health endpoint works repeatedly."""
        for _ in range(10):
            r = client.get("/health")
            assert r.status_code == 200

    def test_create_item_idempotent_request_values(self):
        """Test creating same item multiple times."""
        payload = {"name": "stable", "price": 15.0}
        
        responses = []
        for _ in range(5):
            r = client.post("/items", json=payload)
            assert r.status_code == 200
            responses.append(r.json())
        
        # All responses should have the same structure
        for response in responses:
            assert response["name"] == payload["name"]
            assert response["price"] == payload["price"]
            assert response["id"] == 1

    def test_api_response_speed_validation(self):
        """Test that API responses are returned quickly."""
        import time
        
        start = time.time()
        r = client.post("/items", json={"name": "speed_test", "price": 10.0})
        elapsed = time.time() - start
        
        assert r.status_code == 200
        # Should complete in reasonable time (less than 1 second for test client)
        assert elapsed < 1.0


class TestDataTypePreservation:
    """Test that data types are preserved in responses."""

    def test_price_type_preserved_in_response(self):
        """Test that float prices are preserved as float."""
        test_prices = [0.01, 1.5, 100.0, 999.99]
        
        for price in test_prices:
            r = client.post("/items", json={"name": "test", "price": price})
            response_price = r.json()["price"]
            
            # Should be float type
            assert isinstance(response_price, float)
            # Should equal input (accounting for floating point precision)
            assert abs(response_price - price) < 1e-9

    def test_name_type_preserved_in_response(self):
        """Test that string names are preserved as string."""
        test_names = ["simple", "with spaces", "123", "special!@#"]
        
        for name in test_names:
            r = client.post("/items", json={"name": name, "price": 10.0})
            response_name = r.json()["name"]
            
            # Should be string type
            assert isinstance(response_name, str)
            # Should equal input exactly
            assert response_name == name

    def test_id_type_integer_in_response(self):
        """Test that ID is returned as integer."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        response_id = r.json()["id"]
        
        assert isinstance(response_id, int)
        assert response_id == 1

    def test_get_item_response_types(self):
        """Test get_item response preserves correct types."""
        r = client.get("/items/1")
        data = r.json()
        
        assert isinstance(data["id"], int)
        assert isinstance(data["name"], str)
        assert isinstance(data["price"], float)


class TestRequestPayloadVariations:
    """Test various request payload scenarios."""

    def test_create_item_with_whitespace_around_values(self):
        """Test that JSON parsing handles whitespace correctly."""
        # Note: JSON whitespace shouldn't matter, but testing edge case
        r = client.post("/items", json={"name": " test ", "price": 10.0})
        assert r.status_code == 200

    def test_create_item_payload_ordering(self):
        """Test that field order in payload doesn't matter."""
        r1 = client.post("/items", json={"name": "test", "price": 10.0})
        r2 = client.post("/items", json={"price": 10.0, "name": "test"})
        
        assert r1.status_code == 200
        assert r2.status_code == 200
        # Both should produce same result
        assert r1.json()["id"] == r2.json()["id"]

    def test_create_item_with_numeric_string_price(self):
        """Test price passed as numeric string (Pydantic type coercion)."""
        r = client.post("/items", json={"name": "test", "price": "10.5"})
        # Pydantic will attempt to coerce
        assert r.status_code in [200, 422]

    def test_create_item_with_numeric_name(self):
        """Test name passed as numeric type (Pydantic type coercion)."""
        r = client.post("/items", json={"name": 123, "price": 10.0})
        # Pydantic will attempt to coerce
        assert r.status_code in [200, 422]


class TestResponseDataIntegrity:
    """Test data integrity in responses."""

    def test_response_no_data_leakage(self):
        """Test response doesn't contain unexpected fields."""
        r = client.post("/items", json={"name": "test", "price": 10.0, "secret": "should_not_appear"})
        data = r.json()
        
        # Should not contain extra fields
        assert "secret" not in data
        assert set(data.keys()) == {"id", "name", "price"}

    def test_create_item_response_isolation(self):
        """Test that responses don't leak data between requests."""
        r1 = client.post("/items", json={"name": "item1", "price": 10.0})
        r2 = client.post("/items", json={"name": "item2", "price": 20.0})
        
        # Both should have id=1 but different names
        data1 = r1.json()
        data2 = r2.json()
        
        assert data1["id"] == data2["id"] == 1
        # Names should be what we requested (though implementation always returns 1)
        assert data1["name"] == "item1"
        assert data2["name"] == "item2"

    def test_get_item_not_affected_by_create_requests(self):
        """Test that create requests don't affect get_item response."""
        # Get initial state
        r1 = client.get("/items/1")
        initial = r1.json()
        
        # Create multiple items
        for i in range(5):
            client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
        
        # Get item again
        r2 = client.get("/items/1")
        after = r2.json()
        
        # Should be unchanged
        assert initial == after


class TestEdgeCaseIntegration:
    """Test integration of multiple edge cases."""

    def test_boundary_price_with_various_names(self):
        """Test boundary price with different name variations."""
        test_cases = [
            (0.01, "minimal_price"),       # Minimum valid price
            (0.01, ""),                     # Min price, empty name
            (0.01, "a" * 1000),            # Min price, very long name
            (1e10, "max_price_item"),       # Max price
        ]
        
        for price, name in test_cases:
            r = client.post("/items", json={"name": name, "price": price})
            assert r.status_code == 200
            assert r.json()["price"] == price

    def test_various_get_failures_sequence(self):
        """Test sequence of various get_item failures."""
        failing_ids = [-1, 0, 2, 999, 1000000]
        
        for item_id in failing_ids:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404
            assert "not found" in r.json()["detail"].lower()

    def test_create_failure_reasons_isolation(self):
        """Test that different failure reasons don't interfere."""
        test_cases = [
            {"name": "test"},                   # Missing price
            {"price": 10.0},                    # Missing name  
            {"name": "test", "price": 0},       # Invalid price
            {"name": "test", "price": -1},      # Invalid price
        ]
        
        for payload in test_cases:
            r = client.post("/items", json=payload)
            assert r.status_code >= 400
        
        # Now success should still work
        r = client.post("/items", json={"name": "valid", "price": 10.0})
        assert r.status_code == 200
