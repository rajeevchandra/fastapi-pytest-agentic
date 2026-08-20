"""
Edge cases and integration tests for the items API.
Tests path parameter edge cases, boundary values, and integration scenarios.
"""
from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test get_item endpoint with various path parameters."""

    @pytest.mark.parametrize(
        "item_id,expected_status",
        [
            (1, 200),  # Valid: item exists
            (0, 404),  # Boundary: zero
            (-1, 404),  # Boundary: negative
            (2, 404),  # Beyond range
            (100, 404),  # Large number
            (999999, 404),  # Very large number
            (2147483647, 404),  # Max int32
        ],
    )
    def test_get_item_with_various_ids(self, item_id, expected_status):
        """Test get_item with boundary item IDs."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == expected_status


class TestGetItemErrorMessages:
    """Test error messages from get_item endpoint."""

    def test_not_found_error_message_content(self):
        """Test that not found error has proper message."""
        response = client.get("/items/2")
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "not found"

    def test_not_found_error_message_for_various_ids(self):
        """Test not found message is consistent for different IDs."""
        for item_id in [0, 2, 999, -1]:
            response = client.get(f"/items/{item_id}")
            assert response.status_code == 404
            assert response.json()["detail"] == "not found"


class TestPriceEdgeCases:
    """Test price field edge cases and boundary conditions."""

    @pytest.mark.parametrize(
        "price",
        [
            0.0001,  # Very small
            0.001,
            0.01,
            0.1,
            1,
            10,
            100,
            1000,
            10000,
            100000,
            1000000,
            float("inf") if False else 1e10,  # Very large (avoid actual inf)
        ],
    )
    def test_valid_prices_are_accepted(self, price):
        """Test that valid prices are accepted."""
        response = client.post("/items", json={"name": "test", "price": price})
        assert response.status_code == 200
        data = response.json()
        assert data["price"] == price

    @pytest.mark.parametrize(
        "price",
        [
            0,
            -0.0001,
            -1,
            -100,
            -1000000,
        ],
    )
    def test_invalid_prices_are_rejected(self, price):
        """Test that invalid prices are rejected."""
        response = client.post("/items", json={"name": "test", "price": price})
        assert response.status_code == 400
        data = response.json()
        assert "price must be > 0" in data["detail"]


class TestNameEdgeCases:
    """Test name field edge cases and boundary conditions."""

    @pytest.mark.parametrize(
        "name",
        [
            "a",  # Single char
            "ab",  # Two chars
            "A" * 50,  # Long string
            "A" * 100,  # Very long string
            "A" * 200,  # Extremely long string
            " " * 10,  # Spaces only
            "123456789",  # Numeric only
            "!@#$%^&*()",  # Special chars only
            "\n" * 5,  # Newline chars
            "\t" * 5,  # Tab chars
        ],
    )
    def test_create_item_with_edge_case_names(self, name):
        """Test creating items with edge case names."""
        response = client.post("/items", json={"name": name, "price": 10.0})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == name


