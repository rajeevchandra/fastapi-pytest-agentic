"""Path parameter edge cases and integration testing."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterBoundaries:
    """Tests for item_id path parameter boundaries."""

    def test_get_item_id_one_found(self):
        """Test that item_id=1 is found."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_get_item_id_zero_not_found(self):
        """Test that item_id=0 is not found."""
        r = client.get("/items/0")
        assert r.status_code == 404

    def test_get_item_id_negative_not_found(self):
        """Test that negative item_id is not found."""
        r = client.get("/items/-1")
        assert r.status_code == 404

    def test_get_item_id_large_negative_not_found(self):
        """Test that large negative item_id is not found."""
        r = client.get("/items/-999999")
        assert r.status_code == 404

    def test_get_item_id_two_not_found(self):
        """Test that item_id=2 is not found."""
        r = client.get("/items/2")
        assert r.status_code == 404

    def test_get_item_id_very_large_not_found(self):
        """Test that very large item_id is not found."""
        r = client.get("/items/999999999")
        assert r.status_code == 404

    def test_get_item_id_max_int_not_found(self):
        """Test that maximum integer is not found."""
        r = client.get("/items/9223372036854775807")  # max int64
        assert r.status_code == 404

    @pytest.mark.parametrize("item_id", [2, 3, 100, 1000, 999999])
    def test_various_item_ids_not_found(self, item_id):
        """Test various item IDs that should not be found."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    @pytest.mark.parametrize("item_id", [1])
    def test_item_id_one_always_found(self, item_id):
        """Test that only item_id=1 is found."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 200


class TestGetItemPathParameterTypes:
    """Tests for path parameter type validation."""

    def test_get_item_with_string_id(self):
        """Test that non-numeric path parameter is rejected."""
        r = client.get("/items/invalid")
        assert r.status_code in [404, 422]  # Either not found or validation error

    def test_get_item_with_float_id(self):
        """Test that float in path parameter is handled."""
        r = client.get("/items/1.5")
        assert r.status_code in [404, 422]

    def test_get_item_with_special_chars(self):
        """Test that special characters in path are handled."""
        r = client.get("/items/@#$%")
        assert r.status_code in [404, 422]

    def test_get_item_with_empty_id(self):
        """Test that missing path parameter fails."""
        r = client.get("/items/")
        # This might be a 404 or 422 depending on routing
        assert r.status_code in [404, 422]

    def test_get_item_with_very_long_number(self):
        """Test very long numeric string as path parameter."""
        long_id = "1" * 100
        r = client.get(f"/items/{long_id}")
        assert r.status_code in [404, 422]

    def test_get_item_with_leading_zeros(self):
        """Test item ID with leading zeros."""
        r = client.get("/items/0001")
        # Should be treated as 1
        response_status = r.status_code
        if response_status == 200:
            assert r.json()["id"] == 1
        else:
            assert response_status in [404, 422]

    def test_get_item_with_plus_sign(self):
        """Test item ID with plus sign."""
        r = client.get("/items/+1")
        assert r.status_code in [200, 404, 422]

    def test_get_item_with_hex_notation(self):
        """Test item ID in hex notation."""
        r = client.get("/items/0x1")
        assert r.status_code in [404, 422]


class TestCreateThenGetIntegration:
    """Tests for create followed by get operations."""

    def test_create_item_then_get_fails(self):
        """Test that created items are not persisted."""
        # Create an item
        r1 = client.post("/items", json={"name": "created", "price": 15.0})
        assert r1.status_code == 200
        created = r1.json()
        assert created["id"] == 1

        # Try to get it - should still return the hardcoded item
        r2 = client.get("/items/1")
        assert r2.status_code == 200
        gotten = r2.json()
        # The API returns hardcoded data, not what was created
        assert gotten["id"] == 1
        assert gotten["name"] == "sample"
        assert gotten["price"] == 10.0

    def test_multiple_creates_then_get(self):
        """Test multiple creates followed by get."""
        # Create multiple items
        for i in range(3):
            r = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            assert r.status_code == 200

        # Get should return hardcoded data
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["name"] == "sample"

    def test_create_different_items_get_same_response(self):
        """Test that different create requests get same response."""
        item1 = client.post("/items", json={"name": "book", "price": 12.0}).json()
        item2 = client.post("/items", json={"name": "pen", "price": 1.0}).json()

        # Both should return id=1
        assert item1["id"] == item2["id"] == 1

        # But their names differ
        assert item1["name"] == "book"
        assert item2["name"] == "pen"


