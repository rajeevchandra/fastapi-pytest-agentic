"""Input validation and boundary testing for /items endpoint."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price field validation and boundary conditions."""

    @pytest.mark.parametrize(
        "price,expected_status,should_fail",
        [
            (-100, 400, True),
            (-1, 400, True),
            (-0.01, 400, True),
            (0, 400, True),
            (0.01, 200, False),
            (1, 200, False),
            (10.5, 200, False),
            (100.99, 200, False),
            (1000, 200, False),
            (999999.99, 200, False),
            (1e6, 200, False),
        ],
    )
    def test_create_item_price_boundaries(self, price, expected_status, should_fail):
        """Test price validation at boundary values."""
        response = client.post(
            "/items",
            json={"name": "test_item", "price": price}
        )
        assert response.status_code == expected_status
        if should_fail:
            assert response.json()["detail"] == "price must be > 0"
        else:
            data = response.json()
            assert data["price"] == price
            assert data["name"] == "test_item"

    def test_create_item_price_very_large(self):
        """Test with extremely large price value."""
        response = client.post(
            "/items",
            json={"name": "expensive", "price": 1e15}
        )
        assert response.status_code == 200
        assert response.json()["price"] == 1e15

    def test_create_item_price_decimal_precision(self):
        """Test price with high decimal precision."""
        response = client.post(
            "/items",
            json={"name": "precise", "price": 19.999}
        )
        assert response.status_code == 200
        assert response.json()["price"] == 19.999


class TestCreateItemNameValidation:
    """Test name field validation and boundary conditions."""

    @pytest.mark.parametrize(
        "name",
        [
            "book",
            "pen",
            "A",
            "a",
            "0",
            "product 1",
            "item-with-dash",
            "item_with_underscore",
            "123",
            "a" * 100,  # Long name
        ],
    )
    def test_create_item_valid_names(self, name):
        """Test with various valid name formats."""
        response = client.post(
            "/items",
            json={"name": name, "price": 10.0}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == name
        assert data["price"] == 10.0

    def test_create_item_name_with_unicode(self):
        """Test name with unicode characters."""
        response = client.post(
            "/items",
            json={"name": "商品", "price": 15.5}
        )
        assert response.status_code == 200
        assert response.json()["name"] == "商品"

    def test_create_item_name_with_emojis(self):
        """Test name with emoji characters."""
        response = client.post(
            "/items",
            json={"name": "🎁 gift", "price": 20.0}
        )
        assert response.status_code == 200
        assert response.json()["name"] == "🎁 gift"

    def test_create_item_name_with_special_chars(self):
        """Test name with special characters."""
        response = client.post(
            "/items",
            json={"name": "item!@#$%^&*()", "price": 5.0}
        )
        assert response.status_code == 200
        assert response.json()["name"] == "item!@#$%^&*()"


class TestCreateItemMissingFields:
    """Test handling of missing required fields."""

    def test_create_item_missing_price(self):
        """Test POST with missing price field."""
        response = client.post(
            "/items",
            json={"name": "incomplete"}
        )
        assert response.status_code == 422  # Validation error

    def test_create_item_missing_name(self):
        """Test POST with missing name field."""
        response = client.post(
            "/items",
            json={"price": 10.0}
        )
        assert response.status_code == 422  # Validation error

    def test_create_item_missing_both_fields(self):
        """Test POST with both required fields missing."""
        response = client.post("/items", json={})
        assert response.status_code == 422  # Validation error

    def test_create_item_empty_json(self):
        """Test POST with empty body."""
        response = client.post("/items", json={})
        assert response.status_code == 422


class TestCreateItemInvalidFieldTypes:
    """Test handling of invalid field types."""

    def test_create_item_price_as_string(self):
        """Test with price provided as string."""
        response = client.post(
            "/items",
            json={"name": "test", "price": "not_a_number"}
        )
        assert response.status_code == 422

    def test_create_item_price_as_null(self):
        """Test with price as null."""
        response = client.post(
            "/items",
            json={"name": "test", "price": None}
        )
        assert response.status_code == 422

    def test_create_item_name_as_integer(self):
        """Test with name as integer."""
        response = client.post(
            "/items",
            json={"name": 123, "price": 10.0}
        )
        # FastAPI/Pydantic may coerce or reject - check behavior
        # Most likely accepts it via string coercion or rejects it
        assert response.status_code in [200, 422]

    def test_create_item_name_as_null(self):
        """Test with name as null."""
        response = client.post(
            "/items",
            json={"name": None, "price": 10.0}
        )
        assert response.status_code == 422


class TestCreateItemResponseStructure:
    """Test response structure and format."""

    def test_create_item_response_has_required_fields(self):
        """Test that response contains all required fields."""
        response = client.post(
            "/items",
            json={"name": "test", "price": 5.0}
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "price" in data
        assert len(data) == 3  # Exactly 3 fields

    def test_create_item_response_id_is_integer(self):
        """Test that response id is an integer."""
        response = client.post(
            "/items",
            json={"name": "test", "price": 5.0}
        )
        data = response.json()
        assert isinstance(data["id"], int)
        assert data["id"] == 1

    def test_create_item_response_price_preserved(self):
        """Test that response price matches input price exactly."""
        test_price = 42.77
        response = client.post(
            "/items",
            json={"name": "precision_test", "price": test_price}
        )
        assert response.json()["price"] == test_price


class TestCreateItemEdgeCases:
    """Test edge cases and unusual scenarios."""

    def test_create_item_name_very_long(self):
        """Test with extremely long name."""
        long_name = "x" * 10000
        response = client.post(
            "/items",
            json={"name": long_name, "price": 1.0}
        )
        assert response.status_code == 200
        assert response.json()["name"] == long_name

    def test_create_item_name_whitespace_only(self):
        """Test with name containing only whitespace."""
        response = client.post(
            "/items",
            json={"name": "   ", "price": 1.0}
        )
        assert response.status_code == 200
        assert response.json()["name"] == "   "

    def test_create_item_price_float_precision(self):
        """Test price with various float precisions."""
        prices = [0.01, 0.001, 0.0001, 0.00001]
        for price in prices:
            response = client.post(
                "/items",
                json={"name": "test", "price": price}
            )
            assert response.status_code == 200
            assert response.json()["price"] == price

    def test_create_item_multiple_calls_same_response(self):
        """Test multiple calls return same response structure."""
        for i in range(3):
            response = client.post(
                "/items",
                json={"name": f"item_{i}", "price": i + 1.5}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1  # Always returns id=1
            assert data["name"] == f"item_{i}"
            assert data["price"] == i + 1.5
