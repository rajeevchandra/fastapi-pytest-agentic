"""Path parameter and integration edge case tests.

Comprehensive tests for get_item path parameters, boundary values, and integration scenarios.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test path parameter validation for get_item."""

    @pytest.mark.parametrize("item_id", [
        1,
        0,
        -1,
        -100,
        2,
        100,
        999999,
        2147483647,  # Max 32-bit int
    ])
    def test_get_item_various_ids(self, item_id):
        """Test get_item with various item_id values."""
        r = client.get(f"/items/{item_id}")
        # Only ID 1 should return 200, all others 404
        if item_id == 1:
            assert r.status_code == 200
            assert r.json()["id"] == 1
        else:
            assert r.status_code == 404

    def test_get_item_id_zero(self):
        """Test get_item with ID 0."""
        r = client.get("/items/0")
        assert r.status_code == 404

    def test_get_item_negative_id(self):
        """Test get_item with negative ID."""
        r = client.get("/items/-1")
        assert r.status_code == 404

    def test_get_item_large_id(self):
        """Test get_item with very large ID."""
        r = client.get("/items/999999999999")
        assert r.status_code == 404

    def test_get_item_id_boundary_one(self):
        """Test that exactly ID 1 is found."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1

    def test_get_item_id_just_above_one(self):
        """Test that ID 2 (just above 1) is not found."""
        r = client.get("/items/2")
        assert r.status_code == 404

    def test_get_item_id_just_below_one(self):
        """Test that ID 0 (just below 1) is not found."""
        r = client.get("/items/0")
        assert r.status_code == 404


class TestGetItemResponseConsistency:
    """Test that get_item returns consistent data."""

    def test_get_item_same_data_multiple_calls(self):
        """Test that multiple calls return identical data."""
        r1 = client.get("/items/1")
        r2 = client.get("/items/1")
        r3 = client.get("/items/1")
        
        assert r1.json() == r2.json() == r3.json()

    def test_get_item_fixed_values(self):
        """Test that get_item returns fixed hardcoded values."""
        r = client.get("/items/1")
        data = r.json()
        
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0

    def test_get_item_field_immutability(self):
        """Test that response fields don't change between calls."""
        responses = [client.get("/items/1").json() for _ in range(5)]
        
        for response in responses:
            assert response["id"] == responses[0]["id"]
            assert response["name"] == responses[0]["name"]
            assert response["price"] == responses[0]["price"]


class TestMultipleOperationsIntegration:
    """Test sequences of multiple operations."""

    def test_create_then_get_item_one(self):
        """Test creating an item then getting item 1."""
        # Create item
        create_r = client.post("/items", json={"name": "created", "price": 20})
        assert create_r.status_code == 200
        assert create_r.json()["id"] == 1
        
        # Get item 1
        get_r = client.get("/items/1")
        assert get_r.status_code == 200
        # Note: get_item returns fixed data, not created item
        assert get_r.json()["id"] == 1

    def test_multiple_creates_then_gets(self):
        """Test creating multiple items then getting them."""
        # Create multiple items
        for i, name in enumerate(["item1", "item2", "item3"]):
            r = client.post("/items", json={"name": name, "price": 10 + i})
            assert r.status_code == 200
            assert r.json()["id"] == 1
        
        # Try to get each - only 1 exists
        r1 = client.get("/items/1")
        assert r1.status_code == 200
        
        r2 = client.get("/items/2")
        assert r2.status_code == 404
        
        r3 = client.get("/items/3")
        assert r3.status_code == 404

    def test_interleaved_creates_and_gets(self):
        """Test interleaving creates and gets."""
        # Create
        c1 = client.post("/items", json={"name": "a", "price": 1})
        assert c1.status_code == 200
        
        # Get
        g1 = client.get("/items/1")
        assert g1.status_code == 200
        
        # Create again
        c2 = client.post("/items", json={"name": "b", "price": 2})
        assert c2.status_code == 200
        
        # Get again
        g2 = client.get("/items/1")
        assert g2.status_code == 200
        
        # Responses should be identical
        assert g1.json() == g2.json()


