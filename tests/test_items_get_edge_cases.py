"""Path parameter and integration edge cases for items endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test path parameter validation for get_item endpoint."""

    @pytest.mark.parametrize(
        "item_id,expected_status",
        [
            (1, 200),  # Valid ID
            (0, 404),  # Boundary: zero
            (-1, 404),  # Boundary: negative
            (2, 404),  # Out of range
            (999999, 404),  # Large ID
            (-999, 404),  # Large negative
        ],
    )
    def test_item_id_boundary_values(self, item_id, expected_status):
        """Test various item ID boundary values."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == expected_status

    def test_item_id_one_found(self):
        """Test that item ID 1 is found."""
        response = client.get("/items/1")
        assert response.status_code == 200
        assert response.json()["id"] == 1

    def test_item_id_zero_not_found(self):
        """Test that item ID 0 returns 404."""
        response = client.get("/items/0")
        assert response.status_code == 404

    def test_item_id_negative_not_found(self):
        """Test that negative item ID returns 404."""
        response = client.get("/items/-1")
        assert response.status_code == 404

    def test_item_id_large_positive_not_found(self):
        """Test that large positive ID not in data returns 404."""
        response = client.get("/items/99999")
        assert response.status_code == 404

    def test_item_id_boundary_validation_consistency(self):
        """Test that only ID 1 returns 200, all others 404."""
        for item_id in [0, 1, 2, 3, 5, 10, 100, -1, -10]:
            response = client.get(f"/items/{item_id}")
            if item_id == 1:
                assert response.status_code == 200
            else:
                assert response.status_code == 404


class TestCreateItemMultipleSequential:
    """Test creating multiple items in sequence."""

    def test_create_two_items_sequentially(self):
        """Test creating two items in sequence."""
        response1 = client.post("/items", json={"name": "item1", "price": 10.0})
        assert response1.status_code == 200
        assert response1.json()["name"] == "item1"

        response2 = client.post("/items", json={"name": "item2", "price": 20.0})
        assert response2.status_code == 200
        assert response2.json()["name"] == "item2"

    def test_create_many_items_in_loop(self):
        """Test creating many items in a loop."""
        for i in range(10):
            response = client.post(
                "/items", json={"name": f"item{i}", "price": float(i + 1)}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == f"item{i}"
            assert data["price"] == float(i + 1)

    def test_create_items_with_different_price_ranges(self):
        """Test creating items with various price ranges."""
        prices = [0.01, 1.0, 10.0, 100.0, 1000.0, 10000.0]
        for price in prices:
            response = client.post("/items", json={"name": f"item_{price}", "price": price})
            assert response.status_code == 200
            assert response.json()["price"] == price

    def test_create_items_with_various_names(self):
        """Test creating items with various name formats."""
        names = [
            "Simple",
            "With Space",
            "UPPERCASE",
            "lowercase",
            "123numeric",
            "special!@#$",
            "unicode_café",
            "veryverylongnamethatkeepsgoingandgoing",
        ]
        for name in names:
            response = client.post("/items", json={"name": name, "price": 10.0})
            assert response.status_code == 200
            assert response.json()["name"] == name

    def test_sequential_creates_all_return_200(self):
        """Test that all sequential creates return 200 OK."""
        for i in range(5):
            response = client.post(
                "/items", json={"name": f"test{i}", "price": 15.0 + i}
            )
            assert response.status_code == 200


class TestGetAfterCreate:
    """Test getting item after creation."""

    def test_create_then_get_same_item(self):
        """Test creating an item and verifying it with GET."""
        create_response = client.post(
            "/items", json={"name": "test_item", "price": 25.0}
        )
        assert create_response.status_code == 200
        created_data = create_response.json()

        # Note: The API always returns item ID 1 for GET /items/1
        get_response = client.get("/items/1")
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["id"] == 1

    def test_created_item_matches_request_data(self):
        """Test that created item response matches request data."""
        request_data = {"name": "specific_item", "price": 42.50}
        response = client.post("/items", json=request_data)
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["name"] == request_data["name"]
        assert response_data["price"] == request_data["price"]


class TestErrorRecovery:
    """Test that endpoint recovers properly from errors."""

    def test_error_then_valid_request(self):
        """Test that valid request works after error."""
        # First send invalid request
        error_response = client.post("/items", json={"name": "test", "price": -1})
        assert error_response.status_code == 400

        # Then send valid request
        valid_response = client.post("/items", json={"name": "test", "price": 10.0})
        assert valid_response.status_code == 200
        assert valid_response.json()["price"] == 10.0

    def test_validation_error_then_valid_request(self):
        """Test that valid request works after validation error."""
        # First send request with missing field
        error_response = client.post("/items", json={"name": "test"})
        assert error_response.status_code == 422

        # Then send valid request
        valid_response = client.post("/items", json={"name": "test", "price": 20.0})
        assert valid_response.status_code == 200
        assert valid_response.json()["price"] == 20.0

    def test_404_then_valid_get(self):
        """Test that valid GET works after 404."""
        # First try non-existent item
        not_found_response = client.get("/items/999")
        assert not_found_response.status_code == 404

        # Then get valid item
        valid_response = client.get("/items/1")
        assert valid_response.status_code == 200
        assert valid_response.json()["id"] == 1


class TestCrosEndpointConsistency:
    """Test consistency across different endpoints."""

    def test_create_response_and_get_response_structure_consistent(self):
        """Test that create and get responses have same structure."""
        create_response = client.post(
            "/items", json={"name": "test", "price": 15.0}
        )
        assert create_response.status_code == 200
        create_data = create_response.json()

        get_response = client.get("/items/1")
        assert get_response.status_code == 200
        get_data = get_response.json()

        # Both should have same fields
        assert set(create_data.keys()) == set(get_data.keys())
        assert set(create_data.keys()) == {"id", "name", "price"}

    def test_create_response_field_types_match_get_field_types(self):
        """Test that field types are consistent between endpoints."""
        create_response = client.post(
            "/items", json={"name": "test", "price": 15.0}
        )
        assert create_response.status_code == 200
        create_data = create_response.json()

        get_response = client.get("/items/1")
        assert get_response.status_code == 200
        get_data = get_response.json()

        # Field types should match
        assert type(create_data["id"]) == type(get_data["id"])
        assert type(create_data["name"]) == type(get_data["name"])
        assert type(create_data["price"]) == type(get_data["price"])

    def test_all_responses_are_json_objects(self):
        """Test that all success responses are JSON objects."""
        responses = [
            client.post("/items", json={"name": "test", "price": 10.0}),
            client.get("/items/1"),
            client.get("/health"),
        ]
        for response in responses:
            assert response.status_code == 200
            assert isinstance(response.json(), dict)


class TestComplexScenarios:
    """Test complex real-world scenarios."""

    def test_create_valid_then_try_invalid_then_valid_again(self):
        """Test sequence: valid -> invalid -> valid."""
        # Valid
        r1 = client.post("/items", json={"name": "valid1", "price": 10.0})
        assert r1.status_code == 200

        # Invalid (missing price)
        r2 = client.post("/items", json={"name": "invalid"})
        assert r2.status_code == 422

        # Valid again
        r3 = client.post("/items", json={"name": "valid2", "price": 20.0})
        assert r3.status_code == 200
        assert r3.json()["name"] == "valid2"

    def test_alternating_create_and_get(self):
        """Test alternating POST and GET requests."""
        for i in range(3):
            # Create
            post_response = client.post(
                "/items", json={"name": f"item{i}", "price": 10.0 + i}
            )
            assert post_response.status_code == 200

            # Get
            get_response = client.get("/items/1")
            assert get_response.status_code == 200

    def test_create_with_special_prices_then_get(self):
        """Test creating items with special price values."""
        special_prices = [0.01, 1.0, 9.99, 100.0, 1000.0]
        for price in special_prices:
            create_response = client.post(
                "/items", json={"name": f"item_{price}", "price": price}
            )
            assert create_response.status_code == 200
            assert create_response.json()["price"] == price

            # Verify we can still get item 1
            get_response = client.get("/items/1")
            assert get_response.status_code == 200

    def test_stress_with_boundary_values(self):
        """Test with many boundary value requests."""
        boundary_prices = [0.001, 0.01, 1.0, 10.0, 100.0, 1000.0, 10000.0]
        for price in boundary_prices:
            response = client.post(
                "/items", json={"name": "boundary", "price": price}
            )
            assert response.status_code == 200
            assert response.json()["price"] == price


class TestDataPersistence:
    """Test data persistence across requests."""

    def test_get_item_1_is_consistent(self):
        """Test that getting item 1 returns consistent data structure."""
        responses = []
        for _ in range(3):
            response = client.get("/items/1")
            assert response.status_code == 200
            responses.append(response.json())

        # All responses should have same structure
        for data in responses:
            assert "id" in data
            assert "name" in data
            assert "price" in data
            assert data["id"] == 1

    def test_non_existent_items_remain_not_found(self):
        """Test that non-existent items consistently return 404."""
        test_ids = [2, 3, 5, 10, 100, -1]
        for item_id in test_ids:
            response = client.get(f"/items/{item_id}")
            assert response.status_code == 404

    def test_multiple_get_requests_return_same_status(self):
        """Test consistency of GET responses."""
        # Valid item
        for _ in range(3):
            response = client.get("/items/1")
            assert response.status_code == 200

        # Invalid items
        for item_id in [2, 999]:
            for _ in range(2):
                response = client.get(f"/items/{item_id}")
                assert response.status_code == 404


class TestHealthCheckIntegration:
    """Test health check endpoint integration."""

    def test_health_check_always_200(self):
        """Test that health check always returns 200."""
        for _ in range(5):
            response = client.get("/health")
            assert response.status_code == 200

    def test_health_check_status_always_ok(self):
        """Test that health check status is always 'ok'."""
        for _ in range(5):
            response = client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "ok"

    def test_health_check_independent_of_item_operations(self):
        """Test that health check works independently of item operations."""
        # Create item
        client.post("/items", json={"name": "test", "price": 10.0})
        # Health check should still work
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

        # Try error
        client.post("/items", json={"name": "test", "price": -1})
        # Health check should still work
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_health_check_after_invalid_requests(self):
        """Test that health check is unaffected by invalid requests."""
        # Send several invalid requests
        for _ in range(3):
            client.post("/items", json={"name": "test"})
            client.get("/items/999")

        # Health check should still work
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
