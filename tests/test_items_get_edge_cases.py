"""Test edge cases and integration scenarios."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test path parameter validation for get_item."""

    @pytest.mark.parametrize("item_id", [
        -1,
        -100,
        0,
    ])
    def test_get_item_with_negative_or_zero_ids(self, item_id):
        """Test that negative and zero IDs return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    @pytest.mark.parametrize("item_id", [
        1000,
        999999,
        1000000,
    ])
    def test_get_item_with_large_ids(self, item_id):
        """Test that large IDs (other than 1) return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    def test_get_item_boundary_zero(self):
        """Test item_id = 0 specifically."""
        r = client.get("/items/0")
        assert r.status_code == 404

    def test_get_item_boundary_one(self):
        """Test item_id = 1 specifically (should succeed)."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_get_item_boundary_two(self):
        """Test item_id = 2 specifically (should fail)."""
        r = client.get("/items/2")
        assert r.status_code == 404


class TestCreateItemWithVariousNames:
    """Test create_item with various name inputs."""

    @pytest.mark.parametrize("name", [
        "a",
        "ab",
        "abc",
        "Short",
        "Medium Length Name",
        "Very Long Name With Many Words " * 10,
        "name123",
        "123name",
        "name-with-dashes",
        "name_with_underscores",
        "name.with.dots",
        "name/with/slashes",
        "name with   spaces",
        "UPPERCASE",
        "lowercase",
        "MixedCase",
    ])
    def test_create_item_with_various_name_formats(self, name):
        """Test create_item accepts various name formats."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name


class TestCreateItemWithVariousPrices:
    """Test create_item with various price inputs."""

    @pytest.mark.parametrize("price", [
        0.01,
        0.001,
        0.0001,
        0.00001,
        1,
        1.0,
        1.5,
        10,
        100,
        1000,
        10000,
        100000,
        1000000,
        0.99,
        1.99,
        99.99,
        999.99,
        9999.99,
    ])
    def test_create_item_accepts_various_positive_prices(self, price):
        """Test create_item with various valid positive prices."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    @pytest.mark.parametrize("price", [
        -0.01,
        -0.001,
        -1,
        -10,
        -100,
        -1000,
        0,
    ])
    def test_create_item_rejects_various_non_positive_prices(self, price):
        """Test create_item rejects various non-positive prices."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"


class TestMultipleItemOperations:
    """Test multiple consecutive item operations."""

    def test_create_multiple_items_and_retrieve(self):
        """Test creating multiple items in sequence."""
        # Create multiple items
        for i in range(5):
            r = client.post("/items", json={"name": f"item{i}", "price": float(i + 1)})
            assert r.status_code == 200
            data = r.json()
            assert data["id"] == 1  # API always returns id=1
            assert data["name"] == f"item{i}"
            assert data["price"] == float(i + 1)

    def test_get_existing_item_multiple_times(self):
        """Test retrieving existing item multiple times."""
        for _ in range(5):
            r = client.get("/items/1")
            assert r.status_code == 200
            data = r.json()
            assert data["id"] == 1
            assert data["name"] == "sample"
            assert data["price"] == 10.0

    def test_get_nonexistent_item_multiple_times(self):
        """Test retrieving nonexistent item multiple times."""
        for item_id in range(2, 10):
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404
            assert r.json()["detail"] == "not found"

    def test_mixed_create_and_get_operations(self):
        """Test mixed create and get operations."""
        # Create an item
        create_r = client.post("/items", json={"name": "test", "price": 15.0})
        assert create_r.status_code == 200

        # Get existing item
        get_r = client.get("/items/1")
        assert get_r.status_code == 200

        # Create another item
        create_r2 = client.post("/items", json={"name": "test2", "price": 20.0})
        assert create_r2.status_code == 200

        # Get non-existent item
        get_r2 = client.get("/items/5")
        assert get_r2.status_code == 404


