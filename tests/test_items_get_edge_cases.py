"""
Edge case and integration tests for API endpoints.

Tests cover:
- Boundary value testing for item_id (negative, zero, max)
- Interaction patterns between endpoints
- Complex input/output combinations
- Stress testing with various input scenarios
- State consistency across operations
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemBoundaryValues:
    """Test boundary value analysis for item_id parameter."""

    def test_get_item_with_zero_id(self):
        """Test that item_id = 0 returns 404."""
        r = client.get("/items/0")
        assert r.status_code == 404
        assert "not found" in r.json()["detail"].lower()

    def test_get_item_with_negative_id(self):
        """Test that negative item_id returns 404."""
        r = client.get("/items/-1")
        assert r.status_code == 404

    def test_get_item_with_large_negative_id(self):
        """Test that large negative item_id returns 404."""
        r = client.get("/items/-999999")
        assert r.status_code == 404

    @pytest.mark.parametrize("item_id", [-1, -10, -100, -1000])
    def test_get_item_negative_ids_all_404(self, item_id):
        """Test that all negative item_ids return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    @pytest.mark.parametrize("item_id", [1, 2, 3, 100, 999, 1000])
    def test_get_item_only_id_1_succeeds(self, item_id):
        """Test that only item_id 1 succeeds, others return 404."""
        r = client.get(f"/items/{item_id}")
        if item_id == 1:
            assert r.status_code == 200
        else:
            assert r.status_code == 404

    def test_get_item_id_1_always_succeeds(self):
        """Test that item_id 1 consistently succeeds."""
        for _ in range(3):
            r = client.get("/items/1")
            assert r.status_code == 200
            assert r.json()["id"] == 1

    def test_get_item_max_safe_integer(self):
        """Test with max safe integer value."""
        max_safe_int = 2**53 - 1
        r = client.get(f"/items/{max_safe_int}")
        assert r.status_code == 404

    def test_get_item_very_large_id(self):
        """Test with very large item_id."""
        r = client.get("/items/999999999999999")
        assert r.status_code == 404


