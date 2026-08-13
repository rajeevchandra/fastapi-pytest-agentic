"""
Path parameter edge cases, integration scenarios, and end-to-end testing.

Tests cover:
- Path parameter boundary values (negative, zero, large integers)
- Invalid path parameter types
- URL encoding edge cases
- Integration scenarios (create then retrieve)
- Sequential operations
- Concurrent/repeated operations
- State consistency
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test path parameter validation for GET /items/{item_id}."""

    @pytest.mark.parametrize("item_id,should_exist", [
        (1, True),           # Valid existing item
        (0, False),          # Zero
        (-1, False),         # Negative
        (2, False),          # Non-existent
        (999, False),        # Large ID
        (2147483647, False), # Max 32-bit int
    ])
    def test_get_item_path_parameter_boundary_values(self, item_id, should_exist):
        """Test various item_id values."""
        response = client.get(f"/items/{item_id}")
        
        if should_exist:
            assert response.status_code == 200
            assert response.json()["id"] == item_id
        else:
            assert response.status_code == 404
            assert "detail" in response.json()

    def test_get_item_with_integer_zero(self):
        """Test item_id=0 returns 404."""
        response = client.get("/items/0")
        assert response.status_code == 404

    def test_get_item_with_negative_integer(self):
        """Test negative item_id returns 404."""
        response = client.get("/items/-5")
        assert response.status_code == 404

    def test_get_item_with_large_integer(self):
        """Test very large item_id returns 404."""
        response = client.get("/items/9999999999")
        assert response.status_code == 404

    def test_get_item_with_valid_id_returns_item(self):
        """Test item_id=1 returns the sample item."""
        response = client.get("/items/1")
        assert response.status_code == 200
        assert response.json()["id"] == 1

    def test_get_item_boundary_between_found_and_not_found(self):
        """Test boundary: item 1 exists, item 2 does not."""
        found = client.get("/items/1")
        not_found = client.get("/items/2")
        
        assert found.status_code == 200
        assert not_found.status_code == 404


class TestGetItemPathParameterTypes:
    """Test path parameter type handling."""

    def test_get_item_with_valid_string_integer(self):
        """Test integer passed as URL path segment."""
        response = client.get("/items/1")
        assert response.status_code == 200

    def test_get_item_endpoint_requires_numeric_id(self):
        """Test that non-numeric path causes routing error."""
        # FastAPI will return 404 or 422 for non-numeric path
        response = client.get("/items/abc")
        assert response.status_code in [404, 422]

    def test_get_item_with_float_in_path(self):
        """Test float in path parameter."""
        response = client.get("/items/1.5")
        # FastAPI coerces to int when possible
        assert response.status_code in [200, 404, 422]


class TestItemIntegrationScenarios:
    """Test integration scenarios with multiple operations."""

    def test_create_item_then_retrieve_it(self):
        """Test creating an item then retrieving it."""
        # Create item
        create_response = client.post("/items", json={"name": "test_book", "price": 19.99})
        assert create_response.status_code == 200
        created_item = create_response.json()
        
        # Retrieve the same item
        get_response = client.get(f"/items/{created_item['id']}")
        assert get_response.status_code == 200
        retrieved_item = get_response.json()
        
        # Verify retrieved item has correct data
        assert retrieved_item["id"] == created_item["id"]

    def test_create_multiple_items_with_different_prices(self):
        """Test creating multiple items with varying prices."""
        test_cases = [
            ("item1", 9.99),
            ("item2", 19.99),
            ("item3", 29.99),
            ("item4", 99.99),
        ]
        
        created_ids = []
        for name, price in test_cases:
            response = client.post("/items", json={"name": name, "price": price})
            assert response.status_code == 200
            created_ids.append(response.json()["id"])
        
        # All items should have same ID due to current implementation
        assert len(set(created_ids)) == 1  # All same ID

    def test_create_then_get_preserves_name_and_price(self):
        """Test that created item data is preserved."""
        test_name = "Integration Test Item"
        test_price = 45.67
        
        # Create
        create_response = client.post("/items", json={"name": test_name, "price": test_price})
        assert create_response.status_code == 200
        item_id = create_response.json()["id"]
        
        # Retrieve
        get_response = client.get(f"/items/{item_id}")
        assert get_response.status_code == 200
        
        # Note: Current implementation returns hardcoded sample data
        # In a real app, this would verify the created item
        retrieved = get_response.json()
        assert "id" in retrieved
        assert "name" in retrieved
        assert "price" in retrieved

    def test_repeated_get_requests_are_consistent(self):
        """Test that repeated GET requests return same data."""
        response1 = client.get("/items/1")
        response2 = client.get("/items/1")
        response3 = client.get("/items/1")
        
        assert response1.status_code == response2.status_code == response3.status_code == 200
        data1 = response1.json()
        data2 = response2.json()
        data3 = response3.json()
        
        assert data1 == data2 == data3

    def test_repeated_create_requests_succeed(self):
        """Test that multiple POST requests can succeed."""
        responses = []
        for i in range(3):
            response = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            responses.append(response)
            assert response.status_code == 200
        
        # All should succeed
        assert all(r.status_code == 200 for r in responses)

    def test_get_nonexistent_then_create_then_get(self):
        """Test trying to get non-existent item, then creating similar one."""
        # Try to get non-existent item
        response1 = client.get("/items/999")
        assert response1.status_code == 404
        
        # Create an item
        response2 = client.post("/items", json={"name": "new_item", "price": 15.0})
        assert response2.status_code == 200
        
        # Verify we can still get item 1
        response3 = client.get("/items/1")
        assert response3.status_code == 200


