import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test path parameter validation and edge cases for GET /items/{item_id}."""

    @pytest.mark.parametrize("item_id", [
        1,
        999,
        2,
        3,
        100,
    ])
    def test_get_item_various_ids_behavior(self, item_id):
        """Test GET with various item_ids to understand behavior."""
        r = client.get(f"/items/{item_id}")
        
        if item_id == 1:
            assert r.status_code == 200
            assert r.json()["id"] == 1
        else:
            assert r.status_code == 404

    @pytest.mark.parametrize("item_id", [
        0,
        -1,
        -100,
        -999,
    ])
    def test_get_item_zero_and_negative_ids(self, item_id):
        """Test GET with zero and negative item_ids."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert "detail" in r.json()

    def test_get_item_max_integer_id(self):
        """Test GET with very large integer."""
        large_id = 2147483647  # Max 32-bit int
        r = client.get(f"/items/{large_id}")
        assert r.status_code == 404

    def test_get_item_string_in_url_returns_422(self):
        """Test that string in path parameter causes validation error."""
        r = client.get("/items/invalid")
        assert r.status_code == 422
        assert "detail" in r.json()

    def test_get_item_float_in_url(self):
        """Test that float in path converts to int or error."""
        r = client.get("/items/1.5")
        # FastAPI may treat this as /items/1 or return 422
        assert r.status_code in [200, 422]

    def test_get_item_empty_path_parameter(self):
        """Test missing path parameter."""
        r = client.get("/items/")
        # This typically 404s at routing level
        assert r.status_code in [404, 405]

    def test_get_item_multiple_path_segments(self):
        """Test path with extra segments."""
        r = client.get("/items/1/extra")
        assert r.status_code == 404

    def test_get_item_special_characters_in_path(self):
        """Test special characters in path parameter."""
        r = client.get("/items/@#$%")
        assert r.status_code == 422


class TestCreateItemIdempotency:
    """Test idempotency and consistency of item creation."""

    def test_create_same_item_twice_behavior(self):
        """Test creating the same item twice."""
        payload = {"name": "test_item", "price": 99.99}
        
        r1 = client.post("/items", json=payload)
        r2 = client.post("/items", json=payload)
        
        assert r1.status_code == 200
        assert r2.status_code == 200
        
        # Both should return same ID (implementation specific)
        assert r1.json()["id"] == r2.json()["id"]

    def test_create_different_items_same_id(self):
        """Test creating different items."""
        r1 = client.post("/items", json={"name": "item1", "price": 10.0})
        r2 = client.post("/items", json={"name": "item2", "price": 20.0})
        
        assert r1.status_code == 200
        assert r2.status_code == 200
        
        # Currently returns same ID (mock implementation)
        assert r1.json()["id"] == r2.json()["id"] == 1
        assert r1.json()["name"] != r2.json()["name"]

    def test_multiple_sequential_creates(self):
        """Test multiple sequential item creations."""
        results = []
        for i in range(5):
            r = client.post("/items", json={"name": f"item{i}", "price": float(i + 1)})
            assert r.status_code == 200
            results.append(r.json())
        
        # All should have valid structure
        for result in results:
            assert result["id"] is not None
            assert result["name"] is not None
            assert result["price"] is not None


class TestAPIStateConsistency:
    """Test consistency across multiple API calls."""

    def test_create_then_get_success(self):
        """Test creating an item and then retrieving it."""
        # Create item
        create_r = client.post("/items", json={"name": "created_item", "price": 25.0})
        assert create_r.status_code == 200
        created_id = create_r.json()["id"]
        created_name = create_r.json()["name"]
        
        # Get same item
        get_r = client.get(f"/items/{created_id}")
        assert get_r.status_code == 200
        retrieved = get_r.json()
        
        # IDs should match
        assert retrieved["id"] == created_id

    def test_get_then_create_consistency(self):
        """Test getting item then creating new one."""
        # Get existing
        get_r = client.get("/items/1")
        assert get_r.status_code == 200
        existing = get_r.json()
        
        # Create new
        create_r = client.post("/items", json={"name": "new_item", "price": 30.0})
        assert create_r.status_code == 200
        created = create_r.json()
        
        # Existing should still be retrievable
        get_r2 = client.get(f"/items/{existing['id']}")
        assert get_r2.status_code == 200

    def test_failed_create_does_not_affect_get(self):
        """Test that failed create doesn't break get."""
        # Try invalid create
        create_r = client.post("/items", json={"name": "item", "price": -1})
        assert create_r.status_code == 400
        
        # Get should still work
        get_r = client.get("/items/1")
        assert get_r.status_code == 200


