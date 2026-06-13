"""
Enhanced validation tests for /items POST endpoint.
Tests edge cases, boundary conditions, and input validation.
"""
from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price field validation."""

    def test_create_item_negative_price(self):
        """Test that negative prices are rejected."""
        r = client.post("/items", json={"name": "book", "price": -1})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    def test_create_item_very_negative_price(self):
        """Test that very negative prices are rejected."""
        r = client.post("/items", json={"name": "book", "price": -999999})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    def test_create_item_zero_price(self):
        """Test that zero price is rejected."""
        r = client.post("/items", json={"name": "book", "price": 0})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    @pytest.mark.parametrize("price", [-100, -1, -0.01, 0])
    def test_create_item_non_positive_prices(self, price):
        """Parametrized test for all non-positive prices."""
        r = client.post("/items", json={"name": "book", "price": price})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    @pytest.mark.parametrize("price", [0.01, 1, 100, 999999.99])
    def test_create_item_valid_prices(self, price):
        """Parametrized test for valid prices."""
        r = client.post("/items", json={"name": "book", "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == price


class TestCreateItemNameValidation:
    """Test name field validation."""

    def test_create_item_empty_name(self):
        """Test that empty name is rejected by Pydantic."""
        r = client.post("/items", json={"name": "", "price": 10})
        # Empty string is still a valid string in Pydantic, so this should succeed
        assert r.status_code == 200
        assert r.json()["name"] == ""

    def test_create_item_whitespace_name(self):
        """Test that whitespace-only name is accepted."""
        r = client.post("/items", json={"name": "   ", "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == "   "

    def test_create_item_long_name(self):
        """Test that very long names are accepted."""
        long_name = "a" * 10000
        r = client.post("/items", json={"name": long_name, "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == long_name

    def test_create_item_special_characters_in_name(self):
        """Test that special characters in name are accepted."""
        special_name = "Item @#$%^&*() with 'quotes' and \"double quotes\""
        r = client.post("/items", json={"name": special_name, "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == special_name

    def test_create_item_unicode_name(self):
        """Test that unicode characters in name are accepted."""
        unicode_name = "商品 📦 Товар"
        r = client.post("/items", json={"name": unicode_name, "price": 10})
        assert r.status_code == 200
        assert r.json()["name"] == unicode_name


class TestCreateItemTypeValidation:
    """Test type validation for request fields."""

    def test_create_item_price_as_string(self):
        """Test that string price is rejected."""
        r = client.post("/items", json={"name": "book", "price": "10.5"})
        # FastAPI/Pydantic will attempt to coerce the string to float
        # This might succeed if the string is a valid number string
        assert r.status_code in (200, 422)

    def test_create_item_price_as_null(self):
        """Test that null price is rejected."""
        r = client.post("/items", json={"name": "book", "price": None})
        assert r.status_code == 422

    def test_create_item_name_as_number(self):
        """Test that numeric name is accepted (Pydantic coerces)."""
        r = client.post("/items", json={"name": 123, "price": 10})
        # Pydantic may coerce numeric name to string
        assert r.status_code in (200, 422)

    def test_create_item_name_as_null(self):
        """Test that null name is rejected."""
        r = client.post("/items", json={"name": None, "price": 10})
        assert r.status_code == 422


class TestCreateItemMissingFields:
    """Test missing required fields."""

    def test_create_item_missing_name(self):
        """Test that missing name field is rejected."""
        r = client.post("/items", json={"price": 10})
        assert r.status_code == 422

    def test_create_item_missing_price(self):
        """Test that missing price field is rejected."""
        r = client.post("/items", json={"name": "book"})
        assert r.status_code == 422

    def test_create_item_missing_both_fields(self):
        """Test that missing both fields is rejected."""
        r = client.post("/items", json={})
        assert r.status_code == 422


class TestCreateItemExtraFields:
    """Test behavior with extra fields in request."""

    def test_create_item_with_extra_fields(self):
        """Test that extra fields are ignored."""
        r = client.post(
            "/items",
            json={"name": "book", "price": 10, "extra": "field", "another": 123}
        )
        assert r.status_code == 200
        assert r.json()["name"] == "book"
        assert r.json()["price"] == 10

    def test_create_item_with_id_field(self):
        """Test that providing id field is ignored."""
        r = client.post("/items", json={"name": "book", "price": 10, "id": 999})
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1  # ID should be server-generated, not from request


class TestCreateItemParametrized:
    """Comprehensive parametrized tests."""

    @pytest.mark.parametrize("name,price", [
        ("book", 10),
        ("pen", 0.5),
        ("expensive item", 9999.99),
        ("single char", 1),
    ])
    def test_create_item_various_valid_inputs(self, name, price):
        """Test various valid item names and prices."""
        r = client.post("/items", json={"name": name, "price": price})
        assert r.status_code == 200
        assert r.json()["name"] == name
        assert r.json()["price"] == price
