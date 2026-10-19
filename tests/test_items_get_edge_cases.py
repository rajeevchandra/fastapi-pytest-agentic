"""
Edge case and integration tests for FastAPI endpoints.
Tests boundary values, error combinations, and complex scenarios.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemBoundaryValues:
    """Test get item endpoint with boundary value item IDs."""

    def test_get_item_with_id_zero(self):
        """Test get item with ID of 0."""
        response = client.get("/items/0")
        assert response.status_code == 404
        assert response.json()["detail"] == "not found"

    def test_get_item_with_negative_id(self):
        """Test get item with negative ID."""
        response = client.get("/items/-1")
        assert response.status_code == 404
        assert response.json()["detail"] == "not found"

    def test_get_item_with_large_id(self):
        """Test get item with very large ID."""
        response = client.get("/items/999999999")
        assert response.status_code == 404
        assert response.json()["detail"] == "not found"

    def test_get_item_with_max_int_id(self):
        """Test get item with maximum integer value."""
        response = client.get("/items/2147483647")
        assert response.status_code == 404

    def test_get_item_id_one_success(self):
        """Test that only ID 1 returns success."""
        response = client.get("/items/1")
        assert response.status_code == 200

    @pytest.mark.parametrize("item_id", range(2, 10))
    def test_get_item_ids_two_to_nine_not_found(self, item_id):
        """Test that IDs 2-9 all return 404."""
        response = client.get(f"/items/{item_id}")
        assert response.status_code == 404


class TestCreateItemBoundaryPrices:
    """Test create item with extreme and boundary price values."""

    def test_create_item_smallest_positive_price(self):
        """Test creation with smallest possible positive price."""
        response = client.post(
            "/items",
            json={"name": "item", "price": 1e-300}
        )
        assert response.status_code == 200
        assert response.json()["price"] == 1e-300

    def test_create_item_with_price_just_above_zero(self):
        """Test creation with price just above zero."""
        response = client.post(
            "/items",
            json={"name": "item", "price": 0.0000001}
        )
        assert response.status_code == 200

    def test_create_item_with_price_just_below_zero(self):
        """Test that price just below zero is rejected."""
        response = client.post(
            "/items",
            json={"name": "item", "price": -0.0000001}
        )
        assert response.status_code == 400

    def test_create_item_with_price_at_zero_boundary(self):
        """Test that exactly zero price is rejected."""
        response = client.post(
            "/items",
            json={"name": "item", "price": 0.0}
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "price must be > 0"

    def test_create_item_with_very_large_price(self):
        """Test creation with very large price."""
        response = client.post(
            "/items",
            json={"name": "item", "price": 1.79e308}
        )
        assert response.status_code == 200

    @pytest.mark.parametrize("price", [1, 100, 1000, 1e6])
    def test_create_item_round_prices(self, price):
        """Test creation with round number prices."""
        response = client.post(
            "/items",
            json={"name": "item", "price": price}
        )
        assert response.status_code == 200
        assert response.json()["price"] == price


class TestCreateItemLongNames:
    """Test create item with various name lengths."""

    def test_create_item_single_char_name(self):
        """Test creation with single character name."""
        response = client.post(
            "/items",
            json={"name": "a", "price": 10.0}
        )
        assert response.status_code == 200
        assert response.json()["name"] == "a"

    def test_create_item_very_long_name(self):
        """Test creation with very long name."""
        long_name = "a" * 1000
        response = client.post(
            "/items",
            json={"name": long_name, "price": 10.0}
        )
        assert response.status_code == 200
        assert response.json()["name"] == long_name

    def test_create_item_name_with_all_whitespace(self):
        """Test creation with name containing only whitespace."""
        response = client.post(
            "/items",
            json={"name": "   \t\n  ", "price": 10.0}
        )
        assert response.status_code == 200

    def test_create_item_name_with_newlines(self):
        """Test creation with name containing newlines."""
        response = client.post(
            "/items",
            json={"name": "line1\nline2\nline3", "price": 10.0}
        )
        assert response.status_code == 200
        data = response.json()
        assert "line1" in data["name"]
        assert "line2" in data["name"]

    def test_create_item_name_with_special_chars(self):
        """Test creation with name containing special characters."""
        special_name = "<script>alert('xss')</script>"
        response = client.post(
            "/items",
            json={"name": special_name, "price": 10.0}
        )
        assert response.status_code == 200
        assert response.json()["name"] == special_name


class TestIntegrationMultipleRequests:
    """Test integration patterns with multiple requests."""

    def test_create_then_get_returns_hardcoded_item(self):
        """Test that creating an item then getting ID 1 returns fixed response."""
        # Create an item
        create_response = client.post(
            "/items",
            json={"name": "product_a", "price": 29.99}
        )
        assert create_response.status_code == 200
        
        # Get item 1 - should return hardcoded values
        get_response = client.get("/items/1")
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["id"] == 1
        assert data["name"] == "sample"  # Hardcoded, not "product_a"
        assert data["price"] == 10.0     # Hardcoded, not 29.99

    def test_multiple_creates_all_return_same_id(self):
        """Test that multiple creates all return ID 1."""
        for i in range(3):
            response = client.post(
                "/items",
                json={"name": f"item_{i}", "price": 10.0 + i}
            )
            assert response.status_code == 200
            assert response.json()["id"] == 1

    def test_create_invalid_then_valid(self):
        """Test creating invalid item followed by valid item."""
        # Invalid request
        bad_response = client.post(
            "/items",
            json={"name": "bad", "price": -10}
        )
        assert bad_response.status_code == 400
        
        # Valid request should still work
        good_response = client.post(
            "/items",
            json={"name": "good", "price": 10}
        )
        assert good_response.status_code == 200
        assert good_response.json()["name"] == "good"

    def test_get_invalid_then_valid_item(self):
        """Test getting non-existent item followed by valid item."""
        # Get non-existent
        bad_response = client.get("/items/999")
        assert bad_response.status_code == 404
        
        # Get valid item should still work
        good_response = client.get("/items/1")
        assert good_response.status_code == 200
        assert good_response.json()["id"] == 1


class TestErrorHandlingScenar ios:
    """Test various error handling scenarios."""

    def test_multiple_price_validations_negative_prices(self):
        """Test that all negative prices are rejected."""
        for price in [-1, -0.5, -100, -0.001]:
            response = client.post(
                "/items",
                json={"name": "item", "price": price}
            )
            assert response.status_code == 400
            assert response.json()["detail"] == "price must be > 0"

    def test_multiple_item_id_validations(self):
        """Test that all IDs except 1 return 404."""
        for item_id in [0, 2, 3, 5, 100, -1]:
            response = client.get(f"/items/{item_id}")
            assert response.status_code == 404
            assert response.json()["detail"] == "not found"

    def test_validation_error_on_type_mismatch(self):
        """Test validation errors for type mismatches."""
        invalid_requests = [
            {"name": "item", "price": "not_a_number"},
            {"name": 123, "price": 10.0},
            {"name": ["item"], "price": 10.0},
            {"name": "item", "price": {"value": 10}},
        ]
        
        for request_data in invalid_requests:
            response = client.post("/items", json=request_data)
            assert response.status_code == 422


class TestResponseDataConsistency:
    """Test consistency of response data."""

    def test_echo_property_for_names(self):
        """Test that name is echoed back correctly in create response."""
        test_names = ["apple", "book", "pen", "monitor", "unicode_🎉"]
        
        for name in test_names:
            response = client.post(
                "/items",
                json={"name": name, "price": 10.0}
            )
            assert response.status_code == 200
            assert response.json()["name"] == name

    def test_echo_property_for_prices(self):
        """Test that price is echoed back correctly in create response."""
        test_prices = [0.01, 1.5, 10.0, 99.99, 1000.0]
        
        for price in test_prices:
            response = client.post(
                "/items",
                json={"name": "item", "price": price}
            )
            assert response.status_code == 200
            assert response.json()["price"] == price

    def test_get_item_always_returns_same_data(self):
        """Test that get item ID 1 always returns same hardcoded data."""
        expected_data = {"id": 1, "name": "sample", "price": 10.0}
        
        for _ in range(5):
            response = client.get("/items/1")
            assert response.status_code == 200
            assert response.json() == expected_data


class TestHttpMethodValidation:
    """Test that endpoints respond correctly to different HTTP methods."""

    def test_get_health_with_post_not_allowed(self):
        """Test that POST to /health is not allowed."""
        response = client.post("/health")
        assert response.status_code == 405  # Method not allowed

    def test_create_item_with_get_not_allowed(self):
        """Test that GET to /items is not allowed."""
        response = client.get("/items")
        assert response.status_code == 405

    def test_get_item_with_post_not_allowed(self):
        """Test that POST to /items/{item_id} is not allowed."""
        response = client.post("/items/1")
        assert response.status_code == 405


class TestFieldValidation:
    """Test field-level validation edge cases."""

    def test_price_zero_with_valid_name(self):
        """Test that zero price is rejected regardless of name validity."""
        response = client.post(
            "/items",
            json={"name": "perfectly_valid_name", "price": 0}
        )
        assert response.status_code == 400

    def test_negative_price_with_valid_name(self):
        """Test that negative price is rejected regardless of name validity."""
        response = client.post(
            "/items",
            json={"name": "perfectly_valid_name", "price": -5.5}
        )
        assert response.status_code == 400

    def test_very_long_name_with_valid_price(self):
        """Test that very long names are accepted with valid price."""
        long_name = "x" * 10000
        response = client.post(
            "/items",
            json={"name": long_name, "price": 10.0}
        )
        assert response.status_code == 200
        assert len(response.json()["name"]) == 10000