class TestConcurrentOperationSimulation:
    """Simulate concurrent operations (in sequence)."""

    def test_interleaved_create_and_get(self):
        """Test interleaved create and get operations."""
        operations = []
        
        # Create
        r1 = client.post("/items", json={"name": "item1", "price": 10.0})
        operations.append(("create", r1.status_code))
        
        # Get
        r2 = client.get("/items/1")
        operations.append(("get", r2.status_code))
        
        # Create
        r3 = client.post("/items", json={"name": "item2", "price": 20.0})
        operations.append(("create", r3.status_code))
        
        # Get
        r4 = client.get("/items/1")
        operations.append(("get", r4.status_code))
        
        # All should succeed
        for op, status in operations:
            assert status in [200, 201]

    def test_health_check_interleaved_with_operations(self):
        """Test health check works alongside other operations."""
        results = {
            "health": [],
            "create": [],
            "get": [],
        }
        
        for _ in range(3):
            h = client.get("/health")
            results["health"].append(h.status_code)
            
            c = client.post("/items", json={"name": "test", "price": 10.0})
            results["create"].append(c.status_code)
            
            g = client.get("/items/1")
            results["get"].append(g.status_code)
        
        # All should succeed
        assert all(s == 200 for s in results["health"])
        assert all(s == 200 for s in results["create"])
        assert all(s == 200 for s in results["get"])


class TestEdgeCaseInteractions:
    """Test interactions between different edge cases."""

    def test_create_with_max_length_name_then_get(self):
        """Test creating item with very long name and retrieving."""
        long_name = "x" * 10000
        r1 = client.post("/items", json={"name": long_name, "price": 10.0})
        assert r1.status_code == 200
        
        # Should be retrievable
        r2 = client.get("/items/1")
        assert r2.status_code == 200

    def test_create_with_max_price_then_get(self):
        """Test creating item with very large price."""
        large_price = 999999999.99
        r1 = client.post("/items", json={"name": "expensive", "price": large_price})
        assert r1.status_code == 200
        
        r2 = client.get("/items/1")
        assert r2.status_code == 200
        assert r2.json()["price"] > 0

    def test_create_near_zero_price_then_get(self):
        """Test creating item with price just above zero."""
        r1 = client.post("/items", json={"name": "cheap", "price": 0.001})
        assert r1.status_code == 200
        
        r2 = client.get("/items/1")
        assert r2.status_code == 200
        assert r2.json()["price"] == 0.001

    def test_stress_get_nonexistent_ids(self):
        """Stress test getting many non-existent items."""
        for i in range(2, 20):
            r = client.get(f"/items/{i}")
            assert r.status_code == 404
            assert "detail" in r.json()

    def test_invalid_operations_sequence(self):
        """Test sequence of operations with errors."""
        # Invalid create
        r1 = client.post("/items", json={"name": "bad", "price": -1})
        assert r1.status_code == 400
        
        # Missing field
        r2 = client.post("/items", json={"price": 10.0})
        assert r2.status_code == 422
        
        # Invalid get
        r3 = client.get("/items/999")
        assert r3.status_code == 404
        
        # Valid operations still work
        r4 = client.post("/items", json={"name": "good", "price": 10.0})
        assert r4.status_code == 200
        
        r5 = client.get("/items/1")
        assert r5.status_code == 200


class TestBoundaryValuePairings:
    """Test boundary values across endpoint pairs."""

    @pytest.mark.parametrize("name,price,should_succeed", [
        ("a", 0.01, True),
        ("", 0.01, False),
        ("a", 0, False),
        ("a" * 1000, 1000, True),
        ("special!@#$", 999.99, True),
    ])
    def test_create_with_boundary_combinations(self, name, price, should_succeed):
        """Test create with boundary value combinations."""
        r = client.post("/items", json={"name": name, "price": price})
        
        if should_succeed:
            assert r.status_code == 200
        else:
            assert r.status_code in [400, 422]

    def test_item_id_boundary_with_status_code_sequence(self):
        """Test item_id boundaries return consistent status codes."""
        test_ids = [0, 1, 2, -1, 999]
        expected_codes = []
        
        for item_id in test_ids:
            r = client.get(f"/items/{item_id}")
            expected_codes.append(r.status_code)
        
        # Only item 1 should be 200, others 404
        assert expected_codes[1] == 200  # item_id=1
        assert expected_codes[2] == 404  # item_id=2
        assert expected_codes[0] == 404  # item_id=0
        assert expected_codes[3] == 404  # item_id=-1
        assert expected_codes[4] == 404  # item_id=999
