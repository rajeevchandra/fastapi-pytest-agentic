"""
Path parameter edge cases and integration scenarios.

Tests cover:
- Item ID boundary values (negative, zero, large)
- Multiple item operations
- Integration scenarios
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestGetItemPathParameterValidation:
    """Test path parameter validation for GET /items/{item_id}."""

    @pytest.mark.parametrize(
        "item_id",
        [
            -1,
            -100,
            -999999,
        ],
    )
    def test_get_item_negative_ids_not_found(self, item_id):
        """Negative item IDs should return 404."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    def test_get_item_zero_id_not_found(self):
        """Item ID 0 should return 404."""
        r = client.get("/items/0")
        assert r.status_code == 404

    @pytest.mark.parametrize(
        "item_id",
        [
            2,
            3,
            10,
            100,
            999999,
            2147483647,
        ],
    )
    def test_get_item_large_ids_not_found(self, item_id):
        """Large item IDs should return 404 (only ID 1 exists)."""
        r = client.get(f"/items/{item_id}")
        assert r.status_code == 404

    def test_get_item_only_id_one_exists(self):
        """Only item ID 1 should be found."""
        r = client.get("/items/1")
        assert r.status_code == 200
        assert r.json()["id"] == 1


class TestCreateItemWithVariousNames:
    """Test creating items with various name values."""

    @pytest.mark.parametrize(
        "name",
        [
            "A",
            "Book",
            "Test Item",
            "item_123",
            "item-name",
            "123",
            "!@#$%",
        ],
    )
    def test_create_item_with_various_names(self, name):
        """Creating items with various names should succeed."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name


class TestCreateItemWithVariousPrices:
    """Test creating items with various price values."""

    @pytest.mark.parametrize(
        "price",
        [
            0.01,
            1,
            1.5,
            10.0,
            100.0,
            999.99,
            9999.99,
            99999.99,
            100000.0,
        ],
    )
    def test_create_item_with_various_prices(self, price):
        """Creating items with various prices should succeed."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price


class TestCreateItemPriceBoundaries:
    """Test price boundary conditions."""

    def test_create_item_price_just_above_zero(self):
        """Price slightly above zero should succeed."""
        r = client.post("/items", json={"name": "item", "price": 0.001})
        assert r.status_code == 200
        assert r.json()["price"] > 0

    def test_create_item_price_just_at_zero(self):
        """Price at zero should fail."""
        r = client.post("/items", json={"name": "item", "price": 0.0})
        assert r.status_code == 400

    def test_create_item_price_just_below_zero(self):
        """Price just below zero should fail."""
        r = client.post("/items", json={"name": "item", "price": -0.001})
        assert r.status_code == 400

    def test_create_item_very_small_positive_price(self):
        """Very small positive prices should succeed."""
        r = client.post("/items", json={"name": "item", "price": 0.000001})
        assert r.status_code == 200

    def test_create_item_very_large_positive_price(self):
        """Very large positive prices should succeed."""
        r = client.post("/items", json={"name": "item", "price": 999999999.99})
        assert r.status_code == 200


class TestIntegrationCreateAndGet:
    """Integration tests for create and get operations."""

    def test_create_then_get_returns_created_item(self):
        """Created item should be retrievable (if stored)."""
        # Note: Current implementation only allows ID 1
        create_r = client.post("/items", json={"name": "test_book", "price": 15.5})
        assert create_r.status_code == 200
        assert create_r.json()["id"] == 1

        # Get the same item
        get_r = client.get("/items/1")
        assert get_r.status_code == 200
        # Current implementation returns hardcoded item
        assert get_r.json()["id"] == 1

    def test_multiple_create_requests_return_same_id(self):
        """Multiple creates should return ID 1 (current limitation)."""
        for _ in range(3):
            r = client.post("/items", json={"name": "item", "price": 10.0})
            assert r.status_code == 200
            assert r.json()["id"] == 1

    def test_create_get_sequence_consistent(self):
        """Create and Get operations should be consistent."""
        create_r = client.post("/items", json={"name": "book", "price": 12.5})
        assert create_r.status_code == 200

        get_r = client.get("/items/1")
        assert get_r.status_code == 200
        # Both should return valid items
        assert "id" in create_r.json()
        assert "id" in get_r.json()


class TestErrorRecoveryScenarios:
    """Test recovery from error conditions."""

    def test_api_recovers_after_validation_error(self):
        """API should work after a validation error."""
        # First request with validation error
        r1 = client.post("/items", json={"name": "item"})
        assert r1.status_code == 422

        # Second request should succeed
        r2 = client.post("/items", json={"name": "item", "price": 10.0})
        assert r2.status_code == 200

    def test_api_recovers_after_business_error(self):
        """API should work after a business logic error."""
        # First request with business error
        r1 = client.post("/items", json={"name": "item", "price": 0})
        assert r1.status_code == 400

        # Second request should succeed
        r2 = client.post("/items", json={"name": "item", "price": 10.0})
        assert r2.status_code == 200

    def test_api_recovers_after_not_found_error(self):
        """API should work after a 404 error."""
        # First request with 404
        r1 = client.get("/items/999")
        assert r1.status_code == 404

        # Second request should succeed
        r2 = client.get("/items/1")
        assert r2.status_code == 200


class TestNameFieldEdgeCases:
    """Test name field edge cases."""

    def test_create_item_empty_name(self):
        """Empty name should be accepted."""
        r = client.post("/items", json={"name": "", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == ""

    def test_create_item_name_with_spaces(self):
        """Name with spaces should be accepted."""
        r = client.post("/items", json={"name": "   spaces   ", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "   spaces   "

    def test_create_item_name_very_long(self):
        """Very long names should be accepted."""
        long_name = "x" * 1000
        r = client.post("/items", json={"name": long_name, "price": 10.0})
        assert r.status_code == 200
        assert len(r.json()["name"]) == 1000

    def test_create_item_name_unicode(self):
        """Unicode names should be accepted."""
        r = client.post("/items", json={"name": "日本語テスト", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "日本語テスト"

    def test_create_item_name_with_quotes(self):
        """Names with quotes should be accepted."""
        r = client.post("/items", json={"name": 'name"with"quotes', "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == 'name"with"quotes'


class TestComprehensiveResponseValidation:
    """Comprehensive response validation tests."""

    def test_all_item_responses_have_complete_structure(self):
        """All item responses should have complete structure."""
        # Test POST response
        post_r = client.post("/items", json={"name": "test", "price": 10.0})
        post_data = post_r.json()
        required_fields = {"id", "name", "price"}
        assert required_fields.issubset(post_data.keys())

        # Test GET response
        get_r = client.get("/items/1")
        get_data = get_r.json()
        assert required_fields.issubset(get_data.keys())

    def test_response_data_types_consistent(self):
        """Response data types should be consistent across endpoints."""
        post_r = client.post("/items", json={"name": "test", "price": 10.0})
        post_data = post_r.json()

        get_r = client.get("/items/1")
        get_data = get_r.json()

        # Check types are consistent
        assert type(post_data["id"]) == type(get_data["id"])
        assert type(post_data["name"]) == type(get_data["name"])
        assert type(post_data["price"]) == type(get_data["price"])

    def test_no_null_values_in_responses(self):
        """Responses should not contain null values in required fields."""
        r = client.post("/items", json={"name": "test", "price": 10.0})
        data = r.json()
        assert data["id"] is not None
        assert data["name"] is not None
        assert data["price"] is not None
