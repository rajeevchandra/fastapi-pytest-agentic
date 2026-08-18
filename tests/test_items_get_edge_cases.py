import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test path parameter handling for GET /items/{item_id}."""

    @pytest.mark.parametrize("item_id", [1])
    def test_get_item_valid_id_boundary(self, item_id):
        """Valid item ID at lower boundary."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 200

    @pytest.mark.parametrize("item_id", [0, -1, -100, -999999])
    def test_get_item_zero_and_negative_ids(self, item_id):
        """Zero and negative item IDs return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    @pytest.mark.parametrize("item_id", [2, 3, 10, 100, 999, 1000, 999999])
    def test_get_item_ids_other_than_one(self, item_id):
        """All IDs except 1 return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    @pytest.mark.parametrize("item_id", [
        2147483647,  # Max 32-bit int
        9223372036854775807,  # Max 64-bit int
    ])
    def test_get_item_very_large_ids(self, item_id):
        """Very large integer IDs return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    def test_get_item_id_one_returns_200(self):
        """Only item_id=1 returns 200."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1

    @pytest.mark.parametrize("item_id", [
        float('inf'),
        float('nan'),
    ])
    def test_get_item_invalid_numeric_values_via_casting(self, item_id):
        """Invalid numeric values are handled appropriately."""
        # These will fail path parameter parsing
        # FastAPI should handle gracefully
        try:
            # Convert to string to simulate URL path
            r = client.get(f"/items/{int(item_id) if not (item_id != item_id or item_id == float('inf')) else 999}")
            # Should return 404 for any non-1 value
            if r.status_code == 200:
                assert r.json()["id"] == 1
            elif r.status_code == 404:
                assert "detail" in r.json()
        except (ValueError, OverflowError):
            # Expected for invalid conversions
            pass