class TestPathParameterTypeCoercion:
    """Test type handling in path parameters."""

    def test_get_item_string_integer_path(self):
        """Test that string integers in path are parsed."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_get_item_invalid_path_type_float(self):
        """Test that float in path causes validation error."""
        r = client.get("/items/1.5")
        # FastAPI should reject non-integer path params
        assert r.status_code in [404, 422]

    def test_get_item_invalid_path_type_string(self):
        """Test that non-numeric string in path causes error."""
        r = client.get("/items/abc")
        assert r.status_code == 422

    def test_get_item_invalid_path_type_empty(self):
        """Test that empty path parameter causes error."""
        r = client.get("/items/")
        # Empty parameter or missing should be 404
        assert r.status_code == 404


class TestErrorHandlingInSequences:
    """Test error handling in sequences of operations."""

    def test_invalid_create_then_valid_get(self):
        """Test recovery after invalid create."""
        # Invalid create (price <= 0)
        bad_r = client.post("/items", json={"name": "bad", "price": 0})
        assert bad_r.status_code == 400
        
        # Valid get should still work
        good_r = client.get("/items/1")
        assert good_r.status_code == 200

    def test_invalid_get_then_valid_create(self):
        """Test that invalid get doesn't affect subsequent create."""
        # Invalid get
        bad_r = client.get("/items/999")
        assert bad_r.status_code == 404
        
        # Valid create should still work
        good_r = client.post("/items", json={"name": "ok", "price": 10})
        assert good_r.status_code == 200

    def test_sequence_of_invalid_operations(self):
        """Test sequence of error conditions."""
        # Try several errors
        r1 = client.post("/items", json={"price": 10})  # missing name
        assert r1.status_code == 422
        
        r2 = client.post("/items", json={"name": "item", "price": 0})  # invalid price
        assert r2.status_code == 400
        
        r3 = client.get("/items/999")  # not found
        assert r3.status_code == 404
        
        # Then a valid operation should work
        r4 = client.post("/items", json={"name": "ok", "price": 10})
        assert r4.status_code == 200


class TestEndpointIsolation:
    """Test that operations on different endpoints don't interfere."""

    def test_health_unaffected_by_items_operations(self):
        """Test that items operations don't affect health endpoint."""
        # Get health
        h1 = client.get("/health")
        assert h1.status_code == 200
        
        # Do items operations
        client.post("/items", json={"name": "a", "price": 10})
        client.get("/items/1")
        client.get("/items/999")
        client.post("/items", json={"name": "bad", "price": 0})
        
        # Health should still be ok
        h2 = client.get("/health")
        assert h2.status_code == 200
        assert h1.json() == h2.json()

    def test_multiple_health_calls_consistent(self):
        """Test that health endpoint is stateless."""
        responses = [client.get("/health").json() for _ in range(5)]
        
        # All should be identical
        for response in responses:
            assert response["status"] == "ok"
            assert response == responses[0]


class TestBoundaryValueAnalysis:
    """Test boundary and extreme values."""

    def test_get_item_boundary_values(self):
        """Test boundary values around valid ID."""
        boundaries = {
            -2147483648: 404,  # Min 32-bit int
            -1: 404,
            0: 404,
            1: 200,
            2: 404,
            2147483647: 404,  # Max 32-bit int
        }
        
        for item_id, expected_status in boundaries.items():
            r = client.get(f"/items/{item_id}")
            assert r.status_code == expected_status

    def test_create_item_price_extremes(self):
        """Test extreme price values."""
        extremes = {
            0.000001: 200,
            0.0001: 200,
            0.01: 200,
            1000000: 200,
            1e10: 200,
            1e15: 200,
            -1e10: 400,
            -0.01: 400,
        }
        
        for price, expected_status in extremes.items():
            r = client.post("/items", json={"name": "test", "price": price})
            assert r.status_code == expected_status


class TestConcurrentOperations:
    """Test behavior with rapid sequential operations."""

    def test_rapid_creates(self):
        """Test rapid sequential creates."""
        for i in range(10):
            r = client.post("/items", json={"name": f"item{i}", "price": 10 + i})
            assert r.status_code == 200
            assert r.json()["id"] == 1

    def test_rapid_gets_found(self):
        """Test rapid sequential gets of valid ID."""
        for _ in range(10):
            r = client.get("/items/1")
            assert r.status_code == 200
            assert r.json()["id"] == 1

    def test_rapid_gets_not_found(self):
        """Test rapid sequential gets of invalid ID."""
        for item_id in range(2, 12):
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404

    def test_alternating_operations(self):
        """Test alternating creates and gets."""
        for i in range(5):
            # Create
            cr = client.post("/items", json={"name": f"item{i}", "price": 10})
            assert cr.status_code == 200
            
            # Get valid
            gr1 = client.get("/items/1")
            assert gr1.status_code == 200
            
            # Get invalid
            gr2 = client.get(f"/items/{i+2}")
            assert gr2.status_code == 404