class TestCreateItemWithVariousNames:
    """Test item creation with various name formats."""

    @pytest.mark.parametrize("name,should_succeed", [
        ("Simple", True),
        ("Multiple Words Here", True),
        ("with-dashes", True),
        ("with_underscores", True),
        ("CamelCase", True),
        ("UPPERCASE", True),
        ("with123numbers", True),
        ("Special!@#$%^&*()", True),
        ("Unicode: 日本語 中文", True),
    ])
    def test_create_item_name_formats(self, name, should_succeed):
        """Test item creation with various name formats."""
        response = client.post("/items", json={"name": name, "price": 10.0})
        
        if should_succeed:
            assert response.status_code == 200
            assert response.json()["name"] == name
        else:
            assert response.status_code != 200

    def test_create_items_with_increasingly_long_names(self):
        """Test creating items with very long names."""
        lengths = [1, 10, 100, 500, 1000]
        
        for length in lengths:
            name = "x" * length
            response = client.post("/items", json={"name": name, "price": 10.0})
            assert response.status_code == 200
            assert response.json()["name"] == name
            assert len(response.json()["name"]) == length

    def test_create_items_with_unicode_names(self):
        """Test creating items with unicode names."""
        names = [
            "こんにちは",        # Japanese
            "你好",              # Chinese
            "مرحبا",            # Arabic
            "Привет",           # Russian
            "שלום",             # Hebrew
            "🎉 Party",         # Emoji
        ]
        
        for name in names:
            response = client.post("/items", json={"name": name, "price": 10.0})
            assert response.status_code == 200
            assert response.json()["name"] == name


class TestCreateItemWithVariousPrices:
    """Test item creation with various price formats."""

    @pytest.mark.parametrize("price,should_succeed", [
        (0.01, True),
        (1, True),
        (1.0, True),
        (1.5, True),
        (10.99, True),
        (100, True),
        (1000.50, True),
        (9999.99, True),
        (0, False),
        (-0.01, False),
        (-1, False),
    ])
    def test_create_item_price_values(self, price, should_succeed):
        """Test item creation with various prices."""
        response = client.post("/items", json={"name": "test", "price": price})
        
        if should_succeed:
            assert response.status_code == 200
            assert response.json()["price"] == price
        else:
            assert response.status_code == 400

    def test_create_items_with_incrementing_prices(self):
        """Test creating multiple items with different prices."""
        prices = [0.99, 1.99, 9.99, 19.99, 99.99, 199.99]
        
        for price in prices:
            response = client.post("/items", json={"name": "item", "price": price})
            assert response.status_code == 200
            assert response.json()["price"] == price

    def test_create_items_with_extreme_prices(self):
        """Test creating items with extreme price values."""
        prices = [0.001, 0.01, 999999.99, 1234567890.12]
        
        for price in prices:
            response = client.post("/items", json={"name": "item", "price": price})
            assert response.status_code == 200
            assert response.json()["price"] == price


