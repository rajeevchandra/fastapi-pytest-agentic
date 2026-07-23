import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Parametrized tests for price boundary conditions."""

    @pytest.mark.parametrize("price", [0.01, 0.1, 1.0, 100.0, 999999.99])
    def test_create_item_valid_prices(self, price):
        """Test POST /items with valid prices."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 200
        assert r.json()["price"] == price

    @pytest.mark.parametrize("price", [-0.01, -1.0, -100.0, 0])
    def test_create_item_invalid_prices(self, price):
        """Test POST /items with invalid (non-positive) prices."""
        r = client.post("/items", json={"name": "item", "price": price})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]


class TestCreateItemNameValidation:
    """Parametrized tests for name field variations."""

    @pytest.mark.parametrize("name", [
        "book",
        "a",
        "A",
        "item_123",
        "item-name",
        "Item Name",
        "Item!@#$%",
        "UPPERCASE",
        "A" * 500,
    ])
    def test_create_item_valid_names(self, name):
        """Test POST /items with various valid name formats."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == name


class TestCreateItemMissingFields:
    """Tests for missing or null required fields."""

    def test_create_item_missing_name(self):
        """Test POST /items without name field."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422

    def test_create_item_missing_price(self):
        """Test POST /items without price field."""
        r = client.post("/items", json={"name": "item"})
        assert r.status_code == 422

    def test_create_item_null_name(self):
        """Test POST /items with null name."""
        r = client.post("/items", json={"name": None, "price": 10.0})
        assert r.status_code == 422

    def test_create_item_null_price(self):
        """Test POST /items with null price."""
        r = client.post("/items", json={"name": "item", "price": None})
        assert r.status_code == 422

    def test_create_item_empty_payload(self):
        """Test POST /items with empty JSON object."""
        r = client.post("/items", json={})
        assert r.status_code == 422


class TestCreateItemTypeValidation:
    """Tests for type validation and coercion."""

    def test_create_item_string_price(self):
        """Test POST /items with string price."""
        r = client.post("/items", json={"name": "item", "price": "10.0"})
        assert r.status_code == 200
        assert r.json()["price"] == 10.0

    def test_create_item_non_numeric_string_price(self):
        """Test POST /items with non-numeric string price."""
        r = client.post("/items", json={"name": "item", "price": "abc"})
        assert r.status_code == 422

    def test_create_item_integer_price(self):
        """Test POST /items with integer price."""
        r = client.post("/items", json={"name": "item", "price": 5})
        assert r.status_code == 200
        assert r.json()["price"] == 5

    def test_create_item_extra_fields(self):
        """Test POST /items with extra fields in payload."""
        r = client.post("/items", json={
            "name": "item",
            "price": 10.0,
            "extra": "field",
            "another": 123
        })
        assert r.status_code == 200
        assert r.json()["name"] == "item"
        assert r.json()["price"] == 10.0


class TestCreateItemEdgeCases:
    """Edge case tests for item creation."""

    def test_create_item_very_small_price(self):
        """Test POST /items with very small price."""
        r = client.post("/items", json={"name": "item", "price": 0.00001})
        assert r.status_code == 200
        assert r.json()["price"] == 0.00001

    def test_create_item_very_large_price(self):
        """Test POST /items with very large price."""
        r = client.post("/items", json={"name": "item", "price": 1e10})
        assert r.status_code == 200

    def test_create_item_unicode_name(self):
        """Test POST /items with unicode characters in name."""
        r = client.post("/items", json={"name": "书籍", "price": 10.0})
        assert r.status_code == 200
        assert r.json()["name"] == "书籍"

    def test_create_item_emoji_name(self):
        """Test POST /items with emoji in name."""
        r = client.post("/items", json={"name": "item 🎉", "price": 10.0})
        assert r.status_code == 200
        assert "🎉" in r.json()["name"]

    def test_create_item_sequential(self):
        """Test creating multiple items in sequence."""
        for i in range(3):
            r = client.post("/items", json={"name": f"item{i}", "price": 10.0 + i})
            assert r.status_code == 200
            assert r.json()["name"] == f"item{i}"
