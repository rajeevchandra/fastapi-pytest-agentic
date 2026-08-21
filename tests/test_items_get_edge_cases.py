import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test path parameter validation for get_item endpoint."""

    def test_get_item_with_positive_id(self):
        """Test getting item with positive integer ID."""
        r = client.get("/items/1")
        assert r.status_code == 200

    @pytest.mark.parametrize("item_id", [2, 3, 100, 999, 1000000])
    def test_get_item_with_various_positive_ids(self, item_id):
        """Test that various positive IDs return 404 (since only ID=1 exists)."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    @pytest.mark.parametrize("item_id", [0, -1, -100, -999])
    def test_get_item_with_zero_and_negative_ids(self, item_id):
        """Test with zero and negative IDs."""
        r = client.get(f"/items/{item_id}")
        # Should return 404 since item doesn't exist
        assert r.status_code == 404
        assert "not found" in r.json()["detail"]

    def test_get_item_with_very_large_id(self):
        """Test with extremely large ID value."""
        large_id = 9999999999
        r = client.get(f"/items/{large_id}")
        assert r.status_code == 404

    def test_get_item_with_string_id(self):
        """Test with non-numeric path parameter."""
        r = client.get("/items/notanumber")
        assert r.status_code == 422  # Validation error

    def test_get_item_with_float_id(self):
        """Test with float-like path parameter."""
        r = client.get("/items/1.5")
        # This might be interpreted as string or cause validation error
        assert r.status_code in [404, 422]

    def test_get_item_with_uuid_format_id(self):
        """Test with UUID format instead of integer."""
        r = client.get("/items/550e8400-e29b-41d4-a716-446655440000")
        assert r.status_code == 422  # Should be validation error


class TestGetItemBoundaryValues:
    """Test boundary value conditions for get_item endpoint."""

    def test_get_item_id_zero(self):
        """Test with ID = 0 (common boundary)."""
        r = client.get("/items/0")
        assert r.status_code == 404

    def test_get_item_id_one(self):
        """Test with ID = 1 (the valid ID)."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_get_item_id_negative_one(self):
        """Test with ID = -1 (boundary of positive/negative)."""
        r = client.get("/items/-1")
        assert r.status_code == 404

    def test_get_item_id_max_int_boundary(self):
        """Test with large integer near int32 max."""
        r = client.get("/items/2147483647")
        assert r.status_code == 404

    def test_get_item_id_large_int64(self):
        """Test with large int64 value."""
        r = client.get("/items/9223372036854775807")
        assert r.status_code == 404


class TestCreateItemIdGeneration:
    """Test ID generation in create_item responses."""

    def test_create_item_id_is_always_one(self):
        """Test that all created items get ID = 1."""
        r = client.post("/items", json={"name": "item1", "price": 10})
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_create_item_id_sequential_requests(self):
        """Test ID remains 1 across multiple requests."""
        r1 = client.post("/items", json={"name": "item1", "price": 10})
        assert r1.status_code == 200
        assert r1.json()["id"] == 1

        r2 = client.post("/items", json={"name": "item2", "price": 20})
        assert r2.status_code == 200
        assert r2.json()["id"] == 1

    def test_create_item_id_type_is_integer(self):
        """Test that ID is always an integer."""
        r = client.post("/items", json={"name": "test", "price": 10})
        assert r.status_code == 200
        assert isinstance(r.json()["id"], int)


class TestIntegrationScenarios:
    """Test integration scenarios involving multiple operations."""

    def test_create_and_get_same_item(self):
        """Test creating item then retrieving it (if ID was dynamic)."""
        # Note: This tests current hardcoded behavior where only ID=1 exists
        create_r = client.post("/items", json={"name": "test_item", "price": 15})
        assert create_r.status_code == 200
        created_id = create_r.json()["id"]

        get_r = client.get(f"/items/{created_id}")
        assert get_r.status_code == 200

    def test_create_multiple_items_different_names(self):
        """Test creating multiple items with different names."""
        names = ["book", "pen", "notebook", "pencil"]
        for name in names:
            r = client.post("/items", json={"name": name, "price": 10})
            assert r.status_code == 200
            assert r.json()["name"] == name

    def test_create_multiple_items_different_prices(self):
        """Test creating multiple items with different prices."""
        prices = [5.99, 10.00, 15.50, 99.99]
        for price in prices:
            r = client.post("/items", json={"name": "test", "price": price})
            assert r.status_code == 200
            assert r.json()["price"] == price

    def test_get_item_multiple_times(self):
        """Test retrieving same item multiple times."""
        for _ in range(5):
            r = client.get("/items/1")
            assert r.status_code == 200
            assert r.json()["id"] == 1
            assert r.json()["name"] == "sample"
            assert r.json()["price"] == 10.0

    def test_health_check_before_operations(self):
        """Test health check endpoint works before other operations."""
        health_r = client.get("/health")
        assert health_r.status_code == 200
        assert health_r.json()["status"] == "ok"

        item_r = client.get("/items/1")
        assert item_r.status_code == 200

    def test_health_check_after_operations(self):
        """Test health check still works after create operations."""
        client.post("/items", json={"name": "test", "price": 10})
        client.get("/items/1")

        health_r = client.get("/health")
        assert health_r.status_code == 200
        assert health_r.json()["status"] == "ok"


class TestHTTPMethodValidation:
    """Test that wrong HTTP methods are rejected."""

    def test_wrong_method_on_health_endpoint(self):
        """Test that POST is not allowed on health endpoint."""
        r = client.post("/health")
        assert r.status_code in [405, 404]  # Method Not Allowed or Not Found

    def test_wrong_method_on_create_endpoint(self):
        """Test that GET is not allowed on create endpoint."""
        r = client.get("/items")
        assert r.status_code in [405, 404]

    def test_wrong_method_on_get_endpoint(self):
        """Test that POST is not allowed on get endpoint."""
        r = client.post("/items/1")
        assert r.status_code in [405, 404]


class TestEdgeCaseSequences:
    """Test sequences of edge case operations."""

    def test_error_then_success(self):
        """Test creating error followed by success."""
        # Try invalid price
        error_r = client.post("/items", json={"name": "test", "price": 0})
        assert error_r.status_code == 400

        # Then try valid request
        success_r = client.post("/items", json={"name": "test", "price": 10})
        assert success_r.status_code == 200

    def test_not_found_then_found(self):
        """Test requesting non-existent then existing item."""
        # Try non-existent item
        not_found_r = client.get("/items/999")
        assert not_found_r.status_code == 404

        # Then get existing item
        found_r = client.get("/items/1")
        assert found_r.status_code == 200

    def test_validation_error_then_success(self):
        """Test validation error followed by success."""
        # Missing required field
        error_r = client.post("/items", json={"name": "test"})
        assert error_r.status_code == 422

        # Successful request
        success_r = client.post("/items", json={"name": "test", "price": 10})
        assert success_r.status_code == 200

    def test_multiple_errors_then_success(self):
        """Test multiple failed attempts then success."""
        # Negative price
        r1 = client.post("/items", json={"name": "test", "price": -5})
        assert r1.status_code == 400

        # Zero price
        r2 = client.post("/items", json={"name": "test", "price": 0})
        assert r2.status_code == 400

        # Missing field
        r3 = client.post("/items", json={"price": 10})
        assert r3.status_code == 422

        # Success
        r4 = client.post("/items", json={"name": "test", "price": 10})
        assert r4.status_code == 200


class TestPriceEdgeCases:
    """Test price edge cases comprehensively."""

    @pytest.mark.parametrize("price", [
        0.001, 0.01, 0.1, 1, 10, 100, 1000, 10000, 100000, 1000000
    ])
    def test_create_item_with_powers_of_ten(self, price):
        """Test prices that are powers of 10 or nearby."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    @pytest.mark.parametrize("price", [0.01, 0.5, 0.99, 1.5, 9.99, 10.5, 99.99])
    def test_create_item_with_decimal_precision(self, price):
        """Test various decimal precision values."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 200
        assert abs(r.json()["price"] - price) < 0.0001

    @pytest.mark.parametrize("price", [-0.01, -0.5, -1, -10, -100])
    def test_create_item_rejects_all_negative_prices(self, price):
        """Test that all negative prices are rejected."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400