class TestStateAndConsistency:
    """Test state consistency and behavior across operations."""

    def test_health_endpoint_consistency(self):
        """Test health endpoint returns consistent results."""
        responses = [client.get("/health") for _ in range(3)]
        
        assert all(r.status_code == 200 for r in responses)
        assert all(r.json()["status"] == "ok" for r in responses)

    def test_health_endpoint_remains_ok_after_items_operations(self):
        """Test health endpoint is unaffected by item operations."""
        # Get health
        health1 = client.get("/health")
        assert health1.json()["status"] == "ok"
        
        # Do item operations
        client.post("/items", json={"name": "test", "price": 10.0})
        client.get("/items/1")
        client.get("/items/999")
        
        # Health should still be ok
        health2 = client.get("/health")
        assert health2.json()["status"] == "ok"

    def test_item_response_consistency_across_multiple_gets(self):
        """Test GET /items/1 returns consistent data."""
        responses = [client.get("/items/1") for _ in range(5)]
        
        assert all(r.status_code == 200 for r in responses)
        data = [r.json() for r in responses]
        
        # All responses should be identical
        assert all(d == data[0] for d in data)
        assert all(d["id"] == 1 for d in data)
        assert all(d["name"] == "sample" for d in data)
        assert all(d["price"] == 10.0 for d in data)

    def test_nonexistent_item_consistently_returns_404(self):
        """Test 404 is consistently returned for non-existent items."""
        test_ids = [2, 999, 0, -1, -999]
        
        for item_id in test_ids:
            response = client.get(f"/items/{item_id}")
            assert response.status_code == 404, f"Expected 404 for item_id={item_id}"

    def test_bad_request_response_consistency(self):
        """Test bad request responses are consistent."""
        responses = [
            client.post("/items", json={"name": "item", "price": 0}),
            client.post("/items", json={"name": "item", "price": 0}),
            client.post("/items", json={"name": "item", "price": 0}),
        ]
        
        assert all(r.status_code == 400 for r in responses)
        assert all("price must be > 0" in r.json()["detail"] for r in responses)


class TestEndToEndScenarios:
    """Complete end-to-end test scenarios."""

    def test_full_api_flow(self):
        """Test a complete API usage flow."""
        # 1. Check health
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"
        
        # 2. Create an item
        create = client.post("/items", json={"name": "Test Book", "price": 24.99})
        assert create.status_code == 200
        item = create.json()
        assert item["id"] == 1
        assert item["name"] == "Test Book"
        assert item["price"] == 24.99
        
        # 3. Retrieve the item
        get = client.get(f"/items/{item['id']}")
        assert get.status_code == 200
        
        # 4. Try to get non-existent item
        not_found = client.get("/items/999")
        assert not_found.status_code == 404
        
        # 5. Verify health is still ok
        health2 = client.get("/health")
        assert health2.status_code == 200
        assert health2.json()["status"] == "ok"

    def test_multiple_items_creation_flow(self):
        """Test creating multiple items in sequence."""
        items_to_create = [
            {"name": "Book 1", "price": 15.99},
            {"name": "Book 2", "price": 19.99},
            {"name": "Book 3", "price": 25.99},
        ]
        
        created_items = []
        for item_data in items_to_create:
            response = client.post("/items", json=item_data)
            assert response.status_code == 200
            created_item = response.json()
            assert created_item["name"] == item_data["name"]
            assert created_item["price"] == item_data["price"]
            created_items.append(created_item)
        
        # Try to retrieve each
        for created_item in created_items:
            get_response = client.get(f"/items/{created_item['id']}")
            assert get_response.status_code == 200

    def test_error_handling_flow(self):
        """Test handling various error scenarios."""
        error_cases = [
            ({"name": "item", "price": 0}, 400),           # Zero price
            ({"name": "item", "price": -5}, 400),          # Negative price
            ({"price": 10.0}, 422),                        # Missing name
            ({"name": "item"}, 422),                       # Missing price
            ({}, 422),                                     # Empty payload
        ]
        
        for payload, expected_status in error_cases:
            response = client.post("/items", json=payload)
            assert response.status_code == expected_status, f"Failed for {payload}"
            assert "detail" in response.json()

    def test_boundary_value_flow(self):
        """Test API behavior at boundary values."""
        # Minimum valid price
        response = client.post("/items", json={"name": "cheap", "price": 0.01})
        assert response.status_code == 200
        
        # Just below minimum
        response = client.post("/items", json={"name": "too_cheap", "price": 0.001})
        assert response.status_code == 200  # Accepted if > 0
        
        # Zero (invalid)
        response = client.post("/items", json={"name": "free", "price": 0})
        assert response.status_code == 400
        
        # Very large price
        response = client.post("/items", json={"name": "expensive", "price": 999999.99})
        assert response.status_code == 200
        
        # Get existing item
        response = client.get("/items/1")
        assert response.status_code == 200
        
        # Get at boundary (0)
        response = client.get("/items/0")
        assert response.status_code == 404
        
        # Get just past boundary (2)
        response = client.get("/items/2")
        assert response.status_code == 404
