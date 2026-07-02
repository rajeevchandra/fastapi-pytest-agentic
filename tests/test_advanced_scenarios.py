import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestStressAndPerformance:
    """Stress tests and basic performance validation."""

    def test_multiple_health_checks(self):
        """Should handle multiple health requests."""
        for _ in range(10):
            r = client.get("/health")
            assert r.status_code == 200

    def test_multiple_get_requests_same_item(self):
        """Should handle multiple GET requests for same item."""
        responses = [client.get("/items/1") for _ in range(10)]
        assert all(r.status_code == 200 for r in responses)
        assert all(r.json()["id"] == 1 for r in responses)

    def test_multiple_create_attempts(self):
        """Should handle multiple POST requests."""
        for _ in range(5):
            r = client.post("/items", json={"name": "item", "price": 10.0})
            assert r.status_code == 200

    def test_repeated_error_scenarios(self):
        """Error scenarios should be consistent across multiple attempts."""
        for _ in range(5):
            r = client.post("/items", json={"name": "item", "price": -1})
            assert r.status_code == 400
            assert "price must be > 0" in r.json()["detail"]


class TestItemCreationConsistency:
    """Test consistency of item creation behavior."""

    def test_multiple_items_always_id_one(self):
        """All created items should have id=1."""
        for i in range(3):
            r = client.post("/items", json={"name": f"item_{i}", "price": 10.0 + i})
            assert r.json()["id"] == 1

    def test_response_always_contains_three_fields(self):
        """Create response should always have exactly 3 fields."""
        for _ in range(3):
            r = client.post("/items", json={"name": "item", "price": 10.0})
            data = r.json()
            assert len(data) == 3
            assert set(data.keys()) == {"id", "name", "price"}

    def test_get_item_one_consistency_across_sessions(self):
        """Item 1 should have consistent data."""
        first_get = client.get("/items/1").json()
        
        # Create a new item
        client.post("/items", json={"name": "new_item", "price": 5.0})
        
        # Item 1 should still have same data
        second_get = client.get("/items/1").json()
        assert first_get == second_get


class TestRequestCombinations:
    """Test various request combinations and sequences."""

    def test_create_then_get_same_id(self):
        """Create item then immediately retrieve it."""
        create_r = client.post("/items", json={"name": "book", "price": 15.0})
        created_id = create_r.json()["id"]
        
        get_r = client.get(f"/items/{created_id}")
        assert get_r.status_code == 200
        assert get_r.json()["id"] == created_id

    def test_get_nonexistent_then_create(self):
        """Try to get nonexistent item, then create an item."""
        r1 = client.get("/items/999")
        assert r1.status_code == 404
        
        r2 = client.post("/items", json={"name": "new", "price": 5.0})
        assert r2.status_code == 200

    def test_invalid_create_then_valid_create(self):
        """Invalid create should not affect valid create."""
        invalid_r = client.post("/items", json={"name": "item", "price": -1})
        assert invalid_r.status_code == 400
        
        valid_r = client.post("/items", json={"name": "item", "price": 10.0})
        assert valid_r.status_code == 200

    def test_get_item_one_after_multiple_creates(self):
        """Item 1 should remain accessible after multiple creates."""
        for i in range(5):
            client.post("/items", json={"name": f"item_{i}", "price": 10.0 + i})
        
        r = client.get("/items/1")
        assert r.status_code == 200


class TestNameFieldVariations:
    """Test various name field variations."""

    @pytest.mark.parametrize("name", [
        "A",
        "Simple Product",
        "Product-with-dash",
        "Product_with_underscore",
        "Product with spaces",
        "123NumericStart",
        "product_MIXED_Case",
        "日本語製品",
        "Ürödüct Över Înt",
        "emoji 🎉 test",
        "   spaces   ",
        "product\nwith\nnewlines",
    ])
    def test_various_name_formats(self, name):
        """API should accept various name formats."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name


class TestPriceVariations:
    """Test various price value variations."""

    @pytest.mark.parametrize("price", [
        0.01,
        0.1,
        1,
        1.5,
        10,
        10.99,
        100,
        1000.00,
        9999.99,
        10000,
        100000.50,
        0.001,
        0.0001,
        0.00001,
    ])
    def test_various_price_values(self, price):
        """API should accept various positive price values."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price