class TestCreateItemIntegration:
    """Integration tests for create_item endpoint."""

    def test_create_item_and_get_item_integration(self):
        """Test creating an item and then retrieving it."""
        # Create item
        create_response = client.post(
            "/items", json={"name": "Integration Test", "price": 25.50}
        )
        assert create_response.status_code == 200
        create_data = create_response.json()
        item_id = create_data["id"]

        # Get item
        get_response = client.get(f"/items/{item_id}")
        assert get_response.status_code == 200
        get_data = get_response.json()

        # Verify consistency
        assert get_data["id"] == create_data["id"]
        # Note: get_item returns hardcoded values, not created values

    def test_multiple_create_operations(self):
        """Test multiple consecutive create operations."""
        for i in range(5):
            response = client.post(
                "/items", json={"name": f"Item {i}", "price": 10.0 * (i + 1)}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1  # Always returns ID 1

    def test_create_and_get_item_1_always_works(self):
        """Test that creating and getting item 1 always works."""
        # Create first
        create_response = client.post(
            "/items", json={"name": "Test Item", "price": 100.0}
        )
        assert create_response.status_code == 200

        # Then get
        get_response = client.get("/items/1")
        assert get_response.status_code == 200


class TestGetItemBoundaryValues:
    """Test get_item with specific boundary conditions."""

    def test_get_item_1_returns_sample(self):
        """Test that getting item 1 returns sample item."""
        response = client.get("/items/1")
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == 1
        assert data["name"] == "sample"
        assert data["price"] == 10.0

    def test_get_item_1_consistent_response(self):
        """Test that item 1 returns consistent data."""
        responses = [client.get("/items/1") for _ in range(3)]
        
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
            assert data["name"] == "sample"
            assert data["price"] == 10.0

    def test_get_item_zero_not_found(self):
        """Test that item 0 is not found."""
        response = client.get("/items/0")
        assert response.status_code == 404

    def test_get_item_negative_not_found(self):
        """Test that negative item IDs are not found."""
        for item_id in [-1, -10, -100, -1000]:
            response = client.get(f"/items/{item_id}")
            assert response.status_code == 404


class TestCombinedScenarios:
    """Test combined scenarios involving multiple endpoints."""

    def test_create_with_boundary_price_then_get(self):
        """Test creating item with boundary price and getting it."""
        # Create with very small price
        create_response = client.post(
            "/items", json={"name": "Boundary", "price": 0.01}
        )
        assert create_response.status_code == 200
        assert create_response.json()["price"] == 0.01

        # Get item 1
        get_response = client.get("/items/1")
        assert get_response.status_code == 200
        assert get_response.json()["id"] == 1

    def test_create_with_long_name_then_get(self):
        """Test creating item with very long name and getting it."""
        long_name = "A" * 200
        
        # Create with long name
        create_response = client.post("/items", json={"name": long_name, "price": 10.0})
        assert create_response.status_code == 200
        assert create_response.json()["name"] == long_name

        # Get item 1
        get_response = client.get("/items/1")
        assert get_response.status_code == 200

    def test_invalid_create_then_valid_get(self):
        """Test invalid create doesn't affect subsequent get."""
        # Try invalid create
        invalid_response = client.post(
            "/items", json={"name": "test", "price": -10}
        )
        assert invalid_response.status_code == 400

        # Valid get should still work
        get_response = client.get("/items/1")
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["id"] == 1


class TestAPIRobustness:
    """Test API robustness and error recovery."""

    def test_api_recovers_from_validation_error(self):
        """Test that API works after validation error."""
        # Send invalid request
        client.post("/items", json={"name": "test", "price": -1})

        # Next valid request should still work
        response = client.post("/items", json={"name": "valid", "price": 10})
        assert response.status_code == 200

    def test_api_recovers_from_not_found_error(self):
        """Test that API works after 404 error."""
        # Request non-existent item
        client.get("/items/999")

        # Next valid request should work
        response = client.get("/items/1")
        assert response.status_code == 200

    def test_alternating_valid_invalid_requests(self):
        """Test alternating valid and invalid requests."""
        for i in range(3):
            # Valid create
            valid = client.post("/items", json={"name": f"item{i}", "price": 10.0})
            assert valid.status_code == 200

            # Invalid create
            invalid = client.post(
                "/items", json={"name": f"item{i}", "price": -1}
            )
            assert invalid.status_code == 400


class TestResponseDataTypes:
    """Test response data types across edge cases."""

    def test_id_is_always_positive_integer(self):
        """Test that id is always a positive integer."""
        for _ in range(3):
            response = client.post("/items", json={"name": "test", "price": 10.0})
            data = response.json()
            assert isinstance(data["id"], int)
            assert data["id"] > 0

    def test_name_is_always_string(self):
        """Test that name is always a string."""
        test_names = ["simple", "with spaces", "123", "!@#$"]
        for name in test_names:
            response = client.post("/items", json={"name": name, "price": 10.0})
            data = response.json()
            assert isinstance(data["name"], str)

    def test_price_is_always_number(self):
        """Test that price is always numeric."""
        test_prices = [1, 1.5, 0.01, 1000, 1000000]
        for price in test_prices:
            response = client.post("/items", json={"name": "test", "price": price})
            data = response.json()
            assert isinstance(data["price"], (int, float))


class TestValidationBoundaries:
    """Test validation at exact boundaries."""

    def test_price_boundary_zero_rejected(self):
        """Test that 0 price is exactly at rejection boundary."""
        response = client.post("/items", json={"name": "test", "price": 0})
        assert response.status_code == 400

    def test_price_boundary_positive_accepted(self):
        """Test that any positive price is accepted."""
        response = client.post("/items", json={"name": "test", "price": 0.0000001})
        assert response.status_code == 200

    def test_item_id_boundary_zero_not_found(self):
        """Test that item ID 0 is not found."""
        response = client.get("/items/0")
        assert response.status_code == 404

    def test_item_id_boundary_one_found(self):
        """Test that item ID 1 is found."""
        response = client.get("/items/1")
        assert response.status_code == 200
