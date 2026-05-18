"""Integration tests and parametrized tests for items API.

This module provides comprehensive integration scenarios and uses
parametrized tests for better coverage of value ranges.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestItemsIntegration:
    """Integration tests for end-to-end scenarios."""
    
    def test_create_and_retrieve_workflow(self):
        """Test creating an item and then retrieving it."""
        # Create item
        create_response = client.post("/items", json={"name": "laptop", "price": 999.99})
        assert create_response.status_code == 200
        created_item = create_response.json()
        
        # Verify creation response
        assert created_item["id"] == 1
        assert created_item["name"] == "laptop"
        assert created_item["price"] == 999.99
        
        # Retrieve the same item
        get_response = client.get(f"/items/{created_item['id']}")
        assert get_response.status_code == 200
        retrieved_item = get_response.json()
        
        # Note: The GET endpoint returns a hardcoded "sample" item,
        # so we verify it returns the expected structure
        assert "id" in retrieved_item
        assert "name" in retrieved_item
        assert "price" in retrieved_item
    
    def test_health_check_integration(self):
        """Test health endpoint is accessible."""
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}
    
    def test_multiple_creates_return_same_id(self):
        """Test that multiple creates currently return the same ID (documenting current behavior)."""
        r1 = client.post("/items", json={"name": "item1", "price": 10.0})
        r2 = client.post("/items", json={"name": "item2", "price": 20.0})
        
        assert r1.status_code == 200
        assert r2.status_code == 200
        
        # Document current behavior: both return id=1
        assert r1.json()["id"] == 1
        assert r2.json()["id"] == 1


class TestParametrizedPriceValidation:
    """Parametrized tests for price validation."""
    
    @pytest.mark.parametrize("price,expected_status", [
        (0.01, 200),      # Smallest positive price
        (1.0, 200),       # Simple price
        (10.5, 200),      # Decimal price
        (100.99, 200),    # Large decimal
        (999999, 200),    # Very large price
        (0, 400),         # Zero (invalid)
        (-0.01, 400),     # Negative (invalid)
        (-1, 400),        # Negative integer
        (-999, 400),      # Large negative
    ])
    def test_create_item_price_validation(self, price, expected_status):
        """Test various price values and their validation."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == expected_status
    
    @pytest.mark.parametrize("price", [0.01, 1.0, 5.99, 100.0, 999999.99])
    def test_valid_prices_return_same_value(self, price):
        """Test that valid prices are echoed back correctly."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price


class TestParametrizedNameValidation:
    """Parametrized tests for name validation."""
    
    @pytest.mark.parametrize("name", [
        "a",                          # Single character
        "ab",                         # Two characters
        "book",                       # Simple word
        "laptop computer",            # Multiple words
        "item-with-dashes",          # With dashes
        "item_with_underscores",     # With underscores
        "UPPERCASE",                  # Uppercase
        "MiXeD CaSe",                # Mixed case
        "123",                        # Numbers only
        "item123",                    # Alphanumeric
        "",                           # Empty (tests current behavior)
        "   ",                        # Whitespace only
        "café",                       # Accented characters
        "日本語",                      # Non-Latin characters
        "emoji 🎉",                   # With emoji
    ])
    def test_create_item_various_names(self, name):
        """Test various name values are accepted."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name


class TestParametrizedItemIdValidation:
    """Parametrized tests for item_id path parameter."""
    
    @pytest.mark.parametrize("item_id,expected_status", [
        (1, 200),          # Valid ID
        (0, 404),          # Zero
        (2, 404),          # Not found
        (10, 404),         # Not found
        (999, 404),        # Not found
        (-1, 404),         # Negative
        (-999, 404),       # Large negative
    ])
    def test_get_item_various_ids(self, item_id, expected_status):
        """Test various item_id values."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == expected_status


class TestErrorResponseConsistency:
    """Test that error responses follow consistent structure."""
    
    def test_404_errors_have_consistent_structure(self):
        """Test all 404 errors have the same structure."""
        endpoints_to_test = [
            "/items/0",
            "/items/2",
            "/items/999",
            "/items/-1",
        ]
        
        for endpoint in endpoints_to_test:
            r = client.get(endpoint)
            assert r.status_code == 404, f"Failed for {endpoint}"
            assert "detail" in r.json(), f"No detail in {endpoint}"
            assert r.json()["detail"] == "not found", f"Wrong message in {endpoint}"
    
    def test_400_errors_have_consistent_structure(self):
        """Test all 400 errors have the same structure."""
        invalid_prices = [0, -1, -10.5, -999]
        
        for price in invalid_prices:
            r = client.post("/items", json={"name": "test", "price": price})
            assert r.status_code == 400, f"Failed for price {price}"
            assert "detail" in r.json(), f"No detail for price {price}"
            assert r.json()["detail"] == "price must be > 0", f"Wrong message for price {price}"


class TestConcurrentRequests:
    """Test behavior with multiple requests."""
    
    def test_multiple_get_requests(self):
        """Test that multiple GET requests work independently."""
        responses = [client.get("/items/1") for _ in range(5)]
        
        for r in responses:
            assert r.status_code == 200
            assert r.json()["id"] == 1
    
    def test_mixed_requests_sequence(self):
        """Test a sequence of mixed operations."""
        # Create
        r1 = client.post("/items", json={"name": "item1", "price": 10.0})
        assert r1.status_code == 200
        
        # Get valid
        r2 = client.get("/items/1")
        assert r2.status_code == 200
        
        # Get invalid
        r3 = client.get("/items/999")
        assert r3.status_code == 404
        
        # Create with invalid price
        r4 = client.post("/items", json={"name": "item2", "price": -5})
        assert r4.status_code == 400
        
        # Health check
        r5 = client.get("/health")
        assert r5.status_code == 200
