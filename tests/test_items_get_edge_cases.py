"""
Part 3: Edge Cases & Integration Testing - Boundary value testing for item_id,
interaction patterns between endpoints, stress testing with various combinations.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemIdBoundaryValues:
    """Test edge cases for item_id in get endpoint."""

    def test_get_item_with_valid_id(self):
        """Test get with valid id returns item."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_get_item_negative_id(self):
        """Test get with negative id returns 404."""
        r = client.get("/items/-1")
        assert r.status_code == 404

    def test_get_item_zero_id(self):
        """Test get with zero id returns 404."""
        r = client.get("/items/0")
        assert r.status_code == 404

    def test_get_item_large_id(self):
        """Test get with very large id returns 404."""
        r = client.get("/items/2147483647")
        assert r.status_code == 404

    def test_get_item_id_2(self):
        """Test get with id=2 returns 404."""
        r = client.get("/items/2")
        assert r.status_code == 404

    def test_get_item_id_100(self):
        """Test get with id=100 returns 404."""
        r = client.get("/items/100")
        assert r.status_code == 404

    @pytest.mark.parametrize("item_id", [2, 3, 4, 5, 100, 999, 10000])
    def test_get_nonexistent_items_all_404(self, item_id):
        """Test that all non-existent items return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    @pytest.mark.parametrize("item_id", [-5, -1, -100, -9999])
    def test_get_negative_ids_all_404(self, item_id):
        """Test that all negative ids return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404


class TestItemCreationSequences:
    """Test sequences and patterns of item creation."""

    def test_create_single_item(self):
        """Test creating a single item."""
        r = client.post("/items", json={"name": "single", "price": 10})
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_create_multiple_items_sequential(self):
        """Test creating multiple items in sequence."""
        r1 = client.post("/items", json={"name": "item1", "price": 10})
        r2 = client.post("/items", json={"name": "item2", "price": 20})
        r3 = client.post("/items", json={"name": "item3", "price": 30})
        
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r3.status_code == 200
        
        assert r1.json()["name"] == "item1"
        assert r2.json()["name"] == "item2"
        assert r3.json()["name"] == "item3"

    def test_create_items_different_prices(self):
        """Test creating items with different prices."""
        prices = [0.01, 1, 10, 100, 1000]
        responses = []
        
        for price in prices:
            r = client.post("/items", json={"name": f"item_{price}", "price": price})
            responses.append(r)
            assert r.status_code == 200
            assert r.json()["price"] == price
        
        # All should succeed
        assert all(r.status_code == 200 for r in responses)

    def test_create_then_get_single_item(self):
        """Test creating an item then retrieving it."""
        create_r = client.post("/items", json={"name": "test_item", "price": 25.50})
        assert create_r.status_code == 200
        
        created_id = create_r.json()["id"]
        get_r = client.get(f"/items/{created_id}")
        
        assert get_r.status_code == 200
        assert get_r.json()["id"] == created_id


class TestMixedOperationSequences:
    """Test sequences mixing different operations."""

    def test_create_then_get_then_create_again(self):
        """Test alternating between create and get operations."""
        # Create first item
        r1 = client.post("/items", json={"name": "first", "price": 10})
        assert r1.status_code == 200
        
        # Get it back
        r2 = client.get("/items/1")
        assert r2.status_code == 200
        
        # Create another
        r3 = client.post("/items", json={"name": "second", "price": 20})
        assert r3.status_code == 200
        
        # Try to get the first one again
        r4 = client.get("/items/1")
        assert r4.status_code == 200

    def test_create_invalid_then_valid(self):
        """Test creating invalid then valid items."""
        # Try with invalid price
        r1 = client.post("/items", json={"name": "invalid", "price": 0})
        assert r1.status_code == 400
        
        # Valid creation should still work
        r2 = client.post("/items", json={"name": "valid", "price": 10})
        assert r2.status_code == 200
        
        # Should be able to get the valid item
        r3 = client.get("/items/1")
        assert r3.status_code == 200

    def test_multiple_get_same_item(self):
        """Test getting the same item multiple times."""
        responses = []
        for _ in range(5):
            r = client.get("/items/1")
            responses.append(r)
            assert r.status_code == 200
        
        # All responses should be identical
        first = responses[0].json()
        for r in responses[1:]:
            assert r.json() == first

    def test_get_nonexistent_multiple_times(self):
        """Test getting non-existent item multiple times."""
        responses = []
        for _ in range(5):
            r = client.get("/items/999")
            responses.append(r)
            assert r.status_code == 404
        
        # All error responses should be identical
        first = responses[0].json()
        for r in responses[1:]:
            assert r.json() == first