class TestCreateItemWithVariousNames:
    """Test creating items with various name values."""

    @pytest.mark.parametrize("name,price", [
        ("a", 0.01),
        ("ab", 0.1),
        ("abc", 1.0),
        ("single_word_name", 10.0),
        ("multiple word name", 15.0),
        ("name-with-hyphens", 20.0),
        ("name_with_underscores", 25.0),
        ("nameWithMixedCase", 30.0),
        ("name123WithNumbers", 35.0),
    ])
    def test_create_item_various_valid_names(self, name, price):
        """Create items with various name formats."""
        r = client.post("/items", json={"name": name, "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name
        assert data["price"] == price


class TestCreateItemWithVariousPrices:
    """Test creating items with various price values."""

    @pytest.mark.parametrize("price", [
        0.01,
        0.02,
        0.1,
        0.5,
        0.99,
        1.0,
        1.01,
        10.0,
        10.50,
        100.0,
        1000.0,
        10000.00,
        100000.00,
        999999.99,
        1000000.0,
    ])
    def test_create_item_boundary_prices(self, price):
        """Create items with prices at various boundaries."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == price

    @pytest.mark.parametrize("price", [
        -0.01,
        -0.1,
        -1.0,
        -10.0,
        -100.0,
        -1000.0,
    ])
    def test_create_item_negative_prices_rejected(self, price):
        """Negative prices are consistently rejected."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]

    @pytest.mark.parametrize("price", [
        0,
        0.0,
        0.00,
    ])
    def test_create_item_zero_prices_rejected(self, price):
        """Zero prices are rejected."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]


class TestCreateItemIntegration:
    """Integration tests for item creation and retrieval scenarios."""

    def test_create_item_then_verify_not_retrievable(self):
        """Create item with name and price, verify it's not retrievable at id=2."""
        # Create an item
        create_response = client.post("/items", json={"name": "new_item", "price": 25.0})
        assert create_response.status_code == 200
        created_data = create_response.json()
        assert created_data["name"] == "new_item"
        assert created_data["price"] == 25.0
        
        # Try to retrieve it at a different ID
        get_response = client.get("/items/2")
        assert get_response.status_code == 404
        
        # But original item should still be at ID 1
        original_response = client.get("/items/1")
        assert original_response.status_code == 200
        assert original_response.json()["id"] == 1

    def test_multiple_creates_do_not_affect_get(self):
        """Multiple item creations don't change what GET /items/1 returns."""
        # Create multiple items
        for name in ["item1", "item2", "item3"]:
            r = client.post("/items", json={"name": name, "price": 10.0})
            assert r.status_code == 200
        
        # GET /items/1 should still return the same item
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0

    def test_create_then_error_then_create(self):
        """Verify error handling doesn't affect subsequent operations."""
        # Try to create with invalid price
        bad_r = client.post("/items", json={"name": "bad", "price": 0})
        assert bad_r.status_code == 400
        
        # Create with valid price
        good_r = client.post("/items", json={"name": "good", "price": 10.0})
        assert good_r.status_code == 200
        assert good_r.json()["name"] == "good"
        
        # GET should still work
        get_r = client.get("/items/1")
        assert get_r.status_code == 200


class TestCreateItemResponseValues:
    """Verify response values for create operations."""

    def test_create_item_response_id_is_one(self):
        """Create item always returns id=1."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_create_item_response_preserves_name(self):
        """Create item response preserves input name exactly."""
        test_name = "special_name_123!@#"
        r = client.post("/items", json={"name": test_name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == test_name

    def test_create_item_response_preserves_price(self):
        """Create item response preserves input price exactly."""
        test_price = 123.45
        r = client.post("/items", json={"name": "test", "price": test_price})
        assert r.status_code == 200
        assert r.json()["price"] == test_price

    @pytest.mark.parametrize("name,price", [
        ("book", 9.99),
        ("pen", 0.99),
        ("notebook", 15.50),
        ("calculator", 25.00),
        ("special-item", 100.00),
    ])
    def test_create_item_response_complete_data(self, name, price):
        """Create item response contains all input data correctly."""
        r = client.post("/items", json={"name": name, "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == name
        assert data["price"] == price


class TestGetItemFixedData:
    """Verify GET /items/1 returns fixed sample data."""

    def test_get_item_one_has_fixed_id(self):
        """GET /items/1 returns id=1."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_get_item_one_has_fixed_name(self):
        """GET /items/1 returns fixed name."""
        r = client.get("/items/1")
        assert r.status_code == 200
        name = r.json()["name"]
        assert isinstance(name, str)
        assert len(name) > 0
        # Verify it's consistently the same
        r2 = client.get("/items/1")
        assert r2.json()["name"] == name

    def test_get_item_one_has_fixed_price(self):
        """GET /items/1 returns fixed price."""
        r = client.get("/items/1")
        assert r.status_code == 200
        price = r.json()["price"]
        assert isinstance(price, (int, float))
        assert price > 0
        # Verify it's consistently the same
        r2 = client.get("/items/1")
        assert r2.json()["price"] == price

    def test_get_item_one_complete_response(self):
        """GET /items/1 returns complete valid response."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0


class TestSequentialOperations:
    """Test sequences of operations."""

    def test_create_invalid_create_valid_get(self):
        """Invalid create doesn't prevent subsequent valid operations."""
        # Invalid
        r1 = client.post("/items", json={"name": "test", "price": -1})
        assert r1.status_code == 400
        
        # Valid
        r2 = client.post("/items", json={"name": "test", "price": 10})
        assert r2.status_code == 200
        
        # Get should work
        r3 = client.get("/items/1")
        assert r3.status_code == 200

    def test_get_invalid_get_valid(self):
        """Invalid GET doesn't prevent subsequent valid GET."""
        # Invalid ID
        r1 = client.get("/items/999")
        assert r1.status_code == 404
        
        # Valid ID
        r2 = client.get("/items/1")
        assert r2.status_code == 200

    def test_multiple_get_operations(self):
        """Multiple GET operations return consistent results."""
        results = []
        for _ in range(5):
            r = client.get("/items/1")
            assert r.status_code == 200
            results.append(r.json())
        
        # All results should be identical
        for result in results[1:]:
            assert result == results[0]


class TestEdgeCaseSequences:
    """Test edge case scenarios in sequences."""

    def test_create_with_empty_name_then_valid(self):
        """Create with empty name then valid name."""
        # Empty name (should succeed - validation is app-specific)
        r1 = client.post("/items", json={"name": "", "price": 10.0})
        assert r1.status_code == 200
        
        # Valid name
        r2 = client.post("/items", json={"name": "valid", "price": 10.0})
        assert r2.status_code == 200

    def test_create_with_long_name(self):
        """Create item with very long name."""
        long_name = "a" * 5000
        r = client.post("/items", json={"name": long_name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == long_name

    def test_create_with_unicode_then_get(self):
        """Create with unicode name, then verify behavior."""
        unicode_name = "café☕中文العربية🎉"
        r = client.post("/items", json={"name": unicode_name, "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == unicode_name

    def test_price_precision(self):
        """Verify price precision is preserved."""
        test_prices = [0.01, 0.1, 1.5, 10.99, 100.001, 1234.5678]
        for price in test_prices:
            r = client.post("/items", json={"name": "test", "price": price})
            assert r.status_code == 200
            assert r.json()["price"] == price
