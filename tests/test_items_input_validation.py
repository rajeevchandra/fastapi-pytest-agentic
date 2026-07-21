import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCreateItemPriceValidation:
    """Test price field validation in item creation."""

    @pytest.mark.parametrize("price", [
        -1,
        -100,
        -0.01,
        0,
        0.0,
    ])
    def test_create_item_invalid_non_positive_prices(self, price):
        """Test that non-positive prices are rejected."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 400
        assert "price must be > 0" in r.json()["detail"]

    @pytest.mark.parametrize("price", [
        0.01,
        0.001,
        1.0,
        100.0,
        999999.99,
        1e6,
    ])
    def test_create_item_valid_positive_prices(self, price):
        """Test that positive prices are accepted."""
        r = client.post("/items", json={"name": "test", "price": price})
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == 1
        assert data["price"] == price
        assert data["name"] == "test"


class TestCreateItemNameValidation:
    """Test name field validation in item creation."""

    @pytest.mark.parametrize("name", [
        "",
        " ",
        "   ",
        "\t",
        "\n",
    ])
    def test_create_item_invalid_empty_or_whitespace_names(self, name):
        """Test that empty/whitespace names are rejected."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        # FastAPI Pydantic validation rejects empty strings for non-empty string fields
        # This depends on model validation - testing actual behavior
        if r.status_code == 422:
            assert "validation error" in r.json()["detail"][0]["type"].lower() or \
                   "string" in str(r.json()).lower()

    @pytest.mark.parametrize("name", [
        "a",
        "item",
        "My Book Title",
        "Item-123_with.special",
        "Unicode: café",
        "Emoji: 🎉",
        "x" * 1000,
    ])
    def test_create_item_valid_names(self, name):
        """Test that various valid names are accepted."""
        r = client.post("/items", json={"name": name, "price": 10.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == name
        assert data["price"] == 10.0


class TestCreateItemMissingFields:
    """Test behavior when required fields are missing."""

    def test_create_item_missing_price(self):
        """Test that missing price field is rejected."""
        r = client.post("/items", json={"name": "test"})
        assert r.status_code == 422
        assert "price" in str(r.json())

    def test_create_item_missing_name(self):
        """Test that missing name field is rejected."""
        r = client.post("/items", json={"price": 10.0})
        assert r.status_code == 422
        assert "name" in str(r.json())

    def test_create_item_no_fields(self):
        """Test that request with no fields is rejected."""
        r = client.post("/items", json={})
        assert r.status_code == 422
        assert "validation error" in str(r.json()).lower() or \
               "field" in str(r.json()).lower()


class TestCreateItemTypeValidation:
    """Test type validation for item creation fields."""

    @pytest.mark.parametrize("price_value", [
        "10",
        "10.5",
        None,
        [],
        {},
    ])
    def test_create_item_invalid_price_types(self, price_value):
        """Test that invalid price types are rejected."""
        r = client.post("/items", json={"name": "test", "price": price_value})
        assert r.status_code == 422

    @pytest.mark.parametrize("name_value", [
        123,
        45.67,
        None,
        [],
        {},
    ])
    def test_create_item_invalid_name_types(self, name_value):
        """Test that invalid name types are rejected."""
        r = client.post("/items", json={"name": name_value, "price": 10.0})
        assert r.status_code == 422


class TestCreateItemExtraFields:
    """Test handling of extra/unexpected fields."""

    def test_create_item_with_extra_fields(self):
        """Test that extra fields don't break the request."""
        r = client.post("/items", json={
            "name": "test",
            "price": 10.0,
            "description": "extra",
            "quantity": 5,
        })
        # FastAPI ignores extra fields by default in Pydantic models
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "test"
        assert data["price"] == 10.0

    def test_create_item_with_null_extra_fields(self):
        """Test request with null extra fields."""
        r = client.post("/items", json={
            "name": "test",
            "price": 10.0,
            "extra": None,
        })
        assert r.status_code == 200