class TestPriceValueEdgeCases:
    """Test edge cases and stress scenarios with different price values."""

    @pytest.mark.parametrize("price", [0.001, 0.01, 0.1, 1, 10, 100, 1000, 10000])
    def test_create_items_various_magnitudes(self, price):
        """Test creating items with prices of different magnitudes."""
        r = client.post("/items", json={"name": f"item_{price}", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    @pytest.mark.parametrize("price", [1.1, 1.01, 1.001, 1.0001])
    def test_create_items_decimal_precision(self, price):
        """Test price precision is preserved."""
        r = client.post("/items", json={"name": "precision_test", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    def test_create_item_minimum_valid_price(self):
        """Test creating item with very small valid price."""
        r = client.post("/items", json={"name": "minimum", "price": 1e-10})
        assert r.status_code == 200
        assert r.json()["price"] == 1e-10

    def test_create_item_maximum_typical_price(self):
        """Test creating item with very large price."""
        r = client.post("/items", json={"name": "expensive", "price": 1e15})
        assert r.status_code == 200
        assert r.json()["price"] == 1e15

    def test_create_item_just_above_zero(self):
        """Test creating item with price just above zero."""
        r = client.post("/items", json={"name": "almost_free", "price": 1e-100})
        assert r.status_code == 200

    def test_create_item_float_max_range(self):
        """Test with high float value."""
        high_price = 1.7976931348623157e+308  # Near float64 max
        r = client.post("/items", json={"name": "cosmic", "price": high_price})
        assert r.status_code == 200


class TestNameFieldEdgeCases:
    """Test edge cases and stress scenarios with name field."""

    def test_create_item_single_char_name(self):
        """Test creating item with single character name."""
        r = client.post("/items", json={"name": "a", "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == "a"

    def test_create_item_very_long_name(self):
        """Test creating item with extremely long name."""
        long_name = "x" * 10000
        r = client.post("/items", json={"name": long_name, "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == long_name

    def test_create_item_name_with_newlines(self):
        """Test creating item with newlines in name."""
        name_with_newlines = "line1\nline2\nline3"
        r = client.post("/items", json={"name": name_with_newlines, "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == name_with_newlines

    def test_create_item_name_with_tabs(self):
        """Test creating item with tabs in name."""
        name_with_tabs = "col1\tcol2\tcol3"
        r = client.post("/items", json={"name": name_with_tabs, "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == name_with_tabs

    def test_create_item_name_with_quotes(self):
        """Test creating item with quotes in name."""
        name_with_quotes = 'He said "hello"'
        r = client.post("/items", json={"name": name_with_quotes, "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == name_with_quotes

    def test_create_item_name_with_backslashes(self):
        """Test creating item with backslashes in name."""
        name_with_backslash = "path\\to\\file"
        r = client.post("/items", json={"name": name_with_backslash, "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == name_with_backslash

    def test_create_item_name_only_whitespace(self):
        """Test creating item with only whitespace in name."""
        r = client.post("/items", json={"name": "   ", "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == "   "

    def test_create_item_name_mixed_unicode(self):
        """Test creating item with mixed unicode scripts."""
        mixed_name = "Hello世界мир🌍"
        r = client.post("/items", json={"name": mixed_name, "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == mixed_name


class TestErrorBoundaryConditions:
    """Test error conditions at boundaries."""

    def test_price_exactly_zero_rejected(self):
        """Test that price of exactly 0 is rejected."""
        r = client.post("/items", json={"name": "test", "price": 0})
        assert r.status_code == 400

    def test_price_tiny_positive_accepted(self):
        """Test that tiny positive price is accepted."""
        r = client.post("/items", json={"name": "test", "price": 1e-50})
        assert r.status_code == 200

    def test_price_tiny_negative_rejected(self):
        """Test that tiny negative price is rejected."""
        r = client.post("/items", json={"name": "test", "price": -1e-50})
        assert r.status_code == 400

    def test_missing_name_rejected_with_422(self):
        """Test that missing name returns 422."""
        r = client.post("/items", json={"price": 10})
        assert r.status_code == 422

    def test_missing_price_rejected_with_422(self):
        """Test that missing price returns 422."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422

    def test_both_fields_missing_rejected(self):
        """Test that both fields missing returns 422."""
        r = client.post("/items", json={})
        assert r.status_code == 422


class TestOperationCombinations:
    """Test various combinations of operations."""

    def test_create_with_various_prices_then_get_first(self):
        """Test creating multiple items with different prices then get first."""
        for price in [1, 5, 10, 50, 100]:
            client.post("/items", json={"name": f"item_{price}", "price": price})
        
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_create_invalid_items_dont_affect_valid_gets(self):
        """Test that invalid creates don't interfere with valid gets."""
        # Create valid item
        r1 = client.post("/items", json={"name": "valid", "price": 10})
        assert r1.status_code == 200
        
        # Try multiple invalid creates
        for _ in range(3):
            r_invalid = client.post("/items", json={"name": "invalid", "price": 0})
            assert r_invalid.status_code == 400
        
        # Valid get should still work
        r2 = client.get("/items/1")
        assert r2.status_code == 200

    def test_interleaved_valid_and_invalid_creates(self):
        """Test interleaving valid and invalid creates."""
        results = []
        for i in range(5):
            if i % 2 == 0:
                r = client.post("/items", json={"name": f"valid_{i}", "price": 10})
                results.append((r.status_code, 200))
            else:
                r = client.post("/items", json={"name": f"invalid_{i}", "price": 0})
                results.append((r.status_code, 400))
        
        for actual, expected in results:
            assert actual == expected

    def test_health_check_unaffected_by_operations(self):
        """Test that health check is unaffected by other operations."""
        # Health before
        h1 = client.get("/health")
        assert h1.status_code == 200
        
        # Create items
        for i in range(3):
            client.post("/items", json={"name": f"item_{i}", "price": i * 10})
        
        # Health after should be same
        h2 = client.get("/health")
        assert h2.status_code == 200
        assert h1.json() == h2.json()


class TestResponseConsistencyUnderLoad:
    """Test response consistency when handling multiple operations."""

    def test_same_response_for_identical_requests(self):
        """Test that identical requests get identical responses."""
        responses = []
        for _ in range(5):
            r = client.post("/items", json={"name": "test", "price": 25})
            responses.append(r.json())
        
        # All should have same structure
        first = responses[0]
        for resp in responses[1:]:
            assert resp["id"] == first["id"]
            assert resp["name"] == first["name"]
            assert resp["price"] == first["price"]

    def test_get_request_consistency(self):
        """Test that multiple get requests return same response."""
        responses = []
        for _ in range(5):
            r = client.get("/items/1")
            responses.append(r.json())
        
        first = responses[0]
        for resp in responses[1:]:
            assert resp == first

    def test_error_responses_consistent(self):
        """Test that error responses are consistent."""
        responses = []
        for _ in range(5):
            r = client.post("/items", json={"name": "test", "price": -10})
            responses.append(r.json())
        
        first = responses[0]
        for resp in responses[1:]:
            assert resp == first


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    def test_typical_usage_flow(self):
        """Test a typical usage flow."""
        # Check health
        health = client.get("/health")
        assert health.status_code == 200
        
        # Create an item
        create = client.post("/items", json={"name": "book", "price": 15.99})
        assert create.status_code == 200
        
        # Get the item
        item_id = create.json()["id"]
        get = client.get(f"/items/{item_id}")
        assert get.status_code == 200
        assert get.json()["name"] == "book"
        assert get.json()["price"] == 15.99

    def test_multiple_items_different_operations(self):
        """Test operations with multiple items."""
        # Create several items
        created_ids = []
        for i in range(3):
            r = client.post("/items", json={"name": f"item_{i}", "price": (i + 1) * 10})
            if r.status_code == 200:
                created_ids.append(r.json()["id"])
        
        # Try to get each
        for item_id in created_ids:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 200
        
        # Try to get non-existent
        r = client.get("/items/999")
        assert r.status_code == 404

    def test_error_recovery_flow(self):
        """Test that system recovers from errors."""
        # Normal operation
        r1 = client.post("/items", json={"name": "valid1", "price": 10})
        assert r1.status_code == 200
        
        # Cause error
        r2 = client.post("/items", json={"name": "invalid", "price": -5})
        assert r2.status_code == 400
        
        # System should still work
        r3 = client.post("/items", json={"name": "valid2", "price": 20})
        assert r3.status_code == 200
        
        # Gets should work
        r4 = client.get("/items/1")
        assert r4.status_code == 200
