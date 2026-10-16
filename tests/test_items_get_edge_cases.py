"""Path parameter edge cases and integration tests for /items endpoint."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterBoundaries:
    """Test path parameter edge cases for item_id."""

    @pytest.mark.parametrize("item_id", [-1, -100, -999999])
    def test_get_item_negative_id_not_found(self, item_id):
        """Test that negative item IDs return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        assert "not found" in r.json()["detail"]

    def test_get_item_zero_id_not_found(self):
        """Test that item_id=0 returns 404."""
        r = client.get("/items/0")
        assert r.status_code == 404

    def test_get_item_only_id_1_found(self):
        """Test that only item_id=1 is available."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["id"] == 1

    @pytest.mark.parametrize("item_id", [2, 3, 100, 1000, 999999])
    def test_get_item_other_positive_ids_not_found(self, item_id):
        """Test that item IDs other than 1 return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    def test_get_item_very_large_id_not_found(self):
        """Test that very large item IDs return 404."""
        r = client.get(f"/items/{2**31 - 1}")
        assert r.status_code == 404

    def test_get_item_float_id_handling(self):
        """Test handling of float in path parameter."""
        # FastAPI converts to int or rejects
        r = client.get("/items/1.5")
        # Path parameter conversion may fail or succeed
        assert r.status_code in [200, 422, 404]


class TestGetItemMultipleRequests:
    """Test multiple sequential requests."""

    def test_get_item_multiple_requests_consistency(self):
        """Test that multiple requests for same item return consistent data."""
        data_list = []
        for _ in range(3):
            r = client.get("/items/1")
            assert r.status_code == 200
            data_list.append(r.json())
        
        # All responses should be identical
        assert data_list[0] == data_list[1] == data_list[2]

    def test_get_item_interleaved_requests(self):
        """Test interleaved requests for found and not found items."""
        r1 = client.get("/items/1")
        r2 = client.get("/items/2")
        r3 = client.get("/items/1")
        r4 = client.get("/items/3")
        
        assert r1.status_code == 200
        assert r2.status_code == 404
        assert r3.status_code == 200
        assert r4.status_code == 404
        
        # Found items should return same data
        assert r1.json() == r3.json()


class TestCreateItemMultipleOperations:
    """Test multiple item creation operations."""

    def test_create_multiple_items_returns_same_id(self):
        """Test that multiple creates return consistent ID."""
        ids = []
        for i in range(3):
            r = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            assert r.status_code == 200
            ids.append(r.json()["id"])
        
        # All should have same ID (API limitation - only 1 item stored)
        assert ids[0] == ids[1] == ids[2]

    def test_create_and_retrieve_item(self):
        """Test create followed by retrieve operation."""
        # Create an item
        create_r = client.post("/items", json={"name": "test_item", "price": 15.0})
        assert create_r.status_code == 200
        created_data = create_r.json()
        
        # Retrieve the same item
        get_r = client.get(f"/items/{created_data['id']}")
        assert get_r.status_code == 200
        retrieved_data = get_r.json()
        
        # IDs should match
        assert created_data["id"] == retrieved_data["id"]


class TestCreateItemEdgeCases:
    """Test edge case scenarios for item creation."""

    def test_create_item_boundary_price_then_get(self):
        """Test create with boundary price then retrieve."""
        r = client.post("/items", json={"name": "boundary_item", "price": 0.01})
        assert r.status_code == 200
        create_data = r.json()
        
        # Verify the item exists
        get_r = client.get(f"/items/{create_data['id']}")
        assert get_r.status_code == 200

    def test_create_item_unicode_name_then_get(self):
        """Test create with unicode name then retrieve."""
        unicode_name = "αβγδ-日本語-emoji🎉"
        r = client.post("/items", json={"name": unicode_name, "price": 20.0})
        assert r.status_code == 200
        create_data = r.json()
        assert create_data["name"] == unicode_name
        
        # Verify retrieval
        get_r = client.get(f"/items/{create_data['id']}")
        assert get_r.status_code == 200
        assert get_r.json()["name"] == unicode_name

    def test_create_item_max_price_then_get(self):
        """Test create with very large price then retrieve."""
        r = client.post("/items", json={"name": "expensive", "price": 999999.99})
        assert r.status_code == 200
        create_data = r.json()
        
        get_r = client.get(f"/items/{create_data['id']}")
        assert get_r.status_code == 200
        assert get_r.json()["price"] == 999999.99


