"""
Test suite for input validation and boundary testing of the /items endpoint.
Covers price boundary conditions, name field variations, and missing fields.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Parametrized tests for price boundary conditions."""

    @pytest.mark.parametrize(
        "price,expected_status,should_succeed",
        [
            # Valid prices
            (0.01, 200, True),
            (1.0, 200, True),
            (100.0, 200, True),
            (999999.99, 200, True),
            (0.1, 200, True),
            # Invalid prices
            (-0.01, 400, False),
            (-1.0, 400, False),
            (-100.0, 400, False),
            (0, 400, False),
        ],
    )
    def test_create_item_price_validation(self, price, expected_status, should_succeed):
        """Test create item with various price values."""
        response = client.post(
            "/items",
            json={"name": "test-item", "price": price},
        )
        assert response.status_code == expected_status
        if should_succeed:
            data = response.json()
            assert data["price"] == price
        else:
            assert "detail" in response.json()


class TestCreateItemNameValidation:
    """Parametrized tests for name field variations."""

    @pytest.mark.parametrize(
        "name,expected_status",
        [
            # Valid names
            ("simple-name", 200),
            ("Product With Spaces", 200),
            ("name-with-dashes", 200),
            ("name_with_underscores", 200),
            ("UPPERCASE", 200),
            ("123-numeric", 200),
            ("special!@#$%chars", 200),
            # Edge cases that should still pass (non-empty strings)
            ("a", 200),
            ("very-" * 100 + "long-name", 200),
        ],
    )
    def test_create_item_name_variations(self, name, expected_status):
        """Test create item with various name formats."""
        response = client.post(
            "/items",
            json={"name": name, "price": 10.0},
        )
        assert response.status_code == expected_status
        if expected_status == 200:
            assert response.json()["name"] == name


class TestCreateItemMissingFields:
    """Test missing required fields in request body."""

    def test_create_item_missing_name(self):
        """Test POST /items without name field."""
        response = client.post("/items", json={"price": 10.0})
        # FastAPI returns 422 for validation errors
        assert response.status_code == 422

    def test_create_item_missing_price(self):
        """Test POST /items without price field."""
        response = client.post("/items", json={"name": "test"})
        # FastAPI returns 422 for validation errors
        assert response.status_code == 422

    def test_create_item_empty_payload(self):
        """Test POST /items with empty JSON object."""
        response = client.post("/items", json={})
        # FastAPI returns 422 for validation errors
        assert response.status_code == 422

    def test_create_item_null_name(self):
        """Test POST /items with null name field."""
        response = client.post("/items", json={"name": None, "price": 10.0})
        # FastAPI returns 422 for validation errors
        assert response.status_code == 422

    def test_create_item_null_price(self):
        """Test POST /items with null price field."""
        response = client.post("/items", json={"name": "test", "price": None})
        # FastAPI returns 422 for validation errors
        assert response.status_code == 422


class TestCreateItemTypeValidation:
    """Test type validation for item fields."""

    def test_create_item_price_as_string(self):
        """Test POST /items with price as string (should fail validation or coerce)."""
        response = client.post("/items", json={"name": "test", "price": "10.0"})
        # FastAPI may coerce string to float, so this should succeed
        assert response.status_code == 200
        assert response.json()["price"] == 10.0

    def test_create_item_price_as_string_non_numeric(self):
        """Test POST /items with price as non-numeric string."""
        response = client.post("/items", json={"name": "test", "price": "invalid"})
        # FastAPI returns 422 for validation errors
        assert response.status_code == 422

    def test_create_item_name_as_number(self):
        """Test POST /items with name as number (should coerce to string)."""
        response = client.post("/items", json={"name": 123, "price": 10.0})
        # FastAPI may coerce number to string
        assert response.status_code == 200
        assert response.json()["name"] == "123"

    def test_create_item_extra_fields(self):
        """Test POST /items with extra fields (should be ignored)."""
        response = client.post(
            "/items",
            json={"name": "test", "price": 10.0, "extra_field": "ignored", "id": 999},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test"
        assert data["price"] == 10.0
        # The response has its own id (always 1)
        assert data["id"] == 1


class TestCreateItemEdgeCases:
    """Test edge cases and special scenarios."""

    def test_create_item_very_small_positive_price(self):
        """Test create item with very small but valid price."""
        response = client.post(
            "/items",
            json={"name": "tiny", "price": 0.001},
        )
        assert response.status_code == 200
        assert response.json()["price"] == 0.001

    def test_create_item_very_large_price(self):
        """Test create item with very large price."""
        response = client.post(
            "/items",
            json={"name": "expensive", "price": 999999999.99},
        )
        assert response.status_code == 200
        assert response.json()["price"] == 999999999.99

    def test_create_item_unicode_name(self):
        """Test create item with unicode characters in name."""
        response = client.post(
            "/items",
            json={"name": "商品名", "price": 10.0},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "商品名"

    def test_create_item_emoji_in_name(self):
        """Test create item with emoji in name."""
        response = client.post(
            "/items",
            json={"name": "Product 🎉", "price": 10.0},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Product 🎉"

    def test_create_item_price_integer(self):
        """Test create item with integer price (should coerce to float)."""
        response = client.post(
            "/items",
            json={"name": "test", "price": 25},
        )
        assert response.status_code == 200
        assert response.json()["price"] == 25.0

    def test_create_item_multiple_times_same_request(self):
        """Test creating multiple items shows consistent ID (always returns 1)."""
        response1 = client.post("/items", json={"name": "first", "price": 10.0})
        response2 = client.post("/items", json={"name": "second", "price": 20.0})
        # Both should return id=1 as per implementation
        assert response1.json()["id"] == 1
        assert response2.json()["id"] == 1
