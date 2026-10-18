"""Comprehensive input validation tests for ItemIn model and create_item endpoint."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemValidPrice:
    """Test successful item creation with valid prices."""

    @pytest.mark.parametrize("price", [
        0.01,
        1.0,
        10.5,
        100.0,
        999.99,
        1000.0,
        9999.99,
    ])
    def test_create_item_various_positive_prices(self, price):
        """Test that various positive prices are accepted."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["price"] == price
        assert data["id"] == 1
        assert data["name"] == "test"

    @pytest.mark.parametrize("name", [
        "a",
        "book",
        "very long product name with spaces",
        "Product123",
        "item-with-dashes",
        "item_with_underscores",
        "UPPERCASE",
    ])
    def test_create_item_various_names(self, name):
        """Test that various name formats are accepted."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name
        assert data["price"] == 10.0
        assert data["id"] == 1

    def test_create_item_minimal_valid(self):
        """Test creation with minimal valid inputs."""
        r = client.post("/items", json={"name": "x", "price": 0.01})
        assert r.status_code == 200
        assert r.json()["name"] == "x"
        assert r.json()["price"] == 0.01


class TestCreateItemInvalidPrice:
    """Test rejection of invalid prices."""

    @pytest.mark.parametrize("price", [
        0,
        -0.01,
        -1,
        -10,
        -100.5,
        -999.99,
        -1000.0,
    ])
    def test_create_item_rejects_negative_and_zero_prices(self, price):
        """Test that zero and negative prices are rejected."""
        r = client.post("/items", json={"name": "bad", "price": price})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"

    def test_create_item_zero_price_explicit(self):
        """Test explicit rejection of zero price."""
        r = client.post("/items", json={"name": "item", "price": 0})
        assert r.status_code == 400
        assert r.json()["detail"] == "price must be > 0"


class TestCreateItemMissingFields:
    """Test handling of missing required fields."""

    def test_create_item_missing_name(self):
        """Test that missing name field is rejected."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422

    def test_create_item_missing_price(self):
        """Test that missing price field is rejected."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422

    def test_create_item_missing_all_fields(self):
        """Test that completely empty JSON is rejected."""
        r = client.post("/items", json={})
        assert r.status_code == 422


class TestCreateItemWrongTypes:
    """Test handling of wrong data types."""

    def test_create_item_price_as_string(self):
        """Test that string price is rejected."""
        r = client.post("/items", json={"name": "test", "price": "10"})
        assert r.status_code == 422

    def test_create_item_price_as_null(self):
        """Test that null price is rejected."""
        r = client.post("/items", json={"name": "test", "price": None})
        assert r.status_code == 422

    def test_create_item_name_as_number(self):
        """Test that numeric name is converted to string or rejected."""
        r = client.post("/items", json={"name": 123, "price": 10.0})
        # FastAPI will coerce this, so check it works
        assert r.status_code == 200
        assert r.json()["id"] == 1

    def test_create_item_name_as_null(self):
        """Test that null name is rejected."""
        r = client.post("/items", json={"name": None, "price": 10.0})
        assert r.status_code == 422


class TestCreateItemEmptyName:
    """Test handling of empty name field."""

    def test_create_item_empty_string_name(self):
        """Test creation with empty string name."""
        r = client.post("/items", json={"name": "", "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == ""
        assert data["price"] == 10.0
        assert data["id"] == 1


class TestCreateItemUnicodeHandling:
    """Test handling of unicode and international characters."""

    @pytest.mark.parametrize("name", [
        "café",
        "naïve",
        "日本語",
        "中文",
        "العربية",
        "🎉 emoji",
        "Ñoño",
    ])
    def test_create_item_unicode_names(self, name):
        """Test that unicode names are handled correctly."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name
        assert data["id"] == 1
        assert data["price"] == 10.0


class TestCreateItemEdgeCasePrices:
    """Test edge cases for price values."""

    def test_create_item_very_large_price(self):
        """Test creation with very large price."""
        large_price = 1e10
        r = client.post("/items", json={"name": "expensive", "price": large_price})
        assert r.status_code == 200
        assert r.json()["price"] == large_price

    def test_create_item_very_small_positive_price(self):
        """Test creation with very small positive price."""
        small_price = 0.001
        r = client.post("/items", json={"name": "cheap", "price": small_price})
        assert r.status_code == 200
        assert r.json()["price"] == small_price

    def test_create_item_float_price(self):
        """Test creation with decimal prices."""
        r = client.post("/items", json={"name": "item", "price": 19.99})
        assert r.status_code == 200
        assert r.json()["price"] == 19.99

    def test_create_item_integer_price(self):
        """Test creation with integer price."""
        r = client.post("/items", json={"name": "item", "price": 5})
        assert r.status_code == 200
        assert r.json()["price"] == 5.0


class TestCreateItemSpecialCharactersInName:
    """Test handling of special characters in name."""

    @pytest.mark.parametrize("name", [
        "item#1",
        "item@store",
        "item$price",
        "item%off",
        "item&more",
        "item*special",
        "item(1)",
        "item[1]",
        "item{1}",
        "item/home",
        "item\\path",
    ])
    def test_create_item_special_characters(self, name):
        """Test that special characters are handled."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name
        assert data["id"] == 1