class TestErrorRecovery:
    """Test error scenarios and recovery."""

    def test_invalid_price_doesnt_create_item(self):
        """Test that invalid price doesn't affect subsequent requests."""
        # Attempt with invalid price
        r1 = client.post("/items", json={"name": "bad", "price": -1})
        assert r1.status_code == 400
        
        # Valid request after error should still work
        r2 = client.post("/items", json={"name": "good", "price": 10.0})
        assert r2.status_code == 200

    def test_missing_field_error_doesnt_affect_next_request(self):
        """Test recovery after missing field validation error."""
        # Missing field error
        r1 = client.post("/items", json={"price": 10.0})
        assert r1.status_code == 422
        
        # Valid request after error
        r2 = client.post("/items", json={"name": "item", "price": 10.0})
        assert r2.status_code == 200

    def test_sequential_valid_requests_after_errors(self):
        """Test multiple valid requests after various errors."""
        # Trigger different errors
        errors = [
            {"price": 10.0},  # Missing name - 422
            {"name": "test", "price": 0},  # Invalid price - 400
            {"name": "test"},  # Missing price - 422
        ]
        
        for error_data in errors:
            r = client.post("/items", json=error_data)
            assert r.status_code in [400, 422]
        
        # Now valid request
        r = client.post("/items", json={"name": "valid", "price": 10.0})
        assert r.status_code == 200


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    def test_health_check_then_create_then_get(self):
        """Test health, create, and get sequence."""
        # Health check
        health_r = client.get("/health")
        assert health_r.status_code == 200
        assert health_r.json()["status"] == "ok"
        
        # Create item
        create_r = client.post("/items", json={"name": "seq_item", "price": 25.0})
        assert create_r.status_code == 200
        item_id = create_r.json()["id"]
        
        # Get item
        get_r = client.get(f"/items/{item_id}")
        assert get_r.status_code == 200
        assert get_r.json()["id"] == item_id

    def test_validate_then_create_then_verify(self):
        """Test validation with create and verify flow."""
        test_item = {"name": "validated_item", "price": 35.50}
        
        # Create item
        r = client.post("/items", json=test_item)
        assert r.status_code == 200
        created = r.json()
        
        # Verify response has all expected fields
        assert created["name"] == test_item["name"]
        assert abs(created["price"] - test_item["price"]) < 0.01
        
        # Verify retrieval
        get_r = client.get(f"/items/{created['id']}")
        assert get_r.status_code == 200
        retrieved = get_r.json()
        
        # Verify fields match
        assert created["name"] == retrieved["name"]
        assert abs(created["price"] - retrieved["price"]) < 0.01


class TestAPIConsistency:
    """Test API behavior consistency."""

    def test_create_response_matches_get_response(self):
        """Test that create response has same data structure as get."""
        create_r = client.post("/items", json={"name": "consistency_test", "price": 45.0})
        assert create_r.status_code == 200
        create_data = create_r.json()
        
        get_r = client.get(f"/items/{create_data['id']}")
        assert get_r.status_code == 200
        get_data = get_r.json()
        
        # Both should have same fields
        assert set(create_data.keys()) == set(get_data.keys())

    def test_response_field_consistency_across_requests(self):
        """Test that response fields are consistent across multiple requests."""
        r1 = client.get("/items/1")
        r2 = client.get("/items/1")
        
        data1 = r1.json()
        data2 = r2.json()
        
        # Same field names
        assert set(data1.keys()) == set(data2.keys())
        # Same values
        assert data1 == data2

    def test_error_response_consistency(self):
        """Test that error responses are consistent."""
        # Multiple 404 errors
        errors = []
        for item_id in [2, 3, 4]:
            r = client.get(f"/items/{item_id}")
            assert r.status_code == 404
            errors.append(r.json())
        
        # All should have "not found" in detail
        for error in errors:
            assert "not found" in error["detail"]


class TestPathParameterValidation:
    """Test path parameter validation and edge cases."""

    def test_get_item_valid_int_parameter(self):
        """Test that valid int parameters work."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_get_item_zero_parameter(self):
        """Test that zero parameter is handled."""
        r = client.get("/items/0")
        assert r.status_code == 404

    @pytest.mark.parametrize("item_id", [1, 100, 999, 10000])
    def test_get_item_various_int_values(self, item_id):
        """Test various integer values in path."""
        r = client.get(f"/items/{item_id}")
        # Only 1 should be found
        if item_id == 1:
            assert r.status_code == 200
        else:
            assert r.status_code == 404


class TestCreateItemSequenceBehavior:
    """Test behavior of sequential create operations."""

    def test_create_different_names_same_id(self):
        """Test that creating items with different names returns consistent ID."""
        names = ["item1", "item2", "item3"]
        ids = []
        
        for name in names:
            r = client.post("/items", json={"name": name, "price": 50.0})
            assert r.status_code == 200
            ids.append(r.json()["id"])
        
        # All should return same ID (API constraint)
        assert len(set(ids)) == 1

    def test_create_different_prices_same_id(self):
        """Test that creating items with different prices returns consistent ID."""
        prices = [10.0, 20.0, 30.0]
        ids = []
        
        for price in prices:
            r = client.post("/items", json={"name": "item", "price": price})
            assert r.status_code == 200
            ids.append(r.json()["id"])
        
        # All should return same ID
        assert len(set(ids)) == 1

    def test_create_returns_id_one_consistently(self):
        """Test that create always returns id=1."""
        for _ in range(5):
            r = client.post("/items", json={"name": "item", "price": 10.0})
            assert r.status_code == 200
            assert r.json()["id"] == 1
