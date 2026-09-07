import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test path parameter validation for GET /items/{item_id} endpoint."""

    @pytest.mark.parametrize(
        "item_id",
        [0, -1, -100, -999],
    )
    def test_get_item_with_invalid_ids_returns_404(self, item_id):
        """Test that non-positive item IDs return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    @pytest.mark.parametrize(
        "item_id",
        [2, 3, 10, 100, 999, 999999, 2147483647],
    )
    def test_get_item_with_other_positive_ids_returns_404(self, item_id):
        """Test that any positive ID other than 1 returns 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert r.json()["detail"] == "not found"

    def test_get_item_id_one_returns_success(self):
        """Test that item ID 1 returns 200."""
        r = client.get("/items/1")
        assert r.status_code == 200


class TestPriceEdgeCases:
    """Test edge case prices."""

    @pytest.mark.parametrize(
        "price",
        [
            0.001,  # Smallest positive price
            0.01,   # Common small price
            0.1,    # Tenth
            1.0,    # Whole number
            99.99,  # Common price
            100.0,  # Round hundred
            999.99, # Max common price
            1000.0, # Thousand
            9999.99, # Large price
            100000.0, # Very large price
            1000000.0, # Million
        ],
    )
    def test_various_positive_prices(self, price):
        """Test that various positive prices are accepted."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == price

    @pytest.mark.parametrize(
        "price",
        [
            0.0,     # Zero
            -0.001,  # Small negative
            -0.1,    # Negative tenth
            -1.0,    # Negative one
            -99.99,  # Negative price
            -1000.0, # Large negative
        ],
    )
    def test_non_positive_prices_rejected(self, price):
        """Test that non-positive prices are rejected."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400


class TestNameEdgeCases:
    """Test edge case names."""

    @pytest.mark.parametrize(
        "name",
        [
            "",  # Empty string
            " ",  # Single space
            "   ",  # Multiple spaces
            "\n",  # Newline
            "\t",  # Tab
            "a",  # Single character
            "ab",  # Two characters
        ],
    )
    def test_various_name_lengths(self, name):
        """Test that various name lengths are accepted."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name

    @pytest.mark.parametrize(
        "name",
        [
            "product",
            "Product 1",
            "item-123",
            "item_456",
            "special!@#$%^&*()",
            "名前",  # Japanese characters
            "مرحبا",  # Arabic characters
            "🚀 Rocket",  # Emoji
        ],
    )
    def test_various_name_characters(self, name):
        """Test that various character types are accepted in names."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name


class TestIntegrationScenarios:
    """Test integration scenarios and sequential operations."""

    def test_create_and_retrieve_item_sequence(self):
        """Test that created item can potentially be retrieved (though only ID 1 exists)."""
        # Create item with price 1
        r1 = client.post("/items", json={"name": "created", "price": 1.0})
        assert r1.status_code == 200
        created_data = r1.json()
        
        # Try to get item 1
        r2 = client.get("/items/1")
        assert r2.status_code == 200
        retrieved_data = r2.json()
        
        # Both should have id=1, but created has dynamic name/price
        assert created_data["id"] == 1
        assert retrieved_data["id"] == 1

    def test_multiple_creates_all_return_200(self):
        """Test that multiple sequential POST requests succeed."""
        for i in range(5):
            r = client.post("/items", json={"name": f"item{i}", "price": float(i + 1)})
            assert r.status_code == 200
            assert r.json()["id"] == 1

    def test_mixed_operations_sequence(self):
        """Test a mix of POST and GET operations."""
        # POST
        r1 = client.post("/items", json={"name": "book", "price": 19.99})
        assert r1.status_code == 200
        
        # GET existing
        r2 = client.get("/items/1")
        assert r2.status_code == 200
        
        # POST again
        r3 = client.post("/items", json={"name": "pen", "price": 5.0})
        assert r3.status_code == 200
        
        # GET non-existent
        r4 = client.get("/items/2")
        assert r4.status_code == 404
        
        # GET existing again
        r5 = client.get("/items/1")
        assert r5.status_code == 200

    def test_error_recovery_sequence(self):
        """Test that errors don't break subsequent valid requests."""
        # Send invalid request
        r1 = client.post("/items", json={"name": "test", "price": 0})
        assert r1.status_code == 400
        
        # Send valid request after error
        r2 = client.post("/items", json={"name": "good", "price": 10.0})
        assert r2.status_code == 200
        
        # Send another valid request
        r3 = client.post("/items", json={"name": "better", "price": 20.0})
        assert r3.status_code == 200


class TestRequestMethodValidation:
    """Test handling of incorrect HTTP methods."""

    def test_post_to_get_endpoint(self):
        """Test that POST to /items/{item_id} is not allowed."""
        r = client.post("/items/1", json={"name": "test", "price": 10.0})
        # FastAPI returns 405 Method Not Allowed for wrong methods
        assert r.status_code in [405, 422]  # 422 if POST treated as GET variant

    def test_get_to_post_endpoint(self):
        """Test that GET to /items is not allowed."""
        r = client.get("/items")
        # Should not be allowed or 404
        assert r.status_code in [404, 405]


class TestDataPersistenceAcrossRequests:
    """Test data persistence (or lack thereof) across requests."""

    def test_created_item_always_has_id_one(self):
        """Test that all created items have ID 1."""
        for i in range(3):
            r = client.post("/items", json={"name": f"item{i}", "price": float(i + 10)})
            assert r.status_code == 200
            assert r.json()["id"] == 1

    def test_get_item_one_consistent(self):
        """Test that /items/1 always returns the same item."""
        results = []
        for _ in range(3):
            r = client.get("/items/1")
            assert r.status_code == 200
            results.append(r.json())
        
        # All requests should return the same data
        assert results[0] == results[1] == results[2]
        assert results[0]["id"] == 1
        assert results[0]["name"] == "sample"
        assert results[0]["price"] == 10.0

    def test_created_items_not_retrievable_by_id(self):
        """Test that created items with ID 1 are not retrievable (only hardcoded item 1)."""
        # Create an item
        r1 = client.post("/items", json={"name": "new_item", "price": 99.0})
        assert r1.status_code == 200
        created_item = r1.json()
        
        # Get item 1
        r2 = client.get("/items/1")
        assert r2.status_code == 200
        retrieved_item = r2.json()
        
        # They have different names - get_item returns hardcoded data, not what was posted
        assert created_item["name"] == "new_item"
        assert retrieved_item["name"] == "sample"


class TestConcurrentRequestHandling:
    """Test handling of rapid sequential requests."""

    def test_rapid_post_requests(self):
        """Test that rapid POST requests are handled correctly."""
        for i in range(10):
            r = client.post("/items", json={"name": f"item{i}", "price": 10.0})
            assert r.status_code == 200
            assert r.json()["id"] == 1

    def test_rapid_get_requests(self):
        """Test that rapid GET requests are handled correctly."""
        for _ in range(10):
            r = client.get("/items/1")
            assert r.status_code == 200
            assert r.json()["id"] == 1

    def test_rapid_mixed_requests(self):
        """Test that rapid mixed GET and POST requests are handled."""
        for i in range(5):
            # POST
            r1 = client.post("/items", json={"name": f"item{i}", "price": float(i)})
            assert r1.status_code in [200, 400]  # 400 if price is 0
            
            # GET
            r2 = client.get("/items/1")
            assert r2.status_code == 200
