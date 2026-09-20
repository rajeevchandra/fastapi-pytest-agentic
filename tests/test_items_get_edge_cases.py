"""
Path parameter validation and integration edge case tests.
Tests boundary values, invalid parameters, and complex scenarios.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test path parameter validation for get_item endpoint."""

    @pytest.mark.parametrize("item_id", [1])
    def test_get_item_valid_id(self, item_id):
        """Test that valid item ID returns 200."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 200

    @pytest.mark.parametrize("item_id", [0])
    def test_get_item_zero_id_not_found(self, item_id):
        """Test that item_id=0 returns 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    @pytest.mark.parametrize("item_id", [-1, -100, -999999])
    def test_get_item_negative_id_not_found(self, item_id):
        """Test that negative item IDs return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    @pytest.mark.parametrize("item_id", [2, 3, 10, 100, 1000, 999999])
    def test_get_item_nonexistent_positive_ids(self, item_id):
        """Test that non-existent positive IDs return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    @pytest.mark.parametrize("item_id", [1])
    def test_get_item_boundary_valid(self, item_id):
        """Test lower boundary of valid IDs."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 200


class TestGetItemPathParameterEdgeCases:
    """Test edge cases in path parameter handling."""

    def test_get_item_very_large_id(self):
        """Test that very large item_id returns 404."""
        r = client.get(f"/items/{999999999}")
        assert r.status_code == 404

    def test_get_item_integer_boundaries(self):
        """Test integer boundary values."""
        # Max 32-bit int adjacent
        r = client.get(f"/items/2147483647")
        assert r.status_code == 404

    def test_get_item_id_one_returns_data(self):
        """Test that item_id 1 specifically returns data."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1

    def test_get_item_other_ids_all_not_found(self):
        """Test that all IDs except 1 return 404."""
        for item_id in [0, 2, 3, 10, 100]:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404


class TestCreateItemAndGetItem:
    """Test interaction between create and get endpoints."""

    def test_create_item_then_get_succeeds(self):
        """Test that created item can be retrieved."""
        # Create item
        r1 = client.post("/items", json={"name": "book", "price": 10.0})
        assert r1.status_code == 200
        created = r1.json()
        
        # Get item
        r2 = client.get(f"/items/{created['id']}")
        assert r2.status_code == 200
        # Note: get_item returns fixed data, not the created item
        assert r2.json()["id"] == 1

    def test_create_multiple_then_get(self):
        """Test multiple creates followed by get."""
        # Create multiple items
        created_ids = []
        for i in range(3):
            r = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            assert r.status_code == 200
            created_ids.append(r.json()["id"])
        
        # All should return id=1
        assert all(id == 1 for id in created_ids)
        
        # Get should return fixed data
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_get_item_not_found_remains_not_found(self):
        """Test that missing items stay missing after creates."""
        # Try to get non-existent item
        r1 = client.get("/items/999")
        assert r1.status_code == 404
        
        # Create an item
        r2 = client.post("/items", json={"name": "item", "price": 10.0})
        assert r2.status_code == 200
        
        # Non-existent item should still be not found
        r3 = client.get("/items/999")
        assert r3.status_code == 404


class TestEndpointIntegration:
    """Test integration scenarios across endpoints."""

    def test_health_always_ok(self):
        """Test that health endpoint always returns ok."""
        # Before any operations
        r1 = client.get("/health")
        assert r1.status_code == 200
        assert r1.json()["status"] == "ok"
        
        # After creating items
        client.post("/items", json={"name": "item", "price": 10.0})
        r2 = client.get("/health")
        assert r2.status_code == 200
        assert r2.json()["status"] == "ok"
        
        # After failed item creation
        client.post("/items", json={"name": "item", "price": 0})
        r3 = client.get("/health")
        assert r3.status_code == 200
        assert r3.json()["status"] == "ok"

    def test_failed_create_does_not_affect_get(self):
        """Test that failed create doesn't affect get behavior."""
        # Fail to create (invalid price)
        r1 = client.post("/items", json={"name": "item", "price": 0})
        assert r1.status_code == 400
        
        # Get should still work
        r2 = client.get("/items/1")
        assert r2.status_code == 200
        assert r2.json()["id"] == 1

    def test_sequential_creates_all_succeed(self):
        """Test that multiple creates all succeed."""
        statuses = []
        for i in range(5):
            r = client.post("/items", json={"name": f"item{i}", "price": 10.0})
            statuses.append(r.status_code)
        
        assert all(s == 200 for s in statuses)

    def test_get_after_failed_create_chain(self):
        """Test get after a chain of failed creates."""
        # Multiple failed creates
        for i in range(3):
            r = client.post("/items", json={"name": f"item{i}", "price": -i-1})
            assert r.status_code == 400
        
        # Get should still work
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["id"] == 1


