"""Path parameter and integration edge case tests for items endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test path parameter validation for get item endpoint."""

    @pytest.mark.parametrize("item_id,expected_status", [
        (1, 200),       # Valid single digit
        (10, 404),      # Valid multi-digit but not found
        (100, 404),     # Large valid ID
        (999999, 404),  # Very large valid ID
        (0, 404),       # Zero as ID
        (-1, 404),      # Negative ID
        (-999, 404),    # Large negative ID
    ])
    def test_get_item_path_parameter_boundaries(self, item_id, expected_status):
        """Test various path parameter values."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == expected_status

    def test_get_item_id_zero(self):
        """Test explicitly that ID 0 is not found."""
        r = client.get("/items/0")
        assert r.status_code == 404

    def test_get_item_id_negative(self):
        """Test explicitly that negative IDs are not found."""
        r = client.get("/items/-5")
        assert r.status_code == 404

    def test_get_item_very_large_id(self):
        """Test very large ID value."""
        r = client.get("/items/999999999")
        assert r.status_code == 404

    def test_get_item_max_int_id(self):
        """Test maximum integer value as ID."""
        import sys
        max_int = sys.maxsize
        r = client.get(f"/items/{max_int}")
        assert r.status_code == 404


class TestGetItemInvalidPathParameters:
    """Test invalid path parameter formats."""

    def test_get_item_string_id(self):
        """Test non-numeric string as ID."""
        r = client.get("/items/abc")
        assert r.status_code == 422

    def test_get_item_float_id(self):
        """Test float as ID (may fail parsing)."""
        r = client.get("/items/1.5")
        # Depends on FastAPI path parameter parsing
        assert r.status_code in [404, 422]

    def test_get_item_special_chars_in_id(self):
        """Test special characters in ID."""
        r = client.get("/items/1@2")
        assert r.status_code == 422

    def test_get_item_space_in_id(self):
        """Test space in ID."""
        r = client.get("/items/1 2")
        assert r.status_code == 422

    def test_get_item_comma_separated_ids(self):
        """Test comma-separated IDs."""
        r = client.get("/items/1,2")
        assert r.status_code == 422

    def test_get_item_empty_id(self):
        """Test with empty ID."""
        r = client.get("/items/")
        # FastAPI routes this to a different handler
        assert r.status_code in [307, 404]


class TestMultipleItemOperations:
    """Test multiple item operations in sequence."""

    def test_create_multiple_items_sequentially(self):
        """Test creating multiple items one after another."""
        items = [
            {"name": "item1", "price": 10.0},
            {"name": "item2", "price": 20.0},
            {"name": "item3", "price": 30.0},
        ]
        
        created_ids = []
        for item in items:
            r = client.post("/items", json=item)
            assert r.status_code == 200
            created_ids.append(r.json()["id"])
        
        # Verify all items were created
        assert len(created_ids) == 3

    def test_create_and_get_same_item_twice(self):
        """Test creating and retrieving the same item ID twice."""
        # Create an item
        create_r = client.post("/items", json={"name": "test", "price": 15.0})
        assert create_r.status_code == 200
        item_id = create_r.json()["id"]
        
        # Get it twice
        get_r1 = client.get(f"/items/{item_id}")
        assert get_r1.status_code == 200
        
        get_r2 = client.get(f"/items/{item_id}")
        assert get_r2.status_code == 200
        
        # Both should return same data
        assert get_r1.json() == get_r2.json()

    def test_interleaved_create_and_get_operations(self):
        """Test interleaved create and get operations."""
        # Create item 1
        create1 = client.post("/items", json={"name": "first", "price": 10.0})
        id1 = create1.json()["id"]
        
        # Get item 1
        get1 = client.get(f"/items/{id1}")
        assert get1.status_code == 200
        
        # Create item 2
        create2 = client.post("/items", json={"name": "second", "price": 20.0})
        id2 = create2.json()["id"]
        
        # Get item 1 again
        get1_again = client.get(f"/items/{id1}")
        assert get1_again.status_code == 200
        
        # Get item 2
        get2 = client.get(f"/items/{id2}")
        assert get2.status_code == 200


class TestCreateItemVariations:
    """Test various creation patterns and combinations."""

    def test_create_items_with_same_name_different_prices(self):
        """Test creating multiple items with same name but different prices."""
        names_and_prices = [
            ("book", 10.0),
            ("book", 15.0),
            ("book", 20.0),
        ]
        
        results = []
        for name, price in names_and_prices:
            r = client.post("/items", json={"name": name, "price": price})
            assert r.status_code == 200
            results.append(r.json())
        
        # All should have same name but different prices
        for i, result in enumerate(results):
            assert result["name"] == "book"
            assert result["price"] == names_and_prices[i][1]

    def test_create_items_with_same_price_different_names(self):
        """Test creating multiple items with same price but different names."""
        names_and_prices = [
            ("apple", 10.0),
            ("banana", 10.0),
            ("cherry", 10.0),
        ]
        
        results = []
        for name, price in names_and_prices:
            r = client.post("/items", json={"name": name, "price": price})
            assert r.status_code == 200
            results.append(r.json())
        
        # All should have same price but different names
        for i, result in enumerate(results):
            assert result["price"] == 10.0
            assert result["name"] == names_and_prices[i][0]

    def test_create_items_with_extreme_values(self):
        """Test creating items with extreme but valid values."""
        extreme_items = [
            {"name": "x" * 10000, "price": 1e-10},    # Very long name, tiny price
            {"name": "y", "price": 1e10},              # Very short name, huge price
            {"name": "z" * 5000, "price": 999999.99}, # Long name, large price
        ]
        
        for item in extreme_items:
            r = client.post("/items", json=item)
            assert r.status_code == 200
            assert r.json()["name"] == item["name"]
            assert r.json()["price"] == item["price"]


class TestGetItemBoundaryValues:
    """Test boundary conditions in get item operations."""

    @pytest.mark.parametrize("item_id", [1, 2, 999, 1000000])
    def test_get_item_various_ids_consistency(self, item_id):
        """Test getting various IDs returns consistent response format."""
        r = client.get(f"/items/{item_id}")
        # All should return 404 except for 1 which returns 200
        if item_id == 1:
            assert r.status_code == 200
        else:
            assert r.status_code == 404
        
        # All should return JSON with detail field
        data = r.json()
        assert isinstance(data, dict)

    def test_get_item_id_boundary_just_before_found(self):
        """Test ID just before the found ID."""
        r = client.get("/items/0")
        assert r.status_code == 404
        assert "not found" in r.json()["detail"]

    def test_get_item_id_boundary_just_after_found(self):
        """Test ID just after the found ID."""
        r = client.get("/items/2")
        assert r.status_code == 404
        assert "not found" in r.json()["detail"]


class TestEndToEndScenarios:
    """Test end-to-end workflow scenarios."""

    def test_complete_workflow_create_and_retrieve(self):
        """Test complete workflow: create item and retrieve it."""
        # Step 1: Verify health
        health_r = client.get("/health")
        assert health_r.status_code == 200
        
        # Step 2: Create item
        create_r = client.post("/items", json={
            "name": "integration_test_item",
            "price": 42.50
        })
        assert create_r.status_code == 200
        item_id = create_r.json()["id"]
        
        # Step 3: Retrieve created item
        get_r = client.get(f"/items/{item_id}")
        assert get_r.status_code == 200
        
        # Step 4: Verify data integrity
        item = get_r.json()
        assert item["id"] == item_id
        assert item["name"] == "integration_test_item"
        assert item["price"] == 42.50

    def test_workflow_multiple_creates_followed_by_retrieval(self):
        """Test creating multiple items then retrieving them."""
        # Create multiple items
        items_to_create = [
            {"name": "laptop", "price": 999.99},
            {"name": "mouse", "price": 25.00},
            {"name": "keyboard", "price": 75.50},
        ]
        
        created_items = []
        for item_data in items_to_create:
            r = client.post("/items", json=item_data)
            assert r.status_code == 200
            created_items.append(r.json())
        
        # Retrieve all created items
        for created_item in created_items:
            r = client.get(f"/items/{created_item['id']}")
            assert r.status_code == 200

    def test_error_recovery_workflow(self):
        """Test that system recovers from errors."""
        # First, cause an error
        error_r = client.post("/items", json={"name": "test", "price": -5})
        assert error_r.status_code == 400
        
        # Then create a valid item (should work despite previous error)
        valid_r = client.post("/items", json={"name": "recovery", "price": 10.0})
        assert valid_r.status_code == 200
        item_id = valid_r.json()["id"]
        
        # Retrieve the valid item
        get_r = client.get(f"/items/{item_id}")
        assert get_r.status_code == 200
        assert get_r.json()["name"] == "recovery"


class TestRequestResponseRoundTrip:
    """Test request-response round trip scenarios."""

    def test_create_request_data_matches_response_exactly(self):
        """Test that all sent data appears in response."""
        request_data = {
            "name": "test_product",
            "price": 123.45
        }
        
        r = client.post("/items", json=request_data)
        assert r.status_code == 200
        response_data = r.json()
        
        # Check all request fields in response
        assert response_data["name"] == request_data["name"]
        assert response_data["price"] == request_data["price"]

    def test_create_get_round_trip_preserves_data(self):
        """Test that creating and getting preserves all data."""
        original_data = {
            "name": "delicate_item",
            "price": 99.99
        }
        
        # Create
        create_r = client.post("/items", json=original_data)
        assert create_r.status_code == 200
        created = create_r.json()
        
        # Get
        get_r = client.get(f"/items/{created['id']}")
        assert get_r.status_code == 200
        retrieved = get_r.json()
        
        # Compare original request with retrieved data
        assert retrieved["name"] == original_data["name"]
        assert retrieved["price"] == original_data["price"]

    @pytest.mark.parametrize("name,price", [
        ("item1", 10.0),
        ("item2", 25.50),
        ("special_item", 99.99),
    ])
    def test_create_get_round_trip_parametrized(self, name, price):
        """Test round trip with parametrized data."""
        # Create
        create_r = client.post("/items", json={"name": name, "price": price})
        assert create_r.status_code == 200
        item_id = create_r.json()["id"]
        
        # Get
        get_r = client.get(f"/items/{item_id}")
        assert get_r.status_code == 200
        
        # Verify
        assert get_r.json()["name"] == name
        assert get_r.json()["price"] == price


class TestConcurrentScenarios:
    """Test scenarios that might occur in concurrent usage."""

    def test_multiple_creates_in_sequence(self):
        """Test that multiple sequential creates work correctly."""
        num_items = 10
        
        for i in range(num_items):
            r = client.post("/items", json={
                "name": f"item_{i}",
                "price": float(10 + i)
            })
            assert r.status_code == 200
            assert r.json()["price"] == float(10 + i)

    def test_create_with_all_boundary_prices(self):
        """Test creating items with all boundary prices."""
        boundary_prices = [
            0.001,      # Very small
            0.01,       # Small
            1.0,        # Unit
            10.0,       # Standard
            100.0,      # Large
            1000.0,     # Very large
            10000.0,    # Huge
        ]
        
        for price in boundary_prices:
            r = client.post("/items", json={"name": "boundary_item", "price": price})
            assert r.status_code == 200
            assert r.json()["price"] == price

    def test_alternating_valid_invalid_requests(self):
        """Test alternating between valid and invalid requests."""
        requests_sequence = [
            ("POST", "/items", {"name": "valid1", "price": 10.0}, 200),
            ("POST", "/items", {"name": "invalid", "price": -5}, 400),
            ("POST", "/items", {"name": "valid2", "price": 20.0}, 200),
            ("GET", "/items/999", None, 404),
            ("POST", "/items", {"name": "valid3", "price": 30.0}, 200),
            ("GET", "/items/1", None, 200),
        ]
        
        for method, path, data, expected_status in requests_sequence:
            if method == "POST":
                r = client.post(path, json=data)
            else:
                r = client.get(path)
            
            assert r.status_code == expected_status


class TestIntegrationWithValidation:
    """Test integration between validation and response endpoints."""

    def test_validation_error_doesnt_affect_valid_requests(self):
        """Test that validation error doesn't break subsequent valid requests."""
        # Cause validation error (missing field)
        error_r = client.post("/items", json={"name": "test"})
        assert error_r.status_code == 422
        
        # Valid request should still work
        valid_r = client.post("/items", json={"name": "valid", "price": 10.0})
        assert valid_r.status_code == 200

    def test_business_logic_error_doesnt_affect_valid_requests(self):
        """Test that business logic error doesn't affect valid requests."""
        # Cause business logic error (negative price)
        error_r = client.post("/items", json={"name": "test", "price": -10})
        assert error_r.status_code == 400
        
        # Valid request should work
        valid_r = client.post("/items", json={"name": "valid", "price": 10.0})
        assert valid_r.status_code == 200

    def test_not_found_error_with_subsequent_valid_gets(self):
        """Test that not found error doesn't affect valid retrieval."""
        # Try to get non-existent item
        not_found_r = client.get("/items/99999")
        assert not_found_r.status_code == 404
        
        # Valid retrieval should work
        valid_r = client.get("/items/1")
        assert valid_r.status_code == 200