class TestGetItemConsistency:
    """Tests for GET endpoint consistency."""

    def test_get_item_1_multiple_times_consistent(self):
        """Test that getting item 1 multiple times returns same data."""
        responses = [client.get("/items/1") for _ in range(5)]
        data_list = [r.json() for r in responses]

        # All should be identical
        first = data_list[0]
        for data in data_list[1:]:
            assert data == first

    def test_get_item_1_always_has_same_name(self):
        """Test that item 1 always has the same name."""
        names = [client.get("/items/1").json()["name"] for _ in range(5)]
        assert all(name == "sample" for name in names)

    def test_get_item_1_always_has_same_price(self):
        """Test that item 1 always has the same price."""
        prices = [client.get("/items/1").json()["price"] for _ in range(5)]
        assert all(price == 10.0 for price in prices)


class TestItemIdValidation:
    """Tests for item ID validation across GET operations."""

    @pytest.mark.parametrize("item_id", [1])
    def test_only_item_id_1_works(self, item_id):
        """Test that only item_id=1 returns success."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 200

    @pytest.mark.parametrize("item_id", [2, 3, 0, -1, 100, 999])
    def test_other_item_ids_not_found(self, item_id):
        """Test that other item IDs return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    @pytest.mark.parametrize("item_id", [1, 1, 1, 1])
    def test_multiple_requests_for_item_1(self, item_id):
        """Test multiple requests for item 1."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 200
        assert r.json()["id"] == 1


class TestErrorScenarioSequences:
    """Tests for sequences involving error scenarios."""

    def test_404_then_success(self):
        """Test 404 error followed by successful request."""
        # First request should fail
        r1 = client.get("/items/999")
        assert r1.status_code == 404

        # Second request should succeed
        r2 = client.get("/items/1")
        assert r2.status_code == 200
        assert r2.json()["id"] == 1

    def test_validation_error_then_success(self):
        """Test validation error followed by successful request."""
        # First request should fail
        r1 = client.post("/items", json={"name": "item", "price": -5})
        assert r1.status_code == 400

        # Second request should succeed
        r2 = client.post("/items", json={"name": "item", "price": 10})
        assert r2.status_code == 200
        assert r2.json()["id"] == 1

    def test_multiple_error_scenarios(self):
        """Test multiple error scenarios in sequence."""
        errors = [
            (client.get("/items/999"), 404),
            (client.post("/items", json={"name": "item", "price": 0}), 400),
            (client.post("/items", json={"name": "item"}), 422),
        ]
        for r, expected_status in errors:
            assert r.status_code == expected_status


class TestResponseValidationWithPathParams:
    """Tests for response validation across different path parameters."""

    def test_response_structure_for_item_1(self):
        """Test response structure for item ID 1."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data

    def test_not_found_error_structure_for_item_2(self):
        """Test error structure for non-existent item."""
        r = client.get("/items/2")
        assert r.status_code == 404
        data = r.json()
        assert "detail" in data

    def test_response_values_for_item_1(self):
        """Test specific response values for item 1."""
        r = client.get("/items/1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0

    def test_error_message_for_item_not_found(self):
        """Test error message content."""
        r = client.get("/items/2")
        assert r.status_code == 404
        data = r.json()
        assert data["detail"] == "not found"


class TestIntegrationWithHealthEndpoint:
    """Tests for interactions with health endpoint."""

    def test_health_then_create(self):
        """Test health check followed by create."""
        r1 = client.get("/health")
        assert r1.status_code == 200

        r2 = client.post("/items", json={"name": "item", "price": 10})
        assert r2.status_code == 200

    def test_health_then_get(self):
        """Test health check followed by get."""
        r1 = client.get("/health")
        assert r1.status_code == 200

        r2 = client.get("/items/1")
        assert r2.status_code == 200

    def test_create_then_health(self):
        """Test create followed by health check."""
        r1 = client.post("/items", json={"name": "item", "price": 10})
        assert r1.status_code == 200

        r2 = client.get("/health")
        assert r2.status_code == 200

    def test_get_then_health(self):
        """Test get followed by health check."""
        r1 = client.get("/items/1")
        assert r1.status_code == 200

        r2 = client.get("/health")
        assert r2.status_code == 200

    def test_health_endpoint_not_affected_by_item_operations(self):
        """Test that item operations don't affect health status."""
        # Perform various item operations
        client.post("/items", json={"name": "item1", "price": 10})
        client.get("/items/1")
        client.post("/items", json={"name": "item2", "price": -1})  # Error
        client.get("/items/999")  # 404

        # Health should still be ok
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}


