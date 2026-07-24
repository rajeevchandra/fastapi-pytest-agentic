import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test path parameter validation for get_item endpoint."""

    @pytest.mark.parametrize(
        "item_id,expected_status",
        [
            (1, 200),  # Valid ID that exists
            (0, 404),  # Zero (invalid, not found)
            (-1, 404),  # Negative (not found)
            (-100, 404),  # Large negative (not found)
            (2, 404),  # Different valid ID (not found)
            (999, 404),  # Large ID (not found)
            (999999999, 404),  # Very large ID (not found)
        ],
    )
    def test_get_item_various_ids(self, item_id, expected_status):
        """Test get_item with various ID values."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == expected_status


class TestGetItemBoundaryValues:
    """Test boundary values for item retrieval."""

    def test_get_item_id_zero(self):
        """Test get_item with ID of 0."""
        r = client.get("/items/0")
        assert r.status_code == 404

    def test_get_item_id_one_found(self):
        """Test get_item with ID of 1 (should be found)."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1

    def test_get_item_id_max_int(self):
        """Test get_item with maximum integer value."""
        r = client.get(f"/items/{2147483647}")  # Max 32-bit int
        assert r.status_code == 404

    def test_get_item_multiple_not_found(self):
        """Test that multiple different IDs are not found."""
        for item_id in [2, 3, 4, 5, 100, 1000]:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404


class TestGetItemIDTypeHandling:
    """Test type handling for item_id parameter."""

    def test_get_item_string_convertible_to_int(self):
        """Test get_item with numeric string."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_get_item_negative_string(self):
        """Test get_item with negative numeric string."""
        r = client.get("/items/-1")
        assert r.status_code == 404

    def test_get_item_float_string(self):
        """Test get_item with float string."""
        r = client.get("/items/1.5")
        # Path parameters with decimals may be rejected
        assert r.status_code in [404, 422]


class TestIntegrationScenarios:
    """Test integration scenarios with multiple operations."""

    def test_create_then_retrieve_item(self):
        """Test creating an item and then retrieving it."""
        # Create
        create_r = client.post("/items", json={"name": "test_item", "price": 29.99})
        assert create_r.status_code == 200
        created_data = create_r.json()
        
        # Retrieve the created item (ID is always 1 in this simple API)
        get_r = client.get(f"/items/{created_data['id']}")
        assert get_r.status_code == 200
        retrieved_data = get_r.json()
        
        # Verify it's retrievable
        assert retrieved_data["id"] == created_data["id"]

    def test_multiple_create_attempts_same_id(self):
        """Test that multiple creates use the same ID."""
        r1 = client.post("/items", json={"name": "first", "price": 10.0})
        r2 = client.post("/items", json={"name": "second", "price": 20.0})
        
        assert r1.status_code == 200
        assert r2.status_code == 200
        # Both should return ID 1 (hardcoded)
        assert r1.json()["id"] == 1
        assert r2.json()["id"] == 1

    def test_get_non_existent_then_create(self):
        """Test getting non-existent item then creating it."""
        # Try to get non-existent
        r1 = client.get("/items/2")
        assert r1.status_code == 404
        
        # Create an item
        r2 = client.post("/items", json={"name": "new", "price": 15.0})
        assert r2.status_code == 200
        
        # Now get the created item
        r3 = client.get("/items/1")
        assert r3.status_code == 200

    def test_create_with_all_boundary_prices(self):
        """Test creating items with boundary price values."""
        boundary_prices = [0.01, 1.0, 100.0, 1e6]
        
        for price in boundary_prices:
            r = client.post("/items", json={"name": f"item_{price}", "price": price})
            assert r.status_code == 200
            data = r.json()
            assert data["price"] == price


class TestErrorRecovery:
    """Test error handling and recovery scenarios."""

    def test_invalid_create_then_valid_create(self):
        """Test that valid create works after invalid attempt."""
        # Invalid create
        r1 = client.post("/items", json={"name": "item", "price": -10})
        assert r1.status_code == 400
        
        # Valid create should still work
        r2 = client.post("/items", json={"name": "valid", "price": 10.0})
        assert r2.status_code == 200

    def test_get_non_existent_multiple_times(self):
        """Test multiple get attempts for non-existent items."""
        for _ in range(3):
            r = client.get("/items/999")
            assert r.status_code == 404

    def test_mix_of_valid_and_invalid_operations(self):
        """Test a mix of valid and invalid operations."""
        operations = [
            ("POST", {"name": "valid1", "price": 10.0}, 200),
            ("POST", {"name": "invalid", "price": -5}, 400),
            ("POST", {"name": "valid2", "price": 20.0}, 200),
            ("GET", None, 200),
            ("POST", {"name": "missing_price"}, 422),
            ("GET", None, 200),
        ]
        
        post_count = 0
        for method, data, expected_status in operations:
            if method == "POST":
                r = client.post("/items", json=data)
                post_count += 1
            else:  # GET
                r = client.get("/items/1")
            
            assert r.status_code == expected_status


class TestSequentialAccess:
    """Test sequential access patterns."""

    def test_access_valid_item_repeatedly(self):
        """Test accessing valid item multiple times."""
        for _ in range(5):
            r = client.get("/items/1")
            assert r.status_code == 200
            data = r.json()
            assert data["id"] == 1
            assert data["name"] == "sample"
            assert data["price"] == 10.0

    def test_create_and_retrieve_consistently(self):
        """Test that retrieve returns consistent data after create."""
        create_r = client.post("/items", json={"name": "consistent", "price": 50.0})
        assert create_r.status_code == 200
        created_data = create_r.json()
        
        # Retrieve multiple times
        for _ in range(3):
            get_r = client.get("/items/1")
            assert get_r.status_code == 200
            retrieved_data = get_r.json()
            # Data should be consistent
            assert retrieved_data["id"] == created_data["id"]


class TestEdgeCaseNumbers:
    """Test edge case numeric values."""

    def test_create_item_various_price_formats(self):
        """Test creating items with various price number formats."""
        test_cases = [
            (0.001, 0.001),  # Very small
            (1.0, 1.0),  # Integer as float
            (1.50, 1.5),  # Two decimals
            (999.99, 999.99),  # Large
        ]
        
        for price, expected in test_cases:
            r = client.post("/items", json={"name": "test", "price": price})
            assert r.status_code == 200
            data = r.json()
            assert data["price"] == expected

    def test_get_item_large_positive_id(self):
        """Test get_item with large positive ID."""
        large_ids = [1000, 10000, 100000, 999999]
        
        for item_id in large_ids:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404

    def test_get_item_specific_negative_ids(self):
        """Test get_item with specific negative IDs."""
        negative_ids = [-1, -10, -100, -999]
        
        for item_id in negative_ids:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404
