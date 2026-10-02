"""
Path parameter edge cases and integration testing.

Tests cover:
- Item ID boundary values (negative, zero, very large)
- Multiple item operations
- Integration scenarios
- Path parameter parsing edge cases
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterBoundaries:
    """Test path parameter parsing for get_item."""

    @pytest.mark.parametrize("item_id", [-1, -100, -2**31])
    def test_negative_item_ids(self, item_id):
        """Negative item IDs should return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    def test_zero_item_id(self):
        """Zero item ID should return 404."""
        r = client.get("/items/0")
        assert r.status_code == 404

    @pytest.mark.parametrize("item_id", [2, 3, 10, 100, 1000, 10000])
    def test_non_existing_positive_ids(self, item_id):
        """Non-existing positive IDs should return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    def test_maximum_int_value(self):
        """Very large integer IDs should return 404."""
        r = client.get(f"/items/{2**31 - 1}")
        assert r.status_code == 404

    def test_string_item_id_invalid(self):
        """String item ID should cause validation error."""
        r = client.get("/items/not_an_int")
        assert r.status_code == 422

    def test_float_item_id_invalid(self):
        """Float item ID should cause validation error."""
        r = client.get("/items/1.5")
        assert r.status_code == 422

    def test_special_characters_in_path(self):
        """Special characters in path should cause validation error."""
        r = client.get("/items/1@2")
        assert r.status_code == 422


class TestItemIDConsistency:
    """Test that item ID is handled consistently."""

    def test_item_id_one_always_found(self):
        """Item ID 1 should always be found."""
        for _ in range(5):
            r = client.get("/items/1")
            assert r.status_code == 200
            assert r.json()["id"] == 1

    def test_other_ids_always_not_found(self):
        """Non-1 IDs should always not be found."""
        for item_id in [2, 3, 4, 5]:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404

    def test_item_id_returned_matches_requested(self):
        """Item 1 should have matching ID."""
        r = client.get("/items/1")
        assert r.json()["id"] == 1


class TestMultipleItemOperations:
    """Test creating and retrieving multiple items."""

    def test_create_multiple_items_successively(self):
        """Multiple create operations should succeed."""
        for i in range(3):
            r = client.post("/items", json={"name": f"item_{i}", "price": 10.0 + i})
            assert r.status_code == 200
            assert r.json()["id"] == 1

    def test_create_and_get_sequence(self):
        """Create and immediately get should both work."""
        # Create
        r_create = client.post("/items", json={"name": "test", "price": 25.0})
        assert r_create.status_code == 200
        
        # Get the created item
        r_get = client.get("/items/1")
        assert r_get.status_code == 200
        assert r_get.json()["name"] == "sample"  # Note: API returns hardcoded value

    def test_create_with_various_prices(self):
        """Creating items with different prices should work."""
        prices = [0.01, 1.0, 100.5, 999.99]
        for price in prices:
            r = client.post("/items", json={"name": "item", "price": price})
            assert r.status_code == 200
            assert r.json()["price"] == price

    def test_get_after_multiple_creates(self):
        """Get should work regardless of prior create calls."""
        # Create several items
        for i in range(5):
            r = client.post("/items", json={"name": f"item_{i}", "price": 10.0})
            assert r.status_code == 200
        
        # Get item 1 should still work
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["id"] == 1


class TestCreateItemIntegrationScenarios:
    """Test realistic create_item scenarios."""

    def test_create_minimal_valid_item(self):
        """Create with minimal valid data."""
        r = client.post("/items", json={"name": "x", "price": 0.01})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "x"
        assert data["price"] == 0.01

    def test_create_with_exact_boundary_price(self):
        """Create with price exactly at boundary."""
        r = client.post("/items", json={"name": "boundary", "price": 0.0000001})
        assert r.status_code == 200
        assert r.json()["price"] == 0.0000001

    def test_create_with_extremely_long_name(self):
        """Create item with very long name."""
        long_name = "a" * 10000
        r = client.post("/items", json={"name": long_name, "price": 1.0})
        assert r.status_code == 200
        assert r.json()["name"] == long_name

    def test_create_item_with_newlines_in_name(self):
        """Create item with newlines in name."""
        r = client.post("/items", json={"name": "line1\nline2", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "line1\nline2"

    def test_create_item_with_quotes_in_name(self):
        """Create item with quotes in name."""
        r = client.post("/items", json={"name": 'item "special"', "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == 'item "special"'


class TestGetItemIntegrationScenarios:
    """Test realistic get_item scenarios."""

    def test_rapid_sequential_gets(self):
        """Multiple rapid get requests should work."""
        for _ in range(10):
            r = client.get("/items/1")
            assert r.status_code == 200

    def test_interleaved_operations(self):
        """Interleave create and get operations."""
        for i in range(3):
            # Get
            r_get = client.get("/items/1")
            assert r_get.status_code == 200
            
            # Create
            r_create = client.post("/items", json={"name": f"item_{i}", "price": 10.0})
            assert r_create.status_code == 200

    def test_get_after_failed_create(self):
        """Get should work after failed create."""
        # Failed create
        r_fail = client.post("/items", json={"name": "test", "price": -1})
        assert r_fail.status_code == 400
        
        # Successful get
        r_get = client.get("/items/1")
        assert r_get.status_code == 200

    def test_nonexistent_id_consistency(self):
        """Nonexistent ID behavior should be consistent."""
        results = [client.get(f"/items/{i}") for i in [2, 2, 2]]
        assert all(r.status_code == 404 for r in results)
        assert all(r.json()["detail"] == "not found" for r in results)


class TestErrorRecovery:
    """Test that system recovers from errors."""

    def test_operation_after_validation_error(self):
        """Valid operation after validation error."""
        # Validation error
        r1 = client.post("/items", json={"name": "test"})
        assert r1.status_code == 422
        
        # Valid operation after error
        r2 = client.post("/items", json={"name": "test", "price": 10.0})
        assert r2.status_code == 200

    def test_operation_after_business_logic_error(self):
        """Valid operation after business logic error."""
        # Business logic error
        r1 = client.post("/items", json={"name": "test", "price": 0})
        assert r1.status_code == 400
        
        # Valid operation after error
        r2 = client.post("/items", json={"name": "test", "price": 10.0})
        assert r2.status_code == 200

    def test_operation_after_not_found(self):
        """Valid operation after not found."""
        # Not found
        r1 = client.get("/items/999")
        assert r1.status_code == 404
        
        # Valid operation after not found
        r2 = client.get("/items/1")
        assert r2.status_code == 200


class TestConcurrentPathParameters:
    """Test handling of various path parameter formats."""

    @pytest.mark.parametrize("invalid_path", [
        "/items/",  # Missing ID
        "/items//1",  # Double slash
    ])
    def test_malformed_paths(self, invalid_path):
        """Malformed paths should return appropriate errors."""
        r = client.get(invalid_path)
        # Can be 404 or 422 depending on path
        assert r.status_code in [404, 405, 422, 301]

    def test_path_with_query_params(self):
        """Path with query params should work."""
        r = client.get("/items/1?extra=param")
        assert r.status_code == 200

    def test_path_case_sensitivity(self):
        """Paths should be case sensitive."""
        r = client.get("/Items/1")
        assert r.status_code == 404


class TestEdgeCaseSequences:
    """Test edge cases and corner scenarios."""

    def test_boundary_prices_in_sequence(self):
        """Boundary prices in a sequence."""
        boundaries = [0.01, 0.001, 0.0001, 1, 10, 100, 1e6]
        for price in boundaries:
            r = client.post("/items", json={"name": "test", "price": price})
            assert r.status_code == 200
            assert r.json()["price"] == price

    def test_alternating_success_and_failure(self):
        """Alternating success and failure operations."""
        for i in range(5):
            # Success
            r_success = client.post("/items", json={"name": f"item_{i}", "price": 10.0})
            assert r_success.status_code == 200
            
            # Failure
            r_failure = client.post("/items", json={"name": "bad", "price": -1})
            assert r_failure.status_code == 400

    def test_different_error_types_sequence(self):
        """Sequence of different error types."""
        errors = [
            ({"price": 10.0}, 422),  # Missing name
            ({"name": "test", "price": 0}, 400),  # Invalid price
            ({"name": "test"}, 422),  # Missing price
            ({"name": "test", "price": "string"}, 422),  # Wrong type
        ]
        for data, expected_code in errors:
            r = client.post("/items", json=data)
            assert r.status_code == expected_code

    def test_successful_operations_sequence(self):
        """Sequence of all successful operations."""
        # Multiple creates
        for i in range(5):
            r = client.post("/items", json={"name": f"item_{i}", "price": 10.0 + i})
            assert r.status_code == 200
        
        # Multiple gets
        for _ in range(5):
            r = client.get("/items/1")
            assert r.status_code == 200
        
        # Health check
        r = client.get("/health")
        assert r.status_code == 200


class TestResponseConsistencyAcrossPatterns:
    """Test response consistency across different access patterns."""

    def test_get_same_item_different_times(self):
        """Getting same item at different times returns consistent data."""
        r1 = client.get("/items/1")
        # Perform some other operations
        for i in range(3):
            client.post("/items", json={"name": f"item_{i}", "price": 10.0})
        r2 = client.get("/items/1")
        
        # Response structure should be the same
        assert r1.json() == r2.json()

    def test_error_responses_across_patterns(self):
        """Error responses consistent across patterns."""
        # Get nonexistent
        r1 = client.get("/items/999")
        
        # Another get nonexistent
        r2 = client.get("/items/888")
        
        # Both should be 404 with same structure
        assert r1.status_code == r2.status_code == 404
        assert list(r1.json().keys()) == list(r2.json().keys())