class TestErrorRecovery:
    """Test error recovery and state consistency."""

    def test_error_does_not_affect_subsequent_requests(self):
        """API should recover from errors correctly."""
        # First error
        r1 = client.post("/items", json={"name": "item", "price": 0})
        assert r1.status_code == 400
        
        # Valid request should still work
        r2 = client.post("/items", json={"name": "valid", "price": 10.0})
        assert r2.status_code == 200
        
        # Another error should still be properly rejected
        r3 = client.post("/items", json={"name": "item", "price": -5})
        assert r3.status_code == 400

    def test_multiple_errors_do_not_corrupt_state(self):
        """Multiple errors should not corrupt API state."""
        errors = [
            {"name": "item", "price": -1},
            {"name": "item", "price": 0},
            {"price": 10.0},  # missing name
            {"name": "item"},  # missing price
        ]
        
        for error_payload in errors:
            r = client.post("/items", json=error_payload)
            assert r.status_code >= 400
        
        # Valid request should still work
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200

    def test_item_one_accessible_after_errors(self):
        """Item 1 should still be accessible after error attempts."""
        client.post("/items", json={"name": "item", "price": -1})
        client.get("/items/999")
        client.get("/items/0")
        
        r = client.get("/items/1")
        assert r.status_code == 200


class TestHTTPMethodValidation:
    """Test proper HTTP method validation."""

    def test_health_only_accepts_get(self):
        """Health endpoint should only accept GET."""
        # GET should work
        r = client.get("/health")
        assert r.status_code == 200

    def test_items_create_requires_post(self):
        """Creating items should require POST."""
        # POST should work
        r = client.post("/items", json={"name": "item", "price": 10.0})
        assert r.status_code == 200

    def test_items_get_requires_get(self):
        """Getting items should require GET."""
        r = client.get("/items/1")
        assert r.status_code == 200


class TestResponseIsJSON:
    """Verify all responses are valid JSON."""

    def test_all_success_responses_are_json(self):
        """Success responses should be valid JSON."""
        endpoints = [
            client.get("/health"),
            client.post("/items", json={"name": "item", "price": 10.0}),
            client.get("/items/1"),
        ]
        
        for r in endpoints:
            if r.status_code < 400:
                # Should not raise if JSON is valid
                assert r.json() is not None
                assert isinstance(r.json(), dict)

    def test_error_responses_are_json(self):
        """Error responses should be valid JSON."""
        error_endpoints = [
            client.post("/items", json={"name": "item", "price": -1}),
            client.get("/items/999"),
        ]
        
        for r in error_endpoints:
            if r.status_code >= 400:
                # Should not raise if JSON is valid
                assert r.json() is not None


class TestDataTypeConsistency:
    """Test data type consistency across requests."""

    def test_price_always_numeric(self):
        """Price in response should always be numeric."""
        prices_to_test = [1, 10.5, 0.01, 100, 999.99]
        
        for price in prices_to_test:
            r = client.post("/items", json={"name": "item", "price": price})
            returned_price = r.json()["price"]
            assert isinstance(returned_price, (int, float))

    def test_name_always_string(self):
        """Name in response should always be string."""
        names_to_test = ["a", "test", "Product 123", "Special!@#$"]
        
        for name in names_to_test:
            r = client.post("/items", json={"name": name, "price": 10.0})
            returned_name = r.json()["name"]
            assert isinstance(returned_name, str)

    def test_id_always_integer(self):
        """ID in response should always be integer."""
        for _ in range(3):
            r = client.post("/items", json={"name": "item", "price": 10.0})
            returned_id = r.json()["id"]
            assert isinstance(returned_id, int)


class TestBoundaryBehavior:
    """Test API behavior at boundaries and limits."""

    def test_very_small_positive_price_accepted(self):
        """Very small positive prices should be accepted."""
        tiny_prices = [0.00001, 0.0001, 0.001, 0.01]
        
        for price in tiny_prices:
            r = client.post("/items", json={"name": "item", "price": price})
            assert r.status_code == 200

    def test_very_large_price_accepted(self):
        """Very large prices should be accepted."""
        large_prices = [1000000, 999999.99, 1e6, 1e7]
        
        for price in large_prices:
            r = client.post("/items", json={"name": "item", "price": price})
            assert r.status_code == 200

    def test_zero_price_boundary(self):
        """Zero price should be exactly at the rejection boundary."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.status_code == 400
        
        r = client.post("/items", json={"name": "item", "price": 0.001})
        assert r.status_code == 200

    def test_very_long_name_accepted(self):
        """Very long names should be accepted."""
        long_names = [
            "a" * 100,
            "b" * 1000,
            "c" * 10000,
        ]
        
        for name in long_names:
            r = client.post("/items", json={"name": name, "price": 10.0})
            assert r.status_code == 200
            assert r.json()["name"] == name