class TestErrorScenarios:
    """Test various error scenarios."""

    def test_create_then_404_on_invalid_id(self):
        """Test that 404 still works after successful create."""
        # Create
        r1 = client.post("/items", json={"name": "item", "price": 10.0})
        assert r1.status_code == 200
        
        # Try invalid IDs
        r2 = client.get("/items/999")
        assert r2.status_code == 404

    def test_multiple_404s_consistent(self):
        """Test that 404s are consistent."""
        responses = [client.get(f"/items/{i}").status_code for i in [2, 3, 4]]
        assert all(s == 404 for s in responses)

    def test_multiple_validation_errors_consistent(self):
        """Test that validation errors are consistent."""
        responses = [
            client.post("/items", json={"name": "item", "price": 0}).status_code,
            client.post("/items", json={"name": "item", "price": -1}).status_code,
            client.post("/items", json={"name": "item", "price": -100}).status_code,
        ]
        assert all(s == 400 for s in responses)


class TestConcurrentScenarios:
    """Test handling of concurrent-like scenarios."""

    def test_alternating_success_and_failure(self):
        """Test alternating successful and failed operations."""
        results = []
        
        # Success
        r1 = client.post("/items", json={"name": "item1", "price": 10.0})
        results.append(r1.status_code)
        
        # Failure
        r2 = client.post("/items", json={"name": "item2", "price": 0})
        results.append(r2.status_code)
        
        # Success
        r3 = client.post("/items", json={"name": "item3", "price": 20.0})
        results.append(r3.status_code)
        
        # Failure
        r4 = client.post("/items", json={"name": "item4", "price": -5})
        results.append(r4.status_code)
        
        assert results == [200, 400, 200, 400]

    def test_bulk_valid_creates(self):
        """Test bulk valid item creation."""
        for i in range(10):
            r = client.post("/items", json={"name": f"bulk_item_{i}", "price": float(i+1)})
            assert r.status_code == 200
            assert r.json()["id"] == 1
            assert r.json()["name"] == f"bulk_item_{i}"

    def test_bulk_invalid_creates(self):
        """Test bulk invalid item creation."""
        for i in range(10):
            r = client.post("/items", json={"name": f"bulk_item_{i}", "price": -(i+1)})
            assert r.status_code == 400
            assert "price" in r.json()["detail"].lower()


class TestPathParameterSanity:
    """Sanity tests for path parameter handling."""

    def test_only_id_1_returns_success(self):
        """Verify that only item_id=1 returns 200."""
        # ID 1 should work
        r1 = client.get("/items/1")
        assert r1.status_code == 200
        
        # All other IDs should 404
        for item_id in range(0, 100, 10) + [999, 1000]:
            if item_id != 1:
                r = client.get(f"/items/{item_id}")
                assert r.status_code == 404, f"Expected 404 for item_id={item_id}, got {r.status_code}"

    def test_get_with_valid_id_always_succeeds(self):
        """Test that get with id=1 always succeeds regardless of prior operations."""
        for i in range(5):
            r = client.get("/items/1")
            assert r.status_code == 200
            assert r.json()["id"] == 1

    def test_data_stability(self):
        """Test that get_item returns stable data."""
        responses = [client.get("/items/1").json() for _ in range(5)]
        
        # All should be identical
        first = responses[0]
        for response in responses[1:]:
            assert response == first
            assert response["id"] == 1
            assert response["name"] == "sample"
            assert response["price"] == 10.0


class TestHTTPMethodValidation:
    """Test handling of different HTTP methods."""

    def test_items_post_works(self):
        """Test that POST to /items works."""
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200

    def test_items_get_path_works(self):
        """Test that GET to /items/{id} works."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_health_get_works(self):
        """Test that GET to /health works."""
        r = client.get("/health")
        assert r.status_code == 200


class TestEndpointIsolation:
    """Test that endpoints are properly isolated."""

    def test_create_item_does_not_affect_get_item(self):
        """Test that creating items doesn't change get_item behavior."""
        # Get before create
        r1 = client.get("/items/1")
        before = r1.json()
        
        # Create items
        for i in range(3):
            client.post("/items", json={"name": f"item{i}", "price": 10.0})
        
        # Get after creates
        r2 = client.get("/items/1")
        after = r2.json()
        
        # Should be identical
        assert before == after

    def test_failed_creates_do_not_affect_get_item(self):
        """Test that failed creates don't affect get_item."""
        # Get before failures
        r1 = client.get("/items/1")
        before = r1.json()
        
        # Multiple failed creates
        for i in range(5):
            client.post("/items", json={"name": f"item{i}", "price": -10})
        
        # Get after failures
        r2 = client.get("/items/1")
        after = r2.json()
        
        # Should be identical
        assert before == after

    def test_health_isolated_from_other_endpoints(self):
        """Test that health endpoint is not affected by other operations."""
        # Health before
        r1 = client.get("/health")
        before = r1.json()
        
        # Lots of operations on other endpoints
        for i in range(5):
            client.post("/items", json={"name": f"item{i}", "price": 10.0})
            client.get(f"/items/{i}")
        
        # Health after
        r2 = client.get("/health")
        after = r2.json()
        
        # Should still be ok
        assert before == after
        assert after["status"] == "ok"