class TestNameEdgeCases:
    """Test name field edge cases comprehensively."""

    @pytest.mark.parametrize("name", [
        "a", "ab", "abc", "a" * 10, "a" * 100, "a" * 1000
    ])
    def test_create_item_with_various_name_lengths(self, name):
        """Test various name lengths."""
        r = client.post("/items", json={"name": name, "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == name

    @pytest.mark.parametrize("name", [
        " ", "  ", "\t", "\n", " a ", "a b", "a  b"
    ])
    def test_create_item_with_whitespace_variations(self, name):
        """Test names with various whitespace."""
        r = client.post("/items", json={"name": name, "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == name

    @pytest.mark.parametrize("name", [
        "CaseSensitive", "UPPERCASE", "lowercase", "MiXeD"
    ])
    def test_create_item_with_case_variations(self, name):
        """Test that name case is preserved."""
        r = client.post("/items", json={"name": name, "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == name


class TestResponseConsistency:
    """Test that responses are consistent across requests."""

    def test_get_item_response_consistent(self):
        """Test that getting same item multiple times returns same data."""
        responses = []
        for _ in range(3):
            r = client.get("/items/1")
            assert r.status_code == 200
            responses.append(r.json())

        # All responses should be identical
        assert responses[0] == responses[1] == responses[2]

    def test_create_item_response_consistent_across_names(self):
        """Test that ID is consistent regardless of name."""
        for name in ["a", "test", "product"]:
            r = client.post("/items", json={"name": name, "price": 10})
            assert r.status_code == 200
            assert r.json()["id"] == 1

    def test_create_item_response_consistent_across_prices(self):
        """Test that ID is consistent regardless of price."""
        for price in [1, 10, 100]:
            r = client.post("/items", json={"name": "test", "price": price})
            assert r.status_code == 200
            assert r.json()["id"] == 1