class TestEdgeCaseIntegrations:
    """Test integration scenarios with edge cases."""

    def test_create_item_with_minimal_price(self):
        """Test creating item with minimal positive price."""
        r = client.post("/items", json={"name": "item", "price": 0.001})
        assert r.status_code == 200
        assert r.json()["price"] == 0.001

    def test_create_item_exactly_at_boundary(self):
        """Test price exactly at zero boundary (should fail)."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.status_code == 400

    def test_create_item_just_above_boundary(self):
        """Test price just above zero boundary (should succeed)."""
        r = client.post("/items", json={"name": "item", "price": 0.0001})
        assert r.status_code == 200

    def test_create_item_just_below_boundary(self):
        """Test price just below zero boundary (should fail)."""
        r = client.post("/items", json={"name": "item", "price": -0.0001})
        assert r.status_code == 400

    def test_get_item_boundary_transitions(self):
        """Test transitions around item_id boundaries."""
        # id = 0 should fail
        r = client.get("/items/0")
        assert r.status_code == 404

        # id = 1 should succeed
        r = client.get("/items/1")
        assert r.status_code == 200

        # id = 2 should fail
        r = client.get("/items/2")
        assert r.status_code == 404


class TestResponseConsistency:
    """Test consistency of responses across multiple requests."""

    def test_get_item_response_consistent(self):
        """Test that get_item returns consistent data."""
        r1 = client.get("/items/1")
        r2 = client.get("/items/1")
        assert r1.json() == r2.json()

    def test_create_item_response_consistent_fields(self):
        """Test that create_item response always has same fields."""
        r1 = client.post("/items", json={"name": "test1", "price": 10.0})
        r2 = client.post("/items", json={"name": "test2", "price": 20.0})
        
        data1 = r1.json()
        data2 = r2.json()
        
        # Both responses should have same keys
        assert set(data1.keys()) == set(data2.keys())
        assert set(data1.keys()) == {"id", "name", "price"}

    def test_error_response_consistent(self):
        """Test error responses are consistent."""
        # Both non-positive prices should return same format
        r1 = client.post("/items", json={"name": "test", "price": 0})
        r2 = client.post("/items", json={"name": "test", "price": -5})
        
        assert r1.status_code == r2.status_code == 400
        assert set(r1.json().keys()) == set(r2.json().keys())


class TestInvalidPathParameters:
    """Test handling of invalid path parameters."""

    def test_get_item_with_string_id(self):
        """Test get_item with string that's not a number."""
        r = client.get("/items/abc")
        # FastAPI should return 422 for invalid path parameter
        assert r.status_code == 422

    def test_get_item_with_float_id(self):
        """Test get_item with float in path (may be parsed as int)."""
        r = client.get("/items/1.5")
        # Behavior depends on path parameter parsing
        assert r.status_code in [200, 404, 422]

    def test_get_item_with_negative_string(self):
        """Test get_item with negative number as string."""
        r = client.get("/items/-1")
        # Should parse as -1 and return 404
        assert r.status_code == 404


class TestHTTPMethods:
    """Test various HTTP methods on endpoints."""

    def test_items_post_endpoint_exists(self):
        """Test that POST /items endpoint is available."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code in [200, 400, 422]

    def test_items_get_endpoint_exists(self):
        """Test that GET /items/{id} endpoint is available."""
        r = client.get("/items/1")
        assert r.status_code in [200, 404]

    def test_items_get_without_id_not_allowed(self):
        """Test that GET /items without ID is not available."""
        r = client.get("/items")
        # Should return 404 for non-existent path
        assert r.status_code == 404

    def test_items_put_not_allowed(self):
        """Test that PUT /items is not allowed."""
        r = client.put("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 405  # Method Not Allowed

    def test_items_delete_not_allowed(self):
        """Test that DELETE /items is not allowed."""
        r = client.delete("/items")
        assert r.status_code == 405  # Method Not Allowed