class TestBoundaryConditionSequences:
    """Tests for sequences with boundary conditions."""

    def test_sequence_with_min_price(self):
        """Test sequence with minimum positive price."""
        prices = [0.01, 0.001, 0.0001]
        for price in prices:
            r = client.post("/items", json={"name": f"item_{price}", "price": price})
            if price > 0:
                assert r.status_code == 200

    def test_sequence_with_max_values(self):
        """Test sequence with maximum values."""
        large_price = 999999999.99
        long_name = "x" * 1000

        r = client.post("/items", json={"name": long_name, "price": large_price})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == large_price
        assert data["name"] == long_name

    @pytest.mark.parametrize("item_id_sequence", [
        [1, 1, 1],
        [2, 1, 2],
        [1, 999, 1],
        [0, 1, -1],
    ])
    def test_get_sequences_with_various_ids(self, item_id_sequence):
        """Test GET sequences with various ID patterns."""
        results = []
        for item_id in item_id_sequence:
            r = client.get(f"/items/{item_id}")
            results.append((item_id, r.status_code))

        # Only item_id=1 should succeed
        for item_id, status in results:
            if item_id == 1:
                assert status == 200
            else:
                assert status == 404


class TestDataPersistenceAcrossRequests:
    """Tests verifying that data is NOT persisted (stateless API)."""

    def test_created_item_not_retrievable_by_new_id(self):
        """Test that created items don't get new retrievable IDs."""
        # Create an item
        r1 = client.post("/items", json={"name": "unique_item", "price": 99.99})
        assert r1.status_code == 200
        created_id = r1.json()["id"]

        # Should still be 1
        assert created_id == 1

        # Try to get it back - should get hardcoded item
        r2 = client.get("/items/1")
        assert r2.json()["name"] == "sample"
        assert r2.json()["price"] == 10.0

    def test_multiple_creates_no_id_increment(self):
        """Test that IDs don't increment with multiple creates."""
        ids = []
        for i in range(5):
            r = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            assert r.status_code == 200
            ids.append(r.json()["id"])

        # All should be 1
        assert all(id == 1 for id in ids)

    def test_get_always_returns_same_data(self):
        """Test that GET always returns same hardcoded data."""
        # Create various items first
        client.post("/items", json={"name": "item1", "price": 10})
        client.post("/items", json={"name": "item2", "price": 20})

        # All GETs should return same hardcoded data
        data_list = [client.get("/items/1").json() for _ in range(3)]

        for data in data_list:
            assert data["id"] == 1
            assert data["name"] == "sample"
            assert data["price"] == 10.0