class TestPriceExtremeValues:
    """Test extreme price values and edge cases."""

    @pytest.mark.parametrize("price", [
        float('inf'),
        float('-inf'),
    ])
    def test_create_item_with_infinity_prices(self, price):
        """Test handling of infinite prices."""
        # Note: These may be handled by JSON serialization before reaching validation
        r = client.post("/items", json={"name": "test", "price": price})
        # Should either fail validation or be accepted depending on implementation
        assert r.status_code in (200, 400, 422)

    def test_create_item_price_very_small_positive(self):
        """Test creation with very small positive price."""
        r = client.post("/items", json={"name": "test", "price": 1e-15})
        assert r.status_code == 200
        assert r.json()["price"] == 1e-15

    def test_create_item_price_extremely_large(self):
        """Test creation with extremely large price."""
        r = client.post("/items", json={"name": "test", "price": 1e308})
        # Should succeed unless there's a max price validation
        assert r.status_code in (200, 400)

    @pytest.mark.parametrize("price", [
        0.0000001,
        0.000001,
        0.00001,
        0.0001,
    ])
    def test_create_item_precision_edge_cases(self, price):
        """Test price precision at various decimal places."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 200
        # Price should be preserved or close to original
        returned_price = r.json()["price"]
        assert returned_price == price or abs(returned_price - price) < 1e-15


class TestNameEdgeCases:
    """Test edge cases for the name field."""

    @pytest.mark.parametrize("name", [
        "\n",
        "\t",
        "\r",
        " \n \t ",
    ])
    def test_create_item_whitespace_names(self, name):
        """Test item creation with various whitespace characters."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    def test_create_item_very_long_name(self):
        """Test creation with very long name."""
        long_name = "a" * 10000
        r = client.post("/items", json={"name": long_name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == long_name

    def test_create_item_name_with_null_bytes(self):
        """Test handling of names with null bytes."""
        # Most JSON implementations will either reject or handle null bytes
        r = client.post("/items", json={"name": "test\x00null", "price": 10.0})
        # Behavior depends on JSON parser implementation
        assert r.status_code in (200, 422)

    @pytest.mark.parametrize("name", [
        "🎉🎊🎈",
        "😀😃😄😁",
        "🔥💯✨",
        "🌍🌎🌏",
    ])
    def test_create_item_emoji_names(self, name):
        """Test item creation with emoji characters."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name

    @pytest.mark.parametrize("name", [
        "name\x00with\x00nulls",
        "control\x01\x02\x03chars",
    ])
    def test_create_item_control_characters(self, name):
        """Test handling of control characters in names."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        # May succeed or fail depending on validation
        assert r.status_code in (200, 422)


class TestIntegrationMultipleOperations:
    """Test integration patterns across multiple operations."""

    def test_create_item_then_get_same_item(self):
        """Test that we can create and retrieve an item."""
        # Create item
        create_r = client.post("/items", json={"name": "integration_test", "price": 25.5})
        assert create_r.status_code == 200
        created_data = create_r.json()

        # Get the created item (should get item_id 1)
        get_r = client.get(f"/items/{created_data['id']}")
        assert get_r.status_code == 200
        get_data = get_r.json()

        # Verify consistency
        assert get_data["id"] == created_data["id"]

    def test_multiple_creates_all_return_id_1(self):
        """Test that multiple create operations all return id 1."""
        ids = []
        for i in range(5):
            r = client.post("/items", json={"name": f"item_{i}", "price": 10.0 + i})
            assert r.status_code == 200
            ids.append(r.json()["id"])

        # All should return id 1
        assert all(id == 1 for id in ids)

    def test_create_then_get_price_precision_preserved(self):
        """Test that price precision is preserved through create/get."""
        original_price = 99.99
        create_r = client.post("/items", json={"name": "precision_test", "price": original_price})
        created_price = create_r.json()["price"]

        get_r = client.get("/items/1")
        retrieved_price = get_r.json()["price"]

        # Allow small floating point difference
        assert abs(created_price - original_price) < 1e-9 or created_price == original_price
        assert abs(retrieved_price - original_price) < 1e-9 or retrieved_price == original_price

    def test_health_check_before_and_after_operations(self):
        """Test that health check works before and after other operations."""
        # Health before
        health_before = client.get("/health")
        assert health_before.status_code == 200
        assert health_before.json()["status"] == "ok"

        # Create item
        create_r = client.post("/items", json={"name": "test", "price": 10.0})
        assert create_r.status_code == 200

        # Get item
        get_r = client.get("/items/1")
        assert get_r.status_code == 200

        # Health after
        health_after = client.get("/health")
        assert health_after.status_code == 200
        assert health_after.json()["status"] == "ok"

    def test_consecutive_get_requests_same_response(self):
        """Test that consecutive gets return identical responses."""
        responses = []
        for _ in range(5):
            r = client.get("/items/1")
            assert r.status_code == 200
            responses.append(r.json())

        # All responses should be identical
        for resp in responses[1:]:
            assert resp == responses[0]

    def test_create_with_various_names_then_get(self):
        """Test creating items with various names and verify response."""
        test_names = ["product_a", "product_b", "product_c"]
        for name in test_names:
            r = client.post("/items", json={"name": name, "price": 15.0})
            assert r.status_code == 200
            created_name = r.json()["name"]
            assert created_name == name


class TestErrorRecovery:
    """Test API behavior after error conditions."""

    def test_api_works_after_invalid_price_error(self):
        """Test that API works normally after an invalid price error."""
        # First request with invalid price
        error_r = client.post("/items", json={"name": "bad", "price": -1})
        assert error_r.status_code == 400

        # Next request should work normally
        ok_r = client.post("/items", json={"name": "good", "price": 10.0})
        assert ok_r.status_code == 200
        assert ok_r.json()["name"] == "good"

    def test_api_works_after_404_error(self):
        """Test that API works normally after a 404 error."""
        # First request returns 404
        error_r = client.get("/items/999")
        assert error_r.status_code == 404

        # Next request should work normally
        ok_r = client.get("/items/1")
        assert ok_r.status_code == 200

    def test_api_works_after_validation_error(self):
        """Test that API works normally after a validation error."""
        # Request with missing field
        error_r = client.post("/items", json={"name": "test"})
        assert error_r.status_code == 422

        # Next request should work normally
        ok_r = client.post("/items", json={"name": "test", "price": 10.0})
        assert ok_r.status_code == 200

    def test_error_responses_do_not_affect_get(self):
        """Test that errors in POST don't affect GET."""
        # Generate some POST errors
        for _ in range(3):
            client.post("/items", json={"name": "test", "price": -1})

        # GET should still work
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["id"] == 1


class TestResponseTypeConsistency:
    """Test consistency of response types across scenarios."""

    @pytest.mark.parametrize("price,name", [
        (10.0, "test1"),
        (20.5, "test2"),
        (0.01, "test3"),
        (1000.0, "test4"),
    ])
    def test_all_success_responses_have_same_structure(self, price, name):
        """Test that all successful responses have consistent structure."""
        r = client.post("/items", json={"name": name, "price": price})
        assert r.status_code == 200
        data = r.json()

        # Check structure consistency
        assert "id" in data and isinstance(data["id"], int)
        assert "name" in data and isinstance(data["name"], str)
        assert "price" in data and isinstance(data["price"], (int, float))
        assert len(data) == 3

    @pytest.mark.parametrize("item_id", [2, 10, 100, 999])
    def test_all_404_responses_have_same_structure(self, item_id):
        """Test that all 404 responses have consistent structure."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404
        data = r.json()

        # Check structure consistency
        assert isinstance(data, dict)
        assert "detail" in data
        assert isinstance(data["detail"], str)


class TestRequestMethodCompliance:
    """Test proper HTTP method handling."""

    def test_post_to_items_endpoint(self):
        """Test POST method on items creation endpoint."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        assert r.status_code == 200

    def test_get_items_endpoint(self):
        """Test GET method on items retrieval endpoint."""
        r = client.get("/items/1")
        assert r.status_code == 200

    def test_get_health_endpoint(self):
        """Test GET method on health endpoint."""
        r = client.get("/health")
        assert r.status_code == 200


class TestSpecialInputCombinations:
    """Test special combinations of inputs."""

    @pytest.mark.parametrize("name,price", [
        ("", 0.01),
        ("x", 1e-10),
        ("very_long_name_" * 100, 1e308),
        ("🎉", 0.0000001),
    ])
    def test_create_item_extreme_combinations(self, name, price):
        """Test creation with extreme parameter combinations."""
        r = client.post("/items", json={"name": name, "price": price})
        assert r.status_code == 200
        assert r.json()["name"] == name
        assert r.json()["price"] == price

    @pytest.mark.parametrize("name,price", [
        ("test", 0),
        ("test", -1),
        ("test", -1e10),
        ("", -0.01),
    ])
    def test_create_item_invalid_combinations(self, name, price):
        """Test creation with invalid parameter combinations."""
        r = client.post("/items", json={"name": name, "price": price})
        assert r.status_code == 400
        assert "price" in r.json()["detail"].lower()


class TestRepeatedOperations:
    """Test behavior with repeated operations."""

    def test_repeated_get_requests(self):
        """Test that repeated GET requests return consistent results."""
        first = client.get("/items/1").json()
        for _ in range(10):
            result = client.get("/items/1").json()
            assert result == first

    def test_repeated_health_checks(self):
        """Test that repeated health checks always succeed."""
        for _ in range(10):
            r = client.get("/health")
            assert r.status_code == 200
            assert r.json()["status"] == "ok"

    def test_repeated_successful_creates(self):
        """Test that repeated successful creates all return same id."""
        ids = []
        for i in range(10):
            r = client.post("/items", json={"name": f"item{i}", "price": 10.0})
            assert r.status_code == 200
            ids.append(r.json()["id"])

        assert all(id == ids[0] for id in ids)

    def test_repeated_404_requests(self):
        """Test that repeated 404 requests are consistent."""
        for _ in range(5):
            r = client.get("/items/999")
            assert r.status_code == 404
            assert "not found" in r.json()["detail"].lower()
