"""Input validation and boundary testing for create_item endpoint."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price validation for item creation."""

    @pytest.mark.parametrize("price,expected_status", [
        (0.01, 200),          # minimum positive
        (1.0, 200),           # typical value
        (999999.99, 200),     # large value
        (0, 400),             # zero - invalid
        (-1, 400),            # negative - invalid
        (-0.01, 400),         # small negative - invalid
        (-999999.99, 400),    # large negative - invalid
    ])
    def test_create_item_price_boundaries(self, price, expected_status):
        """Test price boundary values."""
        response = client.post(
            "/items",
            json={"name": "test item", "price": price}
        )
        assert response.status_code == expected_status
        if expected_status == 200:
            data = response.json()
            assert data["price"] == price
        else:
            assert "detail" in response.json()


class TestCreateItemNameValidation:
    """Test name validation for item creation."""

    @pytest.mark.parametrize("name", [
        "a",                           # single char
        "normal item",                 # typical
        "Item with Numbers 123",       # with numbers
        "Special-Chars_Item",          # with special chars
        "Very " * 50 + "Long Name",   # very long (255+ chars)
    ])
    def test_create_item_name_variations(self, name):
        """Test various name formats."""
        response = client.post(
            "/items",
            json={"name": name, "price": 10.0}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == name


class TestCreateItemMissingFields:
    """Test missing required fields."""

    def test_create_item_missing_name(self):
        """Test missing name field."""
        response = client.post(
            "/items",
            json={"price": 10.0}
        )
        assert response.status_code == 422

    def test_create_item_missing_price(self):
        """Test missing price field."""
        response = client.post(
            "/items",
            json={"name": "test"}
        )
        assert response.status_code == 422

    def test_create_item_empty_json(self):
        """Test empty JSON body."""
        response = client.post(
            "/items",
            json={}
        )
        assert response.status_code == 422


class TestCreateItemInputTypes:
    """Test type validation for inputs."""

    def test_create_item_price_as_string(self):
        """Test price provided as string."""
        response = client.post(
            "/items",
            json={"name": "test", "price": "not_a_number"}
        )
        assert response.status_code == 422

    def test_create_item_price_as_null(self):
        """Test price provided as null."""
        response = client.post(
            "/items",
            json={"name": "test", "price": None}
        )
        assert response.status_code == 422

    def test_create_item_name_as_number(self):
        """Test name provided as number."""
        response = client.post(
            "/items",
            json={"name": 123, "price": 10.0}
        )
        # Pydantic will try to coerce, but if it fails validation, returns 422
        assert response.status_code in [200, 422]
